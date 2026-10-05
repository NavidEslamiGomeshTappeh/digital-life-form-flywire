# Digital Life Form — public project overview

## What is this?

Digital Life Form — FlyWire is a research-engineering project that turns selected public FlyWire/FAFB data and external model integrations into inspectable, reproducible evidence.

The project is **provenance-first**: source identity, hashes, receipts, tests, implementation, and scientific boundaries stay connected so results can be audited rather than merely demonstrated.

## What is already evidenced?

- Four exact FAFB v783 reference neurons with immutable root IDs.
- 649/649 synapse-coordinate reproduction against the recorded official Codex product.
- 75/75 directed-pair correspondence against the recorded official Codex connections product.
- Four exact project SWC morphologies and deterministic published subtree-selection reproduction.
- Historical Point_data artifact provenance, with the original producer explicitly left unresolved.
- Pinned FlyVis v1.2.0 runtime evidence.
- A provenance-bearing visual-input boundary from gray8 frames into the pinned FlyVis BoxEye contract.
- CI and security automation that execute the project rather than treating README claims as proof.

## What is not claimed?

The project does not currently claim:

- exact biological electrical activity of the four FAFB roots from a camera;
- conversion of FlyVis continuous responses into biological spikes;
- automatic biological-compartment assignment from geometry alone;
- camera-driven biological control;
- recovery of the unpublished/private December 2025 Point_data producer.

These boundaries are part of the project design.

## How to inspect it

Start with [README.md](../README.md), then inspect `evidence/`, `tests/`, `src/dlf_flywire/`, `docs/`, and `.github/workflows/`.

Useful commands:

```bash
python -m dlf_flywire validate
python -m dlf_flywire audit
python -m dlf_flywire verify-sources
python -m dlf_flywire lineage
python -m pytest -q
```

## Current direction

The next boundary is real visual input: a physical camera can produce bounded, hashed gray8 frames locally and those frames can be rendered through the pinned FlyVis BoxEye interface. A physical-camera execution is only considered proven after a real device capture receipt exists; deterministic CI frames are not presented as hardware evidence.
