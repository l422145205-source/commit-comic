# One retry. Two notes. What happened?

MoonNotes / a repair story with traceable evidence

## 1. Double trouble

I only clicked retry!

The previous importer appended a second note on replay.

## 2. Follow the clue

Same event. Same ID.

Two distinct events can share text; text alone is not an event ID.

## 3. Patch the replay

Changed content? Stop.

Same ID and content: skip. Conflicting content: reject and preserve the note.

## 4. Result and limits

Let the checks speak.

Local checks on this original demo fixture; no production-impact claim.

4 run / suite passed

---

Illustrated interpretation of code evidence; review the scope and evidence notes before posting.
