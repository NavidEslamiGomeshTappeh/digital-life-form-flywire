#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json
from collections import defaultdict
import pyarrow.ipc as ipc

def load_targets(path):
    out=defaultdict(list)
    with open(path,newline="",encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[(r["pre_root_id"],r["post_root_id"])].append((int(r["x"]),int(r["y"]),int(r["z"])))
    return out

def scan(path,wanted):
    rows=defaultdict(list)
    reader=ipc.open_file(path)
    cols=["pre_pt_root_id","post_pt_root_id",
          "pre_pt_position_x","pre_pt_position_y","pre_pt_position_z",
          "post_pt_position_x","post_pt_position_y","post_pt_position_z"]
    for i in range(reader.num_record_batches):
        b=reader.get_batch(i).select(cols)
        vv=[b[n].to_pylist() for n in cols]
        for r in zip(*vv):
            pre,post,*xyz=r
            pair=(str(pre),str(post))
            if pair in wanted:
                rows[pair].append({
                    "pre_xyz":[int(x) for x in xyz[:3]],
                    "post_xyz":[int(x) for x in xyz[3:]]
                })
    return rows

def dist(a,b):
    return sum((x-y)**2 for x,y in zip(a,b))**0.5

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True); ap.add_argument("--target-csv",required=True); ap.add_argument("--output",required=True)
    a=ap.parse_args(); targets=load_targets(a.target_csv); rows=scan(a.source,targets)
    result={"source_dataset":"FlyWire FAFB v783","pair_count":len(targets),"pairs":{}}
    for pair in sorted(targets):
        tc=sorted(set(targets[pair])); cr=rows.get(pair,[])
        nearest=[]
        for t in tc:
            best=None
            for idx,r in enumerate(cr):
                for side in ("pre_xyz","post_xyz"):
                    d=dist(t,r[side])
                    rec={"target":list(t),"distance":d,"row_index":idx,"side":side,"xyz":r[side]}
                    if best is None or d<best["distance"]: best=rec
            if best: nearest.append(best)
        result["pairs"][f"{pair[0]}->{pair[1]}"]={
            "target_count":len(tc),"canonical_row_count":len(cr),
            "canonical_rows":cr,"nearest_target_matches":nearest
        }
    exact=sum(1 for p in result["pairs"].values() for n in p["nearest_target_matches"] if n["distance"]==0)
    result["exact_coordinate_matches"]=exact
    result["status"]="PASS" if exact==sum(p["target_count"] for p in result["pairs"].values()) else "INCOMPLETE"
    with open(a.output,"w",encoding="utf-8") as f: json.dump(result,f,indent=2,sort_keys=True)
    print(json.dumps({"pair_count":len(targets),"exact_coordinate_matches":exact,"target_coordinate_count":sum(len(set(v)) for v in targets.values()),"status":result["status"]},sort_keys=True))
if __name__=="__main__": main()
