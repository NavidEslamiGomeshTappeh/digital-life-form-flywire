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


def test_pre_artifact_geojax_ordering_capability_is_not_misreported_as_producer_proof():
    geojax = json.loads(
        (ROOT / "evidence" / "public_geojax_preartifact_jax_pca.json").read_text(
            encoding="utf-8"
        )
    )
    snapshot = geojax["pre_artifact_axis_ordering_snapshot"]
    assert snapshot["source"]["commit"] == "33b0f8727ab447eff86e35a69c60c1f33b4d1513"
    align = snapshot["functions"]["align_point_cloud"]
    assert "Required caller-supplied eigenvector index order" in align["parameters"]["order"]
    assert "sign(sum(E * target_basis, axis=1))" in align["sign_rule"]
    assert "does not directly emit" in align["output_limit"]
    assert any("producer called" in item for item in snapshot["provenance_boundary"]["not_proven"])

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    producer_claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-002")
    capability_claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-025")
    assert producer_claim["status"] == "UNRESOLVED"
    assert capability_claim["status"] == "PROVEN"
    assert "not that this code generated Subtype_evDir" in capability_claim["statement"]


def test_historical_point_data_public_history_keeps_producer_boundary_unresolved():
    history = json.loads(
        (ROOT / "evidence" / "point_data_historical_path_history.json").read_text(
            encoding="utf-8"
        )
    )
    events = {item["kind"]: item for item in history["events"]}
    consumer = events["consumer_notebook_added_before_artifact"]
    artifact = events["historical_binary_added"]
    duplicate = events["duplicate_add_commit_same_binary"]
    later = events["public_generator_notebooks_added_after_artifact_and_binary_removed"]

    assert consumer["timestamp"] == "2025-12-09T19:40:07Z"
    assert consumer["absolute_local_path_in_notebook"].endswith(
        "T45_Morpho_data/Data/Pickled_data/Point_data.pkl"
    )
    assert consumer["timing_seconds_before_first_binary_commit"] == 103
    assert artifact["timestamp"] == "2025-12-09T19:41:50Z"
    assert artifact["changed_paths"] == ["Data/Point_data.pkl"]
    assert artifact["blob_sha1"] == "b85caf49f45677f2075f7b5f2c8830141cd96d02"
    assert duplicate["blob_sha1"] == artifact["blob_sha1"]
    assert later["point_data_status"] == "removed"
    assert not later["later_metrics_notebook_observation"]["contains_literal_Subtype_evDir"]
    assert history["conclusions"]["unresolved_claim_id"] == "C-POINTDATA-002"

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    producer_claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-002")
    timeline_claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-026")
    assert producer_claim["status"] == "UNRESOLVED"
    assert timeline_claim["status"] == "PROVEN"
