"""
Generate a small set of synthetic source clips used by every demo in this
portfolio. Pure ffmpeg + libavfilter -- no external footage required.

Outputs
-------
    assets/data/clip_a.mp4   colour-bars, 5 s, 1280x720@30, with 1 kHz tone
    assets/data/clip_b.mp4   teal/amber gradient with moving title, 4 s
    assets/data/clip_c.mp4   greyscale gradient + sweep tone, 6 s

Run
---
    python3 scripts/python/make_synthetic_clips.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


OUT = Path("assets/data")


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def make_clip_a(path: Path) -> None:
    """SMPTE colour-bars + 1 kHz tone, 5 s."""
    _run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "smptebars=size=1280x720:rate=30:duration=5",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=5:sample_rate=48000",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "128k",
        str(path),
    ])


def make_clip_b(path: Path) -> None:
    """Teal/amber gradient with a moving title, 4 s."""
    drawtext = (
        "drawtext=text='Katherine Feemster':"
        "fontcolor=white:fontsize=56:"
        "x='if(lt(t\\,2)\\, w*t/2 - tw/2 + 50\\, w/2 - tw/2)':"
        "y=(h-th)/2"
    )
    vf = (
        "color=c=0x2E7A7B:size=1280x720:rate=30,"
        "geq=r='180+40*sin(2*PI*X/W)':g='160':b='110+30*cos(2*PI*Y/H)',"
        + drawtext
    )
    _run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"{vf}",
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-t", "4",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "128k",
        str(path),
    ])


def make_clip_c(path: Path) -> None:
    """Greyscale gradient + sine sweep, 6 s."""
    _run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "gradients=size=1280x720:rate=30:duration=6:c0=0x111418:c1=0xE3DED3",
        "-f", "lavfi", "-i", "sine=frequency=200:beep_factor=4:duration=6",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "128k",
        str(path),
    ])


def main() -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not on PATH; please install it first.")
    OUT.mkdir(parents=True, exist_ok=True)
    make_clip_a(OUT / "clip_a.mp4")
    make_clip_b(OUT / "clip_b.mp4")
    make_clip_c(OUT / "clip_c.mp4")
    for p in sorted(OUT.glob("clip_*.mp4")):
        print(f"[ok] {p}  ({p.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
