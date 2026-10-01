#!/usr/bin/env python3
"""Compare V230 neuron pairs with the official FAFB v783 proofread connections."""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import pyarrow.feather as feather

TARGETS = {
    720575940632008007,
    720575940616224414,
    720575940625571465,
    720575940617782941,
}
COLUMNS = ["pre_pt_root_id", "post_pt_root_id", "syn_count"]


def load_v230(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    pairs = defaultdict(int)
    for r in rows:
        pairs[(int(r["pre_root_id"]), int(r["post_root_id"]))] += 1
    return pairs


def main():
    p = argparse.ArgumentParser()
    p.add_argument("proofread_feather")
    p.add_argument("--artifact", default="v230_results/V230_target_synapses.csv")
    p.add_argument("--output", default="v230_results/V230_proofread_pair_probe.json")
    args = p.parse_args()

    wanted = load_v230(args.artifact)
    source_pairs = defaultdict(int)
    table = feather.read_table(args.proofread_feather, columns=COLUMNS, memory_map=True)
    for batch in table.to_batches(max_chunksize=250_000):
        pre = batch["pre_pt_root_id"]
        post = batch["post_pt_root_id"]
        count = batch["syn_count"]
        for i in range(batch.num_rows):
            pair = (int(pre[i].as_py()), int(post[i].as_py()))
            if pair in wanted:
                source_pairs[pair] += int(count[i].as_py())

    missing = sorted(wanted.keys() - source_pairs.keys())
    below_five = sorted(
        (list(pair), int(source_pairs[pair]))
        for pair in wanted
        if pair in source_pairs and source_pairs[pair] < 5
    )
    result = {
        "dataset": "FAFB v783",
        "source": str(Path(args.proofread_feather)),
        "artifact": args.artifact,
        "v230_pair_count": len(wanted),
        "source_pair_matches": len(source_pairs),
        "missing_pairs": len(missing),
        "pairs_below_5_source_synapses": len(below_five),
        "all_v230_pairs_present": not missing,
        "all_present_pairs_have_at_least_5_synapses": not below_five,
        "status": "PAIR_MATCH" if not missing else "PAIR_MISMATCH",
        "note": "Pair membership/count validation only; this does not validate V230 coordinate rows.",
        "pairs": {
            f"{pre}->{post}": {
                "v230_coordinate_rows": wanted[(pre, post)],
                "source_synapse_count": source_pairs.get((pre, post), 0),
            }
            for pre, post in sorted(wanted)
        },
    }
    if missing:
        result["missing_pair_sample"] = [list(pair) for pair in missing[:20]]
    if below_five:
        result["below_five_sample"] = below_five[:20]

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
