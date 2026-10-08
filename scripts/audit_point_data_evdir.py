from __future__ import annotations

import hashlib
import json
import pickle
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
missing = [c for c in cols if c not in df.columns]
if missing:
    raise RuntimeError(f"Missing columns: {missing}")

def scalar(v):
    if hasattr(v, "item"):
        return float(v.item())
    return float(v)

rows = []
for subtype, g in df.groupby("Subtype", sort=True):
    xyz = g[cols].map(scalar)
    unique = xyz.drop_duplicates()
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
        }
    )

result = {
    "status": "PROVEN_HISTORICAL_EVDIR_WITHIN_SUBTYPE_UNIQUENESS",
    "source": {
        "url": URL,
        "sha256": sha,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
    },
    "subtype_results": rows,
    "global": {
        "subtypes": int(len(rows)),
        "all_subtypes_constant": bool(all(x["constant_within_subtype"] for x in rows)),
        "total_unique_vectors": int(
            df[cols].map(scalar).drop_duplicates().shape[0]
        ),
    },
}

OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
