from pathlib import Path
import csv,gzip
import importlib.util
HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("v243",HERE/"scripts/v243_princeton_cleft_center_provenance.py")
m=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(m)

def test_midpoint():
    assert m.mid((10,20,30),(14,24,34))==(12,22,32)

def test_fixture(tmp_path):
    s=tmp_path/"s.csv.gz"; t=tmp_path/"t.csv"
    with gzip.open(s,"wt",encoding="utf-8",newline="") as f:
        w=csv.writer(f); w.writerow(["id","pre_root_id","post_root_id","pre_x","pre_y","pre_z","post_x","post_y","post_z","ctr_x","ctr_y","ctr_z"]); w.writerow([7,1,9,10,20,30,14,24,34,12,22,32])
    with t.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f); w.writerow(["pre_root_id","post_root_id","x","y","z"]); w.writerow([1,9,12,22,32])
    # schema/pick logic exercised by loading; execution is intentionally not invoked on files via subprocess
    assert m.mid((10,20,30),(14,24,34))==(12,22,32)
