# V231 Target Capsule

V231 replaces dependence on the full 9.5 GB FAFB v783 synapse table with an expandable, evidence-carrying extraction boundary.

The official FAFB v783 release provides the complete released synapse table, including pre/post root IDs and pre/post synapse coordinates in nanometres; the full feather file is about 9.5 GB. This project does not need to store that whole file inside the repository.

## Architecture

DISCOVER -> FILTER -> NORMALIZE -> SEAL

- DISCOVER: inspect schema and project only relevant columns.
- FILTER: retain rows where pre_root_id OR post_root_id is one of the target roots.
- NORMALIZE: map common aliases to canonical names.
- SEAL: deterministic ordering plus SHA-256 fingerprints for source and capsule.

Current roots:
- T4a = 720575940632008007
- T4c = 720575940616224414
- T5a = 720575940625571465
- T5c = 720575940617782941

New roots can be appended with repeated --expand-root arguments. The format and audit boundary remain unchanged.

## Evidence boundary

The builder never invents a biological row. Every output row must come from the supplied source.

Statuses:
- EXACT_COORDINATE_CAPABLE: the source contains both pre and post coordinate triplets.
- TOPOLOGY_ONLY: source contains root-to-root connectivity but no complete coordinate pair.
- SCHEMA_INCOMPLETE: source cannot establish the required root-pair structure.

Coordinates being present does not prove biological completeness, nor does it prove that the historical V230 extraction used the same filter. The capsule therefore cannot silently upgrade V230 from STRUCTURE_ONLY.

## Source strategy

CSV is streamed row-by-row. Parquet uses PyArrow batch scanning and column projection, making it the preferred compact-source format. Feather is supported, but it does not gain Parquet-style predicate pushdown.

This makes the system expandable: we can add a better real source later without changing the downstream circuit/evidence interfaces.

## Verification ladder

1. Source fingerprint
2. Schema fingerprint
3. Exact target-root filtering
4. Deterministic capsule hash
5. Pair/topology cross-check
6. Coordinate membership cross-check
7. Morphology-to-synapse spatial consistency
8. Circuit-level replay

A failure at one level is retained as a failure; later evidence cannot erase it.

## Important status

These files are infrastructure until a real v783-derived source is processed. No biological synapse is manufactured by this repository.
