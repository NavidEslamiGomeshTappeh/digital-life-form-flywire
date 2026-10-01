# Digital Life Form — FlyWire

## V229 FlyWire skeleton recovery

This repository contains the recovery runner for four exact FlyWire v783 neuron skeletons. It is designed to fail closed: a similar or guessed neuron is never accepted as a substitute.

| Cell | FlyWire root ID | VFB ID |
|---|---:|---|
| T4a | 720575940632008007 | VFB_fw077172 |
| T4c | 720575940616224414 | VFB_fw091869 |
| T5a | 720575940625571465 | VFB_fw077056211 |
| T5c | 720575940617782941 | VFB_fw077474 |

Recovery order: fafbseg/FlyWire → MRC precomputed → Zenodo bulk.

## Evidence

`v229_results/V229_recovery_report.json` contains recorded external-data recovery evidence for all four requested cells. It records node counts, structural validation, finite geometry and SHA-256 hashes.

Software tests are not treated as proof of external-data recovery. Those are separate evidence levels.

## Run

    python -m py_compile v229_recovery_runner.py
    python test_v229_recovery_runner.py
    python v229_recovery_runner.py --route all --out v229_results --cache v229_cache

## Validation

A recovered SWC must contain nodes, exactly one structural root, no missing parent references and finite geometry. The source neuron's real ID must match the requested root before serialization.

## V230 synapse artifact — provenance audit

`v230_results/V230_target_synapses.csv` is a checked-in artifact with 649 rows, 33 unique presynaptic roots, 38 unique postsynaptic roots and 75 unique pre/post pairs. All four V229 target roots occur as postsynaptic roots, but the artifact also contains 34 other postsynaptic roots.

The repository history proves that this CSV was introduced in commit `e57b1ccc5b9f64964af223b6bf8e853579985fe0`, whose message is `V229 FlyWire morphology recovery and V230 synapse coordinates`. That proves repository provenance, not scientific provenance.

The current repository does **not** contain the extraction script, source-data filename/record, query/filter code, or a reproducible command that generated the 649 rows. Therefore the following are **not established facts**:

- that the 649 rows were queried directly from FlyWire v783;
- that every row is one real biological synapse;
- that `x,y,z` are postsynaptic coordinates, presynaptic coordinates, or a particular synapse-coordinate field;
- that the apparent minimum of 5 rows per pre/post pair came from a deliberate `>=5` synapse threshold;
- that the artifact is complete for the four target neurons;
- that the 649 rows are sufficient to reconstruct the V230 circuit.

The data pattern is compatible with a pair-level selection followed by expansion to coordinate rows: every observed pair has 5–21 rows and all 649 coordinate triplets are unique. This is an **observation/inference, not provenance evidence**.

See `v230_results/V230_validation.json` for the machine-readable audit. Structural validation of the CSV is intentionally labeled `STRUCTURE_ONLY`, not biological PASS.

## Project status

V229 is a morphology-recovery milestone. V230 is currently a **provenance-unverified synapse-coordinate artifact**. The project does not claim from this CSV alone that it has recovered a verified set of 649 biological synapses or a complete T4/T5 connectivity circuit.

## License

No open-source license has been asserted. Normal copyright rules apply unless the project owner adds a license.

## Command reference

Show version:

    python v229_recovery_runner.py --version

Recover one target:

    python v229_recovery_runner.py --route 1 --only T4a --out v229_results --cache v229_cache

The runner's default output directory is `v229_recovery_results`; examples above explicitly use the repository evidence directory `v229_results`.
