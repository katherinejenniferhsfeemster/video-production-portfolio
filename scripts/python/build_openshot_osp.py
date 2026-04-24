"""
Generate an OpenShot .osp project (JSON) and a parallel OpenTimelineIO
.otio file from a CSV shotlist. OpenShot opens .osp directly; the .otio
flavour is the interchange format every modern NLE understands.

Run
---
    python3 scripts/python/build_openshot_osp.py
"""
from __future__ import annotations

import csv
import json
import uuid
from pathlib import Path

import opentimelineio as otio


# Synthetic shotlist (would come from curate_dataset.py manifest in prod).
SHOTLIST = [
    # (source, in_s, out_s, label)
    ("clip_a.mp4", 0.0, 4.0,  "calibration"),
    ("clip_b.mp4", 0.0, 3.0,  "title"),
    ("clip_c.mp4", 0.5, 5.5,  "b-roll"),
]

DATA_DIR = Path("../../assets/data")


# ---------------------------------------------------------------------------
# OpenShot .osp
# ---------------------------------------------------------------------------
def build_osp(out: Path) -> None:
    project = {
        "id": "PORTFOLIO0001",
        "fps": {"num": 30, "den": 1},
        "width": 1280,
        "height": 720,
        "sample_rate": 48000,
        "channels": 2,
        "channel_layout": 3,
        "duration": sum(b - a for _, a, b, _ in SHOTLIST),
        "scale": 15,
        "tick_pixels": 100,
        "playhead_position": 0.0,
        "profile": "HD 720p 30 fps",
        "files": [],
        "clips": [],
        "effects": [],
        "markers": [],
        "tracks": [
            {"id": "T0", "label": "V1", "number": 1000000, "y": 0, "lock": False},
        ],
        "version": {"openshot-qt": "3.2.1", "libopenshot": "0.4.0"},
    }

    cursor = 0.0
    for src, ts, te, label in SHOTLIST:
        file_id = f"F{uuid.uuid4().hex[:6].upper()}"
        clip_id = f"C{uuid.uuid4().hex[:6].upper()}"
        path = (DATA_DIR / src).as_posix()
        dur = te - ts

        project["files"].append({
            "id": file_id,
            "path": path,
            "media_type": "video",
            "fps": {"num": 30, "den": 1},
            "width": 1280, "height": 720,
            "video_length": str(int(dur * 30)),
            "video_timebase": {"num": 1, "den": 30},
            "duration": dur,
            "has_audio": True, "has_video": True,
        })

        project["clips"].append({
            "id": clip_id,
            "title": label,
            "file_id": file_id,
            "reader": {"path": path},
            "position": cursor,
            "start": ts,
            "end": te,
            "layer": 1000000,
            "alpha": {"Points": [{"co": {"X": 1.0, "Y": 1.0}, "interpolation": 0}]},
            "scale_x": {"Points": [{"co": {"X": 1.0, "Y": 1.0}, "interpolation": 0}]},
            "scale_y": {"Points": [{"co": {"X": 1.0, "Y": 1.0}, "interpolation": 0}]},
            "volume": {"Points": [{"co": {"X": 1.0, "Y": 1.0}, "interpolation": 0}]},
            "scale": 1,
        })
        cursor += dur

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(project, indent=2))
    print(f"[ok] {out} ({out.stat().st_size} bytes, {len(project['clips'])} clips)")


# ---------------------------------------------------------------------------
# OpenTimelineIO .otio (interchange)
# ---------------------------------------------------------------------------
def build_otio(out: Path) -> None:
    timeline = otio.schema.Timeline(name="Katherine Feemster — portfolio cut")
    track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)
    timeline.tracks.append(track)

    rate = 30.0
    for src, ts, te, label in SHOTLIST:
        media_ref = otio.schema.ExternalReference(
            target_url=(DATA_DIR / src).as_posix(),
            available_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, rate),
                duration=otio.opentime.RationalTime((te + 5) * rate, rate),
            ),
        )
        clip = otio.schema.Clip(
            name=label,
            media_reference=media_ref,
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(ts * rate, rate),
                duration=otio.opentime.RationalTime((te - ts) * rate, rate),
            ),
        )
        track.append(clip)

    out.parent.mkdir(parents=True, exist_ok=True)
    otio.adapters.write_to_file(timeline, str(out))
    print(f"[ok] {out} ({out.stat().st_size} bytes)")


def main() -> None:
    build_osp(Path("scripts/projects/portfolio.osp"))
    build_otio(Path("scripts/projects/portfolio.otio"))


if __name__ == "__main__":
    main()
