from __future__ import annotations
import hashlib, json
from pathlib import Path
import pandas as pd

ROOTS = {
    "T4a": "720575940632008007",
    "T4c": "720575940616224414",
    "T5a": "720575940625571465",
    "T5c": "720575940617782941",
}
EXPECTED_SHA256 = "76b7d6a1c44ad6b2ca730feff88174c71327e095cce45d8a47a0d998f77df58f"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> None:
    source = Path("/tmp/Point_data.pkl")
    actual = sha256(source)
    if actual != EXPECTED_SHA256:
        raise RuntimeError(f"Point_data SHA-256 mismatch: {actual}")
    frame = pd.read_pickle(source)
    anchors = {}
    for subtype, root_id in ROOTS.items():
        rows = frame[frame["ID"].astype(str) == root_id]
        if len(rows) != 1:
            raise RuntimeError(f"{subtype}: expected exactly one row, got {len(rows)}")
        anchors[subtype] = rows.iloc[0].to_dict()
    out = Path("v264_results")
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "PASS_POINT_DATA_ANCHORS_EXTRACTED",
        "source": {
            "repository": "borstlab/T4_T5_Dendrite_Morphology_Paper",
            "commit": "56901ad1853b44aeca15504cd908fa4c31009a3e",
            "blob": "b85caf49f45677f2075f7b5f2c8830141cd96d02",
            "sha256": actual,
        },
        "anchors": anchors,
    }
    (out / "V264_Point_data_anchor_rows.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )

if __name__ == "__main__":
    main()
