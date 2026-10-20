# MAI demos

A collection of Microsoft AI model demos. Each demo introduces a model, links to
extended information, demonstrates its features in a notebook, and provides
resources to learn more.

## Demos

| Model | Extended information | Demo |
| --- | --- | --- |
| [MAI-Transcribe-2](MAI-Transcribe-2/README.md) | [Model and API information](MAI-Transcribe-2/information.md) | [Podcast transcript notebook](MAI-Transcribe-2/demo.ipynb) / [Instructions](MAI-Transcribe-2/demo-instructions.md) |
| [MAI-Transcribe-2-Streaming](MAI-Transcribe-2-Streaming/README.md) | [Realtime model and protocol](MAI-Transcribe-2-Streaming/information.md) | [Experimental live-caption notebook](MAI-Transcribe-2-Streaming/demo.ipynb) / [Instructions](MAI-Transcribe-2-Streaming/demo-instructions.md) |
| [MAI-Voice-2.1 and Flash](MAI-Voice-2.1/README.md) | [Voices, APIs, and pricing](MAI-Voice-2.1/information.md) | [Podcast notebook](MAI-Voice-2.1/demo.ipynb) / [Instructions](MAI-Voice-2.1/demo-instructions.md) |

The demos follow **A Bit of AI**: Voice turns a script into the podcast opening;
Transcribe turns a recorded conversation into an editor's transcript; Streaming
is a separate experimental live-caption demo. Each has its own notebook and setup.

## Video walkthroughs

Follow the notebooks on YouTube. Both videos are in English and use Henk's
consented AI-generated narration.

- [MAI-Transcribe-2: from recording to working transcript](https://www.youtube.com/watch?v=E2jf-X_z99k) (6 minutes)
- [MAI-Voice-2.1 and Flash: from script to generated speech](https://www.youtube.com/watch?v=IJdToJGbUdo) (7 minutes 14 seconds)

## Run in GitHub Codespaces

Open **Code > Codespaces > Create codespace** on the branch containing this
configuration. The shared [dev container](.devcontainer/devcontainer.json)
provides Python 3.11, the Python and Jupyter extensions, Azure CLI, FFmpeg, and
the dependencies for all three notebooks.

After setup finishes, open `MAI-Transcribe-2/demo.ipynb` and select
**Python (MAI demos)** as its kernel. Follow the
[Codespaces instructions](MAI-Transcribe-2/demo-instructions.md#github-codespaces)
to supply Azure credentials and upload your recordings. The notebook runs
directly in the editor; no separate JupyterLab server or public port is needed.

For realtime transcription, open `MAI-Transcribe-2-Streaming/demo.ipynb` and follow
its own [setup instructions](MAI-Transcribe-2-Streaming/demo-instructions.md).
It uses `AZURE_MAI_*` settings and a streaming deployment, not the file API.
Browser microphone access depends on the host's permissions; the guide includes
a full-tab JupyterLab route through a **private** Codespaces port. This
experimental path still needs live end-to-end verification in the target environment.

For the voice-generation demo, open `MAI-Voice-2.1/demo.ipynb` with the same kernel and
follow its [Codespaces instructions](MAI-Voice-2.1/demo-instructions.md#github-codespaces).
It uses separate `VOICE_SPEECH_*` settings so voice and transcription resources
are not accidentally mixed. Its core demos need no recordings.

The same configuration works locally with Docker and VS Code's Dev Containers
extension using **Dev Containers: Reopen in Container**. Codespaces compute and
Azure speech usage are billed separately; creating the environment does not
provision an Azure resource, run transcription, synthesize speech, or upload audio.

## Repository structure

```text
.devcontainer/       # Shared Codespaces and local dev-container environment
MAI-Transcribe-2/
  README.md          # Brief intro, information link, demo, learning resources
  information.md     # Reader-facing model article with source links
  demo.ipynb         # Model feature demo
  demo-instructions.md # Setup, credentials, recordings, and running the demo
  requirements.txt   # Demo-specific Python dependencies, when needed
  .env.example       # Safe configuration template, when needed
  tests/             # Demo-specific checks, when needed
MAI-Transcribe-2-Streaming/
  README.md
  information.md
  demo.ipynb
  demo-instructions.md
  requirements.txt
  .env.example
  live_captions.py    # Kernel-side streaming connection and widget lifecycle
  live_captions.js    # Browser microphone, PCM frames, and caption display
  tests/
MAI-Voice-2.1/
  README.md
  information.md
  demo.ipynb
  demo-instructions.md
  requirements.txt
  .env.example
  scripts.json       # Podcast dialogue and solo welcomes
  voice_demo.py      # Synthesis and gated personal-voice API helpers
  tests/
```

Each demo is self-contained. Follow its `demo-instructions.md` for dependencies,
configuration, recordings, and execution instructions.

## Adding a demo

Create a top-level folder named after the model, such as `MAI-Transcribe-2/`;
there is no enclosing `demos/` directory. Add `README.md`, `information.md`,
`demo.ipynb`, and `demo-instructions.md`, then link the model in the index.
Keep dependencies and tests alongside that demo.
If a new demo needs additional preinstalled dependencies or tools, update the
shared dev-container setup alongside its own instructions.

Structure each demo README in this order: a brief model introduction, a link to
extended information, the feature demo with a link to its instructions, then
learning resources. Keep detailed setup steps out of the introductory README.
Write `information.md` as an in-depth, reader-facing article about the model.
