# Changelog

## 2026-10-01

### V229 maintenance
- Added strict source-neuron ID validation before SWC serialization.
- Removed unsafe Route 2 ID assignment before identity checking.
- Added invalid-source-ID unit coverage.
- Added GitHub Actions verification for compile, unit tests and network probing.
- Added professional documentation and an explicit validation contract.
- Preserved the recorded V229 recovery evidence.
### V230 artifact validation
- Added an executable validator for `v230_results/V230_target_synapses.csv`.
- Recorded artifact structure evidence: 649 rows, 33 unique presynaptic roots and 38 unique postsynaptic roots.
- Verified that all four V229 target root IDs occur as postsynaptic roots in the artifact.
