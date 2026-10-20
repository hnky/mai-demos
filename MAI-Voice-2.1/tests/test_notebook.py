import ast
import io
import json
import sys
import tempfile
import unittest
import wave
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import Mock, patch

import nbformat
import requests
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import voice_demo as demo


def wav(seconds=1, rate=24000, channels=1, width=2):
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(channels)
        audio.setsampwidth(width)
        audio.setframerate(rate)
        audio.writeframes(b"\0" * int(seconds * rate * channels * width))
    return output.getvalue()


def response(body=b"", status=200):
    result = Mock()
    result.status_code = status
    result.iter_content.return_value = [body]
    result.__enter__ = Mock(return_value=result)
    result.__exit__ = Mock(return_value=False)
    return result


def json_response(payload, status=200):
    return response(json.dumps(payload).encode(), status)


class VoiceTests(unittest.TestCase):
    def setUp(self):
        self.settings = demo.Settings("westeurope", "offline-test-key",
                                      "https://demo.cognitiveservices.azure.com")
        self.session = Mock()
        self.client = demo.SpeechClient(self.settings, self.session)
        self.turns = [demo.Turn("Welcome to A Bit of AI.", "en-US-Harper")]
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def personal(self, approval=None):
        return demo.PersonalVoiceClient(
            self.settings, approval or demo.Approval(True, True, True, True), self.session)

    def test_configuration_fresh_local_and_environment_precedence(self):
        env = self.root / ".env"
        env.write_text("VOICE_SPEECH_REGION=westeurope\nVOICE_SPEECH_KEY=first\n")
        self.assertEqual(demo.Settings.load(self.root, {}).key, "first")
        env.write_text("VOICE_SPEECH_REGION=swedencentral\nVOICE_SPEECH_KEY=second\n")
        self.assertEqual(demo.Settings.load(self.root, {}).key, "second")
        settings = demo.Settings.load(self.root, {"VOICE_SPEECH_KEY": "override"})
        self.assertEqual(settings.key, "override")
        self.assertNotIn("override", repr(settings))
        child = self.root / "child"
        child.mkdir()
        self.assertEqual(demo.Settings.load(child, {}).key, "")

    def test_missing_configuration_and_transcription_key_do_not_send_requests(self):
        settings = demo.Settings.load(self.root, {"SPEECH_KEY": "not-a-voice-key"})
        with self.assertRaises(demo.DemoError):
            demo.SpeechClient(settings, self.session).synthesize(self.turns)
        self.session.request.assert_not_called()

    def test_xml_escapes_text_and_selects_exact_model(self):
        text = 'AI & agents <audio src="https://example.com"/>'
        data = demo.ssml([demo.Turn(text, "en-US-Harper", "excited")], demo.FLASH)
        root = ET.fromstring(data)
        voice = root.find(f"{{{demo.SPEECH_NS}}}voice")
        self.assertEqual(voice.attrib["name"], "en-US-Harper:MAI-Voice-2.1-Flash")
        style = voice.find(f"{{{demo.MSTTS_NS}}}express-as")
        self.assertEqual(style.text, text)
        self.assertEqual(style.attrib["style"], "excited")
        self.assertIsNone(root.find(".//audio"))

    def test_invalid_voice_style_text_and_limits_are_rejected(self):
        invalid = [
            [], [demo.Turn("", "en-US-Harper")],
            [demo.Turn("Hi", "en-US-Grant", "excited")],
            [demo.Turn("Hi", "en-US-Harper", "happiness")],
            [demo.Turn("Hi", "en-US-Unknown")],
            [demo.Turn("\x00", "en-US-Harper")],
            [demo.Turn("x" * 6001, "en-US-Harper")],
            self.turns * 51,
        ]
        for turns in invalid:
            with self.subTest(turns=turns), self.assertRaises(demo.DemoError):
                self.client.synthesize(turns)
        with self.assertRaises(demo.DemoError):
            demo.ssml(self.turns, "some-other-model")
        self.session.request.assert_not_called()

    def test_supplied_scripts_and_dialogue_casting(self):
        scripts = json.loads((ROOT / "scripts.json").read_text())
        self.assertEqual(len(scripts["dialogue"]), 14)
        self.assertEqual([row["speaker"] for row in scripts["dialogue"]], ["Henk", "Amy"] * 7)
        self.assertEqual(len(scripts["henk_nl"].split("\n\n")), 7)
        self.assertEqual(len(scripts["amy_en"].split("\n\n")), 6)
        text = "\n".join(f"{row['speaker']}: {row['text']}" for row in scripts["dialogue"])
        turns = demo.dialogue_turns(text)
        self.assertEqual([t.text for t in turns], [r["text"] for r in scripts["dialogue"]])
        root = ET.fromstring(demo.ssml(turns))
        self.assertEqual(len(root), 14)
        self.assertEqual(root[0].attrib["name"], "en-US-Grant:MAI-Voice-2.1")
        self.assertEqual(root[1].attrib["name"], "en-US-Harper:MAI-Voice-2.1")
        for key, voice in [("henk_nl", "nl-NL-Grant"), ("amy_en", "en-US-Harper")]:
            demo.ssml([demo.Turn(scripts[key], voice)])

    def test_dialogue_parser_rejects_unknown_or_empty_speakers(self):
        for text in ("", "Other: Hello", "Hello", "Henk: "):
            with self.assertRaises(demo.DemoError):
                demo.dialogue_turns(text)
        with self.assertRaises(demo.DemoError):
            demo.dialogue_turns("Henk: Hi\nAmy: Hello", {"Henk": "profile"})

    def test_synthesis_request_headers_metrics_and_no_redirects(self):
        self.session.request.return_value = response(wav())
        result = self.client.synthesize(self.turns, demo.FLASH)
        args, kwargs = self.session.request.call_args
        self.assertEqual(args, ("POST", "https://westeurope.tts.speech.microsoft.com/cognitiveservices/v1"))
        self.assertEqual(kwargs["headers"]["X-Microsoft-OutputFormat"], demo.OUTPUT_FORMAT)
        self.assertEqual(kwargs["headers"]["Ocp-Apim-Subscription-Key"], "offline-test-key")
        self.assertFalse(kwargs["allow_redirects"])
        self.assertEqual(kwargs["timeout"], (10, 120))
        self.assertEqual(result.duration, 1)
        self.assertEqual(result.estimate_usd, len(self.turns[0].text) * 15 / 1_000_000)
        self.assertNotIn("RIFF", repr(result))

    def test_http_errors_hide_body_and_do_not_retry(self):
        for status in (301, 400, 401, 403, 404, 409, 429, 500):
            self.session.reset_mock()
            self.session.request.return_value = response(b"secret raw error and profile-id", status)
            with self.subTest(status=status), self.assertRaises(demo.DemoError) as error:
                self.client.synthesize(self.turns)
            self.assertNotIn("secret", str(error.exception))
            self.session.request.assert_called_once()

    def test_network_errors_hide_request_details(self):
        self.session.request.side_effect = requests.Timeout("URL and secret key")
        with self.assertRaises(demo.DemoError) as error:
            self.client.synthesize(self.turns)
        self.assertNotIn("secret key", str(error.exception))
        self.assertIn("billed", str(error.exception))

    def test_invalid_empty_truncated_and_wrong_format_audio(self):
        for audio in (b"", b"not audio", wav()[:-8], wav(channels=2), wav(width=1), wav(rate=16000)):
            self.session.request.return_value = response(audio)
            with self.subTest(size=len(audio)), self.assertRaises(demo.DemoError):
                self.client.synthesize(self.turns)

    def test_audio_response_size_limit(self):
        self.session.request.return_value = response(wav())
        with patch.object(demo, "MAX_RESPONSE", 10), self.assertRaises(demo.DemoError):
            self.client.synthesize(self.turns)

    def test_recording_requirements(self):
        path = self.root / "reference.wav"
        for seconds in (5, 60):
            path.write_bytes(wav(seconds))
            self.assertEqual(demo.recording(path, reference=True), path)
        for seconds in (4.99, 60.01):
            path.write_bytes(wav(seconds))
            with self.assertRaises(demo.DemoError):
                demo.recording(path, reference=True)
        path.write_bytes(wav())
        self.assertEqual(demo.recording(path), path)
        with patch.object(demo, "MAX_AUDIO", 10), self.assertRaises(demo.DemoError):
            demo.recording(path)
        with self.assertRaises(demo.DemoError):
            demo.recording(self.root / "missing.wav")

    def test_personal_gate_blocks_all_network(self):
        for values in ((False, True, True, True), (True, False, True, True),
                       (True, True, False, True), (True, True, True, False)):
            client = self.personal(demo.Approval(*values))
            with self.assertRaises(demo.DemoError):
                client.create_project("project")
            with self.assertRaises(demo.DemoError):
                client.load_profile("voice")
        self.session.request.assert_not_called()

    def test_endpoint_and_region_validation(self):
        bad = [
            "http://demo.cognitiveservices.azure.com",
            "https://demo.cognitiveservices.azure.com.evil.example",
            "https://demo.cognitiveservices.azure.com:443",
            "https://user:pass@demo.cognitiveservices.azure.com",
            "https://demo.cognitiveservices.azure.com/path",
            "https://demo.cognitiveservices.azure.com?secret=value",
            "https://demo.cognitiveservices.azure.com#fragment",
            "https://[",
        ]
        for endpoint in bad:
            with self.subTest(endpoint=endpoint), self.assertRaises(demo.DemoError):
                demo.Settings("westeurope", "key", endpoint).personal_endpoint()
        with self.assertRaises(demo.DemoError):
            demo.Settings("northeurope", "key", self.settings.endpoint).personal_endpoint()

    def test_ids_cannot_inject_paths_or_queries(self):
        for value in ("../other", "voice?id=1", "x/y", "", "x" * 65):
            with self.subTest(value=value), self.assertRaises(demo.DemoError):
                self.personal().create_project(value)
        self.session.request.assert_not_called()

    def test_project_and_consent_upload_shape(self):
        self.session.request.return_value = json_response({"status": "NotStarted"})
        client = self.personal()
        client.create_project("project")
        self.assertEqual(self.session.request.call_args.kwargs["json"]["kind"], "PersonalVoice")
        path = self.root / "consent.wav"
        path.write_bytes(wav())
        client.submit_consent("consent", "project", "Test Speaker", "Test Company", "en-US", path)
        args, kwargs = self.session.request.call_args
        self.assertIn("/customvoice/consents/consent?api-version=2026-01-01", args[1])
        self.assertEqual(kwargs["data"]["voiceTalentName"], "Test Speaker")
        self.assertIn("audiodata", kwargs["files"])
        self.assertTrue(kwargs["files"]["audiodata"][1].closed)

    def test_reference_requires_successful_matching_consent(self):
        path = self.root / "reference.wav"
        path.write_bytes(wav(5))
        for status, project in (("NotStarted", "project"), ("Succeeded", "other")):
            self.session.reset_mock()
            self.session.request.return_value = json_response({"status": status, "projectId": project})
            with self.assertRaises(demo.DemoError):
                self.personal().submit_voice("voice", "project", "consent", path)
            self.session.request.assert_called_once()

    def test_reference_upload_success(self):
        path = self.root / "reference.wav"
        path.write_bytes(wav(5))
        self.session.request.side_effect = [
            json_response({"status": "Succeeded", "projectId": "project"}),
            json_response({"status": "NotStarted", "speakerProfileId": "not-ready"}),
        ]
        client = self.personal()
        client.submit_voice("voice", "project", "consent", path)
        self.assertEqual(client._verified_profiles, set())
        self.assertEqual(self.session.request.call_args.kwargs["data"],
                         {"projectId": "project", "consentId": "consent"})

    def test_profile_waits_for_success_and_checks_linked_consent(self):
        client = self.personal()
        self.session.request.return_value = json_response({"status": "NotStarted", "speakerProfileId": "not-ready"})
        with self.assertRaises(demo.DemoError):
            client.load_profile("voice")
        self.assertEqual(client._verified_profiles, set())
        self.session.request.side_effect = [
            json_response({"status": "Succeeded", "projectId": "p", "consentId": "c", "speakerProfileId": "ready-profile"}),
            json_response({"status": "Succeeded", "projectId": "p"}),
        ]
        self.assertEqual(client.load_profile("voice"), "ready-profile")
        self.assertIn("ready-profile", client._verified_profiles)

    def test_unknown_or_failed_states_and_invalid_json(self):
        for payload in ({"status": "Failed"}, {"status": "Mystery"}, [], {"status": "Cancelled"}):
            self.session.request.return_value = json_response(payload)
            with self.assertRaises(demo.DemoError):
                self.personal().status("consents", "consent")
        self.session.request.return_value = response(b"not-json")
        with self.assertRaises(demo.DemoError):
            self.personal().status("consents", "consent")

    def test_personal_synthesis_requires_loaded_profile_and_correct_ssml(self):
        turns = [demo.Turn("Hallo.", "nl-NL-Grant", profile_id="private-profile")]
        with self.assertRaises(demo.DemoError):
            self.client.synthesize(turns)
        personal = self.personal()
        with self.assertRaises(demo.DemoError):
            personal.synthesize(turns)
        personal._verified_profiles.add("private-profile")
        self.session.request.return_value = response(wav())
        personal.synthesize(turns)
        root = ET.fromstring(self.session.request.call_args.kwargs["data"])
        self.assertEqual(root.attrib[demo.XML_LANG], "nl-NL")
        self.assertEqual(root[0].attrib["name"], demo.MODEL)
        self.assertEqual(root[0][0].attrib["speakerProfileId"], "private-profile")
        self.assertNotIn("private-profile", repr(turns))
        with self.assertRaises(demo.DemoError):
            demo.ssml([demo.Turn("Hello", "en-US-Harper", "excited", "private-profile")])

    def test_deletion_requires_exact_confirmation_and_revokes_profiles(self):
        client = self.personal()
        client._verified_profiles.add("profile")
        with self.assertRaises(demo.DemoError):
            client.delete_voice("voice", "wrong")
        self.session.request.assert_not_called()
        self.session.request.return_value = response(status=204)
        client.delete_voice("voice", "voice")
        self.assertEqual(self.session.request.call_args.args[0], "DELETE")
        self.assertEqual(client._verified_profiles, set())

    def test_join_audio_preserves_complete_clips_in_order(self):
        results = [demo.AudioResult(wav(n), demo.MODEL, 0.1, n, 1, 0.0) for n in (1, 2)]
        self.assertEqual(demo.wav_duration(demo.join_audio(results)), 3)
        with self.assertRaises(demo.DemoError):
            demo.join_audio([])

    def test_notebook_valid_clean_and_compilable(self):
        notebook = nbformat.read(ROOT / "demo.ipynb", as_version=4)
        nbformat.validate(notebook)
        self.assertNotIn("widgets", notebook.metadata)
        self.assertNotIn("data:audio", (ROOT / "demo.ipynb").read_text())
        for cell in notebook.cells:
            self.assertNotIn("RUN_", cell.source)
            self.assertFalse(cell.get("attachments"))
            self.assertEqual(cell.metadata, {})
            if cell.cell_type == "code":
                self.assertIsNone(cell.execution_count)
                self.assertEqual(cell.outputs, [])
                compile(cell.source, "demo.ipynb", "exec")

    def test_public_notebook_has_no_personal_configuration(self):
        notebook = nbformat.read(ROOT / "demo.ipynb", as_version=4)
        source = next(cell.source for cell in notebook.cells if cell.id == "personal-config")
        assignments = {
            node.targets[0].id: node.value
            for node in ast.parse(source).body
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
        }
        expected = {
            "project_id": "abitofai-henk",
            "consent_id": "henk-consent",
            "voice_id": "henk-podcast",
            "talent_name": "",
            "company_name": "",
            "consent_locale": "en-US",
            "profile_id": None,
        }
        for name, value in expected.items():
            self.assertEqual(ast.literal_eval(assignments[name]), value, name)
        self.assertEqual(
            {kw.arg: ast.literal_eval(kw.value) for kw in assignments["approval"].keywords},
            {"enabled": True, "approved": False, "permission": False,
             "storage_acknowledged": False},
        )

    def test_post_ssml_sends_exact_body_and_reports_completion_statistics(self):
        document = demo.ssml(self.turns, demo.FLASH).decode().replace("</voice>", "\n</voice>")
        self.session.request.return_value = response(wav())
        output = io.StringIO()
        with patch("sys.stdout", output):
            result = self.client.post_ssml(document)
        self.assertEqual(self.session.request.call_args.kwargs["data"], document.encode())
        self.assertEqual(result.characters, len(self.turns[0].text))
        self.assertEqual(result.model, demo.FLASH)
        for label in ("spoken characters", "estimated cost", "text only", "full request", "audio"):
            self.assertIn(label, output.getvalue())
        self.assertNotIn(self.settings.key, output.getvalue())

    def test_raw_ssml_rejects_unsupported_markup_before_sending(self):
        valid = demo.ssml(self.turns).decode()
        invalid = [
            "<speak>", valid.replace('version="1.0" xml:lang', 'version="2.0" xml:lang'),
            valid.replace('xml:lang="en-US"', 'xml:lang="ja-JP"'),
            valid.replace("</voice>", '<audio src="https://example.com/"/>inside</voice>'),
            valid.replace("</voice>", '</voice><voice name="en-US-Harper:MAI-Voice-2.1-Flash">Hi</voice>'),
            valid.replace('name="en-US-Harper:MAI-Voice-2.1"', 'name="en-US-Harper"'),
            valid.replace("</speak>", '<!-- harmless --><unexpected/></speak>'),
            "<!DOCTYPE speak [<!ENTITY x 'expanded'>]>" + valid,
            "x" * 64001,
        ]
        for document in invalid:
            with self.subTest(document=document[:60]), self.assertRaises(demo.DemoError):
                self.client.post_ssml(document)
        self.session.request.assert_not_called()

    def test_raw_personal_ssml_cannot_bypass_consent(self):
        document = demo.ssml([demo.Turn("Hallo.", "nl-NL-Grant", profile_id="private-profile")])
        with self.assertRaises(demo.DemoError):
            self.client.post_ssml(document)
        client = self.personal()
        with self.assertRaises(demo.DemoError):
            client.post_ssml(document)
        client._verified_profiles.add("private-profile")
        self.session.request.return_value = response(wav())
        output = io.StringIO()
        with patch("sys.stdout", output):
            client.post_ssml(document)
        self.assertNotIn("private-profile", output.getvalue())
        client.approval = demo.Approval()
        with self.assertRaises(demo.DemoError):
            client.post_ssml(document)
        self.session.request.assert_called_once()

    def test_all_six_code_first_demos_with_mocked_azure(self):
        notebook = nbformat.read(ROOT / "demo.ipynb", as_version=4)
        sent_ssml = []
        cells = {cell.id: cell for cell in notebook.cells if cell.cell_type == "code"}
        self.assertFalse({"full-welcomes-post", "personal-setup", "personal-solo",
                          "personal-dialogue"} & cells.keys())
        self.assertNotIn("notebook_ui", cells["imports"].source)
        states = {"consents": "Succeeded", "personalvoices": "Succeeded"}

        def azure(method, url, **kwargs):
            if url.endswith("/cognitiveservices/v1"):
                sent_ssml.append(ET.fromstring(kwargs["data"]))
                return response(wav())
            if method == "PUT" and "/projects/" in url:
                return json_response({})
            if method == "POST" and ("/consents/" in url or "/personalvoices/" in url):
                self.assertEqual(kwargs["data"]["projectId"], "abitofai-henk")
                self.assertIn("audiodata", kwargs["files"])
                return json_response({"status": "NotStarted"})
            if "/personalvoices/" in url:
                return json_response({
                    "status": states["personalvoices"], "projectId": "abitofai-henk",
                    "consentId": "henk-consent", "speakerProfileId": "henk-profile",
                })
            if "/consents/" in url:
                return json_response({"status": states["consents"], "projectId": "abitofai-henk"})
            raise AssertionError("Unexpected request in notebook exercise")

        namespace = {}
        def execute(identifier):
            exec(compile(cells[identifier].source, "demo.ipynb", "exec"), namespace)

        with patch.object(requests.Session, "request", side_effect=azure) as network:
            with patch.object(Path, "cwd", return_value=ROOT):
                with patch.object(demo.Settings, "load", return_value=self.settings):
                    with patch("IPython.display.display"):
                        with patch("sys.stdout", io.StringIO()):
                            for identifier in ("imports", "configuration", "welcome-ssml", "podcast-ssml", "personal-config"):
                                execute(identifier)
                            network.assert_not_called()
                            namespace["ROOT"] = self.root
                            with self.assertRaises(demo.DemoError):
                                execute("personal-files")
                            samples = self.root / "samples"
                            samples.mkdir()
                            (samples / "henk-reference.wav").write_bytes(wav(5))
                            (samples / "henk-consent.wav").write_bytes(wav())
                            execute("personal-files")
                            with self.assertRaises(demo.DemoError):
                                execute("personal-project")
                            with self.assertRaises(demo.DemoError):
                                execute("personal-speech")
                            network.assert_not_called()
                            for identifier in ("welcome-post", "delivery", "languages", "comparison", "podcast-post"):
                                execute(identifier)
                            self.assertEqual(len(sent_ssml), 10)
                            self.assertEqual(len(sent_ssml[-1]), 14)
                            namespace["personal"].approval = demo.Approval(True, True, True, True)
                            namespace["talent_name"] = "Test Speaker"
                            namespace["company_name"] = "Test Company"
                            execute("personal-project")
                            execute("personal-consent")
                            states["consents"] = "Running"
                            execute("personal-consent-status")
                            self.assertEqual(namespace["consent_status"], "Running")
                            requests_before = network.call_count
                            with self.assertRaises(demo.DemoError):
                                execute("personal-reference")
                            self.assertEqual(network.call_count, requests_before + 1)
                            self.assertEqual(network.call_args.args[0], "GET")
                            states["consents"] = "Succeeded"
                            execute("personal-consent-status")
                            execute("personal-reference")
                            states["personalvoices"] = "Running"
                            namespace["profile_id"] = "stale-profile"
                            with self.assertRaises(demo.DemoError):
                                execute("personal-profile")
                            self.assertIsNone(namespace["profile_id"])
                            states["personalvoices"] = "Succeeded"
                            execute("personal-profile")
                            execute("personal-speech")
                            self.assertEqual(len(sent_ssml), 11)
                            self.assertEqual(sent_ssml[-1][0][0].attrib["speakerProfileId"], "henk-profile")
                            namespace["personal"].approval = demo.Approval()
                            requests_before = network.call_count
                            with self.assertRaises(demo.DemoError):
                                execute("personal-speech")
                            self.assertEqual(network.call_count, requests_before)
                            execute("personal-config")
                            self.assertIsNone(namespace["profile_id"])
                            namespace["personal"].approval = demo.Approval(True, True, True, True)
                            execute("personal-profile")
                            self.assertEqual(network.call_count, requests_before + 2)
                            execute("personal-speech")
                            self.assertEqual(len(sent_ssml), 12)

    def test_setup_and_ssml_preparation_do_not_contact_azure(self):
        notebook = nbformat.read(ROOT / "demo.ipynb", as_version=4)
        setup_cells = {"imports", "configuration", "welcome-ssml", "podcast-ssml", "personal-config"}
        notebook.cells = [cell for cell in notebook.cells if cell.id in setup_cells]
        notebook.cells.insert(0, nbformat.v4.new_code_cell(
            "import requests\n"
            "def no_network(*args, **kwargs):\n"
            "    raise AssertionError('Notebook initialization must not contact Azure')\n"
            "requests.sessions.Session.request = no_network\n"
        ))
        NotebookClient(notebook, timeout=120, kernel_name="python3",
                       resources={"metadata": {"path": str(ROOT)}}).execute()
        for cell in notebook.cells:
            if cell.cell_type == "code":
                self.assertFalse(any(output.output_type == "error" for output in cell.outputs))


if __name__ == "__main__":
    unittest.main()
