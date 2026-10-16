import json
import os
from pathlib import Path

APP_NAME = "ORPHE - GEST"
AI_NAME = "Orphéric IA"
CREDIT = "Orphéric Benoît Tech"
LLM_MODEL = "claude-sonnet-5-5"

APP_DIR = Path.home() / ".orphe_gest"
TRASH_DIR = APP_DIR / "corbeille"
TRASH_INDEX = APP_DIR / "corbeille.json"
TRASH_TOKEN = "::corbeille::"


def load_config():
    try:
        with open(APP_DIR / "config.json", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_config(data):
    APP_DIR.mkdir(parents=True, exist_ok=True)
    with open(APP_DIR / "config.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def get_api_key():
    return os.environ.get("ANTHROPIC_API_KEY", "").strip() or str(load_config().get("anthropic_api_key", "")).strip()


def set_api_key(key):
    cfg = load_config()
    if key.strip():
        cfg["anthropic_api_key"] = key.strip()
    else:
        cfg.pop("anthropic_api_key", None)
    save_config(cfg)


def get_model():
    return str(load_config().get("model") or LLM_MODEL)
