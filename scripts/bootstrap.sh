#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.."
mkdir -p v229_results v229_cache
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/network_probe.py || true
python -m py_compile v229_recovery_runner.py
python test_v229_recovery_runner.py
