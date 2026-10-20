# MAI demos

A collection of Microsoft AI model demos. Each demo introduces a model, links to
extended information, demonstrates its features in a notebook, and provides
resources to learn more.

## Demos

| Model | Extended information | Demo |
| --- | --- | --- |
| [MAI-Transcribe-2](MAI-Transcribe-2/README.md) | [Model and API information](MAI-Transcribe-2/information.md) | [Notebook](MAI-Transcribe-2/demo.ipynb) / [Instructions](MAI-Transcribe-2/demo-instructions.md) |

## Run in GitHub Codespaces

Open **Code > Codespaces > Create codespace** on the branch containing this
configuration. The shared [dev container](.devcontainer/devcontainer.json)
provides Python 3.11, the Python and Jupyter extensions, Azure CLI, FFmpeg, and
the MAI-Transcribe-2 notebook dependencies.

After setup finishes, open `MAI-Transcribe-2/demo.ipynb` and select
**Python (MAI demos)** as its kernel. Follow the
[Codespaces instructions](MAI-Transcribe-2/demo-instructions.md#github-codespaces)
to supply Azure credentials and upload your recordings. The notebook runs
directly in the editor; no separate JupyterLab server or public port is needed.

The same configuration works locally with Docker and VS Code's Dev Containers
extension using **Dev Containers: Reopen in Container**. Codespaces compute and
Azure transcription are billed separately; creating the environment does not
provision an Azure resource or run transcription.

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
  .env               # Local credentials; Git-ignored
  samples/           # Local input audio/video/data; Git-ignored
  outputs/           # Generated local results; Git-ignored
  work/              # Internal research, brainstorms, draft scripts; Git-ignored
```

Each demo is self-contained. Run its notebook with that demo directory as the
working directory so `.env`, `samples/`, and `outputs/` resolve consistently.
Follow the demo's `demo-instructions.md` for dependencies and execution instructions.

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
Write `information.md` as a reader-facing article about the model, not as a
research report or presentation plan. Keep the underlying research in `work/`.

## Local-only working documents

Use a `work/` folder inside each demo for internal research, brainstorming,
unfinished video scripts, storyboards, and rehearsal notes. A root `work/` folder
may hold cross-demo notes. All `work/` folders are excluded from Git. Keep
reader-facing articles and public demo instructions outside those folders.

Credentials, input samples, generated output, virtual environments, and notebook
checkpoints are also ignored. Git ignores do not hide content embedded inside a
notebook: clear saved audio, transcripts, credentials, and private outputs before
sharing or committing it.
