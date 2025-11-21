"""
NeuTTS Air TTS Engine Implementation

Integrates the neutts-air on-device TTS engine with instant voice cloning.
Repository: https://github.com/neuphonic/neutts-air
"""

import os
from typing import Tuple
import numpy as np

from .tts_base import TTSEngine


class NeuTTSAirEngine(TTSEngine):
    """NeuTTS Air TTS Engine with voice cloning support"""

    def __init__(self, assets_dir: str, use_gpu: bool = False):
        super().__init__(assets_dir, use_gpu)
        self.model = None
        self.ref_codes = None
        self.ref_text = None
        self.sample_rate = 24000  # NeuTTS Air default

    def load(self):
        """Load the NeuTTS Air model"""
        try:
            from neuttsair.neutts import NeuTTSAir
        except ImportError:
            raise ImportError(
                "neutts-air is not installed. Please install it using:\n"
                "pip install git+https://github.com/neuphonic/neutts-air.git\n"
                "Also ensure espeak is installed on your system."
            )

        print("Loading NeuTTS Air model...")

        # Determine device
        backbone_device = "cuda" if self.use_gpu else "cpu"
        codec_device = "cuda" if self.use_gpu else "cpu"

        # Initialize the model
        self.model = NeuTTSAir(
            backbone_repo="neuphonic/neutts-air",
            backbone_device=backbone_device,
            codec_repo="neuphonic/neucodec",
            codec_device=codec_device
        )

        print("NeuTTS Air model loaded.")

    def set_voice(self, voice_path: str):
        """
        Set the voice using a reference audio file.

        Args:
            voice_path: Path to reference audio file (.wav format recommended)
                       Should be 3-15 seconds, mono, 16-44kHz, clean audio
        """
        if self.current_voice_path == voice_path:
            return

        if not os.path.exists(voice_path):
            raise FileNotFoundError(f"Reference audio not found: {voice_path}")

        # Check for accompanying text file
        text_path = voice_path.rsplit('.', 1)[0] + '.txt'
        if not os.path.exists(text_path):
            raise FileNotFoundError(
                f"Reference text file not found: {text_path}\n"
                f"NeuTTS Air requires a transcript of the reference audio. "
                f"Please create a .txt file with the same name as your audio file."
            )

        print(f"Loading voice from: {voice_path}")

        # Load reference text
        with open(text_path, 'r', encoding='utf-8') as f:
            self.ref_text = f.read().strip()

        # Encode reference audio
        self.ref_codes = self.model.encode_reference(voice_path)
        self.current_voice_path = voice_path

        print(f"Voice loaded successfully.")

    def warm_up(self):
        """Run a short inference to warm up the model"""
        if not self.model or self.ref_codes is None:
            raise RuntimeError("Model or voice not loaded.")

        print("Warming up NeuTTS Air model...")
        # Run a short inference
        _ = self.model.infer("Hello.", self.ref_codes, self.ref_text)
        print("Warm up complete.")

    def synthesize(self, text: str, speed: float = 1.0, steps: int = 5) -> Tuple[np.ndarray, int]:
        """
        Synthesize text to audio using the loaded voice.

        Args:
            text: Text to synthesize
            speed: Speech speed multiplier (note: NeuTTS Air may not support this directly)
            steps: Quality steps (not used by NeuTTS Air, kept for interface compatibility)

        Returns:
            Tuple of (audio_data as float32 numpy array, sample_rate)
        """
        if not self.model or self.ref_codes is None:
            raise RuntimeError("Model or voice not loaded.")

        # Generate audio
        wav = self.model.infer(text, self.ref_codes, self.ref_text)

        # NeuTTS Air doesn't have a direct speed parameter, so we'd need to implement
        # time-stretching if speed != 1.0. For now, we'll warn if speed is not 1.0
        if speed != 1.0:
            print(f"Warning: NeuTTS Air doesn't support speed adjustment natively. "
                  f"Speed parameter {speed} will be ignored.")

        # Ensure output is float32
        if wav.dtype != np.float32:
            wav = wav.astype(np.float32)

        return wav, self.sample_rate

    def get_sample_rate(self) -> int:
        """Get the output sample rate of this engine"""
        return self.sample_rate

    @property
    def engine_name(self) -> str:
        """Return the name of this TTS engine"""
        return "neutts-air"

    @property
    def voice_file_extension(self) -> str:
        """Return the expected voice file extension"""
        return ".wav"
