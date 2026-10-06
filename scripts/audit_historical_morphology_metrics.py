from __future__ import annotations

import hashlib
import json
import pickle
import urllib.request
from pathlib import Path

import pandas as pd

BASE="https://raw.githubusercontent.com/borstlab/T4_T5_Dendrite_Morphology_Paper/56901ad1853b44aeca15504cd908fa4c31009a3e/Data/"
FILES={
  "Point_data": ("Point_data.pkl","76b7d6a1c44ad6b2ca730feff88174c71327e095cce45d8a47a0d998f77df58f"),
  "Vertex_data": ("Vertex_data.pkl",""),
  "Edge_data": ("Edge_data.pkl",""),
}
ANCHORS={
 "T4a":720575940632008007,
 "T4c":720575940616224414,
 "T5a":720575940625571465,
 "T5c":720575940617782941,
}
def fetch(name):
 p=Path("/tmp/"+name+".pkl")
 urllib.request.urlretrieve(BASE+FILES[name][0],p)
 return p
def load(p):
 with p.open("rb") as f: x=pickle.load(f)
 if not isinstance(x,pd.DataFrame): raise TypeError(type(x))
 return x

paths={n:fetch(n) for n in FILES}
dfs={n:load(p) for n,p in paths.items()}
r={
 "files":{
  n:{"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"shape":list(dfs[n].shape),
     "columns":[str(c) for c in dfs[n].columns],"dtypes":{str(c):str(t) for c,t in dfs[n].dtypes.items()}}
  for n,p in paths.items()
 },
 "anchors":{}
}
for subtype, rid in ANCHORS.items():
 p=dfs["Point_data"][dfs["Point_data"]["ID"]==rid].iloc[0]
 v=dfs["Vertex_data"][dfs["Vertex_data"]["ID"]==rid]
 e=dfs["Edge_data"][dfs["Edge_data"]["ID"]==rid]
 leaves=int((v["Out_degree"]==0).sum()) if len(v) else None
 branches=int((v["Out_degree"]>1).sum()) if len(v) else None
 ext=int(e["isExternal"].sum()) if len(e) else None
 internal=int((~e["isExternal"]).sum()) if len(e) else None
 total=float(e["Length"].sum()) if len(e) else None
 r["anchors"][subtype]={
  "id":int(rid),
  "point_data":{
   "segment_count":int(p["Segment_Count"]),
   "vertices_numbers":int(p["Vertices_numbers"]),
   "external_edge_count":int(p["External_edge_count"]),
   "internal_edge_count":int(p["Internal_edge_count"]),
   "leaf_number":int(p["Leaf_number"]),
   "branch_number":int(p["Branch_number"]),
   "total_cable_um":float(p["Total_Cable"]),
   "root":[float(p["Root_x"]),float(p["Root_y"]),float(p["Root_z"])]
  },
  "vertex_data":{"rows":len(v),"leaf_by_out_degree_0":leaves,"branch_by_out_degree_gt1":branches},
  "edge_data":{"rows":len(e),"external_edges":ext,"internal_edges":internal,"length_sum_um":total},
  "consistency":{
   "segment_count_eq_edge_rows":int(p["Segment_Count"])==len(e),
   "vertices_numbers_eq_vertex_rows":int(p["Vertices_numbers"])==len(v),
   "external_edge_count_eq_edge_flag":int(p["External_edge_count"])==ext,
   "internal_edge_count_eq_edge_flag":int(p["Internal_edge_count"])==internal,
   "total_cable_abs_error_um":None if total is None else abs(float(p["Total_Cable"])-total),
   "leaf_number_eq_out_degree_zero":int(p["Leaf_number"])==leaves,
   "branch_number_eq_out_degree_gt1":int(p["Branch_number"])==branches,
  }
 }
}
print(json.dumps(r,indent=2,default=str))
Path("historical_morphology_metric_consistency.json").write_text(json.dumps(r,indent=2,default=str),encoding="utf-8")
