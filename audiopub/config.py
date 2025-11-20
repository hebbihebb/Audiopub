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
DEFAULT_SPEED = 1.0
DEFAULT_STEPS = 5 # Lower for speed, higher for quality (usually 5-10 is enough)

# Audio Settings
CROSSFADE_MS = 50
SILENCE_PADDING_MS = 150
SAMPLE_RATE = 24000 # Supertonic default

# FFMPEG Path (Can be overridden)
FFMPEG_BINARY = "ffmpeg" # Assumes it's in PATH
