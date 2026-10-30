# First run / 第一次使用

Choose the path you need. You do not need to understand the JSON format to try a bundled story.

## Just see the result

Open the [three real-project stories](../examples/cases/README.md). Each includes Chinese/English images, a vertical strip, a share card and source notes. No local software needed to read them.

## Use it inside your Agent

```sh
npx skills add l422145205-source/commit-comic --skill commit-comic
```

Ask: “Use CommitComic to render the bundled completion-race example in Chinese.” In Codex you can invoke `$commit-comic` explicitly. The Agent should locate the installed Skill directory and call `scripts/commitcomic.py demo`, rather than ask you to fill JSON manually.

Next ask it to work on a local repository and an actual base/head range. The Agent selects one change, reads the source, writes a board and inspects the image before handing it back. **`draft` is a starting storyboard, not a finished explanation.**

## Try the tools from a download

From the downloaded repository directory, with Python 3.10+:

```sh
python scripts/commitcomic.py demo --out work/first-comic
```

This defaults to the English completion-race story. Add `--locale zh` for Chinese. Open `comic.svg` in the new output directory, or read `post.md`. The `demo` path does not read Git or contact the network.

For PNG/GIF, install `requirements-images.txt` in your chosen Python environment and pass `--images`. For Chinese raster output, a local CJK font is required; use `--font` if automatic selection fails. See [workflow](../references/workflow.md).

| If this happens | Do this |
| --- | --- |
| Output directory already exists | Choose a new directory; previous editions are preserved |
| Pillow is unavailable | Omit `--images`; SVG and text need only the standard library |
| Chinese raster font unavailable | Use SVG, or pass an installed CJK font with `--font` |
| Your project is not a local Git repository | Try a bundled case first; then supply an actual selected repository or a reviewed evidence packet |
| Result says no diff | Select a meaningful committed range; uncommitted work is intentionally excluded |
| Dialogue is generic or overflows | Ask the Agent to rewrite it around the actual change and shorten the words |

The demo renders a frozen reviewed case. It does not newly execute the historical source project or its experiments. [Report where you got stuck](https://github.com/l422145205-source/commit-comic/issues/new?template=try-it.yml).
