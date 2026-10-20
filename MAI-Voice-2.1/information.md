# MAI-Voice-2.1: from a script to a voice

[Model introduction](README.md) | [Podcast notebook](demo.ipynb) | [Setup instructions](demo-instructions.md)

*Model and service information checked October 20, 2026. Preview features,
availability, catalogs, and prices can change.*

A podcast opening is more than a paragraph read aloud. A host needs a
recognizable voice, a welcoming tone, clear pronunciation, and enough variation
to make a conversation feel alive. When another host joins, the voices need to
remain distinct. When the show welcomes a different audience, the same
identity should still be recognizable in another language.

MAI-Voice-2.1 is Microsoft's text-to-speech model for this kind of expressive
generation. It turns a supplied script into audio, with prebuilt voices,
voice-specific speaking styles, multilingual synthesis, and an approved
personal-voice workflow. MAI-Voice-2.1-Flash shares the broad feature set while
prioritizing responsiveness.

Both are currently **public preview**, provided without an SLA and not
recommended for production workloads. A documented capability is not a
guarantee that every resource, region, voice, and optional control exposes it.
The [official guide][guide] is the starting point for the current service.

## In this article

- [Models and capabilities](#two-models-different-production-priorities)
- [Languages and voice identities](#languages-locales-and-voice-identities)
- [SSML and speaking styles](#directing-a-voice-with-ssml)
- [API, authentication, and audio](#api-authentication-and-audio-output)
- [Regions and availability](#where-to-run-it)
- [Personal-voice lifecycle](#personal-voice-a-lifecycle-not-a-file-drop)
- [Privacy and consent](#privacy-and-consent-after-generation)
- [Pricing and billing](#price-billing-units-and-demo-budgets)
- [Latency measurements](#latency-measure-the-interval-you-actually-show)
- [Streaming and service limits](#streaming-long-form-synthesis-and-service-limits)

## Two models, different production priorities

| | MAI-Voice-2.1 | MAI-Voice-2.1-Flash |
| --- | --- | --- |
| Main emphasis | Expressive, high-fidelity generation and long-form consistency | Low-latency, responsive generation |
| Typical use | Narration, podcasts, educational content, voiceovers | Assistants, interactive experiences, call-center/IVR output |
| Languages | 23 | 23 |
| Managed voices | Current shared MAI catalog | Current shared MAI catalog |
| Style control | Voice-specific SSML styles | Voice-specific SSML styles |
| Personal voice | Gated, consented reference-audio workflow | Gated, consented reference-audio workflow |
| Published synthesis price | $22 / million characters | $15 / million characters |

The current pair was announced on October 1, 2026. Earlier material describes
MAI-Voice-1 and MAI-Voice-2, including different language sets, region lists,
and identifiers. The original Voice-1 announcement describes its use in Copilot
Daily and Podcasts; its model card already includes voice prompting. The
June 2026 Voice-2 card describes a 15-language generation model. Those historical
capabilities do not define the current 2.1 API. [Announcement][launch] |
[Voice-1 announcement][voice1] | [Voice-2 card][voice2card]

The [2.1 card][card] describes chunking and context carryover for long-form
speaker consistency. The [Flash card][flashcard] explicitly describes streaming
audio output for interactive scenarios. Neither makes an arbitrary synchronous
request unlimited, and the reviewed API documentation does not expose a general
context-carryover parameter for applications to invent.

## What the model does—and what surrounds it

The model generates speech from supplied text. It does not write the podcast
script, translate an English script into Dutch, transcribe a reference
conversation, or provide an assistant's reasoning by itself.

Multi-speaker synthesis means rendering a supplied sequence with different
voices. It is different from diarization, which identifies speakers in an
existing recording. Personal voice means conditioning synthesis on a consented
speaker profile; it is not a general-purpose impersonation or voice-conversion
endpoint.

A conversational application also needs recognition, turn-taking, interruption
handling, playback, and usually a language model. Azure Voice Live can provide
that larger integration. A notebook that downloads a WAV and displays an audio
player demonstrates completed-file TTS, not a full streaming voice agent.

The reviewed public sources do not establish downloadable MAI-Voice-2.1 weights,
a self-hosted runtime, parameter counts, a reproducible training recipe, or
hardware requirements for local inference. The integration here is a hosted
Azure service.

## Languages, locales, and voice identities

The advertised language count is **23**. Counting the current guide's managed
voice rows gives **97 base voice IDs across 28 locales**. These are not 97
different named speakers: personas such as Grant and Harper recur across
locales.

There is a documentation discrepancy worth retaining: the launch material and
2.1 card introduction say **26 locales**, while the current guide and product
page include 28. The Flash card's enumerated list omits the UK and India English
variants present in the current shared catalog. The table below reflects that
catalog, not an authenticated availability check on every region. [Guide][guide] |
[Product page][product]

| Language | Locale | Base voice names |
| --- | --- | --- |
| Czech | `cs-CZ` | Grant, Harper |
| Danish | `da-DK` | Grant, Harper |
| German | `de-DE` | Grant, Harper, Klaus, Mia |
| English, Australia | `en-AU` | Isla |
| English, United Kingdom | `en-GB` | Emily, Harry |
| English, India | `en-IN` | Dhruv, Priya |
| English, United States | `en-US` | Ethan, Grant, Harper, Iris, Jasper, Olivia, Sage |
| Spanish, Spain | `es-ES` | Marta |
| Spanish, Mexico | `es-MX` | Alejo, Grant, Harper, Valeria |
| Finnish | `fi-FI` | Grant, Harper |
| French | `fr-FR` | Grant, Harper, Marc, Soleil |
| Hindi | `hi-IN` | Arjun, Dhruv, Grant, Harper, Kavya, Priya |
| Hungarian | `hu-HU` | Bence, Grant, Harper, Levente, Lilla, Reka |
| Indonesian | `id-ID` | Grant, Harper |
| Italian | `it-IT` | Grant, Harper, Luca, Rosa |
| Korean | `ko-KR` | Grant, Haena, Harper, Junho |
| Norwegian Bokmal | `nb-NO` | Grant, Harper |
| Dutch | `nl-NL` | Grant, Harper, Sander |
| Polish | `pl-PL` | Grant, Harper |
| Portuguese, Brazil | `pt-BR` | Caio, Grant, Harper, Luana, Pedro, Rafael |
| Portuguese, Portugal | `pt-PT` | Grant, Harper, Rui |
| Romanian | `ro-RO` | Andrei, Elena, Grant, Harper, Ioana, Radu |
| Russian | `ru-RU` | Grant, Harper, Lev, Masha |
| Swedish | `sv-SE` | Grant, Harper |
| Thai | `th-TH` | Grant, Harper, Krit, Nattapong |
| Turkish | `tr-TR` | Aydin, Elif, Grant, Harper |
| Vietnamese | `vi-VN` | Grant, Harper |
| Simplified Chinese | `zh-CN` | Bo, Grant, Harper, Lan, Mei, Wei |

Build a managed voice identifier from the locale, persona, and exact model
suffix. For example:

```text
en-US-Harper:MAI-Voice-2.1
en-US-Harper:MAI-Voice-2.1-Flash
nl-NL-Grant:MAI-Voice-2.1
nl-NL-Sander:MAI-Voice-2.1-Flash
```

Arabic and Japanese are not in this current MAI list. Their availability
elsewhere in Azure Speech does not imply availability for these models.
Similarly, the broader personal-voice service's language count does not expand
the chosen MAI base model's supported languages.

For a controlled multilingual example, supply matching English and Dutch text
and select locale-specific IDs for the same persona. Switching from Grant to
Sander is a new casting choice, not preservation of the original speaker
identity. Naturalness and accent quality deserve native-speaker listening
checks rather than assumptions from the catalog alone.

## Directing a voice with SSML

Speech Synthesis Markup Language specifies the voice and, where supported,
delivery style. The model suffix is part of the voice name; it is not an
OpenAI-style JSON `model` field on an `/audio/speech` request.

```xml
<speak version="1.0"
       xmlns="http://www.w3.org/2001/10/synthesis"
       xmlns:mstts="http://www.w3.org/2001/mstts"
       xml:lang="en-US">
  <voice name="en-US-Harper:MAI-Voice-2.1">
    <mstts:express-as style="excited">
      Stay with us for the quick fire round!
    </mstts:express-as>
  </voice>
</speak>
```

Style names are exact, voice-specific values. For example, the current catalog
lists:

| Voice | Documented styles |
| --- | --- |
| English Harper | `agent`, `angry`, `audiobook`, `confused`, `customer_call_center`, `determined`, `educational`, `embarrassed`, `excited`, `happy`, `hopeful`, `joyful`, `narrator`, `neutral`, `regretful`, `relieved`, `sad`, `shouting`, `softvoice`, `whispering` |
| English Grant | `agent`, `audiobook`, `customer_call_center`, `educational`, `narrator`, `neutral` |
| Dutch Harper | `agent`, `audiobook`, `customer_call_center`, `educational`, `narrator`, `neutral` |
| Dutch Grant | `agent`, `customer_call_center`, `educational`, `narrator`, `neutral` |
| Dutch Sander | `adventurous`, `caringempathy`, `curious`, `encouraging`, `excited`, `friendlycheerful`, `neutral`, `nostalgic`, `reflective`, `saddisappointed`, `serious` |

The notebook intentionally exposes a small documented subset. It uses Harper
for the neutral/excited/whispering comparison, not Grant.

Some official examples conflict with the table: Harper is shown with
`happiness`, while its row lists `happy` and `joyful`; model cards show Grant
with `excited`, which its current row does not list. The general SSML guide says
invalid or missing styles can be ignored in favor of neutral speech. An HTTP
success is therefore not proof that the requested style was applied.

Controls documented for other families should not be inherited without
verification. Examples involving Dragon HD dialogue elements, bracketed
paralinguistic tags, Phoenix styles, role changes, phonemes, visemes, or pitch
controls are not automatically a MAI feature matrix. [SSML guide][ssmlguide] |
[Personal-voice usage][personaluse]

### More than one speaker

The MAI cards describe multi-speaker support, and Azure SSML supports successive
`<voice>` elements. The notebook's prebuilt dialogue uses one element per
speaker turn, in one request.

For personal voices, the model name changes shape:

```xml
<speak version="1.0"
       xmlns="http://www.w3.org/2001/10/synthesis"
       xmlns:mstts="http://www.w3.org/2001/mstts"
       xml:lang="en-US">
  <voice name="MAI-Voice-2.1">
    <mstts:ttsembedding speakerProfileId="YOUR_APPROVED_PROFILE_ID">
      Welcome to our clearly labeled synthetic podcast opening.
    </mstts:ttsembedding>
  </voice>
</speak>
```

The service-generated `speakerProfileId` is not the caller-chosen personal
voice resource ID. The personal model name has no managed persona/locale prefix.

The notebook's cloning walkthrough uses **one consented speaker** and a short
welcome, starting from prerecorded reference and consent files. It does not
assume that multiple personal profiles can be combined in one SSML request.

## API, authentication, and audio output

The MAI guide demonstrates:

```text
POST https://<region>.tts.speech.microsoft.com/cognitiveservices/v1
```

The body is UTF-8 SSML, with `Content-Type: application/ssml+xml`, an
`Ocp-Apim-Subscription-Key` authentication header, a `User-Agent`, and an
`X-Microsoft-OutputFormat`. A successful response is **binary audio**, not JSON.
The key and region must belong to the same resource.

The general REST guide also documents STS bearer tokens and Entra
authentication. STS tokens expire after ten minutes and are scoped to their
issuing endpoint. Current SDK Entra examples support a credential object with a
configured custom-subdomain endpoint. The exact resource ID, scope, endpoint,
and SDK version matter; a raw transcription bearer token should not be copied
into an unrelated TTS route. Custom-subdomain configuration can be irreversible.
The accompanying notebook uses key authentication only. [REST reference][rest] |
[Entra guide][entra]

Python integration through `azure-cognitiveservices-speech` is another option,
especially for synthesis events and stream handling. The notebook uses REST
to keep the core request visible and avoid native SDK dependencies.

For voice discovery, the REST reference documents:

```text
GET https://<resource>.cognitiveservices.azure.com/tts/cognitiveservices/voices/list
```

Metadata can include `ShortName`, `Locale`, `StyleList`, `SampleRateHertz`,
`Status`, and `WordsPerMinute`. A generic sample response is not proof that
every MAI entry is present in every resource's response.

The MAI guide demonstrates `audio-24khz-160kbitrate-mono-mp3`. The notebook uses
the shared API's `riff-24khz-16bit-mono-pcm` format so it can inspect audio
duration and integrity before playback. Shared formats also
include raw PCM, Opus, WebM, and other rates. Availability of a 48 kHz output
container does not by itself establish native 48 kHz model generation.

## Where to run it

The model guide and cards list 14 serving regions and describe globally
accessible requests routed to serving regions. The shared region table marks
nine of those regions in its MAI column:

| Agreement in the current guides | Identifier |
| --- | --- |
| Canada Central | `canadacentral` |
| Central India | `centralindia` |
| East US | `eastus` |
| East US 2 | `eastus2` |
| France Central | `francecentral` |
| Southeast Asia | `southeastasia` |
| Sweden Central | `swedencentral` |
| West Europe | `westeurope` |
| West US 2 | `westus2` |

**East Asia, Japan East, North Europe, West US, and West US 3** appear in the
model-specific lists but have blank MAI cells in the shared table. This may
reflect distinctions between serving infrastructure and resource availability,
but the documents do not resolve it sufficiently to promise access.

Personal voice is separately listed for **West Europe, Sweden Central, East US,
East US 2, West US 2, Southeast Asia, and East Asia**. A region supporting
prebuilt MAI voices is not automatically a cloning region. West Europe or
Sweden Central provides a documented overlap for the podcast workflow.
North Europe is not listed for personal voice. [Regions][regions] |
[Official custom-voice samples][customsamples]

A resource's region is not a blanket data-residency guarantee when
model-specific documentation describes global routing. Confirm the actual
processing scope and preview terms for your workload.

## Personal voice: a lifecycle, not a file drop

MAI's current guidance recommends **5-60 seconds** of clean reference speech
and describes matching the voice without fine-tuning. Natural delivery,
moderate energy, a consistent microphone, and low background noise help.
General personal-voice documentation allows a broader 5-90 second range;
the model-specific range is the relevant choice here.

Personal voice is a **Limited Access** feature, including its demo experience.
Current eligibility is restricted to Microsoft-managed customers working with
account teams. Approval is linked to intended use cases, not merely possession
of an Azure subscription. Each speaker must provide explicit permission and
a recorded acknowledgment matching the required wording.

The documented `2026-01-01` API lifecycle is:

1. Create a project with `PUT /customvoice/projects/<id>` and
   `kind: "PersonalVoice"`.
2. Upload recorded consent through `POST /customvoice/consents/<id>`, including
   project, talent/company names, consent locale, and audio.
3. Wait for consent verification to succeed.
4. Upload the reference through `POST /customvoice/personalvoices/<id>`, with
   `projectId`, `consentId`, and `audiodata`.
5. Wait for creation to succeed, then use the returned `speakerProfileId` in
   synthesis.

Creation responses can contain an ID while the resource is still `NotStarted`.
Check asynchronous completion rather than assuming that ID means readiness.
Operation responses expose an `Operation-Location`; resource GET operations
also expose current status, which the notebook uses in separate check/load
code cells. An existing successful profile can be reused without re-uploading.

The consent locale describes the language of the recorded consent statement,
not the language of the reference clip or the synthesized output. In this demo,
`en-US` consent and Dutch reference/output are configured separately.

No separate professional-voice deployment is required for this personal-voice
workflow. Personal voice and professional custom-voice training/hosting are
different offerings.

[Project setup][project] | [Consent][consent] | [Reference upload][createvoice] |
[Limited Access requirements][limited]

## Privacy and consent after generation

The privacy documentation says input text and generated audio from the
**real-time prebuilt TTS API** are not retained as service content. That does
not cover an application's logs, notebook outputs, saved files, batch results,
or every downstream service.

Personal voice is different. Consent recordings, prompt data, and profiles
are stored. Personal voice does not support Bring Your Own Storage. Microsoft
documents retention of consent data and potential copies of voice models as
necessary for service security/integrity. Speaker verification can involve
biometric voice signatures. The customer remains responsible for permissions,
disclosures, applicable privacy requirements, and approved use.

Do not describe cloning as zero-retention or claim deleting a profile overrides
all security-retention exceptions. Disclose synthetic speech and do not use it
to imply an unsuspecting person actually said something. The supplied podcast
scripts are not themselves consent to clone anyone.

The notebook's audio players contain generated bytes. Saved widget state can
retain those bytes even when a visible cell looks clean. Clear outputs and
saved widget state before sharing, and obtain appropriate permission before
distributing personal audio. [Privacy and security][privacy] |
[Transparency note][transparency]

No reference or consent recordings are distributed with this repository.
The example filenames are local paths, not downloadable samples. Keep those
files private; Git ignores `samples/` and WAV files, but that does not remove
audio embedded in notebook outputs or protect files deliberately force-added.
The publication copy must therefore also have all outputs, attachments, saved
widget state, and private configuration removed.

## Price, billing units, and demo budgets

The October 1 announcement and current model cards publish:

| Spoken-character baseline | 2.1 at $22/million | Flash at $15/million |
| --- | --- | --- |
| 1,000 | $0.022 | $0.015 |
| 5,000 | $0.110 | $0.075 |
| 10,000 | $0.220 | $0.150 |
| 100,000 | $2.20 | $1.50 |

These are illustrative USD synthesis estimates, not subscription-specific
quotes. Actual rates depend on the applicable offer, currency, and region.
No voice-price expiration was established in the reviewed announcement;
the transcription promotional end date should not be applied to voice.

The shared billing guide counts spaces, punctuation, and applicable SSML
markup, excluding the `<speak>` and `<voice>` tags. It also describes special
weighting for Chinese characters, including applicable kanji/hanja/hanzi.
Consequently, Python string length is only a text-based estimate, not an exact
billable-character calculator.

Every requested variation is another synthesis: two models, three styles,
or regenerating the same text all add calls. Replaying downloaded bytes does
not. A timeout is not proof the request was unprocessed or unbilled.

Personal profiles additionally incur daily storage charges until removed;
less than a full day may still be billed as a day. Voice Live has its own
model/tier/token billing rather than simply inheriting standalone TTS prices.
Generic Neural free-tier allowances do not establish MAI preview entitlement.
[Pricing][pricing] | [Billing overview][overview]

## Latency: measure the interval you actually show

The Microsoft AI product page reports roughly **550 ms model inference** for
2.1 and **45 ms** for Flash. The launch article separately reports **150 ms
end-to-end latency** for a Flash example producing 45 seconds of audio.
These are vendor claims with different scopes, not guarantees for a notebook.

The notebook measures from the start of the HTTP operation through receipt of
the complete audio response. That includes connection/network behavior and
does not measure when a listener first hears sound. It deliberately avoids
labeling that number "inference latency" or "streaming latency."

For deeper instrumentation, the Speech SDK exposes:

| Metric | Property |
| --- | --- |
| Client first audio | `SpeechServiceResponse_SynthesisFirstByteLatencyMs` |
| Client complete audio | `SpeechServiceResponse_SynthesisFinishLatencyMs` |
| Network latency | `SpeechServiceResponse_SynthesisNetworkLatencyMs` |
| Service first audio | `SpeechServiceResponse_SynthesisServiceLatencyMs` |

Keep script, voice, locale, style, output format, and resource fixed when
comparing models. Separate cold connections from reused connections, repeat
manually, and report variability. Listen for omitted/repeated text, timing,
pronunciation, intelligibility, and style—not just speed. Transcribing the
output may help find errors, but introduces an ASR model's errors and is not
a complete voice-quality measure. [Latency guide][latency]

## Streaming, long-form synthesis, and service limits

Streaming audio output, streaming text input, and a live conversational agent
are separate features. The shared SDK text-input streaming route uses:

```text
wss://<region>.tts.speech.microsoft.com/cognitiveservices/websocket/v2
```

That route accepts partial text, configures voice globally, and does **not**
support SSML. Exact MAI support must be verified; it cannot simply inherit the
notebook's SSML-based expression controls.

For long audio, the shared asynchronous batch API uses:

```text
PUT https://<resource>.cognitiveservices.azure.com/texttospeech/batchsyntheses/<id>?api-version=2024-04-01
```

Batch synthesis can produce audio longer than ten minutes. MAI-2.1 support,
boundary events, and optional batch properties need separate confirmation.
The older Long Audio API is scheduled to retire on April 1, 2027.

Important shared quotas include:

| Surface | Documented limit |
| --- | --- |
| Synchronous TTS audio | 10 minutes; REST reference describes truncation beyond this |
| Distinct voice/audio tags | Combined maximum 50 per SSML request |
| WebSocket SSML | 64 KB per turn |
| Standard S0 TTS | 30 TPS default; adjustments up to 1,000 described |
| Personal-voice management | 50 requests per 10 seconds on S0 |
| Batch JSON payload / inputs | 2 MB / up to 10,000 inputs |
| Batch management | 100 requests per 10 seconds |

These are shared service limits, not a model-specific preview entitlement.
HTTP 429 may reflect regional voice capacity rather than subscription quota.
Raising a quota does not necessarily solve it. [Quotas][quotas] |
[Batch synthesis][batch]

Voice Live adds recognition, a chat model, turn handling, interruption, and
output speech. Its current guide shows `MAI-Voice-2-Flash` in an output-voice
example, whereas the current MAI guide uses `MAI-Voice-2.1-Flash`. Do not assume
an undocumented alias. Verify the accepted identifier and processing scope
before building that separate integration. [Voice Live][voicelive]

## Applying this to A Bit of AI

The [notebook](demo.ipynb) follows a single production story. A short welcome
establishes the voice. Repeating one line with different styles lets the
audience hear direction rather than just read a feature list. English and Dutch
welcomes explore identity across languages. The model comparison makes the
quality, timing, and price choices concrete. Finally, the hosts exchange their
opening lines using prebuilt voices. An optional step-by-step cloning workflow
then gives a short welcome your own consented voice.

The original scripts remain editable and the paid actions remain explicit.
That keeps the focus on what the models can contribute to a podcast, while
making their limits, operational dependencies, and consent obligations visible.

[guide]: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-voices
[launch]: https://microsoft.ai/news/our-first-streaming-transcription-model/
[product]: https://microsoft.ai/models/mai-voice-2-1/
[card]: https://microsoft.ai/pdf/MAI-Voice-2.1-Model-Card-Memo.pdf
[flashcard]: https://microsoft.ai/pdf/MAI-Voice-2.1-Flash-Model-Card-Memo.pdf
[voice1]: https://microsoft.ai/news/two-new-in-house-models/
[voice2card]: https://microsoft.ai/pdf/MAI-Voice-2-Model-Card.PDF
[ssmlguide]: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup-voice
[personaluse]: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/personal-voice-how-to-use
[rest]: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-text-to-speech
[entra]: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-configure-azure-ad-auth
[regions]: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/regions?tabs=tts
[customsamples]: https://github.com/Azure-Samples/cognitive-services-speech-sdk/tree/master/samples/custom-voice
[project]: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/personal-voice-create-project
[consent]: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/personal-voice-create-consent
[createvoice]: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/personal-voice-create-voice
[limited]: https://learn.microsoft.com/en-us/azure/foundry/responsible-ai/speech-service/text-to-speech/limited-access
[privacy]: https://learn.microsoft.com/en-us/azure/foundry/responsible-ai/speech-service/text-to-speech/data-privacy-security
[transparency]: https://learn.microsoft.com/en-us/azure/foundry/responsible-ai/speech-service/text-to-speech/transparency-note
[pricing]: https://azure.microsoft.com/en-us/pricing/details/speech/
[overview]: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech
[latency]: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-lower-speech-synthesis-latency
[quotas]: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-services-quotas-and-limits
[batch]: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/batch-synthesis
[voicelive]: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live-how-to
