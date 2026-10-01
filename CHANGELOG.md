# Changelog

## 2026-10-01

### V229 maintenance
- Added strict source-neuron ID validation before SWC serialization.
- Removed unsafe Route 2 ID assignment before identity checking.
- Added invalid-source-ID unit coverage.
- Added GitHub Actions verification for compile, unit tests and network probing.
- Added professional documentation and an explicit validation contract.
- Preserved the recorded V229 recovery evidence.

### V230 provenance audit
- Audited `v230_results/V230_target_synapses.csv` against its Git history and contents.
- Confirmed 649 rows, 33 unique presynaptic roots, 38 unique postsynaptic roots and 75 unique pre/post pairs.
- Confirmed every observed pre/post pair has 5–21 rows and all 649 coordinate triplets are unique.
- Downgraded the V230 artifact status from a generic structural PASS to `STRUCTURE_ONLY`.
- Explicitly marked source dataset, extraction code, coordinate semantics, threshold/filter logic, completeness and reproducibility as unverified.
