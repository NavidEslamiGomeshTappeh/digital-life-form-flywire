# V240 Canonical Coordinate Probe

Purpose: compare every V230 target coordinate against the canonical FlyWire FAFB v783 synapse table.

Source:
- FlyWire FAFB v783
- `flywire_synapses_783.feather`
- official Zenodo record 10676866

The probe checks exact integer XYZ equality for each V230 row against both the canonical presynaptic and postsynaptic coordinate triplets, restricted to the exact V230 pre/post root pair.

A PASS means every V230 coordinate has an exact coordinate match in the canonical table. It does not by itself establish that V230 was originally extracted from this file; provenance requires matching source identity, extraction/filter semantics, and reproducibility evidence.

The full source is about 9.5 GB, so this workflow intentionally scans it in Arrow record batches rather than materializing the entire table in memory.
