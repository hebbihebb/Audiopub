# NeuTTS Air Integration Summary

## Overview

Successfully integrated **NeuTTS Air** as an alternative TTS engine for Audiopub, providing instant voice cloning capabilities alongside the existing Supertonic engine.

## What is NeuTTS Air?

NeuTTS Air is an open-source, on-device text-to-speech model by Neuphonic featuring:
- **Instant voice cloning** using just 3-15 seconds of reference audio
- **Mobile-optimized** with real-time performance on mid-range devices
- **0.5B parameter model** based on Qwen with NeuCodec audio codec
- **24kHz output** sample rate
- **English language** support
- **Apache 2.0 license**

Repository: https://github.com/neuphonic/neutts-air

## Architecture Changes

### 1. Created Base TTS Engine Interface (`tts_base.py`)
- Abstract base class `TTSEngine` defining common interface
- Methods: `load()`, `set_voice()`, `warm_up()`, `synthesize()`, `get_sample_rate()`
- Properties: `engine_name`, `voice_file_extension`
- Enables easy addition of new TTS engines in the future

### 2. Refactored Supertonic Implementation (`tts.py`)
- Updated `TTSWrapper` to inherit from `TTSEngine`
- Implemented all abstract methods
- Maintains backward compatibility
- No changes to existing Supertonic functionality

### 3. Implemented NeuTTS Air Engine (`tts_neutts.py`)
- New `NeuTTSAirEngine` class implementing `TTSEngine` interface
- Voice cloning from WAV audio files + TXT transcripts
- Lazy loading with helpful error messages if dependencies missing
- GPU/CPU support via configuration
- Note: Speed parameter not supported (model limitation)

### 4. Created TTS Engine Factory (`tts_factory.py`)
- Factory function `create_tts_engine()` for engine selection
- `get_available_engines()` utility function
- Centralized engine instantiation logic

### 5. Updated Configuration (`config.py`)
- Added `TTS_ENGINE` config via environment variable
- Default: `supertonic`
- Options: `supertonic`, `neutts-air`
- Set via: `export AUDIOPUB_TTS_ENGINE=neutts-air`

### 6. Updated Worker (`worker.py`)
- Modified to use factory pattern instead of direct instantiation
- Engine selection based on config
- Displays selected engine in logs

### 7. Enhanced Voice Discovery (`main.py`)
- Updated `get_voices()` to be engine-aware
- For Supertonic: Scans for `.json` style files
- For NeuTTS Air: Scans for `.wav` files with accompanying `.txt` files
- Searches in multiple directories: `assets/`, `assets/voices/`, `assets/reference_audio/`

## File Structure

```
audiopub/
├── core/
│   ├── tts_base.py          # NEW: Abstract base class
│   ├── tts.py               # MODIFIED: Supertonic implementation
│   ├── tts_neutts.py        # NEW: NeuTTS Air implementation
│   ├── tts_factory.py       # NEW: Engine factory
│   └── worker.py            # MODIFIED: Uses factory pattern
├── assets/
│   └── reference_audio/     # NEW: Directory for NeuTTS Air voice samples
│       └── README.md        # NEW: Setup instructions
├── config.py                # MODIFIED: Added TTS_ENGINE setting
├── main.py                  # MODIFIED: Engine-aware voice discovery
├── requirements.txt         # MODIFIED: Added NeuTTS Air note
├── requirements-neutts.txt  # NEW: Optional NeuTTS Air dependencies
└── README.md                # MODIFIED: Documentation updates
```

## Usage

### Using Supertonic (Default)
```bash
# Default engine, no changes needed
python audiopub/main.py
```

### Using NeuTTS Air
```bash
# 1. Install dependencies
pip install -r requirements-neutts.txt
sudo apt-get install espeak  # or: brew install espeak

# 2. Set engine
export AUDIOPUB_TTS_ENGINE=neutts-air

# 3. Add voice samples (WAV + TXT pairs) to:
#    audiopub/assets/reference_audio/

# 4. Run
python audiopub/main.py
```

## Voice File Requirements

### Supertonic
- **Format:** `.json` style embedding files
- **Location:** `audiopub/assets/` or subdirectories
- **Size:** ~420 KB per voice

### NeuTTS Air
- **Audio Format:** `.wav` file
  - Duration: 3-15 seconds
  - Channels: Mono
  - Sample Rate: 16-44 kHz
  - Quality: Clean, minimal noise
- **Transcript:** Matching `.txt` file with exact transcript
- **Location:** `audiopub/assets/reference_audio/` (or `voices/` or root)
- **Example:**
  ```
  narrator1.wav  # 5 seconds: "Hello, my name is John..."
  narrator1.txt  # "Hello, my name is John..."
  ```

## Benefits

1. **Voice Cloning:** Create audiobooks with ANY voice using just a short sample
2. **Flexibility:** Choose between quality preset voices (Supertonic) or custom cloning (NeuTTS Air)
3. **Extensible:** Easy to add more TTS engines in the future
4. **No Breaking Changes:** Existing Supertonic workflows unchanged
5. **On-Device:** Both engines run locally, maintaining privacy

## Limitations

### NeuTTS Air
- **English only** (current model limitation)
- **No speed control** (model doesn't support native speed adjustment)
- **Requires espeak** (system dependency for phoneme conversion)
- **Larger dependencies** (PyTorch, transformers vs. ONNX only)
- **Quality depends on reference audio** (garbage in, garbage out)

### Supertonic
- **Fixed voices** (requires pre-trained style embeddings)
- **No voice cloning** (cannot create custom voices from samples)

## Future Enhancements

Potential improvements:
1. Add more TTS engines (Coqui TTS, StyleTTS2, etc.)
2. Implement time-stretching for NeuTTS Air speed control
3. Add voice preview in UI before generation
4. Support multi-language models
5. Add voice quality validation/preprocessing
6. Create unified voice management UI

## Testing Recommendations

1. **Test Supertonic (ensure no regression):**
   ```bash
   export AUDIOPUB_TTS_ENGINE=supertonic
   python audiopub/main.py
   # Generate test audiobook with existing voice
   ```

2. **Test NeuTTS Air:**
   ```bash
   # Install dependencies
   pip install -r requirements-neutts.txt
   sudo apt-get install espeak

   # Create test voice
   mkdir -p audiopub/assets/reference_audio
   # Add test.wav + test.txt

   # Run
   export AUDIOPUB_TTS_ENGINE=neutts-air
   python audiopub/main.py
   # Generate test audiobook
   ```

3. **Test Engine Switching:**
   - Generate with Supertonic
   - Switch to NeuTTS Air
   - Generate with NeuTTS Air
   - Switch back to Supertonic
   - Verify both work independently

## Conclusion

The NeuTTS Air integration provides Audiopub users with powerful voice cloning capabilities while maintaining the simplicity and quality of the existing Supertonic engine. The modular architecture makes it easy to add more TTS engines in the future, positioning Audiopub as a flexible, extensible audiobook generation platform.

---
**Integration Date:** 2025-11-21
**Status:** ✅ Complete and ready for testing
