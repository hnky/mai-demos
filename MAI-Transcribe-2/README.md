# MAI-Transcribe-2

**MAI-Transcribe-2** is Microsoft's speech-to-text model for turning recordings
into transcripts across 60 languages. It supports speaker diarization,
word-level timestamps, clean and verbatim output, and keyword hints for
specialized vocabulary.

[Read the extended information](information.md) for model capabilities, API
details, language support, regions, pricing, limitations, and source references.

## Demo: turn A Bit of AI into a readable episode

Henk and Amy have recorded an episode of **A Bit of AI**. Follow the editor's
workflow: turn that conversation into a transcript, revisit important moments,
and prepare readable text for the episode page.

[Open the podcast demo notebook](demo.ipynb) |
[Setup and demo instructions](demo-instructions.md)

| Story step | Model feature |
| --- | --- |
| Make the first record of the episode | Verbatim transcription and measured request time |
| Follow the handoffs between hosts | Anonymous speaker diarization, not identity recognition |
| Find a name or correction in the recording | Word timestamps and local excerpt playback |
| Prepare a readable episode-page draft | Clean versus verbatim on the same audio |
| Check the show name and AI terminology | Keyword hints without forced replacements |
| Include Henk's Dutch welcome | Automatic language detection, not translation |
| Hand source material to the editor | Optional baseline TXT/JSON exports |

Use a permitted podcast excerpt or record the fictional rehearsal script in the
instructions. No audio is bundled. This is **file transcription**, not the separate
streaming model, automatic show-note generation, or publication of an episode page.
Review the output before sharing.

The [MAI-Voice demo](../MAI-Voice-2.1/README.md) gives A Bit of AI a voice.
This demo turns the recorded conversation back into usable text. Both work
independently; no voice cloning or consent-recording upload is needed here.

Setup only needs connection details and the main recording path. Run the cells
you want: comparisons make requests directly, and the optional export cell saves
files when executed. Keywords and the Dutch clip's path are edited in their own
examples, not in a separate settings block.

## Learn more

- [MAI-Transcribe-2 documentation and API examples](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-transcribe)
- [Fast transcription API guide](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/fast-transcription-create)
- [Supported Azure Speech regions](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/regions?tabs=llmspeech)
- [MAI-Transcribe-2 model card](https://microsoft.ai/pdf/MAI-Transcribe-2-Model-Card.pdf)
- [Microsoft Foundry Speech-to-text playground](https://aka.ms/foundry-speech-to-text)

[All model demos](../README.md)
