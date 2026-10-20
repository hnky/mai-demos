"""Standalone browser audio -> notebook kernel -> MAI-Transcribe-2-Streaming."""

import asyncio
import base64
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlsplit

import anywidget
from azure.core.exceptions import AzureError
from azure.identity.aio import AzureCliCredential
from dotenv import dotenv_values
from websockets.asyncio.client import connect
from websockets.exceptions import WebSocketException


SAMPLE_RATE = 16000
CHUNK_BYTES = 640  # 20 ms of mono PCM16.
QUEUE_SIZE = 50
RECORDING_SECONDS = 300
HANDSHAKE_SECONDS = 30
FINALIZE_SECONDS = 30
HEARTBEAT_SECONDS = 8
EVENT_PREFIX = "conversation.item.input_audio_transcription."


class CaptionError(Exception):
    """An intentionally public error message, without service payloads."""


class NoRedirectConnect(connect):
    def process_redirect(self, exc):
        # Do not forward authentication headers to a redirected resource.
        return exc


def realtime_url(endpoint):
    try:
        parts = urlsplit(endpoint.strip())
        valid = (
            parts.scheme == "https"
            and re.fullmatch(r"[a-zA-Z0-9-]+\.services\.ai\.azure\.com", parts.hostname or "")
            and parts.port in (None, 443)
            and parts.username is None
            and parts.password is None
            and parts.path in ("", "/")
            and not parts.query
            and not parts.fragment
        )
    except ValueError:
        valid = False
    if not valid:
        raise CaptionError(
            "Set AZURE_MAI_ENDPOINT to the HTTPS services.ai.azure.com resource root, "
            "not the file-transcription endpoint or a project URL."
        )
    return f"wss://{parts.hostname}/mai/v1/realtime?intent=transcription"


async def auth_headers(settings):
    key = (settings.get("AZURE_MAI_API_KEY") or "").strip()
    if key:
        return {"api-key": key}
    async with AzureCliCredential() as credential:
        token = await credential.get_token("https://cognitiveservices.azure.com/.default")
        return {"Authorization": f"Bearer {token.token}"}


async def receive_event(ws):
    try:
        event = json.loads(await ws.recv())
    except (ValueError, UnicodeDecodeError):
        raise CaptionError("Azure returned an invalid streaming message.") from None
    if not isinstance(event, dict) or not isinstance(event.get("type"), str):
        raise CaptionError("Azure returned an invalid streaming message.")
    if event["type"] in ("error", EVENT_PREFIX + "failed"):
        raise CaptionError(
            "Azure rejected the streaming request. Check the streaming resource, "
            "deployment, permissions, quota, and service health."
        )
    return event


async def wait_for_event(ws, event_type):
    async def wait():
        while (await receive_event(ws))["type"] != event_type:
            pass
    await asyncio.wait_for(wait(), HANDSHAKE_SECONDS)


async def cancel_tasks(*tasks):
    for task in tasks:
        if not task.done():
            task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


class LiveCaptions(anywidget.AnyWidget):
    """Rendering is offline. Only an explicit browser Start opens a session."""

    _esm = Path(__file__).with_suffix(".js")

    def __init__(self, **kwargs):
        self.transcript = ""
        self._partial = ""
        self._task = None
        self._run_id = None
        self._queue = None
        self._stopping = False
        self._committed = False
        self._ready = False
        self._aborting = False
        self._last_ping = 0.0
        self._abort_reason = "Session cancelled; the transcript may be incomplete."
        super().__init__(**kwargs)
        self.on_msg(self._message)

    def _emit(self, kind, **content):
        self.send({"type": kind, "run_id": self._run_id, **content})

    def _abort(self, message):
        if self._aborting:
            return
        self._aborting = True
        self._abort_reason = message
        if self._task is not None and not self._task.done():
            self._task.cancel()

    def _message(self, widget, content, buffers):
        if not isinstance(content, dict):
            return
        kind, run_id = content.get("type"), content.get("run_id")
        if not isinstance(run_id, str) or not 1 <= len(run_id) <= 100:
            return
        if kind == "start":
            if self._task is not None and not self._task.done():
                self.send({
                    "type": "error", "run_id": run_id,
                    "message": "Another caption session is active. Stop it before starting again.",
                })
                return
            self._run_id = run_id
            self.transcript = self._partial = ""
            # Reserve one queue slot for Stop, even when the audio queue is full.
            self._queue = asyncio.Queue(maxsize=QUEUE_SIZE + 1)
            self._stopping = self._committed = self._ready = False
            self._aborting = False
            self._last_ping = time.monotonic()
            self._task = asyncio.create_task(self._run())
            return
        if run_id != self._run_id or self._task is None or self._task.done() or self._aborting:
            return
        if kind == "ping":
            self._last_ping = time.monotonic()
            self._emit("pong")
        elif kind == "abort":
            self._abort("Browser capture stopped; the transcript may be incomplete.")
        elif kind == "stop" and not self._stopping:
            self._stopping = True
            self._queue.put_nowait(None)
        elif kind == "audio":
            if self._stopping or not self._ready:
                self._abort("Audio arrived outside the recording interval. Start a new session.")
            elif (
                len(buffers) != 1
                or not isinstance(buffers[0], (bytes, bytearray, memoryview))
                or not 0 < len(buffers[0]) <= CHUNK_BYTES
                or len(buffers[0]) % 2
            ):
                self._abort("Invalid microphone PCM frame. The session has been stopped.")
            elif self._queue.qsize() >= QUEUE_SIZE:
                self._abort("Audio buffering exceeded the demo limit. The transcript is incomplete.")
            else:
                self._queue.put_nowait(bytes(buffers[0]))

    async def _watch_browser(self):
        while True:
            await asyncio.sleep(1)
            if time.monotonic() - self._last_ping > HEARTBEAT_SECONDS:
                raise CaptionError("Browser connection lost. The transcript may be incomplete.")

    async def _run(self):
        session = asyncio.create_task(self._session())
        watchdog = asyncio.create_task(self._watch_browser())
        finished = False
        try:
            done, _ = await asyncio.wait(
                {session, watchdog},
                timeout=RECORDING_SECONDS + HANDSHAKE_SECONDS + FINALIZE_SECONDS,
                return_when=asyncio.FIRST_COMPLETED,
            )
            if not done:
                raise CaptionError("The demo session timed out; the transcript may be incomplete.")
            for task in done:
                task.result()
            finished = True
        except CaptionError as exc:
            self._emit("error", message=str(exc))
        except AzureError:
            self._emit("error", message="Azure authentication failed. Check the streaming key or az login and resource access.")
        except (OSError, WebSocketException, asyncio.TimeoutError):
            self._emit("error", message="Streaming connection failed or timed out. Check the endpoint, access, and network. The transcript may be incomplete.")
        except asyncio.CancelledError:
            self._emit("error", message=self._abort_reason)
        finally:
            await cancel_tasks(session, watchdog)
            self._ready = False
            # Release queued microphone bytes, including after failed/cancelled sends.
            self._queue = None
            self._emit("closed", complete=finished)

    async def _session(self):
        settings = {**dotenv_values(Path.cwd() / ".env"), **os.environ}
        url = realtime_url(settings.get("AZURE_MAI_ENDPOINT") or "")
        deployment = (settings.get("AZURE_MAI_DEPLOYMENT_NAME") or "").strip()
        if not deployment:
            raise CaptionError("Set AZURE_MAI_DEPLOYMENT_NAME to your deployed MAI-Transcribe-2-Streaming model.")
        headers = await asyncio.wait_for(auth_headers(settings), HANDSHAKE_SECONDS)
        async with NoRedirectConnect(
            url, additional_headers=headers, open_timeout=15, close_timeout=3,
            max_size=1024 * 1024, max_queue=16,
        ) as ws:
            await wait_for_event(ws, "session.created")
            await ws.send(json.dumps({
                "type": "session.update",
                "session": {
                    "type": "transcription",
                    "audio": {"input": {
                        "format": {"type": "audio/pcm", "rate": SAMPLE_RATE},
                        "transcription": {"model": deployment, "language": None},
                        "turn_detection": None,
                        "noise_reduction": None,
                    }},
                },
            }))
            await wait_for_event(ws, "session.updated")
            self._ready = True
            self._emit("ready", max_seconds=RECORDING_SECONDS)
            sender = asyncio.create_task(self._send_audio(ws))
            receiver = asyncio.create_task(self._receive_transcript(ws))
            try:
                done, _ = await asyncio.wait({sender, receiver}, return_when=asyncio.FIRST_COMPLETED)
                if receiver in done:
                    receiver.result()
                    if not self._committed:
                        raise CaptionError("Azure finalized before Stop; start a new session.")
                sent_audio = await sender
                if sent_audio:
                    # A commit acknowledgement is not a completed transcription.
                    await asyncio.wait_for(receiver, FINALIZE_SECONDS)
                self._emit("finished", text=self.transcript)
            finally:
                await cancel_tasks(sender, receiver)

    async def _send_audio(self, ws):
        total = 0
        while True:
            chunk = await self._queue.get()
            if chunk is None:
                break
            total += len(chunk)
            if total > SAMPLE_RATE * 2 * RECORDING_SECONDS:
                raise CaptionError("The five-minute demo audio limit was exceeded.")
            await ws.send(json.dumps({
                "type": "input_audio_buffer.append",
                "audio": base64.b64encode(chunk).decode("ascii"),
            }))
            self._emit("ack")
        if total:
            self._committed = True
            await ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
        return bool(total)

    async def _receive_transcript(self, ws):
        while True:
            event = await receive_event(ws)
            kind = event["type"]
            fields = {
                EVENT_PREFIX + "delta": "delta",
                EVENT_PREFIX + "intermediate": "intermediate",
                EVENT_PREFIX + "completed": "transcript",
            }
            if kind not in fields:
                continue
            text = event.get(fields[kind])
            if not isinstance(text, str):
                raise CaptionError("Azure returned an invalid caption.")
            if kind == EVENT_PREFIX + "delta":
                self.transcript += text
                self._partial = ""
            elif kind == EVENT_PREFIX + "intermediate":
                self._partial = text
            else:
                self.transcript = text
                self._partial = ""
            if len(self.transcript) + len(self._partial) > 100000:
                raise CaptionError("Caption text exceeded the demo limit.")
            self._emit("caption", final=self.transcript, partial=self._partial)
            if kind == EVENT_PREFIX + "completed":
                return

    def close(self):
        self._abort("Caption widget closed; the transcript may be incomplete.")
        super().close()
