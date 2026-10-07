from __future__ import annotations

import hashlib
import json
import pickle
import pickletools
import re
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

import pandas as pd

HIST_URL = "https://raw.githubusercontent.com/borstlab/T4_T5_Dendrite_Morphology_Paper/cd17d34afd0d46a3c2947e83a1f0fdd835a9959a/Data/Point_data.pkl"
ZENODO_URL = "https://zenodo.org/records/21876510/files/T4_T5_dendrite_morphology_data.zip?download=1"
OUT = Path("point_data_binary_audit.json")

EXPECTED = {
    "T4a": {
        "root_id": 720575940632008007,
        "historical_root": (-46.85120703125, 32.261150390625, -111.5519921875),
        "zenodo_root": (-46.976, 32.06399609375, -111.552),
    },
    "T4c": {
        "root_id": 720575940616224414,
        "historical_root": (-46.16929296875, 22.233228515625, -116.4566640625),
        "zenodo_root": (-45.888, 21.61599609375, -116.352),
    },
    "T5a": {
        "root_id": 720575940625571465,
        "historical_root": (11.981576171875, 50.1895, 120.4021328125),
        "zenodo_root": (13.207995117187501, 51.2, 119.616),
    },
    "T5c": {
        "root_id": 720575940617782941,
        "historical_root": (12.7460712890625, 54.907804687500004, 117.5732734375),
        "zenodo_root": (12.1999951171875, 54.944, 117.952),
    },
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


def qualified_type(value: object) -> str:
    value_type = type(value)
    return f"{value_type.__module__}.{value_type.__qualname__}"


def summarize_object_cells(obj: pd.DataFrame) -> dict:
    type_counts: Counter[str] = Counter()
    per_column: dict[str, Counter[str]] = {}
    object_columns = [str(c) for c in obj.columns if str(obj[c].dtype) == "object"]
    for column in object_columns:
        column_counts: Counter[str] = Counter()
        for value in obj[column].tolist():
            if value is not None:
                value_type = qualified_type(value)
                type_counts[value_type] += 1
                column_counts[value_type] += 1
        per_column[column] = column_counts
    return {
        "object_columns": object_columns,
        "non_null_object_value_types": dict(type_counts.most_common()),
        "per_column_object_value_types": {
            column: dict(counts.most_common()) for column, counts in per_column.items()
        },
        "jax_related_types": {
            key: value for key, value in type_counts.items() if key.startswith(("jax.", "jaxlib."))
        },
    }


def static_pickle_globals(path: Path) -> dict:
    data = path.read_bytes()
    explicit_globals = []
    stack_global_count = 0
    protocol = None

    for opcode, arg, _pos in pickletools.genops(data):
        if protocol is None and opcode.name == "PROTO":
            protocol = int(arg)
        if opcode.name == "GLOBAL":
            explicit_globals.append(str(arg))
        elif opcode.name == "STACK_GLOBAL":
            stack_global_count += 1

    ascii_markers = {}
    for marker in (b"jax", b"jax.numpy", b"jaxlib", b"pandas", b"numpy"):
        ascii_markers[marker.decode()] = len(re.findall(re.escape(marker), data))

    return {
        "bytes": len(data),
        "protocol": protocol,
        "explicit_global_count": len(explicit_globals),
        "explicit_globals": explicit_globals,
        "stack_global_count": stack_global_count,
        "ascii_marker_counts": ascii_markers,
    }


def rows_by_anchor(obj: pd.DataFrame, snapshot: str) -> dict:
    out = {}
    root_column = {"historical": "historical_root", "zenodo": "zenodo_root"}[snapshot]
    for subtype, exp in EXPECTED.items():
        expected_id = exp["root_id"]
        id_matches = obj[obj["ID"].astype("int64") == expected_id]
        if len(id_matches) != 1:
            raise ValueError(
                f"{snapshot} snapshot expected exactly one row for {subtype} "
                f"ID={expected_id}, found {len(id_matches)}"
            )
        row = id_matches.iloc[0]
        target = pd.Series(exp[root_column], index=["Root_x", "Root_y", "Root_z"], dtype="float64")
        distance = float(
            ((row[["Root_x", "Root_y", "Root_z"]].astype("float64") - target) ** 2).sum() ** 0.5
        )
        out[subtype] = {
            "expected_root_id": expected_id,
            "selected_index_by_exact_id": int(id_matches.index[0]),
            "id_match_count": len(id_matches),
            "distance_to_expected_snapshot_root": distance,
            "row": {
                str(k): (None if pd.isna(v) else v.item() if hasattr(v, "item") else v)
                for k, v in row.items()
            },
        }
    return out


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


hist = Path("/tmp/Point_data_historical.pkl")
urllib.request.urlretrieve(HIST_URL, hist)

zen_zip = Path("/tmp/zenodo_metrics.zip")
urllib.request.urlretrieve(ZENODO_URL, zen_zip)

with zipfile.ZipFile(zen_zip) as z:
    matches = [
        n for n in z.namelist()
        if n.lower().endswith("/point_data.pkl") or n.lower() == "point_data.pkl"
    ]
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
    "audit_version": 2,
    "historical_git": {
        "repository": "borstlab/T4_T5_Dendrite_Morphology_Paper",
        "commit": "cd17d34afd0d46a3c2947e83a1f0fdd835a9959a",
        "git_blob": "b85caf49f45677f2075f7b5f2c8830141cd96d02",
        "bytes": hist.stat().st_size,
        "sha256": sha256(hist),
        "expected_sha256": "76b7d6a1c44ad6b2ca730feff88174c71327e095cce45d8a47a0d998f77df58f",
        "dataframe": summarize_df(hist_df),
        "pickle_static": static_pickle_globals(hist),
        "object_cells": summarize_object_cells(hist_df),
        "anchors": rows_by_anchor(hist_df, "historical"),
    },
    "zenodo_release": {
        "record": "10.5281/zenodo.21876510",
        "file": "Data/point_data.pkl",
        "archive_path": zpath,
        "bytes": zen.stat().st_size,
        "sha256": sha256(zen),
        "expected_sha256": "46772ccabc609ab0f7136854024e7665727ff0f58f53c69126ea3e641ce7f891",
        "dataframe": summarize_df(zen_df),
        "object_cells": summarize_object_cells(zen_df),
        "anchors": rows_by_anchor(zen_df, "zenodo"),
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
            deltas[key] = {
                "historical": hv,
                "zenodo": zv,
                "delta_zenodo_minus_historical": zv - hv,
            }
        elif hv != zv:
            deltas[key] = {"historical": hv, "zenodo": zv}

    report["id_and_coordinate_deltas"][subtype] = {
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
