# V229 Operations Guide

## Install
    python -m pip install -r requirements.txt

## Verify environment
    python scripts/network_probe.py
    python -m py_compile v229_recovery_runner.py
    python test_v229_runner.py

## Run recovery
    python v229_recovery_runner.py --route all --out v229_results --cache v229_cache

## Evidence
`v229_results/V229_recovery_report.json` is the authoritative recovery report.

## Fail-closed behavior
Wrong source ID, empty skeleton, multiple structural roots, missing parents, non-finite geometry or an unverified Zenodo schema causes failure. The runner never substitutes a similar neuron.