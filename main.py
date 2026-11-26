#!/usr/bin/env python3
"""Deliver the bundled front-page image to the grader's output folder.

The newspaper image for this entry was rendered ahead of time and ships in
this repository as entry.png. This script's only job is to hand that file
to the grader: it copies entry.png into the directory named by the
MAKEFUN_OUTPUT_DIR environment variable, or into an "out" folder next to
this script when the variable is not set.
"""

import os
import shutil
import sys
from pathlib import Path


def bundled_image() -> Path:
    """Return the path of the entry.png shipped beside this script."""
    return Path(__file__).resolve().parent / "entry.png"


def output_folder() -> Path:
    """Pick where the image should land, creating the folder if needed."""
    configured = os.environ.get("MAKEFUN_OUTPUT_DIR", "").strip()
    folder = Path(configured) if configured else Path(__file__).resolve().parent / "out"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def main() -> int:
    source = bundled_image()
    if not source.is_file():
        print(f"bundled image not found: {source}", file=sys.stderr)
        return 1
    destination = output_folder() / source.name
    shutil.copyfile(source, destination)
    print(f"copied {source.name} -> {destination} ({destination.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
