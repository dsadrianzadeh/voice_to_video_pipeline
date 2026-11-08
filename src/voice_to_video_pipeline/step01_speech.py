"""Step 1: record the microphone and transcribe speech to text."""


import base64
import io
import numpy as np
import queue
import sounddevice as sd
import soundfile as sf

from . import config
from .client import add_cost, post_json
from typing import Any


SAMPLE_RATE: int = 16000  # 16 kHz mono


def record_until_enter() -> np.ndarray:
    """Record from the default microphone between two Enter presses.

    Returns
    -------
    numpy.ndarray
        Float32 audio samples, shape `(n_samples, 1)`.

    Raises
    ------
    RuntimeError
        If no audio was captured.
    """
    q: queue.Queue[np.ndarray] = queue.Queue()

    def callback(
        indata: np.ndarray,
        frames: int,
        time: Any,
        status: sd.CallbackFlags,
    ) -> None:
        """Queue a copy of each audio block from the microphone."""
        q.put(indata.copy())  # The mic reuses its buffer, so copy it.

    input(
        "[input - step01_speech.py] Press Enter to START recording.\n"
    )
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        callback=callback,
    ):
        print("[INFO - step01_speech.py] Recording...\n")
        input("[input - step01_speech.py] Press Enter to STOP.\n")

    chunks: list[np.ndarray] = []
    while not q.empty():
        chunks.append(q.get())
    if not chunks:
        raise RuntimeError(
            "[RuntimeError - step01_speech.py] No audio captured. "
            "Check your microphone.\n"
        )
    return np.concatenate(chunks)


def to_wav_bytes(audio: np.ndarray) -> bytes:
    """Encode audio samples as 16-bit PCM WAV bytes.

    Parameters
    ----------
    audio : numpy.ndarray
        Audio samples recorded at `SAMPLE_RATE`.

    Returns
    -------
    bytes
        A complete WAV file in memory.
    """
    buf: io.BytesIO = io.BytesIO()
    sf.write(
        buf,
        audio,
        SAMPLE_RATE,
        format="WAV",
        subtype="PCM_16",
    )
    return buf.getvalue()


def transcribe(wav_bytes: bytes) -> str:
    """Transcribe WAV audio with the configured speech-to-text model.

    Parameters
    ----------
    wav_bytes : bytes
        WAV file content.

    Returns
    -------
    str
        The transcript with surrounding whitespace removed.
    """
    payload: dict[str, Any] = {
        "model": config.STT_MODEL,
        "input_audio": {
            "data": base64.b64encode(wav_bytes).decode("ascii"),
            "format": "wav",
        },
        "language": "en",
    }
    data: dict[str, Any] = post_json("/audio/transcriptions", payload)
    add_cost(
        label="speech-to-text",
        amount=data.get("usage", {}).get("cost"),
    )
    return data["text"].strip()


def listen() -> str:
    """Record from the microphone and return the transcript.

    Returns
    -------
    str
        What the user said.
    """
    return transcribe(wav_bytes=to_wav_bytes(record_until_enter()))


if __name__ == "__main__":
    config.require_key()
    print(listen())
