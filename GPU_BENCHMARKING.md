# GPU Benchmarking Guide for Audiopub

This document explains how to benchmark and use GPU acceleration with Audiopub's Supertonic TTS engine.

## Overview

Audiopub supports GPU acceleration via ONNX Runtime's CUDA execution provider. According to official Supertone benchmarks, GPU acceleration can provide significant speedups:

- **RTX4090**: Up to 12,164 chars/sec (2-step inference)
- **M4 Pro CPU**: Up to 1,263 chars/sec (2-step inference)
- **Speedup**: ~10x faster on high-end GPU

## Current Implementation: ONNX + CUDA

### Architecture

The current implementation uses:
- **Runtime**: ONNX Runtime with CUDAExecutionProvider
- **Models**: Pre-converted ONNX models from Supertone
- **Fallback**: Automatically falls back to CPU if CUDA unavailable

### Enabling GPU in WebUI

1. Launch Audiopub: `python audiopub/main.py`
2. In the web interface, toggle **"GPU ACCELERATION"** switch
3. The system will use CUDA if available, otherwise fall back to CPU

### Checking GPU Availability

```bash
python -c "import onnxruntime as ort; print('CUDA available:', 'CUDAExecutionProvider' in ort.get_available_providers())"
```

## Running Benchmarks

### Basic Benchmark

```bash
# CPU benchmark (2, 5, 16 steps)
python benchmark_gpu.py

# GPU benchmark (2, 5, 16 steps)
python benchmark_gpu.py --gpu

# Custom step counts
python benchmark_gpu.py --gpu --steps 2,5,16,32,64,128

# Save results to JSON
python benchmark_gpu.py --gpu --steps 2,5,16 --output gpu_results.json
```

### Benchmark Output

The script outputs two tables:

**Characters per Second** (higher is better):
```
Steps      Short (59)     Mid (152)      Long (266)
2          2615           6548           12164
5          1286           3757           6242
16         596            1048           1263
```

**Real-time Factor** (lower is better):
```
Steps      Short (59)     Mid (152)      Long (266)
2          0.005          0.002          0.001
5          0.011          0.004          0.002
16         0.023          0.019          0.018
```

*RTF of 0.001 means it takes 0.001 seconds to generate 1 second of audio*

## Inference Steps Configuration

### What are Inference Steps?

Supertonic uses a diffusion-based model that iteratively refines the audio output. More steps = higher quality, but slower inference.

### Recommended Settings

| Use Case | Steps | Speed | Quality |
|----------|-------|-------|---------|
| **Real-time applications** | 2-5 | Fastest | Good |
| **Balanced (default)** | 16 | Fast | High |
| **High quality** | 32-64 | Moderate | Very High |
| **Maximum quality** | 128 | Slow | Excellent |

### Configuring Steps

#### Via WebUI
Adjust the **"INFERENCE STEPS"** slider (2-128 range)

#### Via Config File
Edit `audiopub/config.py`:
```python
DEFAULT_STEPS = 16  # Change to desired value
```

## Performance Expectations

### GPU Performance (RTX4090, based on official benchmarks)

| Steps | Short Text | Long Text | RTF |
|-------|------------|-----------|-----|
| 2 | 12,164 chars/sec | 2,615 chars/sec | 0.001-0.005 |
| 5 | 6,242 chars/sec | 1,286 chars/sec | 0.002-0.011 |
| 16 | 1,263 chars/sec | 596 chars/sec | 0.018-0.023 |

### CPU Performance (M4 Pro, based on official benchmarks)

| Steps | Short Text | Long Text | RTF |
|-------|------------|-----------|-----|
| 2 | 1,263 chars/sec | 912 chars/sec | 0.012-0.015 |
| 5 | 850 chars/sec | 596 chars/sec | 0.018-0.023 |
| 16 | 596 chars/sec | 437 chars/sec | 0.025-0.030 |

## PyTorch Fallback Option (Future Enhancement)

### Current Limitation

The official Supertone benchmarks showing RTX4090 performance were conducted using **PyTorch models**, not ONNX. While ONNX + CUDA provides GPU acceleration, there may be performance differences.

### When to Consider PyTorch Implementation

Consider implementing the PyTorch path if:

1. **ONNX GPU performance is insufficient**
   - Benchmarks show significantly worse performance than official numbers
   - CUDA provider has compatibility issues

2. **Need exact parity with official benchmarks**
   - Reproducing research results
   - Maximum possible performance required

### How to Implement PyTorch Path

If ONNX + CUDA doesn't meet performance requirements:

1. **Clone official Supertone repository**:
   ```bash
   git clone https://github.com/supertone-inc/supertonic.git
   cd supertonic
   ```

2. **Install PyTorch with CUDA**:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

3. **Create PyTorch TTS engine class**:
   - Implement `TTSEngine` interface in `audiopub/core/tts_pytorch.py`
   - Load PyTorch models from Supertone repo
   - Implement `.to('cuda')` device transfer
   - Register in `tts_factory.py`

4. **Benchmark and compare**:
   ```bash
   python benchmark_gpu.py --gpu --steps 2,5,16
   ```

### Resources

- **Official Supertone Repo**: https://github.com/supertone-inc/supertonic
- **PyTorch Examples**: See `py/` directory in Supertone repo
- **HuggingFace Models**: https://huggingface.co/Supertone/supertonic

## Troubleshooting

### GPU Not Detected

```bash
# Check NVIDIA driver
nvidia-smi

# Check CUDA installation
nvcc --version

# Install CUDA-enabled ONNX Runtime
pip install onnxruntime-gpu
```

### Out of Memory Errors

If you encounter CUDA OOM errors:
1. Reduce batch size (already set to 1 in Audiopub)
2. Reduce inference steps
3. Process shorter text chunks

### Performance Lower Than Expected

1. **Check GPU utilization**: Run `nvidia-smi` during synthesis
2. **Verify CUDA provider**: Check logs for "CUDAExecutionProvider"
3. **Compare with PyTorch**: Consider implementing PyTorch path (see above)
4. **Update drivers**: Ensure latest NVIDIA drivers installed

## System Requirements

### For GPU Acceleration

- **GPU**: NVIDIA GPU with CUDA support (Compute Capability 6.0+)
- **CUDA**: Version 11.8 or 12.x
- **cuDNN**: Matching cuDNN version
- **VRAM**: 4GB+ recommended (models are ~100MB, working memory varies)
- **Driver**: Latest NVIDIA drivers

### Installation

```bash
# Install CUDA-enabled ONNX Runtime
pip install onnxruntime-gpu

# Or install with all dependencies
pip install -r requirements.txt
pip install onnxruntime-gpu
```

## Summary

- ✅ **GPU acceleration is implemented** via ONNX Runtime + CUDA
- ✅ **Configurable inference steps** (2-128, default 16)
- ✅ **Benchmarking tool** included for performance testing
- 📝 **PyTorch option** available as fallback if ONNX performance insufficient
- 🎯 **Expected speedup**: ~10x on high-end GPU vs CPU

Start with ONNX + CUDA implementation and only consider PyTorch if benchmarks show significantly worse performance than official numbers.
