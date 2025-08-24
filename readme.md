# Overview

For my wedding speeches, I needed an application to live translate speeches into multiple languages and show the output on a projector. The requirements were:
- low bandwidth consumption as the local internet was extremely slow,
- multi-language capability,
- doesn't require extra hardware like a sound card or a powerful laptop,
- low latency.

I couldn't find it, so I built it. Feel free to reuse it. 

<img width="4096" height="2450" alt="image" src="https://github.com/user-attachments/assets/d96ac3f1-8307-41d4-a5f4-76b509140781" />

# Architecture 

Slow bandwidth means that sending the audio to a transcription and translation API wasn't feasible, so the hack was to have the speaker carry his phone like a microphone and use the phone's on-device transcription model. The text is then sent to Google Gemini for translation, and to Firebase Realtime Database for low-latency multi-device synchronisation.


