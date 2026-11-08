"""Offline unit tests. They never touch the network or spend credit."""


import numpy as np
import pytest

from conftest import FakeResponse
from pathlib import Path
from typing import Any
from voice_to_video_pipeline import client, config
from voice_to_video_pipeline.step01_speech import (
    to_wav_bytes,
    transcribe,
)
from voice_to_video_pipeline.step02_script import parse_json, write_plan
from voice_to_video_pipeline.step03_image import make_image
from voice_to_video_pipeline.step04_voice import make_voiceover


def test_add_cost_accumulates() -> None:
    """Costs for the same label add up; None counts as zero."""
    client.add_cost(
        label="x",
        amount=0.5,
    )
    client.add_cost(
        label="x",
        amount=None,
    )
    client.add_cost(
        label="x",
        amount="0.25",
    )
    assert client.costs["x"] == pytest.approx(0.75)


def test_require_key_rejects_placeholder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A placeholder key must stop the program."""
    monkeypatch.setattr(config, "API_KEY", "REPLACE_ME_WITH_YOUR_KEY")
    with pytest.raises(SystemExit):
        config.require_key()


def test_parse_json_strips_code_fences() -> None:
    """Markdown fences around JSON are removed before parsing."""
    assert parse_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_parse_json_allows_raw_newline_in_string() -> None:
    """A raw newline inside a string value no longer breaks parsing."""
    assert parse_json(
        text='{"a": "line1\nline2"}',
    ) == {"a": "line1\nline2"}


def test_to_wav_bytes_has_riff_header() -> None:
    """Encoded audio is a real WAV file."""
    audio = np.zeros((1600, 1), dtype="float32")
    assert to_wav_bytes(audio)[:4] == b"RIFF"


def test_request_adds_base_url_and_auth(fake_http: list[Any]) -> None:
    """Paths get the base URL and a Bearer header."""
    fake_http[0]["queue"].append(FakeResponse({"ok": True}))
    client.request(
        method="POST",
        url="/chat/completions",
        json={},
    )
    sent = fake_http[1]
    assert sent["url"] == config.BASE_URL + "/chat/completions"
    assert sent["headers"]["Authorization"] == "Bearer test-key"


def test_request_raises_on_http_error(fake_http: list[Any]) -> None:
    """Non-OK responses become RuntimeError."""
    fake_http[0]["queue"].append(FakeResponse(status=401))
    with pytest.raises(RuntimeError):
        client.request(
            method="GET",
            url="/x",
        )


def test_transcribe_returns_text_and_tracks_cost(
    fake_http: list[Any],
) -> None:
    """Transcript is stripped and cost recorded."""
    fake_http[0]["queue"].append(
        FakeResponse(
            {
                "text": " hello ",
                "usage": {"cost": 0.01},
            }
        )
    )
    assert transcribe(wav_bytes=b"wav") == "hello"
    assert client.costs["speech-to-text"] == pytest.approx(0.01)


def test_write_plan_ok_and_missing_keys(fake_http: list[Any]) -> None:
    """A complete plan passes; an incomplete one raises ValueError."""
    full = (
        '{"title":"t","narration":"n",'
        '"image_prompt":"i","video_prompt":"v"}'
    )
    fake_http[0]["queue"].append(
        FakeResponse({"choices": [{"message": {"content": full}}]})
    )
    assert write_plan(idea="idea")["title"] == "t"
    fake_http[0]["queue"].append(
        FakeResponse(
            {
                "choices": [{"message": {"content": '{"title":"t"}'}}]
            }
        )
    )
    with pytest.raises(ValueError):
        write_plan(idea="idea")


def test_make_image_writes_file(
    fake_http: list[Any],
    tmp_path: Path,
) -> None:
    """Base64 image data is decoded and saved as cover.png."""
    fake_http[0]["queue"].append(
        FakeResponse(
            {
                "data": [
                    {"b64_json": "aGk=", "media_type": "image/png"}
                ]
            }
        )
    )
    assert make_image(
        prompt="p",
        out_dir=tmp_path,
    ).read_bytes() == b"hi"


def test_make_voiceover_rejects_json(
    fake_http: list[Any],
    tmp_path: Path,
) -> None:
    """A JSON reply from the TTS endpoint is treated as an error."""
    fake_http[0]["queue"].append(FakeResponse({"error": "x"}))
    with pytest.raises(RuntimeError):
        make_voiceover(
            narration="hi",
            out_dir=tmp_path,
        )


def test_make_voiceover_saves_audio(
    fake_http: list[Any],
    tmp_path: Path,
) -> None:
    """Audio bytes are saved as voiceover.mp3."""
    fake_http[0]["queue"].append(
        FakeResponse(
            content=b"mp3",
            content_type="audio/mpeg",
        )
    )
    assert make_voiceover(
        narration="hi",
        out_dir=tmp_path,
    ).read_bytes() == b"mp3"
