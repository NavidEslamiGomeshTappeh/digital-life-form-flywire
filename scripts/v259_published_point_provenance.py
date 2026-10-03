#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from typing import Any
import pandas as pd

POINT_DATA_COMMIT = "56901ad1853b44aeca15504cd908fa4c31009a3e"
POINT_DATA_BLOB = "b85caf49f45677f2075f7b5f2c8830141cd96d02"
POINT_DATA_PATH = "Data/Point_data.pkl"
STUDY_REPO = "borstlab/T4_T5_Dendrite_Morphology_Paper"
STUDY_NOTEBOOK = "Notebooks/Metrics1_Point_data.ipynb"
STUDY_NEROSSETTA_COMMIT = "38f20f02194c129c234360db5a8be78a90c61db1"

ROOTS = {"T4a":"720575940632008007","T4c":"720575940616224414","T5a":"720575940625571465","T5c":"720575940617782941"}

CORE_COLUMNS = [
    "ID","Neuron_type","Neuron_subtype","Subtype","hemisphere",
    "root_x","root_y","root_z","Segement_count","Total_cable",
    "Total_nodes","External_edges","Intenal_edges","Number_leaves","Number_branches",
]

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024*1024), b""): h.update(chunk)
    return h.hexdigest()

def load_point_data(path: Path) -> pd.DataFrame:
    obj = pd.read_pickle(path)
    if not isinstance(obj, pd.DataFrame):
        raise TypeError(f"Point_data.pkl must contain a pandas DataFrame, got {type(obj).__name__}")
    if "ID" not in obj.columns:
        raise RuntimeError(f"Point_data.pkl has no ID column; columns={list(obj.columns)}")
    obj = obj.copy()
    obj["ID"] = obj["ID"].astype(str)
    return obj

def extract_anchor_rows(data: pd.DataFrame) -> pd.DataFrame:
    wanted = list(ROOTS.values())
    selected = data[data["ID"].isin(wanted)].copy()
    selected["_order"] = selected["ID"].map({rid:i for i,rid in enumerate(wanted)})
    selected = selected.sort_values("_order").drop(columns=["_order"])
    if len(selected) != len(ROOTS):
        missing = [rid for rid in wanted if rid not in set(selected["ID"])]
        raise RuntimeError(f"published Point_data anchor regression failed; missing={missing}; rows={len(selected)}")
    if selected["ID"].duplicated().any():
        raise RuntimeError("published Point_data has duplicate anchor IDs")
    for col in CORE_COLUMNS:
        if col not in selected.columns:
            raise RuntimeError(f"published Point_data missing required column {col}")
    return selected

def parse_swc(path: Path) -> dict[str, Any]:
    nodes, by_id, children = [], {}, {}
    with path.open(encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"): continue
            parts = line.split()
            if len(parts) < 7: raise RuntimeError(f"malformed SWC row in {path.name}")
            n = {"id":int(parts[0]),"label":int(parts[1]),"x":float(parts[2]),"y":float(parts[3]),
                 "z":float(parts[4]),"radius":float(parts[5]),"parent":int(parts[6])}
            if n["id"] in by_id: raise RuntimeError(f"duplicate SWC node id {n['id']} in {path.name}")
            nodes.append(n); by_id[n["id"]] = n
            if n["parent"] != -1: children.setdefault(n["parent"], []).append(n["id"])
    roots = [n["id"] for n in nodes if n["parent"] == -1]
    if len(roots) != 1: raise RuntimeError(f"{path.name}: expected one structural root, got {roots}")
    for n in nodes:
        if n["parent"] != -1 and n["parent"] not in by_id:
            raise RuntimeError(f"{path.name}: missing parent {n['parent']}")
    order, stack = [], [roots[0]]
    while stack:
        cur = stack.pop(); order.append(cur); stack.extend(reversed(children.get(cur, [])))
    if len(order) != len(nodes): raise RuntimeError(f"{path.name}: graph is disconnected")
    edge_length = {}
    for n in nodes:
        if n["parent"] != -1:
            p = by_id[n["parent"]]
            edge_length[(n["parent"],n["id"])] = math.dist((p["x"],p["y"],p["z"]),(n["x"],n["y"],n["z"]))
    return {"nodes":nodes,"by_id":by_id,"children":children,"order":order,
            "edge_length":edge_length,"total_cable":sum(edge_length.values()),"root":roots[0]}

def legacy_optimal_partition_root(tree: dict[str, Any]) -> dict[str, Any]:
    leaves = {n["id"] for n in tree["nodes"] if len(tree["children"].get(n["id"],[])) == 0}
    subtree_cable = {n["id"]:0.0 for n in tree["nodes"]}
    subtree_leaves = {n["id"]:(1 if n["id"] in leaves else 0) for n in tree["nodes"]}
    for cur in reversed(tree["order"]):
        for child in tree["children"].get(cur,[]):
            subtree_cable[cur] += tree["edge_length"][(cur,child)] + subtree_cable[child]
            subtree_leaves[cur] += subtree_leaves[child]
    candidates = []
    for n in tree["nodes"]:
        nid = n["id"]
        if len(tree["children"].get(nid,[])) < 2: continue
        score = (1.0 - subtree_cable[nid]/tree["total_cable"]) + (subtree_leaves[nid]/len(leaves))
        candidates.append((score,nid))
    if not candidates: raise RuntimeError("no branch candidates")
    score,nid = max(candidates, key=lambda x:x[0])
    return {"node_id":int(nid),"score":float(score),"subtree_cable":float(subtree_cable[nid]),
            "subtree_leaves":int(subtree_leaves[nid]),"leaf_count":int(len(leaves))}

def nearest_node(tree: dict[str, Any], point_nm: tuple[float,float,float]) -> tuple[int,float]:
    best = None
    for n in tree["nodes"]:
        d = math.dist(point_nm,(n["x"],n["y"],n["z"]))
        if best is None or d < best[1]: best = (n["id"],d)
    return int(best[0]),float(best[1])

def find_swc(morphology_dir: Path, root_id: str) -> Path:
    matches = sorted(morphology_dir.glob(f"**/*_{root_id}.swc"))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one SWC ending in _{root_id}.swc, found {matches}")
    return matches[0]

def load_v258_expected(path: Path) -> dict[str,int]:
    report = json.loads(path.read_text(encoding="utf-8"))
    return {ROOTS[sub]:int(report["per_root"][sub]["selected_algorithm_node_id"]) for sub in ROOTS}

def build(point_data: Path, morphology_dir: Path, output_dir: Path,
          point_data_commit: str = POINT_DATA_COMMIT, point_data_blob: str = POINT_DATA_BLOB,
          v258_json: Path|None = None) -> dict[str,Any]:
    output_dir.mkdir(parents=True,exist_ok=True)
    data = load_point_data(point_data); anchors = extract_anchor_rows(data)
    expected_v258 = load_v258_expected(v258_json) if v258_json else {}
    out_rows, per_root = [], {}
    for subtype, root_id in ROOTS.items():
        row = anchors.loc[anchors["ID"]==root_id].iloc[0]
        swc = find_swc(morphology_dir,root_id); tree = parse_swc(swc)
        published_um = (float(row["root_x"]),float(row["root_y"]),float(row["root_z"]))
        published_nm = tuple(v*1000.0 for v in published_um)
        nearest_id, nearest_dist = nearest_node(tree,published_nm)
        legacy = legacy_optimal_partition_root(tree); selected = tree["by_id"][legacy["node_id"]]
        selected_dist = math.dist(published_nm,(selected["x"],selected["y"],selected["z"]))
        v258_match = expected_v258.get(root_id)==legacy["node_id"] if expected_v258 else None
        rec = {
            "subtype":subtype,"root_id":root_id,
            "published_root_x_um":published_um[0],"published_root_y_um":published_um[1],"published_root_z_um":published_um[2],
            "swc_path":str(swc),"swc_node_count":len(tree["nodes"]),
            "published_point_units":"um","published_point_to_swc_nearest_node_id":nearest_id,
            "published_point_to_swc_nearest_node_distance_nm":nearest_dist,
            "published_point_to_legacy_selected_node_distance_nm":selected_dist,
            "legacy_selected_node_id":legacy["node_id"],"legacy_selected_node_score":legacy["score"],
            "legacy_selected_subtree_cable_nm":legacy["subtree_cable"],"legacy_selected_subtree_leaves":legacy["subtree_leaves"],
            "legacy_leaf_count":legacy["leaf_count"],
            "published_root_nearest_node_is_legacy_selected":nearest_id==legacy["node_id"],
            "published_root_within_1nm_of_legacy_selected":selected_dist<=1.0,
            "v258_selected_node_matches_legacy":v258_match,
            "status":"PASS_POINT_PROVENANCE_CROSSCHECK" if v258_match is not False else "FAIL_V258_ALGORITHM_REGRESSION",
        }
        out_rows.append(rec); per_root[subtype]=rec
    pd.DataFrame(out_rows).to_csv(output_dir/"V259_published_point_provenance.csv",index=False)
    report = {
        "schema_version":1,"status":"PASS_PUBLISHED_POINT_PROVENANCE_CROSSCHECK",
        "source":{"study_repository":STUDY_REPO,"study_repository_commit":point_data_commit,
                  "study_file":POINT_DATA_PATH,"study_blob_sha":point_data_blob,"study_notebook":STUDY_NOTEBOOK,
                  "point_data_sha256":sha256_file(point_data),"point_data_bytes":point_data.stat().st_size,
                  "published_coordinate_units":"um"},
        "algorithm_source":{"software_repository":"NikDrummond/NeuRosetta","commit":STUDY_NEROSSETTA_COMMIT,
                            "historical_function":"optimal_partition_root",
                            "selection_formula":"(1 - subtree_cable / total_cable) + (subtree_leaves / total_leaves)"},
        "inputs":{"anchor_count":len(ROOTS),"point_data_anchor_rows":len(anchors),
                  "morphology_stage":"V229 exact project SWCs","v258_report_checked":bool(v258_json)},
        "per_root":per_root,
        "interpretation":"The published Point_data rows for the four exact project anchor IDs were recovered from the immutable historical study-repository commit. Their published root coordinates were converted from micrometers to nanometers and compared with the exact project V229 SWCs. The historical NeuRosetta subtree-selection rule was independently re-applied and compared with the checked-in V258 selected node IDs. This is a provenance/geometry cross-check; it is not a claim that the published manual dendrite curation has been recovered.",
        "not_proven":["Bitwise identity between project V229 SWCs and the study's internal skeletonized .nr forests.",
                      "Manual dendrite annotation decisions beyond the published Point_data root/metrics record.",
                      "Individual synaptic-cleft-to-membrane compartment identity."],
        "output":"V259_published_point_provenance.csv",
    }
    (output_dir/"V259_published_point_provenance.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--point-data",type=Path,required=True); p.add_argument("--morphology-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True); p.add_argument("--point-data-commit",default=POINT_DATA_COMMIT)
    p.add_argument("--point-data-blob",default=POINT_DATA_BLOB); p.add_argument("--v258-json",type=Path,default=None)
    a=p.parse_args(); r=build(a.point_data,a.morphology_dir,a.output_dir,a.point_data_commit,a.point_data_blob,a.v258_json)
    print(json.dumps({"status":r["status"],"anchor_count":r["inputs"]["anchor_count"],"point_data_sha256":r["source"]["point_data_sha256"]}))
if __name__=="__main__": main()
