"""
TTS Engine Factory

Creates TTS engine instances based on configuration.
"""

from typing import Optional
from .tts_base import TTSEngine
from .tts import TTSWrapper
from .tts_neutts import NeuTTSAirEngine


def create_tts_engine(
    engine_name: str,
    assets_dir: str,
    use_gpu: bool = False
) -> TTSEngine:
    """
    Factory function to create TTS engine instances.

    Args:
        engine_name: Name of the TTS engine ("supertonic" or "neutts-air")
        assets_dir: Directory containing TTS assets
        use_gpu: Whether to use GPU acceleration if available

    Returns:
        TTSEngine instance

    Raises:
        ValueError: If engine_name is not recognized
    """
    engine_name = engine_name.lower()

    if engine_name == "supertonic":
        return TTSWrapper(assets_dir, use_gpu)
    elif engine_name == "neutts-air" or engine_name == "neutts_air":
        return NeuTTSAirEngine(assets_dir, use_gpu)
    else:
        raise ValueError(
            f"Unknown TTS engine: {engine_name}. "
            f"Available engines: 'supertonic', 'neutts-air'"
        )


def get_available_engines() -> list[str]:
    """
    Get list of available TTS engines.

    Returns:
        List of engine names
    """
    return ["supertonic", "neutts-air"]
