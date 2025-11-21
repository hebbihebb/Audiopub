# Audiopub

![Audiopub Screenshot](screenshot.png)

**Turn your EPUBs into high-fidelity audiobooks locally.**

Audiopub is a slick, desktop-based power tool that converts ebooks into chapterized .m4b audiobooks using **on-device TTS engines**. It runs entirely on your machine—no cloud APIs, no per-character fees.

### Supported TTS Engines:
- **Supertonic** (default): Supertone's high-quality diffusion-based TTS
- **NeuTTS Air**: Instant voice cloning from 3-15 second audio samples

## Features

*   **⚡ Local & Private:** Powered by ONNX Runtime. Zero data leaves your rig.
*   **💎 Deep Dark UI:** A beautiful, responsive glass-morphism interface built with NiceGUI.
*   **🧠 Smart Context:** Splits text intelligently by sentence to maintain narrative flow.
*   **⏯️ Resumable:** Crash? Quit? No problem. Resume exactly where you left off.
*   **📦 Auto-Muxing:** Outputs ready-to-listen `.m4b` files with proper metadata and chapters.

## Quick Start

1.  **Install:**
    ```bash
    git clone https://github.com/yourusername/audiopub.git
    cd audiopub
    git lfs pull  # Essential: Downloads the AI models
    pip install -r requirements.txt
    ```

2.  **Run:**
    ```bash
    export PYTHONPATH=$PYTHONPATH:.
    python audiopub/main.py
    ```

3.  **Generate:**
    *   Open the UI (it launches automatically).
    *   Select your EPUB and Voice.
    *   Hit **Generate**.

## Requirements

*   **Python 3.9+**
*   **FFmpeg** (Must be in your PATH)
*   **Git LFS** (For model weights)

## Voice Styles

### For Supertonic (default):
Drop your custom `.json` voice style configs into `audiopub/assets/`. The app will auto-detect them.

### For NeuTTS Air:
1. **Install additional dependencies:**
   ```bash
   pip install -r requirements-neutts.txt
   sudo apt-get install espeak  # or: brew install espeak on macOS
   ```

2. **Set the TTS engine:**
   ```bash
   export AUDIOPUB_TTS_ENGINE=neutts-air
   ```

3. **Add voice samples:**
   Place `.wav` audio files (3-15 seconds) with matching `.txt` transcript files in:
   - `audiopub/assets/reference_audio/`

   Example:
   ```
   reference_audio/
   ├── narrator1.wav    # 5 seconds of clean speech
   └── narrator1.txt    # Transcript of the audio
   ```

   See `audiopub/assets/reference_audio/README.md` for detailed setup instructions.

## Switching TTS Engines

Change engines by setting the environment variable:
```bash
# Use NeuTTS Air (with voice cloning)
export AUDIOPUB_TTS_ENGINE=neutts-air

# Use Supertonic (default)
export AUDIOPUB_TTS_ENGINE=supertonic
```

---
*Built for audiophiles who code.*
