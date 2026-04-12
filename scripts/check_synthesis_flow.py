import argparse
import json
import os
import sys
from typing import Any

import requests


def _print(title: str, payload: Any) -> None:
    print(f"\n=== {title} ===")
    if isinstance(payload, (dict, list)):
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Kommz Voice synthesis flow against deployed backend."
    )
    parser.add_argument("--base-url", default=os.environ.get("KOMMZ_BASE_URL", "https://kommzvoice.onrender.com"))
    parser.add_argument("--api-key", default=os.environ.get("KOMMZ_API_KEY", ""))
    parser.add_argument("--voice-id", default=os.environ.get("KOMMZ_VOICE_ID", ""))
    parser.add_argument("--text", default=os.environ.get("KOMMZ_TEXT", "Test synthèse Kommz Voice."))
    parser.add_argument("--language", default=os.environ.get("KOMMZ_LANG", "fr"))
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    health_url = f"{base}/health"
    synth_url = f"{base}/v1/synthesis"

    try:
        hr = requests.get(health_url, timeout=args.timeout)
        _print("health", {"url": health_url, "status": hr.status_code, "body": hr.json()})
    except Exception as exc:
        _print("health_error", str(exc))
        return 2

    if not args.api_key or not args.voice_id:
        _print(
            "missing_credentials",
            "Set KOMMZ_API_KEY and KOMMZ_VOICE_ID (or pass --api-key / --voice-id) to run synthesis validation.",
        )
        return 1

    payload = {
        "text": args.text,
        "voice_id": args.voice_id,
        "language": args.language,
        "speed": 1.0,
        "temperature": 0.7,
    }
    headers = {
        "Authorization": f"Bearer {args.api_key}",
        "Content-Type": "application/json",
    }

    try:
        sr = requests.post(synth_url, headers=headers, json=payload, timeout=max(args.timeout, 60))
        body: Any
        try:
            body = sr.json()
        except Exception:
            body = sr.text[:600]
        _print("synthesis", {"url": synth_url, "status": sr.status_code, "body": body})
    except Exception as exc:
        _print("synthesis_error", str(exc))
        return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
