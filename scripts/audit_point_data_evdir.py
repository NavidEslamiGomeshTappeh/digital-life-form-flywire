from __future__ import annotations
import hashlib, json, math, urllib.request
from pathlib import Path
import pandas as pd

URL=("https://raw.githubusercontent.com/borstlab/T4_T5_Dendrite_Morphology_Paper/"
     "cd17d34afd0d46a3c2947e83a1f0fdd835a9959a/Data/Point_data.pkl")
EXPECTED="76b7d6a1c44ad6b2ca730feff88174c71327e095cce45d8a47a0d998f77df58f"
raw=Path("/tmp/Point_data.pkl")
with urllib.request.urlopen(URL,timeout=60) as r: data=r.read()
raw.write_bytes(data)
sha=hashlib.sha256(data).hexdigest()
if sha!=EXPECTED: raise RuntimeError(f"SHA mismatch {sha}")
df=pd.read_pickle(raw)
vcols=["Subtype_evDir_x","Subtype_evDir_y","Subtype_evDir_z"]
need=vcols+["PC1_angle","PC1","PC2","PC3","Type","Subtype"]
miss=[c for c in need if c not in df.columns]
if miss: raise RuntimeError(f"missing {miss}")

def f(v): return float(v.item()) if hasattr(v,"item") else float(v)

# Signed angle from vector v to target basis axis about normal axis.
# The vector is first sign-aligned to the positive target axis, matching align_with semantics.
def angle_to_axis(v,target,normal):
    vv=[f(x) for x in v]
    t=[0.,0.,0.]; n=[0.,0.,0.]
    t[target]=1.; n[normal]=1.
    dot=sum(vv[i]*t[i] for i in range(3))
    if dot<0: vv=[-x for x in vv]; dot=-dot
    # cross(v,target) dot normal
    cr=[
      vv[1]*t[2]-vv[2]*t[1],
      vv[2]*t[0]-vv[0]*t[2],
      vv[0]*t[1]-vv[1]*t[0],
    ]
    s=cr[normal]
    return math.atan2(s,dot)

axes={"x":0,"y":1,"z":2}
candidates=[]
for tname,t in axes.items():
    for nname,n in axes.items():
        if t==n: continue
        candidates.append((tname+"<-"+nname,t,n))

global_deltas={name:[] for name,_,_ in candidates}
sub_rows={}

for subtype,g in df.groupby("Subtype",sort=True):
    entry={"subtype":str(subtype),"rows":int(len(g))}
    for name,t,n in candidates:
        ds=[]
        for _,row in g.iterrows():
            a=angle_to_axis([row[c] for c in vcols],t,n)
            p=f(row["PC1_angle"])
            d=(a-p+math.pi)%(2*math.pi)-math.pi
            ds.append(d); global_deltas[name].append(d)
        ad=[abs(x) for x in ds]
        entry[name]={
            "median_abs_delta_rad":float(pd.Series(ad).median()),
            "rmse_rad":float(math.sqrt(sum(x*x for x in ds)/len(ds))),
            "within_1e-4_fraction":float(sum(x<=1e-4 for x in ad)/len(ad)),
            "within_1e-6_fraction":float(sum(x<=1e-6 for x in ad)/len(ad)),
        }
    sub_rows[str(subtype)]=entry

best=[]
for name,ds in global_deltas.items():
    ad=[abs(x) for x in ds]
    best.append({
        "candidate":name,
        "median_abs_delta_rad":float(pd.Series(ad).median()),
        "rmse_rad":float(math.sqrt(sum(x*x for x in ds)/len(ds))),
        "within_1e-4_fraction":float(sum(x<=1e-4 for x in ad)/len(ad)),
        "within_1e-6_fraction":float(sum(x<=1e-6 for x in ad)/len(ad)),
    })
best.sort(key=lambda x:x["rmse_rad"])

out={
 "status":"PROVEN_EVDIR_PC1_AXIS_CONVENTION_MATRIX",
 "source":{"url":URL,"sha256":sha,"rows":len(df),"columns":len(df.columns)},
 "candidates_ranked_global":best,
 "by_subtype":sub_rows,
 "interpretation":"Tests all six orthogonal target-axis/plane-normal conventions for the stored Subtype_evDir vector against historical PC1_angle after sign alignment to the target axis. This identifies whether the mismatch is explained by an axis/plane convention alone."
}
Path("evdir_axis_convention_receipt.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
print(json.dumps(out,indent=2))
