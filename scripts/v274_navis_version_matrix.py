#!/usr/bin/env python3
import json, pickle, pathlib, urllib.request, math
import numpy as np, pandas as pd
from fafbseg import flywire as fwy
import navis
IDS=[720575940632008007,720575940616224414,720575940625571465,720575940617782941]
SUB={IDS[0]:"T4a",IDS[1]:"T4c",IDS[2]:"T5a",IDS[3]:"T5c"}
URL="https://raw.githubusercontent.com/borstlab/T4_T5_Dendrite_Morphology_Paper/56901ad1853b44aeca15504cd908fa4c31009a3e/Data/Point_data.pkl"
p="/tmp/Point_data.pkl"; open(p,"wb").write(urllib.request.urlopen(URL).read())
with open(p,"rb") as f: df=pickle.load(f)
out=pathlib.Path("v274_results"); out.mkdir(exist_ok=True)
rows=[]
for rid in IDS:
    pnt=df[df.ID==rid].iloc[0]
    m=fwy.get_mesh_neuron(rid, omit_failures=False, progress=False, dataset="flat_783")
    s=m.skeletonize()
    navis.resample_skeleton(s,resample_to="100 nanometer",inplace=True)
    pp3={720575940632008007:292,720575940616224414:358,720575940625571465:343,720575940617782941:323}[rid]
    if pp3 not in set(s.nodes.node_id.astype(int)):
        raise RuntimeError(f"{rid}: expected PP3 node {pp3} absent")
    row=s.nodes.set_index("node_id").loc[pp3,["x","y","z"]].to_numpy(float)/1000
    target=np.array([pnt.Root_x,pnt.Root_y,pnt.Root_z],float)
    rows.append({"ID":rid,"Subtype":SUB[rid],"navis":navis.__version__,"skel_nodes":len(s.nodes),
                  "pp3_x_um":row[0],"pp3_y_um":row[1],"pp3_z_um":row[2],
                  "point_x_um":target[0],"point_y_um":target[1],"point_z_um":target[2],
                  "residual_um":float(np.linalg.norm(row-target))})
pd.DataFrame(rows).to_csv(out/"V274_matrix_result.csv",index=False)
summary={"navis":navis.__version__,"fafbseg":fwy.__package__,"rows":rows}
(out/"V274_summary.json").write_text(json.dumps(summary,indent=2,default=str)); print(json.dumps(summary,indent=2,default=str))
