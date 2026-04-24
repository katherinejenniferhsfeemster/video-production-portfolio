# OpenShot OSP + OpenTimelineIO Builder

Same source of truth as the Shotcut `.mlt` project, but emitted in two
additional interchange formats so the cut can be opened in OpenShot or handed
off to any NLE that speaks [OpenTimelineIO](https://opentimelineio.readthedocs.io/).

## What the script produces

`scripts/python/build_openshot_osp.py` generates:

- `scripts/projects/portfolio.osp` — OpenShot's native JSON project, with a
  1080p30 `profile`, one `files` entry per curated clip, a single `tracks`
  layer, and `clips` placed end-to-end with a 0.5 s `effects` overlap for
  cross-dissolves.
- `scripts/projects/portfolio.otio` — OpenTimelineIO `Timeline` with one
  `Track` of kind `Video`, each clip as `ExternalReference`, plus a second
  track for the 1 kHz audio. Round-trips through `otiotool` and opens in
  Resolve / Hiero via their OTIO adaptors.

## Why two formats

- **`.osp`** is required for OpenShot users who want a hand-editable project.
- **`.otio`** is the universal interchange — reviewers on Resolve, Hiero, Flame
  or custom tools get the same cut without re-importing rushes.

Both are generated from the same Python model, so they stay in lock-step.

## Run

```bash
python3 scripts/python/build_openshot_osp.py \
  --clips assets/data/curated/manifest.csv \
  --osp scripts/projects/portfolio.osp \
  --otio scripts/projects/portfolio.otio
```

Inspect the OTIO on the command line:

```bash
otiotool -i scripts/projects/portfolio.otio --stats
```

## Why it matters

- AI research teams often split responsibilities: the editor cuts in OpenShot,
  the visualization lead reviews in Resolve, QA plays it in VLC. OTIO is the
  lingua franca that removes "it doesn't open on my machine".
- A JSON-based OpenShot project is easy to post-process: redaction, bulk
  renaming of assets, stripping proxies, inserting slate.

## References

- OpenShot project format (source): https://github.com/OpenShot/libopenshot
- OpenTimelineIO docs: https://opentimelineio.readthedocs.io/
- OTIO adaptors (Resolve, Hiero, FCP X XML): https://github.com/AcademySoftwareFoundation/OpenTimelineIO#adapters
