# MAI-Transcribe-2

**MAI-Transcribe-2** is Microsoft's speech-to-text model for turning recordings
into transcripts across 60 languages. It supports speaker diarization,
word-level timestamps, clean and verbatim output, and keyword hints for
specialized vocabulary.

[Read the extended information](information.md) for model capabilities, API
details, language support, regions, pricing, limitations, and source references.

## Demo

[Open the feature demo notebook](demo.ipynb) |
[Setup and demo instructions](demo-instructions.md)

| Feature | What the notebook demonstrates |
| --- | --- |
| Transcription | Turn a recording into text and measure request time |
| Speaker diarization | Inspect anonymous speaker labels in a multi-person recording |
| Word timestamps | Navigate the recording with an interactive word-playback slider |
| Clean versus verbatim | Compare readable output with fillers and corrections preserved |
| Keyword hints | Compare recognition with and without domain-specific terms |
| Multilingual recognition | Transcribe Dutch with automatic language detection |

The notebook also includes local audio playback and opt-in TXT/JSON exports.
This is **file transcription**, not the separate streaming model. Azure access
and your own permitted audio recordings are required.

## Learn more

- [MAI-Transcribe-2 documentation and API examples](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-transcribe)
- [Fast transcription API guide](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/fast-transcription-create)
- [Supported Azure Speech regions](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/regions?tabs=llmspeech)
- [MAI-Transcribe-2 model card](https://microsoft.ai/pdf/MAI-Transcribe-2-Model-Card.pdf)
- [Microsoft Foundry Speech-to-text playground](https://aka.ms/foundry-speech-to-text)

[All model demos](../README.md)
