from __future__ import annotations

import os
import socket
import sys
import tomllib
from pathlib import Path

from openai import OpenAI


def load_api_key() -> str | None:
    key = os.getenv("MOONSHOT_API_KEY")
    if key:
        return key

    secrets_file = Path(__file__).resolve().parent / ".streamlit" / "secrets.toml"
    if secrets_file.exists():
        data = tomllib.loads(secrets_file.read_text())
        key = data.get("MOONSHOT_API_KEY")
        if isinstance(key, str) and key.strip():
            return key.strip()
    return None


def dns_check(host: str) -> None:
    try:
        ip = socket.gethostbyname(host)
        print(f"[DNS OK] {host} -> {ip}")
    except Exception as exc:
        print(f"[DNS FAIL] {host}: {exc}")
        raise


def main() -> int:
    host = "api.moonshot.cn"
    base_url = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1")
    model = os.getenv("MOONSHOT_MODEL", "kimi-k2.5")
    temperature = 1.0 if model.strip().lower() == "kimi-k2.5" else 0.0

    key = load_api_key()
    if not key:
        print("[CONFIG FAIL] MOONSHOT_API_KEY not found in env or .streamlit/secrets.toml")
        return 2

    print("[CONFIG OK] key found")

    try:
        dns_check(host)
    except Exception:
        return 3

    try:
        client = OpenAI(api_key=key, base_url=base_url)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Return plain text only."},
                {"role": "user", "content": "Reply with exactly: pong"},
            ],
            temperature=temperature,
            timeout=20,
        )
        text = (resp.choices[0].message.content or "").strip()
        print(f"[API OK] model={model} response={text!r}")
        return 0
    except Exception as exc:
        print(f"[API FAIL] {type(exc).__name__}: {exc}")
        return 4


if __name__ == "__main__":
    sys.exit(main())
