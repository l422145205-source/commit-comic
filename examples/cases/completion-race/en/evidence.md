# Evidence notes / 来源说明

Git range: `c1a0c9133df2c18263df200f40c46924abdf7c57..b73e054995e373de35a9d40a96ea5c86e5420a8a`

Panel references prove a source link, not semantic faithfulness, deployment or user impact.

## Panel 1 / summary

Sources: E2

### E2

src/reelpilot/supervisor.py

[Pinned public source](https://github.com/l422145205-source/reelpilot/commit/b73e054995e373de35a9d40a96ea5c86e5420a8a)

Reviewed excerpt of a public GitHub parent-to-commit diff. Selected files only; no new execution implied.

    @@ -53,12 +53,10 @@ def run_isolated(
     
                 def check():
                     nonlocal completed_at
    -                if ticket.completed_by_self():
    +                if ticket.worker_state() == "complete":
                         completed_at = completed_at or time.monotonic()
                         if time.monotonic() - completed_at > 5:
                             raise TimeoutError("completed worker cleanup exceeded grace")
    -                else:
    -                    ticket.guard()
     
                 code = child.wait(check=check, timeout=3605)
                 if child.stdout.total > 65536:

## Panel 2 / summary

Sources: E1, E2

### E1

src/reelpilot/admission.py

[Pinned public source](https://github.com/l422145205-source/reelpilot/commit/b73e054995e373de35a9d40a96ea5c86e5420a8a)

Reviewed excerpt of a public GitHub parent-to-commit diff. Selected files only; no new execution implied.

    @@ -24,6 +24,7 @@
         guard_request,
         terminal_status,
         requested_error,
    +    guard_row,
     )
     
     
    @@ -190,6 +191,19 @@ def completed_by_self(self):
                 row = db.execute("SELECT owner,status FROM submissions WHERE job=?", (self.job,)).fetchone()
             return bool(row and row["owner"] == self.owner and row["status"] == "complete")
     
    +    def worker_state(self):
    +        with self.admission.journal.connect() as db:
    +            row = db.execute(
    +                "SELECT owner,status,lease_until,cancel_requested,cancel_at,deadline "
    +                "FROM submissions WHERE job=?",
    +                (self.job,),
    +            ).fetchone()
    +        if row and row["owner"] == self.owner and row["status"] == "complete":
    +            return "complete"
    +        self.admission.journal.runtime_check()
    +        guard_row(row, self.owner)
    +        return "active"
    +
         def _update(self, status, phase, error=None):
             now = time.time()
             with self.admission.journal.connect() as db:

### E2

src/reelpilot/supervisor.py

[Pinned public source](https://github.com/l422145205-source/reelpilot/commit/b73e054995e373de35a9d40a96ea5c86e5420a8a)

Reviewed excerpt of a public GitHub parent-to-commit diff. Selected files only; no new execution implied.

    @@ -53,12 +53,10 @@ def run_isolated(
     
                 def check():
                     nonlocal completed_at
    -                if ticket.completed_by_self():
    +                if ticket.worker_state() == "complete":
                         completed_at = completed_at or time.monotonic()
                         if time.monotonic() - completed_at > 5:
                             raise TimeoutError("completed worker cleanup exceeded grace")
    -                else:
    -                    ticket.guard()
     
                 code = child.wait(check=check, timeout=3605)
                 if child.stdout.total > 65536:

## Panel 3 / summary

Sources: E1, E2

### E1

src/reelpilot/admission.py

[Pinned public source](https://github.com/l422145205-source/reelpilot/commit/b73e054995e373de35a9d40a96ea5c86e5420a8a)

Reviewed excerpt of a public GitHub parent-to-commit diff. Selected files only; no new execution implied.

    @@ -24,6 +24,7 @@
         guard_request,
         terminal_status,
         requested_error,
    +    guard_row,
     )
     
     
    @@ -190,6 +191,19 @@ def completed_by_self(self):
                 row = db.execute("SELECT owner,status FROM submissions WHERE job=?", (self.job,)).fetchone()
             return bool(row and row["owner"] == self.owner and row["status"] == "complete")
     
    +    def worker_state(self):
    +        with self.admission.journal.connect() as db:
    +            row = db.execute(
    +                "SELECT owner,status,lease_until,cancel_requested,cancel_at,deadline "
    +                "FROM submissions WHERE job=?",
    +                (self.job,),
    +            ).fetchone()
    +        if row and row["owner"] == self.owner and row["status"] == "complete":
    +            return "complete"
    +        self.admission.journal.runtime_check()
    +        guard_row(row, self.owner)
    +        return "active"
    +
         def _update(self, status, phase, error=None):
             now = time.time()
             with self.admission.journal.connect() as db:

### E2

src/reelpilot/supervisor.py

[Pinned public source](https://github.com/l422145205-source/reelpilot/commit/b73e054995e373de35a9d40a96ea5c86e5420a8a)

Reviewed excerpt of a public GitHub parent-to-commit diff. Selected files only; no new execution implied.

    @@ -53,12 +53,10 @@ def run_isolated(
     
                 def check():
                     nonlocal completed_at
    -                if ticket.completed_by_self():
    +                if ticket.worker_state() == "complete":
                         completed_at = completed_at or time.monotonic()
                         if time.monotonic() - completed_at > 5:
                             raise TimeoutError("completed worker cleanup exceeded grace")
    -                else:
    -                    ticket.guard()
     
                 code = child.wait(check=check, timeout=3605)
                 if child.stdout.total > 65536:

## Panel 4 / summary

Sources: E3

### E3

tests/test_runtime_control.py

[Pinned public source](https://github.com/l422145205-source/reelpilot/commit/b73e054995e373de35a9d40a96ea5c86e5420a8a)

Reviewed excerpt of a public GitHub parent-to-commit diff. Selected files only; no new execution implied.

    @@ -230,3 +230,56 @@ def test_postcommit_cleanup_error_is_observable_without_rewriting_completion(tmp
         assert q.get("job")["status"] == j.get("job")["status"] == "complete"
         event = next(e for e in j.get("job")["events"] if e["event"] == "postcommit_error")
         assert "ProcessCleanupError" in event["detail"]
    +
    +
    +def test_supervisor_completion_race_uses_one_state_snapshot(tmp_path, monkeypatch):
    +    from contextlib import contextmanager
    +
    +    for name, legacy in [("legacy-peek", True), ("single-snapshot", False)]:
    +        j, q, t, owner = linked(tmp_path, name)
    +        partial = j.root / (name + ".partial")
    +        partial.write_text("{}")
    +        target = j.root / (name + ".json")
    +        original = j.connect
    +        injected = [False]
    +
    +        @contextmanager
    +        def connect():
    +            with original() as db:
    +
    +                class Proxy:
    +                    def execute(self, sql, args=()):
    +                        cursor = db.execute(sql, args)
    +                        if (
    +                            sql.startswith("SELECT owner,status")
    +                            and "FROM submissions" in sql
    +                            and not injected[0]
    +                        ):
    +
    +                            class OneRow:
    +                                def fetchone(self):
    +                                    row = cursor.fetchone()
    +                                    injected[0] = True
    +                                    # Commit completion after the observer has read
    +                                    # its snapshot, before it validates/acts on it.
    +                                    j.finalize(name, owner, partial, target)
    +                                    return row
    +
    +                            return OneRow()
    +                        return cursor
    +
    +                    def __getattr__(self, key):
    +                        return getattr(db, key)
    +
    +                yield Proxy()
    +
    +        with monkeypatch.context() as patch:
    +            patch.setattr(j, "connect", connect)
    +            if legacy:
    +                assert not t.completed_by_self()
    +                with pytest.raises(BusyJob):
    +                    t.guard()  # Reproduce the old two-read bug.
    +            else:
    +                assert t.worker_state() == "active"
    +                assert t.worker_state() == "complete"
    +        assert injected[0] and q.get(name)["status"] == "complete"

