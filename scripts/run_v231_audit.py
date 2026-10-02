#!/usr/bin/env python3
"""Run the complete V231 local audit pipeline in one command."""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(cmd):
    completed = subprocess.run(cmd, capture_output=True, text=True)
    return completed.returncode, completed.stdout, completed.stderr


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--artifact', default='v230_results/V230_target_synapses.csv')
    p.add_argument('--synapses', help='Local flywire_synapses_783.feather')
    p.add_argument('--proofread', help='Local proofread_connections_783.feather')
    p.add_argument('--topology-csv', help='Local v783-derived connection table in CSV form')
    p.add_argument('--output', default='v231_results/V231_audit_report.json')
    args = p.parse_args()

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    results = {'artifact': args.artifact, 'steps': []}

    steps = [
        ('structural_fingerprint', [sys.executable, 'scripts/v231_circuit_fingerprint.py', args.artifact, '--output', str(out.parent / 'V231_structural_fingerprint.json')]),
        ('evidence_ledger', [sys.executable, 'scripts/build_evidence_ledger.py', '--output', str(out.parent / 'V231_evidence_ledger.json')]),
    ]
    if args.proofread:
        steps.append(('proofread_pair_probe', [sys.executable, 'scripts/v230_proofread_pair_probe.py', args.proofread, '--artifact', args.artifact, '--output', str(out.parent / 'V230_proofread_pair_probe.json')]))
    if args.topology_csv:
        steps.append(('topology_crosscheck', [sys.executable, 'scripts/v231_topology_crosscheck.py', args.topology_csv, '--artifact', args.artifact, '--output', str(out.parent / 'V231_topology_crosscheck.json')]))
    if args.synapses:
        steps.append(('exact_coordinate_probe', [sys.executable, 'scripts/v230_zenodo_exact_probe.py', args.synapses, '--artifact', args.artifact, '--output', str(out.parent / 'V230_zenodo_exact_probe.json')]))

    for name, cmd in steps:
        code, stdout, stderr = run(cmd)
        results['steps'].append({
            'name': name,
            'exit_code': code,
            'status': 'PASS' if code == 0 else 'FAIL',
            'stdout_tail': stdout[-4000:],
            'stderr_tail': stderr[-4000:],
        })

    engine_cmd = [
        sys.executable, 'scripts/v231_evidence_engine.py',
        '--output', str(out.parent / 'V231_evidence_engine.json'),
    ]
    if args.synapses:
        engine_cmd += ['--coordinate-probe', str(out.parent / 'V230_zenodo_exact_probe.json')]
    if args.proofread:
        engine_cmd += ['--proofread-probe', str(out.parent / 'V230_proofread_pair_probe.json')]
    if args.topology_csv:
        engine_cmd += ['--topology', str(out.parent / 'V231_topology_crosscheck.json')]
    code, stdout, stderr = run(engine_cmd)
    results['steps'].append({
        'name': 'evidence_engine',
        'exit_code': code,
        'status': 'PASS' if code == 0 else 'FAIL',
        'stdout_tail': stdout[-4000:],
        'stderr_tail': stderr[-4000:],
    })

    results['overall_status'] = 'PASS' if all(s['exit_code'] == 0 for s in results['steps']) else 'FAIL'
    results['source_data_supplied'] = bool(args.synapses or args.proofread or args.topology_csv)
    results['note'] = 'PASS means the requested computations completed; it does not by itself establish biological provenance.'
    out.write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(results, indent=2))
    return 0 if results['overall_status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
