from __future__ import annotations

import hashlib
import json
import math
import os
import urllib.request
from pathlib import Path

import pandas as pd

URL = (
    "https://raw.githubusercontent.com/borstlab/T4_T5_Dendrite_Morphology_Paper/"
    "cd17d34afd0d46a3c2947e83a1f0fdd835a9959a/Data/Point_data.pkl"
)
EXPECTED = "76b7d6a1c44ad6b2ca730feff88174c71327e095cce45d8a47a0d998f77df58f"
raw = Path("/tmp/Point_data.pkl")
local_source = os.environ.get("POINT_DATA_LOCAL_PATH")

if local_source:
    data = Path(local_source).read_bytes()
else:
    with urllib.request.urlopen(URL, timeout=60) as response:
        data = response.read()

raw.write_bytes(data)
sha = hashlib.sha256(data).hexdigest()
if sha != EXPECTED:
    raise RuntimeError(f"SHA mismatch: {sha}")

df = pd.read_pickle(raw)
vcols = ["Subtype_evDir_x", "Subtype_evDir_y", "Subtype_evDir_z"]
need = vcols + ["PC1_angle", "PC1", "PC2", "PC3", "Type", "Subtype"]
missing = [column for column in need if column not in df.columns]
if missing:
    raise RuntimeError(f"Missing required columns: {missing}")


def scalar_float(value):
    return float(value.item()) if hasattr(value, "item") else float(value)


def angle_to_axis(vector, target_axis, normal_axis):
    """Signed angle vector->target after sign alignment, in the target/normal plane."""
    v = [scalar_float(item) for item in vector]
    target = [0.0, 0.0, 0.0]
    normal = [0.0, 0.0, 0.0]
    target[target_axis] = 1.0
    normal[normal_axis] = 1.0

    dot = sum(v[i] * target[i] for i in range(3))
    if dot < 0:
        v = [-item for item in v]
        dot = -dot

    cross = [
        v[1] * target[2] - v[2] * target[1],
        v[2] * target[0] - v[0] * target[2],
        v[0] * target[1] - v[1] * target[0],
    ]
    sine_component = sum(cross[i] * normal[i] for i in range(3))
    # The vectors may have a component normal to the measurement plane.
    projected_dot = dot - sum(v[i] * normal[i] for i in range(3)) * sum(
        target[i] * normal[i] for i in range(3)
    )
    return math.atan2(sine_component, projected_dot)


def wrapped_delta(angle, reference):
    return (angle - reference + math.pi) % (2 * math.pi) - math.pi


def summarize_deltas(deltas):
    absolute = [abs(delta) for delta in deltas]
    return {
        "rows": len(deltas),
        "median_abs_delta_rad": float(pd.Series(absolute).median()),
        "rmse_rad": float(math.sqrt(sum(delta * delta for delta in deltas) / len(deltas))),
        "within_1e-4_fraction": float(sum(value <= 1e-4 for value in absolute) / len(absolute)),
        "within_1e-6_fraction": float(sum(value <= 1e-6 for value in absolute) / len(absolute)),
    }


axes = {"x": 0, "y": 1, "z": 2}
candidates = [
    (target_name + "<-" + normal_name, target_axis, normal_axis)
    for target_name, target_axis in axes.items()
    for normal_name, normal_axis in axes.items()
    if target_axis != normal_axis
]

global_deltas = {name: [] for name, _, _ in candidates}
subtype_rows = {}
vectors = []
for _, row in df.iterrows():
    vectors.append([scalar_float(row[column]) for column in vcols])

for subtype, group in df.groupby("Subtype", sort=True):
    entry = {"subtype": str(subtype), "rows": int(len(group))}
    for name, target_axis, normal_axis in candidates:
        deltas = []
        for _, row in group.iterrows():
            angle = angle_to_axis(
                [row[column] for column in vcols], target_axis, normal_axis
            )
            delta = wrapped_delta(angle, scalar_float(row["PC1_angle"]))
            deltas.append(delta)
            global_deltas[name].append(delta)
        entry[name] = summarize_deltas(deltas)
        entry[name]["rows"] = int(len(deltas))
    subtype_rows[str(subtype)] = entry

ranked_candidates = []
for name, deltas in global_deltas.items():
    result = summarize_deltas(deltas)
    result["candidate"] = name
    ranked_candidates.append(result)
ranked_candidates.sort(key=lambda item: item["rmse_rad"])

# Test an explicit candidate selection rule, without promoting it to provenance fact:
# a/b compare against the x-axis (a PC2-like in-plane relation); c/d compare against y
# (a PC1-like in-plane relation). This only tests angles; it cannot identify eigenvector
# indices without the historical morphology/eigenvector output.
axis_by_subtype = {
    subtype: ("x" if subtype[-1] in {"a", "b"} else "y")
    for subtype in sorted(df["Subtype"].astype(str).unique())
}
selected_rule_deltas = []
selected_rule_by_subtype = {}
abs_z_by_subtype = {}
for subtype, group in df.groupby("Subtype", sort=True):
    target_name = axis_by_subtype[str(subtype)]
    target_axis = axes[target_name]
    deltas = []
    abs_z = []
    for _, row in group.iterrows():
        vector = [row[column] for column in vcols]
        candidate_angle = angle_to_axis(vector, target_axis, axes["z"])
        delta = wrapped_delta(candidate_angle, scalar_float(row["PC1_angle"]))
        deltas.append(delta)
        selected_rule_deltas.append(delta)
        abs_z.append(abs(scalar_float(row["Subtype_evDir_z"])))
    selected_rule_by_subtype[str(subtype)] = {
        "target_axis": target_name,
        **summarize_deltas(deltas),
    }
    abs_z_by_subtype[str(subtype)] = {
        "median_abs_z_component": float(pd.Series(abs_z).median()),
        "mean_abs_z_component": float(pd.Series(abs_z).mean()),
    }

rule_rmse = float(math.sqrt(sum(delta * delta for delta in selected_rule_deltas) / len(selected_rule_deltas)))
universal_y = next(item for item in ranked_candidates if item["candidate"] == "y<-z")
rule = {
    "classification": "HYPOTHESIS_ONLY",
    "candidate_rule": "a/b compare Subtype_evDir to +x; c/d compare it to +y, measuring in the xy plane around +z.",
    "candidate_axis_by_subtype": axis_by_subtype,
    "per_subtype": selected_rule_by_subtype,
    "weighted_global_rmse_rad": rule_rmse,
    "weighted_global_rmse_deg": float(math.degrees(rule_rmse)),
    "universal_y_rmse_rad": universal_y["rmse_rad"],
    "relative_rmse_reduction_vs_universal_y": float(
        1.0 - rule_rmse / universal_y["rmse_rad"]
    ),
    "median_abs_z_component_by_subtype": abs_z_by_subtype,
    "checks": {
        "c_d_y_rmse_below_2e-6": all(
            subtype_rows[subtype]["y<-z"]["rmse_rad"] < 2e-6
            for subtype in ("T4c", "T4d", "T5c", "T5d")
        ),
        "x_rule_better_than_y_for_all_a_b": all(
            subtype_rows[subtype]["x<-z"]["rmse_rad"]
            < subtype_rows[subtype]["y<-z"]["rmse_rad"]
            for subtype in ("T4a", "T4b", "T5a", "T5b")
        ),
        "subtype_rule_better_than_universal_y": rule_rmse < universal_y["rmse_rad"],
    },
    "interpretation": (
        "The x-for-a/b and y-for-c/d rule describes the observed angular pattern better "
        "than a universal y-axis convention. It is consistent with, but does not prove, "
        "selection of PC2 for a/b and PC1 for c/d. The public audit has no historical "
        "eigenvector arrays or generator code, and z-components make the a/b relation "
        "especially imperfect for T5."
    ),
}

if not all(rule["checks"].values()):
    raise RuntimeError(f"Subtype-axis hypothesis sanity check failed: {rule['checks']}")

out = {
    "status": "PROVEN_EVDIR_PC1_AXIS_CONVENTION_MATRIX",
    "source": {
        "url": URL,
        "sha256": sha,
        "rows": len(df),
        "columns": len(df.columns),
    },
    "candidates_ranked_global": ranked_candidates,
    "by_subtype": subtype_rows,
    "subtype_directional_axis_hypothesis": rule,
    "interpretation": (
        "Tests all six orthogonal target-axis/plane-normal conventions for the stored "
        "Subtype_evDir vector against historical PC1_angle after sign alignment to the "
        "target axis. The subtype rule is explicitly marked as a hypothesis, not as proof "
        "of the historical producer or eigenvector index."
    ),
}
Path("evdir_axis_convention_receipt.json").write_text(
    json.dumps(out, indent=2), encoding="utf-8"
)
print(json.dumps(out, indent=2))
