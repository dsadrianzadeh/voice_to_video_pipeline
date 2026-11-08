"""Step 2: turn a spoken idea into a structured video plan."""


import json
import re
from typing import Any

from . import config
from .client import add_cost, post_json


SYSTEM: str = (
    "You are a video producer. Turn the user's idea into a short video "
    "plan. Reply with ONLY a JSON object with keys: "
    "title (string), narration (string, 2-3 spoken sentences), "
    "image_prompt (string, a detailed 16:9 cover image description), "
    "video_prompt (string, describing motion, camera, lighting, scene)."
)

REQUIRED_KEYS: set[str] = {
    "title",
    "narration",
    "image_prompt",
    "video_prompt",
}

MAX_TRIES: int = 3


def parse_json(text: str) -> dict[str, Any]:
    """Parse JSON from model text, tolerating fences and stray newlines.

    Parameters
    ----------
    text : str
        Raw model reply, possibly wrapped in triple backticks or extra
        text.

    Returns
    -------
    dict
        The decoded JSON object.
    """
    cleaned: str = re.sub(
        pattern=r"^```(?:json)?|```$",
        repl="",
        string=text.strip(),
        flags=re.M,
    ).strip()
    start: int = cleaned.find("{")
    end: int = cleaned.rfind("}")
    if start != -1 and end > start:
        cleaned = cleaned[start : end + 1]
    return json.loads(
        s=cleaned,
        strict=False,
    )


def write_plan(idea: str) -> dict[str, Any]:
    """Ask the text model for a video plan, retrying on invalid JSON.

    Parameters
    ----------
    idea : str
        The user's video idea.

    Returns
    -------
    dict
        Plan with `title`, `narration`, `image_prompt`, and
        `video_prompt`.

    Raises
    ------
    json.JSONDecodeError
        If every attempt returns text that is not valid JSON.
    ValueError
        If the model reply is missing any required key.
    """
    payload: dict[str, Any] = {
        "model": config.TEXT_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": idea},
        ],
    }
    plan: dict[str, Any] = {}
    for attempt in range(1, MAX_TRIES + 1):
        data: dict[str, Any] = post_json(
            path="/chat/completions",
            payload=payload,
        )
        add_cost(
            label="script",
            amount=data.get("usage", {}).get("cost"),
        )
        try:
            plan = parse_json(
                text=data["choices"][0]["message"]["content"],
            )
            break
        except json.JSONDecodeError:
            print(
                f"[WARN - step02_script.py] Attempt "
                f"{attempt}/{MAX_TRIES}: reply was not valid JSON.\n"
            )
            if attempt == MAX_TRIES:
                raise
    missing: set[str] = REQUIRED_KEYS - plan.keys()
    if missing:
        raise ValueError(
            f"[ValueError - step02_script] Model reply missing keys: "
            f"{missing}\n"
        )
    return plan


if __name__ == "__main__":
    config.require_key()
    print(
        json.dumps(
            obj=write_plan(idea="A lighthouse in a storm"),
            indent=2,
        )
    )
