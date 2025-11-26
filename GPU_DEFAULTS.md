# GPU Acceleration Default Configuration

## Summary

The Audiopub WebUI now has GPU acceleration **enabled by default** with a quality-focused inference step setting.

## Changes Made

### 1. Configuration Defaults (`audiopub/config.py`)

Added two new default settings:

```python
DEFAULT_USE_GPU = True                    # Enable GPU by default
DEFAULT_GPU_QUALITY_STEPS = 16            # Quality steps (16 = balanced)
```

### 2. WebUI Initialization (`audiopub/main.py`)

- Updated state initialization to use GPU defaults:
  ```python
  "use_gpu": config.DEFAULT_USE_GPU,
  "inference_steps": config.DEFAULT_GPU_QUALITY_STEPS,
  ```

- Added automatic GPU setup on startup:
  ```python
  from setup_gpu_env import setup_gpu
  setup_gpu(verbose=False)  # Silent setup at startup
  ```

## Startup Behavior

When you run `python audiopub/main.py`:

1. **GPU Setup**: Automatic CUDA library path configuration (if available)
2. **GPU Enabled**: GPU acceleration toggle starts as ON
3. **Quality Setting**: Inference steps default to 16 (balanced quality/speed)
4. **Performance**: ~534-1091 chars/sec on RTX 2070 (6-7x faster than CPU)

## User Control

Users can still control GPU settings in the WebUI:

- **GPU ACCELERATION Toggle**: Turn GPU ON/OFF anytime
- **INFERENCE STEPS Slider**: Adjust quality (2-128)
  - 2-5 steps: Real-time/streaming (fastest, lower quality)
  - 16 steps: Balanced (current default, recommended)
  - 32+ steps: High quality (slower, best audio)

## Performance Expectations

With default settings (16-step GPU inference):

| Metric | Value |
|--------|-------|
| Speed | 534-1091 chars/sec |
| RTF | 0.013-0.026 |
| vs CPU | 6-7x faster |
| vs Real-time | 38-76x faster |

## Configuration Options

To change defaults, edit `audiopub/config.py`:

```python
# For CPU-only mode:
DEFAULT_USE_GPU = False

# For different quality (faster):
DEFAULT_GPU_QUALITY_STEPS = 5

# For high quality:
DEFAULT_GPU_QUALITY_STEPS = 32
```

## Backward Compatibility

- CPU-only systems: GPU toggle will be ON but will gracefully fall back to CPU
- Users can turn GPU OFF in the UI at any time
- All existing functionality unchanged

## Files Modified

- `audiopub/config.py` - Added DEFAULT_USE_GPU and DEFAULT_GPU_QUALITY_STEPS
- `audiopub/main.py` - Updated state init and added GPU setup call

## Related Files

- `GPU_SETUP.md` - How to set up and troubleshoot GPU
- `GPU_BENCHMARKING.md` - Detailed performance metrics
- `setup_gpu.sh` - Bash script for manual GPU setup
- `setup_gpu_env.py` - Python module for GPU initialization

