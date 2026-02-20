"""
=============================================================================
  KOMMZ VOICE ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â WEB SERVER (vtp_web_server.py)
  Backend Flask pour le site de clonage vocal (hÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©bergÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© sur Render.com)
=============================================================================

ARCHITECTURE :
  Client (index.html)  ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢  Flask (vtp_web_server.py)  ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢  Supabase (DB + Storage)
                                      ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ
                              Modal.run (Whisper + XTTS v2)

ROUTES :
  AUTH         POST /login              ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â Connexion utilisateur
               POST /register           ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â Inscription (nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cessite licence VCV-)
               GET  /logout             ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â DÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©connexion
               GET  /me                 ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â Info utilisateur courant

  LICENCE      POST /license/voice/verify-web  ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â VÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rification clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© VCV- (avant inscription)

  PROFILS      GET  /api/profiles               ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â Liste des profils de l'utilisateur
               POST /api/profiles               ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â Sauvegarde un nouveau clone vocal
               DELETE /api/voices/delete/<id>   ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â Supprime un profil

  FICHIERS     POST /api/upload-reference       ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â Upload fichier audio de rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©fÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rence
               POST /api/transcribe/<file_id>   ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â Transcription Whisper via Modal

  GÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â°NÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â°RATION   POST /api/generate               ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â GÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ration vocale XTTS via Modal

INSTALLATION :
  pip install flask flask-session supabase python-dotenv requests gunicorn

VARIABLES D'ENVIRONNEMENT (.env) :
  SUPABASE_URL=https://YOUR_PROJECT.supabase.co
  SUPABASE_KEY=CHANGE_ME_SUPABASE_SERVICE_ROLE   (jamais cÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â´tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© client)
  SUPABASE_ANON_KEY=CHANGE_ME_SUPABASE_ANON      (optionnel)
  MODAL_WHISPER_URL=https://votre-app--whisper.modal.run
  MODAL_XTTS_URL=https://votre-app--kommz-voice-xtts.modal.run
  SECRET_KEY=CHANGE_ME_FLASK_SECRET
  VOICE_SECRET_SALT=CHANGE_ME_VOICE_SALT

=============================================================================
"""

import os
import uuid
import hashlib
import hmac
import time
import tempfile
import base64
import json as pyjson
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

FLASK_ENV = os.environ.get("FLASK_ENV", "production").lower()
IS_PRODUCTION = FLASK_ENV == "production"

# Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()

# Modal endpoints
MODAL_WHISPER_URL = os.environ.get(
    "MODAL_WHISPER_URL",
    "https://your-app--whisper-transcribe.modal.run",
).strip()
MODAL_XTTS_URL = os.environ.get(
    "MODAL_XTTS_URL",
    "https://your-app--kommz-voice-xtts.modal.run",
).strip()

# Secrets
SECRET_KEY = os.environ.get("SECRET_KEY", "").strip()
VOICE_SECRET_SALT = os.environ.get("VOICE_SECRET_SALT", "").strip()
DESKTOP_SECRET_SALT = os.environ.get("DESKTOP_SECRET_SALT", "VTP-2025-MAKE-AUTOMATION-X99").strip()
PASSWORD_SALT = os.environ.get("PASSWORD_SALT", "").strip()
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "").strip()


def _jwt_payload(token: str) -> dict:
    """Decode unverified JWT payload (best effort)."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return {}
        payload = parts[1]
        payload += "=" * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload.encode("utf-8"))
        return pyjson.loads(decoded.decode("utf-8"))
    except Exception:
        return {}


def _is_probably_anon_supabase_key(key: str) -> bool:
    payload = _jwt_payload(key)
    return payload.get("role") == "anon"


def validate_runtime_config() -> None:
    missing = []
    required = {
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_KEY": SUPABASE_KEY,
        "SECRET_KEY": SECRET_KEY,
        "VOICE_SECRET_SALT": VOICE_SECRET_SALT,
        "PASSWORD_SALT": PASSWORD_SALT,
        "ADMIN_SECRET": ADMIN_SECRET,
    }
    for name, value in required.items():
        if not value:
            missing.append(name)

    if missing and IS_PRODUCTION:
        raise RuntimeError(f"Variables manquantes en production: {', '.join(missing)}")

    if SUPABASE_KEY and _is_probably_anon_supabase_key(SUPABASE_KEY):
        msg = "SUPABASE_KEY semble ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âªtre une clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© anon. Une service_role est requise cÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â´tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© serveur."
        if IS_PRODUCTION:
            raise RuntimeError(msg)
        print(f"[WARN] {msg}")

    if IS_PRODUCTION and SECRET_KEY in {"dev-secret-change-in-production", "CHANGE_ME"}:
        raise RuntimeError("SECRET_KEY invalide en production.")
    if IS_PRODUCTION and ADMIN_SECRET in {"admin-secret-change-this", "CHANGE_ME"}:
        raise RuntimeError("ADMIN_SECRET invalide en production.")


validate_runtime_config()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = SECRET_KEY or "dev-only-secret-change-me"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024  # 64 MB max upload

# Supabase client (service role cÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â´tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© serveur uniquement)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Bucket Supabase Storage pour les fichiers audio
STORAGE_BUCKET = "voice-references"
_storage_bucket_checked = False


def ensure_storage_bucket() -> None:
    """VÃ©rifie que le bucket Storage existe, sinon le crÃ©e."""
    global _storage_bucket_checked
    if _storage_bucket_checked:
        return

    buckets = supabase.storage.list_buckets() or []
    names = set()
    for b in buckets:
        if isinstance(b, dict):
            name = b.get("name")
        else:
            name = getattr(b, "name", None)
        if name:
            names.add(str(name))

    if STORAGE_BUCKET not in names:
        created = False
        errors = []

        # Compat multi-versions supabase-py/storage
        create_attempts = [
            lambda: supabase.storage.create_bucket(STORAGE_BUCKET, {"public": True}),
            lambda: supabase.storage.create_bucket(STORAGE_BUCKET),
            lambda: supabase.storage.create_bucket({"name": STORAGE_BUCKET, "public": True}),
            lambda: supabase.storage.create_bucket({"id": STORAGE_BUCKET, "name": STORAGE_BUCKET, "public": True}),
            lambda: supabase.storage.create_bucket(name=STORAGE_BUCKET, options={"public": True}),
            lambda: supabase.storage.create_bucket(name=STORAGE_BUCKET),
        ]

        for attempt in create_attempts:
            try:
                attempt()
                created = True
                break
            except Exception as e:
                errors.append(str(e))

        if not created:
            raise RuntimeError(
                f"Impossible de creer le bucket '{STORAGE_BUCKET}'. "
                f"Erreurs: {' | '.join(errors)}"
            )

        print(f"[INFO] Bucket cree automatiquement: {STORAGE_BUCKET}")

    _storage_bucket_checked = True


try:
    ensure_storage_bucket()
except Exception as e:
    print(f"[WARN] Storage bucket check Ã©chouÃ© au dÃ©marrage: {e}")


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
    """DÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©corateur ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â refuse si non connectÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "Non authentifiÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©"}), 401
        return f(*args, **kwargs)
    return decorated


def hash_password(password: str) -> str:
    """SHA-256 + salt fixe. En prod, prÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©fÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rer bcrypt."""
    salt = PASSWORD_SALT or "dev-password-salt-change-me"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def generate_api_key() -> str:
    """GÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨re une clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© API unique pour l'utilisateur."""
    return f"KV-{uuid.uuid4().hex.upper()}"


# =============================================================================
# VÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â°RIFICATION LICENCE VCV-
# =============================================================================

def verify_vcv_key(key: str) -> dict:
    """
    VÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rifie une clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© VCV-TIMESTAMP-RANDOM-SIG8.

    Format : VCV-{timestamp_expiration}-{random4}-{sha256[:8]}
    Salt    : VOICE_SECRET_SALT

    Retourne : {"valid": bool, "expired": bool, "expiration_ts": int}
    """
    MASTER_KEYS = ["VTP-VOICE-ADMIN", "NICOLAS-VOICE-PRO"]
    if key in MASTER_KEYS:
        return {"valid": True, "expired": False, "expiration_ts": 9999999999}

    parts = key.split("-")
    # Format : VCV-TIMESTAMP-RANDOM-SIG8 ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ 4 parties
    if len(parts) != 4 or parts[0] != "VCV":
        return {"valid": False, "expired": False, "expiration_ts": 0}

    try:
        ts_str, rand, sig = parts[1], parts[2], parts[3]
        expiration_ts = int(ts_str)
    except (ValueError, IndexError):
        return {"valid": False, "expired": False, "expiration_ts": 0}

    # VÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rification signature (compatibilitÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©: ancien + nouveau format)
    sig_upper = sig.upper()
    expected_ts_rand_salt = hashlib.sha256(f"{ts_str}{rand}{VOICE_SECRET_SALT}".encode()).hexdigest()[:8].upper()
    expected_salt_ts_rand = hashlib.sha256(f"{VOICE_SECRET_SALT}{ts_str}{rand}".encode()).hexdigest()[:8].upper()

    if not (
        hmac.compare_digest(sig_upper, expected_ts_rand_salt)
        or hmac.compare_digest(sig_upper, expected_salt_ts_rand)
    ):
        return {"valid": False, "expired": False, "expiration_ts": 0}

    # VÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rification expiration
    expired = expiration_ts < int(time.time())
    return {"valid": True, "expired": expired, "expiration_ts": expiration_ts}


def verify_vtp_key(key: str) -> dict:
    """
    VÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rifie une clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© VTP desktop.
    Format : VTP-{timestamp_expiration}-{random4}-{sha256[:8]}
    """
    parts = key.split("-")
    if len(parts) != 4 or parts[0] != "VTP":
        return {"valid": False, "expired": False, "expiration_ts": 0}

    try:
        ts_str, rand, sig = parts[1], parts[2], parts[3]
        expiration_ts = int(ts_str)
    except (ValueError, IndexError):
        return {"valid": False, "expired": False, "expiration_ts": 0}

    sig_upper = sig.upper()
    expected_ts_rand_salt = hashlib.sha256(f"{ts_str}{rand}{DESKTOP_SECRET_SALT}".encode()).hexdigest()[:8].upper()
    expected_salt_ts_rand = hashlib.sha256(f"{DESKTOP_SECRET_SALT}{ts_str}{rand}".encode()).hexdigest()[:8].upper()
    if not (
        hmac.compare_digest(sig_upper, expected_ts_rand_salt)
        or hmac.compare_digest(sig_upper, expected_salt_ts_rand)
    ):
        return {"valid": False, "expired": False, "expiration_ts": 0}

    expired = expiration_ts < int(time.time())
    return {"valid": True, "expired": expired, "expiration_ts": expiration_ts}


# =============================================================================
# ROUTES STATIQUES ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â Sert index.html
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
        return render_template_string(html, user=user)
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

    La clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© VCV- est obligatoire pour s'inscrire.
    Elle est marquÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e comme utilisÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e en Supabase aprÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s succÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s.
    """
    data = request.get_json() or {}
    email       = (data.get("email") or "").strip().lower()
    password    = (data.get("password") or "").strip()
    license_key = (data.get("license_key") or "").strip().upper()

    # Validations basiques
    if not email or "@" not in email:
        return jsonify({"success": False, "error": "Email invalide"}), 400
    if len(password) < 8:
        return jsonify({"success": False, "error": "Mot de passe trop court (8 caractÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨res min)"}), 400
    if not license_key:
        return jsonify({"success": False, "error": "ClÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© de licence VCV- requise"}), 400

    # VÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rification clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© licence
    vcv_result = verify_vcv_key(license_key)
    if not vcv_result["valid"]:
        return jsonify({"success": False, "error": "ClÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© de licence invalide"}), 403
    if vcv_result["expired"]:
        return jsonify({"success": False, "error": "ClÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© de licence expirÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e"}), 403

    # VÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rification que la clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© n'est pas dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©jÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  utilisÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e par un autre compte
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
                "error": "Cette clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© est dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©jÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  associÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  un autre compte"
            }), 409
    except Exception:
        # La clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© n'existe pas encore en base ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ OK pour un nouvel utilisateur
        pass

    # VÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rification que l'email n'existe pas dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©jÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â 
    try:
        existing = supabase.table("users").select("id").eq("email", email).execute()
        if existing.data:
            return jsonify({"success": False, "error": "Email dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©jÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  utilisÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©"}), 409
    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur DB: {e}"}), 500

    # CrÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ation de l'utilisateur
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
        return jsonify({"success": False, "error": f"Erreur crÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ation compte: {e}"}), 500

    # Marquer la clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© comme activÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e dans license_keys
    expiration_date = datetime.utcfromtimestamp(vcv_result["expiration_ts"]).strftime("%d/%m/%Y") \
        if vcv_result["expiration_ts"] < 9999999999 else "IllimitÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©"

    try:
        # Upsert (insert ou update si dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©jÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  prÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©sent)
        supabase.table("license_keys").upsert({
            "key_value":           license_key,
            "product":             "voice",
            "is_activated":        True,
            "activated_by_email":  email,
            "activated_by_user_id": created_user["id"],
            "activated_at":        datetime.utcnow().isoformat(),
            "expiration":          expiration_date,
        }, on_conflict="key_value").execute()
    except Exception as e:
        # Non bloquant ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â l'utilisateur est crÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©, on log juste l'erreur
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

    # Synchroniser license_keys si l'entrÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e est manquante
    # (cas des comptes crÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©s avant que la table license_keys existait)
    license_key = user.get("license_key", "")
    if license_key:
        try:
            supabase.table("license_keys").upsert({
                "key_value":            license_key,
                "product":              "voice",
                "is_activated":         True,
                "activated_by_email":   user["email"],
                "activated_by_user_id": user["id"],
                "activated_at":         datetime.utcnow().isoformat(),
            }, on_conflict="key_value").execute()
        except Exception as sync_err:
            print(f"[WARN] Sync license_keys ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©chouÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©: {sync_err}")

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
    """Retourne les infos de l'utilisateur connectÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©."""
    user = get_current_user()
    if not user:
        return jsonify({"error": "Session invalide"}), 401
    return jsonify({
        "id":      user["id"],
        "email":   user["email"],
        "api_key": user["api_key"],
    })


# =============================================================================
# ROUTE LICENCE ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â VÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rification avant inscription (appelÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e depuis index.html)
# =============================================================================

@app.route("/license/voice/verify-web", methods=["POST"])
def verify_voice_license_web():
    """
    VÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rifie une clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© VCV- AVANT inscription.

    Body JSON : { license_key: "VCV-..." }

    RÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ponses :
      { valid: true,  already_used: false, expiration: "30/06/2027" }
      { valid: true,  already_used: true,  email: "user@email.com" }  ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â Ãƒâ€šÃ‚Â proposer login
      { valid: false, error: "..." }
    """
    data = request.get_json() or {}
    raw_key = (data.get("license_key") or "").strip().upper()

    if not raw_key:
        return jsonify({"valid": False, "error": "ClÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© manquante"}), 400

    # VÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rification cryptographique locale
    vcv_result = verify_vcv_key(raw_key)
    if not vcv_result["valid"]:
        return jsonify({"valid": False, "error": "ClÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© de licence invalide"}), 200
    if vcv_result["expired"]:
        return jsonify({"valid": False, "error": "ClÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© de licence expirÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e"}), 200

    expiration_date = datetime.utcfromtimestamp(vcv_result["expiration_ts"]).strftime("%d/%m/%Y") \
        if vcv_result["expiration_ts"] < 9999999999 else "IllimitÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©"

    # VÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rification en base ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â est-elle dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©jÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  utilisÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e ?
    try:
        lic = supabase.table("license_keys")\
            .select("*")\
            .eq("key_value", raw_key)\
            .eq("product", "voice")\
            .single()\
            .execute()

        if lic.data and lic.data.get("is_activated"):
            # ClÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©jÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  activÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â proposer la connexion
            return jsonify({
                "valid":        True,
                "already_used": True,
                "email":        lic.data.get("activated_by_email", ""),
                "expiration":   lic.data.get("expiration", expiration_date),
            })
    except Exception:
        pass  # Pas encore en base ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ nouvelle clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©

    return jsonify({
        "valid":        True,
        "already_used": False,
        "expiration":   expiration_date,
    })


def _activate_desktop_license_common(product: str):
    """
    Activation serveur pour desktop (source de vÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ritÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©).
    RÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨gle: une clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© est liÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  un seul email, mais cet email peut changer de PC.
    """
    data = request.get_json() or {}
    key = (data.get("license_key") or "").strip().upper()
    email = (data.get("email") or "").strip().lower()
    hwid = (data.get("hwid") or "").strip().upper()

    if not key or not email or "@" not in email or not hwid:
        return jsonify({"ok": False, "error": "ParamÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨tres manquants"}), 400

    if product == "voice":
        check = verify_vcv_key(key)
        expected_products = {"voice", "bundle"}
    else:
        check = verify_vtp_key(key)
        expected_products = {"gamer", "bundle"}

    if not check["valid"]:
        return jsonify({"ok": False, "error": "ClÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© invalide"}), 403
    if check["expired"]:
        return jsonify({"ok": False, "error": "ClÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© expirÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e"}), 403

    expiration_date = datetime.utcfromtimestamp(check["expiration_ts"]).strftime("%d/%m/%Y") \
        if check["expiration_ts"] < 9999999999 else "IllimitÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©"

    try:
        existing_resp = supabase.table("license_keys").select("*").eq("key_value", key).execute()
        existing = (existing_resp.data or [{}])[0]

        existing_email = (existing.get("activated_by_email") or "").strip().lower()
        if existing_email and existing_email != email:
            return jsonify({
                "ok": False,
                "error": "Cette clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© est dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©jÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  associÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  un autre utilisateur"
            }), 409

        existing_product = (existing.get("product") or "").strip().lower()
        if existing_product and existing_product not in expected_products:
            return jsonify({"ok": False, "error": "ClÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© incompatible avec ce produit"}), 409

        hwid_history_raw = (existing.get("desktop_hwid") or "").strip()
        hwids = [h.strip().upper() for h in hwid_history_raw.split(",") if h.strip()]
        if hwid not in hwids:
            hwids.append(hwid)
        desktop_hwid = ",".join(hwids)

        row = {
            "key_value": key,
            "product": existing_product or product,
            "is_activated": True,
            "activated_by_email": email,
            "desktop_hwid": desktop_hwid,
            "expiration": expiration_date,
            "activated_at": datetime.utcnow().isoformat(),
        }
        supabase.table("license_keys").upsert(row, on_conflict="key_value").execute()
        return jsonify({"ok": True, "expiration": expiration_date})
    except Exception as e:
        return jsonify({"ok": False, "error": f"Erreur DB: {e}"}), 500


@app.route("/license/desktop/activate", methods=["POST"])
def activate_desktop_gamer_license():
    return _activate_desktop_license_common("gamer")


@app.route("/license/voice/activate-desktop", methods=["POST"])
def activate_desktop_voice_license():
    return _activate_desktop_license_common("voice")


# =============================================================================
# ROUTES PROFILS VOCAUX
# =============================================================================

@app.route("/api/profiles", methods=["GET"])
@login_required
def get_profiles():
    """Retourne tous les profils vocaux de l'utilisateur connectÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©."""
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
      file_id:        "uuid",          ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â Ãƒâ€šÃ‚Â ID du fichier uploadÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© via /api/upload-reference
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

    # RÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cupÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ration de l'URL publique du fichier en Supabase Storage
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
    """Supprime un profil vocal (uniquement si appartient ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  l'utilisateur)."""
    user_id = session["user_id"]
    try:
        # VÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rification propriÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©
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
# ROUTE UPLOAD ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â Fichier audio de rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©fÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rence
# =============================================================================

@app.route("/api/upload-reference", methods=["POST"])
@login_required
def upload_reference():
    """
    Upload un fichier audio de rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©fÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rence vers Supabase Storage.

    FormData : file (audio/*)

    Retourne : { success: true, file_id: "uuid", duration_estimate: 30 }
    """
    if "file" not in request.files:
        return jsonify({"success": False, "error": "Aucun fichier fourni"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"success": False, "error": "Nom de fichier manquant"}), 400

    # VÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rification extension
    ext = os.path.splitext(f.filename)[1].lower()
    allowed = {".wav", ".mp3", ".ogg", ".flac", ".webm", ".m4a"}
    if ext not in allowed:
        return jsonify({"success": False, "error": f"Format non supportÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©: {ext}"}), 400

    user_id = session["user_id"]
    file_id = str(uuid.uuid4())
    storage_path = f"{user_id}/{file_id}{ext}"

    try:
        # Lecture du contenu
        # Auto-creation du bucket si necessaire (premier run / mauvais projet).
        ensure_storage_bucket()

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
        err = str(e)
        if "Bucket not found" in err:
            err = f"Bucket Supabase introuvable: {STORAGE_BUCKET}. Verifie SUPABASE_URL/SUPABASE_KEY (service_role)."
        return jsonify({"success": False, "error": f"Upload echoue: {err}"}), 500
# =============================================================================

@app.route("/api/transcribe/<file_id>", methods=["POST"])
@login_required
def transcribe_audio(file_id):
    """
    Lance la transcription Whisper d'un fichier audio via Modal.run.

    URL params : file_id = nom du fichier uploadÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©
    Body JSON  : { model: "small" | "large-v3" }

    Le flux :
      1. RÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cupÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨re le fichier depuis Supabase Storage
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

    # RÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cupÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ration du fichier depuis Supabase Storage
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
            timeout=120  # Whisper peut prendre jusqu'ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  2 min sur large-v3
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
        return jsonify({"success": False, "error": "Timeout ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â Whisper a pris trop de temps. Essayez le modÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨le Small."}), 504
    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur transcription: {e}"}), 500


# =============================================================================
# ROUTE GÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â°NÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â°RATION VOCALE ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â XTTS v2 via Modal
# =============================================================================

@app.route("/api/generate", methods=["POST"])
@login_required
def generate_voice():
    """
    GÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨re un fichier audio via XTTS v2 sur Modal.run.

    Body JSON :
    {
      text:       "Le texte ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  synthÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tiser",
      profile_id: "uuid",          ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â Ãƒâ€šÃ‚Â ID du profil vocal Supabase
      language:   "fr",
      speed:      1.0,
      temperature: 0.7
    }

    Retourne : { success: true, audio_url: "https://..." } ou stream audio

    Note : Pour de grosses demandes, prÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©fÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rer un systÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨me de job async.
           Pour l'instant, on attend la rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ponse Modal directement.
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
        return jsonify({"success": False, "error": "Texte trop long (max 5000 caractÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨res)"}), 400

    # RÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cupÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ration du profil vocal
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

    # TÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©chargement du fichier audio de rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©fÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rence
    file_id      = profile.get("file_id", "")
    storage_path = f"{profile['user_id']}/{file_id}"

    try:
        reference_audio = supabase.storage.from_(STORAGE_BUCKET).download(storage_path)
    except Exception as e:
        return jsonify({"success": False, "error": f"Audio de rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©fÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rence introuvable: {e}"}), 404

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
            timeout=300  # XTTS peut prendre jusqu'ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  5 min
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

        # Upload du rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©sultat dans Supabase Storage pour accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s ultÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rieur
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
        return jsonify({"success": False, "error": "Timeout ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â SynthÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨se trop longue. RÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©duisez le texte."}), 504
    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur gÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ration: {e}"}), 500


# =============================================================================
# ROUTE API EXTERNE ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â GÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ration via clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© API (pour intÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©grations tierces)
# =============================================================================

@app.route("/v1/synthesis", methods=["POST"])
def api_synthesis():
    """
    Endpoint API externe ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â authentification par clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© API dans le header.

    Header : Authorization: Bearer KV-VOTRE_CLE_API
    Body JSON :
    {
      "text":     "Texte ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  synthÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tiser",
      "voice_id": "uuid_profil",
      "speed":    1.0,
      "language": "fr"
    }
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "ClÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© API manquante"}), 401

    api_key = auth_header.split(" ", 1)[1].strip()

    try:
        user_result = supabase.table("users")\
            .select("*")\
            .eq("api_key", api_key)\
            .single()\
            .execute()
        api_user = user_result.data
    except Exception:
        return jsonify({"error": "ClÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© API invalide"}), 401

    if not api_user:
        return jsonify({"error": "ClÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© API invalide"}), 401

    # On simule une session pour rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©utiliser generate_voice()
    data       = request.get_json() or {}
    text       = (data.get("text") or "").strip()
    profile_id = data.get("voice_id")
    language   = data.get("language", "fr")
    speed      = float(data.get("speed", 1.0))
    temperature = float(data.get("temperature", 0.7))

    if not text or not profile_id:
        return jsonify({"error": "text et voice_id requis"}), 400

    # Logique identique ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  /api/generate (extrait pour ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©viter la dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©pendance session)
    try:
        profile_result = supabase.table("voice_profiles")\
            .select("*")\
            .eq("id", profile_id)\
            .single()\
            .execute()
        profile = profile_result.data
    except Exception:
        return jsonify({"error": "Profil vocal introuvable"}), 404

    # VÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rification accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s (public OU appartient ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  l'utilisateur API)
    if profile.get("visibility") == "private" and profile.get("user_id") != api_user["id"]:
        return jsonify({"error": "AccÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s refusÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  ce profil privÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©"}), 403

    storage_path = f"{profile['user_id']}/{profile.get('file_id', '')}"
    try:
        reference_audio = supabase.storage.from_(STORAGE_BUCKET).download(storage_path)
    except Exception as e:
        return jsonify({"error": f"Audio de rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©fÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rence introuvable: {e}"}), 404

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
            return jsonify({"error": "Erreur synthÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨se XTTS"}), 502

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
# ADMIN ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â Routes de gestion des clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©s (protÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©gÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es par clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© admin)
# =============================================================================

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("X-Admin-Secret", "")
        if not hmac.compare_digest(token, ADMIN_SECRET):
            return jsonify({"error": "Non autorisÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©"}), 403
        return f(*args, **kwargs)
    return decorated


@app.route("/admin/keys", methods=["GET"])
@admin_required
def admin_list_keys():
    """Liste toutes les clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©s de licence."""
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
    """Endpoint de santÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© pour Render.com."""
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
    print(f"[KOMMZ VOICE] DÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©marrage sur port {port} ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â debug={debug}")
    app.run(host="0.0.0.0", port=port, debug=debug)
