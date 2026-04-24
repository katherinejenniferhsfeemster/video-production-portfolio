"""
Auto-captioning + burn-in pipeline.

In production this stage runs `whisper` (or the fork of your choice) on the
audio track. Whisper is heavy and not always available in CI, so this
script also ships a deterministic ASR stub that fakes a transcript from a
fixed script -- it lets the rest of the pipeline (SRT generation, ffmpeg
burn-in) run end-to-end in CI without GPU dependencies.

If `WHISPER_MODEL` is set in the environment and `whisper` is importable,
the real model is used; otherwise the stub kicks in.

Run
---
    python3 scripts/python/auto_caption.py assets/data/clip_b.mp4
"""
from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Cue:
    idx: int
    start_s: float
    end_s: float
    text: str

    def to_srt(self) -> str:
        return (f"{self.idx}\n"
                f"{_srt_tc(self.start_s)} --> {_srt_tc(self.end_s)}\n"
                f"{self.text}\n")


def _srt_tc(s: float) -> str:
    h = int(s // 3600); m = int((s % 3600) // 60); ss = s - h*3600 - m*60
    whole = int(ss); ms = int(round((ss - whole) * 1000))
    return f"{h:02d}:{m:02d}:{whole:02d},{ms:03d}"


# ---------------------------------------------------------------------------
# ASR
# ---------------------------------------------------------------------------
STUB_SCRIPT = [
    (0.0, 1.4, "Welcome to the Katherine Feemster portfolio cut."),
    (1.5, 3.0, "Five projects across Shotcut, OpenShot and Lightworks."),
    (3.1, 4.5, "Every figure regenerates from a script."),
]


def transcribe(audio: Path) -> list[Cue]:
    if os.environ.get("WHISPER_MODEL"):
        try:
            import whisper                              # type: ignore
            model = whisper.load_model(os.environ["WHISPER_MODEL"])
            result = model.transcribe(str(audio))
            cues = []
            for i, seg in enumerate(result["segments"], start=1):
                cues.append(Cue(i, seg["start"], seg["end"], seg["text"].strip()))
            return cues
        except Exception as exc:                        # noqa: BLE001
            print(f"[warn] whisper failed ({exc}); falling back to stub", file=sys.stderr)
    return [Cue(i + 1, a, b, t) for i, (a, b, t) in enumerate(STUB_SCRIPT)]


def write_srt(cues: list[Cue], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(c.to_srt() for c in cues))
    print(f"[ok] {out} ({len(cues)} cues)")


# ---------------------------------------------------------------------------
# Burn-in via ffmpeg
# ---------------------------------------------------------------------------
def burn_in(video: Path, srt: Path, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    # Style: bottom safe-area, Inter-equivalent sans, teal background box.
    style = (
        "FontName=DejaVu Sans,FontSize=22,PrimaryColour=&H00FBFAF7,"
        "OutlineColour=&H00000000,BorderStyle=3,Outline=1,Shadow=0,"
        "BackColour=&HCC2E7A7B,MarginV=60,Alignment=2"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video),
         "-vf", f"subtitles={srt.as_posix()}:force_style='{style}'",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "20",
         "-c:a", "copy",
         str(out)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    print(f"[ok] {out} ({out.stat().st_size/1024:.0f} KB)")


def main(argv: list[str]) -> None:
    if not argv:
        argv = ["assets/data/clip_b.mp4"]
    video = Path(argv[0])
    srt = Path("assets/demo") / f"{video.stem}.srt"
    out = Path("assets/demo") / f"{video.stem}.captioned.mp4"

    cues = transcribe(video)
    write_srt(cues, srt)
    burn_in(video, srt, out)


if __name__ == "__main__":
    main(sys.argv[1:])
