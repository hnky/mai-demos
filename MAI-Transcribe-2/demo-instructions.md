# MAI-Transcribe-2: demo instructions

[Model introduction](README.md) | [Extended information](information.md) | [Notebook](demo.ipynb)

Turn an **A Bit of AI** episode recording into a readable, navigable transcript.
The notebook follows Henk and Amy's conversation through an editor's workflow
using your own Azure resource and permitted recordings. For realtime captions,
use the separate [Streaming demo](../MAI-Transcribe-2-Streaming/README.md);
no streaming setup is needed for this notebook.

## GitHub Codespaces

The repository's shared dev container installs Python 3.11, this demo's
dependencies, Azure CLI, FFmpeg, and the VS Code Python/Jupyter extensions.
No local Python installation or separate JupyterLab server is needed.

1. In GitHub **Settings > Codespaces > Secrets**, add `SPEECH_ENDPOINT` and
   `SPEECH_KEY` as **Codespaces development environment secrets**, granting this
   repository access. These are not GitHub Actions secrets. Use the resource's
   HTTPS root endpoint, not a project URL.
2. Open the repository on the branch containing the dev-container configuration,
   choose **Code > Codespaces > Create codespace**, and wait for setup to finish.
3. Upload your permitted audio through the Explorer into
   `MAI-Transcribe-2/samples/`. Name the main recording `a-bit-of-ai-en.wav`, or set
   `AUDIO_PATH` in the notebook to its relative path. Name an optional Dutch
   welcome `a-bit-of-ai-nl.wav`.
4. Open `MAI-Transcribe-2/demo.ipynb`, choose **Select Kernel**, and select
   **Python (MAI demos)**. If it is not listed, select the Python environment at
   `/home/vscode/.venvs/mai-demos/bin/python`.
5. Run setup and the demo cells you want to present. Review the request counts and costs in
   [Run and present](#run-and-present) before executing transcription cells.

Codespaces supplies the secrets as environment variables, which the notebook
already reads. No `.env` file is required for this route. After changing
Codespaces secrets, stop and restart the codespace so its processes receive
the new values; rerunning a cell alone does not refresh process environment
variables.

For **Entra ID** instead of a resource key, provide only `SPEECH_ENDPOINT`,
leave `SPEECH_KEY` unset, and run `az login --use-device-code` in the integrated
terminal. The signed-in identity needs the required resource permissions
described under [Azure access and authentication](#azure-access-and-authentication).
The Azure resource must already exist; the dev container does not create it.

The container uses `/home/vscode/.venvs/mai-demos`, separate from any local
checkout's `.venv`. New terminals use that environment, and notebooks run with
their own file's directory as the working directory so `.env` and `samples/`
resolve correctly. Setup only installs tools and dependencies; it makes no
transcription requests.

Samples, credentials, and generated outputs are Git-ignored and are not included
in a fresh codespace. Upload recordings again when
needed, and save any local-only files you want to keep before deleting a
codespace. Codespaces compute costs are separate from Azure transcription.

## Local setup

Use Python 3.9 or later (3.11+ recommended). From the repository root, create a
shared virtual environment and install this demo's dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r MAI-Transcribe-2/requirements.txt
cd MAI-Transcribe-2
mkdir -p samples
cp -n .env.example .env
```

Edit `.env` beside the notebook with your resource's `SPEECH_ENDPOINT` and
`SPEECH_KEY` (or leave the key blank for Entra ID). Then start Jupyter:

```bash
python -m jupyterlab --ContentsManager.allow_hidden=True
```

Open `demo.ipynb` and select the virtual environment's Python kernel.
VS Code's Jupyter extension also works with that environment.
In JupyterLab, enable **View > Show Hidden Files** to see and edit `.env` directly
in the file browser. Keep Jupyter local and authenticated; `.env` contains secrets.

On macOS, Apple's bundled Python may emit `NotOpenSSLWarning` because it uses
LibreSSL. For live Azure requests, prefer a current Python 3.11+ distribution
linked against OpenSSL and create the virtual environment with that interpreter.
Do not disable TLS certificate verification to work around SSL issues.

## Azure access and authentication

You need an Azure Speech/Foundry resource with access to MAI-Transcribe-2 in a
[supported region](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/regions?tabs=llmspeech).
The notebook uses the `2025-10-15` fast-transcription API and explicitly selects
`MAI-Transcribe-2`. This surface is not available on the Speech F0 tier.

Authentication is automatic; there is no authentication-mode setting:

- **Resource key:** set `SPEECH_KEY` in `.env` or through your environment's secret
  store. The helper uses the configured key without prompting.
- **Entra ID:** leave the key unset, run `az login` locally or
  `az login --use-device-code` in Codespaces, and give the signed-in identity the
  required resource permissions, such as **Cognitive Services Speech User**.
  The helper then uses Azure CLI credentials. It does not silently switch to
  another method if the selected credential fails.

Never paste a real key into a notebook cell, commit it, or display request headers.
The configuration cell reads `.env` fresh from the notebook's working directory
each time it runs, without modifying the process environment. Existing environment
variables take precedence, and parent directories are not searched. A missing
`.env` is fine when you supply settings through the environment. After editing
`.env`, save and rerun the configuration cell. **No kernel or server restart is
needed.** Then rerun the transcription cells you want to use.

The real `.env` is ignored by Git; only the placeholder `.env.example` is tracked.
Hosted notebook users can use their platform's secret store instead and upload
recordings to the kernel's filesystem; no local microphone is required.

## Prepare the recordings

Place a **30-90 second mono, 16-bit PCM WAV** recording at
`samples/a-bit-of-ai-en.wav`, or change `AUDIO_PATH` in the configuration cell.
You can also set `AUDIO_FILE` in `.env` or the environment.
MP3 and FLAC work with the transcription helper, but the word-excerpt player
requires PCM WAV. Compressed-audio playback depends on the notebook frontend.
The notebook enforces a conservative **20 MiB demo limit**, not the service's
maximum file size.

Use a short permitted excerpt of the podcast, or ask two consenting speakers to
read this **fictional rehearsal script**. These are scripted roles, not a claim
that the real hosts said these lines. Listen for the handoffs, fillers, correction,
and names: the same moments carry the story through each notebook section.

> **Henk:** Hi everyone, and welcome to A Bit of AI! I'm Henk Boelman.
>
> **Amy:** And I'm Amy. Today we're looking at Microsoft Foundry and
> MAI-Transcribe. What happens after we finish recording an episode?
>
> **Henk:** Well, um, we need a transcript so listeners can find the parts they
> care about. Remember that conversation about AgentCon?
>
> **Amy:** Yes! That episode goes out on Thursday. Sorry, I mean Friday.
> Let's make sure the transcript keeps that correction.
>
> **Henk:** Exactly. And, uh, the episode page should spell A Bit of AI and
> AgentCon correctly. We can check the names against the recording.
>
> **Amy:** So first we listen, then check who spoke, find the right moment, and
> prepare a readable transcript. No complicated jargon.
>
> **Henk:** And we'll include a Dutch welcome too. Grab a coffee, and let's get
> the episode ready.

For the optional Dutch welcome, record your own Dutch speech at
`samples/a-bit-of-ai-nl.wav`. This short script comes from the podcast opening:

> Hallo allemaal, en welkom bij een nieuwe aflevering van A Bit of AI!
> Ik ben Henk Boelman, en ik ben blij dat je er weer bij bent.

Set the Dutch path directly in its demonstration cell, or skip that cell.
There is no automatic file discovery: missing files raise an error before upload.
Existing filenames such as `samples/meeting-en.wav` and `samples/meeting-nl.wav`
still work when explicitly selected. `AUDIO_FILE` in `.env` continues to set the
main recording, so there is no need to rename an already configured recording.

Audio is transmitted to Azure. Use non-sensitive recordings you have permission
to process. **Do not use a voice-cloning consent recording as the demo input.**
No recordings are bundled; WAV files, `samples/`, and `outputs/` are Git-ignored.
If you use audio generated by the Voice demo, disclose that it is synthetic
and do not present it as an accuracy test on natural conversation.

### Extract or convert audio with FFmpeg

FFmpeg is preinstalled in the dev container. From `MAI-Transcribe-2/`, convert a
video or audio recording to the mono, 16-bit, 16 kHz WAV format used by the
notebook's word-excerpt player:

```bash
ffmpeg -n -i samples/input.mp4 -vn -ac 1 -ar 16000 -c:a pcm_s16le samples/a-bit-of-ai-en.wav
```

Replace `samples/input.mp4` with your uploaded file's path. The `-n` option
refuses to overwrite an existing output. For a Dutch recording, use
`samples/a-bit-of-ai-nl.wav` as the output path. Conversion happens inside the
container; transcription sends the resulting recording to Azure.

## Run and present

Frame the walkthrough as getting an A Bit of AI recording ready for its editor,
not as six unrelated recognition tests:

| Notebook scene | What to show |
| --- | --- |
| Listen to the recorded episode | Identify a handoff, a hesitation, and a name to revisit |
| Make the first transcript | One explicit MAI-Transcribe-2 request, with verbatim text and metadata |
| Follow the hosts | Compare anonymous speaker labels with what you actually hear; do not assume speaker 0 is Henk |
| Revisit an editorial question | Use a word timestamp to replay a name or correction without another API call |
| Prepare the episode-page draft | Compare clean and verbatim on the same audio; clean is not a summary |
| Check the show's vocabulary | Compare the verbatim baseline against keyword-hinted verbatim output |
| Include the Dutch welcome | Let the service detect the language and keep the transcript in Dutch |
| Hand off the source material | Optionally export the baseline TXT, JSON response, and request metadata |

Use hints that are actually spoken in your clip. Defaults match the rehearsal
script: A Bit of AI, Henk Boelman, Amy, Microsoft Foundry, MAI-Transcribe, and
AgentCon. A correct baseline may not change when hints are added.

Run setup, then execute the cells you want to demonstrate. There are no run
switches. Baseline verbatim, clean, and keyword-hinted verbatim each make **one
paid request**: three for the full main-recording walkthrough. For one request,
run the baseline and skip the clean and keyword comparison cells.

The optional Dutch cell makes **one extra request** when run; set its path in
that cell. Skip it if you do not have a Dutch clip. **Run All attempts all four
requests and runs the export cell if it completes.** A missing Dutch clip stops
execution rather than being silently skipped. No requests retry automatically;
a timeout does not imply the service did not process or bill it.

The word slider replays local excerpts without additional API requests. Run the
optional export cell to save the baseline transcript, raw response, and sanitized
request/timing metadata in a unique output folder; skip it to avoid writing files.
Exports do not include audio or credentials, but do contain speech-derived data.
They export **the baseline only**; the clean, hinted, and Dutch results remain
separate notebook variables. Generating summaries, show notes, chapter titles, or
caption files would be a separate step, not an output this notebook invents.

The notebook keeps no fabricated fallback transcripts. It needs your actual
Azure access and recordings for a live presentation. Rehearse with the same
resource, samples, machine, and network you will use on stage.

Setup only loads the connection details and main audio path. Model/API constants
stay in the helper, authentication is selected from your credentials, and the
keyword list and Dutch path sit directly beside the examples that use them.

**Before sharing or committing an executed notebook:** restart the kernel,
clear all outputs, save, and inspect the diff. Audio playback embeds recordings
in notebook outputs; tables and widget outputs also retain transcript content.

The [MAI-Voice notebook](../MAI-Voice-2.1/demo.ipynb) is the companion production
story: write a podcast opening and give it a voice. This notebook starts from a
recording instead. Neither demo needs the other's Azure resource or execution.

## Offline checks

Run from `MAI-Transcribe-2/`, with the virtual environment active. In the dev
container, new integrated terminals already use the prepared environment:

```bash
python -m unittest discover -s tests -v
```

The checks validate notebook structure and code, test the API helper with mocked
responses, and execute a copy of the whole notebook using generated silent WAV
fixtures and explicitly mocked Azure calls. They require no Azure credentials,
make no billable requests, and do not overwrite the notebook with test outputs.
They do not establish actual model access, accuracy, or production latency.
