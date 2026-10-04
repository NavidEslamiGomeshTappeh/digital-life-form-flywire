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

A repository-level DAG audit now makes the publication boundary more precise. The paper repository was initialized at 2025-12-09T19:26:04Z; the first analysis notebook was added at 19:40:07Z and already read `/home/nik/Desktop/Software/T45_Morpho_data/Data/Pickled_data/Point_data.pkl`. The same `Point_data.pkl` blob (`b85caf49f45677f2075f7b5f2c8830141cd96d02`) was then added in two parallel commits at 19:41:50Z and 19:42:19Z, sharing the same parent and tree, and merged at 19:42:30Z without changing the tree. The public `Neuron_ids.csv` did not appear until 2025-12-16. This is strong evidence that the December artifact was ingested as an already-existing output; it does **not** recover the producer that created it, which remains outside the exposed public repository history or in an unexposed local/private environment.

The published paper documents two manual review boundaries that matter for our morphology comparison: the neuron root at the soma is manually verified/corrected before automated subtree selection, and the selected dendritic subtree is then manually verified for completeness with individual routing/skeletonization errors correctable through the GUI. Therefore, an exact match of the automatically selected root node is not sufficient to establish identity of the final historical morphology. The paper separately documents global population alignment and individual PCA/scaling as downstream geometry operations; none is silently promoted here as the December 2025 Point_data transform. The machine-readable method evidence is recorded in `evidence/public_method_boundary.json`.

The archived Zenodo `Submission_release` (2026-01-16) independently confirms this publication boundary: it contains `Point_data.pkl` and the downstream analysis files, but its archive listing does not contain PP1–PP5 or the `Reduced_dendrites/` intermediate forest. This strengthens the conclusion that the public release preserves the derived product while omitting the upstream morphology materialization; it does not prove the producer never existed.

The V230 bridge is now explicit: the canonical 649-row synapse-coordinate table contains 62 endpoint root IDs and 75 directed pairs. All four Point_data anchor roots occur in it, but the remaining endpoints are partner neurons. Because Point_data is one row per dendrite and the V230 artifact is one row per synapse coordinate, their relationship is an anchor-ID bridge only; no historical morphology/run-level join key has been recovered.

The software-family history is now also mapped separately from artifact identity. A public `Neurosetta_old` repository dates to 2023 and contains graph-based simplification and rotation/eigen-axis code; the public `Neurosetta_legacy_v0.0.1` history adds explicit transformation/scaling in 2024, subtree selection in April 2025, and a simplified-root-to-full-neuron mapping fix in July 2025. This makes the family technically plausible as a predecessor path, but the December Point_data artifact is still not cryptographically bound to any one of those commits. The current public PySide6 GUI and manual-subtree GUI operation enter `NikDrummond/NeuRosetta` in April 2026; its initial GUI-port commit explicitly refers to an older GUI, whose public source was not recovered in the targeted search. The public `NeuRosetta` repository itself was initialized on 2025-10-21 with only `.gitignore`, `LICENSE.md`, and `README.md`; its first code-bearing commit is `f2d8778` on 2026-01-20, and its first public Forest implementation is `2f4e52c` on 2026-01-26. Thus the current public `NeuRosetta` tree is temporally excluded as the complete December 2025 producer; unpublished/local code remains possible.

The runtime history has a matching boundary: the first public `conda-environment.yml` was added on 2026-01-16 as `T45_paper` and does not declare NeuRosetta. The contemporaneous December notebook instead records a `neurosetta` Jupyter kernel. This confirms that the later release environment cannot be used to claim an exact December software installation.

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

## Run a verified task plan

The executable agent-runtime layer can run a JSON plan without writing Python code. Each step must declare its capability, action, destination, risk tier, and explicit permission. By default, network access and system mutation are denied by the policy gate.

Example:

```json
{
  "steps": [
    {
      "step_id": "inspect",
      "capability": "runtime.python",
      "action": "run a bounded local inspection",
      "destination": "local-process",
      "risk_tier": 0,
      "permission_granted": true,
      "operation_args": ["-c", "print('ok')"],
      "idempotent": true
    }
  ]
}
```

Run it with:

```bash
dlf-flywire run-plan plan.json --run-id my-run
```

The command resumes successful steps from verified receipts and returns exit code zero only when the independent run verifier reports `PASS`.

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
