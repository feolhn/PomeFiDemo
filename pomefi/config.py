from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOTENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(DOTENV_PATH)

DEFAULT_KIMI_BASE_URL = "https://api.moonshot.cn/v1"
DEFAULT_KIMI_MODEL = "kimi-k2.5"
DEFAULT_KIMI_TEMPERATURE = 1.0
PROBE_REQUIRED_ENV_KEYS = (
    "KIMI_BASE_URL",
    "KIMI_MODEL",
    "KIMI_TEMPERATURE",
    "KIMI_STREAM",
    "DEBUG",
    "KIMI_API_KEY",
)


def env_bool(key: str, default: bool = False) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_str(key: str, default: str = "") -> str:
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip()


@dataclass(frozen=True)
class KimiConfig:
    api_key: str
    base_url: str
    model: str
    temperature: float
    stream: bool
    debug: bool


def resolve_kimi_config() -> KimiConfig:
    return KimiConfig(
        api_key=env_str("KIMI_API_KEY"),
        base_url=env_str("KIMI_BASE_URL", DEFAULT_KIMI_BASE_URL).rstrip("/"),
        model=env_str("KIMI_MODEL", DEFAULT_KIMI_MODEL),
        temperature=float(env_str("KIMI_TEMPERATURE", str(DEFAULT_KIMI_TEMPERATURE))),
        stream=env_bool("KIMI_STREAM", False),
        debug=env_bool("DEBUG", False),
    )


def validate_probe_env_or_raise() -> KimiConfig:
    missing = [key for key in PROBE_REQUIRED_ENV_KEYS if env_str(key) == ""]
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")

    config = resolve_kimi_config()
    if config.stream:
        raise RuntimeError("当前探针仅支持 KIMI_STREAM=0。")
    if config.model == "kimi-k2.5" and config.temperature != 1.0:
        raise RuntimeError("KIMI_MODEL=kimi-k2.5 时，KIMI_TEMPERATURE 必须为 1.0。")
    return config


def print_probe_env_summary(config: KimiConfig) -> None:
    print(f"[ENV] KIMI_BASE_URL={config.base_url}")
    print(f"[ENV] KIMI_MODEL={config.model}")
    print(f"[ENV] KIMI_TEMPERATURE={config.temperature}")
    print(f"[ENV] KIMI_STREAM={1 if config.stream else 0}")
    print(f"[ENV] DEBUG={1 if config.debug else 0}")
    print("[ENV] KIMI_API_KEY=SET")
