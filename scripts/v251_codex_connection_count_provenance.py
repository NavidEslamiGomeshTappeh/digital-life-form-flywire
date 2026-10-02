#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,gzip,json
from collections import Counter

def targets(path):
    c=Counter()
    with open(path,newline='',encoding='utf-8') as f:
        r=csv.DictReader(f)
        for row in r: c[(row['pre_root_id'],row['post_root_id'])]+=1
    return c

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source',required=True); ap.add_argument('--target',required=True); ap.add_argument('--output',required=True); a=ap.parse_args()
    tc=targets(a.target); sc=Counter(); rows=0
    with gzip.open(a.source,'rt',newline='',encoding='utf-8') as f:
        r=csv.DictReader(f)
        expected=['pre_root_id','post_root_id','neuropil','syn_count','nt_type']
        if r.fieldnames!=expected: raise RuntimeError(f'unexpected header: {r.fieldnames}')
        for row in r:
            rows+=1; p=(row['pre_root_id'],row['post_root_id'])
            if p in tc: sc[p]+=int(row['syn_count'])
    exact=sum(sc[p]==tc[p] for p in tc)
    missing=sum(p not in sc for p in tc)
    diffs={ '|'.join(p): {'v230_rows':tc[p],'connections_syn_count':sc.get(p,0),'difference':sc.get(p,0)-tc[p]} for p in sorted(tc)}
    result={'status':'EXACT_PAIR_COUNT_EXPANSION' if exact==len(tc) and missing==0 else 'DIFF', 'source':'Codex FAFB v783 connections.csv.gz', 'source_url':'https://storage.googleapis.com/flywire-data/codex/data/fafb/783/connections.csv.gz', 'source_rows_scanned':rows, 'target_pairs':len(tc), 'pairs_exact':exact, 'pairs_missing':missing, 'all_pair_counts_equal':exact==len(tc) and missing==0, 'v230_total_rows':sum(tc.values()), 'connection_total_for_target_pairs':sum(sc.get(p,0) for p in tc), 'per_pair':diffs}
    with open(a.output,'w',encoding='utf-8') as f: json.dump(result,f,indent=2)
    print(json.dumps({k:result[k] for k in ['status','source_rows_scanned','target_pairs','pairs_exact','pairs_missing','all_pair_counts_equal','v230_total_rows','connection_total_for_target_pairs']}))
    raise SystemExit(0 if result['all_pair_counts_equal'] else 2)
if __name__=='__main__': main()