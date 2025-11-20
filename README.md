# Audiopub

A local desktop application to convert EPUB ebooks into .m4b audiobooks using Supertone's Supertonic TTS.

## Features

- **Local Processing:** Uses ONNX Runtime for high-quality, local text-to-speech.
- **NiceGUI Interface:** Modern, responsive web-based UI (runs as a desktop app).
- **Smart Chunking:** Splits text by sentence boundaries to preserve flow.
- **Resume Capability:** Skips already generated chunks/chapters if restarted.
- **Muxing:** Creates chapterized .m4b files with metadata.

## Prerequisites

1. **Python 3.9+**
2. **FFmpeg**: Must be installed and available in your system PATH.
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.
   - Linux: `sudo apt install ffmpeg`
   - macOS: `brew install ffmpeg`

## Installation

1. Clone the repository.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```


## Model Setup (Git LFS)

This application requires the Supertonic ONNX models. These are large files stored via Git LFS.

1. Ensure you have Git LFS installed: `git lfs install`
2. If you cloned the repo without LFS, pull the actual model files:
   ```bash
   git lfs pull
   ```
   *Note: The application checks for these files on startup. If they are small (<10MB), it will warn you.*

3. Place your Voice Style JSON files in `audiopub/assets/` (or subdirectories).

## Usage

1. Run the application:
   ```bash
   python audiopub/main.py
   ```
2. The UI will open in your default browser (or native window if configured).
3. Select your EPUB file.
4. Select an Output Directory.
5. Select a Voice from the dropdown.
6. Click **Start Conversion**.

## Configuration

You can adjust advanced settings in `audiopub/config.py`:
- `FFMPEG_BINARY`: Path to ffmpeg executable if not in PATH.
- `CROSSFADE_MS`: Duration of crossfade between sentences.
- `SAMPLE_RATE`: Output sample rate.

## Troubleshooting

- **"File is too small" error:** Run `git lfs pull` to download the actual model weights.
- **"ffmpeg not found":** Install FFmpeg or update `audiopub/config.py` with the full path to the binary.
