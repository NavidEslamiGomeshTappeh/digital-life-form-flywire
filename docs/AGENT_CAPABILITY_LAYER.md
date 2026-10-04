# Agent Capability Layer — Architectural Reference

## Purpose

This document records the external architectural reference and the implementation decisions it informed in Digital Life Form.

It is **not** a vendored dependency, not a fork, and not a claim that Agent Reach has been integrated into the product.

## External reference

Repository: `Panniantong/Agent-Reach`

Inspected main commit:

`a19a171fa980a0785849596492e0af4db800c82f`

Observed release version in that tree:

`1.5.0`

The inspected implementation is an internet capability layer around upstream tools. Its central design separates:

`capability -> health check -> ordered backend candidates -> active backend -> direct upstream execution`

## Patterns worth adopting

### 1. Capability is higher-level than implementation

A capability should describe **what the system can do**, while an adapter/backend describes **how it currently does it**.

For Digital Life Form this maps naturally to:

- `web.read`
- `github.read`
- `source.materialize`
- `morphology.recover`
- `evidence.validate`
- future `computer.execute`

The capability contract should remain stable even when the backend changes.

### 2. Backend choice is ordered and observable

Agent Reach represents backends as an ordered candidate list and exposes the backend actually selected after health checking.

Our implemented capability doctor records the equivalent contract:

- capability name;
- candidate backends in priority order;
- probe result for each candidate;
- selected backend;
- reason for selection;
- fallback path if the preferred backend fails.

The selected backend must never be inferred merely from configuration or command existence.

### 3. Health probes must execute something safe

The inspected `probe_command()` distinguishes:

- missing;
- broken;
- timeout;
- error;
- healthy.

This is stronger than `which()` or file existence.

Digital Life Form should use the same principle for external execution boundaries:

`not installed != installed but broken != installed and healthy`

Health probes must be side-effect-free and bounded by a timeout.

### 4. One failing capability must not destroy the whole health report

Agent Reach's doctor collects each channel independently and converts channel exceptions into an error result instead of aborting the complete report.

Our capability doctor returns a complete report even when one backend probe crashes.

### 5. User overrides may reorder candidates, not disable safety

The Agent Reach backend override moves a named backend to the front without allowing an unknown backend to hide the known candidates.

For Digital Life Form:

- explicit backend choice may change priority;
- unknown backends are ignored or rejected;
- the verifier still validates the actually executed backend;
- a forced backend does not bypass policy/risk checks.

### 6. Capability health is a snapshot

A doctor result is evidence about a point in time, not a permanent truth.

Our execution receipts carry:

- probe timestamp;
- capability state;
- selected backend;
- environment identity where available;
- execution timestamp;
- final result.

### 7. Keep capability routing separate from execution

A particularly useful boundary is that the capability layer does not become a giant wrapper for every underlying service.

For Digital Life Form the desired separation is:

`Leader -> capability router -> backend -> execution -> evidence -> Verifier`

not:

`Leader -> one monolithic wrapper that hides every tool`

This preserves inspectability and allows independent backend replacement.

### 8. Safe-by-default installation and configuration

Agent Reach separates checking from operations that modify the environment and provides dry-run behavior.

Our future Computer/Web Hand installation path should adopt:

- check-only by default;
- explicit authorization for system modification;
- dry-run before mutation;
- no credentials in repository artifacts;
- atomic/permission-safe local configuration;
- fail-closed behavior on uncertain security state.

## Patterns we should NOT copy blindly

Agent Reach is optimized for internet access. Digital Life Form is broader and has a scientific verification layer.

Therefore we should **not** copy its platform-channel model as the entire architecture.

Our system additionally needs:

`intent/risk policy -> capability selection -> execution -> checkpoint -> artifact receipt -> independent verification`

A web backend being healthy does not make the scientific result valid.

## Digital Life Form execution contract

The future capability layer should expose a machine-readable record conceptually equivalent to:

```text
CapabilityReceipt
  capability
  requested_action
  policy_decision
  candidate_backends[]
    backend
    probe_status
    probe_evidence
  selected_backend
  execution
    started_at
    finished_at
    status
    exit/result metadata
  inputs[]
    identity/hash
  outputs[]
    identity/hash
  checkpoint
    run_id
    step_id
    state_hash
  verification
    verifier
    status
    evidence
```

The local runtime now implements this contract in a bounded form: policy intent, capability probe, selected backend, execution result, checkpoint state, sealed receipt, and independent run verification.

## Relationship to the existing V1 evidence chain

The project already has:

`source -> artifact -> deterministic transformation -> independent validation -> claim status`

The capability layer should sit **before and around execution**, not replace the scientific evidence chain:

```text
Intent
  -> Policy / Risk Gate
  -> Capability Doctor
  -> Backend Selection
  -> Execution
  -> Checkpoint / Recovery
  -> Artifact + Execution Receipt
  -> Independent Verification
  -> Claim Ledger
```

This is the architectural bridge between the user's desired multi-hand agent system and the current provenance-first research core.

## Relationship to the planned multi-agent design

The mapping is:

| Agent role | Capability-layer responsibility |
|---|---|
| Leader | choose capability and route work |
| Code Hand | code/build backend |
| Computer Hand | local execution/backend control |
| Web Hand | external web/backend access |
| Verifier | challenge result, validate receipt, detect false PASS |
| Recovery layer | resume from latest valid checkpoint |

The important boundary is that **Leader selection must never become evidence by itself**. Only executed and verified receipts can support scientific claims. The current verifier also checks that the receipt intent exactly matches the immutable plan before returning PASS.

## Current decision

Adopt Agent Reach as an **architectural reference for capability discovery, real health probing, ordered backend fallback, safe configuration, and explicit active-backend reporting**.

Do not add Agent Reach as a runtime dependency to the current V1 scientific package.

Do not claim Web Hand or Computer Hand integrations exist until their real backends, tests, and receipts exist.

## Audit principle

The implemented runtime is judged against the same standard already used elsewhere in the project:

- exact inputs;
- deterministic behavior where applicable;
- explicit state transitions;
- failure injection;
- timeout/disconnect handling;
- recovery;
- prompt-injection boundary tests for web-facing agents;
- parallel-run isolation;
- inspectable receipts;
- independent verification;
- no hidden PASS state.
