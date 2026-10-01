# V230 exact provenance route

## Current evidence

The checked-in V230 coordinate artifact remains provenance-unverified.

Codex documents that its programmatic static-download endpoint uses a Codex API token. A CAVE token is a separate credential used for live source-project operations.

For an exact coordinate check without either token, the canonical public FAFB v783 Zenodo release is:

https://zenodo.org/records/10676866

The file required for exact row/coordinate matching is `flywire_synapses_783.feather` (9.5 GB; MD5 `f8f1b97c9d4b0ea9b4c8b287f6b99091`). It contains pre/post root IDs and both pre/post XYZ coordinates.

The smaller `proofread_connections_783.feather` (852 MB) can independently validate neuron-pair connectivity and synapse counts, but it does not contain the individual synapse coordinates, so it cannot by itself prove the 649 V230 coordinate rows.

## Exact test

For each V230 row, compare:

`pre_root_id, post_root_id, x, y, z`

against both:

`pre_pt_root_id, post_pt_root_id, pre_pt_position_x, pre_pt_position_y, pre_pt_position_z`

and:

`pre_pt_root_id, post_pt_root_id, post_pt_position_x, post_pt_position_y, post_pt_position_z`

A 649/649 exact match would establish that every checked-in V230 coordinate row exists in the public FAFB v783 synapse release and would identify the coordinate side. It would not prove the historical extraction command or completeness.
