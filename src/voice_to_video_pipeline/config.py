"""Configuration for the voice-to-video pipeline.

Everything configurable lives here, including model slugs and the
OpenRouter API key.
"""


import os

from dotenv import load_dotenv
from pathlib import Path


# Paths are built relative to this file, so the program works from any
# working directory.
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

# Read `.env` into environment variables.
load_dotenv(PROJECT_ROOT / ".env")

# One URL for every modality.
BASE_URL: str = "https://openrouter.ai/api/v1"

API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

# Model slugs.
STT_MODEL: str = "openai/whisper-large-v3"
TEXT_MODEL: str = "openrouter/free"
IMAGE_MODEL: str = "bytedance-seed/seedream-4.5"
TTS_MODEL: str = "mistralai/voxtral-mini-tts-2603"
TTS_VOICE: str = "en_paul_neutral"
VIDEO_MODEL: str = "google/veo-3.1"

OUTPUT_DIR: Path = PROJECT_ROOT / "output"


def require_key() -> None:
    """Exit with a clear message if the API key is missing or a
    placeholder.

    Raises
    ------
    SystemExit
        If `API_KEY` is empty or still starts with `REPLACE_ME`.
    """
    if not API_KEY or API_KEY.startswith("REPLACE_ME"):
        raise SystemExit(
            "[SystemExit - config.py] Set a real `OPENROUTER_API_KEY` "
            "in `.env` first.\n"
        )
