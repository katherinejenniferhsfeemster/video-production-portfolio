"""
Concatenate the three synthetic clips into a short demo MP4 with crossfades
and a teal/amber lower-third title. The output ships as the playable demo
on the portfolio site.

Run
---
    python3 scripts/python/render_demo.py
"""
from __future__ import annotations

import subprocess
from pathlib import Path


DATA = Path("assets/data")
OUT = Path("assets/demo/portfolio_cut.mp4")


def _normalize(src: Path, dst: Path) -> None:
    """Re-encode a clip to a common timebase so concat/xfade can join them."""
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src),
         "-vf", "fps=30,scale=1280:720:force_original_aspect_ratio=decrease,"
                "pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p,setsar=1",
         "-af", "aformat=sample_rates=48000:channel_layouts=stereo",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-c:a", "aac", "-b:a", "128k",
         "-video_track_timescale", "30000",
         str(dst)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path("assets/demo/_norm")
    tmp.mkdir(parents=True, exist_ok=True)

    # Step 1: normalize each source so xfade has matching streams.
    a = tmp / "a.mp4"; b = tmp / "b.mp4"; c = tmp / "c.mp4"
    _normalize(DATA / "clip_a.mp4", a)
    _normalize(DATA / "clip_b.mp4", b)
    _normalize(DATA / "clip_c.mp4", c)

    # Step 2: xfade the three normalized clips, add a persistent lower-third.
    fc = (
        "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=4.5[vab];"
        "[vab][2:v]xfade=transition=fade:duration=0.5:offset=7.0[vfx];"
        "[vfx]drawtext=text='Katherine Feemster \u2014 portfolio cut':"
        "fontcolor=white:fontsize=28:"
        "box=1:boxcolor=0x2E7A7B@0.85:boxborderw=14:"
        "x=40:y=h-th-40[vout];"
        "[0:a]afade=t=out:st=4.5:d=0.5[a0];"
        "[1:a]adelay=5000|5000,afade=t=in:st=5:d=0.5,afade=t=out:st=7:d=0.5[a1];"
        "[2:a]adelay=7500|7500,afade=t=in:st=7.5:d=0.5[a2];"
        "[a0][a1][a2]amix=inputs=3:normalize=0:duration=longest[aout]"
    )
    subprocess.run(
        ["ffmpeg", "-y",
         "-i", str(a), "-i", str(b), "-i", str(c),
         "-filter_complex", fc,
         "-map", "[vout]", "-map", "[aout]",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "20",
         "-c:a", "aac", "-b:a", "128k",
         "-movflags", "+faststart",
         "-t", "12",
         str(OUT)],
        check=True,
    )
    print(f"[ok] {OUT} ({OUT.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
