"""
Base TTS Engine Interface

Defines the abstract interface that all TTS engines must implement.
"""

from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np


class TTSEngine(ABC):
    """Abstract base class for TTS engines"""

    def __init__(self, assets_dir: str, use_gpu: bool = False):
        """
        Initialize TTS engine.

        Args:
            assets_dir: Directory containing TTS assets (models, voices, etc.)
            use_gpu: Whether to use GPU acceleration if available
        """
        self.assets_dir = assets_dir
        self.use_gpu = use_gpu
        self.current_voice_path = None

    @abstractmethod
    def load(self):
        """Load the TTS model and necessary resources"""
        pass

    @abstractmethod
    def set_voice(self, voice_path: str):
        """
        Set the voice to use for synthesis.

        Args:
            voice_path: Path to voice file (format depends on engine)
        """
        pass

    @abstractmethod
    def warm_up(self):
        """Run a short inference to warm up the model"""
        pass

    @abstractmethod
    def synthesize(self, text: str, speed: float = 1.0, steps: int = 5) -> Tuple[np.ndarray, int]:
        """
        Synthesize text to audio.

        Args:
            text: Text to synthesize
            speed: Speech speed multiplier (1.0 = normal, >1.0 = faster, <1.0 = slower)
            steps: Quality steps (meaning varies by engine)

        Returns:
            Tuple of (audio_data as float32 numpy array, sample_rate)
        """
        pass

    @abstractmethod
    def get_sample_rate(self) -> int:
        """Get the output sample rate of this engine"""
        pass

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Return the name of this TTS engine"""
        pass

    @property
    @abstractmethod
    def voice_file_extension(self) -> str:
        """Return the expected voice file extension (e.g., '.json', '.wav')"""
        pass
