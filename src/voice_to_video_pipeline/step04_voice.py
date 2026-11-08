"""Step 4: generate the voiceover with text-to-speech."""


from pathlib import Path
from typing import Any

from . import config
from .client import request


def make_voiceover(
    narration: str,
    out_dir: Path,
) -> Path:
    """Convert narration text to an MP3 file.

    Parameters
    ----------
    narration : str
        Text to be spoken.
    out_dir : pathlib.Path
        Folder to save `voiceover.mp3` into.

    Returns
    -------
    pathlib.Path
        Path of the saved MP3.

    Raises
    ------
    RuntimeError
        If the API returns JSON (an error) instead of audio.
    """
    payload: dict[str, Any] = {
        "model": config.TTS_MODEL,
        "input": narration,
        "voice": config.TTS_VOICE,
        "response_format": "mp3",
    }
    resp = request(
        method="POST",
        url="/audio/speech",
        json=payload,
        timeout=180,
    )
    if "json" in resp.headers.get("Content-Type", ""):
        raise RuntimeError(
            f"[RuntimeError - step04_voice.py] TTS returned JSON, not "
            f"audio: {resp.text[:300]}\n"
        )
    path: Path = out_dir / "voiceover.mp3"
    path.write_bytes(data=resp.content)
    return path
