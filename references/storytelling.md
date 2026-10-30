# Make the update worth reading

## Pick a change with a visible consequence

Find the user's audience: other developers, a project's users, teammates or a general technical audience. Good candidates include a reproducible bug, a user-facing capability with concrete boundaries, or a surprising implementation constraint. A cosmetic or internal refactor can still be a story; don't invent a user pain or performance gain to make it dramatic.

For a weekly devlog, select a highlight and keep other changes in the accompanying post. For a release, distinguish newly supported behavior, fixes, compatibility notes and pending verification. For teaching, make the synthetic/demonstration scope explicit. A commit prefix such as `fix:` is a hint to inspect, not enough to certify a repair.

## Four beats

1. **Problem** — one recognizable situation grounded in old behavior. “I retried once” is clearer than “idempotency constraints were not enforced”.
2. **Clue** — the idea that makes the fix intelligible. Show why comparing event identity differs from comparing text.
3. **Change** — what the code now does, with the important caveat. Avoid drowning the speech in framework names.
4. **Result** — a scoped observation or honestly stated verification gap. Changed tests are not test execution, and a passing fixture isn't evidence of production impact.

Use the original monitor character, note and bug as illustrative actors. Their dialogue is authored narration unless explicitly in `quote` mode; don't attribute fictional speech to real maintainers or users. Source labels and notes should make the distinction clear.

## Tone and variants

- **Light bug story**: a little surprise, then a clear explanation. Keep the defect's consequences proportional to evidence.
- **Calm project update**: what changed, why it matters within the supplied scope, and what remains to verify.
- **Technical lesson**: a minimal before/after example, the governing concept and its limits.
- **Bilingual share**: adapt the sentence lengths for each layout. Keep the same source packet; don't add stronger claims in translation.

Palette choices are `pop` and `night`. Match scenes to the actual story: `handoff/race/snapshot/schedule` for state observation, `audio/fingerprint/audio-check/reuse` for incremental audio work, and `artifact/crash/gate/recover` for publication boundaries; `duplicate/inspect/repair/check` remain general introductory options. These are deterministic vector templates, not an image model generating arbitrary scenes. Custom art can be created with a host's appropriate visual tools when requested, while preserving source review and truthful captions.

## A quick editorial review

Can someone understand the problem from the first panel? Does the second panel explain a real clue? Does the third describe the implemented change rather than a plan? Is the final result supported and scoped? Is the joke easy to read without treating a fictional character as a real testimonial?

Don't optimize for dramatic claims by fabricating speedups, adoption, stars or user reactions. No tool checks whether a piece is “viral”; validate engagement with real voluntary feedback if available.
