#!/usr/bin/env python3
"""Build a machine-readable evidence ledger from the committed V229/V230 reports."""

import argparse
import json
from pathlib import Path


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--v229', default='v229_results/V229_recovery_report.json')
    p.add_argument('--v230', default='v230_results/V230_validation.json')
    p.add_argument('--output', default='v231_results/V231_evidence_ledger.json')
    args = p.parse_args()

    v229 = read_json(args.v229)
    v230 = read_json(args.v230)

    cells = {}
    for cell in v229['cells']:
        audit = cell['attempts'][0]['audit']
        cells[cell['cell']] = {
            'root_id': cell['root_id'],
            'vfb_id': cell['vfb_id'],
            'recorded_status': cell['status'],
            'node_count': audit['node_count'],
            'structural_root_count': audit['structural_root_count'],
            'missing_parent_refs': audit['missing_parent_refs'],
            'finite_geometry': audit['finite_geometry'],
            'sha256': audit['sha256'],
            'evidence_level': 'RECORDED_EXTERNAL_RECOVERY',
        }

    ledger = {
        'schema_version': 1,
        'project': 'Digital Life Form — FlyWire',
        'milestones': {
            'V229': {
                'status': 'RECORDED',
                'evidence': cells,
                'note': 'Claims are limited to what the committed recovery report records.',
            },
            'V230': {
                'status': v230['validation_status'],
                'artifact': v230['artifact'],
                'artifact_sha256': v230['git_blob_sha'],
                'structural_facts': {
                    'row_count': v230['row_count'],
                    'unique_coordinate_rows': v230['unique_coordinate_rows'],
                    'unique_pre_root_ids': v230['unique_pre_root_ids'],
                    'unique_post_root_ids': v230['unique_post_root_ids'],
                    'unique_pre_post_pairs': v230['unique_pre_post_pairs'],
                    'pair_row_count_min': v230['pair_row_count_min'],
                    'pair_row_count_max': v230['pair_row_count_max'],
                },
                'provenance': v230['provenance'],
            },
        },
        'claim_matrix': [
            {
                'claim': 'The four requested V229 roots were recovered without root-ID substitution.',
                'status': 'RECORDED',
                'evidence': 'V229 recovery report records exact requested_root_id matches.',
            },
            {
                'claim': 'The recovered V229 skeleton files passed structural geometry checks.',
                'status': 'RECORDED',
                'evidence': 'V229 recovery report records one structural root, no missing parents, and finite geometry for all four cells.',
            },
            {
                'claim': 'V230 currently contains 649 structurally valid coordinate rows forming 75 observed pairs.',
                'status': 'STRUCTURE_ONLY',
                'evidence': 'V230 validation report.',
            },
            {
                'claim': 'The V230 649 rows are biologically verified FlyWire synapses from FAFB v783.',
                'status': 'UNVERIFIED',
                'evidence': 'Source record, extraction path, coordinate semantics, threshold and completeness are not established in the repository.',
            },
            {
                'claim': 'All 649 V230 rows exactly match the canonical FAFB v783 synapse release.',
                'status': 'PENDING_EXECUTION',
                'evidence': 'scripts/v230_zenodo_exact_probe.py exists but requires execution against the source Feather file.',
            },
            {
                'claim': 'All 75 V230 neuron pairs occur in proofread FAFB v783 connectivity.',
                'status': 'PENDING_EXECUTION',
                'evidence': 'scripts/v230_proofread_pair_probe.py exists but requires execution against proofread_connections_783.feather.',
            },
        ],
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(ledger, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(ledger, indent=2))


if __name__ == '__main__':
    main()
