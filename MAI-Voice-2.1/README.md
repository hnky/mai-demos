# MAI-Voice-2.1

**MAI-Voice-2.1** turns text into natural, expressive speech across 23 languages.
**MAI-Voice-2.1-Flash** offers a lower-latency alternative. Both provide prebuilt
voices, voice-specific speaking styles, and gated personal voice cloning through
Azure Speech. Both models are currently **public preview**, without an SLA.

[Explore the models, voices, APIs, pricing, and limitations](information.md).

## Demo: give A Bit of AI a voice

Create the opening of **A Bit of AI**, a podcast hosted by Henk and Amy:

1. Give Amy's welcome a voice.
2. Direct the delivery: neutral, excited, or whispering.
3. Welcome listeners in English and Dutch.
4. Compare MAI-Voice-2.1 with Flash using the same podcast excerpt.
5. Produce the Henk-Amy opening conversation.
6. Optionally clone your own consented voice, starting with prerecorded reference and consent
   files, then synthesize a short welcome through step-by-step code.

**[Open the notebook](demo.ipynb)** |
**[Setup and running instructions](demo-instructions.md)**

[Watch the notebook walkthrough on YouTube](https://www.youtube.com/watch?v=IJdToJGbUdo)
(7 minutes 14 seconds, in English with Henk's consented AI-generated narration).

Run it locally or in the repository's shared GitHub Codespaces environment.
The notebook shows the SSML, `post_ssml(...)`, and audio playback explicitly.
The helper hides the URL, headers, and HTTP plumbing, then reports character
count, estimated cost, request time, and audio duration after each successful call.
Configure your key and run individual synthesis cells to make paid requests.
Each rerun makes new requests; replay uses the existing audio. The first five demos
require no recordings or cloning approval. Demo 6 additionally requires a
supported resource, Microsoft approval, speaker permission, recorded consent,
and reference audio.

Prebuilt voices are clearly labeled synthetic stand-ins, not the hosts' actual
voices. Live resource availability and audio quality must be checked on your
subscription; the notebook does not provision resources.

## Recordings stay private

No reference audio, consent recordings, or generated audio are included.
Bring your own recordings for Demo 6 and keep them in the Git-ignored `samples/`
folder. WAV files are also ignored throughout the repository.
**Never commit or share consent recordings.** The published notebook contains no
saved outputs, embedded audio, credentials, or personal profile IDs.

## Learn more

- [Official MAI voices guide](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/mai-voices)
- [MAI-Voice-2.1 model page](https://microsoft.ai/models/mai-voice-2-1/)
- [Azure Speech regions](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/regions?tabs=tts)
- [Speech pricing](https://azure.microsoft.com/en-us/pricing/details/speech/)
- [Personal voice and access requirements](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/personal-voice-overview)
