"""
=============================================================================
  KOMMZ VOICE — WHISPER MODAL ENDPOINT (modal_whisper.py)
  Script Python à déployer sur Modal.com pour la transcription audio.
=============================================================================

DÉPLOIEMENT :
  pip install modal
  modal deploy modal_whisper.py

UTILISATION :
  POST https://your-app--whisper-transcribe.modal.run/transcribe
  FormData: { audio: <fichier>, model: "small" | "large-v3" }

  Réponse:
  { "text": "La transcription...", "language": "fr", "duration": 12.3 }

COÛT ESTIMÉ :
  - Whisper small : ~0.0001$/sec (très rapide, ~5-15s par fichier 30s)
  - Whisper large-v3 : ~0.0003$/sec (précis, ~20-60s par fichier 30s)
  GPU : T4 (suffisant pour Whisper)

=============================================================================
"""

import modal
import io
from fastapi import UploadFile, File, Form
from fastapi.responses import JSONResponse

# =============================================================================
# IMAGE DOCKER — Installation des dépendances
# =============================================================================

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "openai-whisper",
        "torch",
        "torchaudio",
        "fastapi",
        "python-multipart",
        "ffmpeg-python",
    )
    .apt_install("ffmpeg")
)

app = modal.App("kommz-whisper", image=image)

# =============================================================================
# CLASSE WHISPER — Chargement du modèle au warm-up
# =============================================================================

@app.cls(
    gpu="T4",                    # T4 suffit pour Whisper
    container_idle_timeout=120,  # Garde le container chaud 2 minutes
    memory=4096,                 # 4GB RAM
)
class WhisperModel:
    
    @modal.enter()
    def load_model(self):
        """Chargé une seule fois au démarrage du container."""
        import whisper
        # On précharge les deux modèles pour éviter les cold starts
        # (en pratique, ne charger que celui demandé est plus économe)
        print("[WHISPER] Chargement du modèle small...")
        self.model_small = whisper.load_model("small")
        print("[WHISPER] Modèle small chargé.")
        self.model_large = None  # Lazy load pour large-v3

    @modal.method()
    def transcribe(self, audio_bytes: bytes, filename: str, model_name: str = "small") -> dict:
        """
        Transcrit un fichier audio.
        
        Args:
            audio_bytes : Contenu binaire du fichier audio
            filename    : Nom original du fichier (pour déterminer le format)
            model_name  : "small" ou "large-v3"
        
        Returns:
            dict avec text, language, duration
        """
        import whisper
        import tempfile
        import os

        # Sauvegarde temporaire du fichier audio
        suffix = os.path.splitext(filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            # Sélection du modèle
            if model_name == "large-v3":
                if self.model_large is None:
                    print("[WHISPER] Chargement modèle large-v3...")
                    self.model_large = whisper.load_model("large-v3")
                model = self.model_large
            else:
                model = self.model_small

            # Transcription
            print(f"[WHISPER] Transcription avec {model_name}...")
            result = model.transcribe(
                tmp_path,
                language=None,       # Auto-detect
                task="transcribe",
                verbose=False,
            )

            return {
                "text":     result["text"].strip(),
                "language": result.get("language", "fr"),
                "duration": round(result.get("duration", 0), 1),
            }

        finally:
            # Nettoyage fichier temporaire
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


# =============================================================================
# ENDPOINT FASTAPI — Exposition HTTP
# =============================================================================

@app.function(
    image=image,
    container_idle_timeout=120,
)
@modal.fastapi_endpoint(method="POST")
async def transcribe(
    audio: UploadFile = File(...),
    model: str = Form(default="small"),
):
    """
    Endpoint HTTP pour la transcription Whisper.
    
    FormData:
      audio : fichier audio (WAV, MP3, FLAC, etc.)
      model : "small" | "large-v3"
    """
    # Validation du modèle
    if model not in ("small", "large-v3", "large", "medium"):
        model = "small"
    if model == "large":
        model = "large-v3"

    # Lecture du fichier uploadé
    audio_bytes = await audio.read()
    if not audio_bytes:
        return JSONResponse(
            status_code=400,
            content={"error": "Fichier audio vide"}
        )

    # Appel au modèle Whisper
    try:
        whisper_instance = WhisperModel()
        result = whisper_instance.transcribe.remote(
            audio_bytes=audio_bytes,
            filename=audio.filename or "audio.wav",
            model_name=model,
        )
        return JSONResponse(content={
            "success":  True,
            "text":     result["text"],
            "language": result["language"],
            "duration": result["duration"],
            "model":    model,
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Erreur Whisper: {str(e)}"}
        )


# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.function(image=image)
@modal.fastapi_endpoint(method="GET")
async def health():
    return JSONResponse(content={"status": "ok", "service": "kommz-whisper"})


# =============================================================================
# POUR TESTER LOCALEMENT :
# modal run modal_whisper.py::transcribe --audio-path ./test.wav
# =============================================================================

if __name__ == "__main__":
    print("Déploiement : modal deploy modal_whisper.py")
    print("Test local  : modal run modal_whisper.py")
