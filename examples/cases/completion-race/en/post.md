# I finished. Why am I missing?

ReelPilot / completion lands between two supervisor reads

## 1. Done, then lost?

I finished! Why mark me lost?

The old supervisor checked completion, then ownership in a separate read.

## 2. Two reads, two states

Running first. No lease next.

Completion clears the lease between reads. The old guard raises.

## 3. One snapshot

Decide from the same row.

worker_state uses one row for completion and control validation.

## 4. Make the race happen

Force the timing. Then compare.

A forced transition makes the old check raise. The new check later sees completion.

---

Illustrated interpretation of code evidence; review the scope and evidence notes before posting.
