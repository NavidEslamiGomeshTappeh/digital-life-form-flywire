#!/usr/bin/env python3
from pathlib import Path
import csv,hashlib,json,subprocess,sys,tempfile

def run():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); source=root/"source.csv"
        source.write_text(
          "pre_root_id,post_root_id,pre_pt_position_x,pre_pt_position_y,pre_pt_position_z,post_pt_position_x,post_pt_position_y,post_pt_position_z,neuropil\n"
          "720575940632008007,123,1,2,3,4,5,6,ME_L\n"
          "123,456,7,8,9,10,11,12,ME_L\n"
          "999,720575940616224414,13,14,15,16,17,18,LO_L\n",encoding="utf-8")
        out=root/"capsule.csv"; manifest=root/"manifest.json"
        cmd=[sys.executable,"scripts/build_v231_target_capsule.py",str(source),"--output",str(out),"--manifest",str(manifest),"--source-label","TEST_SOURCE"]
        p=subprocess.run(cmd,capture_output=True,text=True); assert p.returncode==0,p.stderr
        m=json.loads(manifest.read_text(encoding="utf-8"))
        assert m["status"]=="EXACT_COORDINATE_CAPABLE"; assert m["output"]["row_count"]==2
        assert m["evidence_boundary"]["rows_are_invented"] is False
        rows=list(csv.DictReader(out.open(encoding="utf-8"))); assert len(rows)==2
        assert {int(r["post_root_id"]) for r in rows}=={123,720575940616224414}
        assert hashlib.sha256(out.read_bytes()).hexdigest()==m["output"]["sha256"]
        out2=root/"expanded.csv"; m2=root/"expanded.json"
        p2=subprocess.run([sys.executable,"scripts/build_v231_target_capsule.py",str(source),"--output",str(out2),"--manifest",str(m2),"--expand-root","456"],capture_output=True,text=True)
        assert p2.returncode==0,p2.stderr
        mm=json.loads(m2.read_text(encoding="utf-8")); assert mm["output"]["row_count"]==3
        assert "456" in mm["expansion"]["extra_roots"]
    print("V231 target capsule tests: PASS")
if __name__=="__main__": run()
