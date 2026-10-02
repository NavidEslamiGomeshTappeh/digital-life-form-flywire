#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, gzip, hashlib, json, shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOTS_DEFAULT = [
    '720575940632008007',
    '720575940616224414',
    '720575940625571465',
    '720575940617782941',
]
CONNECTION_COLUMNS = ['pre_root_id','post_root_id','neuropil','syn_count','nt_type']
SYNAPSE_COLUMNS = ['pre_root_id','post_root_id','x','y','z']

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def read_reference_v230(path: Path):
    pairs = Counter()
    rows = set()
    with path.open(newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        if r.fieldnames != SYNAPSE_COLUMNS:
            raise RuntimeError(f'unexpected V230 header: {r.fieldnames}')
        for row in r:
            p = (row['pre_root_id'], row['post_root_id'])
            pairs[p] += 1
            rows.add((row['pre_root_id'], row['post_root_id'], row['x'], row['y'], row['z']))
    return pairs, rows

def build(args):
    roots = set(args.root)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    connections_out = output / 'connections_selected.csv'
    synapses_out = output / 'synapses_selected.csv'

    pair_syn_counts = Counter()
    selected_connection_rows = 0
    with gzip.open(args.connections, 'rt', newline='', encoding='utf-8') as f, connections_out.open('w', newline='', encoding='utf-8') as out:
        r = csv.DictReader(f)
        if r.fieldnames != CONNECTION_COLUMNS:
            raise RuntimeError(f'unexpected connection header: {r.fieldnames}')
        w = csv.DictWriter(out, fieldnames=CONNECTION_COLUMNS)
        w.writeheader()
        for row in r:
            pre, post = row['pre_root_id'], row['post_root_id']
            if pre in roots or post in roots:
                w.writerow(row)
                selected_connection_rows += 1
                pair_syn_counts[(pre, post)] += int(row['syn_count'])

    selected_pairs = set(pair_syn_counts)
    selected_syn_rows = 0
    selected_syn_counts = Counter()
    selected_syn_set = set()
    prev_pre = None
    prev_post = None
    with gzip.open(args.synapses, 'rt', newline='', encoding='utf-8') as f, synapses_out.open('w', newline='', encoding='utf-8') as out:
        r = csv.DictReader(f)
        if r.fieldnames != SYNAPSE_COLUMNS:
            raise RuntimeError(f'unexpected synapse header: {r.fieldnames}')
        w = csv.DictWriter(out, fieldnames=SYNAPSE_COLUMNS)
        w.writeheader()
        for row in r:
            pre = row['pre_root_id'] or prev_pre
            post = row['post_root_id'] or prev_post
            if pre is None or post is None:
                raise RuntimeError('synapse row encountered before both IDs were established')
            prev_pre, prev_post = pre, post
            if (pre, post) not in selected_pairs:
                continue
            clean = {'pre_root_id': pre, 'post_root_id': post, 'x': row['x'], 'y': row['y'], 'z': row['z']}
            w.writerow(clean)
            selected_syn_rows += 1
            selected_syn_counts[(pre, post)] += 1
            selected_syn_set.add((pre, post, row['x'], row['y'], row['z']))

    result = {
        'schema_version': 1,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'dataset': args.dataset,
        'root_ids': sorted(roots),
        'selection_policy': 'directed pair is incident to one of the requested roots',
        'source_files': {
            'connections': {'path': str(args.connections), 'sha256': sha256(Path(args.connections))},
            'synapse_coordinates': {'path': str(args.synapses), 'sha256': sha256(Path(args.synapses))},
        },
        'selected_connection_rows': selected_connection_rows,
        'selected_directed_pairs': len(selected_pairs),
        'selected_synapse_rows': selected_syn_rows,
        'selected_pair_synapse_counts': {'|'.join(k): v for k, v in sorted(selected_syn_counts.items())},
        'status': 'PASS',
    }

    if args.reference_v230:
        ref_pairs, ref_rows = read_reference_v230(Path(args.reference_v230))
        missing_pairs = sorted(set(ref_pairs) - selected_pairs)
        extra_pairs = sorted(selected_pairs - set(ref_pairs))
        missing_synapses = sorted(ref_rows - selected_syn_set)
        extra_synapses = sorted(selected_syn_set - ref_rows)
        pair_count_diffs = {
            '|'.join(p): {'reference': ref_pairs[p], 'generated': selected_syn_counts.get(p, 0)}
            for p in sorted(ref_pairs)
            if ref_pairs[p] != selected_syn_counts.get(p, 0)
        }
        result['regression'] = {
            'reference': str(args.reference_v230),
            'reference_rows': sum(ref_pairs.values()),
            'reference_pairs': len(ref_pairs),
            'pair_set_exact': not missing_pairs and not extra_pairs,
            'pair_counts_exact': not pair_count_diffs and not missing_pairs and not extra_pairs,
            'individual_synapse_set_exact': not missing_synapses and not extra_synapses,
            'missing_pairs': missing_pairs,
            'extra_pairs': extra_pairs,
            'pair_count_differences': pair_count_diffs,
            'missing_synapses': missing_synapses,
            'extra_synapses': extra_synapses,
        }
        if not result['regression']['pair_counts_exact'] or not result['regression']['individual_synapse_set_exact']:
            result['status'] = 'FAIL'

    (output / 'MANIFEST.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\\n', encoding='utf-8')
    print(json.dumps({
        'status': result['status'],
        'dataset': args.dataset,
        'root_ids': len(roots),
        'selected_directed_pairs': len(selected_pairs),
        'selected_synapse_rows': selected_syn_rows,
        'regression': result.get('regression'),
    }, ensure_ascii=False))
    if result['status'] != 'PASS':
        raise SystemExit(2)

def main():
    p = argparse.ArgumentParser(description='Build a reproducible FlyWire Circuit Evidence Pack from official v783 exports.')
    p.add_argument('--connections', required=True)
    p.add_argument('--synapses', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--dataset', default='FAFB v783')
    p.add_argument('--reference-v230', default=None)
    p.add_argument('--root', action='append', dest='root')
    a = p.parse_args()
    if not a.root:
        a.root = ROOTS_DEFAULT
    build(a)

if __name__ == '__main__':
    main()
