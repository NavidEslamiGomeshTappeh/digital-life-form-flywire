#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json
from collections import defaultdict
from pathlib import Path
import pyarrow.ipc as ipc

ZENODO_URL="https://zenodo.org/records/10676866/files/flywire_synapses_783.feather?download=1"

def load_targets(path):
    out={}
    with open(path,newline="",encoding="utf-8") as f:
        for n,r in enumerate(csv.DictReader(f),2):
            k=(r["pre_root_id"],r["post_root_id"],int(r["x"]),int(r["y"]),int(r["z"]))
            if k in out: raise RuntimeError(f"duplicate target row {n}")
            out[k]=n
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True)
    ap.add_argument("--target",default="v230_results/V230_target_synapses.csv")
    ap.add_argument("--output",default="/tmp/V248_zenodo_midpoint.json")
    a=ap.parse_args()

    targets=load_targets(a.target)
    pairs=set(k[:2] for k in targets)
    hits=defaultdict(list)
    reader=ipc.open_file(a.source)
    names=set(reader.schema.names)
    req=[
        "pre_pt_root_id","post_pt_root_id",
        "pre_pt_position_x","pre_pt_position_y","pre_pt_position_z",
        "post_pt_position_x","post_pt_position_y","post_pt_position_z"
    ]
    missing=[x for x in req if x not in names]
    if missing: raise RuntimeError(f"missing columns: {missing}")
    has_id="id" in names

    cols=req+([ "id" ] if has_id else [])
    scanned=0
    candidate_rows=0
    for bi in range(reader.num_record_batches):
        b=reader.get_batch(bi).select(cols)
        vv={c:b[c].to_pylist() for c in cols}
        for ri in range(b.num_rows):
            scanned+=1
            pair=(str(vv["pre_pt_root_id"][ri]),str(vv["post_pt_root_id"][ri]))
            if pair not in pairs: continue
            candidate_rows+=1
            pre=tuple(int(vv[f"pre_pt_position_{c}"][ri]) for c in "xyz")
            post=tuple(int(vv[f"post_pt_position_{c}"][ri]) for c in "xyz")
            sums=[x+y for x,y in zip(pre,post)]
            if any(s%2 for s in sums): continue
            mid=tuple(s//2 for s in sums)
            key=(*pair,*mid)
            if key in targets:
                hits[key].append({
                    "batch_index":bi,
                    "row_index_within_batch":ri,
                    "global_row_index_0based":scanned-1,
                    "id":(vv["id"][ri] if has_id else None),
                    "pre_xyz":list(pre),
                    "post_xyz":list(post),
                    "midpoint_xyz":list(mid),
                })

    missing_keys=sorted(set(targets)-set(hits))
    ambiguous={k:v for k,v in hits.items() if len(v)!=1}
    result={
        "status":"EXACT_ZENODO_MIDPOINT" if not missing_keys and not ambiguous else "INCOMPLETE",
        "source_dataset":"FlyWire FAFB v783 (Zenodo static release)",
        "source_url":ZENODO_URL,
        "source_file":"flywire_synapses_783.feather",
        "source_file_md5":"f8f1b97c9d4b0ea9b4c8b287f6b99091",
        "v230_rows":len(targets),
        "v230_pairs":len(pairs),
        "canonical_rows_scanned":scanned,
        "candidate_rows_for_target_pairs":candidate_rows,
        "exact_midpoint_matches":len(targets)-len(missing_keys),
        "missing_midpoint_matches":len(missing_keys),
        "ambiguous_matches":len(ambiguous),
        "all_649_exact":not missing_keys and not ambiguous,
        "derivation":"V230 (x,y,z) = ((pre_pt_position_x+post_pt_position_x)/2, ...), component-wise integer midpoint",
        "interpretation":"This proves deterministic source-level reconstruction against the frozen Zenodo v783 synapse table, independent of the live Codex export.",
        "historical_producer_script_proven":False,
        "mapping":[{"v230_csv_row":targets[k],"pre_root_id":k[0],"post_root_id":k[1],"v230_xyz":list(k[2:]),"source_match":hits[k][0]} for k in sorted(targets) if len(hits.get(k,[]))==1],
        "missing":[list(k) for k in missing_keys[:100]],
        "ambiguous":[{"key":list(k),"matches":v} for k,v in sorted(ambiguous.items())]
    }
    Path(a.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({k:result[k] for k in ["status","v230_rows","v230_pairs","candidate_rows_for_target_pairs","exact_midpoint_matches","missing_midpoint_matches","ambiguous_matches","all_649_exact"]},sort_keys=True))
    raise SystemExit(0 if result["status"]=="EXACT_ZENODO_MIDPOINT" else 2)

if __name__=="__main__":
    main()
