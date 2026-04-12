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
import threading
import subprocess
import re
import hashlib
from pathlib import Path
from typing import Optional

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
        "transformers==4.39.3",
        "tokenizers==0.15.2",
        "torch==2.5.1",
        "torchaudio==2.5.1",
        "numpy",
        "soundfile",
        "fastapi",
        "python-multipart",
        "cutlet",
        "fugashi",
        "unidic-lite",
    )
)


app = modal.App("kommz-voice-xtts", image=image)

XTTS_MIN_CONTAINERS = int(os.environ.get("XTTS_MIN_CONTAINERS", "0"))
XTTS_IDLE_TIMEOUT = int(os.environ.get("XTTS_IDLE_TIMEOUT", "300"))
XTTS_POSTPROCESS_MODE = os.environ.get("XTTS_POSTPROCESS_MODE", "strong").strip().lower()
XTTS_MASTERING_ENABLED = os.environ.get("XTTS_MASTERING_ENABLED", "1").strip().lower() in {"1", "true", "yes", "on"}
XTTS_LAUGH_MASTERING_ENABLED = os.environ.get("XTTS_LAUGH_MASTERING_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}
XTTS_LAUGH_BREATH_REDUCTION_ENABLED = os.environ.get("XTTS_LAUGH_BREATH_REDUCTION_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}
XTTS_REF_CLEAN_ENABLED = os.environ.get("XTTS_REF_CLEAN_ENABLED", "1").strip().lower() in {"1", "true", "yes", "on"}
XTTS_REF_MAX_SEC = max(5.0, min(15.0, float(os.environ.get("XTTS_REF_MAX_SEC", "10"))))
XTTS_DEFAULT_TOP_K = int(os.environ.get("XTTS_DEFAULT_TOP_K", "60"))
XTTS_DEFAULT_TOP_P = float(os.environ.get("XTTS_DEFAULT_TOP_P", "0.90"))
XTTS_DEFAULT_REPETITION_PENALTY = float(os.environ.get("XTTS_DEFAULT_REPETITION_PENALTY", "2.2"))
XTTS_DEFAULT_LENGTH_PENALTY = float(os.environ.get("XTTS_DEFAULT_LENGTH_PENALTY", "1.0"))
XTTS_DEFAULT_ENABLE_TEXT_SPLITTING = os.environ.get("XTTS_DEFAULT_ENABLE_TEXT_SPLITTING", "1").strip().lower() in {"1", "true", "yes", "on"}
XTTS_DEFAULT_GPT_COND_LEN = int(os.environ.get("XTTS_DEFAULT_GPT_COND_LEN", "12"))
XTTS_DEFAULT_GPT_COND_CHUNK_LEN = int(os.environ.get("XTTS_DEFAULT_GPT_COND_CHUNK_LEN", "4"))
XTTS_DEFAULT_MAX_REF_LEN = int(os.environ.get("XTTS_DEFAULT_MAX_REF_LEN", "10"))
XTTS_DEFAULT_SOUND_NORM_REFS = os.environ.get("XTTS_DEFAULT_SOUND_NORM_REFS", "0").strip().lower() in {"1", "true", "yes", "on"}
XTTS_CONDITIONING_CACHE_ENABLED = os.environ.get("XTTS_CONDITIONING_CACHE_ENABLED", "1").strip().lower() in {"1", "true", "yes", "on"}
XTTS_CONDITIONING_CACHE_MAX_ITEMS = max(8, min(256, int(os.environ.get("XTTS_CONDITIONING_CACHE_MAX_ITEMS", "64"))))
XTTS_FORCE_SPLIT_CHAR_LIMITS = {"ja": 71}
XTTS_SUPPORTED_LANGS = {
    "en",
    "es",
    "fr",
    "de",
    "it",
    "pt",
    "pl",
    "tr",
    "ru",
    "nl",
    "cs",
    "ar",
    "zh-cn",
    "hu",
    "ko",
    "ja",
    "hi",
}
XTTS_LANGUAGE_ALIASES = {
    "zh": "zh-cn",
    "zh_cn": "zh-cn",
    "zh-tw": "zh-cn",
    "pt-br": "pt",
    "pt-pt": "pt",
    "cs-cz": "cs",
    "kk": "ru",
    "uk": "ru",
    "bg": "ru",
    "sr": "ru",
    "mk": "ru",
    "be": "ru",
}


@app.cls(
    gpu="A10G",
    memory=16384,
    scaledown_window=XTTS_IDLE_TIMEOUT,
    min_containers=XTTS_MIN_CONTAINERS,
    volumes={"/root/.local/share/tts": tts_cache},
)
class XTTSModel:
    @staticmethod
    def _normalize_xtts_language(language: str, text: str = "") -> str:
        lang = (language or "fr").strip().lower().replace("_", "-")
        if lang in XTTS_SUPPORTED_LANGS:
            return lang
        if lang in XTTS_LANGUAGE_ALIASES:
            return XTTS_LANGUAGE_ALIASES[lang]

        short = lang.split("-", 1)[0]
        if short in XTTS_SUPPORTED_LANGS:
            return short
        if short in XTTS_LANGUAGE_ALIASES:
            return XTTS_LANGUAGE_ALIASES[short]
        if short == "zh":
            return "zh-cn"

        sample = str(text or "")
        if re.search(r"[\u0600-\u06FF]", sample):
            return "ar"
        if re.search(r"[\u0900-\u097F]", sample):
            return "hi"
        if re.search(r"[\uAC00-\uD7AF]", sample):
            return "ko"
        if re.search(r"[\u3040-\u30FF]", sample):
            return "ja"
        if re.search(r"[\u4E00-\u9FFF]", sample):
            return "zh-cn"
        if re.search(r"[\u0400-\u04FF]", sample):
            return "ru"
        return "en"

    @staticmethod
    def _to_bool(value, default: bool = False) -> bool:
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _file_sha1(path: str, chunk_size: int = 1024 * 1024) -> str:
        h = hashlib.sha1()
        with open(path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    def _conditioning_cache_key(
        self,
        speaker_path: str,
        language: str,
        gpt_cond_len: int,
        gpt_cond_chunk_len: int,
        max_ref_len: int,
        sound_norm_refs: bool,
    ) -> str:
        ref_hash = self._file_sha1(speaker_path)
        raw = f"{ref_hash}|{language}|{gpt_cond_len}|{gpt_cond_chunk_len}|{max_ref_len}|{int(sound_norm_refs)}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    def _get_conditioning_latents_cached(
        self,
        speaker_path: str,
        language: str,
        gpt_cond_len: int,
        gpt_cond_chunk_len: int,
        max_ref_len: int,
        sound_norm_refs: bool,
    ):
        if not XTTS_CONDITIONING_CACHE_ENABLED:
            return None, None, False

        if not hasattr(self, "_cond_cache_lock"):
            self._cond_cache_lock = threading.Lock()
        if not hasattr(self, "_cond_cache"):
            self._cond_cache = {}

        key = self._conditioning_cache_key(
            speaker_path=speaker_path,
            language=language,
            gpt_cond_len=gpt_cond_len,
            gpt_cond_chunk_len=gpt_cond_chunk_len,
            max_ref_len=max_ref_len,
            sound_norm_refs=sound_norm_refs,
        )

        with self._cond_cache_lock:
            row = self._cond_cache.get(key)
            if row:
                row["last_used"] = time.time()
                return row.get("gpt_cond_latent"), row.get("speaker_embedding"), True

        # Build latents (cache miss)
        model = self.tts.synthesizer.tts_model
        # API-compatible call in TTS 0.22.x
        gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
            audio_path=[speaker_path],
            gpt_cond_len=gpt_cond_len,
            gpt_cond_chunk_len=gpt_cond_chunk_len,
            max_ref_length=max_ref_len,
            sound_norm_refs=sound_norm_refs,
        )

        with self._cond_cache_lock:
            self._cond_cache[key] = {
                "gpt_cond_latent": gpt_cond_latent,
                "speaker_embedding": speaker_embedding,
                "created_at": time.time(),
                "last_used": time.time(),
            }
            # LRU trim
            if len(self._cond_cache) > XTTS_CONDITIONING_CACHE_MAX_ITEMS:
                oldest_key = min(self._cond_cache.items(), key=lambda kv: kv[1].get("last_used", 0.0))[0]
                self._cond_cache.pop(oldest_key, None)

        return gpt_cond_latent, speaker_embedding, False

    def _xtts_infer_with_cached_conditioning(
        self,
        text: str,
        language: str,
        speaker_path: str,
        out_path: str,
        speed: float,
        temperature: float,
        top_k: int,
        top_p: float,
        repetition_penalty: float,
        length_penalty: float,
        enable_text_splitting: bool,
        gpt_cond_len: int,
        gpt_cond_chunk_len: int,
        max_ref_len: int,
        sound_norm_refs: bool,
    ) -> tuple[bool, str]:
        """
        Try the fast path using cached conditioning latents.
        Returns (ok, status) where status is one of:
        - cache_hit
        - cache_miss
        - fallback_error:<reason>
        """
        try:
            import numpy as np
            import soundfile as sf

            model = self.tts.synthesizer.tts_model
            gpt_cond_latent, speaker_embedding, cache_hit = self._get_conditioning_latents_cached(
                speaker_path=speaker_path,
                language=language,
                gpt_cond_len=gpt_cond_len,
                gpt_cond_chunk_len=gpt_cond_chunk_len,
                max_ref_len=max_ref_len,
                sound_norm_refs=sound_norm_refs,
            )

            # XTTS 0.22 inference path
            infer = model.inference(
                text=text,
                language=language,
                gpt_cond_latent=gpt_cond_latent,
                speaker_embedding=speaker_embedding,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                repetition_penalty=repetition_penalty,
                length_penalty=length_penalty,
                speed=speed,
                enable_text_splitting=enable_text_splitting,
            )

            wav = None
            if isinstance(infer, dict):
                wav = infer.get("wav")
            if wav is None and hasattr(infer, "get"):
                try:
                    wav = infer.get("wav")
                except Exception:
                    wav = None
            if wav is None:
                wav = infer

            wav = np.asarray(wav, dtype=np.float32)
            if wav.ndim > 1:
                wav = wav.squeeze()
            sf.write(out_path, wav, 24000, subtype="PCM_16")
            return True, ("cache_hit" if cache_hit else "cache_miss")
        except Exception as e:
            return False, f"fallback_error:{e}"

    @staticmethod
    def _normalize_emotive_text(text: str, language: str) -> str:
        """Make laugh-like interjections easier for XTTS to pronounce."""
        src = (text or "").strip()
        if not src:
            return src

        lang = (language or "fr").strip().lower().split("-")[0]
        out = src

        # Normalize common laugh variants from speech recognition.
        # Examples: "AH AH AH", "ah ah", "ha ha ha", "ahaha"
        laugh_token = r"(?:a+h+|h+a+)"
        laugh_seq = re.compile(rf"\b{laugh_token}(?:[\s,.;:!?-]+{laugh_token})+\b", re.IGNORECASE)
        laugh_repeat = re.compile(r"\b(?:a?h){3,}a?\b", re.IGNORECASE)

        if lang in {"ja"}:
            out = laugh_seq.sub("ははは…", out)
            out = laugh_repeat.sub("ははは…", out)
        else:
            out = laugh_seq.sub("ha ha ha !", out)
            out = laugh_repeat.sub("ha ha ha !", out)

        # Other common emotion markers from live speech recognition.
        if lang in {"ja"}:
            rules = [
                (re.compile(r"\b(?:えー+|えっと+|うー+ん|うーん)\b", re.IGNORECASE), "えっと…"),
                (re.compile(r"\b(?:わあ+|おお+|おー+)\b", re.IGNORECASE), "わあ！"),
                (re.compile(r"\b(?:はぁ+|ふぅ+)\b", re.IGNORECASE), "はぁ…"),
                (re.compile(r"\b(?:しくしく|えーん)\b", re.IGNORECASE), "しくしく…"),
                (re.compile(r"\b(?:ぐるる+|ぐぬぬ)\b", re.IGNORECASE), "ぐるる…"),
                (re.compile(r"\b(?:あっ+|あー+|うわ+)\b", re.IGNORECASE), "あっ！"),
                (re.compile(r"\b(?:やった+)\b", re.IGNORECASE), "やった！"),
                (re.compile(r"\b(?:おっと+)\b", re.IGNORECASE), "おっと…"),
                (re.compile(r"\b(?:えっ+)\b", re.IGNORECASE), "えっ？"),
            ]
        else:
            rules = [
                (re.compile(r"\b(?:rire|rires|je\s+ris|je\s+rigole|rigole|rigoler)\b", re.IGNORECASE), "ha ha ha !"),
                (re.compile(r"\b(?:mdr|lol)\b", re.IGNORECASE), "ha ha ha !"),
                (re.compile(r"\b(?:euh+|heu+|hmm+|hum+)\b", re.IGNORECASE), "euh..."),
                (re.compile(r"\b(?:wow+|wo+w+|oh+)\b", re.IGNORECASE), "oh !"),
                (re.compile(r"\b(?:pff+|pfou+|soupir+)\b", re.IGNORECASE), "pff..."),
                (re.compile(r"\b(?:snif+|sob+)\b", re.IGNORECASE), "snif..."),
                (re.compile(r"\b(?:grr+|grrr+)\b", re.IGNORECASE), "grr..."),
                (re.compile(r"\b(?:hein+)\b", re.IGNORECASE), "hein ?"),
                (re.compile(r"\b(?:bah+|ben+|bof+)\b", re.IGNORECASE), "bah..."),
                (re.compile(r"\b(?:ouf+)\b", re.IGNORECASE), "ouf..."),
                (re.compile(r"\b(?:hop+)\b", re.IGNORECASE), "hop !"),
                (re.compile(r"\b(?:aie+|ouch+|aouh+)\b", re.IGNORECASE), "aïe !"),
                (re.compile(r"\b(?:beurk+|berk+)\b", re.IGNORECASE), "beurk..."),
                (re.compile(r"\b(?:bravo+|yeah+|yes+)\b", re.IGNORECASE), "yeah !"),
                (re.compile(r"\b(?:hein ?quoi+)\b", re.IGNORECASE), "hein ?"),
            ]
        for pat, repl in rules:
            out = pat.sub(repl, out)

        if lang in {"fr"}:
            # STT occasionally outputs single letters for laugh syllables.
            out = re.sub(
                r"\b(?:a+h?|h+a?)(?:[\s,.;:!?-]+(?:a+h?|h+a?)){2,}\b",
                "ha ha ha !",
                out,
                flags=re.IGNORECASE,
            )

        # Long repeated vowels often come from live dictation ("noooon", "ouiiii").
        out = re.sub(r"\b([A-Za-zÀ-ÿ])\1{3,}\b", r"\1\1\1", out)

        # Keep punctuation sane for synthesis.
        out = re.sub(r"([!?.,]){2,}", r"\1", out)
        out = re.sub(r"\s{2,}", " ", out).strip()
        return out

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

    @staticmethod
    def _postprocess_audio(audio, sr: int, laugh_mode: bool = False):
        """Reduce startup artifacts and avoid clipping without changing voice identity."""
        import numpy as np

        if audio is None:
            return audio

        y = np.asarray(audio, dtype=np.float32)
        if y.size == 0:
            return y

        # Remove DC offset (helps "muffled/pop" onset on some generations).
        y = y - float(np.mean(y))

        # Peak management.
        peak = float(np.max(np.abs(y)))
        if XTTS_POSTPROCESS_MODE == "ultra_safe":
            target_peak = 0.58
        elif XTTS_POSTPROCESS_MODE == "strong":
            target_peak = 0.72
        else:
            target_peak = 0.90
        # Laugh-like segments can spike harder: force extra headroom.
        if laugh_mode:
            target_peak = min(target_peak, 0.68)
        if peak > target_peak and peak > 1e-6:
            y = y * (target_peak / peak)

        # Soft limiter to tame harsh transients.
        if XTTS_POSTPROCESS_MODE == "ultra_safe":
            y = np.tanh(y * 1.45) / np.tanh(1.45)
        elif XTTS_POSTPROCESS_MODE == "strong":
            y = np.tanh(y * 1.15) / np.tanh(1.15)
        if laugh_mode:
            y = np.tanh(y * 1.20) / np.tanh(1.20)
            y = y * 0.98

        # Fade-in/out to remove clicks and "muffled burst" at start.
        if XTTS_POSTPROCESS_MODE == "ultra_safe":
            fade_ms = 180
        elif XTTS_POSTPROCESS_MODE == "strong":
            fade_ms = 120
        else:
            fade_ms = 14
        n = max(1, int(sr * (fade_ms / 1000.0)))
        n = min(n, max(1, y.shape[0] // 8))
        if n > 1:
            ramp = np.linspace(0.0, 1.0, n, dtype=np.float32)
            if y.ndim == 1:
                y[:n] *= ramp
                y[-n:] *= ramp[::-1]
            else:
                y[:n, :] *= ramp[:, None]
                y[-n:, :] *= ramp[::-1, None]

        # Extra startup guard for strong/ultra modes: hard mute at the very beginning.
        if XTTS_POSTPROCESS_MODE in {"strong", "ultra_safe"}:
            if XTTS_POSTPROCESS_MODE == "ultra_safe":
                guard_sec = 0.080
                pad_sec = 0.050
            else:
                guard_sec = 0.040
                pad_sec = 0.030
            guard_n = min(y.shape[0], max(1, int(sr * guard_sec)))
            if y.ndim == 1:
                y[:guard_n] *= 0.0
            else:
                y[:guard_n, :] *= 0.0

            # Prepend a tiny silence to hide startup artifacts from playback devices.
            pad_n = max(1, int(sr * pad_sec))
            if y.ndim == 1:
                y = np.concatenate([np.zeros(pad_n, dtype=np.float32), y], axis=0)
            else:
                y = np.concatenate([np.zeros((pad_n, y.shape[1]), dtype=np.float32), y], axis=0)

        return np.clip(y, -1.0, 1.0)

    @staticmethod
    def _master_with_ffmpeg(in_wav: str, out_wav: str, laugh_mode: bool = False) -> bool:
        """
        Apply a conservative mastering chain to reduce sporadic clipping/saturation.
        Falls back silently when ffmpeg or filter is unavailable.
        """
        # Keep chain conservative to preserve voice identity.
        if laugh_mode and XTTS_LAUGH_MASTERING_ENABLED:
            laugh_chain = [
                "highpass=f=70",
                "lowpass=f=13500",
            ]
            if XTTS_LAUGH_BREATH_REDUCTION_ENABLED and XTTS_POSTPROCESS_MODE == "ultra_safe":
                # Tames breath-like hiss/noise often heard during laugh interjections.
                laugh_chain.append("afftdn=nf=-22:tn=1")
            laugh_chain.extend(
                [
                    "acompressor=threshold=-20dB:ratio=2.4:attack=5:release=110:makeup=0",
                    "alimiter=limit=0.62",
                    "volume=-3.0dB",
                ]
            )
            af = ",".join(laugh_chain)
        else:
            af = ",".join(
                [
                    "highpass=f=55",
                    "lowpass=f=15500",
                    "alimiter=limit=0.74",
                    "volume=-1.5dB",
                ]
            )
        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            in_wav,
            "-af",
            af,
            "-c:a",
            "pcm_s16le",
            out_wav,
        ]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=20)
            return p.returncode == 0 and os.path.exists(out_wav)
        except Exception:
            return False

    @staticmethod
    def _probe_duration_seconds(path: str) -> float:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            path,
        ]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=8)
            if p.returncode != 0:
                return 0.0
            return float((p.stdout or "0").strip())
        except Exception:
            return 0.0

    @staticmethod
    def _prepare_reference_audio(in_path: str) -> str:
        """
        Normalize/clean reference audio for stable cloning.
        Returns processed path or original path on failure.
        """
        dur = XTTSModel._probe_duration_seconds(in_path)
        trim_args = []
        if dur > XTTS_REF_MAX_SEC:
            trim_args = ["-ss", "0", "-t", f"{XTTS_REF_MAX_SEC:.2f}"]

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            out_path = tmp.name

        # Conservative chain for reference cleaning (not output mastering).
        af = ",".join(
            [
                "highpass=f=60",
                "lowpass=f=15000",
                "dynaudnorm=f=120:g=12",
            ]
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            in_path,
            *trim_args,
            "-af",
            af,
            "-ac",
            "1",
            "-ar",
            "32000",
            "-c:a",
            "pcm_s16le",
            out_path,
        ]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
            if p.returncode == 0 and os.path.exists(out_path):
                return out_path
        except Exception:
            pass
        try:
            os.remove(out_path)
        except Exception:
            pass
        return in_path

    def _ensure_model(self):
        if hasattr(self, "tts"):
            return
        if not hasattr(self, "_init_lock"):
            self._init_lock = threading.Lock()
        with self._init_lock:
            if hasattr(self, "tts"):
                return
            init_t0 = time.perf_counter()
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
            init_dt = max(0.001, time.perf_counter() - init_t0)
            print(
                f"[XTTS] model_ready device={'cuda' if use_gpu else 'cpu'} "
                f"pid={os.getpid()} load_time={init_dt:.2f}s"
            )

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
        top_k: int = XTTS_DEFAULT_TOP_K,
        top_p: float = XTTS_DEFAULT_TOP_P,
        repetition_penalty: float = XTTS_DEFAULT_REPETITION_PENALTY,
        length_penalty: float = XTTS_DEFAULT_LENGTH_PENALTY,
        enable_text_splitting: Optional[bool] = None,
        gpt_cond_len: int = XTTS_DEFAULT_GPT_COND_LEN,
        gpt_cond_chunk_len: int = XTTS_DEFAULT_GPT_COND_CHUNK_LEN,
        max_ref_len: int = XTTS_DEFAULT_MAX_REF_LEN,
        sound_norm_refs: Optional[bool] = None,
    ) -> bytes:
        import soundfile as sf

        self._ensure_model()
        t0 = time.perf_counter()

        requested_language = (language or "fr").strip().lower()
        language = self._normalize_xtts_language(requested_language, text)
        if language != requested_language:
            print(f"[XTTS] unsupported language '{requested_language}' -> fallback '{language}'")
        if not text or not text.strip():
            raise ValueError("text is required")
        text = self._normalize_emotive_text(text, language)
        laugh_mode = bool(re.search(r"\b(?:ha+|haha+|hahaha+|はは|ふふ)\b", text, flags=re.IGNORECASE))

        # Clamp speed to sane range.
        try:
            speed = float(speed)
        except Exception:
            speed = 1.0
        speed = max(0.5, min(2.0, speed))

        # XTTS decoding parameters
        try:
            temperature = float(temperature)
        except Exception:
            temperature = 0.7
        temperature = max(0.01, min(2.0, temperature))
        try:
            top_k = int(top_k)
        except Exception:
            top_k = XTTS_DEFAULT_TOP_K
        top_k = max(1, min(200, top_k))
        try:
            top_p = float(top_p)
        except Exception:
            top_p = XTTS_DEFAULT_TOP_P
        top_p = max(0.1, min(1.0, top_p))
        try:
            repetition_penalty = float(repetition_penalty)
        except Exception:
            repetition_penalty = XTTS_DEFAULT_REPETITION_PENALTY
        repetition_penalty = max(1.0, min(10.0, repetition_penalty))
        try:
            length_penalty = float(length_penalty)
        except Exception:
            length_penalty = XTTS_DEFAULT_LENGTH_PENALTY
        length_penalty = max(0.1, min(5.0, length_penalty))
        if enable_text_splitting is None:
            enable_text_splitting = XTTS_DEFAULT_ENABLE_TEXT_SPLITTING
        enable_text_splitting = self._to_bool(enable_text_splitting, XTTS_DEFAULT_ENABLE_TEXT_SPLITTING)
        try:
            gpt_cond_len = int(gpt_cond_len)
        except Exception:
            gpt_cond_len = XTTS_DEFAULT_GPT_COND_LEN
        gpt_cond_len = max(1, min(30, gpt_cond_len))
        try:
            gpt_cond_chunk_len = int(gpt_cond_chunk_len)
        except Exception:
            gpt_cond_chunk_len = XTTS_DEFAULT_GPT_COND_CHUNK_LEN
        gpt_cond_chunk_len = max(1, min(10, gpt_cond_chunk_len))
        try:
            max_ref_len = int(max_ref_len)
        except Exception:
            max_ref_len = XTTS_DEFAULT_MAX_REF_LEN
        max_ref_len = max(3, min(20, max_ref_len))
        if sound_norm_refs is None:
            sound_norm_refs = XTTS_DEFAULT_SOUND_NORM_REFS
        sound_norm_refs = self._to_bool(sound_norm_refs, XTTS_DEFAULT_SOUND_NORM_REFS)
        # Keep short emotive utterances unsplit to preserve style/intonation.
        if laugh_mode and len(text) < 180:
            enable_text_splitting = False
        force_split_limit = XTTS_FORCE_SPLIT_CHAR_LIMITS.get(language)
        if force_split_limit and len(text) > force_split_limit:
            if not enable_text_splitting:
                print(
                    f"[XTTS] force enable text splitting lang={language} "
                    f"chars={len(text)} limit={force_split_limit}"
                )
            enable_text_splitting = True

        suffix = Path(speaker_filename or "speaker.wav").suffix or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as spk:
            spk.write(speaker_wav_bytes)
            speaker_path = spk.name
        prepared_speaker_path = speaker_path
        if XTTS_REF_CLEAN_ENABLED:
            prepared_speaker_path = self._prepare_reference_audio(speaker_path)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as out:
            out_path = out.name

        try:
            used_fast_path = False
            cache_status = "disabled"
            if XTTS_CONDITIONING_CACHE_ENABLED:
                ok_fast, cache_status = self._xtts_infer_with_cached_conditioning(
                    text=text,
                    language=language,
                    speaker_path=prepared_speaker_path,
                    out_path=out_path,
                    speed=speed,
                    temperature=temperature,
                    top_k=top_k,
                    top_p=top_p,
                    repetition_penalty=repetition_penalty,
                    length_penalty=length_penalty,
                    enable_text_splitting=enable_text_splitting,
                    gpt_cond_len=gpt_cond_len,
                    gpt_cond_chunk_len=gpt_cond_chunk_len,
                    max_ref_len=max_ref_len,
                    sound_norm_refs=sound_norm_refs,
                )
                used_fast_path = bool(ok_fast)

            if not used_fast_path:
                self.tts.tts_to_file(
                    text=text,
                    speaker_wav=prepared_speaker_path,
                    language=language,
                    file_path=out_path,
                    speed=speed,
                    temperature=temperature,
                    top_k=top_k,
                    top_p=top_p,
                    repetition_penalty=repetition_penalty,
                    length_penalty=length_penalty,
                    enable_text_splitting=enable_text_splitting,
                    gpt_cond_len=gpt_cond_len,
                    gpt_cond_chunk_len=gpt_cond_chunk_len,
                    max_ref_len=max_ref_len,
                    sound_norm_refs=sound_norm_refs,
                )
                if cache_status.startswith("fallback_error:"):
                    print(f"[XTTS] conditioning_cache fallback -> tts_to_file ({cache_status})")
            mastered_path = out_path
            if XTTS_MASTERING_ENABLED:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as mastered_tmp:
                    candidate_mastered = mastered_tmp.name
                if self._master_with_ffmpeg(out_path, candidate_mastered, laugh_mode=laugh_mode):
                    mastered_path = candidate_mastered
                else:
                    try:
                        os.remove(candidate_mastered)
                    except Exception:
                        pass

            audio, sr = sf.read(mastered_path, dtype="float32")
            audio = self._postprocess_audio(audio, int(sr), laugh_mode=laugh_mode)
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
                f"rtf={rtf:.3f} lang={language} chars={len(text)} speed={speed:.2f} "
                f"temp={temperature:.2f} top_k={top_k} top_p={top_p:.2f} split={int(enable_text_splitting)} "
                f"gpt_cond_len={gpt_cond_len} chunk={gpt_cond_chunk_len} max_ref={max_ref_len} "
                f"norm_ref={int(sound_norm_refs)} cond_cache={cache_status}"
            )
            return out_bytes
        finally:
            for p in (speaker_path, out_path):
                try:
                    os.remove(p)
                except Exception:
                    pass
            try:
                if prepared_speaker_path not in {None, "", speaker_path}:
                    os.remove(prepared_speaker_path)
            except Exception:
                pass
            try:
                if "mastered_path" in locals() and mastered_path not in {None, "", out_path}:
                    os.remove(mastered_path)
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
    top_k: int = Form(default=XTTS_DEFAULT_TOP_K),
    top_p: float = Form(default=XTTS_DEFAULT_TOP_P),
    repetition_penalty: float = Form(default=XTTS_DEFAULT_REPETITION_PENALTY),
    length_penalty: float = Form(default=XTTS_DEFAULT_LENGTH_PENALTY),
    enable_text_splitting: Optional[bool] = Form(default=None),
    gpt_cond_len: int = Form(default=XTTS_DEFAULT_GPT_COND_LEN),
    gpt_cond_chunk_len: int = Form(default=XTTS_DEFAULT_GPT_COND_CHUNK_LEN),
    max_ref_len: int = Form(default=XTTS_DEFAULT_MAX_REF_LEN),
    sound_norm_refs: Optional[bool] = Form(default=None),
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
            top_k=top_k,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            length_penalty=length_penalty,
            enable_text_splitting=enable_text_splitting,
            gpt_cond_len=gpt_cond_len,
            gpt_cond_chunk_len=gpt_cond_chunk_len,
            max_ref_len=max_ref_len,
            sound_norm_refs=sound_norm_refs,
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

