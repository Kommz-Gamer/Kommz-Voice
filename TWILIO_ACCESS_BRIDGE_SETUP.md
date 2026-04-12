# Twilio Access Bridge Setup

## Ou mettre les variables

### 1. Logiciel local Kommz Access

Dans :

- `e:\KommzAccess\.env`

Ajouter :

```env
TWILIO_CALLING_ENABLED=1
TWILIO_TOKEN_URL=https://YOUR_ACCESS_CALL_BRIDGE.onrender.com/twilio/token
TWILIO_IDENTITY=kommz-access-agent
TWILIO_PUBLIC_WEBHOOK_BASE=https://YOUR_ACCESS_CALL_BRIDGE.onrender.com
```

### 2. Backend public Twilio

Dans Render sur le service qui execute `twilio_access_bridge.py` :

```env
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_API_KEY_SID=...
TWILIO_API_KEY_SECRET=...
TWILIO_TWIML_APP_SID=...
TWILIO_DEFAULT_IDENTITY=kommz-access-agent
TWILIO_PUBLIC_BASE_URL=https://YOUR_ACCESS_CALL_BRIDGE.onrender.com
TWILIO_ALLOWED_ORIGINS=https://YOUR_ACCESS_APP_DOMAIN
# optionnel pendant le rollout si le client n'envoie pas encore Authorization
TWILIO_BRIDGE_SECRET=CHANGE_ME_TWILIO_BRIDGE_SECRET
TWILIO_TRANSCRIPTION_LANGUAGE=fr-FR
TWILIO_TRANSCRIPTION_ENGINE=google
TWILIO_TRANSCRIPTION_MODEL=telephony
TWILIO_TOKEN_TTL=3600
```

## Start command Render

```bash
gunicorn -w 2 -k gthread -t 120 -b 0.0.0.0:$PORT twilio_access_bridge:app
```

## Routes disponibles

- `GET /health`
- `GET /twilio/token`
- `POST /twilio/voice/incoming`
- `POST /twilio/voice/status`
- `POST /twilio/transcription`
- `GET /twilio/agent/events`
- `POST /twilio/agent/reset`

## Configuration Twilio

Le numero Twilio ou le TwiML App doit pointer vers :

- Voice webhook :
  - `https://YOUR_ACCESS_CALL_BRIDGE.onrender.com/twilio/voice/incoming`

## Ce que fait deja le bridge

- genere un token Twilio Voice JS pour `Kommz Access`
- route un appel entrant vers l'identite `kommz-access-agent`
- active la transcription Twilio sur la piste appelant
- expose une file d'evenements que le logiciel peut consommer

## Durcissement recommande

- definir `TWILIO_ALLOWED_ORIGINS` avec le ou les domaines web autorises
- definir `TWILIO_BRIDGE_SECRET` seulement quand le client envoie deja ce header
- definir `TWILIO_AUTH_TOKEN` pour valider les webhooks Twilio
- envoyer ce secret sur :
  - `GET /twilio/token`
  - `GET /twilio/agent/events`
  - `POST /twilio/agent/reset`

Quand `TWILIO_AUTH_TOKEN` est defini, les routes suivantes refusent les callbacks non signes :

- `POST /twilio/voice/incoming`
- `POST /twilio/voice/status`
- `POST /twilio/transcription`

Exemple avec header :

```http
Authorization: Bearer CHANGE_ME_TWILIO_BRIDGE_SECRET
```

Rollout recommande sans casser le client existant :

1. definir `TWILIO_ALLOWED_ORIGINS`
2. definir `TWILIO_AUTH_TOKEN`
3. laisser `TWILIO_BRIDGE_SECRET` vide tant que le client n'envoie pas encore le header

## Ce qu'il reste a brancher

- le client Twilio JS dans `access.html`
- la consommation de `GET /twilio/agent/events` depuis le logiciel
- la conversion des evenements `transcript` en appels vers `/calls/transcript`
