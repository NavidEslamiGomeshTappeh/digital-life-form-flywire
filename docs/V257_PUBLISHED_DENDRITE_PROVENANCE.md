# V257 — Exact Published Dendrite Provenance

V257 connects the four exact FlyWire roots used by this project to the historical neuron table from the T4/T5 dendrite morphology study.

## Direct evidence

The pinned source is:

- repository: borstlab/T4_T5_Dendrite_Morphology_Paper
- commit: 56901ad1853b44aeca15504cd908fa4c31009a3e
- file: Data/Neuron_ids.csv
- Git blob SHA: a83e001e556f6f83ecfa41a402b07b51bd70ba95

The four exact roots are present exactly once and all four have Dendrite_used=True:

| Project cell | Exact FlyWire root | Published subtype | Dendrite used |
|---|---:|---|---|
| T4a | 720575940632008007 | T4a | True |
| T4c | 720575940616224414 | T4c | True |
| T5a | 720575940625571465 | T5a | True |
| T5c | 720575940617782941 | T5c | True |

This is stronger than a subtype-level or nearest-neuron match: the exact root IDs occur in the published source table.

## What this proves

It establishes that these exact four FlyWire neuron IDs were included in the published dendrite-analysis dataset and marked as successfully usable for dendrite analysis.

The associated paper describes extracting the dendritic arbour of every T4 and T5 neuron in a female FAFB-FlyWire brain and provides the code used for dendrite extraction and analysis.

## What this does not prove

The Dendrite_used=True flag is not an individual synapse coordinate annotation.

It does not prove that a particular V230 x/y/z coordinate is on a particular dendrite node or segment. It also does not license assigning every synapse to a dendritic compartment solely because the cell participated in the dendrite analysis.

That direct association remains the next scientific gate.

## Reproduction

    python scripts/v257_published_dendrite_provenance.py \
      --source Data/Neuron_ids.csv \
      --output-dir v257_results

The CI workflow downloads the exact historical file from its pinned commit, runs four regression tests, verifies all four exact roots, and publishes the machine-readable provenance outputs.