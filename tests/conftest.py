"""Shared pytest fixtures: no real network calls, no real key."""


import pytest
import requests

from typing import Any
from voice_to_video_pipeline import client, config


class FakeResponse:
    """Minimal stand-in for `requests.Response`."""

    def __init__(
        self,
        json_data: dict[str, Any] | None = None,
        content: bytes = b"",
        status: int = 200,
        content_type: str = "application/json",
    ) -> None:
        self._json = json_data or {}
        self.content = content
        self.status_code = status
        self.ok = status < 400
        self.text = str(self._json)
        self.headers = {"Content-Type": content_type}

    def json(self) -> dict[str, Any]:
        """Return the stored JSON body."""
        return self._json


@pytest.fixture(autouse=True)
def _safe_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Use a fake key and clear the cost tracker for every test."""
    monkeypatch.setattr(config, "API_KEY", "test-key")
    client.costs.clear()


@pytest.fixture
def fake_http(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Replace `requests.request`; return the list of captured calls."""
    calls: list[dict[str, Any]] = []
    queue_: list[FakeResponse] = []

    def fake(**kwargs: Any) -> FakeResponse:
        calls.append(kwargs)
        return queue_.pop(0)

    monkeypatch.setattr(requests, "request", fake)
    calls.append({"queue": queue_})  # Index 0 holds the response queue.
    return calls
