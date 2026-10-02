# Digital Life Form — FlyWire

> An auditable pipeline for turning exact FlyWire neuron IDs into reproducible circuit evidence and, eventually, biophysically usable neuron models.

## The problem

FlyWire already has strong tools for data access, annotations, morphology and connectivity. This project is aimed at a different problem:

**Given exact neuron root IDs, can we recover the exact cells, directed connections, individual synapse coordinates, morphology, and every transformation between those layers — with machine-checkable evidence?**

The intended reusable output is a **Circuit Evidence Pack**: a version-pinned bundle containing the exact roots, connections, synapses, morphology references, selection rules, hashes and validation results needed to reproduce the same circuit.

## Why this is different

This is deliberately **not another whole-brain animation or generic FlyWire viewer**.

The project treats provenance as part of the computational artifact:

source data
→ exact neuron identity
→ directed connectivity
→ individual synapse coordinates
→ exact morphology
→ synapse-to-compartment mapping
→ conductance-ready representation

A plausible-looking neuron, a matching count, or a successful simulation is not accepted as proof of biological provenance.

## Current evidence: V215 → V230

Four exact anchor neurons were fixed for the V215–V229 work:

| Cell | Root ID | VFB |
|---|---:|---|
| T4a | 720575940632008007 | VFB_fw077172 |
| T4c | 720575940616224414 | VFB_fw091869 |
| T5a | 720575940625571465 | VFB_fw056211 |
| T5c | 720575940617782941 | VFB_fw077474 |

V215 reports 52 direct real connection rows into those four targets. V218 later expanded the surrounding real graph to 10,396 depth-2 edges.

V230 contains:

- 649 coordinate rows
- 75 directed pre/post pairs
- 33 unique presynaptic roots
- 38 unique postsynaptic roots

The 75 pairs are now reproducibly reconstructed from the official Codex FAFB v783 connection table:

**one endpoint is one of the four anchor roots → group by directed pair → sum syn_count**

An independent GitHub Actions run scanned 3,869,878 source rows and reproduced 75/75 directed pairs and 649/649 total synapses.

The same 649 V230 coordinate rows were independently matched against the frozen FAFB v783 synapse release.

### Important provenance distinction

The original V230 producer script is **not preserved** in Git history.

The repository therefore distinguishes:

1. historical recovery of the original code;
2. deterministic reproduction of the historical output from the canonical source data.

The second is established for the current V230 artifact; the first is not.

## What the project is for

The practical user is a researcher who has a small, hypothesis-driven set of neurons and needs a trustworthy model input.

For example:

> Give me these exact neurons and this FlyWire snapshot, and return the exact circuit data used by the model, with enough evidence that another researcher can regenerate it.

The useful deliverable is not the words Digital Life Form. It is the **reproducible bridge between connectomics and downstream neural modeling**.

Possible downstream uses include circuit-hypothesis testing, compartmental simulation input generation, comparison of alternative biophysical assumptions on a fixed anatomical substrate, and reproducible sharing of a small circuit.

## What this project is not

It is not currently a claim to have reconstructed a complete biological fly brain.

There are already whole-brain FlyWire simulators, visualization projects, and mature FlyWire access libraries. This project should therefore compete on:

**exact identity + cross-layer traceability + reproducibility + simulation readiness**

rather than on another whole-brain demo.

## Next major milestone: V254 Circuit Evidence Pack

The next major engineering step is to turn the existing evidence into a reusable pipeline.

Input:
- exact root IDs
- dataset/version
- explicit selection policy

Output:
- exact cell identities and annotations
- directed connectivity
- individual synapse coordinates
- exact morphology
- synapse-to-compartment mapping
- provenance manifest
- hashes
- validation report
- regeneration command

The existing four-neuron V215–V230 circuit is the first real regression case. The new pipeline must reproduce established evidence before adding deeper electrophysiology.

## Useful entry points

- v230_results/V230_target_synapses.csv — 649-row V230 artifact
- v230_results/V230_validation.json — machine-readable validation/provenance record
- scripts/v251_codex_connection_count_provenance.py — exact pair-count validation
- scripts/v253_v230_pair_selection_provenance.py — exact reconstruction of the 75-pair selection
- docs/V230_PROVENANCE_CONSOLIDATED.md — consolidated V230 provenance
- docs/PROJECT_POSITIONING.md — project purpose and scope
- v229_recovery_runner.py — exact-root morphology recovery

## Reproducibility rule

The project separates:

**observed data → deterministic computation → source match → biological interpretation**

An inferred rule is not silently promoted to historical fact. A computational assumption is not presented as measured biology. A retrieval failure is not replaced with a plausible substitute.

## Ecosystem

The project builds on existing FlyWire infrastructure rather than replacing it:

- FlyConnectome / FlyWire annotations
- Codex FAFB snapshots and bulk data
- fafbseg
- navis

The intended contribution is the auditable handoff between these layers.

## Scientific status

Research engineering project. Claims are recorded with their evidence level and strengthened only when source data, computation and independent reproduction support them.

No open-source license is currently asserted for this repository.