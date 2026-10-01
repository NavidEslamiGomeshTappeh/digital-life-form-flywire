#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,shutil,time,tempfile,platform
from urllib.request import Request,urlopen
ROOTS={"T4a":720575940632008007,"T4c":720575940616224414,"T5a":720575940625571465,"T5c":720575940617782941}
VFB_IDS={"T4a":"VFB_fw077172","T4c":"VFB_fw091869","T5a":"VFB_fw056211","T5c":"VFB_fw077474"}
MRC_BASE="https://flyem.mrc-lmb.cam.ac.uk/flyconnectome/flywire_skeletons_783"
ZENODO_URL="https://zenodo.org/records/10877326/files/sk_lod1_783_healed_ds2.parquet?download=1"
ZENODO_MD5="a4c104776f33ec539ef859064c4de3df"
VERSION="0.229.0"
def digest(p,a="sha256"):
 h=hashlib.new(a)
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1048576),b""): h.update(b)
 return h.hexdigest()
def neuron_id_as_int(neuron):
    """Return the source neuron/root ID without inventing one."""
    value = getattr(neuron, "id", None)
    if value is None:
        raise RuntimeError("source neuron has no ID")
    try:
        return int(value)
    except (TypeError, ValueError) as e:
        raise RuntimeError(f"source neuron ID is not an integer: {value!r}") from e

def verify_swc(p,rid):
 rows=[]
 for line in open(p,encoding="utf-8",errors="replace"):
  if not line.strip() or line.lstrip().startswith("#"): continue
  x=line.split()
  if len(x)>=7:
   try: rows.append((int(x[0]),float(x[2]),float(x[3]),float(x[4]),float(x[5]),int(x[6])))
   except: pass
 ids={x[0] for x in rows}; roots=[x[0] for x in rows if x[5]==-1]; missing=sorted({x[5] for x in rows if x[5]!=-1}-ids)
 finite=all(all(v==v and abs(v)!=float("inf") for v in x[1:5]) for x in rows)
 return {"requested_root_id":rid,"node_count":len(rows),"structural_root_count":len(roots),"missing_parent_refs":missing,"finite_geometry":finite,"sha256":digest(p),"valid":bool(rows) and len(roots)==1 and not missing and finite}
def route1(rid,out):
 from fafbseg import flywire; import navis
 n=flywire.get_skeletons(rid,dataset=783,progress=False)
 if neuron_id_as_int(n)!=rid: raise RuntimeError(f"root ID mismatch: requested {rid}, received {getattr(n, 'id', None)!r}")
 navis.write_swc(n,out); a=verify_swc(out,rid)
 if not a["valid"]: raise RuntimeError("SWC validation failed")
 return a
def route2(rid,out):
 import navis
 n=navis.read_precomputed(f"{MRC_BASE}/{rid}")
 if isinstance(n, navis.NeuronList):
  if len(n) != 1: raise RuntimeError(f"precomputed endpoint returned {len(n)} neurons")
  n = n[0]
 source_id = neuron_id_as_int(n)
 if source_id != rid: raise RuntimeError(f"root ID mismatch: requested {rid}, received {source_id}")
 navis.write_swc(n,out); a=verify_swc(out,rid)
 if not a["valid"]: raise RuntimeError("SWC validation failed")
 return a
def download(url,p,md5=None):
 p.parent.mkdir(parents=True,exist_ok=True)
 with urlopen(Request(url,headers={"User-Agent":"V229-Recovery-Runner/1.0"}),timeout=120) as r,open(p,"wb") as f:
  while (b:=r.read(8388608)): f.write(b)
 if md5 and digest(p,"md5").lower()!=md5.lower(): raise RuntimeError("MD5 mismatch")
def route3(rid,out,cache):
 import pyarrow.parquet as pq
 p=cache/"sk_lod1_783_healed_ds2.parquet"
 if not p.exists(): download(ZENODO_URL,p,ZENODO_MD5)
 pf=pq.ParquetFile(p); cols=set(pf.schema_arrow.names); rc=next((c for c in ("root_id","rootId","id","segment_id","segment") if c in cols),None)
 if not rc: raise RuntimeError(f"root-id column not found: {sorted(cols)}")
 tab=pq.read_table(p,filters=[(rc,"=",rid)])
 if tab.num_rows==0: raise RuntimeError(f"root {rid} not found")
 raise RuntimeError("Zenodo reached but schema is not a verified node-table; no approximation made")
def main():
 ap=argparse.ArgumentParser(description="Recover and validate exact FlyWire v783 neuron skeletons.")
 ap.add_argument("--version",action="version",version=VERSION)
 ap.add_argument("--route",choices=["all","1","2","3"],default="all"); ap.add_argument("--only",nargs="*",choices=list(ROOTS),default=list(ROOTS)); ap.add_argument("--out",default="v229_recovery_results"); ap.add_argument("--cache",default="v229_cache"); a=ap.parse_args(); out=Path(a.out); cache=Path(a.cache); out.mkdir(parents=True,exist_ok=True); report={"schema_version":1,"runner_version":VERSION,"dataset":783,"route_order":[1,2,3],"python":platform.python_version(),"cells":[]}
 for name in a.only:
  rid=ROOTS[name]; rec={"cell":name,"root_id":rid,"vfb_id":VFB_IDS[name],"attempts":[]}
  for route in ([1,2,3] if a.route=="all" else [int(a.route)]):
   tmp=out/f".{name}_{rid}.route{route}.tmp.swc"; t=time.time()
   try:
    aa=route1(rid,tmp) if route==1 else route2(rid,tmp) if route==2 else route3(rid,tmp,cache); shutil.copy2(tmp,out/f"{name}_{rid}.swc"); tmp.unlink(missing_ok=True); rec["attempts"].append({"route":route,"status":"PASS","seconds":round(time.time()-t,3),"audit":aa}); rec["selected_route"]=route; rec["status"]="PASS"; break
   except Exception as e:
    rec["attempts"].append({"route":route,"status":"FAIL","seconds":round(time.time()-t,3),"error":f"{type(e).__name__}: {e}"})
    if tmp.exists(): tmp.unlink()
  else: rec["status"]="FAIL"
  report["cells"].append(rec)
 (out/"V229_recovery_report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)); return 0 if all(x["status"]=="PASS" for x in report["cells"]) else 2
if __name__=="__main__": raise SystemExit(main())
