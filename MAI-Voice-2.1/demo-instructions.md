# MAI-Voice-2.1: demo instructions

[Model introduction](README.md) | [Extended information](information.md) | [Notebook](demo.ipynb)

The notebook creates an A Bit of AI podcast opening using Azure Speech's REST
API. The core demos need text, a voice-enabled resource, and its key. Recording
uploads are required only for the optional personal-voice workflow.

## GitHub Codespaces

The shared dev container installs Python 3.11, Jupyter, ipywidgets, the notebook
dependencies, Azure CLI, and FFmpeg. No separate server or forwarded port is
needed when using the VS Code notebook editor.

1. Create or select a Speech/Foundry resource that supports the chosen MAI
   voices. **West Europe (`westeurope`)** is a recommended starting point;
   **Sweden Central (`swedencentral`)** is another. Availability and preview access
   must be checked for your subscription.
2. Add **Codespaces development environment secrets** in GitHub settings, with
   access to this repository:

   | Secret | Value |
   | --- | --- |
   | `VOICE_SPEECH_REGION` | Region of the voice resource, for example `westeurope` |
   | `VOICE_SPEECH_KEY` | Key from that same resource |
   | `VOICE_SPEECH_ENDPOINT` | Only for Demo 6: custom-subdomain root such as `https://your-voice-resource.cognitiveservices.azure.com` |

3. Create a codespace on the branch containing this demo, or rebuild an existing
   container after pulling these changes.
4. Open `MAI-Voice-2.1/demo.ipynb` and select **Python (MAI demos)**. If necessary,
   select `/home/vscode/.venvs/mai-demos/bin/python`.
5. Run the imports and configuration cells, then run individual synthesis cells
   to generate audio. Each synthesis cell sends paid requests immediately.
   Skip the optional examples you do not want to run.

Stop and restart the codespace after changing Codespaces secrets. These are
process environment variables; rerunning a configuration cell alone cannot
refresh values supplied by the Codespaces host.

The `VOICE_` prefix deliberately separates these settings from the transcription
demo's `SPEECH_KEY` and `SPEECH_ENDPOINT`. Do not mix a key from a North Europe
transcription resource with a West Europe voice region.

Codespaces compute and Azure usage are billed separately. Container setup does
not provision resources, synthesize speech, or upload recordings.

## Local setup

Use Python 3.9 or later; a current Python 3.11+ linked against OpenSSL is
recommended, particularly on macOS.

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r MAI-Voice-2.1/requirements.txt
python -m ipykernel install --user --name mai-demos --display-name "Python (MAI demos)"
cd MAI-Voice-2.1
mkdir -p samples
cp -n .env.example .env
python -m jupyterlab --ContentsManager.allow_hidden=True
```

Edit `.env` beside the notebook; never paste keys into notebook cells. In
JupyterLab, enable **View > Show Hidden Files** if needed. Keep the server local
and authenticated. VS Code notebooks work with the same environment.

The kernel's working directory must be `MAI-Voice-2.1`, where the notebook,
helper modules, scripts, and `.env` reside. Configuration reads this `.env`
fresh without changing the process environment or searching parent folders.
Environment variables take precedence, including intentionally empty values.

After a local `.env` edit, rerun the configuration cell. This rebinds `post_ssml`
to a client using the latest settings. If using personal voice, also rerun its
Step 2 configuration cell to recreate the client, then load the profile again
in Step 7. Configuring the client does not make API calls.

After updating `voice_demo.py`, restart the kernel and rerun imports and
configuration so Python loads the new helper code. Choose **Restart Kernel**,
not **Restart and Run All**. If Jupyter reports external notebook changes,
choose **Reload** to load the version on disk.

## Authentication and availability

This notebook implements **resource-key authentication** for the documented
regional TTS route:

```text
POST https://<region>.tts.speech.microsoft.com/cognitiveservices/v1
```

Azure also supports Entra/SDK configurations, but those require a matching
endpoint and permission setup and are not implemented by this notebook.
Installing Azure CLI does not make this key-based client use your CLI session.

The model guide and general region table disagree about North Europe, East
Asia, Japan East, West US, and West US 3. The notebook warns for these regions;
it never silently chooses another. **North Europe is not listed for personal
voice.** West Europe and Sweden Central agree across the relevant lists.

Both models are public preview, without an SLA. Generic Neural TTS free-tier
allowances do not establish a free MAI entitlement. Verify billing and access
for the selected resource.

## Run and present

Every synthesis example follows the same visible sequence:

```python
ssml = """
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
  <voice name="en-US-Harper:MAI-Voice-2.1">Welcome to A Bit of AI!</voice>
</speak>
"""
result = post_ssml(ssml)
display(Audio(data=result.audio, autoplay=False))
```

The complete SSML in each cell shows the model, voice, style, language, and
speaker changes. The helper validates the demo's supported SSML subset and sends
the **exact supplied bytes**, without reconstructing or silently changing them.
It handles URL, headers, timeout, HTTP status, and WAV validation.
This demo accepts `speak`, `voice`, `mstts:express-as`, and
`mstts:ttsembedding` with the documented English/Dutch voice choices and one
model per request. Unsupported markup is rejected, not silently removed.

1. Edit the text or SSML in the notebook. Escape dynamic text with `escape(...)`.
2. Run the chosen synthesis cell. Each `post_ssml` call makes one paid request.
3. After each success, read the character count, estimated cost, full request
   time, and audio duration. Press Play in the resulting player.

There is no preview button, generation widget, or run switch. **Run All sends
requests** and reaches the optional personal-voice workflow, which requires
local recordings, approval, and asynchronous processing. Run those steps
individually: upload cells send recordings to Azure, while status cells let you
check progress without repeating uploads. Skip Demo 6 if you only need prebuilt
voices. Cloning approval, permission, and retention confirmations remain required.
Requests run sequentially with explicit timeouts and no automatic retries. An error stops the cell with a
sanitized message; earlier requests may still be billed. Earlier audio players
remain available where the cell already displayed them.

| Section | Requests per cell run |
| --- | --- |
| 1. Welcome | 1 |
| 2. Three deliveries | 3 |
| 3. English/Dutch Grant and Dutch Sander | 3 |
| 4. Standard/Flash comparison | 2 |
| 5. Dialogue | 1 |
| 6. Personal welcome | 1, requires your consented profile; management requests are separate |

Running the five core demos once makes **10** synthesis requests.
Editing SSML and replaying existing audio do not make synthesis requests.

Prices used are published USD reference rates: $22 per million characters for
2.1 and $15 for Flash. Estimates use spoken text length only; billable SSML,
language-specific character weighting, profile storage, and other Azure charges
can differ. These estimates are not invoice predictions.

All output is mono 24 kHz, 16-bit PCM WAV. The displayed timer measures the
**full HTTP request and audio download**, not model inference or time to first
speech. A completed-file player is not a streaming demo. Reversing model order
and manually repeating requests can help expose warm-up and network effects,
but this is not a formal benchmark.

The demo caps requests at 6,000 spoken characters, 50 turns, 64 KB of SSML, and
30 MiB of response data. These are conservative demo limits, not a complete
service quota specification. Audio near the ten-minute synchronous service
limit is rejected as potentially truncated.

## The podcast scripts

`scripts.json` holds the complete supplied dialogue and solo welcomes. The
notebook uses excerpts in the early demos and the full dialogue in Demo 5.
The original solo scripts remain in the file but are not generated as a separate section.
Speaker labels are parsed separately and are never spoken.

In the prebuilt version, Henk is Grant and Amy is Harper. They are synthetic
stand-ins. Demo 3 defines the short English Henk welcome and its prepared Dutch
translation directly as strings, not as a model-generated translation or a
modification of the full original Dutch script.

Edit short excerpts directly in code. Demo 5 builds visible `<voice>` elements
from `scripts.json` and prints the prebuilt dialogue's SSML. Changes to notebook
variables do not overwrite that file; persist deliberate full-script changes
there when appropriate. Never print personal SSML, which contains a profile ID.

## Demo 6: clone your own consented voice

### Before recording

Obtain [Limited Access approval](https://aka.ms/customneural) for the resource
and intended use. The current eligibility policy is restricted to customers
working with Microsoft account teams; approval is not guaranteed.

Obtain each speaker's explicit permission, provide the required disclosures,
and record that same person reading the
[official locale-specific consent statement](https://github.com/Azure-Samples/Cognitive-Speech-TTS/blob/master/CustomVoice/script/verbal-statement-all-locales.txt).
Use the exact talent/company names from the recording in the configuration cell.
A podcast script, an ordinary reference recording, or a Boolean confirmation
is not a substitute for recorded consent.

Set `consent_locale` to the language of the consent recording: the notebook uses
`en-US` for English consent. This does not change the Dutch reference audio or
the `nl-NL` synthesis language.

Record a separate clean reference clip, **5-60 seconds** of natural speech.
This notebook accepts mono 16-bit PCM WAV at 16, 24, 44.1, or 48 kHz and caps
uploads at 30 MB. Consent clips may be 1-120 seconds in this demo. The service
supports additional formats; restricting the demo to PCM WAV allows local
duration/integrity checks before upload.

If necessary, convert an authorized recording without overwriting the input:

```bash
ffmpeg -n -i samples/reference-original.mp3 -ac 1 -ar 24000 -c:a pcm_s16le samples/henk-reference.wav
```

Upload recordings through the Codespaces Explorer or put them in `samples/`
locally. Keep them out of source control.

### Follow the code steps

The walkthrough uses one speaker: your own voice. No forms or microphone capture
are involved. API helpers use the configured custom-subdomain endpoint and the
`2026-01-01` personal-voice REST API.

1. **Choose prerecorded files.** Set `reference_audio` and `consent_audio` to your
   existing WAV files. Validate them locally and listen to the reference; nothing
   is uploaded in this step.
2. **Configure the voice.** Set project, consent, and voice resource IDs, the real
   talent/company names, and consent locale. Confirm actual Microsoft approval,
   speaker permission, and storage/retention acknowledgment. This creates a client
   locally and clears the in-memory profile.
3. **Create the project.** Call `personal.create_project(project_id)`.
4. **Upload recorded consent.** Call `personal.submit_consent(...)` once.
5. **Check consent.** Rerun the status cell until `Succeeded`; do not re-upload.
6. **Upload the reference.** Call `personal.submit_voice(...)` once. It checks
   successful consent in the same project before uploading the reference.
7. **Load the ready profile.** Call `personal.load_profile(voice_id)`. If processing
   is unfinished, wait and rerun this cell. It verifies the linked consent too.
8. **Synthesize your welcome.** Edit the short Dutch text and visible
   `mstts:ttsembedding` SSML, post it, and play the result. This is one synthesis
   request, with characters, estimated cost, timing, and duration after completion.

To reuse an existing voice, set its `voice_id` in Step 2 and jump to Step 7.
No local recordings, project creation, or repeat uploads are needed for reuse.
The Voice ID is not the service-generated `speakerProfileId`, which stays in
memory and is not printed.

After changing the resource, identity, or approval details, rerun Step 2 and
reload the profile. A failed profile load clears the notebook's previous profile
value. No cloned output is replaced silently with a prebuilt voice.

### Costs, privacy, and cleanup

Personal voice has **daily per-profile storage charges** in addition to
synthesis. Partial days can still count as a day. Consent, reference data, and
profiles are stored under the service's documented policies; personal voice
does not support Bring Your Own Storage. Microsoft documents security-related
retention exceptions, so this is not a zero-retention workflow.

The final markdown cell includes a cleanup snippet. Copy it into a code cell and
pass the exact **Voice ID** as `confirmation` to `personal.delete_voice(...)`.
It is deliberately not an executable notebook step, so Run All cannot delete a
profile. This does not delete the separate consent/project resources. Remove those through Azure
as appropriate; do not promise that deletion overrides retention exceptions.
Removing a notebook or codespace does not remove Azure profiles.

Audio players embed reference or generated audio in cell outputs. Before sharing, clear
**all cell outputs and saved widget state**. Do not commit keys, recordings,
profile IDs, or personal audio. The notebook ships with no outputs, execution
counts, attachments, or widget state.

See the [privacy documentation](https://learn.microsoft.com/en-us/azure/foundry/responsible-ai/speech-service/text-to-speech/data-privacy-security)
and [Limited Access obligations](https://learn.microsoft.com/en-us/azure/foundry/responsible-ai/speech-service/text-to-speech/limited-access).

## Before sharing or committing

No audio recordings are supplied with the demo. **Never commit consent recordings
or reference audio**, including copies outside `samples/`. The repository ignores
`samples/`, WAV files regardless of extension case, `.env`, and generated outputs.
Do not bypass these rules with `git add --force`.

Clear all notebook outputs, execution counts, attachments, and saved widget state:
audio players embed the bytes inside the notebook, so ignoring the WAV alone is
not enough. Restore example resource IDs, blank talent/company fields, and reset
approval confirmations before publishing. Keep any executed personal copy outside
the files being shared.

Review the staged file list and diff, not just the working tree. Only the
documented upload cells send recordings to Azure when deliberately executed with
valid approval; setup, packaging, and offline tests never upload consent or audio.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Recording missing or invalid | Check Step 1's paths, PCM WAV format, channel count, duration, and size |
| Imports or scripts not found | Kernel environment and working directory must match this demo |
| Missing key/region | Set the `VOICE_` settings, not the transcription settings; rerun configuration and, if needed, personal-voice setup |
| HTTP 401 | Key and region must belong to the same voice resource |
| HTTP 403 | Resource/model access, permissions, or cloning approval |
| HTTP 400 / voice unavailable | Exact model suffix, region, and voice/style combination |
| Neutral output despite a style | Check the voice-specific catalog and listen; service success does not prove style application |
| HTTP 429 | Regional voice capacity or quota; wait and explicitly retry |
| Timeout | The request may still have been processed/billed; no automatic retry occurs |
| Profile still processing | Check/load again later, without creating/uploading again |
| Consent or profile failure | Review the resource details in Azure; the notebook deliberately does not print raw service bodies |
| `SpeechClient` has no `post_ssml` | Restart the kernel to reload the updated helper, then rerun imports and configuration |

## Offline checks

From the repository root:

```bash
.venv/bin/python -m unittest discover -s MAI-Voice-2.1/tests -v
```

The suite checks request shapes, escaping, limits, error handling, approval
gates, asynchronous states, profile reuse/deletion, exact SSML transport, and
execution of every notebook cell against mocked Azure responses, plus
network-free initialization. These checks do not
establish live Azure access, acceptance of every preview feature, or audio
quality. Authorize a short live request separately before presenting.
