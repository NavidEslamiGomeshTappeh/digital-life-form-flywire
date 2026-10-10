import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_historical_evdir_pc_axis_rule_remains_a_hypothesis():
    evidence = json.loads(
        (ROOT / "evidence" / "point_data_evdir_pc_axis_hypothesis.json").read_text(
            encoding="utf-8"
        )
    )

    assert evidence["status"] == "HYPOTHESIS_ONLY_SUBTYPE_DEPENDENT_PC_AXIS_SELECTION"
    assert evidence["source"]["rows"] == 5828
    assert evidence["source"]["sha256"] == (
        "76b7d6a1c44ad6b2ca730feff88174c71327e095cce45d8a47a0d998f77df58f"
    )

    rule = evidence["candidate_rule"]
    assert rule["classification"] == "HYPOTHESIS_ONLY"
    assert math.isclose(
        rule["weighted_global_rmse_rad"],
        0.42643560211880194,
        rel_tol=0.0,
        abs_tol=1e-12,
    )
    assert rule["weighted_global_rmse_rad"] < evidence["results"]["universal_y"]["rmse_rad"]

    groups = evidence["results"]["by_subtype"]
    for subtype in ("T4c", "T4d", "T5c", "T5d"):
        assert groups[subtype]["y_rmse_rad"] < 2e-6

    for subtype in ("T4a", "T4b", "T5a", "T5b"):
        assert groups[subtype]["x_rmse_rad"] < groups[subtype]["y_rmse_rad"]

    # The poorer T5 a/b planar fit is visible in the larger z-components and must not
    # be silently converted into an exact PC2 identity claim.
    assert groups["T5a"]["median_abs_z_component"] > 0.6
    assert groups["T5b"]["median_abs_z_component"] > 0.4
    assert any(
        "literally PC2" in item or "eigenvector index" in item
        for item in evidence["provenance_boundary"]["not_proven"]
    )

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    generator_claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-002")
    assert generator_claim["status"] == "UNRESOLVED"
