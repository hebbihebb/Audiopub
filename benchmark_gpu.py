#!/usr/bin/env python3
"""
GPU Benchmarking Script for Supertonic TTS
==========================================

This script benchmarks Supertonic TTS performance with different configurations:
- CPU vs GPU (CUDA)
- Different inference step counts (2, 5, 16, 32, 64, 128)
- Different text lengths (Short, Mid, Long)

Outputs performance metrics matching the official Supertone benchmarks:
- Characters per Second
- Real-time Factor (RTF)

Usage:
    python benchmark_gpu.py [--gpu] [--steps 2,5,16] [--output results.json]
"""

import argparse
import json
import os
import time
import sys
from typing import Dict, List, Tuple
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from audiopub.core.tts_factory import create_tts_engine
from audiopub import config

# Test texts matching Supertone's benchmarks
TEST_TEXTS = {
    "short": "Hello, this is a test of the text to speech system today.",  # 59 chars
    "mid": "The quick brown fox jumps over the lazy dog multiple times. "
           "This sentence is designed to test the performance of our speech synthesis "
           "system with medium length input.",  # ~152 chars
    "long": "In the heart of a bustling city, where towering skyscrapers pierce the sky "
            "and endless streams of people flow through the streets, there exists a "
            "hidden world of stories waiting to be told. Each person carries with them "
            "a unique narrative, shaped by their experiences, dreams, and aspirations.",  # ~266 chars
}

def check_gpu_availability():
    """Check if GPU is available via ONNX Runtime"""
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        has_cuda = "CUDAExecutionProvider" in providers
        print(f"Available ONNX Runtime providers: {providers}")
        return has_cuda
    except ImportError:
        print("ERROR: onnxruntime not installed. Run: pip install -r requirements.txt")
        return False

def benchmark_synthesis(tts_engine, text: str, steps: int, iterations: int = 3) -> Dict:
    """
    Benchmark TTS synthesis for given text and steps.

    Returns:
        Dict with timing metrics
    """
    timings = []
    audio_durations = []

    # Warm-up run
    tts_engine.synthesize(text, speed=1.0, steps=steps)

    # Actual benchmark runs
    for i in range(iterations):
        start_time = time.time()
        wav_data, sample_rate = tts_engine.synthesize(text, speed=1.0, steps=steps)
        end_time = time.time()

        synthesis_time = end_time - start_time
        audio_duration = len(wav_data) / sample_rate

        timings.append(synthesis_time)
        audio_durations.append(audio_duration)

    avg_synthesis_time = np.mean(timings)
    avg_audio_duration = np.mean(audio_durations)

    # Calculate metrics
    chars_per_second = len(text) / avg_synthesis_time
    rtf = avg_synthesis_time / avg_audio_duration  # Real-time Factor

    return {
        "text_length": len(text),
        "synthesis_time": avg_synthesis_time,
        "audio_duration": avg_audio_duration,
        "chars_per_second": chars_per_second,
        "rtf": rtf,
        "timings": timings
    }

def run_benchmarks(use_gpu: bool, step_counts: List[int], voice_path: str = None):
    """
    Run comprehensive benchmarks.
    """
    print("\n" + "="*70)
    print(f"SUPERTONIC TTS BENCHMARK")
    print(f"Mode: {'GPU (CUDA)' if use_gpu else 'CPU'}")
    print(f"Inference Steps: {step_counts}")
    print("="*70 + "\n")

    # Initialize TTS engine
    print(f"Initializing TTS engine...")
    tts = create_tts_engine(config.TTS_ENGINE, config.ASSETS_DIR, use_gpu=use_gpu)
    tts.load()

    # Load default voice if not specified
    if voice_path is None:
        import glob
        voices = glob.glob(os.path.join(config.ASSETS_DIR, "*.json"))
        voices = [v for v in voices if not v.endswith(("tts.json", "unicode_indexer.json"))]
        if not voices:
            print("ERROR: No voice files found in assets directory")
            return None
        voice_path = voices[0]

    print(f"Loading voice: {os.path.basename(voice_path)}")
    tts.set_voice(voice_path)

    print("Warming up model...")
    tts.warm_up()

    results = {
        "config": {
            "use_gpu": use_gpu,
            "tts_engine": config.TTS_ENGINE,
            "voice": os.path.basename(voice_path)
        },
        "benchmarks": {}
    }

    # Run benchmarks for each step count
    for steps in step_counts:
        print(f"\n{'='*70}")
        print(f"Testing with {steps} inference steps")
        print(f"{'='*70}")

        step_results = {}

        for text_type, text in TEST_TEXTS.items():
            print(f"\n{text_type.upper()} ({len(text)} chars): ", end="", flush=True)

            result = benchmark_synthesis(tts, text, steps)
            step_results[text_type] = result

            print(f"{result['chars_per_second']:.0f} chars/sec, RTF: {result['rtf']:.3f}")

        results["benchmarks"][f"{steps}_steps"] = step_results

    return results

def print_summary_table(results: Dict):
    """Print formatted summary tables"""
    print("\n" + "="*70)
    print("SUMMARY RESULTS")
    print("="*70)

    mode = "GPU (CUDA)" if results["config"]["use_gpu"] else "CPU"

    # Characters per Second Table
    print(f"\nCharacters per Second ({mode}):")
    print("-" * 70)
    print(f"{'Steps':<10} {'Short (59)':<15} {'Mid (152)':<15} {'Long (266)':<15}")
    print("-" * 70)

    for step_key in sorted(results["benchmarks"].keys(), key=lambda x: int(x.split("_")[0])):
        steps = step_key.split("_")[0]
        bench = results["benchmarks"][step_key]
        print(f"{steps:<10} {bench['short']['chars_per_second']:<15.0f} "
              f"{bench['mid']['chars_per_second']:<15.0f} "
              f"{bench['long']['chars_per_second']:<15.0f}")

    # Real-time Factor Table
    print(f"\nReal-time Factor ({mode}):")
    print("-" * 70)
    print(f"{'Steps':<10} {'Short (59)':<15} {'Mid (152)':<15} {'Long (266)':<15}")
    print("-" * 70)

    for step_key in sorted(results["benchmarks"].keys(), key=lambda x: int(x.split("_")[0])):
        steps = step_key.split("_")[0]
        bench = results["benchmarks"][step_key]
        print(f"{steps:<10} {bench['short']['rtf']:<15.3f} "
              f"{bench['mid']['rtf']:<15.3f} "
              f"{bench['long']['rtf']:<15.3f}")

    print("\n" + "="*70 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Benchmark Supertonic TTS performance")
    parser.add_argument("--gpu", action="store_true", help="Enable GPU acceleration")
    parser.add_argument("--steps", type=str, default="2,5,16",
                       help="Comma-separated list of inference steps to test (default: 2,5,16)")
    parser.add_argument("--voice", type=str, default=None,
                       help="Path to voice file (default: first .json in assets)")
    parser.add_argument("--output", type=str, default=None,
                       help="Output JSON file for results")
    parser.add_argument("--iterations", type=int, default=3,
                       help="Number of iterations per test (default: 3)")

    args = parser.parse_args()

    # Parse step counts
    step_counts = [int(s.strip()) for s in args.steps.split(",")]

    # Check GPU availability if requested
    if args.gpu:
        if not check_gpu_availability():
            print("\nWARNING: GPU requested but CUDA not available. Falling back to CPU.")
            args.gpu = False

    # Run benchmarks
    results = run_benchmarks(args.gpu, step_counts, args.voice)

    if results is None:
        return 1

    # Print summary
    print_summary_table(results)

    # Save to file if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to: {args.output}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
