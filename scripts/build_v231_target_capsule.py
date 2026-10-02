#!/usr/bin/env python3
"""Build a small, deterministic, expandable V231 target-data capsule."""
from __future__ import annotations
import argparse, csv, hashlib, json, sys
from pathlib import Path
from typing import Iterable

BASE_TARGET_ROOTS = {
    "T4a": 720575940632008007,
    "T4c": 720575940616224414,
    "T5a": 720575940625571465,
    "T5c": 720575940617782941,
}
TARGET_ROOTS = dict(BASE_TARGET_ROOTS)
ROOT_ALIASES = {"pre_pt_root_id":"pre_root_id","post_pt_root_id":"post_root_id","pre":"pre_root_id","post":"post_root_id"}
COORDS = ["pre_pt_position_x","pre_pt_position_y","pre_pt_position_z","post_pt_position_x","post_pt_position_y","post_pt_position_z"]
TOPOLOGY = ["pre_root_id","post_root_id"]
OPTIONAL = ["id","neuropil","connection_score","cleft_score","syn_count","count","gaba","ach","glut","oct","ser","da"]

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def normalize_name(name:str)->str: return ROOT_ALIASES.get(name,name)
def normalize_row(row:dict)->dict: return {normalize_name(k):v for k,v in row.items()}

def root_value(v):
    if v is None or v=="": return None
    try: return int(v)
    except (TypeError,ValueError): return None

def selected_columns(headers:Iterable[str])->list[str]:
    wanted=set(TOPOLOGY+COORDS+OPTIONAL)
    return list(dict.fromkeys(normalize_name(h) for h in headers if normalize_name(h) in wanted))

def row_touches_targets(row:dict)->bool:
    targets=set(TARGET_ROOTS.values())
    return root_value(row.get("pre_root_id")) in targets or root_value(row.get("post_root_id")) in targets

def iter_csv(path:Path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f); cols=selected_columns(reader.fieldnames or [])
        for raw in reader:
            row=normalize_row(raw)
            if row_touches_targets(row): yield {c:row.get(c,"") for c in cols},cols

def iter_arrow(path:Path):
    try:
        import pyarrow.dataset as ds
        import pyarrow.feather as feather
    except ImportError as e:
        raise SystemExit("pyarrow is required for Parquet/Feather inputs") from e
    if path.suffix.lower()==".parquet":
        dataset=ds.dataset(str(path),format="parquet")
        names=dataset.schema.names; cols=selected_columns(names)
        physical=[]
        for c in cols:
            if c in names: physical.append(c)
            else:
                for original,canonical in ROOT_ALIASES.items():
                    if canonical==c and original in names: physical.append(original); break
        for batch in dataset.scanner(columns=physical,batch_size=65536).to_batches():
            data=batch.to_pydict()
            for i in range(batch.num_rows):
                row=normalize_row({k:data[k][i] for k in data})
                if row_touches_targets(row): yield {c:row.get(c,"") for c in cols},cols
        return
    table=feather.read_table(str(path))
    names=table.schema.names; cols=selected_columns(names)
    physical=[]
    for c in cols:
        if c in names: physical.append(c)
        else:
            for original,canonical in ROOT_ALIASES.items():
                if canonical==c and original in names: physical.append(original); break
    table=feather.read_table(str(path),columns=physical)
    for batch in table.to_batches(max_chunksize=65536):
        data=batch.to_pydict()
        for i in range(batch.num_rows):
            row=normalize_row({k:data[k][i] for k in data})
            if row_touches_targets(row): yield {c:row.get(c,"") for c in cols},cols

def iter_rows(path:Path):
    if path.suffix.lower()==".csv": yield from iter_csv(path)
    elif path.suffix.lower() in {".parquet",".feather"}: yield from iter_arrow(path)
    else: raise SystemExit("Unsupported source format: CSV, Parquet, or Feather")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("source")
    p.add_argument("--output",default="v231_results/V231_target_capsule.csv")
    p.add_argument("--manifest",default="v231_results/V231_target_capsule_manifest.json")
    p.add_argument("--source-label",default="UNSPECIFIED")
    p.add_argument("--expand-root",action="append",default=[])
    args=p.parse_args()
    source=Path(args.source)
    if not source.is_file(): raise SystemExit(f"source does not exist: {source}")
    TARGET_ROOTS.clear(); TARGET_ROOTS.update(BASE_TARGET_ROOTS)
    for raw in args.expand_root: TARGET_ROOTS[f"extra_{raw}"]=int(raw)
    out=Path(args.output); manifest_path=Path(args.manifest)
    out.parent.mkdir(parents=True,exist_ok=True); manifest_path.parent.mkdir(parents=True,exist_ok=True)
    rows=[]; columns=[]
    for row,cols in iter_rows(source):
        if not columns: columns=cols
        rows.append(row)
    rows.sort(key=lambda r:(root_value(r.get("pre_root_id")) or -1,root_value(r.get("post_root_id")) or -1,str(r.get("id","")),str(r.get("pre_pt_position_x","")),str(r.get("post_pt_position_x",""))))
    if not columns: columns=TOPOLOGY
    with out.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=columns); w.writeheader(); w.writerows(rows)
    has_coords=all(c in columns for c in COORDS); has_topology=all(c in columns for c in TOPOLOGY)
    status="EXACT_COORDINATE_CAPABLE" if has_coords else ("TOPOLOGY_ONLY" if has_topology else "SCHEMA_INCOMPLETE")
    manifest={
      "schema":"V231-target-capsule/v1","status":status,
      "source":{"path_name":source.name,"size_bytes":source.stat().st_size,"sha256":sha256_file(source),"label":args.source_label},
      "filter":{"root_ids":TARGET_ROOTS,"touch_rule":"pre_root_id OR post_root_id is in target set"},
      "output":{"path_name":out.name,"row_count":len(rows),"columns":columns,"sha256":sha256_file(out)},
      "evidence_boundary":{"rows_are_copied_from_source":True,"rows_are_invented":False,"coordinate_columns_present":has_coords,"biological_completeness_proven":False,"historical_extraction_rule_proven":False},
      "expansion":{"base_targets_preserved":BASE_TARGET_ROOTS,"extra_roots":args.expand_root,"rebuild_is_deterministic":True}
    }
    manifest_path.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(manifest,indent=2))

if __name__=="__main__": main()
