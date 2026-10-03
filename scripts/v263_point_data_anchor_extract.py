from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOTS = {
    "T4a": "720575940632008007",
    "T4c": "720575940616224414",
    "T5a": "720575940625571465",
    "T5c": "720575940617782941",
}


def main() -> None:
    source = Path("/tmp/Point_data.pkl")
    frame = pd.read_pickle(source)

    result = {}
    for subtype, root_id in ROOTS.items():
        rows = frame[frame["ID"].astype(str) == root_id]
        if len(rows) != 1:
            raise RuntimeError(f"{subtype}: expected one Point_data row, got {len(rows)}")
        row = rows.iloc[0]
        result[subtype] = {
            k: (int(v) if isinstance(v, (int,)) else float(v) if isinstance(v, float) else str(v))
            for k, v in row.to_dict().items()
        }

    out = Path("v263_results")
    out.mkdir(parents=True, exist_ok=True)
    (out / "V263_Point_data_anchor_rows.json").write_text(
        json.dumps(
            {
                "source": {
                    "repository": "borstlab/T4_T5_Dendrite_Morphology_Paper",
                    "commit": "56901ad1853b44aeca15504cd908fa4c31009a3e",
                    "blob": "b85caf49f45677f2075f7b5f2c8830141cd96d02",
                },
                "anchors": result,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
