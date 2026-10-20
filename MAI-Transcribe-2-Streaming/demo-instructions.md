# MAI-Transcribe-2-Streaming: demo instructions

[Model introduction](README.md) | [Extended information](information.md) | [Notebook](demo.ipynb)

**A Bit of AI is live:** the audience reads Henk's welcome while he speaks.
This standalone notebook uses the Realtime API and the browser microphone.
It needs no prerecorded files or execution of another demo.

**Status:** experimental. The browser-microphone/Azure path still requires
end-to-end verification on the machine, browser, resource, and network used
for the presentation. This separation does not establish that the live path
works. Do not rely on it for a live event without rehearsing successfully.

## Azure access and deployment

The [Realtime guide](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-transcribe-2-streaming-realtime)
requires a **Foundry resource and a deployed MAI-Transcribe-2-Streaming model**.
Use a supported region: Sweden Central, Central US, East US 2, or Southeast
Asia, subject to subscription availability. A North Europe resource used for
file transcription is not a streaming resource.

In Foundry, open the project, choose **Build > Models > Deploy a base model**,
and deploy MAI-Transcribe-2-Streaming. Record the deployment name and the
resource's `services.ai.azure.com` root endpoint, not a project URL.

Configure these values in this folder's `.env` or your environment's secret store:

```dotenv
AZURE_MAI_ENDPOINT=https://your-streaming-resource.services.ai.azure.com
AZURE_MAI_DEPLOYMENT_NAME=your-streaming-deployment
AZURE_MAI_API_KEY=
```

Set the key from the streaming resource. Alternatively, leave it blank and
authenticate with Azure CLI after `az login` locally or
`az login --use-device-code` in Codespaces. The identity needs inference access
to the resource. The helper uses only the selected method; it does not fall
back to another credential or model on failure.

The helper never reads `SPEECH_KEY`, `SPEECH_ENDPOINT`, or `VOICE_SPEECH_*`.
Use this folder's `.env`; it does not search the file demo or parent directories.
Each Start reads configuration fresh, with environment variables taking
precedence. Do not paste real keys into cells, JavaScript, or WebSocket URLs.
Private configuration is not copied from another demo automatically.

## Local setup

Use Python 3.9 or later; Python 3.11+ linked against OpenSSL is recommended.
From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r MAI-Transcribe-2-Streaming/requirements.txt
cd MAI-Transcribe-2-Streaming
cp -n .env.example .env
```

Edit `.env` with your own streaming connection details, then start JupyterLab:

```bash
python -m jupyterlab --ContentsManager.allow_hidden=True
```

Open `demo.ipynb` in a full browser tab and select this virtual environment's
kernel. Keep Jupyter authenticated and local. If dependencies were installed
while Jupyter was already running, restart the server/kernel and refresh the
browser to load the widget extension.

On macOS, Apple's Python may emit a LibreSSL warning. Prefer a current
OpenSSL-linked Python distribution for Azure traffic; never disable TLS
verification as a workaround.

## GitHub Codespaces

The shared dev container installs this folder's requirements, Python 3.11,
Azure CLI, and Jupyter. Rebuild an existing container or install the new
requirements into `/home/vscode/.venvs/mai-demos` if it predates this demo.

1. Add `AZURE_MAI_ENDPOINT`, `AZURE_MAI_DEPLOYMENT_NAME`, and, when using a key,
   `AZURE_MAI_API_KEY` in **GitHub Settings > Codespaces > Secrets**, granting
   this repository access. These are development environment secrets, not
   GitHub Actions secrets.
2. Create or restart the codespace so its processes receive the variables.
3. Open `MAI-Transcribe-2-Streaming/demo.ipynb` and select **Python (MAI demos)**.
   The environment is `/home/vscode/.venvs/mai-demos/bin/python`.
4. Use the browser route below if the editor blocks microphone access.

No `.env` is needed when Codespaces secrets supply the configuration. Changes
to those secrets require a codespace restart, not merely rerunning a cell.
The container does not provision a resource, deploy a model, or start paid
requests. Codespaces compute costs are separate from Azure usage.

### Browser microphone permissions

Capture happens on your computer, not on the remote kernel host. Use a current
Chrome or Edge browser on **HTTPS or localhost**, with microphone permission,
AudioWorklet support, and a 16 kHz AudioContext. No remote audio device or
`sounddevice` installation is required.

Embedded VS Code notebooks, app previews, OS permissions, and browser
Permissions Policy can block capture. A full JupyterLab browser tab avoids
some embedding restrictions, but is not a guarantee of working capture.
From the Codespaces terminal, using the prepared environment:

```bash
cd MAI-Transcribe-2-Streaming
python -m jupyterlab --ip=0.0.0.0 --port=8888 --no-browser
```

Forward port 8888 through the **Ports** view, keep visibility **Private**, and
choose **Open in Browser**. Authenticate using Jupyter's token from the
terminal; keep it private. Open `demo.ipynb` and select the prepared kernel.
Do not make the port public or disable authentication.

## Run and present

Run the notebook's import and display cells. That only renders the controls:
**no microphone capture or Azure request starts from Run All**.

1. Click **Start captions**, allow the microphone, and wait for
   **LIVE - microphone on** before speaking.
2. Say: "Welcome to A Bit of AI. I'm Henk, and today we're trying live captions
   for the podcast. You can read this welcome while I'm still speaking."
3. Pause, then say: "Hallo allemaal, en welkom bij A Bit of AI. Vandaag
   proberen we live ondertiteling voor de podcast." Language detection is
   automatic; this is transcription, not translation.
4. Point out that italic provisional text can change. Confirmed text
   accumulates separately.
5. Click **Stop**. The microphone stops, buffered audio is drained, and a
   commit requests finalization. Wait for **Captions finalized**.

After a successful Stop, `captions.transcript` contains the final text in
kernel memory. After an error it may be incomplete. There is no automatic
export, summary generation, diarization, word timing, or caption-file creation.

The demo caps capture at five minutes. Switching away from the browser tab
stops capture; closing or rerunning the widget cancels the session. Heartbeats
detect lost browser/kernel connections. Buffer overflow and timeouts are
reported rather than silently dropping audio or inventing a transcript.
There is no automatic reconnection. A new Start is a new paid session.

## Cost and privacy

Start sends permitted microphone speech to Azure and incurs streaming usage
charges, including applicable processing of silence. Consult current deployment
pricing rather than treating the file model's price as the streaming price.
An error or timeout does not prove that a session was not billed.

Keys stay in Python, and authentication uses WebSocket headers. The demo writes
no microphone audio file and does not persist captions as widget traits.
Live text is still visible in the browser and confirmed text stays in kernel
memory. Displaying or exporting that text yourself can retain it.

Use non-sensitive speech everyone involved permits you to process.
**Do not upload or use a private voice-cloning consent recording.**
No recordings or credentials are bundled. `.env`, `samples/`, WAV files, and
`outputs/` are Git-ignored. Restart the kernel and clear outputs before sharing
a notebook; never choose a shared/public notebook as your secret store.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Import or widget-rendering error | This folder's requirements, selected kernel, Jupyter server restart, browser refresh |
| Missing configuration | `.env` beside this notebook, or `AZURE_MAI_*` in the kernel environment |
| Permission denied | Browser/site and OS microphone permissions; try a full JupyterLab tab |
| Browser audio cannot start | HTTPS/localhost, current browser, AudioWorklet and 16 kHz AudioContext support |
| Azure rejects the session | Deployed streaming model, exact deployment name, supported resource region, key/Entra access, quota |
| Connection cannot keep up | Browser/kernel load and network; the demo stops instead of silently losing audio |
| Stop does not finalize | Treat the transcript as incomplete; inspect service health before starting another paid session |

For a reproducible failure, note the displayed error, browser, notebook host,
and whether it occurred before permission, before LIVE, or after Stop.
Never include keys, token URLs, private recordings, or raw service payloads.

## Offline checks

With the environment active, from this folder:

```bash
python -m unittest discover -s tests -v
```

Tests mock the Azure WebSocket, verify the protocol/lifecycle, and execute the
notebook with external connections forbidden. They do not open a microphone,
make paid requests, or establish live model availability.

For browser checks, serve this folder locally with
`python -m http.server 8000 --bind 127.0.0.1`, then open
`http://127.0.0.1:8000/tests/frontend.html`. Stop the server afterward and never
expose this directory publicly. The page uses synthetic Web Audio and mocked
microphone/kernel messages; it does not request microphone permission or
contact Azure.
