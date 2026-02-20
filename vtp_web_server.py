"""
=============================================================================
  KOMMZ VOICE — WEB SERVER (vtp_web_server.py)
  Backend Flask pour le site de clonage vocal (hébergé sur Render.com)
=============================================================================

ARCHITECTURE :
  Client (index.html)  →  Flask (vtp_web_server.py)  →  Supabase (DB + Storage)
                                      ↓
                              Modal.run (Whisper + XTTS v2)

ROUTES :
  AUTH         POST /login              — Connexion utilisateur
               POST /register           — Inscription (nécessite licence VCV-)
               GET  /logout             — Déconnexion
               GET  /me                 — Info utilisateur courant

  LICENCE      POST /license/voice/verify-web  — Vérification clé VCV- (avant inscription)

  PROFILS      GET  /api/profiles               — Liste des profils de l'utilisateur
               POST /api/profiles               — Sauvegarde un nouveau clone vocal
               DELETE /api/voices/delete/<id>   — Supprime un profil

  FICHIERS     POST /api/upload-reference       — Upload fichier audio de référence
               POST /api/transcribe/<file_id>   — Transcription Whisper via Modal

  GÉNÉRATION   POST /api/generate               — Génération vocale XTTS via Modal

INSTALLATION :
  pip install flask flask-session supabase python-dotenv requests gunicorn

VARIABLES D'ENVIRONNEMENT (.env) :
  SUPABASE_URL=https://xxxxxxxx.supabase.co
  SUPABASE_KEY=eyJhbGci...   (service role key — jamais côté client !)
  SUPABASE_ANON_KEY=eyJ...   (pour auth côté client si besoin)
  MODAL_WHISPER_URL=https://votre-app--whisper.modal.run
  MODAL_XTTS_URL=https://votre-app--kommz-voice-xtts.modal.run
  SECRET_KEY=une_cle_tres_longue_et_aleatoire
  VOICE_SECRET_SALT=VTP-KOMMZ-VOICE-2026-X77

=============================================================================
"""

import os
import uuid
import hashlib
import hmac
import time
import tempfile
import requests
from datetime import datetime
from functools import wraps

from flask import (
    Flask, request, jsonify, session,
    send_from_directory, render_template_string
)
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CONFIG
# =============================================================================

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024  # 64 MB max upload

# Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")  # Service role (côté serveur uniquement)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Modal endpoints
MODAL_WHISPER_URL = os.environ.get("MODAL_WHISPER_URL", "https://your-app--whisper-transcribe.modal.run")
MODAL_XTTS_URL    = os.environ.get("MODAL_XTTS_URL",    "https://your-app--kommz-voice-xtts.modal.run")

# Licence Voice
VOICE_SECRET_SALT = os.environ.get("VOICE_SECRET_SALT", "VTP-KOMMZ-VOICE-2026-X77")

# Bucket Supabase Storage pour les fichiers audio
STORAGE_BUCKET = "voice-references"


# =============================================================================
# HELPERS
# =============================================================================

def get_current_user():
    """Retourne l'utilisateur de la session ou None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    try:
        result = supabase.table("users").select("*").eq("id", user_id).single().execute()
        return result.data
    except Exception:
        return None


def login_required(f):
    """Décorateur — refuse si non connecté."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "Non authentifié"}), 401
        return f(*args, **kwargs)
    return decorated


def hash_password(password: str) -> str:
    """SHA-256 + salt fixe. En prod, préférer bcrypt."""
    salt = os.environ.get("PASSWORD_SALT", "KommzVoiceSalt2026!")
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def generate_api_key() -> str:
    """Génère une clé API unique pour l'utilisateur."""
    return f"KV-{uuid.uuid4().hex.upper()}"


# =============================================================================
# VÉRIFICATION LICENCE VCV-
# =============================================================================

def verify_vcv_key(key: str) -> dict:
    """
    Vérifie une clé VCV-TIMESTAMP-RANDOM-SIG8.
    
    Format : VCV-{timestamp_expiration}-{random4}-{sha256[:8]}
    Salt    : VOICE_SECRET_SALT
    
    Retourne : {"valid": bool, "expired": bool, "expiration_ts": int}
    """
    MASTER_KEYS = ["VTP-VOICE-ADMIN", "NICOLAS-VOICE-PRO"]
    if key in MASTER_KEYS:
        return {"valid": True, "expired": False, "expiration_ts": 9999999999}

    parts = key.split("-")
    # Format : VCV-TIMESTAMP-RANDOM-SIG8 → 4 parties
    if len(parts) != 4 or parts[0] != "VCV":
        return {"valid": False, "expired": False, "expiration_ts": 0}

    try:
        ts_str, rand, sig = parts[1], parts[2], parts[3]
        expiration_ts = int(ts_str)
    except (ValueError, IndexError):
        return {"valid": False, "expired": False, "expiration_ts": 0}

    # Vérification signature
    # Format Make.com : SHA256(timestamp + random + salt) — sans séparateur
    expected_sig = hashlib.sha256(f"{ts_str}{rand}{VOICE_SECRET_SALT}".encode()).hexdigest()[:8].upper()
    
    if not hmac.compare_digest(sig.upper(), expected_sig):
        return {"valid": False, "expired": False, "expiration_ts": 0}

    # Vérification expiration
    expired = expiration_ts < int(time.time())
    return {"valid": True, "expired": expired, "expiration_ts": expiration_ts}


# =============================================================================
# ROUTES STATIQUES — Sert index.html
# =============================================================================

@app.route("/")
def index():
    """Sert l'application principale."""
    user = get_current_user()
    # On passe le user au template Jinja si besoin
    # Pour une SPA pure, on peut retourner juste le fichier statique
    try:
        with open(os.path.join(app.static_folder or ".", "index.html"), "r", encoding="utf-8") as f:
            html = f.read()
        return html
    except FileNotFoundError:
        return "<h1>index.html introuvable dans le dossier static/</h1>", 404


# =============================================================================
# ROUTES AUTH
# =============================================================================

@app.route("/register", methods=["POST"])
def register():
    """
    Inscription.
    Body JSON : { email, password, license_key }
    
    La clé VCV- est obligatoire pour s'inscrire.
    Elle est marquée comme utilisée en Supabase après succès.
    """
    data = request.get_json() or {}
    email       = (data.get("email") or "").strip().lower()
    password    = (data.get("password") or "").strip()
    license_key = (data.get("license_key") or "").strip().upper()

    # Validations basiques
    if not email or "@" not in email:
        return jsonify({"success": False, "error": "Email invalide"}), 400
    if len(password) < 8:
        return jsonify({"success": False, "error": "Mot de passe trop court (8 caractères min)"}), 400
    if not license_key:
        return jsonify({"success": False, "error": "Clé de licence VCV- requise"}), 400

    # Vérification clé licence
    vcv_result = verify_vcv_key(license_key)
    if not vcv_result["valid"]:
        return jsonify({"success": False, "error": "Clé de licence invalide"}), 403
    if vcv_result["expired"]:
        return jsonify({"success": False, "error": "Clé de licence expirée"}), 403

    # Vérification que la clé n'est pas déjà utilisée par un autre compte
    try:
        lic_check = supabase.table("license_keys")\
            .select("*")\
            .eq("key_value", license_key)\
            .eq("product", "voice")\
            .single()\
            .execute()
        
        if lic_check.data and lic_check.data.get("is_activated") and lic_check.data.get("activated_by_email") != email:
            return jsonify({
                "success": False,
                "error": "Cette clé est déjà associée à un autre compte"
            }), 409
    except Exception:
        # La clé n'existe pas encore en base → OK pour un nouvel utilisateur
        pass

    # Vérification que l'email n'existe pas déjà
    try:
        existing = supabase.table("users").select("id").eq("email", email).execute()
        if existing.data:
            return jsonify({"success": False, "error": "Email déjà utilisé"}), 409
    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur DB: {e}"}), 500

    # Création de l'utilisateur
    new_user = {
        "id":           str(uuid.uuid4()),
        "email":        email,
        "password":     hash_password(password),
        "api_key":      generate_api_key(),
        "license_key":  license_key,
        "created_at":   datetime.utcnow().isoformat(),
    }

    try:
        result = supabase.table("users").insert(new_user).execute()
        created_user = result.data[0]
    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur création compte: {e}"}), 500

    # Marquer la clé comme activée dans license_keys
    expiration_date = datetime.utcfromtimestamp(vcv_result["expiration_ts"]).strftime("%d/%m/%Y") \
        if vcv_result["expiration_ts"] < 9999999999 else "Illimité"
    
    try:
        # Upsert (insert ou update si déjà présent)
        supabase.table("license_keys").upsert({
            "key_value":           license_key,
            "product":             "voice",
            "is_activated":        True,
            "activated_by_email":  email,
            "activated_by_user_id": created_user["id"],
            "activated_at":        datetime.utcnow().isoformat(),
            "expiration":          expiration_date,
        }).execute()
    except Exception as e:
        # Non bloquant — l'utilisateur est créé, on log juste l'erreur
        print(f"[WARN] Impossible de marquer la licence: {e}")

    # Session
    session["user_id"] = created_user["id"]
    session["email"]   = created_user["email"]

    return jsonify({
        "success":  True,
        "user_id":  created_user["id"],
        "email":    created_user["email"],
        "api_key":  created_user["api_key"],
    })


@app.route("/login", methods=["POST"])
def login():
    """
    Connexion.
    Body JSON : { email, password }
    """
    data = request.get_json() or {}
    email    = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not email or not password:
        return jsonify({"success": False, "error": "Email et mot de passe requis"}), 400

    try:
        result = supabase.table("users")\
            .select("*")\
            .eq("email", email)\
            .eq("password", hash_password(password))\
            .single()\
            .execute()
    except Exception:
        return jsonify({"success": False, "error": "Identifiants incorrects"}), 401

    if not result.data:
        return jsonify({"success": False, "error": "Identifiants incorrects"}), 401

    user = result.data
    session["user_id"] = user["id"]
    session["email"]   = user["email"]

    return jsonify({
        "success": True,
        "user_id": user["id"],
        "email":   user["email"],
        "api_key": user["api_key"],
    })


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


@app.route("/me", methods=["GET"])
@login_required
def me():
    """Retourne les infos de l'utilisateur connecté."""
    user = get_current_user()
    if not user:
        return jsonify({"error": "Session invalide"}), 401
    return jsonify({
        "id":      user["id"],
        "email":   user["email"],
        "api_key": user["api_key"],
    })


# =============================================================================
# ROUTE LICENCE — Vérification avant inscription (appelée depuis index.html)
# =============================================================================

@app.route("/license/voice/verify-web", methods=["POST"])
def verify_voice_license_web():
    """
    Vérifie une clé VCV- AVANT inscription.
    
    Body JSON : { license_key: "VCV-..." }
    
    Réponses :
      { valid: true,  already_used: false, expiration: "30/06/2027" }
      { valid: true,  already_used: true,  email: "user@email.com" }  ← proposer login
      { valid: false, error: "..." }
    """
    data = request.get_json() or {}
    raw_key = (data.get("license_key") or "").strip().upper()

    if not raw_key:
        return jsonify({"valid": False, "error": "Clé manquante"}), 400

    # Vérification cryptographique locale
    vcv_result = verify_vcv_key(raw_key)
    if not vcv_result["valid"]:
        return jsonify({"valid": False, "error": "Clé de licence invalide"}), 200
    if vcv_result["expired"]:
        return jsonify({"valid": False, "error": "Clé de licence expirée"}), 200

    expiration_date = datetime.utcfromtimestamp(vcv_result["expiration_ts"]).strftime("%d/%m/%Y") \
        if vcv_result["expiration_ts"] < 9999999999 else "Illimité"

    # Vérification en base — est-elle déjà utilisée ?
    try:
        lic = supabase.table("license_keys")\
            .select("*")\
            .eq("key_value", raw_key)\
            .eq("product", "voice")\
            .single()\
            .execute()

        if lic.data and lic.data.get("is_activated"):
            # Clé déjà activée — proposer la connexion
            return jsonify({
                "valid":        True,
                "already_used": True,
                "email":        lic.data.get("activated_by_email", ""),
                "expiration":   lic.data.get("expiration", expiration_date),
            })
    except Exception:
        pass  # Pas encore en base → nouvelle clé

    return jsonify({
        "valid":        True,
        "already_used": False,
        "expiration":   expiration_date,
    })


# =============================================================================
# ROUTES PROFILS VOCAUX
# =============================================================================

@app.route("/api/profiles", methods=["GET"])
@login_required
def get_profiles():
    """Retourne tous les profils vocaux de l'utilisateur connecté."""
    user_id = session["user_id"]
    try:
        result = supabase.table("voice_profiles")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()
        return jsonify({"success": True, "profiles": result.data or []})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/profiles", methods=["POST"])
@login_required
def save_profile():
    """
    Sauvegarde un nouveau profil vocal en Supabase.
    
    Body JSON :
    {
      file_id:        "uuid",          ← ID du fichier uploadé via /api/upload-reference
      name:           "Narrateur Pro",
      reference_text: "Transcription Whisper...",
      description:    "...",
      tags:           "Profond, Masculin, Narration",
      visibility:     "public" | "private"
    }
    """
    data    = request.get_json() or {}
    user_id = session["user_id"]

    file_id        = data.get("file_id")
    name           = (data.get("name") or "").strip()
    reference_text = (data.get("reference_text") or "").strip()
    description    = data.get("description", "")
    tags           = data.get("tags", "")
    visibility     = data.get("visibility", "public")
    language       = data.get("language", "fr")

    if not name:
        return jsonify({"success": False, "error": "Nom requis"}), 400
    if not reference_text:
        return jsonify({"success": False, "error": "Transcription Whisper requise"}), 400
    if not file_id:
        return jsonify({"success": False, "error": "Fichier audio requis"}), 400

    # Récupération de l'URL publique du fichier en Supabase Storage
    try:
        audio_url = supabase.storage.from_(STORAGE_BUCKET)\
            .get_public_url(f"{user_id}/{file_id}")
    except Exception:
        audio_url = ""

    profile_id = str(uuid.uuid4())
    new_profile = {
        "id":             profile_id,
        "user_id":        user_id,
        "name":           name,
        "reference_text": reference_text,
        "description":    description,
        "tags":           tags,
        "visibility":     visibility,
        "language":       language,
        "file_id":        file_id,
        "audio_url":      audio_url,
        "created_at":     datetime.utcnow().isoformat(),
    }

    try:
        result = supabase.table("voice_profiles").insert(new_profile).execute()
        return jsonify({"success": True, "profile": result.data[0]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/voices/delete/<profile_id>", methods=["DELETE"])
@login_required
def delete_profile(profile_id):
    """Supprime un profil vocal (uniquement si appartient à l'utilisateur)."""
    user_id = session["user_id"]
    try:
        # Vérification propriété
        check = supabase.table("voice_profiles")\
            .select("id, file_id")\
            .eq("id", profile_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        
        if not check.data:
            return jsonify({"success": False, "error": "Profil introuvable"}), 404

        # Suppression du fichier audio dans Storage
        file_id = check.data.get("file_id")
        if file_id:
            try:
                supabase.storage.from_(STORAGE_BUCKET)\
                    .remove([f"{user_id}/{file_id}"])
            except Exception:
                pass  # Non bloquant

        # Suppression du profil en base
        supabase.table("voice_profiles")\
            .delete()\
            .eq("id", profile_id)\
            .execute()

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# ROUTE UPLOAD — Fichier audio de référence
# =============================================================================

@app.route("/api/upload-reference", methods=["POST"])
@login_required
def upload_reference():
    """
    Upload un fichier audio de référence vers Supabase Storage.
    
    FormData : file (audio/*)
    
    Retourne : { success: true, file_id: "uuid", duration_estimate: 30 }
    """
    if "file" not in request.files:
        return jsonify({"success": False, "error": "Aucun fichier fourni"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"success": False, "error": "Nom de fichier manquant"}), 400

    # Vérification extension
    ext = os.path.splitext(f.filename)[1].lower()
    allowed = {".wav", ".mp3", ".ogg", ".flac", ".webm", ".m4a"}
    if ext not in allowed:
        return jsonify({"success": False, "error": f"Format non supporté: {ext}"}), 400

    user_id = session["user_id"]
    file_id = str(uuid.uuid4())
    storage_path = f"{user_id}/{file_id}{ext}"

    try:
        # Lecture du contenu
        file_bytes = f.read()
        
        # Upload vers Supabase Storage
        supabase.storage.from_(STORAGE_BUCKET).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": f.content_type or "audio/wav"}
        )

        return jsonify({
            "success":           True,
            "file_id":           f"{file_id}{ext}",  # On garde l'extension pour retrouver le fichier
            "storage_path":      storage_path,
            "original_filename": f.filename,
        })

    except Exception as e:
        return jsonify({"success": False, "error": f"Upload échoué: {e}"}), 500


# =============================================================================
# ROUTE TRANSCRIPTION — Whisper via Modal
# =============================================================================

@app.route("/api/transcribe/<file_id>", methods=["POST"])
@login_required
def transcribe_audio(file_id):
    """
    Lance la transcription Whisper d'un fichier audio via Modal.run.
    
    URL params : file_id = nom du fichier uploadé
    Body JSON  : { model: "small" | "large-v3" }
    
    Le flux :
      1. Récupère le fichier depuis Supabase Storage
      2. L'envoie au endpoint Whisper sur Modal.run
      3. Retourne la transcription
    
    Retourne : { success: true, text: "La transcription...", language: "fr" }
    """
    data        = request.get_json() or {}
    model       = data.get("model", "small")  # "small" ou "large-v3"
    user_id     = session["user_id"]

    # Validation du model
    if model not in ("small", "large", "large-v3"):
        model = "small"
    if model == "large":
        model = "large-v3"

    # Récupération du fichier depuis Supabase Storage
    storage_path = f"{user_id}/{file_id}"
    try:
        file_bytes = supabase.storage.from_(STORAGE_BUCKET).download(storage_path)
    except Exception as e:
        return jsonify({"success": False, "error": f"Fichier audio introuvable: {e}"}), 404

    # Envoi vers Modal Whisper endpoint
    try:
        whisper_response = requests.post(
            f"{MODAL_WHISPER_URL}/transcribe",
            files={"audio": (file_id, file_bytes, "audio/wav")},
            data={"model": model},
            timeout=120  # Whisper peut prendre jusqu'à 2 min sur large-v3
        )
        
        if not whisper_response.ok:
            return jsonify({
                "success": False,
                "error":   f"Erreur Modal Whisper (HTTP {whisper_response.status_code})"
            }), 502

        result = whisper_response.json()
        text = result.get("text") or result.get("transcript") or ""

        if not text:
            return jsonify({"success": False, "error": "Transcription vide"}), 422

        return jsonify({
            "success":  True,
            "text":     text.strip(),
            "language": result.get("language", "fr"),
            "model":    model,
        })

    except requests.Timeout:
        return jsonify({"success": False, "error": "Timeout — Whisper a pris trop de temps. Essayez le modèle Small."}), 504
    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur transcription: {e}"}), 500


# =============================================================================
# ROUTE GÉNÉRATION VOCALE — XTTS v2 via Modal
# =============================================================================

@app.route("/api/generate", methods=["POST"])
@login_required
def generate_voice():
    """
    Génère un fichier audio via XTTS v2 sur Modal.run.
    
    Body JSON :
    {
      text:       "Le texte à synthétiser",
      profile_id: "uuid",          ← ID du profil vocal Supabase
      language:   "fr",
      speed:      1.0,
      temperature: 0.7
    }
    
    Retourne : { success: true, audio_url: "https://..." } ou stream audio
    
    Note : Pour de grosses demandes, préférer un système de job async.
           Pour l'instant, on attend la réponse Modal directement.
    """
    data       = request.get_json() or {}
    user_id    = session["user_id"]
    text       = (data.get("text") or "").strip()
    profile_id = data.get("profile_id")
    language   = data.get("language", "fr")
    speed      = float(data.get("speed", 1.0))
    temperature = float(data.get("temperature", 0.7))

    if not text:
        return jsonify({"success": False, "error": "Texte requis"}), 400
    if len(text) > 5000:
        return jsonify({"success": False, "error": "Texte trop long (max 5000 caractères)"}), 400

    # Récupération du profil vocal
    if not profile_id:
        return jsonify({"success": False, "error": "profile_id requis"}), 400

    try:
        profile_result = supabase.table("voice_profiles")\
            .select("*")\
            .eq("id", profile_id)\
            .single()\
            .execute()
        profile = profile_result.data
    except Exception:
        return jsonify({"success": False, "error": "Profil vocal introuvable"}), 404

    # Téléchargement du fichier audio de référence
    file_id      = profile.get("file_id", "")
    storage_path = f"{profile['user_id']}/{file_id}"

    try:
        reference_audio = supabase.storage.from_(STORAGE_BUCKET).download(storage_path)
    except Exception as e:
        return jsonify({"success": False, "error": f"Audio de référence introuvable: {e}"}), 404

    # Envoi vers Modal XTTS
    try:
        xtts_response = requests.post(
            f"{MODAL_XTTS_URL}/clone",
            files={"speaker_wav": (file_id, reference_audio, "audio/wav")},
            data={
                "text":            text,
                "reference_text":  profile.get("reference_text", ""),
                "language":        language,
                "speed":           str(speed),
                "temperature":     str(temperature),
            },
            timeout=300  # XTTS peut prendre jusqu'à 5 min
        )

        if not xtts_response.ok:
            err = ""
            try:
                err = xtts_response.json().get("error", "")
            except Exception:
                pass
            return jsonify({
                "success": False,
                "error":   f"Erreur Modal XTTS (HTTP {xtts_response.status_code}): {err}"
            }), 502

        # L'endpoint Modal retourne directement le fichier WAV
        audio_bytes = xtts_response.content
        
        # Upload du résultat dans Supabase Storage pour accès ultérieur
        result_path = f"generated/{user_id}/{uuid.uuid4()}.wav"
        try:
            supabase.storage.from_(STORAGE_BUCKET).upload(
                path=result_path,
                file=audio_bytes,
                file_options={"content-type": "audio/wav"}
            )
            audio_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(result_path)
        except Exception:
            audio_url = ""  # Non bloquant

        # Retourne le fichier directement en streaming si possible
        return jsonify({
            "success":   True,
            "audio_url": audio_url,
            "profile":   profile.get("name", ""),
        })

    except requests.Timeout:
        return jsonify({"success": False, "error": "Timeout — Synthèse trop longue. Réduisez le texte."}), 504
    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur génération: {e}"}), 500


# =============================================================================
# ROUTE API EXTERNE — Génération via clé API (pour intégrations tierces)
# =============================================================================

@app.route("/v1/synthesis", methods=["POST"])
def api_synthesis():
    """
    Endpoint API externe — authentification par clé API dans le header.
    
    Header : Authorization: Bearer KV-VOTRE_CLE_API
    Body JSON :
    {
      "text":     "Texte à synthétiser",
      "voice_id": "uuid_profil",
      "speed":    1.0,
      "language": "fr"
    }
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Clé API manquante"}), 401

    api_key = auth_header.split(" ", 1)[1].strip()

    try:
        user_result = supabase.table("users")\
            .select("*")\
            .eq("api_key", api_key)\
            .single()\
            .execute()
        api_user = user_result.data
    except Exception:
        return jsonify({"error": "Clé API invalide"}), 401

    if not api_user:
        return jsonify({"error": "Clé API invalide"}), 401

    # On simule une session pour réutiliser generate_voice()
    data       = request.get_json() or {}
    text       = (data.get("text") or "").strip()
    profile_id = data.get("voice_id")
    language   = data.get("language", "fr")
    speed      = float(data.get("speed", 1.0))
    temperature = float(data.get("temperature", 0.7))

    if not text or not profile_id:
        return jsonify({"error": "text et voice_id requis"}), 400

    # Logique identique à /api/generate (extrait pour éviter la dépendance session)
    try:
        profile_result = supabase.table("voice_profiles")\
            .select("*")\
            .eq("id", profile_id)\
            .single()\
            .execute()
        profile = profile_result.data
    except Exception:
        return jsonify({"error": "Profil vocal introuvable"}), 404

    # Vérification accès (public OU appartient à l'utilisateur API)
    if profile.get("visibility") == "private" and profile.get("user_id") != api_user["id"]:
        return jsonify({"error": "Accès refusé à ce profil privé"}), 403

    storage_path = f"{profile['user_id']}/{profile.get('file_id', '')}"
    try:
        reference_audio = supabase.storage.from_(STORAGE_BUCKET).download(storage_path)
    except Exception as e:
        return jsonify({"error": f"Audio de référence introuvable: {e}"}), 404

    try:
        xtts_response = requests.post(
            f"{MODAL_XTTS_URL}/clone",
            files={"speaker_wav": (profile.get("file_id", "ref.wav"), reference_audio, "audio/wav")},
            data={
                "text":           text,
                "reference_text": profile.get("reference_text", ""),
                "language":       language,
                "speed":          str(speed),
                "temperature":    str(temperature),
            },
            timeout=300
        )

        if not xtts_response.ok:
            return jsonify({"error": "Erreur synthèse XTTS"}), 502

        result_path = f"generated/{api_user['id']}/{uuid.uuid4()}.wav"
        supabase.storage.from_(STORAGE_BUCKET).upload(
            path=result_path,
            file=xtts_response.content,
            file_options={"content-type": "audio/wav"}
        )
        audio_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(result_path)

        return jsonify({"success": True, "audio_url": audio_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# ADMIN — Routes de gestion des clés (protégées par clé admin)
# =============================================================================

ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "admin-secret-change-this")

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("X-Admin-Secret", "")
        if not hmac.compare_digest(token, ADMIN_SECRET):
            return jsonify({"error": "Non autorisé"}), 403
        return f(*args, **kwargs)
    return decorated


@app.route("/admin/keys", methods=["GET"])
@admin_required
def admin_list_keys():
    """Liste toutes les clés de licence."""
    try:
        result = supabase.table("license_keys").select("*").order("created_at", desc=True).execute()
        return jsonify({"success": True, "keys": result.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/admin/users", methods=["GET"])
@admin_required
def admin_list_users():
    """Liste tous les utilisateurs (sans les mots de passe)."""
    try:
        result = supabase.table("users")\
            .select("id, email, api_key, license_key, created_at")\
            .order("created_at", desc=True)\
            .execute()
        return jsonify({"success": True, "users": result.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/admin/stats", methods=["GET"])
@admin_required
def admin_stats():
    """Statistiques globales."""
    try:
        users_count    = len(supabase.table("users").select("id").execute().data or [])
        profiles_count = len(supabase.table("voice_profiles").select("id").execute().data or [])
        keys_count     = len(supabase.table("license_keys").select("key_value").eq("is_activated", True).execute().data or [])
        return jsonify({
            "users":            users_count,
            "voice_profiles":   profiles_count,
            "activated_keys":   keys_count,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.route("/health", methods=["GET"])
def health():
    """Endpoint de santé pour Render.com."""
    return jsonify({
        "status":  "ok",
        "version": "1.0.0",
        "service": "Kommz Voice Web Server",
    })


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "production") == "development"
    print(f"[KOMMZ VOICE] Démarrage sur port {port} — debug={debug}")
    app.run(host="0.0.0.0", port=port, debug=debug)
