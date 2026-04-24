# Auto-Captioning + Safe-Area Burn-In

Accessible captions for research clips and social cut-downs, generated
reproducibly from code. Whisper does the transcription when available;
otherwise a scripted `.srt` feeds the same burn-in path so CI never needs a
network round-trip.

## What the script produces

`scripts/python/auto_caption.py` emits:

- **`assets/demo/portfolio.srt`** — transcript with `HH:MM:SS,mmm` timing.
- **`assets/demo/clip_b.captioned.mp4`** — 1080p30 MP4 with the SRT burned in
  via ffmpeg's `subtitles` filter, respecting a **10 % action-safe** bottom
  margin (108 px at 1080p).

## Whisper path (optional)

```bash
WHISPER=1 python3 scripts/python/auto_caption.py \
  --input assets/data/clip_b.mp4 \
  --srt  assets/demo/portfolio.srt \
  --out  assets/demo/clip_b.captioned.mp4
```

When `WHISPER=1` the script loads the `base` model (configurable), transcribes
the audio and writes a proper `.srt`. Without the flag the script falls back
to a hand-written transcript committed in the repo, so CI stays offline and
deterministic.

## Style

ASS subtitle style baked into the burn:

| Property      | Value                       | Why                          |
|---------------|-----------------------------|------------------------------|
| Font          | Inter, 44 pt                | Matches portfolio identity.  |
| Primary color | white `#FFFFFF`             | Max contrast on footage.     |
| Outline       | 3 px, ink `#0F1A1F`         | Legible over busy backdrops. |
| Shadow        | 2 px, 60 % opacity          | Rescues thin highlights.     |
| Margin V      | 84 px                       | Safe-area, mobile 9:16 safe. |
| Alignment     | 2 (bottom-center)           | Broadcast convention.        |

## Why it matters

- Captions are a hard requirement for accessibility (WCAG 2.2 1.2.2) and a soft
  requirement for most platforms' autoplay-muted feeds.
- Burning in is the simplest delivery path for internal Slack / Notion review
  where players don't pick up sidecars.
- For broadcast delivery, the same SRT can be muxed as a soft track
  (`ffmpeg -c:s mov_text`) or converted to `.ttml` / `.scc`.

## Run (offline default)

```bash
python3 scripts/python/auto_caption.py
```

## References

- Whisper: https://github.com/openai/whisper
- SRT spec (de-facto): https://www.matroska.org/technical/subtitles.html#srt-subtitles
- ffmpeg `subtitles` filter: https://ffmpeg.org/ffmpeg-filters.html#subtitles-1
- WCAG 2.2 Captions: https://www.w3.org/WAI/WCAG22/Understanding/captions-prerecorded.html
