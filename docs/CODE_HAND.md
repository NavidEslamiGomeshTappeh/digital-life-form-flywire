# Code Hand

## Purpose

`CodeHand` is the first concrete Hand implementation in the project. It provides a narrow, guarded interface for creating a source file inside an explicit workspace and executing explicit Python assertions against that generated file.

The Hand is intentionally smaller than a general-purpose coding agent. It does not claim to edit arbitrary remote repositories, browse the web, install software, or operate a user's desktop.

## Execution path

```text
CodeHand
  -> RunPlan
  -> PolicyGate
  -> CapabilityDoctor
  -> code.write / code.test.python
  -> Python backend
  -> checkpoint + sealed receipts
  -> independent verify_run()
```

Both operations are represented as ordinary task-plan steps, so they inherit the same dependency ordering, fail-closed policy, checkpoint/recovery, receipt sealing, and independent verification used by the Leader runtime.

## Workspace boundary

Code Hand accepts only relative paths and resolves them against the declared workspace root.

It rejects:

- absolute paths;
- `..` traversal outside the workspace;
- an existing target file (the first implementation is create-only).

The generated file's SHA-256 is checked again after execution against the requested source content.

## Permission boundary

`permission_granted` defaults to `false`.

A caller must explicitly grant permission for a write/test run. Network access and system mutation remain disabled by the default policy.

## Current capabilities

| Capability | Operation |
|---|---|
| `code.write` | Create one UTF-8 source file |
| `code.test.python` | Execute the generated Python file with explicit assertions |

Both currently use the real Python interpreter selected by the capability doctor.

## What is demonstrated

The CI Code Hand smoke test creates a real `code_hand_demo.py`, tests `add(2, 3) == 5` and `add(-2, 5) == 3`, prints both execution receipts, and independently verifies the two-step run.

The smoke-test file is created only in the ephemeral GitHub Actions workspace; it is not committed to `main`.

## Next boundary

A future Code Hand expansion can add structured edit/patch operations, language-specific test backends, repository-aware changes, and recovery of interrupted edits. Those should be added only with explicit path contracts, tests, receipts, and verifier coverage.
## Failure-injection evidence

The first end-to-end Code Hand smoke attempt intentionally exercised the real runner path and exposed two implementation defects: the generated inline Python source was encoded incorrectly, and the orchestrator did not fail closed when a step returned a non-success receipt. The source-generation path was corrected, the orchestrator now records the failed step and raises ExecutionError, and a regression test covers that failure boundary.

This is retained as engineering evidence: a green test result is not treated as proof until an observed failure mode has also been handled and regression-tested.
