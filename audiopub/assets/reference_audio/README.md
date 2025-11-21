# NeuTTS Air Reference Audio

This directory is for NeuTTS Air reference audio files used for voice cloning.

## Setup Instructions

To use NeuTTS Air for voice cloning, you need to:

1. **Install NeuTTS Air dependencies:**
   ```bash
   pip install -r requirements-neutts.txt
   ```

2. **Install espeak (system dependency):**
   - **Ubuntu/Debian:** `sudo apt-get install espeak`
   - **macOS:** `brew install espeak`
   - **Windows:** Download from http://espeak.sourceforge.net/

3. **Set the TTS engine in your environment:**
   ```bash
   export AUDIOPUB_TTS_ENGINE=neutts-air
   ```

## Adding Voice Samples

For each voice you want to use, you need TWO files:

### 1. Audio File (`.wav`)
- **Duration:** 3-15 seconds
- **Format:** Mono channel
- **Sample Rate:** 16-44 kHz
- **Quality:** Clean audio with minimal background noise
- **Content:** Natural, continuous speech (like a monologue)

### 2. Transcript File (`.txt`)
- Same filename as the audio file but with `.txt` extension
- Contains the exact transcript of what is spoken in the audio file
- Plain text format

## Example

If you have a voice sample file named `john_doe.wav`, you also need `john_doe.txt`:

```
reference_audio/
├── john_doe.wav      # 5 seconds of clean speech
└── john_doe.txt      # "Hello, my name is John and I love reading books."
```

## File Placement

You can place your reference audio files in any of these locations:
- `audiopub/assets/reference_audio/` (recommended)
- `audiopub/assets/voices/`
- `audiopub/assets/` (root)

The application will scan all these directories recursively.

## Voice Quality Tips

For best results:
- Use professional quality recordings
- Avoid background noise, echo, or reverb
- Ensure clear pronunciation
- Use natural speaking pace
- Match the tone/style you want for the audiobook

## Switching Between Engines

To switch back to the default Supertonic engine:
```bash
export AUDIOPUB_TTS_ENGINE=supertonic
```

Or simply unset the variable to use the default.
