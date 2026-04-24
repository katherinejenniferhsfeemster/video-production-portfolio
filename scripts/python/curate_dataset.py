"""
AI dataset video curation pipeline.

For each input video, this script:
    1.  Probes container/codec/duration/fps with ffprobe (JSON output)
    2.  Detects scene cuts with PySceneDetect (content detector)
    3.  Computes a perceptual-hash dedup key per shot (3 frames -> aHash)
    4.  Writes a normalized H.264 / yuv420p / 30 fps mezzanine
    5.  Emits a per-shot CSV manifest ready for downstream AI labelling

Outputs
-------
    assets/data/curated/<basename>.mp4         normalized clip
    assets/data/curated/<basename>.shots.csv   per-shot manifest

Manifest columns
----------------
    shot_id, start_tc, end_tc, start_frame, end_frame, duration_s,
    ahash_a, ahash_b, ahash_c, dedup_key

Run
---
    python3 scripts/python/curate_dataset.py assets/data/clip_a.mp4 ...
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
from scenedetect import detect, ContentDetector


CURATED = Path("assets/data/curated")


# ---------------------------------------------------------------------------
# ffprobe / ffmpeg
# ---------------------------------------------------------------------------
def ffprobe(src: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", str(src)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(out.stdout)


def normalize(src: Path, dst: Path, fps: int = 30, height: int = 720) -> None:
    """Re-mux/transcode to H.264 yuv420p @ 30 fps, audio AAC 48 kHz stereo."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src),
         "-vf", f"scale=-2:{height},fps={fps}",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "20",
         "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "128k",
         "-movflags", "+faststart",
         str(dst)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


# ---------------------------------------------------------------------------
# scene detection + perceptual hash
# ---------------------------------------------------------------------------
def detect_shots(video: Path, threshold: float = 27.0) -> list[tuple[int, int, str, str, float]]:
    """Return list of (start_frame, end_frame, start_tc, end_tc, duration_s)."""
    scenes = detect(str(video), ContentDetector(threshold=threshold))
    out = []
    for s, e in scenes:
        out.append((s.frame_num, e.frame_num,
                    s.get_timecode(), e.get_timecode(),
                    (e - s).get_seconds()))
    if not out:
        # Single-shot fallback: treat whole clip as one shot
        cap = cv2.VideoCapture(str(video))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        out = [(0, n, "00:00:00.000", _tc(n / fps), n / fps)]
    return out


def _tc(seconds: float) -> str:
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = seconds - h*3600 - m*60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def ahash(frame_bgr: np.ndarray) -> str:
    """8x8 average-hash, hex-encoded."""
    g = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    g = cv2.resize(g, (8, 8), interpolation=cv2.INTER_AREA)
    bits = (g > g.mean()).flatten()
    val = 0
    for b in bits:
        val = (val << 1) | int(b)
    return f"{val:016x}"


def shot_hashes(video: Path, start_frame: int, end_frame: int) -> tuple[str, str, str]:
    """3 hashes: at start, middle, end of the shot."""
    cap = cv2.VideoCapture(str(video))
    n = max(1, end_frame - start_frame)
    targets = [start_frame, start_frame + n // 2, max(start_frame, end_frame - 1)]
    hashes = []
    for t in targets:
        cap.set(cv2.CAP_PROP_POS_FRAMES, t)
        ok, fr = cap.read()
        hashes.append(ahash(fr) if ok else "0" * 16)
    cap.release()
    return tuple(hashes)  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
@dataclass
class Shot:
    shot_id: int
    start_tc: str
    end_tc: str
    start_frame: int
    end_frame: int
    duration_s: float
    ahash_a: str
    ahash_b: str
    ahash_c: str

    @property
    def dedup_key(self) -> str:
        return self.ahash_b   # middle frame: representative

    def as_row(self) -> dict:
        d = self.__dict__.copy()
        d["dedup_key"] = self.dedup_key
        d["duration_s"] = round(self.duration_s, 3)
        return d


def curate(src: Path) -> dict:
    info = ffprobe(src)
    norm = CURATED / f"{src.stem}.mp4"
    normalize(src, norm)
    raw_shots = detect_shots(norm)
    shots: list[Shot] = []
    for i, (sf, ef, stc, etc, dur) in enumerate(raw_shots):
        ha, hb, hc = shot_hashes(norm, sf, ef)
        shots.append(Shot(i, stc, etc, sf, ef, dur, ha, hb, hc))

    csv_path = CURATED / f"{src.stem}.shots.csv"
    with csv_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(shots[0].as_row().keys()))
        w.writeheader()
        for s in shots:
            w.writerow(s.as_row())

    return {
        "input": str(src),
        "normalized": str(norm),
        "manifest": str(csv_path),
        "shots": len(shots),
        "container": info["format"]["format_name"],
        "duration_s": round(float(info["format"]["duration"]), 3),
    }


def main(args: Iterable[str]) -> None:
    inputs = [Path(a) for a in args]
    if not inputs:
        # default: every clip in assets/data
        inputs = sorted(Path("assets/data").glob("clip_*.mp4"))
    summary = [curate(p) for p in inputs]
    out = Path("assets/data/curated/_summary.json")
    out.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
