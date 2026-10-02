#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import polars as pl

SOURCE_URL="https://storage.googleapis.com/flywire-data/codex/data/fafb/783/fafb_v783_princeton_synapse_table.csv.gz"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True)
    ap.add_argument("--target",default="v230_results/V230_target_synapses.csv")
    ap.add_argument("--output",default="/tmp/V244_fast_princeton_provenance.json")
    a=ap.parse_args()

    target=(pl.scan_csv(a.target,schema_overrides={
        "pre_root_id":pl.Utf8,"post_root_id":pl.Utf8,
        "x":pl.Int64,"y":pl.Int64,"z":pl.Int64
    }).select(["pre_root_id","post_root_id","x","y","z"])
      .with_columns(pl.lit("v230").alias("target_marker")))

    pairs=target.select(["pre_root_id","post_root_id"]).unique()

    src=pl.scan_csv(a.source,schema_overrides={
        "pre_x":pl.Int64,"pre_y":pl.Int64,"pre_z":pl.Int64,
        "post_x":pl.Int64,"post_y":pl.Int64,"post_z":pl.Int64,
        "ctr_x":pl.Int64,"ctr_y":pl.Int64,"ctr_z":pl.Int64,
        "pre_root_id_720575940":pl.Utf8,"post_root_id_720575940":pl.Utf8
    })

    src=src.rename({
        "pre_root_id_720575940":"pre_root_id",
        "post_root_id_720575940":"post_root_id"
    }).with_columns([
        (pl.lit("720575940000000000").cast(pl.Int64)+pl.col("pre_root_id").cast(pl.Int64)).cast(pl.Utf8).alias("pre_root_id"),
        (pl.lit("720575940000000000").cast(pl.Int64)+pl.col("post_root_id").cast(pl.Int64)).cast(pl.Utf8).alias("post_root_id")
    ]).select([
        "pre_root_id","post_root_id",
        "pre_x","pre_y","pre_z",
        "post_x","post_y","post_z",
        "ctr_x","ctr_y","ctr_z"
    ])

    # Restrict the 2.7 GB source to the 75 target directed pairs first.
    candidates=src.join(pairs,on=["pre_root_id","post_root_id"],how="inner")
    candidates=candidates.with_columns([
        ((pl.col("pre_x")+pl.col("post_x"))/2).cast(pl.Int64).alias("x"),
        ((pl.col("pre_y")+pl.col("post_y"))/2).cast(pl.Int64).alias("y"),
        ((pl.col("pre_z")+pl.col("post_z"))/2).cast(pl.Int64).alias("z")
    ])

    joined=(target.join(candidates,on=["pre_root_id","post_root_id","x","y","z"],how="left")
        .collect(engine="streaming"))

    matched=joined.filter(pl.col("pre_x").is_not_null())
    ambiguous=(matched.group_by(["pre_root_id","post_root_id","x","y","z"])
               .len().filter(pl.col("len")!=1).height)

    ctr_equal=(matched.filter(
        (pl.col("ctr_x")==pl.col("x")) &
        (pl.col("ctr_y")==pl.col("y")) &
        (pl.col("ctr_z")==pl.col("z"))
    ).height)

    pair_target=target.group_by(["pre_root_id","post_root_id"]).len().rename({"len":"v230_rows"})
    pair_source=(src.join(pairs,on=["pre_root_id","post_root_id"],how="inner")
                   .group_by(["pre_root_id","post_root_id"]).len().rename({"len":"source_rows"}))
    pair_counts=pair_target.join(pair_source,on=["pre_root_id","post_root_id"],how="left").with_columns(
        pl.col("source_rows").fill_null(0)
    ).collect(engine="streaming")
    pair_equal=bool((pair_counts["v230_rows"]==pair_counts["source_rows"]).all())

    mappings=(
        matched.select([
            "pre_root_id","post_root_id","x","y","z",
            "pre_x","pre_y","pre_z","post_x","post_y","post_z",
            "ctr_x","ctr_y","ctr_z"
        ]).to_dicts()
    )
    result={
        "status":"EXACT_MIDPOINT_AND_CTR" if matched.height==649 and ambiguous==0 and ctr_equal==649 and pair_equal else "INCOMPLETE",
        "source_dataset":"FlyWire FAFB v783 Princeton Synapse Table",
        "source_url":SOURCE_URL,
        "v230_rows":649,
        "target_pairs":int(pairs.height),
        "matched_midpoint_rows":int(matched.height),
        "ambiguous_matches":int(ambiguous),
        "ctr_equals_v230_midpoint":int(ctr_equal),
        "pair_counts_equal":pair_equal,
        "formula":"v230 xyz = (pre_xyz + post_xyz) / 2",
        "root_id_reconstruction":"720575940000000000 + 9-digit suffix from *_720575940 columns",
        "ctr_formula_check":"ctr xyz == v230 xyz",
        "mapping":mappings,
        "pair_counts":pair_counts.sort(["pre_root_id","post_root_id"]).to_dicts()
    }
    Path(a.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({k:result[k] for k in [
        "status","v230_rows","target_pairs","matched_midpoint_rows",
        "ambiguous_matches","ctr_equals_v230_midpoint","pair_counts_equal"
    ]},sort_keys=True))
    return 0 if result["status"]=="EXACT_MIDPOINT_AND_CTR" else 2

if __name__=="__main__":
    raise SystemExit(main())
