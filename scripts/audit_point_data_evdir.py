from __future__ import annotations

import hashlib
import json
import math
import urllib.request
from pathlib import Path

import pandas as pd

URL = (
    "https://raw.githubusercontent.com/"
    "borstlab/T4_T5_Dendrite_Morphology_Paper/"
    "cd17d34afd0d46a3c2947e83a1f0fdd835a9959a/"
    "Data/Point_data.pkl"
)
EXPECTED_SHA256 = "76b7d6a1c44ad6b2ca730feff88174c71327e095cce45d8a47a0d998f77df58f"
OUT = Path("evdir_uniqueness_receipt.json")
RAW = Path("/tmp/Point_data_historical.pkl")

with urllib.request.urlopen(URL, timeout=60) as r:
    data = r.read()
RAW.write_bytes(data)
sha = hashlib.sha256(data).hexdigest()
if sha != EXPECTED_SHA256:
    raise RuntimeError(f"SHA-256 mismatch: {sha}")

df = pd.read_pickle(RAW)

cols = ["Subtype_evDir_x", "Subtype_evDir_y", "Subtype_evDir_z"]
missing = [c for c in cols + ["PC1_angle", "PC1", "PC2", "PC3", "Type", "Subtype"] if c not in df.columns]
if missing:
    raise RuntimeError(f"Missing columns: {missing}")

def scalar(v):
    return float(v.item()) if hasattr(v, "item") else float(v)

def signed_angle_evdir_to_y(evdir):
    x, y, z = (float(v) for v in evdir)
    if y < 0.0:
        x, y, z = -x, -y, -z
    norm_v = math.hypot(x, y)
    if norm_v == 0.0:
        return math.nan
    x, y = x / norm_v, y / norm_v
    return math.atan2(x, y)

rows = []
all_deltas = []
for subtype, g in df.groupby("Subtype", sort=True):
    xyz = g[cols].map(scalar)
    unique = xyz.drop_duplicates()
    deltas = []
    angles = []
    observed = []
    for _, row in g.iterrows():
        v = [scalar(row[c]) for c in cols]
        a = signed_angle_evdir_to_y(v)
        p = scalar(row["PC1_angle"])
        angles.append(a)
        observed.append(p)
        if math.isfinite(a) and math.isfinite(p):
            d = (a - p + math.pi) % (2.0 * math.pi) - math.pi
            deltas.append(d)
            all_deltas.append(d)

    # Mean direction of evDir for this subtype (vector arithmetic, then unit normalize).
    vx = sum(scalar(v) for v in g[cols[0]]) / len(g)
    vy = sum(scalar(v) for v in g[cols[1]]) / len(g)
    vz = sum(scalar(v) for v in g[cols[2]]) / len(g)
    mn = math.sqrt(vx * vx + vy * vy + vz * vz)
    mean_unit = [vx / mn, vy / mn, vz / mn] if mn else [math.nan] * 3

    # Mean PC values and angle.
    mean_pc = [sum(scalar(v) for v in g[c]) / len(g) for c in ["PC1", "PC2", "PC3"]]
    mean_pc_angle = sum(observed) / len(observed)

    rows.append(
        {
            "subtype": str(subtype),
            "type": str(g["Type"].iloc[0]),
            "rows": int(len(g)),
            "unique_vectors": int(len(unique)),
            "constant_within_subtype": bool(len(unique) == 1),
            "first_vector": [float(x) for x in unique.iloc[0].tolist()],
            "mean_evdir": [float(x) for x in mean_unit],
            "mean_evdir_angle_to_y_rad": float(signed_angle_evdir_to_y(mean_unit)),
            "mean_pc": [float(x) for x in mean_pc],
            "mean_pc1_angle_rad": float(mean_pc_angle),
            "angle_abs_delta_max_rad": float(max(abs(x) for x in deltas)) if deltas else math.nan,
            "angle_abs_delta_median_rad": float(pd.Series([abs(x) for x in deltas]).median()) if deltas else math.nan,
            "within_1e4_rad": int(sum(abs(x) <= 1e-4 for x in deltas)),
            "within_1e6_rad": int(sum(abs(x) <= 1e-6 for x in deltas)),
        }
    )

finite = [d for d in all_deltas if math.isfinite(d)]
rmse = math.sqrt(sum(d * d for d in finite) / len(finite))
result = {
    "status": "PROVEN_HISTORICAL_EVDIR_STRUCTURE_PC1_COMPARISON_AND_SUBTYPE_SUMMARY",
    "source": {"url": URL, "sha256": sha, "rows": int(len(df)), "columns": int(len(df.columns))},
    "subtype_results": rows,
    "evdir_vs_pc1_angle": {
        "formula": "align evDir to +y by sign; signed planar angle from aligned evDir to +y around +z",
        "compared_rows": int(len(finite)),
        "rmse_rad": float(rmse),
        "max_abs_delta_rad": float(max(abs(d) for d in finite)),
        "max_abs_delta_deg": float(math.degrees(max(abs(d) for d in finite))),
        "within_1e-6_rad": int(sum(abs(d) <= 1e-6 for d in finite)),
        "within_1e-4_rad": int(sum(abs(d) <= 1e-4 for d in finite)),
        "fraction_within_1e-6": float(sum(abs(d) <= 1e-6 for d in finite) / len(finite)),
        "fraction_within_1e-4": float(sum(abs(d) <= 1e-4 for d in finite) / len(finite)),
    },
    "global": {
        "subtypes": int(len(rows)),
        "all_subtypes_constant": bool(all(x["constant_within_subtype"] for x in rows)),
        "total_unique_vectors": int(df[cols].map(scalar).drop_duplicates().shape[0]),
    },
}
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
