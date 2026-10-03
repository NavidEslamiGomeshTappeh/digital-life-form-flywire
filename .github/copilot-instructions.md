# Digital Life Form — repository instructions

## Project identity
This is a provenance-first connectomics research-engineering project.
Core chain:
exact FlyWire root IDs → exact identity → directed connectivity → individual synapses → morphology → measured geometry → compartment evidence → simulation-ready structure.

## Non-negotiable evidence rules
- Never substitute a similar neuron for an exact root ID.
- Never manufacture fallback coordinates, connectivity, morphology, compartment labels, hashes, or PASS states.
- External-source failure is recorded as FAIL or UNAVAILABLE, never silently converted to PASS.
- Distinguish recorded facts, structural validation, computational inference, published biological evidence, and unresolved claims.
- Pin external datasets by version/commit where possible and preserve source identifiers and hashes.
- Do not upgrade nearest-neighbour geometry into a biological compartment label without independent evidence.
- Preserve reproducibility with deterministic inputs, explicit transformations, manifests, regression tests, and immutable source references.

## Workflow
- Work on a branch.
- Add focused tests with every substantive change.
- Run focused tests, then the repository gate.
- Inspect generated evidence for identity drift, coordinate drift, provenance loss, or stale outputs.
- Prefer small auditable changes.
- Do not modify scientific output merely to make CI green.

## Current layers
- V230: 649 exact synapse-coordinate rows / 75 directed pairs.
- V255: usable Circuit Evidence Pack.
- V256: cell-level input/output evidence; coordinate-level compartment unresolved.
- V257: exact-root provenance into the published T4/T5 dendrite study.
- V258: published automatic dendrite-subtree candidate reproduction on exact project SWCs.
- V259: published Point_data provenance cross-check against exact project SWCs.

## Status vocabulary
PASS = demonstrated by the current test.
PASS_WITH_LIMITS = demonstrated with explicit bounds.
INFERRED = computational or biological inference.
UNRESOLVED = intentionally not established.
FAIL = a reproducible check failed.
UNAVAILABLE = a required external source or tool could not be reached.

## Pull requests
Explain source chain, transformation, tests and CI evidence, what is newly proven, and what remains unproven.
