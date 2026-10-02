#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,gzip,json
from collections import Counter,defaultdict

TARGET_ROOTS = {
    "720575940632008007",
    "720575940616224414",
    "720575940625571465",
    "720575940617782941",
}

def read_v230(path):
    counts=Counter()
    with open(path,newline="",encoding="utf-8") as f:
        r=csv.DictReader(f)
        expected=["pre_root_id","post_root_id","x","y","z"]
        if r.fieldnames != expected:
            raise RuntimeError(f"unexpected V230 header: {r.fieldnames}")
        rows=0
        for row in r:
            rows += 1
            counts[(row["pre_root_id"],row["post_root_id"])] += 1
    return counts,rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True)
    ap.add_argument("--target",required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()

    v230,pair_rows=read_v230(args.target)
    source=Counter()
    source_rows=0
    with gzip.open(args.source,"rt",newline="",encoding="utf-8") as f:
        r=csv.DictReader(f)
        expected=["pre_root_id","post_root_id","neuropil","syn_count","nt_type"]
        if r.fieldnames != expected:
            raise RuntimeError(f"unexpected source header: {r.fieldnames}")
        for row in r:
            source_rows += 1
            pre,post=row["pre_root_id"],row["post_root_id"]
            if pre in TARGET_ROOTS or post in TARGET_ROOTS:
                source[(pre,post)] += int(row["syn_count"])

    incident_all = {p:c for p,c in source.items()}
    for threshold in (1,2,3,4,5,6,7,10):
        cand={p:c for p,c in source.items() if c >= threshold}
        exact_pairs = cand.keys() == v230.keys()
        exact_counts = exact_pairs and all(cand[p] == v230[p] for p in v230)
        print(json.dumps({
            "threshold":threshold,
            "candidate_pairs":len(cand),
            "candidate_total_synapses":sum(cand.values()),
            "exact_pair_set":exact_pairs,
            "exact_pair_counts":exact_counts
        }))

    threshold=5
    cand={p:c for p,c in source.items() if c >= threshold}
    missing=sorted(set(v230)-set(cand))
    extra=sorted(set(cand)-set(v230))
    count_diffs={ "|".join(p): {"v230_rows":v230[p],"source_syn_count":cand.get(p,0),"difference":cand.get(p,0)-v230[p]} for p in sorted(v230) if cand.get(p,0) != v230[p]}
    per_target=defaultdict(lambda:{"incoming":0,"outgoing":0,"incident":0,"synapses":0})
    for (pre,post),count in cand.items():
        for root in TARGET_ROOTS:
            if post==root and pre!=root:
                per_target[root]["incoming"] += 1
            if pre==root and post!=root:
                per_target[root]["outgoing"] += 1
            if pre==root or post==root:
                per_target[root]["incident"] += 1
                per_target[root]["synapses"] += count

    result={
        "status":"EXACT_V230_PAIR_SELECTION_RECONSTRUCTION" if not missing and not extra and not count_diffs else "DIFF",
        "selection_rule_tested":"pair is incident to one of four V229/V215 target roots AND aggregated source syn_count >= 5",
        "target_roots":sorted(TARGET_ROOTS),
        "source":"Codex FAFB v783 connections.csv.gz",
        "source_url":"https://storage.googleapis.com/flywire-data/codex/data/fafb/783/connections.csv.gz",
        "source_rows_scanned":source_rows,
        "v230_rows":pair_rows,
        "v230_pairs":len(v230),
        "incident_pairs_all_thresholds":len(incident_all),
        "threshold5_pairs":len(cand),
        "threshold5_total_synapses":sum(cand.values()),
        "threshold5_exact_pair_set":not missing and not extra,
        "threshold5_exact_pair_counts":not missing and not extra and not count_diffs,
        "missing_v230_pairs_at_threshold5":missing,
        "extra_source_pairs_at_threshold5":extra,
        "pair_count_differences":count_diffs,
        "per_target":{k:per_target[k] for k in sorted(per_target)},
        "note":"This establishes a deterministic reproduction rule if exact; it does not recover the historical V230 producer script or prove that this was the rule originally used."
    }
    with open(args.output,"w",encoding="utf-8") as f:
        json.dump(result,f,indent=2,ensure_ascii=False)
    print(json.dumps({k:result[k] for k in ["status","source_rows_scanned","v230_rows","v230_pairs","incident_pairs_all_thresholds","threshold5_pairs","threshold5_total_synapses","threshold5_exact_pair_set","threshold5_exact_pair_counts"]},ensure_ascii=False))
    raise SystemExit(0 if result["threshold5_exact_pair_counts"] else 2)

if __name__=="__main__":
    main()
