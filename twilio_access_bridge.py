import hmac
import json
import os
import threading
import time
from collections import defaultdict, deque
from functools import wraps
from urllib.parse import urlencode

from flask import Flask, Response, jsonify, request
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
from twilio.request_validator import RequestValidator
from twilio.twiml.voice_response import Dial, VoiceResponse


app = Flask(__name__)

FLASK_ENV = os.environ.get("FLASK_ENV", "production").strip().lower()
IS_PRODUCTION = FLASK_ENV == "production"
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
TWILIO_API_KEY_SID = os.environ.get("TWILIO_API_KEY_SID", "").strip()
TWILIO_API_KEY_SECRET = os.environ.get("TWILIO_API_KEY_SECRET", "").strip()
TWILIO_TWIML_APP_SID = os.environ.get("TWILIO_TWIML_APP_SID", "").strip()
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
TWILIO_DEFAULT_IDENTITY = os.environ.get("TWILIO_DEFAULT_IDENTITY", "kommz-access-agent").strip()
TWILIO_PUBLIC_BASE_URL = os.environ.get("TWILIO_PUBLIC_BASE_URL", "").strip().rstrip("/")
TWILIO_ALLOWED_ORIGINS = {
    origin.strip().rstrip("/")
    for origin in os.environ.get("TWILIO_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
}
TWILIO_BRIDGE_SECRET = os.environ.get("TWILIO_BRIDGE_SECRET", "").strip()
TWILIO_TRANSCRIPTION_LANGUAGE = os.environ.get("TWILIO_TRANSCRIPTION_LANGUAGE", "fr-FR").strip()
TWILIO_TRANSCRIPTION_ENGINE = os.environ.get("TWILIO_TRANSCRIPTION_ENGINE", "google").strip()
TWILIO_TRANSCRIPTION_MODEL = os.environ.get("TWILIO_TRANSCRIPTION_MODEL", "telephony").strip()
TWILIO_TOKEN_TTL = max(60, int(os.environ.get("TWILIO_TOKEN_TTL", "3600")))
TWILIO_EVENTS_MAX = max(100, int(os.environ.get("TWILIO_EVENTS_MAX", "500")))

EVENT_LOCK = threading.Lock()
EVENT_SEQ = defaultdict(int)
AGENT_EVENTS = defaultdict(deque)


def _request_origin() -> str:
    return (request.headers.get("Origin") or "").strip().rstrip("/")


def _origin_allowed(origin: str) -> bool:
    if not origin:
        return False
    return origin in TWILIO_ALLOWED_ORIGINS


def _provided_bridge_secret() -> str:
    auth = (request.headers.get("Authorization") or "").strip()
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return (request.headers.get("X-Bridge-Secret") or "").strip()


def bridge_auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not TWILIO_BRIDGE_SECRET:
            return f(*args, **kwargs)
        provided = _provided_bridge_secret()
        if not provided or not hmac.compare_digest(provided, TWILIO_BRIDGE_SECRET):
            return jsonify({"ok": False, "error": "Unauthorized"}), 401
        return f(*args, **kwargs)

    return decorated


def _external_request_url() -> str:
    proto = (request.headers.get("X-Forwarded-Proto") or request.scheme or "https").strip()
    host = (request.headers.get("X-Forwarded-Host") or request.host or "").strip()
    base = f"{proto}://{host}{request.path}"
    if request.query_string:
        base += "?" + request.query_string.decode("utf-8", errors="ignore")
    return base


def _twilio_request_params() -> dict:
    params = {}
    for key in request.form.keys():
        values = request.form.getlist(key)
        params[key] = values if len(values) > 1 else values[0]
    return params


def twilio_signature_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not TWILIO_AUTH_TOKEN:
            return f(*args, **kwargs)
        signature = (request.headers.get("X-Twilio-Signature") or "").strip()
        if not signature:
            return jsonify({"ok": False, "error": "Missing Twilio signature"}), 403
        validator = RequestValidator(TWILIO_AUTH_TOKEN)
        if not validator.validate(_external_request_url(), _twilio_request_params(), signature):
            return jsonify({"ok": False, "error": "Invalid Twilio signature"}), 403
        return f(*args, **kwargs)

    return decorated


def _after(resp):
    origin = _request_origin()
    if _origin_allowed(origin):
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Vary"] = "Origin"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Bridge-Secret"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp


app.after_request(_after)


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "ok": True,
            "service": "twilio-access-bridge",
            "configured": _is_configured(),
            "bridge_auth_enabled": bool(TWILIO_BRIDGE_SECRET),
            "twilio_signature_validation_enabled": bool(TWILIO_AUTH_TOKEN),
            "allowed_origins_configured": len(TWILIO_ALLOWED_ORIGINS),
            "default_identity": TWILIO_DEFAULT_IDENTITY,
        }
    )


def _is_configured():
    return all(
        [
            TWILIO_ACCOUNT_SID,
            TWILIO_API_KEY_SID,
            TWILIO_API_KEY_SECRET,
            TWILIO_TWIML_APP_SID,
            TWILIO_PUBLIC_BASE_URL,
        ]
    )


def _push_event(identity: str, event_type: str, payload: dict):
    identity = (identity or TWILIO_DEFAULT_IDENTITY).strip() or TWILIO_DEFAULT_IDENTITY
    with EVENT_LOCK:
        EVENT_SEQ[identity] += 1
        event = {
            "seq": EVENT_SEQ[identity],
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "type": event_type,
            **(payload or {}),
        }
        AGENT_EVENTS[identity].append(event)
        while len(AGENT_EVENTS[identity]) > TWILIO_EVENTS_MAX:
            AGENT_EVENTS[identity].popleft()
    return event


def _transcription_callback_url(identity: str):
    return f"{TWILIO_PUBLIC_BASE_URL}/twilio/transcription?{urlencode({'identity': identity})}"


def _status_callback_url(identity: str):
    return f"{TWILIO_PUBLIC_BASE_URL}/twilio/voice/status?{urlencode({'identity': identity})}"


@app.route("/twilio/token", methods=["GET"])
@bridge_auth_required
def twilio_token():
    if not _is_configured():
        return jsonify({"ok": False, "error": "Twilio bridge not configured"}), 500

    identity = (request.args.get("identity") or TWILIO_DEFAULT_IDENTITY).strip() or TWILIO_DEFAULT_IDENTITY
    token = AccessToken(
        TWILIO_ACCOUNT_SID,
        TWILIO_API_KEY_SID,
        TWILIO_API_KEY_SECRET,
        identity=identity,
        ttl=TWILIO_TOKEN_TTL,
    )
    voice_grant = VoiceGrant(
        outgoing_application_sid=TWILIO_TWIML_APP_SID,
        incoming_allow=True,
    )
    token.add_grant(voice_grant)
    return jsonify(
        {
            "ok": True,
            "identity": identity,
            "token": token.to_jwt().decode("utf-8"),
            "expires_in": TWILIO_TOKEN_TTL,
        }
    )


@app.route("/twilio/voice/incoming", methods=["POST"])
@twilio_signature_required
def twilio_voice_incoming():
    identity = (request.args.get("identity") or TWILIO_DEFAULT_IDENTITY).strip() or TWILIO_DEFAULT_IDENTITY
    call_sid = (request.form.get("CallSid") or "").strip()
    from_number = (request.form.get("From") or "").strip()
    to_number = (request.form.get("To") or "").strip()

    _push_event(
        identity,
        "incoming",
        {
            "call_sid": call_sid,
            "from_number": from_number,
            "to_number": to_number,
            "display_name": from_number or "Appel entrant",
        },
    )

    response = VoiceResponse()
    start = response.start()
    start.transcription(
        name=f"access-{call_sid or 'session'}",
        status_callback_url=_transcription_callback_url(identity),
        language_code=TWILIO_TRANSCRIPTION_LANGUAGE,
        track="inbound_track",
        inbound_track_label="caller",
        transcription_engine=TWILIO_TRANSCRIPTION_ENGINE,
        speech_model=TWILIO_TRANSCRIPTION_MODEL,
        partial_results=False,
        enable_automatic_punctuation=True,
    )

    dial = Dial(answer_on_bridge=True)
    dial.client(
        identity,
        status_callback=_status_callback_url(identity),
        status_callback_event="initiated ringing answered completed",
    )
    response.append(dial)
    return Response(str(response), mimetype="text/xml")


@app.route("/twilio/voice/status", methods=["POST"])
@twilio_signature_required
def twilio_voice_status():
    identity = (request.args.get("identity") or TWILIO_DEFAULT_IDENTITY).strip() or TWILIO_DEFAULT_IDENTITY
    event = {
        "call_sid": (request.form.get("CallSid") or "").strip(),
        "call_status": (request.form.get("CallStatus") or "").strip().lower(),
        "direction": (request.form.get("Direction") or "").strip().lower(),
        "from_number": (request.form.get("From") or "").strip(),
        "to_number": (request.form.get("To") or "").strip(),
    }
    _push_event(identity, "call-status", event)
    return ("", 204)


@app.route("/twilio/transcription", methods=["POST"])
@twilio_signature_required
def twilio_transcription():
    identity = (request.args.get("identity") or TWILIO_DEFAULT_IDENTITY).strip() or TWILIO_DEFAULT_IDENTITY
    transcription_event = (request.form.get("TranscriptionEvent") or "").strip().lower()
    payload = {
        "call_sid": (request.form.get("CallSid") or "").strip(),
        "track": (request.form.get("Track") or "").strip().lower(),
        "final": str(request.form.get("Final") or "").strip().lower() == "true",
        "transcription_event": transcription_event,
    }

    if transcription_event == "transcription-content":
        data_raw = request.form.get("TranscriptionData") or "{}"
        try:
            data = json.loads(data_raw)
        except Exception:
            data = {"transcript": ""}
        text = str(data.get("transcript") or "").strip()
        if text and payload["final"]:
            _push_event(
                identity,
                "transcript",
                {
                    **payload,
                    "text": text,
                    "speaker_label": "APPELANT",
                },
            )
    elif transcription_event:
        _push_event(identity, "transcription-meta", payload)

    return ("", 204)


@app.route("/twilio/agent/events", methods=["GET"])
@bridge_auth_required
def twilio_agent_events():
    identity = (request.args.get("identity") or TWILIO_DEFAULT_IDENTITY).strip() or TWILIO_DEFAULT_IDENTITY
    try:
        after_seq = int(request.args.get("after_seq") or "0")
    except Exception:
        after_seq = 0

    with EVENT_LOCK:
        events = [e for e in AGENT_EVENTS[identity] if int(e.get("seq") or 0) > after_seq]
        last_seq = EVENT_SEQ[identity]

    return jsonify({"ok": True, "identity": identity, "last_seq": last_seq, "events": events})


@app.route("/twilio/agent/reset", methods=["POST"])
@bridge_auth_required
def twilio_agent_reset():
    identity = (request.get_json(silent=True) or {}).get("identity") or TWILIO_DEFAULT_IDENTITY
    identity = identity.strip() or TWILIO_DEFAULT_IDENTITY
    with EVENT_LOCK:
        AGENT_EVENTS[identity].clear()
        EVENT_SEQ[identity] = 0
    return jsonify({"ok": True, "identity": identity})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5055"))
    app.run(host="0.0.0.0", port=port)
