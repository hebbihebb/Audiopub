"""
GPU Acceleration Setup for Audiopub Supertonic TTS
Call this at the start of your application to enable GPU support.

Usage:
    from setup_gpu_env import setup_gpu
    setup_gpu()
"""

import os
import sys

def setup_gpu(conda_env_path="/mnt/Games/abogen-env", verbose=True):
    """
    Setup CUDA library paths for GPU acceleration with ONNX Runtime.
    
    Args:
        conda_env_path: Path to conda environment with CUDA libraries
        verbose: Print setup information
    
    Returns:
        bool: True if setup successful, False if conda_env not found
    """
    if not os.path.exists(conda_env_path):
        if verbose:
            print(f"⚠️  Conda environment not found: {conda_env_path}")
        return False
    
    # CUDA library paths
    cuda_lib_paths = [
        f"{conda_env_path}/lib/python3.12/site-packages/nvidia/cublas/lib",
        f"{conda_env_path}/lib/python3.12/site-packages/nvidia/cudnn/lib",
        f"{conda_env_path}/lib/python3.12/site-packages/nvidia/cuda_runtime/lib",
        f"{conda_env_path}/lib/python3.12/site-packages/nvidia/curand/lib",
        f"{conda_env_path}/lib/python3.12/site-packages/nvidia/cufft/lib",
        f"{conda_env_path}/lib/python3.12/site-packages/nvidia/cusolver/lib",
        f"{conda_env_path}/lib/python3.12/site-packages/nvidia/nccl/lib",
    ]
    
    # Add to LD_LIBRARY_PATH
    current_path = os.environ.get("LD_LIBRARY_PATH", "")
    new_path = ":".join(cuda_lib_paths)
    if current_path:
        new_path = f"{new_path}:{current_path}"
    
    os.environ["LD_LIBRARY_PATH"] = new_path
    
    if verbose:
        print("✓ GPU acceleration enabled via ONNX Runtime + CUDA")
        print(f"  CUDA libraries: {conda_env_path}")
        
        # Verify CUDA is available
        try:
            import onnxruntime as ort
            providers = ort.get_available_providers()
            if "CUDAExecutionProvider" in providers:
                print("✓ CUDA provider available in ONNX Runtime")
            else:
                print("⚠️  CUDA provider not detected, using CPU")
        except ImportError:
            print("⚠️  onnxruntime not installed")
    
    return True

if __name__ == "__main__":
    setup_gpu()
