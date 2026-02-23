"""
KOMMZ VOICE - XTTS v2 Modal endpoint

Deploy:
  pip install modal
  modal deploy modal_xtts.py

API:
  POST /clone
  FormData:
    - speaker_wav: file
    - text: str
    - reference_text: str (optional)
    - language: str (default: fr)
    - speed: float (default: 1.0)
    - temperature: float (accepted for API compatibility, currently not used by XTTS)
"""

from __future__ import annotations

import os
import tempfile
import time
import wave
import functools
from pathlib import Path

import modal
from fastapi import File, Form, UploadFile
from fastapi.responses import JSONResponse, Response


tts_cache = modal.Volume.from_name("kommz-xtts-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg")
    .env({"COQUI_TOS_AGREED": "1"})
    .pip_install(
        "TTS==0.22.0",
        # Keep transformers/tokenizers compatible with Coqui TTS 0.22.0 (XTTS v2).
        "transformers==4.39.3",
        "tokenizers==0.15.2",
        # Torch 2.6+ changes torch.load(weights_only=True by default) and breaks XTTS checkpoints.
        "torch==2.5.1",
        "torchaudio==2.5.1",
        "numpy",
        "soundfile",
        "fastapi",
        "python-multipart",
    )
)

app = modal.App("kommz-voice-xtts", image=image)

XTTS_MIN_CONTAINERS = int(os.environ.get("XTTS_MIN_CONTAINERS", "0"))
XTTS_IDLE_TIMEOUT = int(os.environ.get("XTTS_IDLE_TIMEOUT", "300"))


@app.cls(
    gpu="A10G",
    memory=16384,
    scaledown_window=XTTS_IDLE_TIMEOUT,
    min_containers=XTTS_MIN_CONTAINERS,
    volumes={"/root/.local/share/tts": tts_cache},
)
class XTTSModel:
    @staticmethod
    def _wav_duration_seconds(wav_bytes: bytes) -> float:
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(wav_bytes)
                tmp_path = tmp.name
            try:
                with wave.open(tmp_path, "rb") as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate() or 1
                    return float(frames) / float(rate)
            finally:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
        except Exception:
            return 0.0

    def _ensure_model(self):
        if hasattr(self, "tts"):
            return
        # Non-interactive containers (Modal) cannot answer input() prompts.
        os.environ.setdefault("COQUI_TOS_AGREED", "1")
        # Compatibility guard for Coqui XTTS checkpoints with PyTorch weights_only behavior.
        try:
            import torch
            _torch_load = torch.load

            @functools.wraps(_torch_load)
            def _compat_torch_load(*args, **kwargs):
                kwargs.setdefault("weights_only", False)
                return _torch_load(*args, **kwargs)

            torch.load = _compat_torch_load  # type: ignore[assignment]
        except Exception:
            pass
        from TTS.api import TTS
        # Force GPU usage on A10G container; fallback to CPU only if CUDA unavailable.
        try:
            import torch
            use_gpu = bool(torch.cuda.is_available())
            if use_gpu:
                torch.set_float32_matmul_precision("high")
        except Exception:
            use_gpu = False
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=use_gpu)
        print(f"[XTTS] device={'cuda' if use_gpu else 'cpu'} pid={os.getpid()}")

    @modal.enter()
    def load(self):
        self._ensure_model()

    @modal.method()
    def clone(
        self,
        text: str,
        speaker_wav_bytes: bytes,
        speaker_filename: str,
        language: str = "fr",
        speed: float = 1.0,
        temperature: float = 0.7,  # accepted for API compatibility
    ) -> bytes:
        import soundfile as sf

        self._ensure_model()
        t0 = time.perf_counter()

        language = (language or "fr").strip().lower()
        if not text or not text.strip():
            raise ValueError("text is required")

        # Clamp speed to sane range.
        try:
            speed = float(speed)
        except Exception:
            speed = 1.0
        speed = max(0.5, min(2.0, speed))

        # temperature is currently kept for compatibility even if XTTS API does not use it.
        _ = temperature

        suffix = Path(speaker_filename or "speaker.wav").suffix or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as spk:
            spk.write(speaker_wav_bytes)
            speaker_path = spk.name

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as out:
            out_path = out.name

        try:
            self.tts.tts_to_file(
                text=text,
                speaker_wav=speaker_path,
                language=language,
                file_path=out_path,
                speed=speed,
            )
            audio, sr = sf.read(out_path, dtype="float32")
            # Normalize to 16-bit PCM WAV bytes for downstream compatibility.
            import numpy as np

            pcm16 = (np.clip(audio, -1.0, 1.0) * 32767.0).astype("int16")
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as final_wav:
                final_path = final_wav.name
            sf.write(final_path, pcm16, sr, subtype="PCM_16")
            with open(final_path, "rb") as f:
                out_bytes = f.read()

            elapsed = max(0.001, time.perf_counter() - t0)
            audio_sec = self._wav_duration_seconds(out_bytes)
            rtf = (elapsed / audio_sec) if audio_sec > 0 else 0.0
            print(
                f"[XTTS] synth_time={elapsed:.3f}s audio={audio_sec:.3f}s "
                f"rtf={rtf:.3f} lang={language} chars={len(text)} speed={speed:.2f}"
            )
            return out_bytes
        finally:
            for p in (speaker_path, out_path):
                try:
                    os.remove(p)
                except Exception:
                    pass
            try:
                os.remove(final_path)  # type: ignore[name-defined]
            except Exception:
                pass

    @modal.method()
    def warmup(self) -> dict:
        self._ensure_model()
        return {"ready": bool(hasattr(self, "tts")), "model": "xtts_v2"}

xtts_actor = XTTSModel()


@app.function(
    image=image,
    timeout=600,
    scaledown_window=XTTS_IDLE_TIMEOUT,
    min_containers=XTTS_MIN_CONTAINERS,
    volumes={"/root/.local/share/tts": tts_cache},
)
@modal.fastapi_endpoint(method="POST")
async def clone(
    speaker_wav: UploadFile = File(...),
    text: str = Form(...),
    reference_text: str = Form(default=""),
    language: str = Form(default="fr"),
    speed: float = Form(default=1.0),
    temperature: float = Form(default=0.7),
):
    if not text.strip():
        return JSONResponse(status_code=400, content={"error": "text is required"})

    speaker_bytes = await speaker_wav.read()
    if not speaker_bytes:
        return JSONResponse(status_code=400, content={"error": "speaker_wav is empty"})

    try:
        wav_bytes = await xtts_actor.clone.remote.aio(
            text=text.strip(),
            speaker_wav_bytes=speaker_bytes,
            speaker_filename=speaker_wav.filename or "speaker.wav",
            language=language,
            speed=speed,
            temperature=temperature,
        )
        return Response(content=wav_bytes, media_type="audio/wav")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"XTTS error: {e}"})


@app.function(
    image=image,
    timeout=900,
    scaledown_window=XTTS_IDLE_TIMEOUT,
    min_containers=XTTS_MIN_CONTAINERS,
    volumes={"/root/.local/share/tts": tts_cache},
)
@modal.fastapi_endpoint(method="POST")
async def warmup():
    try:
        data = await xtts_actor.warmup.remote.aio()
        return JSONResponse(content={"status": "ok", **(data or {})})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"warmup failed: {e}"})


@app.function(image=image, volumes={"/root/.local/share/tts": tts_cache})
@modal.fastapi_endpoint(method="GET")
async def health():
    return JSONResponse(
        content={
            "status": "ok",
            "service": "kommz-voice-xtts",
            "model": "xtts_v2",
        }
    )

