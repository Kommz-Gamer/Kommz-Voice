#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path


def sanitize_text(value: str) -> str:
    value = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "admin@example.com", value)
    value = re.sub(r"https://buy\.stripe\.com/[A-Za-z0-9]+", "https://buy.stripe.com/REDACTED", value)
    value = re.sub(r"\b\d{6,}\b", "REDACTED_ID", value)
    return value


def sanitize_obj(obj):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in {"account", "__IMTCONN__", "__IMTHOOK__"}:
                out[k] = "REDACTED_CONNECTION"
                continue
            out[k] = sanitize_obj(v)
        return out
    if isinstance(obj, list):
        return [sanitize_obj(v) for v in obj]
    if isinstance(obj, str):
        return sanitize_text(obj)
    return obj


def main():
    if len(sys.argv) != 3:
        print("Usage: sanitize-make-blueprint.py <input.json> <output.json>")
        sys.exit(1)

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    data = json.loads(src.read_text(encoding="utf-8"))
    sanitized = sanitize_obj(data)
    dst.write_text(json.dumps(sanitized, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Sanitized blueprint written to: {dst}")


if __name__ == "__main__":
    main()
