"""List OpenRouter text-to-speech models currently available."""


import requests

from typing import Any


URL: str = (
    "https://openrouter.ai/api/v1/models?output_modalities=speech"
)

resp: requests.Response = requests.get(
    url=URL,
    timeout=30,
)
resp.raise_for_status()
models: list[dict[str, Any]] = resp.json()["data"]

for m in models:
    print(
        m["id"], "|", m.get("pricing"), "|", m.get("supported_voices")
    )
