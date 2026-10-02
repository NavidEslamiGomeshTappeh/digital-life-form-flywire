#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json
from collections import defaultdict
import pyarrow.ipc as ipc

def load_targets(path):
    targets=defaultdict(list)
    with open(path,newline="",encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pair=(r["pre_root_id"],r["post_root_id"])
            xyz=(int(r["x"]),int(r["y"]),int(r["z"]))
            targets[pair].append(xyz)
    return targets

def scan_source(path, targets):
    remaining={pair:set(coords) for pair,coords in targets.items()}
    hits=defaultdict(lambda: defaultdict(set))
    reader=ipc.open_file(path)
    for i in range(reader.num_record_batches):
        batch=reader.get_batch(i).select([
            "pre_pt_root_id","post_pt_root_id",
            "pre_pt_position_x","pre_pt_position_y","pre_pt_position_z",
            "post_pt_position_x","post_pt_position_y","post_pt_position_z",
        ])
        cols=[batch[n].to_pylist() for n in batch.schema.names]
        for row in zip(*cols):
            pre,post,*xyz=row
            pair=(str(pre),str(post))
            wanted=remaining.get(pair)
            if not wanted:
                continue
            pre_xyz=tuple(int(v) for v in xyz[:3])
            post_xyz=tuple(int(v) for v in xyz[3:])
            if pre_xyz in wanted:
                hits[pair]["pre"].add(pre_xyz)
                wanted.discard(pre_xyz)
            if post_xyz in wanted:
                hits[pair]["post"].add(post_xyz)
                wanted.discard(post_xyz)
    return hits, remaining

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True)
    ap.add_argument("--target-csv",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    targets=load_targets(a.target_csv)
    hits,remaining=scan_source(a.source,targets)

    total=sum(len(v) for v in targets.values())
    matched=sum(len(v) for v in hits.values() for _ in [0])  # pair count only
    coordinate_hits=0
    unresolved=[]
    ambiguous=[]
    pair_results=[]

    for pair in sorted(targets):
        target_coords=set(targets[pair])
        pre_hits=set(hits[pair].get("pre",set()))
        post_hits=set(hits[pair].get("post",set()))
        found=pre_hits | post_hits
        coordinate_hits += len(found)
        unresolved_coords=sorted(target_coords-found)
        if unresolved_coords:
            unresolved.append({"pre":pair[0],"post":pair[1],"missing_coordinates":unresolved_coords})
        both=sorted(pre_hits & post_hits)
        if both:
            ambiguous.append({"pre":pair[0],"post":pair[1],"coordinates":both})
        pair_results.append({
            "pre":pair[0],"post":pair[1],
            "target_coordinate_count":len(target_coords),
            "pre_coordinate_matches":len(pre_hits),
            "post_coordinate_matches":len(post_hits),
            "missing_coordinate_count":len(unresolved_coords),
        })

    status="PASS" if coordinate_hits==total and not unresolved else "INCOMPLETE"
    result={
        "source_dataset":"FlyWire FAFB v783",
        "source_file":"flywire_synapses_783.feather",
        "target_row_count":total,
        "coordinate_match_count":coordinate_hits,
        "missing_coordinate_count":total-coordinate_hits,
        "pair_count":len(targets),
        "unresolved_pairs":len(unresolved),
        "ambiguous_coordinate_count":sum(len(x["coordinates"]) for x in ambiguous),
        "status":status,
        "coordinate_provenance":"SUPPORTED" if status=="PASS" and not ambiguous else "INCOMPLETE",
        "boundary":"Exact coordinate membership in canonical v783 synapse table; does not by itself prove that the 649 rows originated from this source without a provenance chain for V230 extraction.",
        "unresolved":unresolved,
        "ambiguous":ambiguous,
        "pairs":pair_results,
    }
    with open(a.output,"w",encoding="utf-8") as f:
        json.dump(result,f,indent=2,sort_keys=True)
    print(json.dumps({k:result[k] for k in [
        "target_row_count","coordinate_match_count","missing_coordinate_count",
        "pair_count","unresolved_pairs","ambiguous_coordinate_count","status",
        "coordinate_provenance"]},sort_keys=True))

if __name__=="__main__":
    main()
