# Evidence notes / 来源说明

Git range: `6ba257030ab3b928b15ac9b0506b76cc3c17cc8c..fcd0e40027f482b7ee14851359acac0aa280e328`

Panel references prove a source link, not semantic faithfulness, deployment or user impact.

## Panel 1 / summary

Sources: E1

### E1

notes.py

    diff --git a/notes.py b/notes.py
    index cf53294..63eccbd 100644
    --- a/notes.py
    +++ b/notes.py
    @@ -1,3 +1,10 @@
     def import_note(notes, event_id, content):
    +    if not event_id:
    +        raise ValueError("An event ID is required")
    +    for note in notes:
    +        if note["id"] == event_id:
    +            if note["content"] != content:
    +                raise ValueError("Conflicting content for the same event")
    +            return False
         notes.append({"id": event_id, "content": content})
         return True

## Panel 2 / summary

Sources: E1

### E1

notes.py

    diff --git a/notes.py b/notes.py
    index cf53294..63eccbd 100644
    --- a/notes.py
    +++ b/notes.py
    @@ -1,3 +1,10 @@
     def import_note(notes, event_id, content):
    +    if not event_id:
    +        raise ValueError("An event ID is required")
    +    for note in notes:
    +        if note["id"] == event_id:
    +            if note["content"] != content:
    +                raise ValueError("Conflicting content for the same event")
    +            return False
         notes.append({"id": event_id, "content": content})
         return True

## Panel 3 / summary

Sources: E1

### E1

notes.py

    diff --git a/notes.py b/notes.py
    index cf53294..63eccbd 100644
    --- a/notes.py
    +++ b/notes.py
    @@ -1,3 +1,10 @@
     def import_note(notes, event_id, content):
    +    if not event_id:
    +        raise ValueError("An event ID is required")
    +    for note in notes:
    +        if note["id"] == event_id:
    +            if note["content"] != content:
    +                raise ValueError("Conflicting content for the same event")
    +            return False
         notes.append({"id": event_id, "content": content})
         return True

## Panel 4 / check

Sources: C1

### C1

original synthetic MoonNotes fixture

    4 tests run; suite passed; 0 skipped; supplied log, scope: original synthetic MoonNotes fixture

