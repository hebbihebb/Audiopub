"""
Config settings for Audiopub
"""
import os

# Default Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Create directories if they don't exist
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# TTS Settings
TTS_ENGINE = os.getenv("AUDIOPUB_TTS_ENGINE", "supertonic")  # Options: "supertonic", "neutts-air"
DEFAULT_SPEED = 1.05 # Recommended default (Range: 0.75 - 1.1)
DEFAULT_STEPS = 16 # Higher for better quality (Range: 2 - 16)

# Text Processing
MIN_CHUNK_SIZE = 1    # Minimum characters per chunk
MAX_CHUNK_SIZE = 300  # Recommended max chunk size for natural pauses

# Audio Settings
CROSSFADE_MS = 50
SILENCE_PADDING_MS = 300 # Recommended silence between chunks
CHAPTER_SILENCE_MS = 5000 # Silence between chapters (ACX recommends 1-5 seconds); default near 5s for clearer separation
SAMPLE_RATE = 24000 # Supertonic default

# FFMPEG Path (Can be overridden)
FFMPEG_BINARY = "ffmpeg" # Assumes it's in PATH
