# Compact packet and storyboard format

All JSON inputs use `format: commit-comic/1`. File size is capped at 3 MB; IDs use letters, digits, `_.-` up to 80 characters. Monetary/customer/owner records are not part of this format. See the original synthetic inputs in [assets](../assets/packet.example.json).

## Evidence packet

`project`, optional plain GitHub `project_url`, `repository_id` (root-commit fingerprint), full Git `base`/`head`, `commits[]`, `evidence[]`, `coverage`, `basis`.

`commits[]` contains SHA and sanitized subject only. It is contextual intent; the evidence used for implemented behavior is the endpoint net diff.

Each evidence row has a stable `id`, a `kind`, `text` and source note:

- `net_diff`: relative `path`, Git status, exact `base`/`head`, bounded excerpt and `truncated` flag.
- `check`: local label, `status` (`passed`, `failed`, `unknown`), number `count` run, optional skipped count, concise text, original-log SHA-256 and source qualification. This parser handles one unittest summary, not arbitrary CI/performance formats.
- `record`: selected text from a reviewed, fixed source file, with relative `path`, exact `ref` equal to the packet head, original `file_sha256`, pinned `source_url` and scope note. Used by the bundled historical project cases; it is not a check execution. Do not attach a fabricated unittest summary to report numeric fields.

Optional `source_url` must pin a GitHub file or commit to a full SHA within `project_url`. It is a clickable provenance link; tools do not follow it or use it as execution authority. The bundled real cases use root-commit fingerprints from their complete public histories, matching local collector identity. Their coverage includes only the selected patch excerpts and frozen records, not every changed file.

Coverage reports range/included commit counts, changed/included/excluded path counts, truncated diffs and common-pattern redaction counts. `net_diff_empty` describes endpoint snapshots even if history contains several commits. A subset isn't evidence about excluded files.

## Storyboard

Required fields: `packet_sha256`, `edition`, `locale` (`zh` or `en`), `title`, `subtitle`, exactly four `panels`. Optional theme `pop`/`night`, optional author notice.

The packet SHA is calculated from canonical sorted UTF-8 JSON using SHA-256. Whitespace changes are harmless; changed evidence requires review and a refreshed binding.

Panel order is `problem`, `clue`, `change`, `result`. Each has:

| Field | Meaning |
| --- | --- |
| `beat` | Narrative position |
| `title` | Short panel heading, up to 40 chars; layout can reject an oversized line |
| `bubble` | Authored speech, up to 100 chars; render bounds are intentionally tighter |
| `caption` | Context, up to 180 chars; shorten for layout |
| `scene` | Original vector scene: `duplicate`, `inspect`, `repair`, `check`, `handoff`, `race`, `snapshot`, `schedule`, `audio`, `fingerprint`, `audio-check`, `reuse`, `artifact`, `crash`, `gate`, `recover` |
| `evidence[]` | One or more existing evidence IDs |
| `mode` | `summary` (interpretation), `quote` (literal source text) or `check` |
| `check_id` | Required for `check`; must reference a cited check row |

A quote's bubble must occur literally in a cited excerpt. Check mode adds a standardized line from the referenced summary. Source references and hashes do not prove the prose semantically faithful. There is no automatic claim of deployment, performance, model accuracy, adoption or human approval.

## Edition ledger

Local `format`, `repository_id`, `last_head`, `editions[]`. Each edition stores its stable ID, input packet/board hashes and range. Replays are no-ops, conflicting IDs fail and subsequent editions must continue the last head. A new destination/range should use its own ledger. Register one canonical language version and retain translations as output variants.

The helper uses an exclusive sidecar lock and atomic replacement for its own ledger writes. This doesn't coordinate unrelated editors or provide distributed transactions. No ledger is uploaded automatically.
