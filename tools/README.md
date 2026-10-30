# Reproduce the example

For the easiest first try, render a reviewed real-project case with `python scripts/commitcomic.py demo --case completion-race --out work/first-comic`. This needs no Git/network/model and does not rerun the historical experiment. To render all three cases, use `python tools/render_cases.py --out work/cases --locale both --images` (optional image dependencies apply). [Case sources](../examples/cases/README.md). The original synthetic Git reproduction follows.

Use Python 3.10+ and Git. The helper creates an **original synthetic** note-import repository, commits its before/after states using a synthetic noreply identity, runs four small tests it authored, collects the actual diff, renders the comic and records the edition twice. It does not read another repository or publish anything.

Run from the downloaded repository directory. Output directories must be new:

```sh
python tools/reproduce.py --out work/repro --locale en
```

To generate PNG/GIF too, install optional dependencies in your chosen Python environment:

```sh
python -m pip install -r requirements-images.txt
python tools/reproduce.py --out work/repro-images --locale both --images
```

Chinese raster output requires a local CJK font. Automatic candidates cover Windows Microsoft YaHei, Linux Noto Sans CJK and macOS PingFang; use `--font /path/to/local-font.ttc` for another installed font. Proprietary fonts are not bundled. Without Pillow, omit `--images` and use SVG/text output.

The demo writes:

```text
work/repro/
  fixture/              original local Git demo, never uploaded
  demo-check.log        actual four-test execution output
  packet.json           net diffs and scoped check summary
  board.en.json         authored storyboard (zh too when requested)
  en/                   comic, strip, card, copy, sources, manifest
  editions.json         one canonical edition; repeat was a no-op
  verification.json     execution summary and scope
```

The example's commit IDs are reproducible from the fixed synthetic history; the raw test log includes timing and its hash can vary across runs. Rendered raster bytes may also vary with fonts/Pillow. Use each run's manifest to check its own files rather than demanding cross-platform byte-identical PNGs.

## Render the included reviewed boards

This does not require a new Git fixture:

```sh
python scripts/commitcomic.py validate --packet assets/packet.example.json --board assets/board.en.example.json
python scripts/commitcomic.py render --packet assets/packet.example.json --board assets/board.en.example.json --out work/from-example
```

Add `--images` to `render` for raster exports. A new directory prevents accidental overwrite of an earlier edition.

## Run the tool tests

```sh
python -m unittest discover -s tests -v
```

The 28 tests include temporary original Git fixtures and all bundled reviewed boards. They cover net diffs and reverted changes, identity omission/common-pattern redaction, literal filenames/renames, bounded collection, storyboard binding, quotes/check summaries, pinned record sources, SVG escaping/output hashes, no-overwrite behavior, edition continuity, and the first-run CLI from a different working directory. They do not execute arbitrary user code. CI repeats these, the synthetic Git workflow and all three English case renders on Linux and Windows.

For your own project, follow [the workflow](../references/workflow.md); collection reads committed changes only and does not verify production outcomes. Do not publish its evidence notes until that specific code material is approved for disclosure.
