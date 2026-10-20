# MAI-Transcribe-2-Streaming: extended information

**MAI-Transcribe-2-Streaming** is Microsoft's streaming speech-to-text model.
Instead of waiting for a completed recording, an application sends audio while
someone speaks and receives evolving text. That makes it relevant to live
captions, meeting notes, voice interfaces, lectures, and call-center workflows.

This article describes the documented service and the standalone **A Bit of AI**
notebook. Documentation snapshot: **October 20, 2026**. Availability, pricing,
and preview behavior can change; confirm them against the linked sources.

The model is in **public preview**, without an SLA. Microsoft does not recommend
it for production workloads. Separately, this repository's browser-microphone
demo is experimental and still requires live end-to-end verification in the
target environment. Protocol tests and a rendered widget are not evidence of
working microphone capture, deployment access, or production readiness.

## What streaming changes

In the [file-transcription demo](../MAI-Transcribe-2/README.md), Henk and Amy have
already recorded an episode. The editor uploads that file and receives a
transcript with navigation metadata. Here, the episode is happening now:
listeners should see Henk's welcome before he finishes speaking.

| Aspect | File transcription | Streaming transcription |
| --- | --- | --- |
| Input | A completed supported audio file | A continuous sequence of PCM audio buffers |
| Transport in these demos | Multipart HTTP request | Bidirectional WebSocket |
| Model selection | `MAI-Transcribe-2` in the request definition | Streaming deployment name in the Realtime session |
| Output timing | Response after processing the uploaded file | Provisional and finalized text while audio arrives |
| End of input | End of the uploaded file | Explicit commit and finalization |
| Typical story | Prepare a transcript for the episode editor | Caption a host's live welcome |

Uploading many small WAV files is not this protocol. The file model's
diarization, word timestamps, phrase hints, and clean/verbatim controls should
not be assumed to exist on the streaming route.

Transcription is also not translation, summarization, or speaker identity
recognition. Those require separate documented capabilities and workflows.

## Languages and automatic detection

The [streaming overview](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-transcribe-2-streaming)
documents **60 languages**:

| Code | Language | Code | Language | Code | Language |
| --- | --- | --- | --- | --- | --- |
| `af` | Afrikaans | `ar` | Arabic | `as` | Assamese |
| `az` | Azerbaijani | `bg` | Bulgarian | `bn` | Bengali |
| `bs` | Bosnian | `ca` | Catalan | `cs` | Czech |
| `da` | Danish | `de` | German | `el` | Greek |
| `en` | English | `es` | Spanish | `et` | Estonian |
| `fa` | Persian | `fi` | Finnish | `fil` | Filipino |
| `fr` | French | `gl` | Galician | `gu` | Gujarati |
| `he` | Hebrew | `hi` | Hindi | `hu` | Hungarian |
| `hy` | Armenian | `id` | Indonesian | `is` | Icelandic |
| `it` | Italian | `ja` | Japanese | `kk` | Kazakh |
| `kn` | Kannada | `ko` | Korean | `lt` | Lithuanian |
| `lv` | Latvian | `mk` | Macedonian | `ml` | Malayalam |
| `mr` | Marathi | `ms` | Malay | `nb` | Norwegian Bokmal |
| `ne` | Nepali | `nl` | Dutch | `or` | Odia |
| `pa` | Punjabi, Gurmukhi script | `pl` | Polish | `pt` | Portuguese |
| `ro` | Romanian | `ru` | Russian | `sk` | Slovak |
| `sl` | Slovenian | `sv` | Swedish | `sw` | Swahili |
| `ta` | Tamil | `te` | Telugu | `th` | Thai |
| `tr` | Turkish | `uk` | Ukrainian | `ur` | Urdu |
| `vi` | Vietnamese | `yue` | Cantonese | `zh` | Chinese, simplified |

The Realtime configuration accepts an optional language hint; `null` leaves
detection automatic. The notebook uses automatic detection rather than adding
a language settings panel. A Dutch welcome should remain Dutch, not become an
English translation.

Language support does not mean identical accuracy across accents, microphones,
noise levels, or language switches. Rehearse the actual English/Dutch sequence
rather than treating support for both languages as an accuracy guarantee.

## Availability, resources, and integrations

The current overview lists these serving regions:

| Region | Azure name |
| --- | --- |
| Sweden Central | `swedencentral` |
| Central US | `centralus` |
| East US 2 | `eastus2` |
| Southeast Asia | `southeastasia` |

The October 1 model card described East US 2 as coming soon; the October 7 Learn
overview lists it as available. Prefer current operational documentation and
confirm deployment availability for the subscription. A North Europe file-model
resource is not a substitute for a Sweden Central streaming resource.

Two integration routes are documented:

| Route | Prerequisites and selection | Responsibility |
| --- | --- | --- |
| [Speech SDK](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-transcribe-2-streaming-speech-sdk) | Guide specifies SDK v1.52.0 and a supported Speech/Foundry resource; select `mai-transcribe-2-streaming` | SDK-managed connection and recognition lifecycle |
| [Realtime API](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-transcribe-2-streaming-realtime) | Foundry resource with a deployed streaming model; use its deployment name | Application manages audio buffers, events, commits, and cleanup |

The SDK guide provides Python, C#, Java, and C++ examples. That does not
establish equivalent JavaScript SDK support. The notebook uses Realtime and a
Python backend, not an assumed browser Speech SDK integration.

## Realtime endpoint and authentication

The documented connection URI is:

```text
wss://<resource-name>.services.ai.azure.com/mai/v1/realtime?intent=transcription
```

Authenticate with an `api-key` header or an `Authorization: Bearer ...` header.
The Entra token scope is `https://cognitiveservices.azure.com/.default`.
Resource access, role assignments, deployment availability, and network access
must all be valid; a syntactically correct endpoint does not prove access.

Native browser WebSockets cannot set these arbitrary authentication headers.
Do not work around that by placing a long-lived key in JavaScript or a URL.
The notebook uses the Python kernel as a relay and rejects redirects rather
than forwarding credentials to another resource.

Its connection variables are:

| Variable | Meaning |
| --- | --- |
| `AZURE_MAI_ENDPOINT` | HTTPS `services.ai.azure.com` resource root |
| `AZURE_MAI_DEPLOYMENT_NAME` | The actual deployed streaming model's name |
| `AZURE_MAI_API_KEY` | Optional streaming resource key; blank selects Azure CLI authentication |

These are independent of the file and voice demos' settings. `.env` is read
only from this notebook's working directory, and environment variables win.
No keys are synchronized as widget state or sent to the browser.

## Configuring a session

Connect and wait for `session.created`. Then send the configuration below
and wait for `session.updated` before sending audio:

```json
{
  "type": "session.update",
  "session": {
    "type": "transcription",
    "audio": {
      "input": {
        "format": {"type": "audio/pcm", "rate": 16000},
        "transcription": {
          "model": "<deployment-name>",
          "language": null
        },
        "turn_detection": null,
        "noise_reduction": null
      }
    }
  }
}
```

The model field is a **deployment name**, not a file-model identifier.
Settings cannot change after the first audio append, even after a commit.
The documented route supports only `null` for turn detection and noise
reduction; do not assume server-side voice activity detection or automatic
commits.

## Audio format and browser capture

The service accepts raw, signed, little-endian **PCM16, mono, at 16 kHz or
24 kHz**. Base64-encode the bytes in an append event, without a WAV header:

```json
{
  "type": "input_audio_buffer.append",
  "audio": "<base64 PCM16 bytes>"
}
```

Browser `MediaRecorder` commonly produces compressed/containerized audio.
Sending arbitrary WebM/Opus or WAV bytes as PCM is not a valid substitute.
The demo creates a 16 kHz Web Audio context, downmixes to mono, and uses an
AudioWorklet to convert floating-point samples into PCM16. It frames 320
samples per **20 ms** message, within the guide's 10-20 ms low-latency guidance.

Audio travels from the browser to the kernel in binary widget messages, then
to Azure as base64 WebSocket events. No local audio file is created. This
architecture permits a remote kernel without requiring a microphone on the
Codespaces host, but browser/OS permissions and embedding policy remain
independent failure points.

A full HTTPS/localhost JupyterLab tab can avoid some iframe restrictions.
It cannot override an OS microphone denial, organization policy, missing
device, unsupported Web Audio behavior, or a service configuration error.

## Partial text, finalized text, and completion

The event types have different meanings:

| Event | Meaning | Correct display behavior |
| --- | --- | --- |
| `conversation.item.input_audio_transcription.delta` | Newly finalized text | Append exactly; do not trim or insert spaces |
| `conversation.item.input_audio_transcription.intermediate` | Entire provisional suffix | Replace the previous suffix |
| `input_audio_buffer.committed` | Commit accepted | Keep waiting; finalization may still be running |
| `conversation.item.input_audio_transcription.completed` | Full final transcript since the previous commit | Replace/reconcile that interval, rather than duplicating its deltas |
| `error` or `conversation.item.input_audio_transcription.failed` | Session/transcription failure | Mark the result incomplete and stop safely |

For example, a final delta `Hello`, followed by provisional ` world`, then
provisional ` there`, should display `Hello there`. When the final delta
` there!` arrives, display `Hello there!` and clear the old provisional suffix.
Appending every event would produce repeated or contradictory captions.

The notebook uses normal text for accumulated final deltas and italic text for
the provisional suffix. It inserts transcript content as text, not executable
HTML. Captions are untrusted speech-derived content, not instructions to run
tools or trigger actions.

## Stop, commit, and lifecycle

The client must explicitly request finalization:

```json
{"type": "input_audio_buffer.commit"}
```

The service does not acknowledge every audio append. An application may commit
at natural pauses or at the end of recording; this demo commits once at Stop.
It releases microphone tracks, flushes the last partial frame, drains queued
audio, sends the commit, and waits for `completed` before calling the text final.
An empty capture does not send an empty commit.

The documented service session limit is **one hour**. This demo deliberately
caps capture at **five minutes**, with bounded queues and finite startup and
finalization timeouts. Browser/worklet acknowledgements indicate that the
kernel forwarded a frame, not that Azure accepted or transcribed it.

Overflows and connection failures are visible rather than silent gaps.
Heartbeats detect a lost browser or kernel connection. Closing/rerunning the
widget cancels its session, while leaving the browser tab stops capture.
There is no automatic reconnection: a new Start opens a new session.

These controls are safeguards, not service guarantees. A timeout can leave a
partial transcript and does not prove that the session was unbilled.

## Latency, accuracy, and evaluation

Model inference latency is only part of microphone-to-screen latency.
Capture buffering, resampling, browser scheduling, widget communication,
network transit, service processing, and rendering all contribute. A
20 ms frame size is not a promise of captions within 20 ms.

Microsoft's [streaming announcement](https://microsoft.ai/news/our-first-streaming-transcription-model/)
and [model card](https://microsoft.ai/pdf/MAI-Transcribe-2-Streaming-Model-Card-Memo.pdf)
describe published model measurements. Those are not end-to-end measurements
of this notebook, and results from different datasets should not be compared
as if they were the same benchmark.

For a realistic evaluation, separately measure first provisional text,
stabilization of words, Stop-to-final latency, and final transcript accuracy.
Use representative microphones, accents, background noise, and terminology.
Review names, numbers, negations, and corrections, not just a fluent-looking
paragraph. A correct final transcript may still have shown misleading
provisional text earlier.

## Pricing, privacy, and limitations

Consult [Microsoft Foundry Models pricing](https://azure.microsoft.com/pricing/details/ai-foundry-models/microsoft/)
and the deployment's current offer. Do not reuse the file model's pricing or
an introductory announcement as a permanent quote. Budget for actual streamed
audio and applicable silence processing, plus any Codespaces compute costs.
The notebook makes no paid call until Start, but a failed session may still
incur usage charges.

Speech and transcripts can identify people or contain sensitive information.
Obtain permission to process the speech, avoid private consent recordings,
and review the applicable
[Speech privacy documentation](https://learn.microsoft.com/en-us/azure/foundry/responsible-ai/speech-service/speech-to-text/data-privacy-security)
and preview terms. Do not automatically extend a file-transcription retention
statement to this preview deployment or infer residency guarantees solely
from the resource region.

The demo saves no audio file and does not synchronize caption text as persisted
widget traits. Confirmed text remains in `captions.transcript` in kernel memory.
Browser displays, screenshots, manually displayed notebook outputs, exported
text, application logs, and downstream services are separate retention surfaces.
Clear outputs and restart the kernel before sharing.

This is not a ready-made production captioning system. It does not provide
speaker identity, diarization, word timestamps, keyword hints, clean/verbatim
selection, translations, summaries, broadcast overlays, or timed subtitle-file
exports. Each would need its own supported implementation and validation.

## Follow the podcast story

The [standalone notebook](demo.ipynb) keeps the presentation simple:
prepare the streaming resource, open the live-caption controls, welcome the
audience in English, try Dutch, then Stop and review the final transcript.
Transport details live in `live_captions.py` and `live_captions.js`.

The [setup instructions](demo-instructions.md) cover local installation,
Codespaces, browser permissions, credentials, and troubleshooting. The
[file-transcription notebook](../MAI-Transcribe-2/demo.ipynb) remains a separate
editorial workflow, and the [Voice notebook](../MAI-Voice-2.1/demo.ipynb)
creates the podcast opening. None requires running the others.

[Back to the model introduction](README.md)
