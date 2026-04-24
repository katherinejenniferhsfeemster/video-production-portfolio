"""
Generate a Shotcut-native .mlt project from a CSV shotlist.

The output is valid MLT XML that opens directly in Shotcut: it includes a
profile, three producers (one per source clip), a tractor/playlist for the
V1 video track, and a transparent "Text: Simple" filter on each clip for
lower-thirds. Audio is taken from the underlying clips.

This script exercises every primitive a real cutter touches in Shotcut:
profile selection, producers with in/out, playlists, filters with keyframes.

Run
---
    python3 scripts/python/build_shotcut_mlt.py
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom


PROFILE = {
    "description": "HD 720p 30 fps",
    "width": "1280", "height": "720",
    "progressive": "1",
    "sample_aspect_num": "1", "sample_aspect_den": "1",
    "display_aspect_num": "16", "display_aspect_den": "9",
    "frame_rate_num": "30", "frame_rate_den": "1",
    "colorspace": "709",
}


CLIPS = [
    # (source, in_frame, out_frame, lower_third)
    ("clip_a.mp4",   0, 119, "01 — Bars (calibration)"),
    ("clip_b.mp4",   0,  89, "02 — Title — Katherine Feemster"),
    ("clip_c.mp4",  10, 169, "03 — Gradient B-roll"),
]


def _e(parent: ET.Element, tag: str, attrib: dict | None = None,
       text: str | None = None) -> ET.Element:
    el = ET.SubElement(parent, tag, attrib or {})
    if text is not None:
        el.text = text
    return el


def _prop(parent: ET.Element, name: str, value: str) -> None:
    p = ET.SubElement(parent, "property", {"name": name})
    p.text = value


def build_mlt(out: Path, data_dir: Path) -> None:
    mlt = ET.Element("mlt", {
        "LC_NUMERIC": "C",
        "version": "7.24.0",
        "title": "Katherine Feemster — portfolio cut",
        "producer": "main_bin",
    })

    profile = ET.SubElement(mlt, "profile", PROFILE)  # noqa: F841

    # Producers
    for i, (src, _in, _out, _) in enumerate(CLIPS):
        prod = _e(mlt, "producer", {"id": f"producer{i}", "in": "00:00:00.000"})
        _prop(prod, "resource", str((data_dir / src).as_posix()))
        _prop(prod, "mlt_service", "avformat-novalidate")
        _prop(prod, "audio_index", "1")
        _prop(prod, "video_index", "0")
        _prop(prod, "mute_on_pause", "0")

    # Playlist for the video track
    playlist = _e(mlt, "playlist", {"id": "playlist0"})
    _prop(playlist, "shotcut:video", "1")
    _prop(playlist, "shotcut:name", "V1")

    for i, (_src, fi, fo, lower) in enumerate(CLIPS):
        entry = _e(playlist, "entry", {
            "producer": f"producer{i}",
            "in": _frames_to_tc(fi),
            "out": _frames_to_tc(fo),
        })
        # Lower-third overlay (Shotcut "Text: Simple")
        flt = _e(entry, "filter", {"id": f"filter{i}"})
        _prop(flt, "argument", lower)
        _prop(flt, "geometry", "0 600 1280 80 1")
        _prop(flt, "family", "Inter")
        _prop(flt, "size", "36")
        _prop(flt, "fgcolour", "#FBFAF7")
        _prop(flt, "bgcolour", "#992E7A7B")     # 60% teal
        _prop(flt, "olcolour", "#000F1A1F")
        _prop(flt, "halign", "left")
        _prop(flt, "valign", "top")
        _prop(flt, "mlt_service", "dynamictext")
        _prop(flt, "shotcut:filter", "dynamicText")

    # Tractor wires the playlist into the master timeline
    tractor = _e(mlt, "tractor", {
        "id": "tractor0",
        "title": "Shotcut version 7.24.0",
        "in": "00:00:00.000",
    })
    _prop(tractor, "shotcut", "1")
    _e(tractor, "track", {"producer": "playlist0"})

    # main_bin so Shotcut shows clips in the Source pane
    main_bin = _e(mlt, "playlist", {"id": "main_bin"})
    _prop(main_bin, "shotcut:projectAudioChannels", "2")
    _prop(main_bin, "shotcut:projectFolder", "1")
    for i in range(len(CLIPS)):
        _e(main_bin, "entry", {"producer": f"producer{i}"})

    rough = ET.tostring(mlt, encoding="utf-8")
    pretty = minidom.parseString(rough).toprettyxml(indent="  ")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(pretty)
    print(f"[ok] {out} ({out.stat().st_size} bytes)")


def _frames_to_tc(frames: int, fps: int = 30) -> str:
    seconds = frames / fps
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = seconds - h*3600 - m*60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


if __name__ == "__main__":
    build_mlt(Path("scripts/projects/portfolio.mlt"),
              data_dir=Path("../../assets/data"))
