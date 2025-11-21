import json
import os
import time
from contextlib import contextmanager
from typing import Optional, Tuple, List
from unicodedata import normalize

import numpy as np
import onnxruntime as ort
import soundfile as sf

from .tts_base import TTSEngine

# --- Core Classes from helper.py ---

class UnicodeProcessor:
    def __init__(self, unicode_indexer_path: str):
        if not os.path.exists(unicode_indexer_path):
             raise FileNotFoundError(f"Unicode indexer not found at {unicode_indexer_path}")
        with open(unicode_indexer_path, "r") as f:
            self.indexer = json.load(f)

    def _preprocess_text(self, text: str) -> str:
        text = normalize("NFKD", text)
        return text

    def _get_text_mask(self, text_ids_lengths: np.ndarray) -> np.ndarray:
        text_mask = length_to_mask(text_ids_lengths)
        return text_mask

    def _text_to_unicode_values(self, text: str) -> np.ndarray:
        unicode_values = np.array(
            [ord(char) for char in text], dtype=np.uint16
        )  # 2 bytes
        return unicode_values

    def __call__(self, text_list: list[str]) -> tuple[np.ndarray, np.ndarray]:
        text_list = [self._preprocess_text(t) for t in text_list]
        text_ids_lengths = np.array([len(text) for text in text_list], dtype=np.int64)
        text_ids = np.zeros((len(text_list), text_ids_lengths.max()), dtype=np.int64)
        for i, text in enumerate(text_list):
            unicode_vals = self._text_to_unicode_values(text)
            text_ids[i, : len(unicode_vals)] = np.array(
                [self.indexer[val] for val in unicode_vals], dtype=np.int64
            )
        text_mask = self._get_text_mask(text_ids_lengths)
        return text_ids, text_mask


class Style:
    def __init__(self, style_ttl_onnx: np.ndarray, style_dp_onnx: np.ndarray):
        self.ttl = style_ttl_onnx
        self.dp = style_dp_onnx


class TextToSpeech:
    def __init__(
        self,
        cfgs: dict,
        text_processor: UnicodeProcessor,
        dp_ort: ort.InferenceSession,
        text_enc_ort: ort.InferenceSession,
        vector_est_ort: ort.InferenceSession,
        vocoder_ort: ort.InferenceSession,
    ):
        self.cfgs = cfgs
        self.text_processor = text_processor
        self.dp_ort = dp_ort
        self.text_enc_ort = text_enc_ort
        self.vector_est_ort = vector_est_ort
        self.vocoder_ort = vocoder_ort
        self.sample_rate = cfgs["ae"]["sample_rate"]
        self.base_chunk_size = cfgs["ae"]["base_chunk_size"]
        self.chunk_compress_factor = cfgs["ttl"]["chunk_compress_factor"]
        self.ldim = cfgs["ttl"]["latent_dim"]

    def sample_noisy_latent(
        self, duration: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        bsz = len(duration)
        wav_len_max = duration.max() * self.sample_rate
        wav_lengths = (duration * self.sample_rate).astype(np.int64)
        chunk_size = self.base_chunk_size * self.chunk_compress_factor
        latent_len = ((wav_len_max + chunk_size - 1) / chunk_size).astype(np.int32)
        latent_dim = self.ldim * self.chunk_compress_factor
        noisy_latent = np.random.randn(bsz, latent_dim, latent_len).astype(np.float32)
        latent_mask = get_latent_mask(
            wav_lengths, self.base_chunk_size, self.chunk_compress_factor
        )
        noisy_latent = noisy_latent * latent_mask
        return noisy_latent, latent_mask

    def infer(
        self, text_list: list[str], style: Style, total_step: int, speed: float = 1.05
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Original _infer method made public.
        Returns raw wav (batch, length) and duration.
        """
        assert (
            len(text_list) == style.ttl.shape[0]
        ), "Number of texts must match number of style vectors"
        bsz = len(text_list)
        text_ids, text_mask = self.text_processor(text_list)
        dur_onnx, *_ = self.dp_ort.run(
            None, {"text_ids": text_ids, "style_dp": style.dp, "text_mask": text_mask}
        )
        dur_onnx = dur_onnx / speed
        text_emb_onnx, *_ = self.text_enc_ort.run(
            None,
            {"text_ids": text_ids, "style_ttl": style.ttl, "text_mask": text_mask},
        )  # dur_onnx: [bsz]
        xt, latent_mask = self.sample_noisy_latent(dur_onnx)
        total_step_np = np.array([total_step] * bsz, dtype=np.float32)
        for step in range(total_step):
            current_step = np.array([step] * bsz, dtype=np.float32)
            xt, *_ = self.vector_est_ort.run(
                None,
                {
                    "noisy_latent": xt,
                    "text_emb": text_emb_onnx,
                    "style_ttl": style.ttl,
                    "text_mask": text_mask,
                    "latent_mask": latent_mask,
                    "current_step": current_step,
                    "total_step": total_step_np,
                },
            )
        wav, *_ = self.vocoder_ort.run(None, {"latent": xt})
        return wav, dur_onnx

# --- Helper Functions ---

def length_to_mask(lengths: np.ndarray, max_len: Optional[int] = None) -> np.ndarray:
    max_len = max_len or lengths.max()
    ids = np.arange(0, max_len)
    mask = (ids < np.expand_dims(lengths, axis=1)).astype(np.float32)
    return mask.reshape(-1, 1, max_len)

def get_latent_mask(
    wav_lengths: np.ndarray, base_chunk_size: int, chunk_compress_factor: int
) -> np.ndarray:
    latent_size = base_chunk_size * chunk_compress_factor
    latent_lengths = (wav_lengths + latent_size - 1) // latent_size
    latent_mask = length_to_mask(latent_lengths)
    return latent_mask

def load_onnx(
    onnx_path: str, opts: ort.SessionOptions, providers: list[str]
) -> ort.InferenceSession:
    if not os.path.exists(onnx_path):
        raise FileNotFoundError(f"Model file not found: {onnx_path}")

    # LFS Check: Check if file is an LFS pointer
    try:
        with open(onnx_path, 'rb') as f:
            header = f.read(100)
            if b'version https://git-lfs.github.com/spec/v1' in header:
                 raise RuntimeError(f"Model file {onnx_path} is a Git LFS pointer. Please run 'git lfs pull'.")
    except Exception as e:
        if "is a Git LFS pointer" in str(e):
            raise e
        # Ignore other errors (e.g. permission), let onnxruntime handle it

    return ort.InferenceSession(onnx_path, sess_options=opts, providers=providers)

def load_onnx_all(
    onnx_dir: str, opts: ort.SessionOptions, providers: list[str]
) -> tuple:
    dp_onnx_path = os.path.join(onnx_dir, "duration_predictor.onnx")
    text_enc_onnx_path = os.path.join(onnx_dir, "text_encoder.onnx")
    vector_est_onnx_path = os.path.join(onnx_dir, "vector_estimator.onnx")
    vocoder_onnx_path = os.path.join(onnx_dir, "vocoder.onnx")

    dp_ort = load_onnx(dp_onnx_path, opts, providers)
    text_enc_ort = load_onnx(text_enc_onnx_path, opts, providers)
    vector_est_ort = load_onnx(vector_est_onnx_path, opts, providers)
    vocoder_ort = load_onnx(vocoder_onnx_path, opts, providers)
    return dp_ort, text_enc_ort, vector_est_ort, vocoder_ort

def load_cfgs(onnx_dir: str) -> dict:
    cfg_path = os.path.join(onnx_dir, "tts.json")
    if not os.path.exists(cfg_path):
        raise FileNotFoundError(f"Config file not found: {cfg_path}")
    with open(cfg_path, "r") as f:
        cfgs = json.load(f)
    return cfgs

def load_text_processor(onnx_dir: str) -> UnicodeProcessor:
    unicode_indexer_path = os.path.join(onnx_dir, "unicode_indexer.json")
    text_processor = UnicodeProcessor(unicode_indexer_path)
    return text_processor

def load_model(onnx_dir: str, use_gpu: bool = False) -> TextToSpeech:
    opts = ort.SessionOptions()
    if use_gpu:
        # Basic GPU support if available, else CPU
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    else:
        providers = ["CPUExecutionProvider"]

    cfgs = load_cfgs(onnx_dir)
    dp_ort, text_enc_ort, vector_est_ort, vocoder_ort = load_onnx_all(
        onnx_dir, opts, providers
    )
    text_processor = load_text_processor(onnx_dir)
    return TextToSpeech(
        cfgs, text_processor, dp_ort, text_enc_ort, vector_est_ort, vocoder_ort
    )

def load_voice_style(voice_style_path: str) -> Style:
    """Loads a single voice style"""
    if not os.path.exists(voice_style_path):
        raise FileNotFoundError(f"Voice style not found: {voice_style_path}")

    with open(voice_style_path, "r") as f:
        voice_style = json.load(f)

    ttl_dims = voice_style["style_ttl"]["dims"]
    dp_dims = voice_style["style_dp"]["dims"]

    ttl_data = np.array(voice_style["style_ttl"]["data"], dtype=np.float32).flatten()
    ttl_style = ttl_data.reshape(1, ttl_dims[1], ttl_dims[2]) # Batch size 1

    dp_data = np.array(voice_style["style_dp"]["data"], dtype=np.float32).flatten()
    dp_style = dp_data.reshape(1, dp_dims[1], dp_dims[2]) # Batch size 1

    return Style(ttl_style, dp_style)

# --- Interface for Audiopub ---

class TTSWrapper(TTSEngine):
    """Supertonic TTS Engine Implementation"""

    def __init__(self, assets_dir: str, use_gpu: bool = False):
        super().__init__(assets_dir, use_gpu)
        self.onnx_dir = os.path.join(assets_dir, "onnx") # Assuming 'onnx' subdir in assets, or assets itself
        if not os.path.exists(os.path.join(self.onnx_dir, "tts.json")):
            # If not in assets/onnx, check assets/
            if os.path.exists(os.path.join(assets_dir, "tts.json")):
                self.onnx_dir = assets_dir
            else:
                 # Fallback/Error, but we let load_model handle it or caller to check
                 pass

        self.model = None
        self.current_style = None

    def load(self):
        print(f"Loading TTS model from {self.onnx_dir}...")
        self.model = load_model(self.onnx_dir, self.use_gpu)
        print("Model loaded.")

    def set_voice(self, voice_path: str):
        if self.current_voice_path != voice_path:
            print(f"Loading voice: {voice_path}")
            self.current_style = load_voice_style(voice_path)
            self.current_voice_path = voice_path

    def warm_up(self):
        """Runs a short inference to warm up the model."""
        if not self.model or not self.current_style:
            raise RuntimeError("Model or voice not loaded.")
        print("Warming up model...")
        self.model.infer(["."], self.current_style, total_step=1)
        print("Warm up complete.")

    def synthesize(self, text: str, speed: float = 1.0, steps: int = 5) -> Tuple[np.ndarray, int]:
        """
        Synthesizes text to audio.
        Returns (audio_data_float32_numpy, sample_rate)
        """
        if not self.model or not self.current_style:
            raise RuntimeError("Model or voice not loaded.")

        # The model.infer expects a list of texts matching the batch size of style.
        # Our load_voice_style loads with batch size 1.
        wav, dur = self.model.infer([text], self.current_style, total_step=steps, speed=speed)

        # wav is [Batch, Time]
        wav_data = wav[0]
        # Trim based on duration? The original code does:
        # w = wav[b, : int(text_to_speech.sample_rate * duration[b].item())]
        valid_length = int(self.model.sample_rate * dur[0].item())
        wav_data = wav_data[:valid_length]

        return wav_data, self.model.sample_rate

    def get_sample_rate(self) -> int:
        """Get the output sample rate of this engine"""
        if self.model:
            return self.model.sample_rate
        return 24000  # Default for Supertonic

    @property
    def engine_name(self) -> str:
        """Return the name of this TTS engine"""
        return "supertonic"

    @property
    def voice_file_extension(self) -> str:
        """Return the expected voice file extension"""
        return ".json"
