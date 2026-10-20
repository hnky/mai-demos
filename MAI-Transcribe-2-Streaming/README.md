# MAI-Transcribe-2-Streaming

**MAI-Transcribe-2-Streaming** is Microsoft's low-latency speech-to-text model
for receiving captions while someone speaks. It supports 60 languages and
returns changing provisional text alongside finalized text.

The model is in **public preview**, without an SLA, and is not recommended for
production workloads.

[Read the extended information](information.md) for languages, regions,
deployment requirements, the Realtime protocol, latency, costs, and limitations.

## Demo: A Bit of AI goes live

Henk opens a live episode of **A Bit of AI**. The audience should be able to
read his welcome before he finishes speaking, then see the transcript settle
when he stops.

[Open the realtime demo notebook](demo.ipynb) |
[Setup and demo instructions](demo-instructions.md)

**Experimental:** the browser-microphone/Azure flow still needs end-to-end
verification in the presentation environment. Rendering a widget or passing
offline checks does not establish that live transcription works there.

| Story step | What to demonstrate |
| --- | --- |
| Prepare the live desk | A streaming deployment and browser microphone permissions |
| Open the episode | Start explicitly; wait for the microphone-on indicator |
| Watch the captions evolve | Provisional text changes while confirmed text accumulates |
| Welcome Dutch listeners | Automatic language detection, not translation |
| Finish the welcome | Stop capture, drain buffered audio, and await the final transcript |

This folder is independent of the
[file-transcription demo](../MAI-Transcribe-2/README.md) and the
[voice-generation demo](../MAI-Voice-2.1/README.md). It does not import either
notebook, need their sample recordings, or reuse their resource keys.

Running the notebook cells only prepares the controls. **Start captions**
requests the browser microphone and opens a separately billed Azure session.
Credentials stay in the Python kernel. No microphone audio file is saved by
the demo.

## Learn more

- [Streaming model overview](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-transcribe-2-streaming)
- [Realtime API guide](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-transcribe-2-streaming-realtime)
- [Speech SDK integration](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-transcribe-2-streaming-speech-sdk)
- [Streaming model card](https://microsoft.ai/pdf/MAI-Transcribe-2-Streaming-Model-Card-Memo.pdf)
- [Microsoft Foundry Models pricing](https://azure.microsoft.com/pricing/details/ai-foundry-models/microsoft/)

[All model demos](../README.md)
