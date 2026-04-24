# AI Dataset Video Curation

Turning raw, heterogeneous footage into a versioned, deduplicated and
normalized training set. The pipeline is idempotent — re-running it on new
footage only adds new rows to the manifest.

## Problem

AI research programs collect footage from many sources: drone captures, screen
recordings, phone clips, archive stock. Training on that raw pile leads to two
classes of bugs:

1. **Duplicate or near-duplicate shots** inflate easy classes and bias the model.
2. **Container / codec / fps drift** breaks downstream decoding (especially when
   a model's data loader expects constant-rate frames).

## Approach

Single-pass Python script, `scripts/python/curate_dataset.py`, that:

1. **Probes** each clip with `ffprobe` (container, codec, fps, duration, size).
2. **Detects scenes** via [PySceneDetect](https://scenedetect.com/) `ContentDetector`
   at threshold 27. One row per scene, not per file.
3. **Deduplicates** via 8×8 **average hash (aHash)** of the scene midpoint
   frame, with a Hamming-distance threshold of 8 (conservative).
4. **Normalizes** survivors to 1080p / 30 fps / yuv420p / AAC 48 kHz using
   `ffmpeg -vf scale=1920:1080,fps=30 -c:v libx264 -pix_fmt yuv420p -c:a aac`.
5. **Writes a manifest**: `assets/data/curated/manifest.csv` with
   `source, scene_idx, start, end, ahash, duration, resolution, fps, status`.

## Output

- `assets/data/curated/*.mp4` — normalized scenes.
- `assets/data/curated/manifest.csv` — deterministic, reviewable in git.
- `assets/data/curated/rejected.csv` — the duplicates / failed probes, for audit.

## Why it matters for an AI research team

- The manifest is **diffable** — a reviewer can see exactly which scenes entered
  training and which were dropped, which is not possible when curation is done
  by hand in an NLE.
- aHash is intentionally cheap; it catches the "same b-roll imported twice"
  case without needing a GPU. For semantic dedup you'd layer a CLIP-based pass
  on top — hook point is already in the script (`dedup_strategy` argument).
- Normalization to a single profile means data loaders (FFCV, DALI, torchcodec)
  never hit a surprise container.

## Run

```bash
python3 scripts/python/curate_dataset.py \
  --input assets/data \
  --output assets/data/curated
```

## References

- PySceneDetect docs: https://scenedetect.com/
- aHash method: "Kind of Like That" by Neal Krawetz, HackerFactor 2011.
- EBU R128 for loudness normalization (paired with caption pipeline): https://tech.ebu.ch/docs/r/r128.pdf
