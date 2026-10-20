# MAI-Transcribe-2: from conversation to usable text

A recording captures a conversation, but finding something inside it still
takes work. You might remember a decision without remembering when it was made,
want to revisit a particular speaker's explanation, or need a readable version
of an interview. Transcription makes those recordings easier to use, especially
when the text stays connected to the people speaking and the original audio.

**MAI-Transcribe-2** is Microsoft's speech-to-text model for completed
recordings. Available through Azure Speech in Microsoft Foundry, it combines
multilingual recognition with speaker labels, timestamps, and a choice of
transcription styles. The result can be more than a block of text: it can become
a way to explore a conversation.

The availability, prices, and API details below reflect Microsoft's documentation
as of **October 20, 2026**. Announcement benchmarks are attributed to their
publishers rather than presented as measurements from the accompanying notebook.

## Where the model fits

MAI-Transcribe-2 is a model, while **Azure Speech in Microsoft Foundry** is the
managed service that exposes it. **Fast transcription** is the synchronous
file-processing API: the application sends a recording and waits for the
result. That API can run different models, so using the endpoint alone does not
establish that a request used MAI-Transcribe-2.

The default model on this surface is Azure Transcribe. Enhanced mode also
provides access to Azure LLM Speech, while MAI-Transcribe-2 is selected explicitly
by name. Azure Speech's asynchronous **batch transcription** is a different
workflow for processing stored recordings as jobs; it is not another name for
the MAI fast-transcription request.

The version matters when following older tutorials. Microsoft's
[MAI documentation](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-transcribe)
lists MAI-Transcribe-1 as deprecated on August 20, 2026, and still lists
MAI-Transcribe-1.5 as supported. Microsoft announced MAI-Transcribe-2 on
September 3, followed by the separate streaming model on October 1.
Version 1 examples, prices, and availability should not be carried over to
version 2. Similarly, MAI-Voice generates speech from text; it is not a
transcription model.

## A transcript in the speaker's language

MAI-Transcribe-2 supports 60 languages, including English and Dutch. It detects
the language automatically by default, so an application can process an English
interview and a Dutch conversation without selecting a different model. When
the language is known, a request can supply a single language hint through
`locales`.

The model also supports speech that switches languages. Microsoft's
documentation gives Hinglish and Spanglish as examples, although support does
not imply equal accuracy for every language pair, accent, or recording
condition. The [model documentation](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-transcribe)
lists all supported languages and their codes.

### The 60 supported languages

The file-model guide and streaming overview publish the same language set:

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

Dutch support means a Dutch recording can be transcribed by the model. It does
not establish identical performance across regional accents or mixed
Dutch/English sentences. A language hint is useful when the language is certain;
automatic detection is useful when the application does not know it in advance.

Transcription preserves the language being spoken; it does not translate the
recording into another language. Translation and free-form prompting are
features of the separate
[Azure LLM Speech model](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/llm-speech),
which shares the fast-transcription API surface but is not MAI-Transcribe-2.

## Following the conversation

In a conversation with several people, knowing *who said what* can be as useful
as the words themselves. Speaker diarization separates speech into turns and
assigns anonymous speaker labels. Those labels help a reader follow a discussion,
but they do not identify people by name or establish that a speaker in one
recording is the same person in another.

Timestamps connect those turns back to the recording. MAI-Transcribe-2 can
return segment-level timing or more detailed word-level timing. An application
can use that information to let someone select a word and listen to the
surrounding audio, rather than searching through the entire recording.

These are complementary capabilities: diarization organizes the conversation,
while timestamps make it navigable. The service supplies the transcript and
metadata; playback controls, highlighting, and subtitle formatting are features
an application builds on top. Overlapping speech and poor audio can still cause
recognition or speaker-attribution errors, so the recording remains important
when checking a transcript.

Speaker diarization is also different from separating audio channels. A stereo
file might place each participant on a different channel, but the
[shared API feature matrix](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/fast-transcription-create)
does not list independent stereo-channel transcription for MAI-Transcribe-2.
Channel handling available with Azure Transcribe should not be assumed to
transfer to MAI. The accompanying notebook uses mono recordings.

## Choosing between verbatim and clean text

Spoken language rarely reads like a finished document. People hesitate, repeat
themselves, start a sentence again, and correct what they just said.
MAI-Transcribe-2 offers two styles for different uses of that speech.

**Verbatim** is the default style and preserves fillers, false starts, and
self-corrections. It is useful when the way something was said matters, or when
comparing the transcript closely with the recording. **Clean** produces a more
readable transcript by removing verbal clutter such as fillers.

Clean output is still a transcript, not a summary. It does not turn a meeting
into action items or decide which points matter most. Those tasks require
separate processing. Likewise, choosing verbatim does not guarantee a
word-perfect record: either style needs human review before use in consequential
settings.

## Helping with specialized vocabulary

Product names, acronyms, and domain-specific terms can be difficult to recognize
from sound alone. Keyword hints let an application provide relevant vocabulary
through `phraseList.phrases`. For example, a recording about an AI project might
include hints for "Microsoft Foundry" and "MAI-Transcribe".

Hints bias recognition toward likely terms; they are not replacements that force
particular words into the transcript. Their effect depends on the recording,
and a hint does not guarantee the correct spelling. Comparing the same audio
with and without hints is a useful way to understand whether they help with
your vocabulary.

This is a vocabulary list, not a general-purpose instruction prompt. Requests
such as "translate this into English" or "summarize the discussion" are not
documented MAI-Transcribe-2 keyword-hint features. Noise robustness is likewise
a model capability rather than a switch: there is no option here that guarantees
correct recognition of an unclear recording.

## From an audio file to a structured response

MAI-Transcribe-2 uses the synchronous fast-transcription API. An application
uploads a completed recording and receives a structured JSON response when
processing finishes. The model-specific documentation lists WAV, MP3, and FLAC
as supported formats.

### The resource and request

An application needs an Azure subscription and a supported Foundry or Speech
resource with access to the model. The file-transcription guide selects the
model inside the request; unlike the streaming Realtime route, it does not
document a separate named model deployment as a prerequisite. Actual access
still depends on the resource, region, and subscription.

The request goes to the Speech resource's transcription endpoint:

```text
POST https://<resource-name>.cognitiveservices.azure.com/speechtotext/transcriptions:transcribe?api-version=2025-10-15
```

The multipart request contains an `audio` file and a JSON-serialized `definition`
field. This definition selects MAI-Transcribe-2 and asks for word timestamps,
verbatim text, speaker diarization, and vocabulary hints:

```json
{
  "enhancedMode": {
    "enabled": true,
    "model": "MAI-Transcribe-2",
    "modelOptions": {
      "timestamps": "word",
      "transcribeStyle": "verbatim"
    }
  },
  "diarization": {
    "enabled": true
  },
  "phraseList": {
    "phrases": ["Microsoft Foundry", "MAI-Transcribe"]
  }
}
```

The explicit model name matters. Enabling enhanced mode without selecting MAI
uses the Azure LLM Speech path instead. Changing `transcribeStyle` to `"clean"`
requests the alternative output style. Timestamps can also be requested at
`"segment"` granularity or disabled with `"none"`, the documented default.

For a minimal request, only `enhancedMode.enabled` and
`enhancedMode.model` are needed in the definition. The following shell example
assumes the resource endpoint and key have already been supplied securely in
the environment:

```bash
curl --fail-with-body --silent --show-error \
  "${SPEECH_ENDPOINT%/}/speechtotext/transcriptions:transcribe?api-version=2025-10-15" \
  --header "Ocp-Apim-Subscription-Key: ${SPEECH_KEY}" \
  --form 'audio=@./sample.wav' \
  --form 'definition={"enhancedMode":{"enabled":true,"model":"MAI-Transcribe-2"}}'
```

`SPEECH_ENDPOINT` is the resource root URL, not a Foundry project URL and not a
URL with the transcription path already appended. Curl creates the multipart
boundary automatically. The richer JSON definition above goes into that same
`definition` form field when those features are needed.

### Reading the response

The response contains both text and the structure needed to connect it back to
the recording:

| Response field | Meaning |
| --- | --- |
| `durationMilliseconds` | Duration of the input audio, not request latency |
| `combinedPhrases[].text` | Combined transcript text |
| `phrases[].text` | Text for an individual segment |
| `phrases[].speaker` | Anonymous speaker label when diarization is enabled |
| `phrases[].locale` | Language or locale information |
| `offsetMilliseconds` | Start position of a segment or word when timing is enabled |
| `durationMilliseconds` within a segment or word | Duration of that segment or word |
| `phrases[].words[]` | Word-level text and timings when requested |
| `confidence` | A schema field that should not be treated as a calibrated accuracy score |

Applications should handle the fields returned for their selected configuration
rather than assuming every optional field is always present. For example, word
navigation depends on requesting word timestamps, and speaker rendering depends
on diarization.

A response may also contain a `confidence` field. The model card includes an
example with `confidence: 0`; that should not be interpreted as "0% accuracy."
Transcript quality needs to be evaluated against the recording rather than
inferred from an uncalibrated schema field.

The [fast-transcription guide](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/fast-transcription-create)
and [REST reference](https://learn.microsoft.com/en-us/rest/api/speechtotext/transcriptions/transcribe?view=rest-speechtotext-2025-10-15)
explain authentication and the response structure. Resource keys must stay out
of source control and client-side application code; Microsoft also documents
Entra ID authentication for the service.

The API supplies structured transcription data, not an entire user interface.
TXT/JSON downloads, synchronized playback, captions, and search are application
features. A summary or action-item list adds a separate processing step rather
than revealing another field in the transcription response.

## Availability, cost, and practical limits

### Choosing a region

As of October 20, 2026, the
[Speech regions documentation](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/regions?tabs=llmspeech)
lists the following regions for MAI file transcription:

| Region | Azure identifier |
| --- | --- |
| Central India | `centralindia` |
| East US | `eastus` |
| North Europe | `northeurope` |
| Southeast Asia | `southeastasia` |
| West US | `westus` |
| West US 2 | `westus2` |

Availability should be checked for the chosen resource and subscription,
including the deployment's current release status and applicable terms.
The file-model card describes global access with requests routed to serving
regions; the resource's location is not, by itself, a data-residency guarantee.

### Understanding the bill

Microsoft announced an introductory price of **$0.10 per hour of audio** for
MAI-Transcribe-2 through the end of 2026. At that rate, ten minutes of audio costs
about $0.017 for transcription alone. Processing the same recording again, for
example to compare clean and verbatim output, adds another transcription
request. The [launch announcement](https://microsoft.ai/news/mai-transcribe-2-is-the-fastest-most-accurate-and-cheapest-speech-recognition-model-in-the-world/)
describes the offer; consult [Azure Speech pricing](https://azure.microsoft.com/en-us/pricing/details/speech/)
for current prices, currency, and applicable terms.

The separate streaming model has an announced introductory rate of **$0.54 per
audio hour** through December 31, 2026, according to its
[model card](https://microsoft.ai/pdf/MAI-Transcribe-2-Streaming-Model-Card-Memo.pdf).
The difference becomes clearer when expressed as audio-processing costs:

| Audio processed | File model at $0.10/hour | Streaming model at $0.54/hour |
| --- | --- | --- |
| 10 minutes | About $0.017 | $0.09 |
| 1 hour | $0.10 | $0.54 |
| 10 hours | $1.00 | $5.40 |

These examples exclude application hosting, storage, network charges, and any
downstream model use. Repeated submissions and retries can add to usage.
Voice Live has its own billing surface; these standalone transcription rates
are not a price for a complete voice-agent session.

Fast transcription is not supported on the **Free F0** tier. The five free
monthly hours described on the Speech pricing page apply to Standard/Custom
realtime transcription on F0, not an established free MAI entitlement. The
$0.36/hour in the
[original MAI-Transcribe-1 announcement](https://microsoft.ai/news/state-of-the-art-speech-recognition-with-mai-transcribe-1/)
is historical, not the version 2 rate. Prices after the introductory offer
should be checked on the current
[Speech](https://azure.microsoft.com/en-us/pricing/details/speech/) and
[Foundry model pricing](https://azure.microsoft.com/en-us/pricing/details/ai-foundry-models/microsoft/)
pages for the relevant currency and subscription offer.

### File sizes, duration, and quotas

The model-specific guide explicitly lists WAV, MP3, and FLAC. The shared API
accepts additional formats, but that does not establish identical format support
across every model behind the endpoint.

Published size and duration limits also differ:

| Source | Published file limit | Scope |
| --- | --- | --- |
| [MAI-Transcribe-2 model card](https://microsoft.ai/pdf/MAI-Transcribe-2-Model-Card.pdf), September 3 | 300 MB / two hours | Model-specific launch information |
| [REST reference for API `2025-10-15`](https://learn.microsoft.com/en-us/rest/api/speechtotext/transcriptions/transcribe?view=rest-speechtotext-2025-10-15) | Smaller than 250 MB and shorter than two hours | Generated API reference |
| [Fast-transcription guide](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/fast-transcription-create) and [quotas page](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-services-quotas-and-limits) | Smaller than 500 MB and shorter than five hours | Shared service documentation |
| [MAI model guide](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-transcribe) | Refers to the REST reference and notes shorter recordings for diarization | Does not resolve the exact diarization cap |

The largest shared limit should not be treated as the effective maximum for
every model. For longer recordings, verify the combination of model, API version,
and diarization settings before relying on an upper limit. Short clips avoid
these boundary conditions, but successful processing of a short clip says
nothing about a resource's maximum supported duration.

The quotas page lists a shared fast/batch request-rate quota of **600 requests
per minute**. That is a request-rate limit, not a promise of concurrent capacity
or a latency guarantee. Streaming deployment limits should be checked separately
rather than inferred from these file-processing quotas.

## Understanding speed and accuracy

Microsoft's announcements and model cards report strong benchmark results.
Those results describe particular datasets and measurement conditions, not a
guarantee for every interview, meeting, or microphone:

| Published result | Source and context | What it does not establish |
| --- | --- | --- |
| 5.2% average word error rate across 60 languages on FLEURS | [September 3 file-model announcement](https://microsoft.ai/news/mai-transcribe-2-is-the-fastest-most-accurate-and-cheapest-speech-recognition-model-in-the-world/) | The error rate on a particular recording |
| Second on the Artificial Analysis WER leaderboard at launch | File-model announcement and [model card](https://microsoft.ai/pdf/MAI-Transcribe-2-Model-Card.pdf) | A permanent ranking across all models and tasks |
| Up to 10x faster than named competitors | File-model announcement, referencing Artificial Analysis evaluations | A speedup for every workload or future model version |
| Approximately one hour of audio processed in ten seconds | File-model card example | An upload-time guarantee or latency SLA |
| 2.5% average final-transcript WER in the published streaming comparison | [October 1 streaming model card](https://microsoft.ai/pdf/MAI-Transcribe-2-Streaming-Model-Card-Memo.pdf) | A directly comparable result to the file model's FLEURS score |
| First streaming partials just over 100 ms after receiving audio | [October 1 streaming announcement](https://microsoft.ai/news/our-first-streaming-transcription-model/) | End-to-end microphone-to-screen latency |

The 5.2% file result and 2.5% streaming result come from different evaluations.
They do not show that streaming halves the file model's errors. Rankings and
comparative claims are also dated observations, not permanent properties of a
service.

### Measuring performance on your recordings

For file transcription, measure elapsed request time separately from audio
duration. Network transfer and service processing both contribute to the time
the caller observes. For streaming, distinguish time to first provisional text
from time to final text after a commit; audio capture, buffering, network travel,
and rendering add to the model's own processing time.

Accuracy starts with a human-reviewed reference transcript. Word error rate
counts substitutions, deletions, and insertions relative to the number of words
in that reference. Comparisons need consistent normalization and tokenization,
including language-appropriate handling rather than assuming all languages use
whitespace-separated words.

Clean mode deliberately removes some spoken disfluencies. Comparing its output
to an unchanged verbatim reference can count intended editing as errors, so the
evaluation should match the output style. Average scores also hide important
mistakes: a wrong name, number, negation, or speaker assignment may matter more
to an application than several minor wording differences.

## File transcription is different from live captions

Uploading a recording and getting a fast response is not the same as receiving
text while someone is speaking. Microsoft provides a separate model,
**MAI-Transcribe-2-Streaming**, for continuous audio and incremental transcripts.
It returns provisional text that can change as more speech arrives, alongside
finalized text.

The streaming model is in **public preview**, without an SLA, as of October 20,
2026. Its documentation does not recommend production use. Its configuration and
capabilities should not be assumed to match the file model, and repeatedly
uploading small files is not equivalent to using its streaming protocol.
The notebook in this repository focuses on completed recordings; the following
details explain the separate integration needed for live captions.

### Regions and integration choices

The [streaming overview](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-transcribe-2-streaming)
lists Sweden Central (`swedencentral`), Central US (`centralus`), East US 2
(`eastus2`), and Southeast Asia (`southeastasia`). The October 1 model card lists
East US 2 as "coming soon," while the October 7 Learn overview lists it as
available. The newer operational documentation is the better starting point,
with access still subject to the target subscription.

Only Southeast Asia appears in both the file and streaming region lists.
In particular, North Europe for file transcription and Sweden Central for
streaming are different regions. A single European resource should not be
assumed to support both paths.

There are two documented integration routes:

| Route | Resource and model selection | Application fit |
| --- | --- | --- |
| [Azure Speech SDK](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-transcribe-2-streaming-speech-sdk) | The guide specifies SDK v1.52.0 and a supported Foundry or Speech resource; select `mai-transcribe-2-streaming` | SDK-managed audio and connection handling |
| [Realtime-compatible WebSocket API](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-transcribe-2-streaming-realtime) | A Foundry resource with a deployed streaming model; configure the session with the **deployment name** | Direct control over audio buffers, transcript events, and commits |

The SDK guide provides Python, C#, Java, and C++ examples. Those examples do not
establish equivalent JavaScript SDK support. The SDK's model identifier and the
Realtime route's deployment name are not interchangeable setup instructions.

### Configuring a Realtime session

The WebSocket endpoint is:

```text
wss://<resource-name>.services.ai.azure.com/mai/v1/realtime?intent=transcription
```

The client configures a transcription session before sending audio. This
example selects 16 kHz audio and leaves language detection automatic:

```json
{
  "type": "session.update",
  "session": {
    "type": "transcription",
    "audio": {
      "input": {
        "format": {
          "type": "audio/pcm",
          "rate": 16000
        },
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

Audio must be raw, signed little-endian **PCM16, mono, at 16 kHz or 24 kHz**,
base64-encoded, without a WAV header. This differs from uploading a WAV file to
the file API. Browser `MediaRecorder` output is commonly compressed or
containerized; a browser integration therefore needs an appropriate capture
and resampling path rather than forwarding arbitrary recorder output.

After successful session configuration, the client sends
`input_audio_buffer.append` messages while also receiving transcript events.
The guide suggests 10-20 ms audio chunks for low latency; larger chunks trade
latency for fewer messages. Session settings cannot change after the first
audio append, even after a commit.

The documented route supports only `null` for `turn_detection` and
`noise_reduction`: it does not provide server-side speech detection or automatic
commits. The client sends `input_audio_buffer.commit` at a natural pause or at the
end of recording. An explicit Stop/Finalize control or client-side voice-activity
detection can decide when to do that. A session can last **up to one hour**.

### How evolving text becomes a final transcript

The event types have different meanings. Treating every event as text to append
creates duplicated or stale captions:

| Event | Meaning | How the application uses it |
| --- | --- | --- |
| `conversation.item.input_audio_transcription.delta` | Newly finalized text | Append exactly as received, preserving spacing |
| `conversation.item.input_audio_transcription.intermediate` | The entire current provisional suffix | Replace the previous provisional suffix |
| `conversation.item.input_audio_transcription.completed` | The full final transcript for the interval since the previous commit | Reconcile that interval instead of appending text already accumulated from deltas |
| `input_audio_buffer.committed` | The commit was accepted | Continue receiving; acceptance does not mean transcription has finished |

An application needs to track the relevant items or intervals and visually
distinguish provisional text from finalized text. Revision of a provisional
suffix is normal, not an error. Stopping capture should still allow buffered
audio to be sent and final results to arrive before the interface declares the
transcript complete.

The streaming guides do not document equivalents for all file-model options.
In particular, diarization, keyword hints, clean/verbatim style, and word
timestamps should not be assumed to work through this protocol.

### Connecting a browser safely

The Realtime guide supports Entra bearer tokens or an API key. Native browser
WebSockets cannot set the documented custom authentication headers. Although
query-string keys are described, a long-lived service key should not be exposed
in browser code or in URLs that can be logged.

A backend relay keeps those credentials server-side: the browser captures
audio, the backend maintains the authenticated Azure connection, and transcript
events flow back to the browser. Any short-lived browser credential mechanism
needs to be supported by this exact endpoint rather than assumed from another
realtime product.

Streaming applications also need bounded buffering and visible error states.
A lost connection or dropped audio should not leave apparently current captions
on screen. Microphone capture should stop on Stop, navigation, or failure, and
reconnect behavior should make any gap in the transcript clear.

## When a different model is a better fit

MAI-Transcribe-2 is one option in a wider set of speech services. The distinction
matters most when an application needs a capability beyond its documented
transcription features.

### Azure Transcribe and Azure LLM Speech

**Azure Transcribe**, the default model on the fast-transcription surface,
supports diarization, phrase lists, language identification, word/segment timing,
and channel handling. It provides a baseline under the same API, but the
[feature matrix](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/fast-transcription-create)
should guide which options apply to which model.

**Azure LLM Speech** is the relevant alternative for custom prompts or speech
translation. The current guide names its service-managed release
**Azure LLM Speech 07 2026**; that release label is not a selectable model ID.
Its documented translation target codes are `de`, `en`, `es`, `fr`, `it`, `ko`,
`ja`, `pt`, and `zh`. Dutch transcription support does not imply Dutch is a
translation target. These are
[Azure LLM Speech capabilities](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/llm-speech),
not additional MAI-Transcribe settings.

### OpenAI models hosted on Azure

Azure also offers
[OpenAI transcription workflows](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/transcribe-overview),
including Whisper and newer transcription offerings. These are OpenAI-built
models hosted through Microsoft services, not Microsoft-authored MAI models.
They have their own deployment names, routes, limits, and feature support.
File-based and realtime workflows remain separate even when the provider is
the same.

### Open-model audio understanding

[Phi-4-multimodal-instruct](https://huggingface.co/microsoft/Phi-4-multimodal-instruct)
is Microsoft's open multimodal model for audio, images, and text, with text
output. Its audio tasks include speech recognition, translation, question
answering, and summarization. This makes it a different kind of tool from a
managed transcription endpoint and introduces model-runtime and hardware
considerations.

Its model card lists English, Chinese, German, French, Italian, Japanese,
Spanish, and Portuguese as audio languages. Dutch is listed for text, **not
audio**. It should not be assumed to offer the same Dutch speech support as
MAI-Transcribe-2.

The MAI sources linked here do not document downloadable weights or local
container deployment for MAI-Transcribe-2. General Azure Speech container
availability does not establish that MAI can run locally.

## Looking after recordings and transcripts

Audio and transcripts can contain personal or confidential information. Use
recordings you have permission to process, obtain the necessary speaker consent,
and decide how your application handles uploads, logs, and exported text.

Microsoft's [Speech privacy documentation](https://learn.microsoft.com/en-us/azure/foundry/responsible-ai/speech-service/speech-to-text/data-privacy-security)
states that customer data is not retained or stored by the service for fast
transcription. That does not automatically cover copies saved by your own
application or any downstream service. Likewise, a resource's region alone is
not sufficient to establish a data-residency guarantee; applicable processing
and routing terms still matter.

The privacy documentation distinguishes fast and realtime transcription from
asynchronous batch transcription, which has its own storage and retention
controls. Preview-specific terms and the actual streaming deployment also need
to be considered before extending a general service statement to that route.
Browser buffers, backend logs, observability platforms, and downstream models
are all separate parts of the application's data handling.

Prefer appropriately licensed or original recordings with speaker consent, and
avoid publishing a recording at a public URL just to make it accessible to an
application. Logs should contain only the metadata necessary to diagnose
failures, not credentials, full audio payloads, or transcripts by default. A
live interface should clearly show when the microphone is active.

Transcripts are useful working material, not an unquestionable record.
Names, numbers, negations, and speaker attribution deserve particular attention
when reviewing them. Keeping the text connected to the source audio makes that
review easier.

If transcript text is passed to an assistant or agent, it remains untrusted
content rather than an instruction to execute tools. Keep that boundary explicit,
and do not trigger irreversible actions from provisional speech hypotheses.
Anonymous speaker labels likewise should not be used as biometric identity
verification.

## Explore the features in the notebook

The [feature notebook](demo.ipynb) follows a recording from playback to a
speaker-labeled transcript, then uses word timestamps to revisit individual
moments. It compares clean and verbatim output, adds keyword hints, and supports
a Dutch recording to explore automatic language detection. Optional TXT and
JSON exports make the results available for further use.

Follow the [demo instructions](demo-instructions.md) to configure Azure access
and prepare your recordings. For more examples and model details, continue with
the [MAI-Transcribe-2 documentation](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-transcribe)
or the [model card](https://microsoft.ai/pdf/MAI-Transcribe-2-Model-Card.pdf).

For a no-code starting point, the
[Foundry Speech-to-text playground](https://aka.ms/foundry-speech-to-text)
provides transcript, JSON, and code views as described in the fast-transcription
guide. Explicitly select MAI-Transcribe-2: opening "Fast transcription" or
enabling enhanced mode alone does not establish which model is running.
The [Microsoft AI model directory](https://microsoft.ai/models/) and
[Microsoft AI Playground](https://playground.microsoft.ai/) provide broader
entry points into the model family.

[Back to the model introduction](README.md)
