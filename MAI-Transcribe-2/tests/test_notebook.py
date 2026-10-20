import ast
import copy
import io
import json
import sys
import tempfile
import types
import unittest
import wave
from pathlib import Path
from unittest.mock import Mock, patch

import nbformat
import requests
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "demo.ipynb"
RESPONSE = {
    "durationMilliseconds": 2000,
    "combinedPhrases": [{"text": "Welcome Amy. Goedemorgen."}],
    "phrases": [
        {
            "speaker": 0,
            "locale": "en",
            "offsetMilliseconds": 100,
            "durationMilliseconds": 800,
            "text": "Welcome Amy.",
            "words": [
                {"text": "Welcome", "offsetMilliseconds": 100, "durationMilliseconds": 300},
                {"text": "Amy.", "offsetMilliseconds": 400, "durationMilliseconds": 500},
            ],
        },
        {
            "speaker": 1,
            "locale": "nl",
            "offsetMilliseconds": 1000,
            "durationMilliseconds": 700,
            "text": "Goedemorgen.",
            "words": [
                {"text": "Goedemorgen.", "offsetMilliseconds": 1000, "durationMilliseconds": 700},
            ],
        },
    ],
}


def make_wav(path, channels=1, frames=32000):
    with wave.open(str(path), "wb") as output:
        output.setnchannels(channels)
        output.setsampwidth(2)
        output.setframerate(16000)
        output.writeframes(b"\x00\x00" * frames * channels)


class NotebookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.notebook = nbformat.read(NOTEBOOK, as_version=4)
        cls.demo = types.ModuleType("transcribe_notebook_under_test")
        sys.modules[cls.demo.__name__] = cls.demo
        for cell in cls.notebook.cells:
            if cell.cell_type == "code" and set(cell.metadata.get("tags", [])) & {
                "demo-imports", "demo-helpers"
            }:
                exec(compile(cell.source, str(NOTEBOOK), "exec"), cls.demo.__dict__)
        cls.demo.SPEECH_ENDPOINT = "https://demo.cognitiveservices.azure.com"
        cls.demo.SETTINGS = {}
        cls.demo._credential = None

    @classmethod
    def tearDownClass(cls):
        del sys.modules[cls.demo.__name__]

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.audio = Path(self.temp.name) / "sample.wav"
        make_wav(self.audio)

    def response_mock(self, status=200, payload=None):
        response = Mock()
        response.status_code = status
        response.json.return_value = copy.deepcopy(RESPONSE if payload is None else payload)
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        return response

    def test_notebook_is_valid_and_has_no_saved_outputs(self):
        nbformat.validate(self.notebook)
        self.assertNotIn("widgets", self.notebook.metadata)
        self.assertNotIn("data:audio", NOTEBOOK.read_text())
        for cell in self.notebook.cells:
            self.assertFalse(cell.get("attachments"))
            for setting in ("RUN_COMPARISONS", "EXPORT_RESULTS", "AUTH_MODE", "DUTCH_AUDIO_PATH"):
                self.assertNotIn(setting, cell.source)
            if cell.cell_type == "code":
                self.assertIsNone(cell.execution_count)
                self.assertEqual(cell.outputs, [])
                compile(cell.source, str(NOTEBOOK), "exec")

    def run_configuration(self, environment):
        configuration = next(
            cell for cell in self.notebook.cells if cell.id == "configuration"
        )
        namespace = dict(self.demo.__dict__)
        captured = io.StringIO()
        with patch.dict("os.environ", environment, clear=True):
            with patch.object(Path, "cwd", return_value=Path(self.temp.name)):
                with patch("sys.stdout", captured):
                    exec(configuration.source, namespace)
        return namespace, captured.getvalue()

    def test_dotenv_loads_before_configuration_without_printing_secrets(self):
        (Path(self.temp.name) / ".env").write_text(
            "SPEECH_ENDPOINT=https://dotenv.cognitiveservices.azure.com\n"
            "SPEECH_KEY=offline-dotenv-secret\n"
            'AUDIO_FILE="samples/dutch meeting.wav"\n',
            encoding="utf-8",
        )
        configuration, output = self.run_configuration({})
        self.assertEqual(
            configuration["SPEECH_ENDPOINT"], "https://dotenv.cognitiveservices.azure.com"
        )
        self.assertEqual(configuration["SETTINGS"]["SPEECH_KEY"], "offline-dotenv-secret")
        self.assertEqual(configuration["AUDIO_PATH"], Path("samples/dutch meeting.wav"))
        self.assertNotIn("offline-dotenv-secret", output)

    def test_configuration_has_only_connection_and_main_recording_settings(self):
        source = next(c.source for c in self.notebook.cells if c.id == "configuration")
        assignments = {
            node.targets[0].id for node in ast.parse(source).body
            if isinstance(node, ast.Assign)
        }
        self.assertEqual(assignments, {"SETTINGS", "SPEECH_ENDPOINT", "AUDIO_PATH"})

    def test_recording_path_is_explicit_without_automatic_file_selection(self):
        samples = Path(self.temp.name) / "samples"
        samples.mkdir()
        for locale in ("en", "nl"):
            make_wav(samples / f"meeting-{locale}.wav")
        configuration, _ = self.run_configuration({})
        self.assertEqual(configuration["AUDIO_PATH"], Path("samples/a-bit-of-ai-en.wav"))
        for name in ("meeting-en.wav", "my-episode.wav"):
            configuration, _ = self.run_configuration({"AUDIO_FILE": f"samples/{name}"})
            self.assertEqual(configuration["AUDIO_PATH"], Path(f"samples/{name}"))

    def test_podcast_keywords_and_editorial_story(self):
        cells = {cell.id: cell for cell in self.notebook.cells}
        keywords = ast.literal_eval(ast.parse(cells["keywords"].source).body[0].value)
        self.assertEqual(keywords, [
            "A Bit of AI", "Henk Boelman", "Amy", "Microsoft Foundry", "MAI-Transcribe", "AgentCon",
        ])
        instructions = (ROOT / "demo-instructions.md").read_text()
        for term in keywords:
            self.assertIn(term, instructions)
        self.assertIn("A Bit of AI", cells["intro"].source)
        self.assertIn("anonymous", cells["inspect-heading"].source.lower())
        self.assertIn("not a summary", cells["styles-heading"].source)
        self.assertIn("the baseline only", cells["export-heading"].source)
        self.assertIn("../MAI-Voice-2.1/demo.ipynb", cells["wrap-up"].source)

    def test_dotenv_preserves_existing_environment(self):
        (Path(self.temp.name) / ".env").write_text(
            "SPEECH_ENDPOINT=https://dotenv.cognitiveservices.azure.com\n"
            "SPEECH_KEY=offline-dotenv-secret\n"
            "AUDIO_FILE=samples/dotenv.wav\n",
            encoding="utf-8",
        )
        configuration, _ = self.run_configuration({
            "SPEECH_ENDPOINT": "https://environment.cognitiveservices.azure.com",
            "SPEECH_KEY": "",
            "AUDIO_FILE": "samples/environment.wav",
        })
        self.assertEqual(
            configuration["SPEECH_ENDPOINT"], "https://environment.cognitiveservices.azure.com"
        )
        self.assertEqual(configuration["SETTINGS"]["SPEECH_KEY"], "")
        self.assertEqual(configuration["AUDIO_PATH"], Path("samples/environment.wav"))

    def test_dotenv_edits_take_effect_without_kernel_restart(self):
        env_path = Path(self.temp.name) / ".env"
        configuration_cell = next(
            cell for cell in self.notebook.cells if cell.id == "configuration"
        )
        namespace = dict(self.demo.__dict__)
        with patch.dict("os.environ", {}, clear=True):
            with patch.object(Path, "cwd", return_value=Path(self.temp.name)):
                with patch("sys.stdout", io.StringIO()):
                    for value in ("first", "second"):
                        env_path.write_text(
                            f"SPEECH_ENDPOINT=https://{value}.cognitiveservices.azure.com\n"
                            f"SPEECH_KEY={value}-offline-key\n",
                            encoding="utf-8",
                        )
                        exec(configuration_cell.source, namespace)
                        self.assertEqual(
                            namespace["SPEECH_ENDPOINT"],
                            f"https://{value}.cognitiveservices.azure.com",
                        )
                        self.assertEqual(namespace["SETTINGS"]["SPEECH_KEY"], f"{value}-offline-key")
                        self.assertNotIn("SPEECH_KEY", self.demo.os.environ)

    def test_authentication_uses_current_notebook_settings(self):
        with patch.object(self.demo, "SETTINGS", {"SPEECH_KEY": "updated-offline-key"}):
            self.assertEqual(
                self.demo.auth_headers(),
                {"Ocp-Apim-Subscription-Key": "updated-offline-key"},
            )

    def test_dotenv_is_optional_and_does_not_search_parent_directories(self):
        parent = Path(self.temp.name)
        (parent / ".env").write_text(
            "SPEECH_ENDPOINT=https://parent.cognitiveservices.azure.com\n"
            "SPEECH_KEY=parent-secret\n",
            encoding="utf-8",
        )
        child = parent / "notebook"
        child.mkdir()
        configuration_cell = next(
            cell for cell in self.notebook.cells if cell.id == "configuration"
        )
        namespace = dict(self.demo.__dict__)
        with patch.dict("os.environ", {}, clear=True):
            with patch.object(Path, "cwd", return_value=child):
                with patch("sys.stdout", io.StringIO()):
                    exec(configuration_cell.source, namespace)
        self.assertEqual(namespace["SPEECH_ENDPOINT"], "")
        self.assertNotIn("SPEECH_KEY", namespace["SETTINGS"])
        self.assertEqual(namespace["AUDIO_PATH"], Path("samples/a-bit-of-ai-en.wav"))

    def test_endpoint_rejects_unsafe_or_wrong_resource_urls(self):
        self.assertEqual(
            self.demo.resource_endpoint("https://demo.cognitiveservices.azure.com/"),
            "https://demo.cognitiveservices.azure.com",
        )
        for endpoint in [
            "", "http://demo.cognitiveservices.azure.com",
            "https://example.com", "https://demo.cognitiveservices.azure.com.evil.example",
            "https://user:secret@demo.cognitiveservices.azure.com",
            "https://demo.cognitiveservices.azure.com/projects/project",
            "https://demo.cognitiveservices.azure.com?key=secret",
            "https://demo.cognitiveservices.azure.com#fragment",
            "https://demo.cognitiveservices.azure.com:8080",
        ]:
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                self.demo.resource_endpoint(endpoint)

    def test_audio_validation(self):
        self.assertEqual(self.demo.validate_audio(self.audio), self.audio)
        with self.assertRaises(FileNotFoundError):
            self.demo.validate_audio(self.audio.with_name("missing.wav"))
        invalid = self.audio.with_name("bad.wav")
        invalid.write_bytes(b"not a wave file")
        with self.assertRaises(ValueError):
            self.demo.validate_audio(invalid)
        empty = self.audio.with_name("empty.wav")
        make_wav(empty, frames=0)
        with self.assertRaises(ValueError):
            self.demo.validate_audio(empty)
        stereo = self.audio.with_name("stereo.wav")
        make_wav(stereo, channels=2)
        with self.assertRaises(ValueError):
            self.demo.validate_audio(stereo)
        with patch.object(self.demo, "MAX_DEMO_BYTES", 10), self.assertRaises(ValueError):
            self.demo.validate_audio(self.audio)

    def test_configuration_and_hints(self):
        definition = self.demo.request_definition(phrases=["Contoso"])
        self.assertEqual(definition["enhancedMode"]["model"], "MAI-Transcribe-2")
        self.assertTrue(definition["enhancedMode"]["enabled"])
        self.assertEqual(definition["enhancedMode"]["modelOptions"]["timestamps"], "word")
        self.assertEqual(definition["phraseList"]["phrases"], ["Contoso"])
        self.assertNotIn("locales", definition)
        self.assertNotIn("phraseList", self.demo.request_definition())
        with self.assertRaises(ValueError):
            self.demo.request_definition(style="summary")
        with self.assertRaises(ValueError):
            self.demo.request_definition(phrases=[" "])

    def test_configured_key_does_not_acquire_cli_credentials(self):
        with patch.object(self.demo, "SETTINGS", {"SPEECH_KEY": " test-secret "}):
            with patch("azure.identity.AzureCliCredential") as credential:
                self.assertEqual(
                    self.demo.auth_headers(), {"Ocp-Apim-Subscription-Key": "test-secret"}
                )
                credential.assert_not_called()

    def test_entra_credential_scope(self):
        credential = Mock()
        credential.get_token.return_value.token = "offline-token"
        with patch.object(self.demo, "SETTINGS", {"SPEECH_KEY": ""}):
            with patch.object(self.demo, "_credential", credential):
                self.assertEqual(
                    self.demo.auth_headers(), {"Authorization": "Bearer offline-token"}
                )
        credential.get_token.assert_called_once_with(
            "https://cognitiveservices.azure.com/.default"
        )

    def test_successful_request_and_closed_audio(self):
        sent = {}

        def post(url, **kwargs):
            sent.update(kwargs)
            self.assertEqual(
                url,
                "https://demo.cognitiveservices.azure.com/speechtotext/transcriptions:transcribe",
            )
            self.assertGreater(len(kwargs["files"]["audio"][1].read()), 0)
            return self.response_mock()

        definition = self.demo.request_definition()
        with patch.object(self.demo, "auth_headers", return_value={"test": "secret"}):
            with patch.object(requests, "post", side_effect=post) as mocked:
                run = self.demo.transcribe(self.audio, definition)
        mocked.assert_called_once()
        self.assertTrue(sent["files"]["audio"][1].closed)
        self.assertEqual(sent["params"], {"api-version": "2025-10-15"})
        self.assertEqual(sent["timeout"], (10, 180))
        self.assertFalse(sent["allow_redirects"])
        self.assertEqual(json.loads(sent["data"]["definition"]), definition)
        self.assertEqual(run.text, RESPONSE["combinedPhrases"][0]["text"])
        definition["enhancedMode"]["model"] = "changed"
        self.assertEqual(run.definition["enhancedMode"]["model"], "MAI-Transcribe-2")
        self.assertGreaterEqual(run.elapsed_seconds, 0)

    def test_preflight_failure_makes_no_request(self):
        with patch.object(requests, "post") as mocked:
            with self.assertRaises(FileNotFoundError):
                self.demo.transcribe(self.audio.with_name("missing.wav"), {})
        mocked.assert_not_called()

    def test_http_errors_do_not_retry_or_leak_response_body(self):
        for status in [302, 400, 401, 403, 404, 413, 429, 500]:
            response = self.response_mock(status=status)
            response.text = "sensitive transcript and key"
            with self.subTest(status=status):
                with patch.object(self.demo, "auth_headers", return_value={}):
                    with patch.object(requests, "post", return_value=response) as mocked:
                        with self.assertRaisesRegex(RuntimeError, f"HTTP {status}") as caught:
                            self.demo.transcribe(self.audio, self.demo.request_definition())
                self.assertNotIn("sensitive", str(caught.exception))
                mocked.assert_called_once()

    def test_timeout_and_invalid_json(self):
        with patch.object(self.demo, "auth_headers", return_value={}):
            with patch.object(requests, "post", side_effect=requests.Timeout("secret")) as mocked:
                with self.assertRaisesRegex(RuntimeError, "may still have been billed") as caught:
                    self.demo.transcribe(self.audio, {})
                self.assertNotIn("secret", str(caught.exception))
                mocked.assert_called_once()
            response = self.response_mock()
            response.json.side_effect = ValueError("not JSON")
            with patch.object(requests, "post", return_value=response):
                with self.assertRaisesRegex(RuntimeError, "not valid JSON"):
                    self.demo.transcribe(self.audio, {})

    def test_response_validation_and_silence(self):
        self.demo.validate_result(RESPONSE)
        self.demo.validate_result({"combinedPhrases": [], "phrases": []})
        for payload in [
            [], {}, {"combinedPhrases": [{"text": None}]},
            {"combinedPhrases": [], "phrases": None},
            {"combinedPhrases": [], "durationMilliseconds": -1},
            {"combinedPhrases": [], "durationMilliseconds": True},
            {"combinedPhrases": [], "durationMilliseconds": float("inf")},
            {"combinedPhrases": [], "phrases": [{"text": "test", "words": [None]}]},
            {"combinedPhrases": [], "phrases": [{"text": "test", "offsetMilliseconds": "0"}]},
        ]:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                self.demo.validate_result(payload)

    def test_tables_preserve_speaker_zero_and_missing_fields(self):
        run = self.demo.TranscriptionRun(self.audio, {}, copy.deepcopy(RESPONSE), 0.1)
        segments, words = self.demo.transcript_tables(run)
        self.assertEqual(list(segments.speaker), [0, 1])
        self.assertEqual(words.iloc[0].start_s, 0.1)
        self.assertEqual(words.iloc[1].duration_s, 0.5)
        run.response = {"combinedPhrases": [{"text": "test"}], "phrases": [{"text": "test"}]}
        segments, words = self.demo.transcript_tables(run)
        self.assertIsNone(segments.iloc[0].speaker)
        self.assertIsNone(segments.iloc[0].start_s)
        self.assertTrue(words.empty)
        self.assertIn("start_s", words.columns)

    def test_wav_excerpt_frame_boundaries(self):
        excerpt = self.demo.wav_excerpt(self.audio, 0.25, 0.75)
        with wave.open(io.BytesIO(excerpt), "rb") as result:
            self.assertEqual(result.getnframes(), 8000)
            self.assertEqual(result.getframerate(), 16000)
            self.assertEqual(result.getnchannels(), 1)
        with wave.open(io.BytesIO(self.demo.wav_excerpt(self.audio, 1.5, 3.0)), "rb") as result:
            self.assertEqual(result.getnframes(), 8000)
        for start, end in [(-1, 1), (0, 0), (3, 4), (0, float("nan"))]:
            with self.subTest(interval=(start, end)), self.assertRaises(ValueError):
                self.demo.wav_excerpt(self.audio, start, end)

    def test_exports_are_unique_utf8_and_contain_no_credentials(self):
        payload = copy.deepcopy(RESPONSE)
        payload["combinedPhrases"] = [{"text": "Café in Nederland."}]
        run = self.demo.TranscriptionRun(
            self.audio, self.demo.request_definition(), payload, 0.25
        )
        root = Path(self.temp.name) / "exports"
        first = self.demo.export_run(run, root)
        second = self.demo.export_run(run, root)
        self.assertNotEqual(first, second)
        self.assertEqual(
            (first / "transcript.txt").read_text(encoding="utf-8"), run.text
        )
        metadata = json.loads((first / "run.json").read_text(encoding="utf-8"))
        self.assertEqual(set(metadata), {
            "model", "request_definition", "elapsed_seconds", "exported_at"
        })
        self.assertEqual(
            json.loads((first / "response.json").read_text(encoding="utf-8")), payload
        )

    def test_full_notebook_executes_offline(self):
        self.execute_notebook(comparisons=True, dutch=True, exports=True)

    def test_core_demo_cells_execute_offline(self):
        self.execute_notebook(comparisons=True, dutch=False, exports=False)

    def test_one_request_notebook_handles_no_speech(self):
        self.execute_notebook(
            comparisons=False,
            dutch=False,
            exports=False,
            payload={"durationMilliseconds": 2000, "combinedPhrases": [], "phrases": []},
        )

    def execute_notebook(self, comparisons, dutch, exports, payload=None):
        payload = RESPONSE if payload is None else payload
        notebook = copy.deepcopy(self.notebook)
        skipped = set()
        if not comparisons:
            skipped.update({"styles", "keywords"})
        if not dutch:
            skipped.add("dutch")
        if not exports:
            skipped.add("export")
        notebook.cells = [cell for cell in notebook.cells if cell.id not in skipped]
        samples = Path(self.temp.name) / "samples"
        samples.mkdir()
        make_wav(samples / "a-bit-of-ai-en.wav")
        make_wav(samples / "a-bit-of-ai-nl.wav")
        setup = nbformat.v4.new_code_cell(
            "SPEECH_ENDPOINT = 'https://offline.cognitiveservices.azure.com'\n"
            "SETTINGS['SPEECH_KEY'] = 'offline-test-key'\n"
            "recorded_requests = []\n"
            f"fixture_response = {payload!r}\n"
            "class OfflineResponse:\n"
            "    status_code = 200\n"
            "    def __enter__(self): return self\n"
            "    def __exit__(self, *args): return False\n"
            "    def json(self): return copy.deepcopy(fixture_response)\n"
            "def offline_post(url, **kwargs):\n"
            "    assert kwargs['files']['audio'][1].read(4) == b'RIFF'\n"
            "    recorded_requests.append(json.loads(kwargs['data']['definition']))\n"
            "    return OfflineResponse()\n"
            "def forbid_network(*args, **kwargs):\n"
            "    raise AssertionError('Live network requests are forbidden in offline tests')\n"
            "requests.sessions.Session.request = forbid_network\n"
            "requests.post = offline_post\n"
        )
        config_index = next(
            i for i, cell in enumerate(notebook.cells) if cell.id == "configuration"
        )
        notebook.cells.insert(config_index + 1, setup)
        notebook.cells.append(nbformat.v4.new_code_cell(
            f"assert len(recorded_requests) == {1 + 2 * comparisons + dutch}\n"
            "assert recorded_requests[0]['enhancedMode']['model'] == 'MAI-Transcribe-2'\n"
            "assert 'phraseList' not in recorded_requests[0]\n"
            f"if {comparisons!r}:\n"
            "    assert recorded_requests[1]['enhancedMode']['modelOptions']['transcribeStyle'] == 'clean'\n"
            "    assert recorded_requests[2]['phraseList']['phrases'] == keywords\n"
            "    assert clean is not None and hinted is not None\n"
            "else:\n"
            "    assert 'clean' not in globals() and 'hinted' not in globals()\n"
            f"if {dutch!r}:\n"
            "    assert 'locales' not in recorded_requests[-1] and dutch is not None\n"
            "else:\n"
            "    assert 'dutch' not in globals()\n"
            f"assert len(words) == {sum(len(segment.get('words', [])) for segment in payload['phrases'])}\n"
            f"if {exports!r}:\n"
            "    assert (export_directory / 'response.json').is_file()\n"
            "else:\n"
            "    assert not Path('outputs').exists()\n"
        ))
        # Use the same environment as the test runner, not an unrelated global kernel.
        from ipykernel.kernelspec import install
        kernel_prefix = Path(self.temp.name) / "kernel"
        install(prefix=str(kernel_prefix), kernel_name="mai-offline-test")
        with patch.dict("os.environ", {
            "JUPYTER_PATH": str(kernel_prefix / "share" / "jupyter"),
            "AUDIO_FILE": str(samples / "a-bit-of-ai-en.wav"),
        }):
            NotebookClient(
                notebook,
                timeout=60,
                kernel_name="mai-offline-test",
                resources={"metadata": {"path": self.temp.name}},
            ).execute()


if __name__ == "__main__":
    unittest.main()
