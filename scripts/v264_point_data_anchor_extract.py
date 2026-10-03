from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd

ROOTS = {
    "T4a": "720575940632008007",
    "T4c": "720575940616224414",
    "T5a": "720575940625571465",
    "T5c": "720575940617782941",
}

HISTORICAL_COMMIT = "56901ad1853b44aeca15504cd908fa4c31009a3e"
HISTORICAL_BLOB = "b85caf49f45677f2075f7b5f2c8830141cd96d02"
EXPECTED_SHA256 = "76b7d6a1c44ad6b2ca730feff88174c71327e095cce45d8a47a0d998f77df58f"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    source = Path("/tmp/Point_data.pkl")
    if not source.is_file():
        raise FileNotFoundError(source)

    actual_sha256 = sha256(source)
    actual_blob = subprocess.check_output(
        ["git", "hash-object", "-t", "blob", str(source)], text=True
    ).strip()

    if actual_sha256 != EXPECTED_SHA256:
        raise RuntimeError(
            "Point_data historical SHA-256 mismatch: "
            f"expected {EXPECTED_SHA256}, got {actual_sha256}"
        )
    if actual_blob != HISTORICAL_BLOB:
        raise RuntimeError(
            "Point_data historical Git blob mismatch: "
            f"expected {HISTORICAL_BLOB}, got {actual_blob}"
        )

    frame = pd.read_pickle(source)
    if "ID" not in frame.columns:
        raise RuntimeError("Point_data.pkl has no ID column")

    # IDs are 64-bit FlyWire identifiers. Never serialize them through float.
    id_strings = frame["ID"].map(lambda value: str(value))
    anchors: dict[str, dict] = {}

    for subtype, root_id in ROOTS.items():
        rows = frame[id_strings == root_id]
        if len(rows) != 1:
            raise RuntimeError(f"{subtype}: expected exactly one row, got {len(rows)}")

        row = rows.iloc[0].to_dict()
        row["ID"] = root_id
        anchors[subtype] = row

    out = Path("v264_results")
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "PASS_POINT_DATA_ANCHORS_EXTRACTED_FROM_EXACT_HISTORICAL_BLOB",
        "source": {
            "repository": "borstlab/T4_T5_Dendrite_Morphology_Paper",
            "commit": HISTORICAL_COMMIT,
            "blob": HISTORICAL_BLOB,
            "sha256": actual_sha256,
            "exact_historical_bytes": True,
        },
        "anchors": anchors,
    }
    (out / "V264_Point_data_anchor_rows.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
