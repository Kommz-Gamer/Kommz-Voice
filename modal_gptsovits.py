"""
KOMMZ VOICE - GPT-SoVITS v2Pro Modal endpoint

Deploy:
  set GPTSOVITS_LOCAL_DIR=C:/Users/nicol/Desktop/GPT-SoVITS-v2pro
  modal deploy modal_gptsovits.py

Optional env vars:
  GPTSOVITS_CONFIG_REL=GPT_SoVITS/configs/tts_infer.yaml
  GPTSOVITS_CUSTOM_T2S_WEIGHTS_PATH=GPT_weights_v2Pro/your_model.ckpt
  GPTSOVITS_CUSTOM_VITS_WEIGHTS_PATH=SoVITS_weights_v2Pro/your_model.pth
  GPTSOVITS_DEFAULT_VARIANT=auto
  GPTSOVITS_GPU=A10G
  GPTSOVITS_MIN_CONTAINERS=0
  GPTSOVITS_IDLE_TIMEOUT=300

API:
  POST /tts
    multipart/form-data:
      - ref_audio: file
      - text: str
      - text_lang: str
      - prompt_lang: str
      - prompt_text: str
      - style_text: str (optional; fallback to text)
      - model_variant: auto|custom|generic (optional; default=auto)
      - speed_factor: float (optional)
      - top_k: int (optional)
      - top_p: float (optional)
      - temperature: float (optional)
      - repetition_penalty: float (optional)
      - text_split_method: str (optional, default=cut5)
  POST /warmup
  GET  /health
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
import threading
import time
import warnings
from pathlib import Path
from typing import Optional

import modal
from fastapi import File, Form, UploadFile
from fastapi.responses import JSONResponse, Response

try:
    from requests import RequestsDependencyWarning
except Exception:
    RequestsDependencyWarning = Warning

warnings.filterwarnings("ignore", category=RequestsDependencyWarning)
warnings.filterwarnings(
    "ignore",
    message="Using `TRANSFORMERS_CACHE` is deprecated and will be removed in v5 of Transformers. Use `HF_HOME` instead.",
    category=FutureWarning,
)


REMOTE_ROOT = "/root/gpt-sovits"
WINDOWS_LOCAL_ROOT = Path(
    os.environ.get("GPTSOVITS_LOCAL_DIR", r"C:\Users\nicol\Desktop\GPT-SoVITS-v2pro")
).expanduser()
IS_WINDOWS_DEPLOY_HOST = os.name == "nt"
if IS_WINDOWS_DEPLOY_HOST and not WINDOWS_LOCAL_ROOT.exists():
    raise RuntimeError(
        f"GPTSOVITS_LOCAL_DIR introuvable: {WINDOWS_LOCAL_ROOT}. "
        "Definis GPTSOVITS_LOCAL_DIR avant le deploy Modal."
    )
LOCAL_ROOT = WINDOWS_LOCAL_ROOT if IS_WINDOWS_DEPLOY_HOST else Path(REMOTE_ROOT)

CONFIG_REL = os.environ.get("GPTSOVITS_CONFIG_REL", "GPT_SoVITS/configs/tts_infer.yaml").strip()
LEGACY_T2S_WEIGHTS_PATH = os.environ.get("GPTSOVITS_T2S_WEIGHTS_PATH", "").strip()
LEGACY_VITS_WEIGHTS_PATH = os.environ.get("GPTSOVITS_VITS_WEIGHTS_PATH", "").strip()
CUSTOM_T2S_WEIGHTS_PATH = os.environ.get(
    "GPTSOVITS_CUSTOM_T2S_WEIGHTS_PATH",
    LEGACY_T2S_WEIGHTS_PATH,
).strip()
CUSTOM_VITS_WEIGHTS_PATH = os.environ.get(
    "GPTSOVITS_CUSTOM_VITS_WEIGHTS_PATH",
    LEGACY_VITS_WEIGHTS_PATH,
).strip()
DEFAULT_VARIANT = (os.environ.get("GPTSOVITS_DEFAULT_VARIANT", "auto") or "auto").strip().lower()
if DEFAULT_VARIANT not in {"auto", "custom", "generic"}:
    DEFAULT_VARIANT = "auto"
GPTSOVITS_GPU = os.environ.get("GPTSOVITS_GPU", "A10G").strip() or "A10G"
GPTSOVITS_MIN_CONTAINERS = int(os.environ.get("GPTSOVITS_MIN_CONTAINERS", "0"))
GPTSOVITS_IDLE_TIMEOUT = int(os.environ.get("GPTSOVITS_IDLE_TIMEOUT", "300"))

hf_cache = modal.Volume.from_name("kommz-gptsovits-cache", create_if_missing=True)

image = modal.Image.debian_slim(python_version="3.11").apt_install(
    "ffmpeg",
    "build-essential",
    "libsndfile1",
    "libopenblas-dev",
    "libgl1",
    "libglib2.0-0",
    "libopencc-dev",
)
if IS_WINDOWS_DEPLOY_HOST:
    image = image.add_local_dir(str(WINDOWS_LOCAL_ROOT), remote_path=REMOTE_ROOT, copy=True)
image = (
    image.workdir(REMOTE_ROOT)
    .env(
        {
            "PYTHONPATH": f"{REMOTE_ROOT}:{REMOTE_ROOT}/GPT_SoVITS",
            "HF_HOME": "/root/.cache/huggingface",
            "NLTK_DATA": "/root/nltk_data",
        }
    )
    .pip_install(
        "torch==2.5.1",
        "torchaudio==2.5.1",
        "numpy<2.0",
        "soundfile",
        "scipy",
        "librosa==0.10.2",
        "fastapi",
        "python-multipart",
    )
    .run_commands("python -m pip install -r requirements.txt")
    .run_commands(
        "python -c \"import nltk; "
        "pkgs=['averaged_perceptron_tagger_eng','averaged_perceptron_tagger','cmudict','punkt','punkt_tab']; "
        "[nltk.download(pkg, download_dir='/root/nltk_data') for pkg in pkgs]\""
    )
)

app = modal.App("kommz-voice-gptsovits", image=image)


@app.cls(
    gpu=GPTSOVITS_GPU,
    memory=32768,
    scaledown_window=GPTSOVITS_IDLE_TIMEOUT,
    min_containers=GPTSOVITS_MIN_CONTAINERS,
    volumes={"/root/.cache/huggingface": hf_cache},
)
class GPTSoVITSModel:
    def _resolve_repo_path(self, raw_path: str) -> str:
        txt = str(raw_path or "").strip()
        if not txt:
            return ""
        p = Path(txt)
        if p.is_absolute():
            try:
                rel = p.resolve().relative_to(LOCAL_ROOT.resolve())
                return str(Path(REMOTE_ROOT) / rel).replace("\\", "/")
            except Exception:
                return str(p).replace("\\", "/")
        return str(Path(REMOTE_ROOT) / txt).replace("\\", "/")

    def _ensure_pipeline(self):
        if hasattr(self, "_tts_pipeline"):
            return
        if not hasattr(self, "_init_lock"):
            self._init_lock = threading.Lock()
        with self._init_lock:
            if hasattr(self, "_tts_pipeline"):
                return

            init_t0 = time.perf_counter()
            sys.path.insert(0, REMOTE_ROOT)
            sys.path.insert(0, f"{REMOTE_ROOT}/GPT_SoVITS")

            import torch
            import soundfile as sf
            from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config
            from GPT_SoVITS.TTS_infer_pack.text_segmentation_method import (
                get_method_names as get_cut_method_names,
            )

            self.sf = sf
            self.cut_method_names = set(get_cut_method_names())

            cfg = TTS_Config(str(Path(REMOTE_ROOT) / CONFIG_REL))
            use_gpu = bool(torch.cuda.is_available())
            cfg.device = "cuda" if use_gpu else "cpu"
            cfg.is_half = bool(use_gpu)

            self._tts_pipeline = TTS(cfg)
            self._tts_lock = threading.Lock()
            self.generic_t2s_path = self._resolve_repo_path(self._tts_pipeline.configs.t2s_weights_path)
            self.generic_vits_path = self._resolve_repo_path(self._tts_pipeline.configs.vits_weights_path)
            self.custom_t2s_path = self._resolve_repo_path(CUSTOM_T2S_WEIGHTS_PATH)
            self.custom_vits_path = self._resolve_repo_path(CUSTOM_VITS_WEIGHTS_PATH)
            self.current_variant = "generic"
            self.current_t2s_path = self.generic_t2s_path
            self.current_vits_path = self.generic_vits_path

            init_dt = max(0.001, time.perf_counter() - init_t0)
            print(
                f"[GPT-SoVITS] ready device={'cuda' if use_gpu else 'cpu'} "
                f"pid={os.getpid()} load_time={init_dt:.2f}s"
            )

    def _normalize_variant(self, raw_variant: str) -> str:
        variant = (raw_variant or DEFAULT_VARIANT or "auto").strip().lower()
        if variant not in {"auto", "custom", "generic"}:
            raise ValueError(f"Unsupported model_variant: {raw_variant}")
        return variant

    def _has_custom_variant(self) -> bool:
        return bool(self.custom_t2s_path and self.custom_vits_path)

    def _get_variant_weights(self, variant: str) -> tuple[str, str]:
        if variant == "generic":
            return self.generic_t2s_path, self.generic_vits_path
        if variant == "custom":
            if not self._has_custom_variant():
                raise RuntimeError("Custom GPT-SoVITS weights are not configured")
            return self.custom_t2s_path, self.custom_vits_path
        raise ValueError(f"Unsupported variant: {variant}")

    def _switch_variant_if_needed(self, variant: str) -> None:
        variant = self._normalize_variant(variant)
        if variant == "auto":
            variant = "custom" if self._has_custom_variant() else "generic"
        if self.current_variant == variant:
            return

        t2s_path, vits_path = self._get_variant_weights(variant)
        switch_t0 = time.perf_counter()
        self._tts_pipeline.init_t2s_weights(t2s_path)
        self._tts_pipeline.init_vits_weights(vits_path)
        self.current_variant = variant
        self.current_t2s_path = t2s_path
        self.current_vits_path = vits_path
        print(
            f"[GPT-SoVITS] switched variant={variant} "
            f"load_time={max(0.001, time.perf_counter() - switch_t0):.2f}s"
        )

    @staticmethod
    def _pack_wav(audio_data, rate: int) -> bytes:
        buf = io.BytesIO()
        import soundfile as sf

        sf.write(buf, audio_data, rate, format="wav")
        return buf.getvalue()

    def _prepare_reference_audio(self, ref_audio_bytes: bytes, ref_audio_filename: str) -> str:
        import numpy as np

        suffix = Path(ref_audio_filename or "reference.wav").suffix or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_ref:
            tmp_ref.write(ref_audio_bytes)
            ref_path = tmp_ref.name

        try:
            audio_data, sample_rate = self.sf.read(ref_path, dtype="float32", always_2d=False)
            if getattr(audio_data, "ndim", 1) > 1:
                audio_data = audio_data.mean(axis=1)
            if audio_data is None or len(audio_data) == 0:
                raise RuntimeError("Reference audio is empty after decoding")

            audio_data = np.asarray(audio_data, dtype="float32")
            duration = float(len(audio_data)) / float(sample_rate)
            was_changed = False

            if duration > 10.0:
                target_samples = max(1, int(sample_rate * 8.0))
                start = max(0, (len(audio_data) - target_samples) // 2)
                audio_data = audio_data[start : start + target_samples]
                was_changed = True
            elif duration < 3.0:
                target_samples = max(1, int(sample_rate * 3.0))
                missing = max(0, target_samples - len(audio_data))
                pad_left = missing // 2
                pad_right = missing - pad_left
                audio_data = np.pad(audio_data, (pad_left, pad_right), mode="constant")
                was_changed = True

            peak = float(np.max(np.abs(audio_data))) if len(audio_data) else 0.0
            if peak > 1.0:
                audio_data = audio_data / peak
                was_changed = True

            self.sf.write(ref_path, audio_data, sample_rate, format="wav")
            print(
                f"[GPT-SoVITS] ref prepared duration={len(audio_data)/float(sample_rate):.2f}s "
                f"changed={was_changed}"
            )
            return ref_path
        except Exception:
            try:
                os.remove(ref_path)
            except Exception:
                pass
            raise

    @modal.enter()
    def load(self):
        self._ensure_pipeline()

    @modal.method()
    def warmup(self) -> dict:
        self._ensure_pipeline()
        return {
            "ready": True,
            "model": "gpt_sovits_v2pro",
            "current_variant": self.current_variant,
            "default_variant": DEFAULT_VARIANT,
            "custom_available": self._has_custom_variant(),
        }

    @modal.method()
    def tts(
        self,
        ref_audio_bytes: bytes,
        ref_audio_filename: str,
        text: str,
        text_lang: str,
        prompt_lang: str,
        prompt_text: str = "",
        style_text: str = "",
        model_variant: str = DEFAULT_VARIANT,
        media_type: str = "wav",
        text_split_method: str = "cut5",
        top_k: int = 5,
        top_p: float = 1.0,
        temperature: float = 1.0,
        speed_factor: float = 1.0,
        repetition_penalty: float = 1.35,
        sample_steps: int = 32,
        parallel_infer: bool = True,
    ) -> bytes:
        self._ensure_pipeline()

        if not text.strip():
            raise ValueError("text is required")
        if not ref_audio_bytes:
            raise ValueError("ref_audio is empty")
        if media_type.strip().lower() != "wav":
            raise ValueError("Only media_type=wav is supported in this worker")

        split_method = (text_split_method or "cut5").strip()
        if split_method not in self.cut_method_names:
            raise ValueError(f"Unsupported text_split_method: {split_method}")

        style_text = (style_text or "").strip() or text.strip()
        requested_variant = self._normalize_variant(model_variant)
        if requested_variant == "auto":
            variants_to_try = ["custom", "generic"] if self._has_custom_variant() else ["generic"]
        elif requested_variant == "custom":
            variants_to_try = ["custom"]
        else:
            variants_to_try = ["generic"]

        ref_path = self._prepare_reference_audio(ref_audio_bytes, ref_audio_filename)

        try:
            req = {
                "text": text.strip(),
                "text_lang": (text_lang or "").strip().lower(),
                "ref_audio_path": ref_path,
                "prompt_text": (prompt_text or "").strip(),
                "prompt_lang": (prompt_lang or "").strip().lower(),
                "top_k": int(top_k),
                "top_p": float(top_p),
                "temperature": float(temperature),
                "text_split_method": split_method,
                "batch_size": 1,
                "batch_threshold": 0.75,
                "split_bucket": True,
                "speed_factor": float(speed_factor),
                "fragment_interval": 0.3,
                "seed": -1,
                "media_type": "wav",
                "streaming_mode": False,
                "parallel_infer": bool(parallel_infer),
                "repetition_penalty": float(repetition_penalty),
                "sample_steps": int(sample_steps),
                "super_sampling": False,
            }

            if style_text != text.strip():
                req["text"] = style_text

            last_error = None
            with self._tts_lock:
                for variant in variants_to_try:
                    try:
                        self._switch_variant_if_needed(variant)
                        gen = self._tts_pipeline.run(req)
                        sr, audio_data = next(gen)
                        return self._pack_wav(audio_data, int(sr))
                    except Exception as e:
                        last_error = e
                        if requested_variant != "auto" or variant == variants_to_try[-1]:
                            raise
                        print(f"[GPT-SoVITS] variant={variant} failed, fallback next: {e}")
            if last_error is not None:
                raise last_error
            raise RuntimeError("GPT-SoVITS generation failed without explicit error")
        finally:
            try:
                os.remove(ref_path)
            except Exception:
                pass


gptsovits_actor = GPTSoVITSModel()


@app.function(
    image=image,
    timeout=900,
    scaledown_window=GPTSOVITS_IDLE_TIMEOUT,
    min_containers=GPTSOVITS_MIN_CONTAINERS,
    volumes={"/root/.cache/huggingface": hf_cache},
)
@modal.fastapi_endpoint(method="POST")
async def tts(
    ref_audio: UploadFile = File(...),
    text: str = Form(...),
    text_lang: str = Form(...),
    prompt_lang: str = Form(...),
    prompt_text: str = Form(default=""),
    style_text: str = Form(default=""),
    model_variant: str = Form(default=DEFAULT_VARIANT),
    media_type: str = Form(default="wav"),
    text_split_method: str = Form(default="cut5"),
    top_k: int = Form(default=5),
    top_p: float = Form(default=1.0),
    temperature: float = Form(default=1.0),
    speed_factor: float = Form(default=1.0),
    repetition_penalty: float = Form(default=1.35),
    sample_steps: int = Form(default=32),
    parallel_infer: bool = Form(default=True),
):
    ref_bytes = await ref_audio.read()
    if not ref_bytes:
        return JSONResponse(status_code=400, content={"error": "ref_audio is empty"})

    try:
        wav_bytes = await gptsovits_actor.tts.remote.aio(
            ref_audio_bytes=ref_bytes,
            ref_audio_filename=ref_audio.filename or "reference.wav",
            text=text,
            text_lang=text_lang,
            prompt_lang=prompt_lang,
            prompt_text=prompt_text,
            style_text=style_text,
            model_variant=model_variant,
            media_type=media_type,
            text_split_method=text_split_method,
            top_k=top_k,
            top_p=top_p,
            temperature=temperature,
            speed_factor=speed_factor,
            repetition_penalty=repetition_penalty,
            sample_steps=sample_steps,
            parallel_infer=parallel_infer,
        )
        return Response(content=wav_bytes, media_type="audio/wav")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"GPT-SoVITS error: {e}"})


@app.function(
    image=image,
    timeout=900,
    scaledown_window=GPTSOVITS_IDLE_TIMEOUT,
    min_containers=GPTSOVITS_MIN_CONTAINERS,
    volumes={"/root/.cache/huggingface": hf_cache},
)
@modal.fastapi_endpoint(method="POST")
async def warmup():
    try:
        data = await gptsovits_actor.warmup.remote.aio()
        return JSONResponse(content={"status": "ok", **(data or {})})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"warmup failed: {e}"})


@app.function(image=image, volumes={"/root/.cache/huggingface": hf_cache})
@modal.fastapi_endpoint(method="GET")
async def health():
    return JSONResponse(
        content={
            "status": "ok",
            "service": "kommz-voice-gptsovits",
            "model": "gpt_sovits_v2pro",
            "config_rel": CONFIG_REL,
            "default_variant": DEFAULT_VARIANT,
            "custom_t2s": bool(CUSTOM_T2S_WEIGHTS_PATH),
            "custom_vits": bool(CUSTOM_VITS_WEIGHTS_PATH),
            "custom_available": bool(CUSTOM_T2S_WEIGHTS_PATH and CUSTOM_VITS_WEIGHTS_PATH),
            "legacy_env_detected": bool(LEGACY_T2S_WEIGHTS_PATH or LEGACY_VITS_WEIGHTS_PATH),
        }
    )
