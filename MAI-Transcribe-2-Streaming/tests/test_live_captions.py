import asyncio
import base64
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import live_captions as live


SETTINGS = {
    "AZURE_MAI_ENDPOINT": "https://offline.services.ai.azure.com",
    "AZURE_MAI_DEPLOYMENT_NAME": "test-streaming",
    "AZURE_MAI_API_KEY": "private-test-key",
}


class FakeSocket:
    def __init__(self, complete=True):
        self.events = asyncio.Queue()
        self.events.put_nowait({"type": "session.created"})
        self.sent = []
        self.complete = complete
        self.closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self.closed = True

    async def recv(self):
        event = await self.events.get()
        if isinstance(event, Exception):
            raise event
        return json.dumps(event)

    async def send(self, message):
        message = json.loads(message)
        self.sent.append(message)
        if message["type"] == "session.update":
            self.events.put_nowait({"type": "session.updated"})
        if message["type"] == "input_audio_buffer.commit":
            self.events.put_nowait({"type": "input_audio_buffer.committed"})
            if self.complete:
                self.events.put_nowait({
                    "type": live.EVENT_PREFIX + "completed", "transcript": "Hello there!",
                })


class LiveCaptionTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.widget = live.LiveCaptions()
        self.widget.send = Mock()
        self.socket = FakeSocket()
        self.connection = Mock(return_value=self.socket)
        self.patches = [
            patch.object(live, "NoRedirectConnect", self.connection),
            patch.object(live, "dotenv_values", return_value={}),
            patch.dict("os.environ", SETTINGS, clear=True),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    async def asyncTearDown(self):
        self.widget.close()
        if self.widget._task:
            await asyncio.gather(self.widget._task, return_exceptions=True)

    def message(self, kind, buffers=(), run_id="test-run"):
        self.widget._message(self.widget, {"type": kind, "run_id": run_id}, buffers)

    def events(self, kind):
        return [c.args[0] for c in self.widget.send.call_args_list if c.args[0]["type"] == kind]

    async def until(self, predicate):
        async def wait():
            while not predicate():
                await asyncio.sleep(0)
        await asyncio.wait_for(wait(), 2)

    async def start(self):
        self.message("start")
        await self.until(lambda: self.events("ready") or self.widget._task.done())
        self.assertTrue(self.events("ready"), self.events("error"))

    async def finish(self):
        self.message("stop")
        await asyncio.wait_for(self.widget._task, 2)

    def test_rendering_is_offline_and_state_contains_no_private_data(self):
        self.connection.assert_not_called()
        self.assertIsNone(self.widget._task)
        self.widget.transcript = "private caption"
        state = json.dumps(self.widget.get_state())
        self.assertNotIn("private-test-key", state)
        self.assertNotIn("private caption", state)
        self.assertNotIn("test-streaming", state)

    def test_endpoint_rejects_credentials_and_other_hosts(self):
        self.assertEqual(
            live.realtime_url(SETTINGS["AZURE_MAI_ENDPOINT"] + "/"),
            "wss://offline.services.ai.azure.com/mai/v1/realtime?intent=transcription",
        )
        for endpoint in (
            "", "http://offline.services.ai.azure.com", "https://example.com",
            "https://offline.services.ai.azure.com.evil.example",
            "https://user:secret@offline.services.ai.azure.com",
            "https://offline.services.ai.azure.com?api-key=secret",
            "https://offline.services.ai.azure.com/#secret",
            "https://offline.services.ai.azure.com/project",
            "https://offline.cognitiveservices.azure.com",
            "https://offline.services.ai.azure.com:1234",
            "https://[invalid",
        ):
            with self.subTest(endpoint=endpoint), self.assertRaises(live.CaptionError) as caught:
                live.realtime_url(endpoint)
            self.assertNotIn("secret", str(caught.exception))

    async def test_handshake_pcm_commit_and_completion(self):
        await self.start()
        self.assertEqual(self.socket.sent[0]["type"], "session.update")
        config = self.socket.sent[0]["session"]["audio"]["input"]
        self.assertEqual(config, {
            "format": {"type": "audio/pcm", "rate": 16000},
            "transcription": {"model": "test-streaming", "language": None},
            "turn_detection": None, "noise_reduction": None,
        })
        self.assertEqual(self.connection.call_args.kwargs["additional_headers"], {"api-key": "private-test-key"})
        self.assertNotIn("private-test-key", self.connection.call_args.args[0])
        audio = b"\x01\x00" * 320
        tail = b"\x02\x00" * 3
        self.message("audio", [memoryview(audio)])
        self.message("audio", [memoryview(tail)])
        await self.finish()
        self.assertEqual([m["type"] for m in self.socket.sent], [
            "session.update", "input_audio_buffer.append", "input_audio_buffer.append",
            "input_audio_buffer.commit",
        ])
        self.assertEqual(base64.b64decode(self.socket.sent[1]["audio"]), audio)
        self.assertEqual(base64.b64decode(self.socket.sent[2]["audio"]), tail)
        self.assertEqual(len(self.events("ack")), 2)
        self.assertEqual(self.widget.transcript, "Hello there!")
        self.assertTrue(self.events("closed")[-1]["complete"])
        self.assertTrue(self.socket.closed)
        self.assertIsNone(self.widget._queue)

    async def test_intermediate_replacement_exact_deltas_and_no_duplicate_final(self):
        await self.start()
        self.message("audio", [b"\x00\x00"])
        for field, text in (
            ("delta", "Hello"), ("intermediate", " world"),
            ("intermediate", " there"), ("delta", " there!"),
        ):
            self.socket.events.put_nowait({"type": live.EVENT_PREFIX + field, field: text})
        await self.until(lambda: len(self.events("caption")) == 4)
        self.assertEqual(
            [(e["final"], e["partial"]) for e in self.events("caption")],
            [("Hello", ""), ("Hello", " world"), ("Hello", " there"), ("Hello there!", "")],
        )
        await self.finish()
        self.assertEqual(self.widget.transcript, "Hello there!")

    async def test_commit_ack_does_not_complete_and_timeout_is_visible(self):
        self.socket.complete = False
        with patch.object(live, "FINALIZE_SECONDS", 0.02):
            await self.start()
            self.message("audio", [b"\x00\x00"])
            await self.finish()
        self.assertFalse(self.events("finished"))
        self.assertIn("timed out", self.events("error")[-1]["message"])
        self.assertFalse(self.events("closed")[-1]["complete"])
        self.assertTrue(self.socket.closed)

    async def test_service_errors_and_disconnects_are_sanitized(self):
        for event in (
            {"type": "error", "error": {"message": "private-test-key"}},
            {"type": live.EVENT_PREFIX + "failed", "error": "private-test-key"},
            OSError("private-test-key"),
            {"type": live.EVENT_PREFIX + "delta", "delta": None},
            ["private-test-key"],
        ):
            self.socket = FakeSocket()
            self.connection.return_value = self.socket
            self.widget.send.reset_mock()
            await self.start()
            self.socket.events.put_nowait(event)
            await asyncio.wait_for(self.widget._task, 2)
            self.assertTrue(self.events("error"))
            self.assertNotIn("private-test-key", str(self.widget.send.call_args_list))
            self.assertTrue(self.socket.closed)

    async def test_empty_capture_does_not_commit_or_wait_for_final(self):
        await self.start()
        await self.finish()
        self.assertEqual([e["type"] for e in self.socket.sent], ["session.update"])
        self.assertEqual(self.events("finished")[-1]["text"], "")

    async def test_overflow_cancels_instead_of_silently_dropping_audio(self):
        await self.start()
        for _ in range(live.QUEUE_SIZE + 1):
            self.message("audio", [b"\x00\x00"])
        await asyncio.wait_for(self.widget._task, 2)
        self.assertIn("buffering", self.events("error")[-1]["message"])
        self.assertIsNone(self.widget._queue)
        self.assertTrue(self.socket.closed)

    async def test_stop_has_reserved_queue_capacity(self):
        await self.start()
        for _ in range(live.QUEUE_SIZE):
            self.message("audio", [b"\x00\x00"])
        await self.finish()
        self.assertEqual(len(self.events("ack")), live.QUEUE_SIZE)
        self.assertTrue(self.events("finished"))

    async def test_invalid_pcm_is_rejected(self):
        for buffers in ([], [b"x"], [b""], [b"x" * 642], [b"xx", b"xx"], ["xx"]):
            self.socket = FakeSocket()
            self.connection.return_value = self.socket
            self.widget.send.reset_mock()
            await self.start()
            self.message("audio", buffers)
            await asyncio.wait_for(self.widget._task, 2)
            self.assertIn("Invalid microphone", self.events("error")[-1]["message"])

    async def test_heartbeat_both_directions_and_browser_loss(self):
        await self.start()
        self.message("ping")
        self.assertTrue(self.events("pong"))
        with patch.object(live, "HEARTBEAT_SECONDS", -1):
            await asyncio.wait_for(self.widget._task, 2)
        self.assertIn("Browser connection lost", self.events("error")[-1]["message"])
        self.assertTrue(self.socket.closed)

    async def test_repeated_start_stale_messages_and_new_session(self):
        await self.start()
        task = self.widget._task
        self.message("start", run_id="other-view")
        self.assertIs(self.widget._task, task)
        self.assertEqual(self.events("error")[-1]["run_id"], "other-view")
        self.message("abort", run_id="old-run")
        self.assertFalse(task.done())
        await self.finish()
        self.socket = FakeSocket()
        self.connection.return_value = self.socket
        self.widget.send.reset_mock()
        await self.start()
        self.assertIsNot(self.widget._task, task)
        self.assertEqual(self.widget.transcript, "")
        await self.finish()

    async def test_close_cancels_handshake_and_closes_socket(self):
        self.socket.events = asyncio.Queue()
        self.message("start")
        await self.until(lambda: self.connection.called)
        self.widget.close()
        await asyncio.wait_for(self.widget._task, 2)
        self.assertTrue(self.socket.closed)

    async def test_repeated_abort_cannot_interrupt_cleanup(self):
        await self.start()
        self.message("abort")
        self.message("abort")
        self.message("audio", [b"\x00\x00"])
        await asyncio.wait_for(self.widget._task, 2)
        self.assertTrue(self.socket.closed)
        self.assertIsNone(self.widget._queue)
        self.assertEqual(len(self.events("closed")), 1)

    async def test_audio_duration_limit_is_enforced_in_kernel(self):
        await self.start()
        with patch.object(live, "RECORDING_SECONDS", 0):
            self.message("audio", [b"\x00\x00"])
            await asyncio.wait_for(self.widget._task, 2)
        self.assertIn("audio limit", self.events("error")[-1]["message"])
        self.assertFalse(self.events("finished"))

    async def test_stop_during_handshake_and_handshake_timeout(self):
        self.socket.events = asyncio.Queue()
        with patch.object(live, "HANDSHAKE_SECONDS", 0.02):
            self.message("start")
            self.message("stop")
            await asyncio.wait_for(self.widget._task, 2)
        self.assertTrue(self.events("error"))
        self.assertFalse(self.events("ready"))
        self.assertTrue(self.socket.closed)

    async def test_configuration_does_not_reuse_file_credentials(self):
        with patch.dict("os.environ", {"SPEECH_KEY": "file-only-secret"}, clear=True):
            self.message("start")
            await asyncio.wait_for(self.widget._task, 2)
        self.connection.assert_not_called()
        self.assertIn("AZURE_MAI_ENDPOINT", self.events("error")[-1]["message"])

    async def test_authentication_uses_only_selected_streaming_credential(self):
        credential = AsyncMock()
        credential.__aenter__.return_value = credential
        credential.get_token.return_value = SimpleNamespace(token="private-entra-token")
        with patch.object(live, "AzureCliCredential", return_value=credential) as factory:
            self.assertEqual(await live.auth_headers(SETTINGS), {"api-key": "private-test-key"})
            factory.assert_not_called()
            self.assertEqual(
                await live.auth_headers({"SPEECH_KEY": "file-key"}),
                {"Authorization": "Bearer private-entra-token"},
            )
        credential.get_token.assert_awaited_once_with("https://cognitiveservices.azure.com/.default")
        credential.__aexit__.assert_awaited_once()

    async def test_dotenv_refresh_and_environment_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(Path, "cwd", return_value=Path(directory)):
                with patch.object(live, "dotenv_values", return_value={**SETTINGS, "AZURE_MAI_API_KEY": "dotenv-key"}) as dotenv:
                    await self.start()
                    dotenv.assert_called_once_with(Path(directory) / ".env")
                    self.assertEqual(self.connection.call_args.kwargs["additional_headers"]["api-key"], "private-test-key")
                    await self.finish()


class RedirectTests(unittest.TestCase):
    def test_redirects_are_never_followed(self):
        error = ValueError("redirect")
        self.assertIs(live.NoRedirectConnect.process_redirect(None, error), error)


if __name__ == "__main__":
    unittest.main()
