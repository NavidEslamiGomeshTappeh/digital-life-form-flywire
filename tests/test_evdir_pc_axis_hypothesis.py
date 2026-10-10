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


def test_current_neurosetta_pca_history_is_post_artifact_and_not_producer_proof():
    history = json.loads(
        (ROOT / "evidence" / "public_neurosetta_geometry_timeline.json").read_text(
            encoding="utf-8"
        )
    )
    events = {item["kind"]: item for item in history["events"]}
    initial = events["repository_initial_commit"]
    first_pca = events["first_pca_module_in_public_git_history"]
    refactor = events["pca_refactored_into_geometry_utils"]

    assert history["source"]["repository_created_at"] == "2026-01-20T22:42:16Z"
    assert initial["timestamp"] == "2025-10-21T09:23:42Z"
    assert initial["files_at_this_commit"] == [".gitignore", "LICENSE.md", "README.md"]
    assert first_pca["timestamp"] == "2026-07-27T15:05:30Z"
    assert "np.linalg.svd" in first_pca["implementation_summary"]["principal_components"]
    assert refactor["timestamp"] == "2026-07-28T22:03:34Z"
    assert refactor["implementation_summary"]["eigensolver"] == "numpy.linalg.eigh"
    assert history["conclusion"]["unresolved_claim_id"] == "C-POINTDATA-002"

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    producer_claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-002")
    timeline_claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-027")
    assert producer_claim["status"] == "UNRESOLVED"
    assert timeline_claim["status"] == "PROVEN"


def test_legacy_neurosetta_eigen_alignment_is_a_pre_artifact_capability_not_producer_proof():
    evidence = json.loads(
        (ROOT / "evidence" / "legacy_neurosetta_eig_alignment.json").read_text(
            encoding="utf-8"
        )
    )
    impl = evidence["implementation"]
    assert evidence["source"]["pinned_commit"] == "9c27f226128d98ea5420e7a3a32acf2adc8ce138"
    assert evidence["source"]["commit_timestamp"] == "2025-01-15T11:30:24Z"
    assert impl["coord_eig_decomp"]["eigensolver"] == "numpy.linalg.eig"
    assert any(
        "via eig_order" in item for item in impl["eig_align"]["capabilities"]
    )
    assert any("eigenvector index" in item for item in impl["eig_align"]["capabilities"])
    assert impl["jax_declared_directly_in_environment_yml"] is False
    assert "does not define the historical Subtype_evDir_x/y/z" in impl["eig_align"]["output_behavior"]

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    producer = next(c for c in claims["claims"] if c["id"] == "C-POINTDATA-002")
    legacy = next(c for c in claims["claims"] if c["id"] == "C-POINTDATA-028")
    assert producer["status"] == "UNRESOLVED"
    assert legacy["status"] == "PROVEN"
    assert "does not prove that this code produced Subtype_evDir" in legacy["statement"]


def test_jax_scalar_fingerprint_ranks_runtime_family_only_as_inference():
    matrix = json.loads(
        (ROOT / "evidence" / "point_data_revision_candidate_matrix.json").read_text(
            encoding="utf-8"
        )
    )
    comparison = matrix["runtime_type_fingerprint_assessment"]
    historical = comparison["historical_pickle"]
    assert historical["object_type"] == "jaxlib._jax.ArrayImpl"
    assert historical["scalar_cells"] == 46624
    assert len(historical["columns"]) == 8
    assert historical["rows"] * len(historical["columns"]) == historical["scalar_cells"]
    assert comparison["relative_compatibility"]["geojax"]["source_commit"] == (
        "33b0f8727ab447eff86e35a69c60c1f33b4d1513"
    )
    assert comparison["relative_compatibility"]["legacy_neurosetta"]["source_commit"] == (
        "9c27f226128d98ea5420e7a3a32acf2adc8ce138"
    )
    assert comparison["conclusion"]["status"] == "INFERENCE_ONLY"
    assert comparison["conclusion"]["unresolved_claim_id"] == "C-POINTDATA-002"

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    producer = next(c for c in claims["claims"] if c["id"] == "C-POINTDATA-002")
    family_claim = next(c for c in claims["claims"] if c["id"] == "C-POINTDATA-029")
    assert producer["status"] == "UNRESOLVED"
    assert family_claim["status"] == "INFERENCE_ONLY"


def test_same_week_geojax_consumer_is_not_misidentified_as_point_data_producer():
    bridge = json.loads(
        (ROOT / "evidence" / "contemporaneous_pointdata_geojax_consumer.json").read_text(
            encoding="utf-8"
        )
    )
    observed = bridge["random_bifurcations_nonproducer_check"]
    nonproducer = observed["non_producer_indicators"]
    figure5 = observed["figure5_binding"]
    assert figure5["loads_exact_historical_point_data_blob"] is True
    assert figure5["notebook_blob_sha1"] == "a65df260ce2b118d44e58388349b91a6c9483333"
    assert figure5["consumes_from_point_data"] == ["PC1", "PC2", "PC3"]
    assert nonproducer["mentions_subtype_evdir_literal"] is False
    assert nonproducer["calls_coord_eig_decomp"] is False
    assert nonproducer["calls_align_point_cloud"] is False
    assert nonproducer["writes_point_data_pickle"] is False

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    producer = next(c for c in claims["claims"] if c["id"] == "C-POINTDATA-002")
    consumer = next(c for c in claims["claims"] if c["id"] == "C-POINTDATA-030")
    assert producer["status"] == "UNRESOLVED"
    assert consumer["status"] == "PROVEN"
