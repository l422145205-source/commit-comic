# Evidence notes / 来源说明

Git range: `2e1a94e5572e4ec375a7914bb4e183247d0d42ba..ba3d650556124b206682ee2eec361148f52fb779`

Panel references prove a source link, not semantic faithfulness, deployment or user impact.

## Panel 1 / summary

Sources: E1, E2

### E1

src/reelpilot/journal.py

[Pinned public source](https://github.com/l422145205-source/reelpilot/commit/ba3d650556124b206682ee2eec361148f52fb779)

Reviewed excerpt of a public GitHub parent-to-commit diff. Selected files only; no new execution implied.

    +    def finalize(self, job, owner, temporary: Path, destination: Path, *, checkpoint=None):
    +        """Linearize completion against cancel using the same SQLite write lock.
    +
    +        A process death after rename but before commit may leave an unacknowledged
    +        file. The API does not serve it until the database completion is committed.
    +        This is process-crash recovery, not a filesystem/DB power-loss transaction.
    +        """
    +        if not temporary.resolve().is_relative_to(self.root) or not destination.resolve().is_relative_to(
    +            self.root
    +        ):
    +            raise ValueError("final publication escapes job storage")
    +        with self.connect() as db:
    +            db.execute("BEGIN IMMEDIATE")
    +            row = self._owned(db, job, owner)
    +            temporary.replace(destination)
    +            if checkpoint is not None:
    +                checkpoint("result_replaced_before_commit")
    +            self._owned(db, job, owner)
    +            now = time.time()
    +            db.execute(
    +                "UPDATE jobs SET owner=NULL,lease_until=0,status='complete',error=NULL,updated=? "
    +                "WHERE id=? AND owner=?",
    +                (now, job, owner),
    +            )
    +            if row["request_owner"] is not None:
    +                db.execute(
    +                    "UPDATE submissions SET status='complete',phase='complete',lease_until=0,error=NULL,updated=? "
    +                    "WHERE job=? AND owner=?",
    +                    (now, job, row["request_owner"]),
    +                )
    +                db.execute(
    +                    "INSERT INTO events(job,event,detail,at) VALUES (?,?,?,?)",
    +                    (job, "request_complete", "atomic finalization", now),
    +                )
    +

### E2

tests/test_process_runtime.py

[Pinned public source](https://github.com/l422145205-source/reelpilot/commit/ba3d650556124b206682ee2eec361148f52fb779)

Reviewed excerpt of a public GitHub parent-to-commit diff. Selected files only; no new execution implied.

    +def test_hard_kill_recovers_verified_render_without_serving_uncommitted_result(real_library, tmp_path, point):
    +    journal = Journal(tmp_path / "jobs")
    +    queue = Admission(journal, ttl=1, interval=0.15)
    +    body = {"brief": {"text": "forest;robot", "budget_seconds": 8}, "mode": "lexical", "provider": "explicit"}
    +    old = queue.reserve("crash", body, timeout_seconds=30)
    +    old.start()
    +    child = OwnedProcess([sys.executable, "-B", str(HELPER), point], gated=True, env=source_env())
    +    try:
    +        child.send(
    +            (
    +                json.dumps(
    +                    {
    +                        "job_id": "crash",
    +                        "owner": old.owner,
    +                        "request": body,
    +                        "parent_pid": os.getpid(),
    +                        "jobs": str(journal.root),
    +                        "collection": str(real_library.root),
    +                        "lease": {"ttl": 1, "interval": 0.15},
    +                    }
    +                )
    +                + "\n"
    +            ).encode()
    +        )
    +        wait_for(lambda: marker(journal.root / "crash/fault-marker.json"))
    +        assert child.process.poll() is None
    +        old.stop()  # Simulate the API admission heartbeat dying with its server.
    +        killed = time.monotonic()
    +        child.close()  # OS hard kill, no Python exception handler/finally.
    +        assert process_exited(child.process.pid)
    +        assert (journal.root / "crash/result.json").exists() == (point == "result_replaced_before_commit")
    +        assert journal.get("crash")["status"] == "running"  # Uncommitted SQL rolled back.
    +        wait_for(lambda: queue.get("crash")["status"] == "interrupted", seconds=3)
    +        expired = time.monotonic()
    +        with TestClient(create_app(real_library.root, journal.root)) as c:
    +            assert c.get("/api/jobs/crash/output").status_code == 409
    +            assert "result" not in c.get("/api/jobs/crash").json()
    +        new = queue.reserve("crash", body, timeout_seconds=30)
    +        new.start()
    +        try:
    +            run_isolated(new, body, real_library)
    +            new.finish()
    +        finally:
    +            new.stop()
    +        assert journal.get("crash")["status"] == queue.get("crash")["status"] == "complete"
    +        render = next(s for s in journal.get("crash")["stages"] if s["stage"] == "render")
    +        assert render["attempts"] == 1
    +        with pytest.raises(BusyJob):
    +            old.guard()
    +        evidence(
    +            tmp_path,
    +            {
    +                "case": point,
    +                "fault": "OS hard kill",
    +                "expiry": "elapsed request lease",
    +                "lease_wait_seconds": expired - killed,
    +                "recovery_seconds": time.monotonic() - expired,
    +                "render_commits": render["attempts"],
    +                "uncommitted_result_served": False,
    +                "status": queue.get("crash")["status"],
    +            },
    +        )
    +    finally:
    +        old.stop()
    +        child.close()
    +
    +

## Panel 2 / summary

Sources: E1, E2

### E1

src/reelpilot/journal.py

[Pinned public source](https://github.com/l422145205-source/reelpilot/commit/ba3d650556124b206682ee2eec361148f52fb779)

Reviewed excerpt of a public GitHub parent-to-commit diff. Selected files only; no new execution implied.

    +    def finalize(self, job, owner, temporary: Path, destination: Path, *, checkpoint=None):
    +        """Linearize completion against cancel using the same SQLite write lock.
    +
    +        A process death after rename but before commit may leave an unacknowledged
    +        file. The API does not serve it until the database completion is committed.
    +        This is process-crash recovery, not a filesystem/DB power-loss transaction.
    +        """
    +        if not temporary.resolve().is_relative_to(self.root) or not destination.resolve().is_relative_to(
    +            self.root
    +        ):
    +            raise ValueError("final publication escapes job storage")
    +        with self.connect() as db:
    +            db.execute("BEGIN IMMEDIATE")
    +            row = self._owned(db, job, owner)
    +            temporary.replace(destination)
    +            if checkpoint is not None:
    +                checkpoint("result_replaced_before_commit")
    +            self._owned(db, job, owner)
    +            now = time.time()
    +            db.execute(
    +                "UPDATE jobs SET owner=NULL,lease_until=0,status='complete',error=NULL,updated=? "
    +                "WHERE id=? AND owner=?",
    +                (now, job, owner),
    +            )
    +            if row["request_owner"] is not None:
    +                db.execute(
    +                    "UPDATE submissions SET status='complete',phase='complete',lease_until=0,error=NULL,updated=? "
    +                    "WHERE job=? AND owner=?",
    +                    (now, job, row["request_owner"]),
    +                )
    +                db.execute(
    +                    "INSERT INTO events(job,event,detail,at) VALUES (?,?,?,?)",
    +                    (job, "request_complete", "atomic finalization", now),
    +                )
    +

### E2

tests/test_process_runtime.py

[Pinned public source](https://github.com/l422145205-source/reelpilot/commit/ba3d650556124b206682ee2eec361148f52fb779)

Reviewed excerpt of a public GitHub parent-to-commit diff. Selected files only; no new execution implied.

    +def test_hard_kill_recovers_verified_render_without_serving_uncommitted_result(real_library, tmp_path, point):
    +    journal = Journal(tmp_path / "jobs")
    +    queue = Admission(journal, ttl=1, interval=0.15)
    +    body = {"brief": {"text": "forest;robot", "budget_seconds": 8}, "mode": "lexical", "provider": "explicit"}
    +    old = queue.reserve("crash", body, timeout_seconds=30)
    +    old.start()
    +    child = OwnedProcess([sys.executable, "-B", str(HELPER), point], gated=True, env=source_env())
    +    try:
    +        child.send(
    +            (
    +                json.dumps(
    +                    {
    +                        "job_id": "crash",
    +                        "owner": old.owner,
    +                        "request": body,
    +                        "parent_pid": os.getpid(),
    +                        "jobs": str(journal.root),
    +                        "collection": str(real_library.root),
    +                        "lease": {"ttl": 1, "interval": 0.15},
    +                    }
    +                )
    +                + "\n"
    +            ).encode()
    +        )
    +        wait_for(lambda: marker(journal.root / "crash/fault-marker.json"))
    +        assert child.process.poll() is None
    +        old.stop()  # Simulate the API admission heartbeat dying with its server.
    +        killed = time.monotonic()
    +        child.close()  # OS hard kill, no Python exception handler/finally.
    +        assert process_exited(child.process.pid)
    +        assert (journal.root / "crash/result.json").exists() == (point == "result_replaced_before_commit")
    +        assert journal.get("crash")["status"] == "running"  # Uncommitted SQL rolled back.
    +        wait_for(lambda: queue.get("crash")["status"] == "interrupted", seconds=3)
    +        expired = time.monotonic()
    +        with TestClient(create_app(real_library.root, journal.root)) as c:
    +            assert c.get("/api/jobs/crash/output").status_code == 409
    +            assert "result" not in c.get("/api/jobs/crash").json()
    +        new = queue.reserve("crash", body, timeout_seconds=30)
    +        new.start()
    +        try:
    +            run_isolated(new, body, real_library)
    +            new.finish()
    +        finally:
    +            new.stop()
    +        assert journal.get("crash")["status"] == queue.get("crash")["status"] == "complete"
    +        render = next(s for s in journal.get("crash")["stages"] if s["stage"] == "render")
    +        assert render["attempts"] == 1
    +        with pytest.raises(BusyJob):
    +            old.guard()
    +        evidence(
    +            tmp_path,
    +            {
    +                "case": point,
    +                "fault": "OS hard kill",
    +                "expiry": "elapsed request lease",
    +                "lease_wait_seconds": expired - killed,
    +                "recovery_seconds": time.monotonic() - expired,
    +                "render_commits": render["attempts"],
    +                "uncommitted_result_served": False,
    +                "status": queue.get("crash")["status"],
    +            },
    +        )
    +    finally:
    +        old.stop()
    +        child.close()
    +
    +

## Panel 3 / summary

Sources: E2

### E2

tests/test_process_runtime.py

[Pinned public source](https://github.com/l422145205-source/reelpilot/commit/ba3d650556124b206682ee2eec361148f52fb779)

Reviewed excerpt of a public GitHub parent-to-commit diff. Selected files only; no new execution implied.

    +def test_hard_kill_recovers_verified_render_without_serving_uncommitted_result(real_library, tmp_path, point):
    +    journal = Journal(tmp_path / "jobs")
    +    queue = Admission(journal, ttl=1, interval=0.15)
    +    body = {"brief": {"text": "forest;robot", "budget_seconds": 8}, "mode": "lexical", "provider": "explicit"}
    +    old = queue.reserve("crash", body, timeout_seconds=30)
    +    old.start()
    +    child = OwnedProcess([sys.executable, "-B", str(HELPER), point], gated=True, env=source_env())
    +    try:
    +        child.send(
    +            (
    +                json.dumps(
    +                    {
    +                        "job_id": "crash",
    +                        "owner": old.owner,
    +                        "request": body,
    +                        "parent_pid": os.getpid(),
    +                        "jobs": str(journal.root),
    +                        "collection": str(real_library.root),
    +                        "lease": {"ttl": 1, "interval": 0.15},
    +                    }
    +                )
    +                + "\n"
    +            ).encode()
    +        )
    +        wait_for(lambda: marker(journal.root / "crash/fault-marker.json"))
    +        assert child.process.poll() is None
    +        old.stop()  # Simulate the API admission heartbeat dying with its server.
    +        killed = time.monotonic()
    +        child.close()  # OS hard kill, no Python exception handler/finally.
    +        assert process_exited(child.process.pid)
    +        assert (journal.root / "crash/result.json").exists() == (point == "result_replaced_before_commit")
    +        assert journal.get("crash")["status"] == "running"  # Uncommitted SQL rolled back.
    +        wait_for(lambda: queue.get("crash")["status"] == "interrupted", seconds=3)
    +        expired = time.monotonic()
    +        with TestClient(create_app(real_library.root, journal.root)) as c:
    +            assert c.get("/api/jobs/crash/output").status_code == 409
    +            assert "result" not in c.get("/api/jobs/crash").json()
    +        new = queue.reserve("crash", body, timeout_seconds=30)
    +        new.start()
    +        try:
    +            run_isolated(new, body, real_library)
    +            new.finish()
    +        finally:
    +            new.stop()
    +        assert journal.get("crash")["status"] == queue.get("crash")["status"] == "complete"
    +        render = next(s for s in journal.get("crash")["stages"] if s["stage"] == "render")
    +        assert render["attempts"] == 1
    +        with pytest.raises(BusyJob):
    +            old.guard()
    +        evidence(
    +            tmp_path,
    +            {
    +                "case": point,
    +                "fault": "OS hard kill",
    +                "expiry": "elapsed request lease",
    +                "lease_wait_seconds": expired - killed,
    +                "recovery_seconds": time.monotonic() - expired,
    +                "render_commits": render["attempts"],
    +                "uncommitted_result_served": False,
    +                "status": queue.get("crash")["status"],
    +            },
    +        )
    +    finally:
    +        old.stop()
    +        child.close()
    +
    +

## Panel 4 / summary

Sources: R1

### R1

reports/runtime_fault_validation.json

[Pinned public source](https://github.com/l422145205-source/reelpilot/blob/ba3d650556124b206682ee2eec361148f52fb779/reports/runtime_fault_validation.json)

Source file SHA-256: `3da8c4ba19d3f9dfef6f8a4aef72672616f43d73fe0a48eff0c7a77ccc713a5a`

Selected JSON fields from the pinned historical report; original file hash retained. Not a newly executed result or external-user feedback.

    {
      "date": "2026-10-26",
      "case": {
        "case": "result_replaced_before_commit",
        "fault": "OS hard kill",
        "expiry": "elapsed request lease",
        "lease_wait_seconds": 0.9537455000099726,
        "recovery_seconds": 0.8624342999974033,
        "render_commits": 1,
        "uncommitted_result_served": false,
        "status": "complete"
      },
      "coverage_notes": [
        "real media, SQLite and HTTP handlers; no models loaded",
        "crash recovery waits for actual request lease expiry; no manual lease SQL edit",
        "deadline during FFmpeg is set to now+0.25s after startup, then expires by elapsed time",
        "queued deadline expires by elapsed time without SQL edits",
        "slow FFmpeg entry point is a trusted test worker; production supervisor is unchanged",
        "unit tests also cover synthetic lease states and blocked model doubles",
        "process-crash tests do not establish disk-power-loss atomicity or production scale"
      ]
    }

