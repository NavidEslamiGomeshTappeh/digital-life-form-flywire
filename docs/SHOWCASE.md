# Digital Life Form — FlyWire: public showcase

## What is it?

**Digital Life Form — FlyWire** is a provenance-first research-engineering project exploring a narrow, reproducible path from exact connectome data to constrained neural-model execution and real visual input.

It deliberately separates **what is demonstrated** from **what is still a scientific hypothesis**.

## The strongest verified pieces

### 1. Exact connectome anchors

The current research baseline uses four exact FAFB v783 roots:

- T4a — `720575940632008007`
- T4c — `720575940616224414`
- T5a — `720575940625571465`
- T5c — `720575940617782941`

The consolidated public-data evidence records:

- **649/649** synapse-coordinate reproduction
- **75/75** directed neuron-pair correspondence
- four reference SWC morphologies

### 2. Reproducible model execution

The project pins its FlyVis integration to a specific upstream revision and records runtime evidence as immutable repository artifacts.

The important boundary is:

`input image → FlyVis BoxEye → continuous model response`

That is a model/runtime result. It is **not** presented as exact biological electrical activity.

### 3. Real visual input

The repository now contains a genuine physical-camera implementation:

`physical camera → gray8 VisionFrame → exact PGM → SHA-256 receipt → FlyVis BoxEye`

The camera implementation uses bounded OpenCV capture, releases the device on exit, and fails closed on capture/read/timeout errors.

The local command is:

`python -m pip install -e ".[vision]"`

then:

`dlf-flywire camera-flyvis --device 0 --frames 20 --output data/vision/camera-flyvis`

A successful local run is the evidence boundary for **actual hardware capture**. GitHub Actions cannot access a user's physical camera, so CI does not pretend otherwise.

### 4. Evidence before claims

The project treats these as separate states:

- **PROVEN** — backed by inspectable evidence and reproducible checks.
- **INFERENCE_ONLY** — a useful computational observation that is not historical/biological proof.
- **UNRESOLVED** — evidence is insufficient.
- **NOT CLAIMED** — intentionally outside the current proof boundary.

This is important because the project is trying to build a serious research trail, not a demo that quietly upgrades model output into biological fact.

## What is still open?

The public project still has important unresolved questions, including:

- exact bitwise identity of project SWCs with any unpublished internal study morphology;
- recovery of the original December 2025 Point_data generator;
- the historical coordinate transform used to create that artifact;
- direct biological compartment assignment for an individual synaptic cleft;
- proof of camera-driven activity at exact FAFB root level;
- biological control claims.

These are visible in the repository instead of being hidden behind a polished headline.

## How to inspect it yourself

From a clean checkout:

```bash
python -m pip install -e ".[dev]"
python -m dlf_flywire validate
python -m dlf_flywire audit
python -m pytest -q
```

For the source-chain receipts:

```bash
python -m dlf_flywire verify-sources
python -m dlf_flywire lineage
```

## Current vision work

The live implementation and CI work is tracked in **PR #59 — Add provenance-bearing real vision input boundary**.

The intended boundary is deliberately small:

**camera/image → immutable frame → provenance → BoxEye → FlyVis continuous response**

It does not grant the neural path permission to perform system mutation, network access, or biological control.

## Contribution mindset

The project favors:

1. exact identifiers over approximate labels;
2. deterministic computation over screenshots;
3. immutable hashes over unverifiable claims;
4. independent verification over self-attestation;
5. explicit failure and recovery paths;
6. scientific boundaries that remain visible.

If a result cannot be proven yet, the project records that fact and keeps working toward the missing evidence.
