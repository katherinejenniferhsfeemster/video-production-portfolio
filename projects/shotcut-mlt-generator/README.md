# Shotcut MLT Project Generator

Programmatically build a valid Shotcut `.mlt` project from a list of clips and
cue points. No manual dragging of clips onto the timeline — the project opens,
plays and exports identically on every machine.

## Why generate the project file

Shotcut's `.mlt` is just an XML document produced by the
[MLT Framework](https://www.mltframework.org/). Anything the GUI does — tracks,
filters, transitions, dynamic text — is available as XML nodes. Generating the
file is strictly more reliable than UI automation.

## What the script produces

`scripts/python/build_shotcut_mlt.py` emits `scripts/projects/portfolio.mlt`
with:

- `<profile>` locked to 1920×1080, 30 fps, progressive, square pixels.
- Three `<producer>` nodes for the curated clips.
- A main `<playlist>` and a `<tractor>` with an audio + video track.
- `dynamicText` filters on each segment for lower-thirds (clip name + tc).
- A `brightness` filter on the intro producer to ramp from black.
- A final `fadeOut` filter for the outro.

Open the resulting file in Shotcut 22.06 or newer — Edit → Properties works
just like a hand-built project.

## Why it matters

- **Version control**: `.mlt` is plain XML, so cuts are reviewable in PRs.
- **Parameter sweeps**: a producer can swap in a different LUT, title, or
  transition by changing one Python argument. Great for A/B rendering of
  dataset teasers.
- **Cross-machine determinism**: the profile is pinned, so no surprise 23.976
  fps imports.

## Run

```bash
python3 scripts/python/build_shotcut_mlt.py \
  --clips assets/data/curated/manifest.csv \
  --output scripts/projects/portfolio.mlt
```

## Open in Shotcut

```bash
shotcut scripts/projects/portfolio.mlt
```

## References

- MLT XML schema: https://www.mltframework.org/docs/mltxml/
- Shotcut user handbook: https://shotcut.org/bin/view/Shotcut/HowTos
- `dynamicText` filter reference: https://www.mltframework.org/plugins/FilterDynamictext/
