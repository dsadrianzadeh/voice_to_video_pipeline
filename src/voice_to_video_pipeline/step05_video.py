"""Step 5: generate the video from the cover image and a prompt."""


import base64
import time

from . import config
from .client import add_cost, post_json, request
from pathlib import Path
from typing import Any


POLL_SECONDS: int = 15
TIMEOUT_SECONDS: int = 15 * 60


def make_video(
    prompt: str,
    image_path: Path,
    out_dir: Path,
) -> Path:
    """Generate an 8-second 720p video and download it.

    Parameters
    ----------
    prompt : str
        Description of motion, camera, lighting, and scene.
    image_path : pathlib.Path
        Cover image used as the first frame.
    out_dir : pathlib.Path
        Folder to save `video.mp4` into.

    Returns
    -------
    pathlib.Path
        Path of the saved video.

    Raises
    ------
    RuntimeError
        If the job fails, is cancelled or expires.
    TimeoutError
        If the job takes longer than `TIMEOUT_SECONDS`.
    """
    b64: str = base64.b64encode(
        s=image_path.read_bytes(),
    ).decode("ascii")
    mime: str = (
        "image/png"
        if image_path.suffix == ".png"
        else "image/jpeg"
    )
    payload: dict[str, Any] = {
        "model": config.VIDEO_MODEL,
        "prompt": prompt,
        "duration": 6,
        "resolution": "720p",
        "aspect_ratio": "16:9",
        "frame_images": [{
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{b64}"},
            "frame_type": "first_frame",
        }],
    }
    job: dict[str, Any] = post_json(
        path="/videos",
        payload=payload,
    )
    polling_url: str = job["polling_url"]
    print(f"    - Video job {job['id']} submitted.\n")

    start: float = time.time()
    while True:
        status: dict[str, Any] = request(
            method="GET",
            url=polling_url,
        ).json()
        state: str = status["status"]
        print(f"    - Video job {job['id']} status: {state}\n")
        if state == "completed":
            break
        if state in ("failed", "cancelled", "expired"):
            raise RuntimeError(
                f"[RuntimeError - step05_video.py] Video job {state}: "
                f"{status.get('error')}\n"
            )
        if time.time() - start > TIMEOUT_SECONDS:
            raise TimeoutError(
                "[TimeoutError - step05_video.py] Video generation "
                "took too long.\n"
            )
        time.sleep(POLL_SECONDS)

    add_cost(
        label="video",
        amount=status.get("usage", {}).get("cost"),
    )
    content = request(
        method="GET",
        url=status["unsigned_urls"][0],
        timeout=300,
    )
    path: Path = out_dir / "video.mp4"
    path.write_bytes(data=content.content)
    return path
