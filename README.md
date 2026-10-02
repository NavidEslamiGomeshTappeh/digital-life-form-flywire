# Digital Life Form — FlyWire

> **A provenance-first attempt to reconstruct and validate a small visual microcircuit from the public FlyWire connectome.**
>
> **Current scientific status:** V229 morphology recovery is documented; V230 contains a 649-row synapse-coordinate artifact; V231 now gives that artifact a reproducible structural fingerprint. **Biological provenance of the 649 rows is still unverified.**

[![V229 verification](https://github.com/mafiabax/digital-life-form-flywire/actions/workflows/v229-verification.yml/badge.svg)](https://github.com/mafiabax/digital-life-form-flywire/actions/workflows/v229-verification.yml)

## What is unusual about this repository

This project treats **evidence as part of the implementation**. A code test is not counted as biological proof, an inferred threshold is not recorded as a fact, and a matching-looking neuron is not accepted as the requested neuron.

The central challenge is falsifiable:

**Can the checked-in V230 coordinates be independently recovered from the canonical FAFB v783 release, row for row, without guessing?**

The repository now contains the machinery to answer that question.

## Current milestones

| Milestone | State |
|---|---|
| V229 exact-root morphology recovery pipeline | Implemented |
| V230 649-row structural validation | Implemented |
| V230 provenance audit | Implemented; provenance is **UNVERIFIED** |
| V230 exact coordinate probe against FAFB v783 | Implemented; awaiting source-file execution |
| V230 pair-level probe against proofread v783 connections | Implemented; awaiting source-file execution |
| V231 reproducible structural fingerprint | Implemented and CI-tested |

## V231 structural fingerprint

V231 turns the V230 artifact into a machine-checkable target: canonical SHA-256, row/coordinate counts, neuron-pair counts, bidirectionality, self-loops, connected components and degree distributions.

Run:

    python scripts/v231_circuit_fingerprint.py

See docs/V231_STRUCTURAL_FINGERPRINT.md.

## Research principle

The project deliberately separates:

**observed data → reproducible computation → source match → biological interpretation**

No missing stage is silently promoted to a stronger claim.

## V229 FlyWire skeleton recovery

This repository contains the recovery runner for four exact FlyWire v783 neuron skeletons. It is designed to fail closed: a similar or guessed neuron is never accepted as a substitute.

| Cell | FlyWire root ID | VFB ID |
|---|---:|---|
| T4a | 720575940632008007 | VFB_fw077172 |
| T4c | 720575940616224414 | VFB_fw091869 |
| T5a | 720575940625571465 | VFB_fw056211 |
| T5c | 720575940617782941 | VFB_fw077474 |

Recovery order: fafbseg/FlyWire → MRC precomputed → Zenodo bulk.

## Evidence

`v229_results/V229_recovery_report.json` contains recorded external-data recovery evidence for all four requested cells. It records node counts, structural validation, finite geometry and SHA-256 hashes.

Software tests are not treated as proof of external-data recovery. Those are separate evidence levels.

## Run

    python -m py_compile v229_recovery_runner.py
    python test_v229_recovery_runner.py
    python v229_recovery_runner.py --route all --out v229_results --cache v229_cache

## Validation

A recovered SWC must contain nodes, exactly one structural root, no missing parent references and finite geometry. The source neuron's real ID must match the requested root before serialization.

## V230 synapse artifact — provenance audit

`v230_results/V230_target_synapses.csv` is a checked-in artifact with 649 rows, 33 unique presynaptic roots, 38 unique postsynaptic roots and 75 unique pre/post pairs. All four V229 target roots occur as postsynaptic roots, but the artifact also contains 34 other postsynaptic roots.

The repository history proves that this CSV was introduced in commit `e57b1ccc5b9f64964af223b6bf8e853579985fe0`, whose message is `V229 FlyWire morphology recovery and V230 synapse coordinates`. That proves repository provenance, not scientific provenance.

The current repository does **not** contain the extraction script, source-data filename/record, query/filter code, or a reproducible command that generated the 649 rows. Therefore the following are **not established facts**:

- that the 649 rows were queried directly from FlyWire v783;
- that every row is one real biological synapse;
- that `x,y,z` are postsynaptic coordinates, presynaptic coordinates, or a particular synapse-coordinate field;
- that the apparent minimum of 5 rows per pre/post pair came from a deliberate `>=5` synapse threshold;
- that the artifact is complete for the four target neurons;
- that the 649 rows are sufficient to reconstruct the V230 circuit.

The data pattern is compatible with a pair-level selection followed by expansion to coordinate rows: every observed pair has 5–21 rows and all 649 coordinate triplets are unique. This is an **observation/inference, not provenance evidence**.

See `v230_results/V230_validation.json` for the machine-readable audit. Structural validation of the CSV is intentionally labeled `STRUCTURE_ONLY`, not biological PASS.

## V230 exact provenance route

The repository now includes `scripts/v230_zenodo_exact_probe.py`. It compares every V230 `(pre_root_id, post_root_id, x, y, z)` row against both coordinate sides in a local copy of the canonical public FAFB v783 `flywire_synapses_783.feather` release.

The canonical public Zenodo release is 9.5 GB and has MD5 `f8f1b97c9d4b0ea9b4c8b287f6b99091`. It contains pre/post root IDs and separate pre/post XYZ coordinates. The smaller 852 MB `proofread_connections_783.feather` can validate pair-level connectivity/counts but cannot validate individual coordinate rows.

Codex's current static-download API documents an `api_token` requirement for programmatic downloads. Therefore this repository does not claim that the Codex API route is token-free.

Example after obtaining the canonical Feather file:

    python scripts/v230_zenodo_exact_probe.py /path/to/flywire_synapses_783.feather

An `EXACT_MATCH` result would establish exact membership of the 649 V230 rows in the public FAFB v783 synapse release and identify whether V230 coordinates are pre- or post-synaptic. It would not prove the historical extraction command or completeness.

## Project status

V229 is a morphology-recovery milestone. V230 is currently a **provenance-unverified synapse-coordinate artifact**. The project does not claim from this CSV alone that it has recovered a verified set of 649 biological synapses or a complete T4/T5 connectivity circuit.

## License

No open-source license has been asserted. Normal copyright rules apply unless the project owner adds a license.

## Command reference

Show version:

    python v229_recovery_runner.py --version

Recover one target:

    python v229_recovery_runner.py --route 1 --only T4a --out v229_results --cache v229_cache

The runner's default output directory is `v229_recovery_results`; examples above explicitly use the repository evidence directory `v229_results`.
