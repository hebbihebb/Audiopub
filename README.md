# Audiopub

![Audiopub Screenshot](screenshot.png)

**Turn your EPUBs into high-fidelity audiobooks locally.**

Audiopub is a slick, desktop-based power tool that converts ebooks into chapterized .m4b audiobooks using **on-device TTS engines**. It runs entirely on your machine—no cloud APIs, no per-character fees.

### Supported TTS Engines:
- **Supertonic** (default): Supertone's high-quality diffusion-based TTS
- **NeuTTS Air**: Instant voice cloning from 3-15 second audio samples

## Features

*   **⚡ Local & Private:** Powered by ONNX Runtime. Zero data leaves your rig.
*   **🚀 GPU Acceleration:** Optional CUDA support for 10x faster synthesis on NVIDIA GPUs.
*   **💎 Deep Dark UI:** A beautiful, responsive glass-morphism interface built with NiceGUI.
*   **🧠 Smart Context:** Splits text intelligently by sentence to maintain narrative flow.
*   **⏯️ Resumable:** Crash? Quit? No problem. Resume exactly where you left off.
*   **📦 Auto-Muxing:** Outputs ready-to-listen `.m4b` files with proper metadata and chapters.
*   **🎚️ Configurable Quality:** Adjust inference steps (2-128) for speed/quality tradeoff.

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

## GPU Acceleration

### Enabling GPU Support

Audiopub supports GPU acceleration via ONNX Runtime's CUDA provider, offering up to **10x faster synthesis** on NVIDIA GPUs.

**In the WebUI:**
1. Toggle the **"GPU ACCELERATION"** switch
2. Adjust **"INFERENCE STEPS"** slider (2-128)
   - Lower steps = faster (2-5 for real-time)
   - Higher steps = better quality (16+ recommended)

**Requirements:**
- NVIDIA GPU with CUDA support
- CUDA 11.8+ or 12.x
- Install GPU-enabled ONNX Runtime:
  ```bash
  pip install onnxruntime-gpu
  ```

### Benchmarking

Test GPU performance on your hardware:

```bash
# CPU benchmark
python benchmark_gpu.py

# GPU benchmark
python benchmark_gpu.py --gpu --steps 2,5,16,32,64,128

# Save results
python benchmark_gpu.py --gpu --output results.json
```

**Expected Performance (RTX4090 vs M4 Pro CPU):**
- GPU: ~12,000 chars/sec (2-step) → ~600 chars/sec (16-step)
- CPU: ~1,200 chars/sec (2-step) → ~400 chars/sec (16-step)

See [GPU_BENCHMARKING.md](GPU_BENCHMARKING.md) for detailed performance tuning, PyTorch fallback options, and troubleshooting.

---
*Built for audiophiles who code.*
