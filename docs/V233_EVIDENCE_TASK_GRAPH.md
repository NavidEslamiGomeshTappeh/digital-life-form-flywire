# V233 — Evidence-Carrying Task Graph

V233 turns the existing research pipeline into a resumable dependency graph.

## Guarantees

- A task cannot run until every declared dependency is DONE.
- A task is DONE only when its registered executor returns PASS.
- A failed terminal dependency blocks downstream tasks; failure is never silently promoted.
- Unknown executor kinds fail closed.
- Python test execution uses an explicit script allowlist; arbitrary shell commands are not accepted.
- State is atomically checkpointed before and after each task.
- Every task result carries an output digest and the worker records a journal.
- A runner timeout leaves unfinished tasks resumable on the next invocation.

## Current graph

V229 exact roots -> V230 structure -> V231 fingerprint/ledger -> V231 evidence engine
and V231 target capsule -> V232 worker -> V231 audit.

This graph verifies engineering state. It does not convert the V230 biological provenance boundary into proof.

## Long-run execution

GitHub-hosted jobs have a finite execution ceiling. V233 therefore treats a workflow run as a compute slice, not as the research lifetime. The state file is persisted as an Actions artifact and can be restored by a later scheduled or manually dispatched run.

The scheduled runner intentionally uses a minute away from the top of the hour because GitHub documents that scheduled events can be delayed under high load.

## State integrity

The state digest covers the task table and recent journal tail. The plan is immutable for an existing task ID: changing its kind, dependencies, payload, or retry budget causes a hard failure instead of silently changing the meaning of prior evidence.
