#!/bin/bash
# GPU acceleration setup for Audiopub Supertonic TTS
# Source this file to enable GPU acceleration: source setup_gpu.sh

CONDA_ENV="/mnt/Games/abogen-env"

export LD_LIBRARY_PATH="${CONDA_ENV}/lib/python3.12/site-packages/nvidia/cublas/lib:\
${CONDA_ENV}/lib/python3.12/site-packages/nvidia/cudnn/lib:\
${CONDA_ENV}/lib/python3.12/site-packages/nvidia/cuda_runtime/lib:\
${CONDA_ENV}/lib/python3.12/site-packages/nvidia/curand/lib:\
${CONDA_ENV}/lib/python3.12/site-packages/nvidia/cufft/lib:\
${CONDA_ENV}/lib/python3.12/site-packages/nvidia/cusolver/lib:\
${CONDA_ENV}/lib/python3.12/site-packages/nvidia/nccl/lib:${LD_LIBRARY_PATH}"

echo "✓ GPU acceleration enabled"
echo "  - CUDA libraries from: ${CONDA_ENV}"
echo "  - Run 'python benchmark_gpu.py --gpu' to test GPU performance"
