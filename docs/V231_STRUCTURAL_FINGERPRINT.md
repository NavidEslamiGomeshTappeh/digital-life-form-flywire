# V231 — Structural Fingerprint

V231 introduces a reproducible identity for the checked-in V230 synapse-coordinate artifact.

## Why this exists

The 649-row V230 CSV currently has a strong internal structure, but its historical extraction provenance is not established. A source-data match must therefore be compared against a fixed, machine-readable target.

The fingerprint engine records:

- canonical SHA-256 of the CSV rows;
- row count and unique coordinate triplets;
- unique presynaptic and postsynaptic root IDs;
- unique pre/post neuron pairs;
- minimum and maximum coordinate rows per pair;
- bidirectional pair count;
- self-loop count;
- weakly connected component sizes;
- pre/post degree distributions.

These measurements are deliberately **structural**. They do not label a row as biologically real.

## Reproduce

From the repository root:

    python scripts/v231_circuit_fingerprint.py

To write the report somewhere else:

    python scripts/v231_circuit_fingerprint.py v230_results/V230_target_synapses.csv --output v231_results/V231_structural_fingerprint.json

The CI test independently checks the key invariants of the current artifact.

## What a future source match can prove

If the exact V230 rows are independently recovered from the canonical FAFB v783 release, the source result can be compared with this fingerprint and with the V230 provenance ledger.

That can establish increasingly stronger evidence:

1. the artifact has not changed;
2. the V230 neuron-pair structure matches;
3. individual coordinate rows match the official release;
4. coordinate side (pre or post) can be identified;
5. the historical extraction command can be reconstructed, if its source/query/filter evidence is recovered.

The first four levels are still distinct from proving that the historical V230 selection was complete.

## Current status

`provenance_status = UNVERIFIED`

This status is intentional. V231 makes the project easier to verify; it does not manufacture missing evidence.
