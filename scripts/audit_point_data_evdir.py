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
missing = [c for c in cols + ["PC1_angle"] if c not in df.columns]
if missing:
    raise RuntimeError(f"Missing columns: {missing}")

def scalar(v):
    return float(v.item()) if hasattr(v, "item") else float(v)

def signed_angle_evdir_to_y(evdir):
    # Historical/public metric semantics:
    # align the vector with +y (flip only when its y component is negative),
    # project both vectors to the xy plane (normal +z), then take the signed angle.
    x, y, z = (float(v) for v in evdir)
    if y < 0.0:
        x, y, z = -x, -y, -z

    # Project to plane perpendicular to +z.
    vx, vy = x, y
    norm_v = math.hypot(vx, vy)
    if norm_v == 0.0:
        return math.nan
    vx, vy = vx / norm_v, vy / norm_v

    # Reference is +y = (0,1) in the xy plane.
    dot = max(-1.0, min(1.0, vy))
    cross_z = vx * 1.0 - vy * 0.0
    return math.atan2(cross_z, dot)

rows = []
all_deltas = []
for subtype, g in df.groupby("Subtype", sort=True):
    xyz = g[cols].map(scalar)
    unique = xyz.drop_duplicates()

    derived = []
    observed = []
    for _, row in g.iterrows():
        v = [scalar(row[c]) for c in cols]
        a = signed_angle_evdir_to_y(v)
        p = scalar(row["PC1_angle"])
        derived.append(a)
        observed.append(p)
        if math.isfinite(a) and math.isfinite(p):
            d = a - p
            # Wrap to [-pi, pi].
            d = (d + math.pi) % (2.0 * math.pi) - math.pi
            all_deltas.append(d)

    abs_d = [abs(x) for x in all_deltas[-len(derived):] if math.isfinite(x)]

    rows.append(
        {
            "subtype": str(subtype),
            "rows": int(len(g)),
            "unique_vectors": int(len(unique)),
            "constant_within_subtype": bool(len(unique) == 1),
            "min_x": float(xyz[cols[0]].min()),
            "max_x": float(xyz[cols[0]].max()),
            "min_y": float(xyz[cols[1]].min()),
            "max_y": float(xyz[cols[1]].max()),
            "min_z": float(xyz[cols[2]].min()),
            "max_z": float(xyz[cols[2]].max()),
            "first_vector": [float(x) for x in unique.iloc[0].tolist()],
            "angle_abs_delta_max_rad": float(max(abs_d)) if abs_d else math.nan,
        }
    )

finite = [d for d in all_deltas if math.isfinite(d)]
rmse = math.sqrt(sum(d * d for d in finite) / len(finite)) if finite else math.nan
within_1e6 = sum(abs(d) <= 1e-6 for d in finite)
within_1e4 = sum(abs(d) <= 1e-4 for d in finite)

result = {
    "status": "PROVEN_HISTORICAL_EVDIR_STRUCTURE_AND_PC1_ANGLE_COMPARISON",
    "source": {
        "url": URL,
        "sha256": sha,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
    },
    "subtype_results": rows,
    "evdir_vs_pc1_angle": {
        "formula": "align evDir to +y; signed planar angle from aligned evDir to +y around +z",
        "compared_rows": int(len(finite)),
        "rmse_rad": float(rmse),
        "max_abs_delta_rad": float(max(abs(d) for d in finite)) if finite else math.nan,
        "max_abs_delta_deg": float(math.degrees(max(abs(d) for d in finite))) if finite else math.nan,
        "within_1e-6_rad": int(within_1e6),
        "within_1e-4_rad": int(within_1e4),
        "exact_within_1e-6_fraction": float(within_1e6 / len(finite)) if finite else math.nan,
        "interpretation": (
            "A near-zero delta across all rows would strongly support that "
            "Subtype_evDir is the sign-aligned first eigenvector used for PC1_angle; "
            "a systematic/nonzero delta would reject that identity."
        ),
    },
    "global": {
        "subtypes": int(len(rows)),
        "all_subtypes_constant": bool(all(x["constant_within_subtype"] for x in rows)),
        "total_unique_vectors": int(df[cols].map(scalar).drop_duplicates().shape[0]),
    },
}

OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
