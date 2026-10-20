"""Explicit, bounded Azure requests for the MAI-Voice podcast notebook."""

import io
import json
import os
import re
import time
import wave
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional, Sequence
from urllib.parse import urlsplit

import requests
from dotenv import dotenv_values


MODEL = "MAI-Voice-2.1"
FLASH = "MAI-Voice-2.1-Flash"
PRICES = {MODEL: 22, FLASH: 15}
OUTPUT_FORMAT = "riff-24khz-16bit-mono-pcm"
API_VERSION = "2026-01-01"
MAX_TEXT = 6000
MAX_AUDIO = 30_000_000
MAX_RESPONSE = 30 * 1024 * 1024
SPEECH_NS = "http://www.w3.org/2001/10/synthesis"
MSTTS_NS = "http://www.w3.org/2001/mstts"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
ET.register_namespace("", SPEECH_NS)
ET.register_namespace("mstts", MSTTS_NS)

CATALOG = {
    "en-US-Harper": (
        "neutral", "excited", "whispering", "happy", "joyful", "narrator",
        "audiobook", "educational",
    ),
    "en-US-Grant": (
        "neutral", "agent", "audiobook", "customer_call_center", "educational", "narrator",
    ),
    "nl-NL-Harper": (
        "neutral", "agent", "audiobook", "customer_call_center", "educational", "narrator",
    ),
    "nl-NL-Grant": (
        "neutral", "agent", "customer_call_center", "educational", "narrator",
    ),
    "nl-NL-Sander": (
        "neutral", "adventurous", "caringempathy", "curious", "encouraging", "excited",
        "friendlycheerful", "nostalgic", "reflective", "saddisappointed", "serious",
    ),
}
MAI_REGIONS = {
    "canadacentral", "centralindia", "eastus", "eastus2", "francecentral",
    "southeastasia", "swedencentral", "westeurope", "westus2",
}
DISPUTED_REGIONS = {"eastasia", "japaneast", "northeurope", "westus", "westus3"}
PERSONAL_REGIONS = {
    "westeurope", "swedencentral", "eastus", "eastus2", "westus2",
    "southeastasia", "eastasia",
}


class DemoError(Exception):
    """A safe, actionable message that never includes a response body or key."""


@dataclass(frozen=True)
class Settings:
    region: str = ""
    key: str = field(default="", repr=False)
    endpoint: str = ""

    @classmethod
    def load(cls, directory: Path, environment: Optional[Mapping[str, str]] = None):
        values = {**dotenv_values(directory / ".env"),
                  **(os.environ if environment is None else environment)}
        return cls(
            region=(values.get("VOICE_SPEECH_REGION") or "").strip().lower(),
            key=(values.get("VOICE_SPEECH_KEY") or "").strip(),
            endpoint=(values.get("VOICE_SPEECH_ENDPOINT") or "").strip(),
        )

    def validate(self):
        if self.region not in MAI_REGIONS | DISPUTED_REGIONS:
            raise DemoError("Set VOICE_SPEECH_REGION to a documented MAI region, such as westeurope.")
        if not self.key or any(c in self.key for c in "\r\n"):
            raise DemoError("Set VOICE_SPEECH_KEY to the key for that same voice resource.")

    def personal_endpoint(self):
        self.validate()
        if self.region not in PERSONAL_REGIONS:
            raise DemoError("Personal voice needs a supported region; use West Europe or Sweden Central.")
        try:
            parsed = urlsplit(self.endpoint)
        except ValueError:
            raise DemoError("Use a valid HTTPS custom-subdomain resource endpoint.") from None
        if (
            parsed.scheme != "https"
            or not re.fullmatch(r"[a-z0-9][a-z0-9-]*\.cognitiveservices\.azure\.com", parsed.netloc)
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment
        ):
            raise DemoError("Set VOICE_SPEECH_ENDPOINT to the HTTPS custom-subdomain root of the same resource.")
        return self.endpoint.rstrip("/")


@dataclass(frozen=True)
class Turn:
    text: str
    voice: str
    style: str = "neutral"
    profile_id: str = field(default="", repr=False)


@dataclass(frozen=True)
class AudioResult:
    audio: bytes = field(repr=False)
    model: str
    seconds: float
    duration: float
    characters: int
    estimate_usd: float


def _text(value):
    if not isinstance(value, str) or not value.strip():
        raise DemoError("Each spoken turn needs nonempty text.")
    if any(not (c in "\t\n\r" or 0x20 <= ord(c) <= 0xD7FF
                or 0xE000 <= ord(c) <= 0xFFFD or 0x10000 <= ord(c) <= 0x10FFFF)
           for c in value):
        raise DemoError("Text contains characters that are invalid in XML.")
    return value


def _identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value):
        raise DemoError("Use a resource ID of 1-64 letters, digits, hyphens or underscores, starting with a letter or digit.")
    return value


def _profile_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9-]{1,128}", value):
        raise DemoError("The service did not return a valid speaker profile ID.")
    return value


def ssml(turns: Sequence[Turn], model=MODEL):
    if model not in PRICES:
        raise DemoError("Select MAI-Voice-2.1 or MAI-Voice-2.1-Flash explicitly.")
    if not turns or len(turns) > 50:
        raise DemoError("Supply between 1 and 50 spoken turns.")
    if sum(len(_text(t.text)) for t in turns) > MAX_TEXT:
        raise DemoError("Keep each demo request at or below 6,000 spoken characters.")
    root = ET.Element(f"{{{SPEECH_NS}}}speak", {"version": "1.0", XML_LANG: turns[0].voice[:5]})
    for turn in turns:
        if turn.voice not in CATALOG or turn.style not in CATALOG[turn.voice]:
            raise DemoError("That voice/style combination is not in this demo's documented catalog.")
        if turn.profile_id:
            _profile_id(turn.profile_id)
            if turn.style != "neutral":
                raise DemoError("This demo does not assume expressive-style support for personal voices.")
            if turn.voice[:5] != turns[0].voice[:5]:
                raise DemoError("Use separate personal-voice requests for different languages.")
        name = model if turn.profile_id else f"{turn.voice}:{model}"
        node = ET.SubElement(root, f"{{{SPEECH_NS}}}voice", {"name": name})
        if turn.profile_id:
            node = ET.SubElement(node, f"{{{MSTTS_NS}}}ttsembedding",
                                 {"speakerProfileId": turn.profile_id})
        elif turn.style != "neutral":
            node = ET.SubElement(node, f"{{{MSTTS_NS}}}express-as", {"style": turn.style})
        node.text = turn.text
    body = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    if len(body) > 64000:
        raise DemoError("The generated SSML exceeds this demo's 64 KB limit.")
    return body


def dialogue_turns(text, profiles=None):
    """Parse visible speaker labels without speaking the labels."""
    profiles = {} if profiles is None else profiles
    voices = {"Henk": "en-US-Grant", "Amy": "en-US-Harper"}
    turns = []
    for line in text.splitlines():
        if not line.strip():
            continue
        speaker, separator, words = line.partition(":")
        if not separator or speaker.strip() not in voices:
            raise DemoError("Each dialogue line must begin with Henk: or Amy:.")
        speaker = speaker.strip()
        if profiles and speaker not in profiles:
            raise DemoError("Both speakers need loaded, consented profiles for this dialogue.")
        turns.append(Turn(_text(words.strip()), voices[speaker],
                          profile_id=profiles.get(speaker, "")))
    if not turns:
        raise DemoError("The dialogue is empty.")
    return turns


def inspect_ssml(document):
    """Validate the demo's SSML subset without rewriting the submitted body."""
    if not isinstance(document, (str, bytes)):
        raise DemoError("Pass an SSML string or UTF-8 bytes to post_ssml.")
    try:
        body = document.encode("utf-8") if isinstance(document, str) else document
        text = body.decode("utf-8")
    except UnicodeError:
        raise DemoError("SSML must be valid UTF-8.") from None
    if len(body) > 64000 or "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
        raise DemoError("Use SSML below 64 KB without document types or entity declarations.")
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        raise DemoError("SSML is not well-formed XML. Escape dynamic text with html.escape.") from None
    if (root.tag != f"{{{SPEECH_NS}}}speak" or root.get("version") != "1.0"
            or root.get(XML_LANG) not in {"en-US", "nl-NL"}
            or set(root.attrib) != {"version", XML_LANG} or (root.text or "").strip()):
        raise DemoError("Use a speak element with version='1.0', an en-US/nl-NL xml:lang, and voice children.")
    turns, models = [], set()
    for voice in root:
        if (voice.tag != f"{{{SPEECH_NS}}}voice" or set(voice.attrib) != {"name"}
                or (voice.tail or "").strip() or len(voice) > 1):
            raise DemoError("Each voice needs a name and either text or one expression/profile element.")
        name = voice.get("name")
        node, style, profile = voice, "neutral", ""
        if len(voice):
            node = voice[0]
            if len(node) or (voice.text or "").strip() or (node.tail or "").strip():
                raise DemoError("Keep spoken text inside a single expression/profile element.")
            if node.tag == f"{{{MSTTS_NS}}}express-as" and set(node.attrib) == {"style"}:
                style = node.get("style")
            elif node.tag == f"{{{MSTTS_NS}}}ttsembedding" and set(node.attrib) == {"speakerProfileId"}:
                profile = _profile_id(node.get("speakerProfileId"))
            else:
                raise DemoError("This demo supports express-as and ttsembedding, not other nested SSML tags.")
        if profile:
            model, base_voice = name, root.get(XML_LANG) + "-Grant"
        else:
            base_voice, separator, model = name.rpartition(":")
            if not separator:
                raise DemoError("A prebuilt voice name must include its MAI model suffix.")
        models.add(model)
        turns.append(Turn(_text((node.text or "").strip()), base_voice, style, profile))
    if len(models) != 1:
        raise DemoError("Use at least one voice and exactly one MAI model per request.")
    model = models.pop()
    ssml(turns, model)
    return body, model, turns


def wav_duration(audio, expected_rate=None):
    try:
        with wave.open(io.BytesIO(audio), "rb") as source:
            channels, width, rate, frames, compression, _ = source.getparams()
            if (channels != 1 or width != 2 or compression != "NONE" or frames < 1
                    or rate not in {16000, 24000, 44100, 48000}
                    or (expected_rate is not None and rate != expected_rate)):
                raise DemoError("Expected nonempty mono 16-bit PCM WAV audio at a supported sample rate.")
            if len(source.readframes(frames)) != frames * width * channels:
                raise DemoError("The WAV data is incomplete.")
            return frames / rate
    except (wave.Error, EOFError):
        raise DemoError("Audio is not a valid PCM WAV file.") from None


def recording(path, reference=False):
    path = Path(path)
    if not path.is_file():
        raise DemoError("The selected recording does not exist. Upload a permitted WAV first.")
    if path.suffix.lower() != ".wav" or path.stat().st_size > MAX_AUDIO:
        raise DemoError("Use a WAV recording no larger than 30 MB.")
    try:
        duration = wav_duration(path.read_bytes())
    except OSError:
        raise DemoError("The selected recording could not be read.") from None
    minimum, maximum = (5, 60) if reference else (1, 120)
    if not minimum <= duration <= maximum:
        raise DemoError(f"Use a recording between {minimum} and {maximum} seconds.")
    return path


class SpeechClient:
    def __init__(self, settings: Settings, session=None):
        self.settings = settings
        self.session = session if session is not None else requests.Session()

    def _request(self, method, url, *, headers=None, **kwargs):
        self.settings.validate()
        request_headers = {
            "Ocp-Apim-Subscription-Key": self.settings.key,
            "User-Agent": "mai-voice-podcast-demo",
            **(headers or {}),
        }
        try:
            with self.session.request(
                method, url, headers=request_headers, timeout=(10, 120),
                allow_redirects=False, stream=True, **kwargs,
            ) as response:
                if not 200 <= response.status_code < 300:
                    guidance = {
                        400: "Check the voice, SSML, IDs, and request parameters.",
                        401: "Check the key and region belong to the same resource.",
                        403: "Check permissions and Limited Access approval.",
                        404: "Check resource IDs and model availability.",
                        409: "The ID already exists. Check its status or choose a new ID.",
                        429: "Rate limit or regional voice capacity reached; retry manually later.",
                    }.get(response.status_code, "Check Azure service status and resource configuration.")
                    raise DemoError(f"Azure returned HTTP {response.status_code}. {guidance} No automatic retry was made.")
                body = bytearray()
                for chunk in response.iter_content(chunk_size=65536):
                    body.extend(chunk)
                    if len(body) > MAX_RESPONSE:
                        raise DemoError("Response exceeds the demo's safety limit.")
                return bytes(body)
        except requests.RequestException:
            raise DemoError("Azure request failed or timed out. It may still have been processed or billed. No automatic retry was made.") from None

    def synthesize(self, turns, model=MODEL):
        if any(turn.profile_id for turn in turns):
            raise DemoError("Use the gated personal-voice client for cloned voices.")
        return self._synthesize(turns, model)

    def _synthesize(self, turns, model):
        body = ssml(turns, model)
        return self._post_audio(body, model, sum(len(turn.text) for turn in turns))

    def post_ssml(self, document):
        body, model, turns = inspect_ssml(document)
        self._authorize_ssml(turns)
        result = self._post_audio(body, model, sum(len(turn.text) for turn in turns))
        print(
            f"{result.model} | {result.characters:,} spoken characters | "
            f"estimated cost ~${result.estimate_usd:.4f} (text only) | "
            f"full request {result.seconds:.2f}s | audio {result.duration:.2f}s"
        )
        return result

    def _authorize_ssml(self, turns):
        if any(turn.profile_id for turn in turns):
            raise DemoError("Use the gated personal-voice client for cloned voices.")

    def _post_audio(self, body, model, characters):
        started = time.perf_counter()
        audio = self._request(
            "POST", f"https://{self.settings.region}.tts.speech.microsoft.com/cognitiveservices/v1",
            headers={"Content-Type": "application/ssml+xml",
                     "X-Microsoft-OutputFormat": OUTPUT_FORMAT},
            data=body,
        )
        elapsed = time.perf_counter() - started
        duration = wav_duration(audio, expected_rate=24000)
        if duration >= 590:
            raise DemoError("Output is near the ten-minute service limit; split the script and check for truncation.")
        return AudioResult(audio, model, elapsed, duration, characters,
                           characters * PRICES[model] / 1_000_000)


@dataclass(frozen=True)
class Approval:
    enabled: bool = False
    approved: bool = False
    permission: bool = False
    storage_acknowledged: bool = False

    def require(self):
        if not all((self.enabled, self.approved, self.permission, self.storage_acknowledged)):
            raise DemoError("Personal voice is gated: enable it and confirm Microsoft approval, this speaker's permission, and storage/retention terms.")


class PersonalVoiceClient(SpeechClient):
    """One explicitly consented speaker per instance; IDs never appear in errors."""

    def __init__(self, settings, approval: Approval, session=None):
        super().__init__(settings, session)
        self.approval = approval
        self._verified_profiles = set()

    def _root(self):
        self.approval.require()
        return self.settings.personal_endpoint()

    def _resource(self, collection, resource_id):
        return f"{self._root()}/customvoice/{collection}/{_identifier(resource_id)}?api-version={API_VERSION}"

    def _json(self, method, url, **kwargs):
        body = self._request(method, url, **kwargs)
        if not body:
            return {}
        try:
            result = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            raise DemoError("Azure returned an invalid JSON response.") from None
        if not isinstance(result, dict):
            raise DemoError("Azure returned an unexpected response shape.")
        return result

    def create_project(self, project_id):
        self._json("PUT", self._resource("projects", project_id),
                   json={"kind": "PersonalVoice", "description": "Consented podcast voice"})

    def submit_consent(self, consent_id, project_id, talent, company, locale, path):
        url = self._resource("consents", consent_id)
        _identifier(project_id)
        if locale not in {"en-US", "nl-NL"}:
            raise DemoError("This demo's consent locale must be en-US or nl-NL.")
        _text(talent)
        _text(company)
        path = recording(path)
        try:
            with path.open("rb") as audio:
                self._json("POST", url, data={
                    "projectId": project_id, "voiceTalentName": talent,
                    "companyName": company, "locale": locale,
                }, files={"audiodata": (path.name, audio, "audio/wav")})
        except OSError:
            raise DemoError("Could not open the consent recording.") from None

    def status(self, collection, resource_id):
        if collection not in {"consents", "personalvoices"}:
            raise DemoError("Unsupported personal-voice resource type.")
        result = self._json("GET", self._resource(collection, resource_id))
        status = result.get("status")
        if status in {"Failed", "Canceled", "Cancelled"}:
            raise DemoError("Azure voice processing failed. Review the resource in Azure; no raw response is displayed here.")
        if status not in {"NotStarted", "Running", "Succeeded"}:
            raise DemoError("Azure returned an unknown processing state.")
        return result

    def submit_voice(self, voice_id, project_id, consent_id, path):
        url = self._resource("personalvoices", voice_id)
        _identifier(project_id)
        consent = self.status("consents", consent_id)
        if consent["status"] != "Succeeded" or consent.get("projectId") != project_id:
            raise DemoError("Consent must have succeeded in this project before uploading reference audio.")
        path = recording(path, reference=True)
        try:
            with path.open("rb") as audio:
                self._json("POST", url, data={"projectId": project_id, "consentId": consent_id},
                           files={"audiodata": (path.name, audio, "audio/wav")})
        except OSError:
            raise DemoError("Could not open the reference recording.") from None

    def load_profile(self, voice_id):
        result = self.status("personalvoices", voice_id)
        if result["status"] != "Succeeded":
            raise DemoError("Personal voice is still processing. Check again later; do not re-upload.")
        consent = self.status("consents", result.get("consentId"))
        if (consent["status"] != "Succeeded" or not result.get("projectId")
                or consent.get("projectId") != result["projectId"]):
            raise DemoError("The profile must have successful consent in the same project.")
        profile = _profile_id(result.get("speakerProfileId"))
        self._verified_profiles.add(profile)
        return profile

    def synthesize(self, turns, model=MODEL):
        self._authorize_ssml(turns)
        return self._synthesize(turns, model)

    def _authorize_ssml(self, turns):
        self._root()
        if not turns or any(not t.profile_id or t.profile_id not in self._verified_profiles for t in turns):
            raise DemoError("Load a successful consented profile before personal-voice synthesis.")

    def delete_voice(self, voice_id, confirmation):
        if confirmation != voice_id:
            raise DemoError("Type the exact personal-voice resource ID to confirm deletion.")
        self._json("DELETE", self._resource("personalvoices", voice_id))
        self._verified_profiles.clear()


def join_audio(results):
    """Join validated WAV clips in order, without overlapping or hiding failures."""
    if not results:
        raise DemoError("No completed clips to assemble.")
    output = io.BytesIO()
    with wave.open(output, "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(24000)
        for result in results:
            wav_duration(result.audio, expected_rate=24000)
            with wave.open(io.BytesIO(result.audio), "rb") as source:
                target.writeframes(source.readframes(source.getnframes()))
    return output.getvalue()
