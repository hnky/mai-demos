# MAI-Transcribe-2: demo instructions

[Model introduction](README.md) | [Extended information](information.md) | [Notebook](demo.ipynb)

Set up and run the file-transcription feature demo with your own Azure resource
and permitted recordings. These steps do not cover the separate streaming model.

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
   `MAI-Transcribe-2/samples/`. Name the main recording `meeting-en.wav`, or set
   `AUDIO_PATH` in the notebook to its relative path. Name an optional Dutch
   recording `meeting-nl.wav`.
4. Open `MAI-Transcribe-2/demo.ipynb`, choose **Select Kernel**, and select
   **Python (MAI demos)**. If it is not listed, select the Python environment at
   `/home/vscode/.venvs/mai-demos/bin/python`.
5. Run the notebook from the top. Review the request counts and costs in
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

Samples, credentials, private working documents, and generated outputs are
Git-ignored and are not included in a fresh codespace. Upload them again when
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

Choose one authentication method:

- **Entra ID:** install the Azure CLI if needed (the dev container includes it),
  run `az login` locally or `az login --use-device-code` in Codespaces, and ensure the
  signed-in identity has the required resource permissions, such as
  **Cognitive Services Speech User**. Leave `AUTH_MODE = "entra"` in the notebook.
- **Resource key:** set `SPEECH_KEY` in `.env` or supply it through your
  environment's secret-management mechanism. The notebook selects key
  authentication automatically. Alternatively, set `AUTH_MODE` to `"key"` in
  the configuration cell to enter the key through a hidden prompt.

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
`samples/meeting-en.wav`, or change `AUDIO_PATH` in the configuration cell.
You can also set `AUDIO_FILE` in `.env` or the environment.
MP3 and FLAC work with the transcription helper, but the word-excerpt player
requires PCM WAV. Compressed-audio playback depends on the notebook frontend.
The notebook enforces a conservative **20 MiB demo limit**, not the service's
maximum file size.

Record two consenting speakers reading an original fictional conversation such as:

> Speaker A: Okay, um, let's review the Contoso demo. We will use Microsoft Foundry
> and MAI-Transcribe to turn this recording into a transcript.
>
> Speaker B: Sounds good. The rehearsal is on Thursday. Sorry, I mean Friday,
> at ten thirty. We should check the speaker labels and the timestamps.
>
> Speaker A: Right. And, uh, the customer name is Contoso, not Fabrikam.
> Let's keep those names in our keyword list.
>
> Speaker B: I'll prepare the audio today. The transcript should keep this
> correction in verbatim mode, but clean mode can remove the filler words.
>
> Speaker A: Great. We also need a Dutch recording. After the rehearsal,
> we'll check any mistakes together before sharing the results.

For the optional Dutch section, record your own Dutch speech and place it at
`samples/meeting-nl.wav`. The configuration cell selects this file automatically
when it exists; set `DUTCH_AUDIO_PATH = None` to skip it. A starting script:

> Goedemorgen, vandaag bespreken we de demonstratie voor Contoso. We gebruiken
> Microsoft Foundry om deze opname om te zetten naar tekst. De repetitie is op
> donderdag, sorry, op vrijdag om half elf. Controleer de namen en de tijdstempels.
> Daarna vergelijken we de oorspronkelijke tekst met de opgeschoonde versie.

Audio is transmitted to Azure. Use fictional, non-sensitive content you have
permission to process. `samples/` and `outputs/` are ignored by Git.

### Extract or convert audio with FFmpeg

FFmpeg is preinstalled in the dev container. From `MAI-Transcribe-2/`, convert a
video or audio recording to the mono, 16-bit, 16 kHz WAV format used by the
notebook's word-excerpt player:

```bash
ffmpeg -n -i samples/input.mp4 -vn -ac 1 -ar 16000 -c:a pcm_s16le samples/meeting-en.wav
```

Replace `samples/input.mp4` with your uploaded file's path. The `-n` option
refuses to overwrite an existing output. For a Dutch recording, use
`samples/meeting-nl.wav` as the output path. Conversion happens inside the
container; transcription sends the resulting recording to Azure.

## Run and present

Run the notebook from top to bottom. The default performs **three paid requests**
for the main recording: baseline verbatim, clean, and verbatim with keyword hints.
Set `RUN_COMPARISONS = False` for a one-request walkthrough. The Dutch section
makes one extra request only when its path is configured. No requests retry
automatically; a timeout does not imply the service did not process or bill it.

The word slider replays local excerpts without additional API requests.
`EXPORT_RESULTS` defaults to `False`; enable it to save the baseline transcript,
raw response, and sanitized request/timing metadata in a unique output folder.
Exports do not include audio or credentials, but do contain speech-derived data.

The notebook keeps no fabricated fallback transcripts. It needs your actual
Azure access and recordings for a live presentation. Rehearse with the same
resource, samples, machine, and network you will use on stage.

**Before sharing or committing an executed notebook:** restart the kernel,
clear all outputs, save, and inspect the diff. Audio playback embeds recordings
in notebook outputs; tables and widget outputs also retain transcript content.

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

## Working documents

Keep internal research, brainstorming, draft scripts, storyboards, and rehearsal
notes in `work/` inside this demo. That directory is Git-ignored and local only.
Reader-facing model information, notebook documentation, and other public demo
materials belong outside it.
