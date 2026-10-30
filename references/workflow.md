# From a Git range to a shareable update

## 1. Scope and collect

Use the repository the user selected, not the entire workspace. Resolve a release pair, an explicit commit pair or the last recorded edition. The first collection needs `--base`; later `--ledger` can supply the prior head. The base must be an ancestor of head. This format uses direct snapshot differences, not GitHub's three-dot PR comparison.

The collector reads up to 60 commit subjects and 30 supported file diffs by default; bounds can be explicitly adjusted within CLI limits. It does not fetch/pull, check out files, execute source code, run hooks/tests, collect authors/emails, or read remote URLs. Optional `--project-url` accepts only a plain `https://github.com/owner/repo` supplied for this task; collection doesn't establish that a private repository is public.

Evidence is the **net diff** between endpoints, so a feature later reverted isn't presented from its old commit message alone. History is useful context for intent. A merge, squash or partial/truncated range still requires inspection before claiming causality. Large blobs, binary data, symlinks/submodules and some sensitive paths are excluded. Coverage states what was omitted; it isn't complete semantic analysis.

For an unavailable local repo, use an explicitly supplied packet matching the documented schema; do not invent commit IDs or imply a pasted description has been verified as Git evidence.

## 2. Add a scoped check only when one exists

```sh
python <skill-dir>/scripts/commitcomic.py attach-check --packet <packet.json> --log <unittest.log> --label "local demo fixture" --out <packet-with-check.json>
```

This reads one supplied unittest summary. It never executes the log's commands. Suite status and number run are separate; skipped tests aren't described as successful test cases. A missing/ambiguous summary is unknown, not passed. Mixed failure indicators produce a failed status. Other test frameworks and performance measurements need separate source review rather than being forced into this parser.

The record keeps a SHA-256 of the original log and a concise summary, not the full raw log. A supplied log isn't authenticated proof that the user ran it in a particular environment. The Agent must state its scope and not upgrade a fixture result into production impact.

## 3. Author a small story

Use `draft`, then read and rewrite the words. Choose one meaningful change. Keep a compact problem, the relevant clue, what actually changed, and a result/limitation. A valid draft is not automatically a good comic. Source IDs link panels to excerpts; the Agent still checks whether the interpretation is faithful.

For Chinese layout, aim for panel titles under 18 characters, bubbles under about 35 characters and captions around 50 characters. English should also be short. The renderer rejects overflow rather than silently clipping. A long technical explanation belongs in `post.md` or accompanying prose, not a tiny speech balloon.

## 4. Render and inspect

Default exports use only Python standard library: editable `comic.svg`, `strip.svg`, `card.svg`; `post.md`, `alt-text.txt`, `evidence.md`, `manifest.json`. SVGs have no external image/font requests or scripts. Text uses local font fallbacks.

Optional `--images` requires Pillow, declared in `requirements-images.txt`. Use the host's permitted dependency environment or a task-local virtualenv when needed. The Skill does not require a new model/image API. Chinese PNG/GIF needs a CJK font; pass a local font via `--font` if automatic detection fails. Do not bundle a proprietary font with a public output. The SVG and copy remain usable without raster dependencies.

PNG mode adds `comic.png` (1540×1500), `strip.png` (1000×2920), `card.png` (1200×1200) and `preview.gif`. The GIF progressively reveals the four panels; it is an illustrated preview, not an Agent or application recording. A short source label travels with each panel. Full excerpts and coverage belong in the accompanying notes.

The output folder must be new. Inspect readability, layout, wording, redactions and source references. The manifest binds original input hashes and exported file hashes (excluding its own self-hash). Rendering may mask additional common text patterns and records the count. No output is sent or published by the helper.

## 5. Continue an edition series

`record` stores one canonical board per edition. An exact repeated edition doesn't add a row or change the file; a changed board with the same ID fails. Use a new edition ID for a revised deliverable, but an ongoing sequence must continue from the prior head. Language variants are output variants of that edition; don't register the second language as a new range.

A ledger belongs to the repository's root-commit fingerprint. Forks with identical history can share that fingerprint; use separate ledgers when they are separate editorial projects. The file is local and contains no remote synchronization or publishing action. Sidecar locks coordinate this helper; they aren't a database lock against unrelated editors. Do not remove another process's lock.

## Sharing responsibly

The collector's common-pattern masking and excluded-file list are aids, not a complete secret/identity scanner. Review both illustrations and source notes before sharing private project material. Source notes can contain code even when the comic itself looks harmless. Public demonstrations should use original synthetic inputs unless the specific real material is approved for disclosure.
