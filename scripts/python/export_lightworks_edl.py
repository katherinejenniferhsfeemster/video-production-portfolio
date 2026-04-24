"""
Export a CMX 3600 EDL plus a tab-separated shotlist that Lightworks (and
Avid / DaVinci Resolve) can import directly. EDLs are the lowest-common-
denominator interchange format -- they survive every NLE roundtrip.

The generated EDL also includes a sidecar `.cube` LUT (33-point, identity
biased toward teal/amber) so a colour grading pass has something concrete
to attach to.

Run
---
    python3 scripts/python/export_lightworks_edl.py
"""
from __future__ import annotations

import csv
from pathlib import Path
import numpy as np


SHOTLIST = [
    # (reel, source_in, source_out, record_in, record_out, source_clip, label)
    ("AX",   "00:00:00:00", "00:00:04:00", "00:00:00:00", "00:00:04:00", "clip_a.mp4", "calibration"),
    ("BX",   "00:00:00:00", "00:00:03:00", "00:00:04:00", "00:00:07:00", "clip_b.mp4", "title"),
    ("CX",   "00:00:00:15", "00:00:05:15", "00:00:07:00", "00:00:12:00", "clip_c.mp4", "b-roll"),
]


def write_edl(out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "TITLE:   KATHERINE_FEEMSTER_PORTFOLIO",
        "FCM: NON-DROP FRAME",
        "",
    ]
    for i, (reel, sin, sout, rin, rout, src, label) in enumerate(SHOTLIST, start=1):
        # CMX-3600: <event#> <reel> <track> <transition> <source-in> <source-out> <record-in> <record-out>
        lines.append(f"{i:03d}  {reel:<8}V     C        {sin} {sout} {rin} {rout}")
        lines.append(f"* FROM CLIP NAME: {src}")
        lines.append(f"* COMMENT: {label}")
        lines.append("")
    out.write_text("\n".join(lines))
    print(f"[ok] {out} ({out.stat().st_size} bytes, {len(SHOTLIST)} events)")


def write_shotlist_tsv(out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["event", "reel", "src_in", "src_out",
                    "rec_in", "rec_out", "source", "label"])
        for i, row in enumerate(SHOTLIST, start=1):
            w.writerow([i, *row])
    print(f"[ok] {out}")


def write_lut(out: Path, n: int = 33) -> None:
    """Identity LUT biased toward the teal/amber editorial palette."""
    out.parent.mkdir(parents=True, exist_ok=True)
    grid = np.linspace(0, 1, n)
    teal = np.array([0.18, 0.48, 0.48])
    amber = np.array([0.85, 0.64, 0.25])

    with out.open("w") as fh:
        fh.write("# Katherine Feemster — editorial teal/amber LUT (33-pt cube)\n")
        fh.write("LUT_3D_SIZE 33\nDOMAIN_MIN 0.0 0.0 0.0\nDOMAIN_MAX 1.0 1.0 1.0\n\n")
        for b in grid:
            for g in grid:
                for r in grid:
                    rgb = np.array([r, g, b])
                    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
                    # Lift shadows toward teal, push highlights toward amber
                    push = (1 - luma) * teal + luma * amber
                    out_rgb = 0.85 * rgb + 0.15 * push
                    out_rgb = np.clip(out_rgb, 0.0, 1.0)
                    fh.write(f"{out_rgb[0]:.6f} {out_rgb[1]:.6f} {out_rgb[2]:.6f}\n")
    print(f"[ok] {out}")


def main() -> None:
    base = Path("scripts/projects")
    write_edl(base / "portfolio.edl")
    write_shotlist_tsv(base / "portfolio.shotlist.tsv")
    write_lut(base / "editorial.cube")


if __name__ == "__main__":
    main()
