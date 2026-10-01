# Digital Life Form — FlyWire

## V229 FlyWire skeleton recovery

This repository contains the recovery runner for four exact FlyWire v783 neuron skeletons. It is designed to fail closed: a similar or guessed neuron is never accepted as a substitute.

| Cell | FlyWire root ID | VFB ID |
|---|---:|---|
| T4a | 720575940632008007 | VFB_fw077172 |
| T4c | 720575940616224414 | VFB_fw091869 |
| T5a | 720575940625571465 | VFB_fw056211 |
| T5c | 720575940617782941 | VFB_fw077474 |

Recovery order: fafbseg/FlyWire → MRC precomputed → Zenodo bulk.

## Evidence

`v229_results/V229_recovery_report.json` contains recorded external-data recovery evidence for all four requested cells. It records node counts, structural validation, finite geometry and SHA-256 hashes.

Software tests are not treated as proof of external-data recovery. Those are separate evidence levels.

## Run

    python -m py_compile v229_recovery_runner.py
    python test_v229_runner.py
    python v229_recovery_runner.py --route all --out v229_results --cache v229_cache

## Validation

A recovered SWC must contain nodes, exactly one structural root, no missing parent references and finite geometry. The source neuron's real ID must match the requested root before serialization.

## Project status

V229 is a morphology-recovery milestone. It is not a claim of a complete fly brain, complete connectome simulation, or biological equivalence.

## License

No open-source license has been asserted. Normal copyright rules apply unless the project owner adds a license.

## Command reference

Show version:

    python v229_recovery_runner.py --version

Recover one target:

    python v229_recovery_runner.py --route 1 --only T4a --out v229_results --cache v229_cache

The runner's default output directory is `v229_recovery_results`; examples above explicitly use the repository evidence directory `v229_results`.
