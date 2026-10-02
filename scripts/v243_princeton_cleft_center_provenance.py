#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,gzip,json
from collections import Counter,defaultdict
from pathlib import Path

SOURCE_URL="https://storage.googleapis.com/flywire-data/codex/data/fafb/783/fafb_v783_princeton_synapse_table.csv.gz"

def mid(a,b):
    s=[int(x)+int(y) for x,y in zip(a,b)]
    if any(v%2 for v in s): return None
    return tuple(v//2 for v in s)

def pick(fields, names):
    for n in names:
        if n in fields: return n
    return None

def load_target(path):
    out={}; pairs=Counter()
    with path.open(newline="",encoding="utf-8") as f:
        r=csv.DictReader(f)
        if r.fieldnames != ["pre_root_id","post_root_id","x","y","z"]:
            raise RuntimeError(f"bad target header: {r.fieldnames}")
        for i,row in enumerate(r,2):
            k=(int(row["pre_root_id"]),int(row["post_root_id"]),int(float(row["x"])),int(float(row["y"])),int(float(row["z"])))
            if k in out: raise RuntimeError(f"duplicate target key row {i}")
            out[k]=i; pairs[k[:2]]+=1
    return out,pairs

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True,type=Path)
    ap.add_argument("--target-csv",default="v230_results/V230_target_synapses.csv",type=Path)
    ap.add_argument("--output",default="v243_results/V243_princeton_cleft_center.json",type=Path)
    a=ap.parse_args()
    targets,pairs=load_target(a.target_csv)
    tp=set(pairs)
    hits=defaultdict(list); ctr_hits=defaultdict(list); src_pairs=Counter(); scanned=0; candidates=0

    with gzip.open(a.source,"rt",encoding="utf-8",newline="") as f:
        rd=csv.DictReader(f); fields=set(rd.fieldnames or [])
        pre_root=pick(fields,["pre_root_id","pre_root_id_720575940","pre_pt_root_id"])
        post_root=pick(fields,["post_root_id","post_root_id_720575940","post_pt_root_id"])
        pre=tuple(pick(fields,[f"pre_{c}",f"pre_pt_position_{c}"]) for c in "xyz")
        post=tuple(pick(fields,[f"post_{c}",f"post_pt_position_{c}"]) for c in "xyz")
        ctr=tuple(pick(fields,[f"ctr_{c}",f"center_{c}",f"cleft_center_{c}"]) for c in "xyz")
        sid=pick(fields,["id","synapse_id"])
        need=[pre_root,post_root,*pre,*post]
        if any(x is None for x in need):
            raise RuntimeError(f"required column missing; header={rd.fieldnames}")
        ctr_ok=not any(x is None for x in ctr)
        for row in rd:
            scanned+=1
            pair=(int(row[pre_root]),int(row[post_root]))
            if pair not in tp: continue
            candidates+=1; src_pairs[pair]+=1
            px=tuple(int(float(row[c])) for c in pre); qx=tuple(int(float(row[c])) for c in post)
            m=mid(px,qx)
            if m is None: continue
            k=(*pair,*m)
            if k in targets:
                rec={"source_synapse_id":(int(row[sid]) if sid is not None else None),"pre_xyz":list(px),"post_xyz":list(qx),"midpoint_xyz":list(m)}
                hits[k].append(rec)
                if ctr_ok:
                    c=tuple(int(float(row[x])) for x in ctr)
                    ctr_hits[k].append({"ctr_xyz":list(c),"ctr_equals_midpoint":c==m})
    missing=sorted(set(targets)-set(hits))
    amb={k:v for k,v in hits.items() if len(v)!=1}
    pair_equal=all(src_pairs[p]==pairs[p] for p in tp)
    ctr_equal=sum(1 for k,v in ctr_hits.items() if any(x["ctr_equals_midpoint"] for x in v))
    result={
      "schema_version":1,
      "source_dataset":"FlyWire FAFB v783 Princeton Synapse Table",
      "source_url":SOURCE_URL,
      "source_file":a.source.name,
      "v230_row_count":len(targets),
      "v230_pair_count":len(tp),
      "canonical_rows_scanned":scanned,
      "candidate_rows_for_target_pairs":candidates,
      "exact_midpoint_matches":len(targets)-len(missing),
      "missing_midpoint_matches":len(missing),
      "ambiguous_midpoint_matches":len(amb),
      "all_649_rows_exact_midpoint_matched":not missing and not amb,
      "all_75_pair_counts_equal":pair_equal,
      "cleft_center_columns_available":ctr_ok,
      "cleft_center_equal_to_midpoint_count":ctr_equal,
      "cleft_center_exact_for_all_matches": ctr_ok and ctr_equal == (len(targets)-len(missing)),
      "coordinate_derivation":"component-wise mean of canonical pre and post synaptic coordinates",
      "historical_extraction_command_proven":False,
      "source_identifier_available":sid is not None,
      "source_identifier_column":sid,
      "mapping":[{"v230_csv_row":targets[k],"v230_xyz":list(k[2:]),"source_matches":hits[k],"ctr_matches":ctr_hits.get(k,[])} for k in sorted(targets) if k in hits],
      "missing":[list(k) for k in missing[:100]],
      "pair_results":[{"pre_root_id":p[0],"post_root_id":p[1],"v230_rows":pairs[p],"canonical_rows":src_pairs[p],"exact_midpoint_matches":sum(1 for k,v in hits.items() if k[:2]==p and len(v)==1)} for p in sorted(tp)]
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ["v230_row_count","v230_pair_count","candidate_rows_for_target_pairs","exact_midpoint_matches","missing_midpoint_matches","ambiguous_midpoint_matches","all_649_rows_exact_midpoint_matched","all_75_pair_counts_equal","cleft_center_columns_available","cleft_center_equal_to_midpoint_count"]},sort_keys=True))
    return 0 if result["all_649_rows_exact_midpoint_matched"] and pair_equal else 2

if __name__=="__main__": raise SystemExit(main())
