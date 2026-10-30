# Three real-project stories / 三个真实项目故事

These stories come from the maintainer's public ReelPilot and VoxStage projects. Each board is authored from a fixed commit and selected evidence; none is external-user feedback. Images illustrate the implementation, not a live Agent recording. The historical experiments are not rerun when you render a comic.

| Story | 中文 | English | Source walkthrough |
| --- | --- | --- | --- |
| Completion versus supervision | [活干完了，我怎么反而掉线了？](completion-race/zh/comic.png) | [I finished. Why am I missing?](completion-race/en/comic.png) | [Read](completion-race/README.md) |
| Incremental audio editing | [只改一句，另外三句别加班。](one-line-edit/zh/comic.png) | [One line changed. Spare the other three.](one-line-edit/en/comic.png) | [Read](one-line-edit/README.md) |
| Filesystem / SQL publication gap | [文件都在了，为什么还不给下载？](publish-gap/zh/comic.png) | [The file exists. Why no download?](publish-gap/en/comic.png) | [Read](publish-gap/README.md) |

Each language directory contains `comic.svg/png`, `strip.svg/png`, `card.svg/png`, `preview.gif`, `post.md`, `alt-text.txt`, `evidence.md` and `manifest.json`.

## Start with a reviewed board

From a downloaded repository:

```sh
python scripts/commitcomic.py demo --case completion-race --out work/first-comic
```

Choose `one-line-edit` or `publish-gap`, add `--locale zh` for Chinese, or `--images` for optional PNG/GIF output. [First run](../../docs/first-run.md)

The reviewed packets live in [assets/cases](../../assets/cases/completion-race/packet.json). Source IDs link interpretations to excerpts; they do not independently certify semantic truth. Some patches are deliberately selected/truncated; coverage remains explicit.

For a completely original synthetic Git fixture with four real local checks, the [MoonNotes example](../README.md) remains available.
