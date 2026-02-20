"""
=============================================================================
  KOMMZ VOICE Ã¢â‚¬â€ WEB SERVER (vtp_web_server.py)
  Backend Flask pour le site de clonage vocal (hÃƒÂ©bergÃƒÂ© sur Render.com)
=============================================================================

ARCHITECTURE :
  Client (index.html)  Ã¢â€ â€™  Flask (vtp_web_server.py)  Ã¢â€ â€™  Supabase (DB + Storage)
                                      Ã¢â€ â€œ
                              Modal.run (Whisper + XTTS v2)

ROUTES :
  AUTH         POST /login              Ã¢â‚¬â€ Connexion utilisateur
               POST /register           Ã¢â‚¬â€ Inscription (nÃƒÂ©cessite licence VCV-)
               GET  /logout             Ã¢â‚¬â€ DÃƒÂ©connexion
               GET  /me                 Ã¢â‚¬â€ Info utilisateur courant

  LICENCE      POST /license/voice/verify-web  Ã¢â‚¬â€ VÃƒÂ©rification clÃƒÂ© VCV- (avant inscription)

  PROFILS      GET  /api/profiles               Ã¢â‚¬â€ Liste des profils de l'utilisateur
               POST /api/profiles               Ã¢â‚¬â€ Sauvegarde un nouveau clone vocal
               DELETE /api/voices/delete/<id>   Ã¢â‚¬â€ Supprime un profil

  FICHIERS     POST /api/upload-reference       Ã¢â‚¬â€ Upload fichier audio de rÃƒÂ©fÃƒÂ©rence
               POST /api/transcribe/<file_id>   Ã¢â‚¬â€ Transcription Whisper via Modal

  GÃƒâ€°NÃƒâ€°RATION   POST /api/generate               Ã¢â‚¬â€ GÃƒÂ©nÃƒÂ©ration vocale XTTS via Modal

INSTALLATION :
  pip install flask flask-session supabase python-dotenv requests gunicorn

VARIABLES D'ENVIRONNEMENT (.env) :
  SUPABASE_URL=https://YOUR_PROJECT.supabase.co
  SUPABASE_KEY=CHANGE_ME_SUPABASE_SERVICE_ROLE   (jamais cÃƒÂ´tÃƒÂ© client)
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
        msg = "SUPABASE_KEY semble ÃƒÂªtre une clÃƒÂ© anon. Une service_role est requise cÃƒÂ´tÃƒÂ© serveur."
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

# Supabase client (service role cÃƒÂ´tÃƒÂ© serveur uniquement)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
    """DÃƒÂ©corateur Ã¢â‚¬â€ refuse si non connectÃƒÂ©."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "Non authentifiÃƒÂ©"}), 401
        return f(*args, **kwargs)
    return decorated


def hash_password(password: str) -> str:
    """SHA-256 + salt fixe. En prod, prÃƒÂ©fÃƒÂ©rer bcrypt."""
    salt = PASSWORD_SALT or "dev-password-salt-change-me"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def generate_api_key() -> str:
    """GÃƒÂ©nÃƒÂ¨re une clÃƒÂ© API unique pour l'utilisateur."""
    return f"KV-{uuid.uuid4().hex.upper()}"


# =============================================================================
# VÃƒâ€°RIFICATION LICENCE VCV-
# =============================================================================

def verify_vcv_key(key: str) -> dict:
    """
    VÃƒÂ©rifie une clÃƒÂ© VCV-TIMESTAMP-RANDOM-SIG8.

    Format : VCV-{timestamp_expiration}-{random4}-{sha256[:8]}
    Salt    : VOICE_SECRET_SALT

    Retourne : {"valid": bool, "expired": bool, "expiration_ts": int}
    """
    MASTER_KEYS = ["VTP-VOICE-ADMIN", "NICOLAS-VOICE-PRO"]
    if key in MASTER_KEYS:
        return {"valid": True, "expired": False, "expiration_ts": 9999999999}

    parts = key.split("-")
    # Format : VCV-TIMESTAMP-RANDOM-SIG8 Ã¢â€ â€™ 4 parties
    if len(parts) != 4 or parts[0] != "VCV":
        return {"valid": False, "expired": False, "expiration_ts": 0}

    try:
        ts_str, rand, sig = parts[1], parts[2], parts[3]
        expiration_ts = int(ts_str)
    except (ValueError, IndexError):
        return {"valid": False, "expired": False, "expiration_ts": 0}

    # VÃƒÂ©rification signature (compatibilitÃƒÂ©: ancien + nouveau format)
    sig_upper = sig.upper()
    expected_ts_rand_salt = hashlib.sha256(f"{ts_str}{rand}{VOICE_SECRET_SALT}".encode()).hexdigest()[:8].upper()
    expected_salt_ts_rand = hashlib.sha256(f"{VOICE_SECRET_SALT}{ts_str}{rand}".encode()).hexdigest()[:8].upper()

    if not (
        hmac.compare_digest(sig_upper, expected_ts_rand_salt)
        or hmac.compare_digest(sig_upper, expected_salt_ts_rand)
    ):
        return {"valid": False, "expired": False, "expiration_ts": 0}

    # VÃƒÂ©rification expiration
    expired = expiration_ts < int(time.time())
    return {"valid": True, "expired": expired, "expiration_ts": expiration_ts}


def verify_vtp_key(key: str) -> dict:
    """
    VÃƒÂ©rifie une clÃƒÂ© VTP desktop.
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
# ROUTES STATIQUES Ã¢â‚¬â€ Sert index.html
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

    La clÃƒÂ© VCV- est obligatoire pour s'inscrire.
    Elle est marquÃƒÂ©e comme utilisÃƒÂ©e en Supabase aprÃƒÂ¨s succÃƒÂ¨s.
    """
    data = request.get_json() or {}
    email       = (data.get("email") or "").strip().lower()
    password    = (data.get("password") or "").strip()
    license_key = (data.get("license_key") or "").strip().upper()

    # Validations basiques
    if not email or "@" not in email:
        return jsonify({"success": False, "error": "Email invalide"}), 400
    if len(password) < 8:
        return jsonify({"success": False, "error": "Mot de passe trop court (8 caractÃƒÂ¨res min)"}), 400
    if not license_key:
        return jsonify({"success": False, "error": "ClÃƒÂ© de licence VCV- requise"}), 400

    # VÃƒÂ©rification clÃƒÂ© licence
    vcv_result = verify_vcv_key(license_key)
    if not vcv_result["valid"]:
        return jsonify({"success": False, "error": "ClÃƒÂ© de licence invalide"}), 403
    if vcv_result["expired"]:
        return jsonify({"success": False, "error": "ClÃƒÂ© de licence expirÃƒÂ©e"}), 403

    # VÃƒÂ©rification que la clÃƒÂ© n'est pas dÃƒÂ©jÃƒÂ  utilisÃƒÂ©e par un autre compte
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
                "error": "Cette clÃƒÂ© est dÃƒÂ©jÃƒÂ  associÃƒÂ©e ÃƒÂ  un autre compte"
            }), 409
    except Exception:
        # La clÃƒÂ© n'existe pas encore en base Ã¢â€ â€™ OK pour un nouvel utilisateur
        pass

    # VÃƒÂ©rification que l'email n'existe pas dÃƒÂ©jÃƒÂ 
    try:
        existing = supabase.table("users").select("id").eq("email", email).execute()
        if existing.data:
            return jsonify({"success": False, "error": "Email dÃƒÂ©jÃƒÂ  utilisÃƒÂ©"}), 409
    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur DB: {e}"}), 500

    # CrÃƒÂ©ation de l'utilisateur
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
        return jsonify({"success": False, "error": f"Erreur crÃƒÂ©ation compte: {e}"}), 500

    # Marquer la clÃƒÂ© comme activÃƒÂ©e dans license_keys
    expiration_date = datetime.utcfromtimestamp(vcv_result["expiration_ts"]).strftime("%d/%m/%Y") \
        if vcv_result["expiration_ts"] < 9999999999 else "IllimitÃƒÂ©"

    try:
        # Upsert (insert ou update si dÃƒÂ©jÃƒÂ  prÃƒÂ©sent)
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
        # Non bloquant Ã¢â‚¬â€ l'utilisateur est crÃƒÂ©ÃƒÂ©, on log juste l'erreur
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

    # Synchroniser license_keys si l'entrÃƒÂ©e est manquante
    # (cas des comptes crÃƒÂ©ÃƒÂ©s avant que la table license_keys existait)
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
            print(f"[WARN] Sync license_keys ÃƒÂ©chouÃƒÂ©: {sync_err}")

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
    """Retourne les infos de l'utilisateur connectÃƒÂ©."""
    user = get_current_user()
    if not user:
        return jsonify({"error": "Session invalide"}), 401
    return jsonify({
        "id":      user["id"],
        "email":   user["email"],
        "api_key": user["api_key"],
    })


# =============================================================================
# ROUTE LICENCE Ã¢â‚¬â€ VÃƒÂ©rification avant inscription (appelÃƒÂ©e depuis index.html)
# =============================================================================

@app.route("/license/voice/verify-web", methods=["POST"])
def verify_voice_license_web():
    """
    VÃƒÂ©rifie une clÃƒÂ© VCV- AVANT inscription.

    Body JSON : { license_key: "VCV-..." }

    RÃƒÂ©ponses :
      { valid: true,  already_used: false, expiration: "30/06/2027" }
      { valid: true,  already_used: true,  email: "user@email.com" }  Ã¢â€ Â proposer login
      { valid: false, error: "..." }
    """
    data = request.get_json() or {}
    raw_key = (data.get("license_key") or "").strip().upper()

    if not raw_key:
        return jsonify({"valid": False, "error": "ClÃƒÂ© manquante"}), 400

    # VÃƒÂ©rification cryptographique locale
    vcv_result = verify_vcv_key(raw_key)
    if not vcv_result["valid"]:
        return jsonify({"valid": False, "error": "ClÃƒÂ© de licence invalide"}), 200
    if vcv_result["expired"]:
        return jsonify({"valid": False, "error": "ClÃƒÂ© de licence expirÃƒÂ©e"}), 200

    expiration_date = datetime.utcfromtimestamp(vcv_result["expiration_ts"]).strftime("%d/%m/%Y") \
        if vcv_result["expiration_ts"] < 9999999999 else "IllimitÃƒÂ©"

    # VÃƒÂ©rification en base Ã¢â‚¬â€ est-elle dÃƒÂ©jÃƒÂ  utilisÃƒÂ©e ?
    try:
        lic = supabase.table("license_keys")\
            .select("*")\
            .eq("key_value", raw_key)\
            .eq("product", "voice")\
            .single()\
            .execute()

        if lic.data and lic.data.get("is_activated"):
            # ClÃƒÂ© dÃƒÂ©jÃƒÂ  activÃƒÂ©e Ã¢â‚¬â€ proposer la connexion
            return jsonify({
                "valid":        True,
                "already_used": True,
                "email":        lic.data.get("activated_by_email", ""),
                "expiration":   lic.data.get("expiration", expiration_date),
            })
    except Exception:
        pass  # Pas encore en base Ã¢â€ â€™ nouvelle clÃƒÂ©

    return jsonify({
        "valid":        True,
        "already_used": False,
        "expiration":   expiration_date,
    })


def _activate_desktop_license_common(product: str):
    """
    Activation serveur pour desktop (source de vÃƒÂ©ritÃƒÂ©).
    RÃƒÂ¨gle: une clÃƒÂ© est liÃƒÂ©e ÃƒÂ  un seul email, mais cet email peut changer de PC.
    """
    data = request.get_json() or {}
    key = (data.get("license_key") or "").strip().upper()
    email = (data.get("email") or "").strip().lower()
    hwid = (data.get("hwid") or "").strip().upper()

    if not key or not email or "@" not in email or not hwid:
        return jsonify({"ok": False, "error": "ParamÃƒÂ¨tres manquants"}), 400

    if product == "voice":
        check = verify_vcv_key(key)
        expected_products = {"voice", "bundle"}
    else:
        check = verify_vtp_key(key)
        expected_products = {"gamer", "bundle"}

    if not check["valid"]:
        return jsonify({"ok": False, "error": "ClÃƒÂ© invalide"}), 403
    if check["expired"]:
        return jsonify({"ok": False, "error": "ClÃƒÂ© expirÃƒÂ©e"}), 403

    expiration_date = datetime.utcfromtimestamp(check["expiration_ts"]).strftime("%d/%m/%Y") \
        if check["expiration_ts"] < 9999999999 else "IllimitÃƒÂ©"

    try:
        existing_resp = supabase.table("license_keys").select("*").eq("key_value", key).execute()
        existing = (existing_resp.data or [{}])[0]

        existing_email = (existing.get("activated_by_email") or "").strip().lower()
        if existing_email and existing_email != email:
            return jsonify({
                "ok": False,
                "error": "Cette clÃƒÂ© est dÃƒÂ©jÃƒÂ  associÃƒÂ©e ÃƒÂ  un autre utilisateur"
            }), 409

        existing_product = (existing.get("product") or "").strip().lower()
        if existing_product and existing_product not in expected_products:
            return jsonify({"ok": False, "error": "ClÃƒÂ© incompatible avec ce produit"}), 409

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
    """Retourne tous les profils vocaux de l'utilisateur connectÃƒÂ©."""
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
      file_id:        "uuid",          Ã¢â€ Â ID du fichier uploadÃƒÂ© via /api/upload-reference
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

    # RÃƒÂ©cupÃƒÂ©ration de l'URL publique du fichier en Supabase Storage
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
    """Supprime un profil vocal (uniquement si appartient ÃƒÂ  l'utilisateur)."""
    user_id = session["user_id"]
    try:
        # VÃƒÂ©rification propriÃƒÂ©tÃƒÂ©
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
# ROUTE UPLOAD Ã¢â‚¬â€ Fichier audio de rÃƒÂ©fÃƒÂ©rence
# =============================================================================

@app.route("/api/upload-reference", methods=["POST"])
@login_required
def upload_reference():
    """
    Upload un fichier audio de rÃƒÂ©fÃƒÂ©rence vers Supabase Storage.

    FormData : file (audio/*)

    Retourne : { success: true, file_id: "uuid", duration_estimate: 30 }
    """
    if "file" not in request.files:
        return jsonify({"success": False, "error": "Aucun fichier fourni"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"success": False, "error": "Nom de fichier manquant"}), 400

    # VÃƒÂ©rification extension
    ext = os.path.splitext(f.filename)[1].lower()
    allowed = {".wav", ".mp3", ".ogg", ".flac", ".webm", ".m4a"}
    if ext not in allowed:
        return jsonify({"success": False, "error": f"Format non supportÃƒÂ©: {ext}"}), 400

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
        return jsonify({"success": False, "error": f"Upload ÃƒÂ©chouÃƒÂ©: {e}"}), 500


# =============================================================================
# ROUTE TRANSCRIPTION Ã¢â‚¬â€ Whisper via Modal
# =============================================================================

@app.route("/api/transcribe/<file_id>", methods=["POST"])
@login_required
def transcribe_audio(file_id):
    """
    Lance la transcription Whisper d'un fichier audio via Modal.run.

    URL params : file_id = nom du fichier uploadÃƒÂ©
    Body JSON  : { model: "small" | "large-v3" }

    Le flux :
      1. RÃƒÂ©cupÃƒÂ¨re le fichier depuis Supabase Storage
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

    # RÃƒÂ©cupÃƒÂ©ration du fichier depuis Supabase Storage
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
            timeout=120  # Whisper peut prendre jusqu'ÃƒÂ  2 min sur large-v3
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
        return jsonify({"success": False, "error": "Timeout Ã¢â‚¬â€ Whisper a pris trop de temps. Essayez le modÃƒÂ¨le Small."}), 504
    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur transcription: {e}"}), 500


# =============================================================================
# ROUTE GÃƒâ€°NÃƒâ€°RATION VOCALE Ã¢â‚¬â€ XTTS v2 via Modal
# =============================================================================

@app.route("/api/generate", methods=["POST"])
@login_required
def generate_voice():
    """
    GÃƒÂ©nÃƒÂ¨re un fichier audio via XTTS v2 sur Modal.run.

    Body JSON :
    {
      text:       "Le texte ÃƒÂ  synthÃƒÂ©tiser",
      profile_id: "uuid",          Ã¢â€ Â ID du profil vocal Supabase
      language:   "fr",
      speed:      1.0,
      temperature: 0.7
    }

    Retourne : { success: true, audio_url: "https://..." } ou stream audio

    Note : Pour de grosses demandes, prÃƒÂ©fÃƒÂ©rer un systÃƒÂ¨me de job async.
           Pour l'instant, on attend la rÃƒÂ©ponse Modal directement.
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
        return jsonify({"success": False, "error": "Texte trop long (max 5000 caractÃƒÂ¨res)"}), 400

    # RÃƒÂ©cupÃƒÂ©ration du profil vocal
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

    # TÃƒÂ©lÃƒÂ©chargement du fichier audio de rÃƒÂ©fÃƒÂ©rence
    file_id      = profile.get("file_id", "")
    storage_path = f"{profile['user_id']}/{file_id}"

    try:
        reference_audio = supabase.storage.from_(STORAGE_BUCKET).download(storage_path)
    except Exception as e:
        return jsonify({"success": False, "error": f"Audio de rÃƒÂ©fÃƒÂ©rence introuvable: {e}"}), 404

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
            timeout=300  # XTTS peut prendre jusqu'ÃƒÂ  5 min
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

        # Upload du rÃƒÂ©sultat dans Supabase Storage pour accÃƒÂ¨s ultÃƒÂ©rieur
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
        return jsonify({"success": False, "error": "Timeout Ã¢â‚¬â€ SynthÃƒÂ¨se trop longue. RÃƒÂ©duisez le texte."}), 504
    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur gÃƒÂ©nÃƒÂ©ration: {e}"}), 500


# =============================================================================
# ROUTE API EXTERNE Ã¢â‚¬â€ GÃƒÂ©nÃƒÂ©ration via clÃƒÂ© API (pour intÃƒÂ©grations tierces)
# =============================================================================

@app.route("/v1/synthesis", methods=["POST"])
def api_synthesis():
    """
    Endpoint API externe Ã¢â‚¬â€ authentification par clÃƒÂ© API dans le header.

    Header : Authorization: Bearer KV-VOTRE_CLE_API
    Body JSON :
    {
      "text":     "Texte ÃƒÂ  synthÃƒÂ©tiser",
      "voice_id": "uuid_profil",
      "speed":    1.0,
      "language": "fr"
    }
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "ClÃƒÂ© API manquante"}), 401

    api_key = auth_header.split(" ", 1)[1].strip()

    try:
        user_result = supabase.table("users")\
            .select("*")\
            .eq("api_key", api_key)\
            .single()\
            .execute()
        api_user = user_result.data
    except Exception:
        return jsonify({"error": "ClÃƒÂ© API invalide"}), 401

    if not api_user:
        return jsonify({"error": "ClÃƒÂ© API invalide"}), 401

    # On simule une session pour rÃƒÂ©utiliser generate_voice()
    data       = request.get_json() or {}
    text       = (data.get("text") or "").strip()
    profile_id = data.get("voice_id")
    language   = data.get("language", "fr")
    speed      = float(data.get("speed", 1.0))
    temperature = float(data.get("temperature", 0.7))

    if not text or not profile_id:
        return jsonify({"error": "text et voice_id requis"}), 400

    # Logique identique ÃƒÂ  /api/generate (extrait pour ÃƒÂ©viter la dÃƒÂ©pendance session)
    try:
        profile_result = supabase.table("voice_profiles")\
            .select("*")\
            .eq("id", profile_id)\
            .single()\
            .execute()
        profile = profile_result.data
    except Exception:
        return jsonify({"error": "Profil vocal introuvable"}), 404

    # VÃƒÂ©rification accÃƒÂ¨s (public OU appartient ÃƒÂ  l'utilisateur API)
    if profile.get("visibility") == "private" and profile.get("user_id") != api_user["id"]:
        return jsonify({"error": "AccÃƒÂ¨s refusÃƒÂ© ÃƒÂ  ce profil privÃƒÂ©"}), 403

    storage_path = f"{profile['user_id']}/{profile.get('file_id', '')}"
    try:
        reference_audio = supabase.storage.from_(STORAGE_BUCKET).download(storage_path)
    except Exception as e:
        return jsonify({"error": f"Audio de rÃƒÂ©fÃƒÂ©rence introuvable: {e}"}), 404

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
            return jsonify({"error": "Erreur synthÃƒÂ¨se XTTS"}), 502

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
# ADMIN Ã¢â‚¬â€ Routes de gestion des clÃƒÂ©s (protÃƒÂ©gÃƒÂ©es par clÃƒÂ© admin)
# =============================================================================

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("X-Admin-Secret", "")
        if not hmac.compare_digest(token, ADMIN_SECRET):
            return jsonify({"error": "Non autorisÃƒÂ©"}), 403
        return f(*args, **kwargs)
    return decorated


@app.route("/admin/keys", methods=["GET"])
@admin_required
def admin_list_keys():
    """Liste toutes les clÃƒÂ©s de licence."""
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
    """Endpoint de santÃƒÂ© pour Render.com."""
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
    print(f"[KOMMZ VOICE] DÃƒÂ©marrage sur port {port} Ã¢â‚¬â€ debug={debug}")
    app.run(host="0.0.0.0", port=port, debug=debug)
