#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import polars as pl
URL="https://storage.googleapis.com/flywire-data/codex/data/fafb/783/connections_princeton.csv.gz"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True)
    ap.add_argument("--target",default="v230_results/V230_target_synapses.csv")
    ap.add_argument("--output",default="/tmp/V246_connection_count_provenance.json")
    a=ap.parse_args()
    t=(pl.scan_csv(a.target,schema_overrides={"pre_root_id":pl.Utf8,"post_root_id":pl.Utf8})
       .group_by(["pre_root_id","post_root_id"]).len().rename({"len":"v230_rows"}))
    s=(pl.scan_csv(a.source,schema_overrides={"pre_root_id":pl.Utf8,"post_root_id":pl.Utf8,"syn_count":pl.Int64})
       .group_by(["pre_root_id","post_root_id"]).agg(pl.col("syn_count").sum().alias("syn_count_sum")))
    j=t.join(s,on=["pre_root_id","post_root_id"],how="left").with_columns(pl.col("syn_count_sum").fill_null(0)).collect(engine="streaming")
    exact=int((j["v230_rows"]==j["syn_count_sum"]).sum())
    result={
      "status":"EXACT_COUNT_EXPANSION" if exact==75 else "INCOMPLETE",
      "v230_rows":649,"v230_pairs":75,"pairs_exact_count_match":exact,
      "all_pairs_exact_count_match":exact==75,
      "total_v230_rows":int(j["v230_rows"].sum()),
      "total_syn_count_for_75_pairs":int(j["syn_count_sum"].sum()),
      "pair_results":j.sort(["pre_root_id","post_root_id"]).to_dicts(),
      "source_url":URL,
      "interpretation":"V230 rows per directed pair are the individual synapse expansion of the official Princeton connections syn_count values when all 75 pairs match."
    }
    Path(a.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({k:result[k] for k in ["status","v230_rows","v230_pairs","pairs_exact_count_match","total_v230_rows","total_syn_count_for_75_pairs"]},sort_keys=True))
    return 0 if result["status"]=="EXACT_COUNT_EXPANSION" else 2
if __name__=="__main__": raise SystemExit(main())
