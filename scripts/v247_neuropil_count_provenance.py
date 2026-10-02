import argparse,json
from pathlib import Path
import polars as pl
URL="https://storage.googleapis.com/flywire-data/codex/data/fafb/783/connections_princeton.csv.gz"

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--source",required=True); ap.add_argument("--target",default="v230_results/V230_target_synapses.csv"); ap.add_argument("--output",default="/tmp/V247.json"); a=ap.parse_args()
 t=(pl.scan_csv(a.target,schema_overrides={"pre_root_id":pl.Utf8,"post_root_id":pl.Utf8})
    .group_by(["pre_root_id","post_root_id"]).len().rename({"len":"v230_rows"}))
 s=pl.scan_csv(a.source,schema_overrides={"pre_root_id":pl.Utf8,"post_root_id":pl.Utf8,"syn_count":pl.Int64,"neuropil":pl.Utf8})
 per=s.select(["pre_root_id","post_root_id","neuropil","syn_count"]).collect(engine="streaming")
 targets=t.collect(engine="streaming")
 j=targets.join(per,on=["pre_root_id","post_root_id"],how="left")
 matches=[]
 for row in targets.iter_rows(named=True):
   sub=per.filter((pl.col("pre_root_id")==row["pre_root_id"])&(pl.col("post_root_id")==row["post_root_id"]))
   vals=sub.to_dicts()
   exact=[x for x in vals if x["syn_count"]==row["v230_rows"]]
   nearest=min(vals,key=lambda x:abs(int(x["syn_count"])-int(row["v230_rows"]))) if vals else None
   matches.append({**row,"neuropil_exact_matches":exact,"nearest_neuropil":nearest})
 exact_pairs=sum(1 for x in matches if x["neuropil_exact_matches"])
 nearest_dist=sorted(abs(int(x["v230_rows"])-int(x["nearest_neuropil"]["syn_count"])) for x in matches if x["nearest_neuropil"])
 result={"status":"REPORT_ONLY","v230_rows":int(targets["v230_rows"].sum()),"v230_pairs":targets.height,"pairs_matching_a_single_neuropil_count":exact_pairs,"nearest_abs_diff_median":nearest_dist[len(nearest_dist)//2],"nearest_abs_diff_max":max(nearest_dist),"pair_results":matches,"source_url":URL}
 Path(a.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
 print(json.dumps({"pairs_matching_a_single_neuropil_count":exact_pairs,"v230_rows":result["v230_rows"],"v230_pairs":result["v230_pairs"],"nearest_abs_diff_median":result["nearest_abs_diff_median"],"nearest_abs_diff_max":result["nearest_abs_diff_max"]}))
 return 0

if __name__=="__main__": raise SystemExit(main())
