#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json
from collections import defaultdict
import pyarrow.feather as feather
def load_pairs(path):
    pairs=defaultdict(int)
    with open(path,newline="",encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pairs[(r["pre_root_id"],r["post_root_id"])] += 1
    return pairs
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True); ap.add_argument("--target-csv",required=True); ap.add_argument("--output",required=True)
    a=ap.parse_args(); wanted=load_pairs(a.target_csv)
    table=feather.read_table(a.source,columns=["pre_pt_root_id","post_pt_root_id","syn_count"])
    source={(str(pre),str(post)):int(n) for pre,post,n in zip(table["pre_pt_root_id"].to_pylist(),table["post_pt_root_id"].to_pylist(),table["syn_count"].to_pylist())}
    matched=[]; missing=[]; below=[]
    for pair,v in sorted(wanted.items()):
        n=source.get(pair)
        if n is None: missing.append({"pre":pair[0],"post":pair[1],"v230_rows":v})
        else:
            x={"pre":pair[0],"post":pair[1],"v230_rows":v,"canonical_syn_count":n}; matched.append(x)
            if n < v: below.append(x)
    result={"source_dataset":"FlyWire FAFB v783","source_file":"proofread_connections_783.feather","target_pair_count":len(wanted),"matched_pair_count":len(matched),"missing_pair_count":len(missing),"below_v230_coordinate_row_count":len(below),"status":"PASS" if not missing else "FAIL","biological_coordinate_provenance":"UNKNOWN","boundary":"Pair membership only; this does not prove the 649 coordinates.","missing":missing,"below":below,"matched":matched}
    with open(a.output,"w",encoding="utf-8") as f: json.dump(result,f,indent=2,sort_keys=True)
    print(json.dumps({k:result[k] for k in ["target_pair_count","matched_pair_count","missing_pair_count","below_v230_coordinate_row_count","status","biological_coordinate_provenance"]},sort_keys=True))
if __name__=="__main__": main()
