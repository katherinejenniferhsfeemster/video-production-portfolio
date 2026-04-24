# Lightworks EDL Export + Editorial LUT

Finishing hand-off: a CMX-3600 EDL that Lightworks (or DaVinci Resolve, Avid,
Premiere) can import, a plain-text shotlist for producers, and a matching 33pt
`.cube` LUT so the look survives the round-trip.

## What the script produces

`scripts/python/export_lightworks_edl.py` emits three files into
`scripts/projects/`:

- **`portfolio.edl`** — CMX-3600 with `FCM: NON-DROP FRAME`, numbered events,
  reel names truncated to 8 characters, source TC and record TC aligned to a
  30 fps timeline, dissolves written as `C` + `D` pairs with explicit length.
- **`portfolio.shotlist.tsv`** — one row per event: `event, reel, clip, src_in,
  src_out, rec_in, rec_out, duration, transition, note`. Opens cleanly in
  Excel / Numbers / Google Sheets for a producer review.
- **`editorial.cube`** — 33×33×33 LUT that pushes midtones toward the portfolio
  palette (teal `#2E7A7B` shadows, amber `#D9A441` highlights). Header declares
  `LUT_3D_SIZE 33` and `DOMAIN_MIN/MAX` as required by Resolve / Nuke / Lightworks.

## Why EDL, not just OTIO

EDL is ancient (CMX-3600 dates from 1982) but it is the **most compatible**
timeline hand-off in the industry. Every finishing tool speaks it. For
archival delivery and for vendor finishers who still run Avid / Lightworks
seats, an EDL is the safe choice.

The OTIO file in [`../openshot-osp-builder/`](../openshot-osp-builder/) covers
modern pipelines; the EDL covers the long tail.

## Run

```bash
python3 scripts/python/export_lightworks_edl.py \
  --clips assets/data/curated/manifest.csv \
  --edl scripts/projects/portfolio.edl \
  --shotlist scripts/projects/portfolio.shotlist.tsv \
  --lut scripts/projects/editorial.cube
```

## Apply the LUT with ffmpeg

```bash
ffmpeg -i in.mp4 \
  -vf "lut3d=scripts/projects/editorial.cube" \
  -c:v libx264 -crf 18 out.mp4
```

## Why it matters

- An EDL plus a shotlist plus a LUT is exactly the package a finishing vendor
  expects. It cuts the back-and-forth of "what's the look supposed to be?".
- The LUT is generated, not hand-crafted in Resolve — reviewable in a PR and
  deterministic for CI.

## References

- CMX-3600 EDL spec (unofficial but widely used): https://xmil.biz/EDL-X/CMX3600.pdf
- Adobe `.cube` LUT format: https://wwwimages2.adobe.com/content/dam/acom/en/products/speedgrade/cc/pdfs/cube-lut-specification-1.0.pdf
- Lightworks import guide: https://lwks.com/
