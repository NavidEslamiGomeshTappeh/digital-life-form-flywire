from __future__ import annotations

import hashlib
import json
import pickle
import urllib.request
from pathlib import Path

import pandas as pd

URL = "https://raw.githubusercontent.com/borstlab/T4_T5_Dendrite_Morphology_Paper/56901ad1853b44aeca15504cd908fa4c31009a3e/Data/Point_data.pkl"
OUT = Path("point_data_binary_audit.json")

EXPECTED = {
    "T4a": {
        "root_id": 720575940632008007,
        "root": (-46.976, 32.06399609375, -111.552),
    },
    "T4c": {
        "root_id": 720575940616224414,
        "root": (-45.888, 21.61599609375, -116.352),
    },
    "T5a": {
        "root_id": 720575940625571465,
        "root": (13.207995117187501, 51.2, 119.616),
    },
    "T5c": {
        "root_id": 720575940617782941,
        "root": (12.1999951171875, 54.944, 117.952),
    },
}

path = Path("/tmp/Point_data.pkl")
urllib.request.urlretrieve(URL, path)

raw = path.read_bytes()
sha = hashlib.sha256(raw).hexdigest()


# Print the pickle's referenced GLOBAL-like opcodes without importing its modules.
def pickle_globals(raw: bytes):
    import io
    import pickletools
    found = []
    for opcode, arg, _pos in pickletools.genops(io.BytesIO(raw)):
        if opcode.name in {"GLOBAL", "STACK_GLOBAL"} and arg is not None:
            found.append({"opcode": opcode.name, "arg": str(arg)})
    return found[:500]

report["pickle_protocol_globals"] = pickle_globals(raw)
\nwith path.open("rb") as fh:
    obj = pickle.load(fh)

if not isinstance(obj, pd.DataFrame):
    raise TypeError(f"expected pandas.DataFrame, got {type(obj)!r}")

report = {
    "file": {
        "bytes": len(raw),
        "sha256": sha,
        "expected_historical_sha256": "76b7d6a1c44ad6b2ca730feff88174c71327e095cce45d8a47a0d998f77df58f",
    },
    "dataframe": {
        "shape": list(obj.shape),
        "columns": [str(c) for c in obj.columns],
        "dtypes": {str(c): str(t) for c, t in obj.dtypes.items()},
    },
    "anchors": {},
}

for subtype, exp in EXPECTED.items():
    if "Subtype" in obj.columns:
        subset = obj[obj["Subtype"].astype(str).str.upper() == subtype.upper()].copy()
    else:
        subset = obj.iloc[0:0].copy()

    if {"Root_x", "Root_y", "Root_z"}.issubset(obj.columns):
        root_cols = ["Root_x", "Root_y", "Root_z"]
        target = pd.Series(exp["root"], index=root_cols, dtype="float64")
        distances = ((subset[root_cols] - target) ** 2).sum(axis=1) ** 0.5
        if len(distances):
            idx = distances.idxmin()
            row = obj.loc[idx]
            root_distance = float(distances.loc[idx])
        else:
            idx = None
            row = None
            root_distance = None
    else:
        idx = None
        row = None
        root_distance = None

    record = {
        "expected_root_id": exp["root_id"],
        "expected_root": list(exp["root"]),
        "candidate_count_for_subtype": int(len(subset)),
        "selected_index_by_root_coordinate": None if idx is None else int(idx),
        "root_coordinate_distance": root_distance,
        "row": None if row is None else {
            str(k): (None if pd.isna(v) else v.item() if hasattr(v, "item") else v)
            for k, v in row.items()
        },
    }
    if row is not None and "ID" in row:
        record["id_value"] = int(row["ID"])
        record["id_delta_from_expected_root_id"] = int(row["ID"]) - exp["root_id"]
    report["anchors"][subtype] = record

OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
print(json.dumps(report, indent=2, default=str))
