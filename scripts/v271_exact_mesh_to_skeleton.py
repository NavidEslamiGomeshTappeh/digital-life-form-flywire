#!/usr/bin/env python3
import json, pickle, pathlib, math
import numpy as np, pandas as pd
from fafbseg import flywire as fwy
import navis

IDS=[720575940632008007,720575940616224414,720575940625571465,720575940617782941]
OUT=pathlib.Path("v271_results"); OUT.mkdir(exist_ok=True)
with open("/tmp/Point_data.pkl","wb") as f:
    import urllib.request
    f.write(urllib.request.urlopen("https://raw.githubusercontent.com/borstlab/T4_T5_Dendrite_Morphology_Paper/56901ad1853b44aeca15504cd908fa4c31009a3e/Data/Point_data.pkl").read())
with open("/tmp/Point_data.pkl","rb") as f: point=pickle.load(f)

rows=[]
for rid in IDS:
    p=point[point.ID==rid].iloc[0]
    m=fwy.get_mesh_neuron(rid, omit_failures=False, progress=True, dataset='flat_783')
    s=m.skeletonize()
    if getattr(s,'units',None) is None: s.units='1 nm'
    navis.resample_skeleton(s, resample_to=100, inplace=True)
    root=s.nodes.loc[s.root, ['x','y','z']].to_numpy(dtype=float)
    rpoint=np.array([p.Root_x,p.Root_y,p.Root_z],float)
    rows.append(dict(ID=rid,Subtype=p.Subtype,Point_x=rpoint[0],Point_y=rpoint[1],Point_z=rpoint[2],
                     mesh_vertices=int(m.vertices.shape[0]),mesh_faces=int(m.faces.shape[0]),
                     skel_nodes=int(len(s.nodes)),skel_root_x=root[0]/1000,skel_root_y=root[1]/1000,skel_root_z=root[2]/1000,
                     residual_x=root[0]/1000-rpoint[0],residual_y=root[1]/1000-rpoint[1],residual_z=root[2]/1000-rpoint[2],
                     residual_um=float(np.linalg.norm(root/1000-rpoint))))
df=pd.DataFrame(rows)
df.to_csv(OUT/"V271_mesh_skeleton_roots.csv",index=False)
summary={"versions":{"navis":navis.__version__,"fafbseg":fwy.__package__},"dataset_default":"fafbseg.get_mesh_neuron default","residuals":df.to_dict(orient="records"),
          "rms_um":float(np.sqrt(np.mean(df.residual_um**2))),"max_um":float(df.residual_um.max())}
(OUT/"V271_summary.json").write_text(json.dumps(summary,indent=2,default=str))
print(json.dumps(summary,indent=2,default=str))
