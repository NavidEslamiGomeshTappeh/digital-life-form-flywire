#!/usr/bin/env python3
"""Stream the official Codex FAFB v783 synapse-coordinate table and audit V230 rows."""
from __future__ import annotations
import csv, gzip, hashlib, io, json, sys, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE_URL="https://storage.googleapis.com/flywire-data/codex/data/fafb/783/synapse_coordinates.csv.gz"
TARGETS={
"720575940632008007","720575940616224414",
"720575940625571465","720575940617782941",
}
V230=ROOT/"v230_results/V230_target_synapses.csv"
OUT=ROOT/"v238_results"
OUT.mkdir(exist_ok=True)

def norm(v):
    return str(v).strip()

def sha256_file(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def main():
    with V230.open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    expected={(norm(r["pre_root_id"]),norm(r["post_root_id"]),norm(r["x"]),norm(r["y"]),norm(r["z"])):i+2 for i,r in enumerate(rows)}

    matched={}
    pair_hits={}
    with urllib.request.urlopen(SOURCE_URL,timeout=60) as resp:
        raw=io.BufferedReader(resp,buffer_size=1024*1024)
        with gzip.GzipFile(fileobj=raw,mode="rb") as gz:
            text=io.TextIOWrapper(gz,encoding="utf-8",newline="")
            reader=csv.DictReader(text)
            header=reader.fieldnames or []
            required={"pre_pt_root_id","post_pt_root_id"}
            if not required.issubset(header):
                raise RuntimeError(f"unexpected header: {header}")
            pre_xyz=[f"pre_pt_position_{a}" for a in "xyz"]
            post_xyz=[f"post_pt_position_{a}" for a in "xyz"]
            for r in reader:
                pre=norm(r["pre_pt_root_id"]); post=norm(r["post_pt_root_id"])
                if pre not in TARGETS and post not in TARGETS:
                    continue
                pair_hits[(pre,post)]=pair_hits.get((pre,post),0)+1
                pxyz=tuple(norm(r[c]) for c in pre_xyz)
                qxyz=tuple(norm(r[c]) for c in post_xyz)
                for coord_kind,xyz in (("pre",pxyz),("post",qxyz)):
                    key=(pre,post,*xyz)
                    if key in expected:
                        matched.setdefault(key,[]).append({
                            "coord_kind":coord_kind,
                            "pre_root_id":pre,
                            "post_root_id":post,
                            "x":xyz[0],"y":xyz[1],"z":xyz[2]
                        })
    exact=sum(1 for v in matched.values() if v)
    ambiguous=sum(1 for v in matched.values() if len(v)>1)
    result={
      "source_url":SOURCE_URL,
      "source_dataset":"FAFB v783 Codex synapse_coordinates",
      "source_policy":"official public static resource",
      "v230_rows":len(rows),
      "exact_coordinate_rows_matched":exact,
      "ambiguous_v230_rows":ambiguous,
      "unmatched_v230_rows":len(rows)-exact,
      "target_pair_hits":sum(pair_hits.values()),
      "target_pairs_observed":len(pair_hits),
      "match_examples":list(matched.items())[:10],
      "interpretation":"MATCHED means an exact V230 pre/post pair and xyz tuple occurs in the canonical source in either pre- or post-coordinate field. It does not by itself prove which coordinate semantics V230 used."
    }
    (OUT/"V238_coordinate_probe.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__": main()
