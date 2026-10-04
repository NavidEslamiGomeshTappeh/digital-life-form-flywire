# Digital Life Form — FlyWire

Version 1.3.1

> **Project continuity / canonical research memory:** [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)
>
> This is the first file to read when continuing the project in a new chat or agent session. It contains the current scientific boundaries, verified evidence, ecosystem research, architecture direction, unresolved items, and continuation rules.

Digital Life Form — FlyWire is a provenance-first research-engineering toolkit for extracting a small, exact subset of the FlyWire connectome and packaging the result as reproducible scientific evidence.

## Current validated core

Four exact FAFB v783 neurons:

| Cell | Root ID | VFB |
|---|---:|---|
| T4a | 720575940632008007 | VFB_fw077172 |
| T4c | 720575940616224414 | VFB_fw091869 |
| T5a | 720575940625571465 | VFB_fw056211 |
| T5c | 720575940617782941 | VFB_fw077474 |

The consolidated evidence contains 649 individual synapse-coordinate rows and 75 directed neuron pairs, with exact public-data reproduction, four exact SWC morphologies, published dendrite provenance, historical Point_data provenance, coordinate-frame boundaries, and a frozen Codex/Zenodo cross-source receipt contract tied to explicit proof executions.

## Scientific status

Proven:
- exact identity of all four reference roots;
- exact 649/649 reproduction against the official Codex FAFB v783 synapse-coordinate product;
- exact 75/75 pair-count correspondence against the official Codex FAFB v783 connections product;
- exact inclusion of all four roots in the published dendrite-analysis table;
- deterministic reproduction of the published subtree-selection algorithm on the project SWCs;
- exact historical Point_data Git-blob and SHA-256 provenance;
- the documented historical/public toolchain temporal boundary.

Unresolved:
- bitwise identity of project SWCs with unpublished internal study morphology;
- the original December 2025 Point_data generator implementation;
- a common coordinate transform between study-native and project-native frames;
- direct biological compartment assignment for an individual synaptic cleft.

Geometry is never promoted to biological truth by proximity alone.

### Latest coordinate/provenance audit — 2026-10-04

A deeper reconstruction now tests both the committed SWC parent roots and the roots selected by the published subtree algorithm. Neither reproduces the historical Point_data roots by the documented nm-to-um division alone. The public NeuRosetta import_swc implementation also explicitly declares units without rescaling coordinates; rescaling is a separate convert_units operation. The public align_forest path performs centering/PCA rotation, not an implicit scale.

The public Zenodo data release contains metric pickles (point_data, vertex_data, edge_data, etc.) but does not expose the Reduced_dendrites or .nr intermediate trees needed to compare the historical root nodes directly. The associated software release contains PP1–PP5 and Metrics1_Point_data, but it was published on 2026-08-10, long after the December 2025 Point_data artifact.

An empirical four-point similarity fit from the project SWC subtree roots to the recorded Point_data roots reaches about 9.6 µm RMS residual with a fitted scale of about 2.7055. This is recorded strictly as INFERENCE_ONLY: no historical source or code currently establishes that transform as the one used to generate Point_data.

Therefore the exact December 2025 producer, intermediate morphology materialization, coordinate transform, and execution environment remain UNRESOLVED.

A separate public legacy NeuRosetta repository predates the artifact and contains subtree selection, simplified-to-full root mapping, and explicit coordinate transformation/scaling functions. This makes it a technically plausible predecessor path, but no inspected record binds it to the December 2025 execution; it is therefore contextual evidence, not recovered provenance.

## Repository layout

src/dlf_flywire/   installable Python package
tests/             canonical regression suite
data/morphology/   four exact reference SWCs
evidence/          consolidated machine-readable evidence
docs/              current scientific and engineering documentation
scripts/           small operational entry points
.github/           CI, security, agents and issue templates

Historical V-numbered working files are intentionally removed from the V1 working tree. Their Git history remains available for audit.

## Install

The core package has no third-party runtime dependencies.

```bash
python -m pip install -e ".[dev]"
```

## Audit the evidence chain

The project exposes two complementary checks:

```bash
python -m dlf_flywire validate
python -m dlf_flywire audit
```

`validate` checks the scientific baseline and morphology invariants. `audit` additionally checks the machine-readable claim ledger, artifact identities, and version consistency.

The claim ledger is at [evidence/claims.json](evidence/claims.json), with artifact fingerprints in [evidence/artifact_manifest.json](evidence/artifact_manifest.json). The record-level lineage index is [evidence/synapse_lineage.json](evidence/synapse_lineage.json), with a deterministic builder at [scripts/build_synapse_lineage.py](scripts/build_synapse_lineage.py). CI also regenerates the index and requires byte-for-byte equality with the committed artifact.

## Verify the cross-source chain

For the four-neuron FAFB v783 case, the repository also exposes a frozen-receipt validator:

```bash
python -m dlf_flywire verify-sources
python -m dlf_flywire lineage
```

This checks the 649-row canonical artifact against immutable Codex and Zenodo verification receipts, including provider-level independence, dataset-release consistency, exact match counts, and the canonical SHA-256. It does **not** re-download the approximately 9.5 GB Zenodo source, so a PASS means the recorded frozen evidence is internally consistent, not that a new live re-run was performed.

## Validate

The `lineage` command validates all 649 record IDs, canonical row references, Codex/Zenodo receipt bindings, and the unresolved biological-compartment boundary.


```bash
python -m dlf_flywire validate
python -m pytest -q
```

## Recover exact morphology

V1.1.0 recovery reads the public FAFB v783 Neuroglancer precomputed skeleton endpoint directly and writes SWC without the vulnerable `fafbseg → diskcache` dependency chain.

```bash
dlf-flywire recover --dataset 783 --output data/morphology
```

Recovery fails closed on malformed source data, unsupported skeleton layouts, and source-root/output validation errors.

## Security

Workflow actions are pinned to immutable commit SHAs. CodeQL and OpenSSF Scorecard run in CI. V1.1.0 also removes the vulnerable transitive DiskCache dependency from the core installation path.

## License

Original project code is MIT licensed. Third-party data remain governed by upstream terms.
