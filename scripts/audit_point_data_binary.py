from __future__ import annotations

import hashlib
import json
import pickle
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

HIST_URL = "https://raw.githubusercontent.com/borstlab/T4_T5_Dendrite_Morphology_Paper/56901ad1853b44aeca15504cd908fa4c31009a3e/Data/Point_data.pkl"
ZENODO_URL = "https://zenodo.org/records/21876510/files/T4_T5_dendrite_morphology_data.zip?download=1"
OUT = Path("point_data_binary_audit.json")

EXPECTED = {
    "T4a": {"root_id": 720575940632008007, "root": (-46.976, 32.06399609375, -111.552)},
    "T4c": {"root_id": 720575940616224414, "root": (-45.888, 21.61599609375, -116.352)},
    "T5a": {"root_id": 720575940625571465, "root": (13.207995117187501, 51.2, 119.616)},
    "T5c": {"root_id": 720575940617782941, "root": (12.1999951171875, 54.944, 117.952)},
}

def load_df(path: Path) -> pd.DataFrame:
    with path.open("rb") as fh:
        obj = pickle.load(fh)
    if not isinstance(obj, pd.DataFrame):
        raise TypeError(f"expected pandas.DataFrame, got {type(obj)!r}")
    return obj

def summarize_df(obj: pd.DataFrame) -> dict:
    return {
        "shape": list(obj.shape),
        "columns": [str(c) for c in obj.columns],
        "dtypes": {str(c): str(t) for c, t in obj.dtypes.items()},
    }

def rows_by_anchor(obj: pd.DataFrame) -> dict:
    out = {}
    for subtype, exp in EXPECTED.items():
        subset = obj[obj["Subtype"].astype(str).str.upper() == subtype.upper()].copy()
        target = pd.Series(exp["root"], index=["Root_x", "Root_y", "Root_z"], dtype="float64")
        distances = ((subset[["Root_x", "Root_y", "Root_z"]] - target) ** 2).sum(axis=1) ** 0.5
        idx = distances.idxmin()
        row = obj.loc[idx]
        rec = {
            "expected_root_id": exp["root_id"],
            "expected_root": list(exp["root"]),
            "candidate_count_for_subtype": len(subset),
            "selected_index_by_expected_root": int(idx),
            "distance_to_expected_root": float(distances.loc[idx]),
            "row": {
                str(k): (None if pd.isna(v) else v.item() if hasattr(v, "item") else v)
                for k, v in row.items()
            },
            "id_value": int(row["ID"]),
            "id_delta_from_expected_root_id": int(row["ID"]) - exp["root_id"],
        }
        out[subtype] = rec
    return out

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

hist = Path("/tmp/Point_data_historical.pkl")
urllib.request.urlretrieve(HIST_URL, hist)

zen_zip = Path("/tmp/zenodo_metrics.zip")
urllib.request.urlretrieve(ZENODO_URL, zen_zip)

with zipfile.ZipFile(zen_zip) as z:
    matches = [n for n in z.namelist() if n.lower().endswith("/point_data.pkl") or n.lower() == "point_data.pkl"]
    if not matches:
        matches = [n for n in z.namelist() if "point_data.pkl" in n.lower()]
    if not matches:
        raise FileNotFoundError("point_data.pkl not found in Zenodo archive")
    zpath = matches[0]
    with z.open(zpath) as src, Path("/tmp/Point_data_zenodo.pkl").open("wb") as dst:
        dst.write(src.read())

zen = Path("/tmp/Point_data_zenodo.pkl")

hist_df = load_df(hist)
zen_df = load_df(zen)

report = {
    "historical_git": {
        "bytes": hist.stat().st_size,
        "sha256": sha256(hist),
        "expected_sha256": "76b7d6a1c44ad6b2ca730feff88174c71327e095cce45d8a47a0d998f77df58f",
        "dataframe": summarize_df(hist_df),
        "anchors": rows_by_anchor(hist_df),
    },
    "zenodo_release": {
        "archive_path": zpath,
        "bytes": zen.stat().st_size,
        "sha256": sha256(zen),
        "expected_sha256_from_project_evidence": "46772ccabc609ab0f7136854024e7665727ff0f58f53c69126ea3e641ce7f891",
        "dataframe": summarize_df(zen_df),
        "anchors": rows_by_anchor(zen_df),
    },
    "id_and_coordinate_deltas": {},
}

for subtype in EXPECTED:
    h = report["historical_git"]["anchors"][subtype]
    z = report["zenodo_release"]["anchors"][subtype]
    hr, zr = h["row"], z["row"]
    common = sorted(set(hr) & set(zr))
    deltas = {}
    for key in common:
        hv, zv = hr[key], zr[key]
        if isinstance(hv, (int, float)) and isinstance(zv, (int, float)):
            deltas[key] = {"historical": hv, "zenodo": zv, "delta_zenodo_minus_historical": zv - hv}
        elif hv != zv:
            deltas[key] = {"historical": hv, "zenodo": zv}

    report.setdefault("id_and_coordinate_deltas", {})[subtype] = {
        "same_id": hr.get("ID") == zr.get("ID"),
        "historical_id": hr.get("ID"),
        "zenodo_id": zr.get("ID"),
        "same_subtype": hr.get("Subtype") == zr.get("Subtype"),
        "historical_root": [hr.get("Root_x"), hr.get("Root_y"), hr.get("Root_z")],
        "zenodo_root": [zr.get("Root_x"), zr.get("Root_y"), zr.get("Root_z")],
        "common_column_deltas": deltas,
        "common_columns": common,
    }

OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
print(json.dumps(report, indent=2, default=str))
