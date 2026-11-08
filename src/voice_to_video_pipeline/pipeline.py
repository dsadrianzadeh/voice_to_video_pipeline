"""Command-line entry point that runs all five pipeline steps."""


import argparse

from . import config
from .client import print_costs
from .step01_speech import listen
from .step02_script import write_plan
from .step03_image import make_image
from .step04_voice import make_voiceover
from .step05_video import make_video
from datetime import datetime
from pathlib import Path
from typing import Any


def main() -> None:
    """Run idea -> plan -> image -> voiceover -> video (optional) ."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument(
        "--text",
        help="Skip the microphone and use this idea.",
    )
    parser.add_argument(
        "--no-video",
        action="store_true",
        help="Stop before the (expensive) video step.",
    )
    args: argparse.Namespace = parser.parse_args()

    config.require_key()
    run_dir: Path = (
        config.OUTPUT_DIR / datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    run_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("[INFO - pipeline.py] 1/5 Getting your idea...\n")
    idea: str = args.text or listen()
    print(f"    - Idea: {idea}\n")

    print("[INFO - pipeline.py] 2/5 Writing the plan...\n")
    plan: dict[str, Any] = write_plan(idea=idea)
    (run_dir / "plan.txt").write_text(
        data="\n\n".join(f"{k.upper()}:\n{v}" for k, v in plan.items()),
        encoding="utf-8",
    )
    print(f"    - Title: {plan['title']}\n")

    print("[INFO - pipeline.py] 3/5 Generating cover image...\n")
    image: Path = make_image(
        prompt=plan["image_prompt"],
        out_dir=run_dir,
    )

    print("[INFO - pipeline.py] 4/5 Generating voiceover...\n")
    make_voiceover(
        narration=plan["narration"],
        out_dir=run_dir,
    )

    if args.no_video:
        print("[INFO - pipeline.py] Skipping video (--no-video).\n")
    else:
        print(
            "[INFO - pipeline.py] 5/5 Generating video (this can take "
            "minutes)...\n"
        )
        video: Path = make_video(
            prompt=plan["video_prompt"],
            image_path=image,
            out_dir=run_dir,
        )
        print(f"    - Video: {video}\n")

    print(f"\nSaved to {run_dir}\n")
    print_costs()


if __name__ == "__main__":
    main()
