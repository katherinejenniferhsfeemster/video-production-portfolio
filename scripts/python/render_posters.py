"""
Render the four PNG posters that ship in docs/assets:

    1. waveform_scopes.png   audio waveform + RGB parade for clip_a (bars)
    2. scene_grid.png        scene-cut grid: thumbnails per detected shot
    3. timeline_mock.png     editorial timeline with V1, A1, lower-thirds
    4. caption_preview.png   single frame from the captioned demo

Run
---
    python3 scripts/python/render_posters.py
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


# Editorial palette
TEAL = "#2E7A7B"
TEAL_DEEP = "#1F5A5B"
AMBER = "#D9A441"
INK = "#0F1A1F"
BG = "#FBFAF7"
BG2 = "#F2EFE8"
LINE = "#E3DED3"


REND = Path("assets/renders")
DATA = Path("assets/data")
DEMO = Path("assets/demo")


def _setup() -> None:
    REND.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK, "ytick.color": INK,
        "axes.spines.top": False, "axes.spines.right": False,
        "figure.facecolor": BG, "axes.facecolor": BG,
    })


# ---------------------------------------------------------------------------
# 1. Waveform + RGB parade for clip_a
# ---------------------------------------------------------------------------
def render_waveform_scopes() -> None:
    src = DATA / "clip_a.mp4"
    # Audio: extract mono PCM, read with numpy
    pcm = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(src),
         "-f", "s16le", "-ac", "1", "-ar", "48000", "-"],
        check=True, capture_output=True,
    ).stdout
    audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
    # Downsample for plotting
    if audio.size > 4000:
        step = audio.size // 4000
        audio = np.abs(audio[: step * 4000]).reshape(-1, step).max(axis=1)
    t = np.linspace(0, 5, audio.size)

    # Video: RGB parade -- column-mean channels of the middle frame
    cap = cv2.VideoCapture(str(src))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, n // 2)
    ok, frame = cap.read()
    cap.release()
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) if ok else np.zeros((720, 1280, 3))
    parade = rgb.mean(axis=0) / 255.0   # (W, 3)
    x = np.linspace(0, 100, parade.shape[0])

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6.5),
                                   gridspec_kw={"height_ratios": [1, 1.1]})
    fig.subplots_adjust(hspace=0.45, top=0.92, bottom=0.10, left=0.08, right=0.96)

    ax1.fill_between(t, audio, -audio, color=TEAL, linewidth=0)
    ax1.set_xlim(0, 5)
    ax1.set_ylim(-1, 1)
    ax1.set_xlabel("seconds", fontsize=10)
    ax1.set_ylabel("amplitude", fontsize=10)
    ax1.set_title("Audio waveform — clip_a (1 kHz tone, 5 s)",
                  loc="left", fontsize=12, color=INK, weight="bold", pad=12)

    ax2.plot(x, parade[:, 0], color="#B82E2E", linewidth=1.4, label="R")
    ax2.plot(x, parade[:, 1], color=TEAL, linewidth=1.4, label="G")
    ax2.plot(x, parade[:, 2], color=AMBER, linewidth=1.4, label="B")
    ax2.set_xlim(0, 100); ax2.set_ylim(0, 1)
    ax2.set_xlabel("horizontal position (%)", fontsize=10)
    ax2.set_ylabel("intensity", fontsize=10)
    ax2.legend(loc="upper right", frameon=False)
    ax2.set_title("RGB parade — middle frame of clip_a",
                  loc="left", fontsize=12, color=INK, weight="bold", pad=12)

    fig.savefig(REND / "waveform_scopes.png", dpi=140, facecolor=BG)
    plt.close(fig)
    print(f"[ok] {REND / 'waveform_scopes.png'}")


# ---------------------------------------------------------------------------
# 2. Scene-cut grid
# ---------------------------------------------------------------------------
def render_scene_grid() -> None:
    """Tile of representative frames -- one per source clip (proxy for shots)."""
    cells = []
    for src in sorted(DATA.glob("clip_*.mp4")):
        cap = cv2.VideoCapture(str(src))
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        for t in (n // 4, n // 2, 3 * n // 4):
            cap.set(cv2.CAP_PROP_POS_FRAMES, t)
            ok, fr = cap.read()
            if ok:
                cells.append((src.stem, t, cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)))
        cap.release()

    cols = 3
    rows = int(np.ceil(len(cells) / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(11, 2.6 * rows))
    fig.subplots_adjust(hspace=0.35, wspace=0.08, top=0.93, bottom=0.04, left=0.04, right=0.96)
    fig.suptitle("Scene grid — representative frames per shot",
                 x=0.04, y=0.985, ha="left", fontsize=14, color=INK, weight="bold")
    for ax, (name, frame_idx, img) in zip(np.array(axes).flatten(), cells):
        ax.imshow(img); ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(f"{name} · f{frame_idx}", fontsize=10, color=INK, loc="left")
        for spine in ax.spines.values():
            spine.set_color(LINE)
    for ax in np.array(axes).flatten()[len(cells):]:
        ax.set_visible(False)
    fig.savefig(REND / "scene_grid.png", dpi=140, facecolor=BG)
    plt.close(fig)
    print(f"[ok] {REND / 'scene_grid.png'}")


# ---------------------------------------------------------------------------
# 3. Timeline mockup
# ---------------------------------------------------------------------------
def render_timeline() -> None:
    fig, ax = plt.subplots(figsize=(12, 4.2))
    fig.subplots_adjust(top=0.85, bottom=0.18, left=0.07, right=0.97)

    track_y = {"V1": 1.6, "A1": 0.6}
    clips = [  # (track, start, dur, label, color)
        ("V1", 0.0, 4.0, "calibration · clip_a", TEAL),
        ("V1", 4.0, 3.0, "title · clip_b", AMBER),
        ("V1", 7.0, 5.0, "b-roll · clip_c", TEAL_DEEP),
        ("A1", 0.0, 4.0, "tone 1 kHz", TEAL),
        ("A1", 4.0, 3.0, "silence", LINE),
        ("A1", 7.0, 5.0, "sweep", TEAL_DEEP),
    ]
    for track, start, dur, label, color in clips:
        y = track_y[track]
        ax.add_patch(mpatches.FancyBboxPatch(
            (start, y - 0.32), dur, 0.64, boxstyle="round,pad=0.02,rounding_size=0.08",
            linewidth=0.8, edgecolor=INK, facecolor=color, alpha=0.92))
        ax.text(start + 0.15, y, label, fontsize=9, color="white" if color != LINE else INK,
                va="center", ha="left", weight="bold")

    # Lower-third markers
    for x, txt in [(0.4, "01 — Bars"),
                   (4.4, "02 — Title"),
                   (7.4, "03 — B-roll")]:
        ax.text(x, 2.55, txt, fontsize=9, color=INK,
                bbox=dict(facecolor=BG2, edgecolor=LINE, boxstyle="round,pad=0.25"))

    ax.set_xlim(-0.2, 12.2); ax.set_ylim(0, 3)
    ax.set_yticks([0.6, 1.6], ["A1", "V1"])
    ax.set_xticks(range(0, 13))
    ax.set_xlabel("seconds", fontsize=10)
    ax.set_title("Editorial timeline — Shotcut/OpenShot/Lightworks compatible",
                 loc="left", fontsize=14, color=INK, weight="bold", pad=14)
    ax.grid(axis="x", color=LINE, linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.savefig(REND / "timeline_mock.png", dpi=140, facecolor=BG)
    plt.close(fig)
    print(f"[ok] {REND / 'timeline_mock.png'}")


# ---------------------------------------------------------------------------
# 4. Caption preview (extracted from captioned demo)
# ---------------------------------------------------------------------------
def render_caption_preview() -> None:
    cap = DEMO / "clip_b.captioned.mp4"
    out = REND / "caption_preview.png"
    if not cap.exists():
        print(f"[skip] {cap} not yet rendered; run auto_caption first")
        return
    subprocess.run(
        ["ffmpeg", "-y", "-ss", "00:00:01.500", "-i", str(cap),
         "-frames:v", "1", str(out)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    print(f"[ok] {out}")


def main() -> None:
    _setup()
    render_waveform_scopes()
    render_scene_grid()
    render_timeline()
    render_caption_preview()


if __name__ == "__main__":
    main()
