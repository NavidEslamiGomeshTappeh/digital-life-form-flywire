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

EXPECTED_BLOB = "b85caf49f45677f2075f7b5f2c8830141cd96d02"
EXPECTED_SHA256 = "76b7d6a1c44ad6b2ca730feff88174c71327e095cce45d8a47a0d998f77df58f"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def download_historical_blob(out: Path) -> None:
    payload = subprocess.check_output(
        [
            "gh", "api",
            "repos/borstlab/T4_T5_Dendrite_Morphology_Paper/git/blobs/" + EXPECTED_BLOB,
            "--jq", ".content",
        ],
        text=True,
    )
    import base64
    out.write_bytes(base64.b64decode("".join(payload.split())))

def anchor_rows(path: Path) -> dict:
    frame = pd.read_pickle(path)
    out = {}
    for subtype, root_id in ROOTS.items():
        rows = frame[frame["ID"].astype(str) == root_id]
        if len(rows) != 1:
            raise RuntimeError(f"{subtype}: expected one row, got {len(rows)}")
        row = rows.iloc[0]
        out[subtype] = row.to_dict()
    return out

def main() -> None:
    outdir = Path("v265_results")
    outdir.mkdir(parents=True, exist_ok=True)
    path = Path("/tmp/Point_data_git_historical.pkl")
    download_historical_blob(path)

    actual_blob = subprocess.check_output(
        ["git", "hash-object", "-t", "blob", str(path)], text=True
    ).strip()
    actual_sha = sha256(path)
    if actual_blob != EXPECTED_BLOB:
        raise RuntimeError(f"historical blob mismatch: {actual_blob}")
    if actual_sha != EXPECTED_SHA256:
        raise RuntimeError(f"historical sha256 mismatch: {actual_sha}")

    report = {
        "status": "PASS_HISTORICAL_GIT_POINT_DATA_RECOVERED",
        "source": {
            "repository": "borstlab/T4_T5_Dendrite_Morphology_Paper",
            "commit": "56901ad1853b44aeca15504cd908fa4c31009a3e",
            "blob": EXPECTED_BLOB,
            "sha256": actual_sha,
        },
        "anchors": anchor_rows(path),
    }

    (outdir / "V265_historical_Point_data_anchor_rows.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )

if __name__ == "__main__":
    main()
