"""Step 3: generate the 16:9 cover image."""


import base64

from . import config
from .client import add_cost, post_json
from pathlib import Path
from typing import Any


def make_image(
    prompt: str,
    out_dir: Path,
) -> Path:
    """Generate a cover image and save it to disk.

    Parameters
    ----------
    prompt : str
        Description of the image.
    out_dir : pathlib.Path
        Folder to save into. The file is named `cover.<ext>`.

    Returns
    -------
    pathlib.Path
        Path of the saved image.
    """
    payload: dict[str, Any] = {
        "model": config.IMAGE_MODEL,
        "prompt": prompt,
        "aspect_ratio": "16:9",
    }
    data: dict[str, Any] = post_json(
        path="/images",
        payload=payload,
        timeout=300,
    )
    add_cost(
        label="image",
        amount=data.get("usage", {}).get("cost"),
    )
    item: dict[str, Any] = data["data"][0]
    ext: str = {
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/webp": "webp",
    }.get(item.get("media_type", "image/png"), "png")
    path: Path = out_dir / f"cover.{ext}"
    path.write_bytes(data=base64.b64decode(s=item["b64_json"]))
    return path
