#!/usr/bin/env python3
"""Compare V230 pair structure with a v783-derived connection table.

The source table may come from an official v783 release or an explicitly
identified derivative. The report never treats a derivative as coordinate proof.
"""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


TARGETS = {
    '720575940632008007',
    '720575940616224414',
    '720575940625571465',
    '720575940617782941',
}

def load_pairs(path):
    pairs = {}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        names = set(reader.fieldnames or [])
        pre = next((x for x in ('pre','pre_root_id','pre_pt_root_id') if x in names), None)
        post = next((x for x in ('post','post_root_id','post_pt_root_id') if x in names), None)
        count = next((x for x in ('syn_count','weight','count') if x in names), None)
        if not pre or not post:
            raise SystemExit('SOURCE_SCHEMA_MISMATCH')
        for r in reader:
            a, b = str(r[pre]), str(r[post])
            if a and b:
                pairs[(a,b)] = pairs.get((a,b), 0) + (int(float(r[count])) if count and r[count] else 0)
    return pairs

def main():
    p=argparse.ArgumentParser()
    p.add_argument('source_csv')
    p.add_argument('--artifact', default='v230_results/V230_target_synapses.csv')
    p.add_argument('--output', default='v231_results/V231_topology_crosscheck.json')
    args=p.parse_args()
    source=load_pairs(args.source_csv)
    with open(args.artifact, newline='', encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    v230={ (r['pre_root_id'],r['post_root_id']) for r in rows }
    source_pairs=set(source)
    present=sorted(v230 & source_pairs)
    missing=sorted(v230-source_pairs)
    extra=sorted(source_pairs-v230)
    result={
        'source':args.source_csv,
        'artifact':args.artifact,
        'v230_pair_count':len(v230),
        'source_pair_count':len(source_pairs),
        'v230_pairs_found_in_source':len(present),
        'v230_pairs_missing_from_source':len(missing),
        'all_v230_pairs_present':not missing,
        'missing_pairs':missing,
        'target_post_pair_presence':{t:sum(1 for a,b in v230 if b==t and (a,b) in source_pairs) for t in sorted(TARGETS)},
        'status':'TOPOLOGY_MATCH' if not missing else 'TOPOLOGY_MISMATCH',
        'evidence_boundary':'Pair presence is a topology cross-check. It is not exact coordinate provenance.',
    }
    if present:
        result['source_synapse_count_for_v230_pairs']=sum(source[p] for p in present)
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    return 0 if not missing else 2

if __name__=='__main__':
    raise SystemExit(main())
