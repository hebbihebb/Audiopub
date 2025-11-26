# GPU Acceleration Setup for Audiopub Supertonic TTS

## Status: ✅ FULLY FUNCTIONAL

GPU acceleration is working on your system with **5-10x speedup** on RTX 2070.

## Quick Start

### Option 1: Bash Script (Recommended for terminal use)

```bash
# Enable GPU acceleration for current shell
source setup_gpu.sh

# Now run with GPU
python benchmark_gpu.py --gpu
python audiopub/main.py  # WebUI with GPU enabled
```

### Option 2: Python Module (Recommended for code)

```python
# At the start of your script
from setup_gpu_env import setup_gpu
setup_gpu()

# Now all TTS operations use GPU
from audiopub.core.tts_factory import create_tts_engine
from audiopub import config

tts = create_tts_engine(config.TTS_ENGINE, config.ASSETS_DIR, use_gpu=True)
```

### Option 3: Permanent Setup (For .bashrc/.zshrc)

Add this line to your shell configuration file:

```bash
# Add to ~/.bashrc or ~/.zshrc
source /mnt/Games/Audiopub/setup_gpu.sh
```

Then reload your shell:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

## Performance Benchmarks

Tested on: RTX 2070 with CUDA 12.8

### Inference Speed (chars/sec)

```
Steps  | 2-step (Fastest) | 16-step (Default) | 32-step (Quality)
-------|------------------|-------------------|------------------
GPU    | 1915-3614        | 534-1091          | 285-606
CPU    | 182-409          | 89-163            | 56-98
Speedup| 8.8-10.5x        | 6.0-6.7x          | 5.1-6.2x
```

### Real-time Factor (RTF)

Lower RTF = faster (RTF < 1 means faster than real-time)

```
Steps  | GPU RTF | CPU RTF | Improvement
-------|---------|---------|------------
2      | 0.004   | 0.036   | 9x faster
16     | 0.013   | 0.090   | 7x faster
32     | 0.024   | 0.150   | 6x faster
```

## Configuration

### In WebUI

When GPU acceleration is enabled via setup script or Python module:
- Toggle "GPU ACCELERATION" switch in the UI
- Adjust "INFERENCE STEPS" slider for quality/speed tradeoff
  - 2-5: Real-time / Streaming (fastest)
  - 16: Default (balanced)
  - 32+: High quality

### In Code

```python
from setup_gpu_env import setup_gpu
setup_gpu()

from audiopub.core.tts_factory import create_tts_engine
from audiopub import config

# GPU acceleration
tts = create_tts_engine(config.TTS_ENGINE, config.ASSETS_DIR, use_gpu=True)
tts.load()
tts.set_voice("path/to/voice.json")

# Synthesize with custom steps
wav, sr = tts.synthesize("Hello world", steps=2)  # Fast
wav, sr = tts.synthesize("Hello world", steps=16)  # Default quality
wav, sr = tts.synthesize("Hello world", steps=32)  # High quality
```

## Troubleshooting

### GPU Not Detected

1. Verify CUDA is available:
```bash
source setup_gpu.sh
python -c "import onnxruntime as ort; print(ort.get_available_providers())"
```

Should show: `['TensorrtExecutionProvider', 'CUDAExecutionProvider', 'CPUExecutionProvider']`

2. Check GPU status:
```bash
nvidia-smi
```

Should show your GPU with available VRAM.

### Performance Not Improving

1. Verify models are using CUDA:
```bash
source setup_gpu.sh
python benchmark_gpu.py --gpu --steps 16 --output test.json
```

Check the output log - should show "Mode: GPU (CUDA)"

2. Monitor GPU during synthesis:
```bash
# In another terminal
watch -n 0.5 nvidia-smi
```

You should see GPU memory usage and compute utilization increase.

### Out of Memory

RTX 2070 has 8GB VRAM. If you encounter OOM errors:
1. Reduce inference steps (use 2-5 instead of 16+)
2. Process shorter text chunks
3. Close other GPU applications

## Architecture

The setup works by:
1. **LD_LIBRARY_PATH**: Points ONNX Runtime to CUDA libraries in conda environment
2. **ONNX Runtime**: Automatically uses CUDAExecutionProvider when available
3. **Fallback**: Gracefully falls back to CPU if GPU unavailable

Models affected:
- ✓ Diffusion Predictor (main computation)
- ✓ Text Encoder (GPU accelerated)
- ✓ Vector Estimator (GPU accelerated)
- ✓ Vocoder (GPU accelerated)

## Files

- `setup_gpu.sh` - Bash script to enable GPU in current shell
- `setup_gpu_env.py` - Python module for GPU setup
- `GPU_SETUP.md` - This documentation
- `GPU_BENCHMARKING.md` - Detailed benchmark guide

## Next Steps

1. Use `setup_gpu.sh` or add setup to shell config
2. Run benchmarks to confirm GPU working
3. Adjust inference steps based on your speed/quality needs
4. (Optional) Consider PyTorch implementation for even higher performance

## Resources

- ONNX Runtime CUDA: https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html
- Supertone Official: https://github.com/supertone-inc/supertonic
- GPU_BENCHMARKING.md: See GPU performance expectations
