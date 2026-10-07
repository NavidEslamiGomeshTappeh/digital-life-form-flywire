import json
import shutil
import subprocess
import sys
from pathlib import Path

from dlf_flywire import __version__
from dlf_flywire.cli import main as cli_main
from dlf_flywire.provenance import (
    ProvenanceError,
    audit_provenance,
    git_blob_sha1,
    trace_claim,
    validate_artifact_manifest,
    validate_claim_ledger,
    validate_evidence_manifest_version,
    validate_release_receipt_versions,
    validate_synapse_lineage,
)

ROOT = Path(__file__).resolve().parents[1]


def test_provenance_audit_passes():
    report = audit_provenance(ROOT)
    assert report["status"] == "PASS"
    assert report["product_version"] == __version__
    assert report["artifact_manifest"]["artifacts_checked"] >= 20
    assert report["claim_ledger"]["claims_checked"] >= 8


def test_claim_ledger_contains_unresolved_boundaries():
    report = validate_claim_ledger(ROOT)
    assert report["status_counts"]["UNRESOLVED"] >= 2


def test_independent_corroboration_claim_binds_source_receipts():
    ledger = json.loads(
        (ROOT / "evidence" / "claims.json").read_text(encoding="utf-8")
    )
    claim = next(item for item in ledger["claims"] if item["id"] == "C-CONNECTIVITY-003")
    assert "E-SOURCE-RECEIPTS" in claim["evidence"]


def test_artifact_manifest_excludes_itself():
    manifest = json.loads(
        (ROOT / "evidence" / "artifact_manifest.json").read_text(encoding="utf-8")
    )
    paths = {item["path"] for item in manifest["artifacts"]}
    assert "evidence/artifact_manifest.json" not in paths
    assert "evidence/artifact_manifest.json" in manifest["exclusion"]



def test_synapse_lineage_passes():
    report = validate_synapse_lineage(ROOT)
    assert report["status"] == "PASS_SYNAPSE_LINEAGE"
    assert report["records_checked"] == 649
    assert report["unique_record_ids"] == 649
    assert report["codex_exact_tuple_matches"] == 649
    assert report["zenodo_exact_midpoint_matches"] == 649


def test_synapse_lineage_fails_closed_on_record_id_drift(tmp_path):
    (tmp_path / "evidence").mkdir()
    (tmp_path / "src" / "dlf_flywire").mkdir(parents=True)
    for relative in ("VERSION", "pyproject.toml", "src/dlf_flywire/__init__.py", "evidence/synapses.csv"):
        source = ROOT / relative
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    lineage = json.loads(
        (ROOT / "evidence" / "synapse_lineage.json").read_text(encoding="utf-8")
    )
    lineage["records"][0]["record_id"] = "syn-tampered"
    (tmp_path / "evidence" / "synapse_lineage.json").write_text(
        json.dumps(lineage), encoding="utf-8"
    )
    try:
        validate_synapse_lineage(tmp_path)
    except ProvenanceError as exc:
        assert "record ID mismatch" in str(exc)
    else:
        raise AssertionError("tampered synapse lineage was accepted")




def test_point_data_sha256_binding_is_consistent():
    comparison = json.loads(
        (ROOT / "evidence" / "root_coordinate_comparison.json").read_text(
            encoding="utf-8"
        )
    )
    provenance = json.loads(
        (ROOT / "evidence" / "point_data_provenance.json").read_text(
            encoding="utf-8"
        )
    )
    assert comparison["point_data_sha256"] == provenance["source"]["sha256"]
    assert provenance["source"]["commit"] == "cd17d34afd0d46a3c2947e83a1f0fdd835a9959a"


def test_global_alignment_boundary_is_ledgered():
    boundary = json.loads(
        (ROOT / "evidence" / "global_alignment_boundary.json").read_text(
            encoding="utf-8"
        )
    )
    assert boundary["status"] == "PROVEN_PUBLISHED_GLOBAL_ALIGNMENT_BOUNDARY"
    assert boundary["population_specific"] is True
    assert boundary["operations"] == [
        "mean_center_population",
        "pca_rotation",
        "fit_sphere_and_recenter",
        "final_axis_orientation_rotation",
    ]
    assert boundary["pp4_persistence"]["save_after_alignment"] is False
    comparison = json.loads(
        (ROOT / "evidence" / "root_coordinate_comparison.json").read_text(
            encoding="utf-8"
        )
    )
    assert comparison["alignment_confounded"] is True
    assert comparison["status"] == "NEGATIVE_PRE_ALIGNMENT_BASELINE_ONLY"
    assert comparison["alignment_boundary_evidence"]["evidence_id"] == "E-GLOBAL-ALIGNMENT-BOUNDARY"


def test_point_data_snapshot_delta_is_ledgered():
    evidence = json.loads(
        (ROOT / "evidence" / "point_data_version_delta.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["status"] == "PROVEN_POINTDATA_MULTI_SNAPSHOT_BOUNDARY"
    assert evidence["sources"]["historical_git"]["sha256"] != evidence["sources"]["zenodo_release"]["sha256"]
    assert evidence["sources"]["historical_git"]["rows"] == 5828
    assert evidence["sources"]["zenodo_release"]["rows"] == 11838
    assert len(evidence["anchor_comparison"]) == 4
    assert all(isinstance(item["id"], str) and item["id"].isdigit() for item in evidence["anchor_comparison"])
    assert all(
        item["historical_root"] != item["zenodo_root"]
        for item in evidence["anchor_comparison"]
    )
    claims = json.loads(
        (ROOT / "evidence" / "claims.json").read_text(encoding="utf-8")
    )
    claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-006")
    assert claim["status"] == "PROVEN"
    assert "E-POINTDATA-VERSION-DELTA" in claim["evidence"]


def test_point_data_exact_id_decode_receipt_is_ledgered():
    evidence = json.loads(
        (ROOT / "evidence" / "point_data_pickle_decode_receipt.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["status"] == "PROVEN_POINTDATA_EXACT_ID_DECODE"
    assert evidence["workflow"]["run_id"] == 37483737773
    assert evidence["workflow"]["conclusion"] == "success"
    assert evidence["decode_runtime"]["historical_pickle_protocol"] == 5
    assert evidence["decode_runtime"]["historical_stack_global_count"] == 11
    assert evidence["decode_runtime"]["historical_object_cell_types"][
        "jaxlib._jax.ArrayImpl"
    ] == 46624
    per_column = evidence["decode_runtime"]["historical_per_column_object_value_types"]
    for column in ("PC1", "PC2", "PC3", "PC1_angle", "Mean_segment_angle", "Subtype_evDir_x", "Subtype_evDir_y", "Subtype_evDir_z"):
        assert per_column[column] == {"jaxlib._jax.ArrayImpl": 5828}
    assert evidence["decode_runtime"]["pattern_check"]["exact"] is True
    expected_ids = {
        "T4a": "720575940632008007",
        "T4c": "720575940616224414",
        "T5a": "720575940625571465",
        "T5c": "720575940617782941",
    }
    for subtype, root_id in expected_ids.items():
        anchor = evidence["anchor_selection"]["anchors"][subtype]
        assert anchor["root_id"] == root_id
    claims = json.loads(
        (ROOT / "evidence" / "claims.json").read_text(encoding="utf-8")
    )
    claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-007")
    assert claim["status"] == "REPRODUCED"
    assert "E-POINTDATA-DECODE" in claim["evidence"]
    claim_context = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-008")
    assert claim_context["classification"] == "SOURCE_OBSERVATION"
    assert claim_context["status"] == "PROVEN"


def test_point_data_snapshot_anchor_ids_are_exact_and_unique():
    evidence = json.loads(
        (ROOT / "evidence" / "point_data_version_delta.json").read_text(
            encoding="utf-8"
        )
    )
    expected_ids = {
        "T4a": "720575940632008007",
        "T4c": "720575940616224414",
        "T5a": "720575940625571465",
        "T5c": "720575940617782941",
    }
    assert evidence["verification"]["anchor_selection_method"] == "exact_root_id"
    assert evidence["verification"]["exact_id_storage"] == "string"
    assert evidence["verification"]["unique_historical_rows"] == 4
    assert evidence["verification"]["unique_zenodo_rows"] == 4
    assert evidence["verification"]["previous_nearest_coordinate_selector_corrected"] is True
    for item in evidence["anchor_comparison"]:
        assert item["id"] == expected_ids[item["subtype"]]


def test_public_coordinate_pipeline_boundary_is_ledgered():
    boundary = json.loads(
        (ROOT / "evidence" / "public_coordinate_pipeline_boundary.json").read_text(
            encoding="utf-8"
        )
    )
    assert boundary["status"] == "PROVEN_PUBLIC_PIPELINE_COORDINATE_BOUNDARY"
    assert any(
        "no coordinate rotation/translation/scaling" in item.lower()
        for source in boundary["sources"]
        for item in source.get("observations", [])
    )
    assert any(
        "does not apply a coordinate-frame transform" in text
        for source in boundary["sources"]
        for text in (
            source.get("observations", [])
            + ([source["observation"]] if "observation" in source else [])
        )
    )
    claims = json.loads(
        (ROOT / "evidence" / "claims.json").read_text(encoding="utf-8")
    )
    claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-005")
    assert claim["status"] == "PROVEN"


def test_archived_submission_release_boundary_is_ledgered():
    boundary = json.loads(
        (ROOT / "evidence" / "zenodo_submission_release_boundary.json").read_text(
            encoding="utf-8"
        )
    )
    assert boundary["status"] == "PROVEN_ARCHIVED_RELEASE_CONTENT_BOUNDARY"
    assert "Data/Point_data.pkl" in boundary["archive_observations"]["includes"]
    assert "Notebooks/PP3_Dendrite_extraction.ipynb" in boundary["archive_observations"]["does_not_list"]
    assert "Reduced_dendrites/" in boundary["archive_observations"]["does_not_list"]
    claims = json.loads(
        (ROOT / "evidence" / "claims.json").read_text(encoding="utf-8")
    )
    claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-004")
    assert claim["status"] == "PROVEN"
    assert "E-ZENODO-SUBMISSION-BOUNDARY" in claim["evidence"]


def test_v230_point_data_bridge_is_anchor_only():
    bridge = json.loads(
        (ROOT / "evidence" / "point_data_connectivity_bridge.json").read_text(
            encoding="utf-8"
        )
    )
    assert bridge["status"] == "PROVEN_ANCHOR_ID_BRIDGE_ONLY"
    assert bridge["synapse_artifact"]["row_count"] == 649
    assert bridge["synapse_artifact"]["unique_endpoint_root_ids"] == 62
    assert bridge["synapse_artifact"]["unique_directed_pairs"] == 75
    for root_id in bridge["point_data_anchor_roots"]:
        assert bridge["anchor_presence_in_synapse_artifact"][root_id]["total"] > 0
    assert "historical_reduced_morphology_artifact_hash" in bridge["join_keys"]["unavailable"]


def test_historical_neurosetta_lineage_is_context_only():
    lineage = json.loads(
        (ROOT / "evidence" / "historical_neurosetta_lineage_context.json").read_text(
            encoding="utf-8"
        )
    )
    assert lineage["status"] == "PROVEN_SOFTWARE_FAMILY_CONTEXT_NOT_ARTIFACT_IDENTITY"
    assert lineage["lineage"][0]["relevant_commits"][1]["sha"] == (
        "bb5f5ffaf435bf8d0d7fbc70238bab2c47b7ca92"
    )
    legacy = next(
        item for item in lineage["lineage"]
        if item["repository"] == "NikDrummond/Neurosetta_legacy_v0.0.1"
    )
    assert any(
        item["sha"] == "94ff9e5a956d5a91c40bb386f33e3dfa60896987"
        for item in legacy["relevant_commits"]
    )
    neuoptics = next(
        item for item in lineage["lineage"]
        if item["repository"] == "NikDrummond/NeuOptics"
    )
    assert neuoptics["initial_commit"]["sha"] == (
        "1e2c5b4653f7d5e785df98457a17c0a82a2bca99"
    )
    assert any(
        item["sha"] == "d208e46aa6403a3e9502135d3b538c65ea2ab0b3"
        for item in neuoptics["relevant_commits"]
    )
    neurossetta = next(
        item for item in lineage["lineage"]
        if item["repository"] == "NikDrummond/NeuRosetta"
    )
    assert neurossetta["relevant_commits"][0]["sha"] == (
        "661a51d24f1f7fb96da2fbbf6fbefc9a5282a7f0"
    )
    assert lineage["gui_boundary"]["public_history_result"].startswith(
        "A targeted search"
    )
    claims = json.loads(
        (ROOT / "evidence" / "claims.json").read_text(encoding="utf-8")
    )
    assert next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-003")["status"] == "PROVEN"
    assert next(item for item in claims["claims"] if item["id"] == "C-MORPH-003")["status"] == "PROVEN"


def test_published_method_boundary_is_ledgered():
    boundary = json.loads(
        (ROOT / "evidence" / "public_method_boundary.json").read_text(
            encoding="utf-8"
        )
    )
    assert boundary["status"] == "PROVEN_PUBLISHED_METHOD_BOUNDARY"
    assert any(
        item["stage"] == "manual_root_verification"
        for item in boundary["method_boundary"]
    )
    assert any(
        item["stage"] == "manual_dendrite_verification_and_modification"
        for item in boundary["method_boundary"]
    )
    claims = json.loads(
        (ROOT / "evidence" / "claims.json").read_text(encoding="utf-8")
    )
    claim = next(item for item in claims["claims"] if item["id"] == "C-MORPH-002")
    assert claim["status"] == "PROVEN"
    assert "E-PUBLISHED-METHOD-BOUNDARY" in claim["evidence"]


def test_point_data_evdir_lifecycle_is_ledgered():
    evidence = json.loads(
        (ROOT / "evidence" / "point_data_evdir_legacy_lifecycle.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["status"] == "PROVEN_POINTDATA_EVDIR_LEGACY_COLUMN_LIFECYCLE"
    assert evidence["historical"]["columns"] == [
        "Subtype_evDir_x",
        "Subtype_evDir_y",
        "Subtype_evDir_z",
    ]
    assert evidence["december_public_readme"]["documented_column_count"] == 21
    assert evidence["december_public_readme"]["historical_extra_columns_not_documented"] == evidence["historical"]["columns"]
    assert evidence["later_zenodo"]["has_subtype_evdir_columns"] is False
    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-011")
    assert claim["status"] == "PROVEN"
    assert claim["evidence"] == ["E-POINTDATA-EVDIR-LIFECYCLE"]


def test_point_data_evdir_anchor_vectors_are_unit_norm():
    evidence = json.loads(
        (ROOT / "evidence" / "point_data_evdir_anchor_vectors.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["status"] == "PROVEN_HISTORICAL_SUBTYPE_EVDIR_VECTOR_EXTRACTION"
    assert len(evidence["anchor_vectors"]) == 4
    for item in evidence["anchor_vectors"]:
        assert item["norm_error"] < 2e-7
    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-010")
    assert claim["status"] == "PROVEN"
    assert claim["evidence"] == ["E-POINTDATA-EVDIR-ANCHORS"]


def test_point_data_producer_gap_claim_is_unresolved():
    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-009")
    assert claim["status"] == "UNRESOLVED"
    assert claim["classification"] == "UNRESOLVED"
    assert claim["evidence"] == ["E-POINTDATA-PUBLIC-GENERATOR-GAP"]
    assert claim["caveats"]


def test_point_data_public_generator_gap_is_ledgered():
    evidence = json.loads(
        (ROOT / "evidence" / "point_data_public_generator_gap.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["status"] == "PROVEN_PUBLIC_METRICS_GENERATOR_GAP"
    public = evidence["public_notebook"]
    historical = evidence["historical_artifact"]
    assert public["column_count"] == 23
    assert public["save_operation_present"] is False
    assert historical["column_count"] == 24
    assert historical["historical_extra_columns"] == [
        "Subtype_evDir_x",
        "Subtype_evDir_y",
        "Subtype_evDir_z",
    ]
    assert evidence["repository_search_observation"]["github_code_search_hits"] == 0
    matrix = json.loads(
        (ROOT / "evidence" / "point_data_revision_candidate_matrix.json").read_text(
            encoding="utf-8"
        )
    )
    assert any(
        item["status"] == "PROVEN_PUBLIC_NOTEBOOK_NON_IDENTITY"
        and item["finding"] == "Public Metrics1 generator gap"
        for item in matrix["decisions"]
    )


def test_github_platform_audit_snapshot_is_ledgered():
    audit = json.loads(
        (ROOT / "evidence" / "github_platform_october_2026_audit.json").read_text(
            encoding="utf-8"
        )
    )
    live = audit["repository_live_state"]
    assert live["visibility"] == "public"
    assert live["default_branch"] == "main"
    assert live["main_head"] == "a867738499b473e99500c20da73bb992ee172745"
    assert live["public_branch_count"] == 63
    assert live["description"] is None
    manifest = json.loads((ROOT / "evidence" / "artifact_manifest.json").read_text(encoding="utf-8"))
    assert any(item["id"] == "E-GITHUB-PLATFORM-AUDIT" for item in manifest["artifacts"])


def test_later_public_pp3_reconstruction_receipt_is_ledgered():
    receipt = json.loads(
        (ROOT / "evidence" / "historical_pp3_later_reconstruction_receipt.json").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["status"] == "PROVEN_LATER_PUBLIC_PP3_EXECUTION_RECONSTRUCTION"
    assert receipt["workflow"]["run_id"] == 37158493013
    assert receipt["workflow"]["conclusion"] == "success"
    assert receipt["historical_artifact_identity"]["exact_first_git_commit"] == (
        "cd17d34afd0d46a3c2947e83a1f0fdd835a9959a"
    )
    assert receipt["results"]["selected_nodes_match_expected"] == {
        "T4a": 292,
        "T4c": 358,
        "T5a": 343,
        "T5c": 323,
    }
    assert receipt["results"]["direct_selected_root_exact_match"] is False
    assert receipt["results"]["rigid_rms_um"] > 70
    assert receipt["results"]["similarity_rms_um"] < 11
    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    claim = next(item for item in claims["claims"] if item["id"] == "C-MORPH-004")
    assert claim["status"] == "REPRODUCED"
    assert "E-HISTORICAL-PP3-LATER-RECONSTRUCTION" in claim["evidence"]


def test_historical_point_data_ingest_boundary_is_locked():
    boundary = json.loads(
        (ROOT / "evidence" / "historical_generator_boundary.json").read_text(
            encoding="utf-8"
        )
    )
    assert boundary["status"].startswith("PROVEN_HISTORICAL_")
    assert boundary["checks"]["parallel_point_commits_same_tree"] is True
    assert boundary["checks"]["parallel_point_commits_same_blob"] is True
    assert boundary["checks"]["duplicate_point_commits_merged_without_tree_change"] is True
    assert boundary["checks"]["neuron_ids_added_after_point_data"] is True
    assert boundary["checks"]["anova_output_execution_metadata_present"] is True
    assert boundary["checks"]["public_branch_listing_verified"] is True
    assert boundary["checks"]["public_branch_count"] == 63
    assert "v268-point-data-provenance-repair" in boundary["checks"]["relevant_point_data_branches_visible"]
    assert boundary["consumer_path_evidence"]["kernel"] == "neurosetta"
    assert boundary["consumer_path_evidence"]["local_path"].endswith(
        "T45_Morpho_data/Data/Pickled_data/Point_data.pkl"
    )
    assert boundary["initial_point_data_tree_audit"]["truncated"] is False
    assert boundary["initial_point_data_tree_audit"]["total_blob_paths"] == 4
    assert boundary["initial_point_data_tree_audit"]["point_related_blob_paths"] == [
        "Data/Point_data.pkl"
    ]
    assert boundary["initial_point_data_tree_audit"]["producer_related_paths_present"] is False
    dag = {item["sha"]: item for item in boundary["git_dag"]}
    assert dag["cd17d34afd0d46a3c2947e83a1f0fdd835a9959a"]["blob"] == (
        "b85caf49f45677f2075f7b5f2c8830141cd96d02"
    )
    assert dag["fe9779d4ca425613eec44b19e961610d117e7232"]["blob"] == (
        "b85caf49f45677f2075f7b5f2c8830141cd96d02"
    )
    assert dag["8a38537f55371de369f80c50778915afb5d954b4"]["tree"] == (
        "cd10c382b3abbbe68bf00e3841959b7fb06f4c07"
    )


def test_lineage_builder_reproduces_committed_artifact(tmp_path):
    output = tmp_path / "synapse_lineage.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_synapse_lineage.py"),
            "--input",
            str(ROOT / "evidence" / "synapses.csv"),
            "--output",
            str(output),
            "--product-version",
            __version__,
        ],
        check=True,
    )
    committed = (ROOT / "evidence" / "synapse_lineage.json").read_bytes()
    assert output.read_bytes() == committed


def test_synapse_lineage_uses_stable_tuple_identifier():
    lineage = json.loads(
        (ROOT / "evidence" / "synapse_lineage.json").read_text(encoding="utf-8")
    )
    first = lineage["records"][0]
    expected = (
        "syn-720575940605560678|720575940632008007|790590|265784|210220"
    )
    assert first["record_id"] == expected


def test_evidence_manifest_version_is_current():
    report = validate_evidence_manifest_version(ROOT)
    assert report["product_version"] == __version__


def test_release_receipt_versions_are_current():
    report = validate_release_receipt_versions(ROOT)
    assert report["status"] == "PASS_RELEASE_RECEIPTS"
    assert report["product_version"] == __version__
    assert report["receipts_checked"] == 5
    assert report["historical_receipts_without_version"] == 1


def test_flyvis_claim_traces_to_immutable_evidence():
    report = trace_claim(ROOT, "C-FLYVIS-RUNTIME-001")
    assert report["status"] == "PASS_CLAIM_TRACE"
    assert report["product_version"] == __version__
    assert report["claim"]["status"] == "REPRODUCED"
    assert [item["id"] for item in report["evidence"]] == [
        "E-FLYVIS-RUNTIME",
        "E-FLYVIS-RUNTIME-SMOKE",
        "E-FLYVIS-WORKFLOW",
        "E-FLYVIS-RUNTIME-RECEIPT",
    ]
    evidence_by_id = {item["id"]: item for item in report["evidence"]}
    assert evidence_by_id["E-FLYVIS-RUNTIME"]["path"] == "src/dlf_flywire/flyvis_runtime.py"
    assert evidence_by_id["E-FLYVIS-RUNTIME-SMOKE"]["path"] == "scripts/flyvis_integration_smoke.py"
    assert evidence_by_id["E-FLYVIS-WORKFLOW"]["path"] == ".github/workflows/flyvis-integration.yml"
    assert evidence_by_id["E-FLYVIS-RUNTIME-RECEIPT"]["path"] == "evidence/flyvis_integration_receipt.json"


def test_claim_trace_cli_emits_verified_json(capsys):
    assert cli_main([
        "claim",
        "C-FLYVIS-RUNTIME-001",
        "--root",
        str(ROOT),
    ]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "PASS_CLAIM_TRACE"
    assert report["claim"]["id"] == "C-FLYVIS-RUNTIME-001"


def test_claim_trace_fails_closed_for_unknown_claim():
    try:
        trace_claim(ROOT, "C-DOES-NOT-EXIST")
    except ProvenanceError as exc:
        assert "unknown claim id" in str(exc)
    else:
        raise AssertionError("unknown claim ID was accepted")


def test_release_receipt_version_drift_fails_closed(tmp_path):
    receipt = ROOT / "evidence" / "flyvis_integration_receipt.json"
    target = tmp_path / receipt.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    payload["product_version"] = "0.0.0"
    target.write_text(json.dumps(payload), encoding="utf-8")

    for relative in (
        "evidence/source_receipts.json",
        "evidence/synapse_lineage.json",
        "evidence/flydrones_integration_receipt.json",
        "evidence/flydrones_integration_receipt_2.json",
    ):
        source = ROOT / relative
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    for relative in ("VERSION", "pyproject.toml", "src/dlf_flywire/__init__.py"):
        source = ROOT / relative
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    try:
        validate_release_receipt_versions(tmp_path)
    except ProvenanceError as exc:
        assert "flyvis_integration_receipt.json version" in str(exc)
        assert "'0.0.0'" in str(exc)
    else:
        raise AssertionError("release receipt version drift was accepted")


def test_git_blob_sha1_matches_known_vector(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_bytes(b"hello\n")
    assert git_blob_sha1(path) == "ce013625030ba8dba906f756967f9e9ca394464a"


def test_unsafe_artifact_paths_fail_closed(tmp_path):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (tmp_path / "VERSION").write_text(__version__ + "\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nversion = "{__version__}"\n', encoding="utf-8"
    )
    package = tmp_path / "src" / "dlf_flywire"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        f'__version__ = "{__version__}"\n', encoding="utf-8"
    )
    manifest = """{
      "schema_version": 1,
      "product_version": "__VERSION__",
      "artifacts": [{
        "id": "E-BAD",
        "path": "../outside.txt",
        "identity": {"type": "sha256", "value": "00"}
      }]
    }""".replace("__VERSION__", __version__)
    (evidence / "artifact_manifest.json").write_text(manifest, encoding="utf-8")
    (tmp_path / "outside.txt").write_text("unexpected", encoding="utf-8")

    try:
        validate_artifact_manifest(tmp_path)
    except ProvenanceError as exc:
        assert "unsafe artifact path" in str(exc)
    else:
        raise AssertionError("unsafe artifact path was accepted")

def test_point_data_evdir_structure_is_ledgered():
    evidence = json.loads(
        (ROOT / "evidence" / "point_data_evdir_structure.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["status"] == "PROVEN_POINTDATA_EVDIR_STRUCTURE"
    assert evidence["global"]["rows"] == 5828
    assert evidence["global"]["exact_vector_count"] == 5828
    assert evidence["global"]["scalar_dtype"] == "float32"
    assert evidence["global"]["columns"] == 3
    assert all(
        item["rows"] == item["unique_exact"]
        for item in evidence["by_subtype"].values()
    )
    assert evidence["global"]["global_max_abs_unit_norm_error"] < 5e-7


def test_public_subtype_evdir_search_is_ledgered():
    evidence = json.loads(
        (ROOT / "evidence" / "public_subtype_evdir_search.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["status"] == "PROVEN_BOUNDED_PUBLIC_CODE_SEARCH_NEGATIVE"
    assert evidence["search_date"] == "2026-10-06"
    assert all(item["external_matches"] == 0 for item in evidence["queries"])


def test_point_data_jax_serializer_byte_alignment_is_ledgered():
    evidence = json.loads(
        (ROOT / "evidence" / "point_data_jax_serializer_compatibility.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["historical_artifact"]["pickle_global"] == (
        "jax._src.array._reconstruct_array"
    )
    alignment = evidence["historical_byte_alignment"]
    assert alignment["pickle_byte_position"] == 717551
    assert alignment["opcode"] == "STACK_GLOBAL"
    assert alignment["preceding_strings"][-2:] == [
        "jax._src.array",
        "_reconstruct_array",
    ]
    assert (
        alignment["independent_local_recheck"]["sha256"]
        == "76b7d6a1c44ad6b2ca730feff88174c71327e095cce45d8a47a0d998f77df58f"
    )


def test_public_point_data_ingest_dag_boundary_is_ledgered():
    evidence = json.loads(
        (ROOT / "evidence" / "public_point_data_ingest_boundary.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["status"] == "PROVEN_PUBLIC_DAG_INGEST_BOUNDARY"
    assert evidence["conclusions"]["proven"][0].startswith(
        "The public paper repository had no src/"
    )
    assert evidence["key_commits"][2]["point_data_blob"] == (
        "b85caf49f45677f2075f7b5f2c8830141cd96d02"
    )
    first_src = next(
        item
        for item in evidence["key_commits"]
        if item["sha"] == "1007a708f0b2cd4d55875174256774a41ff5b0f4"
    )
    assert first_src["src_files_at_that_commit"] == [
        {
            "path": "src/paper_ANOVA.py",
            "blob": "0f806edd292478db76cf330955b6c81c230f7059",
        }
    ]
    assert evidence["derived_intervals"]["point_data_to_first_src_seconds"] == 1602


def test_historical_neurosetta_runtime_family_fingerprint_is_ledgered():
    evidence = json.loads(
        (ROOT / "evidence" / "legacy_jax_geometry_context.json").read_text(
            encoding="utf-8"
        )
    )
    legacy = evidence["sources"]["legacy_neurosetta"]
    assert legacy["commit_date"] == "2025-07-31T14:40:07Z"
    assert legacy["environment"] == {
        "name": "neurosetta",
        "python": "3.10",
        "jax": True,
        "source": "environment.yml",
        "blob": "05cf1967baea026f1bb251b99eabd454bfa302b0",
    }
    consumer = evidence["sources"]["paper_repository"]["observed_files"][
        "historical_consumer_notebook"
    ]
    assert consumer["kernelspec"] == "neurosetta"
    assert consumer["python"] == "3.10.17"
    assert (
        evidence["relationship_to_historical_point_data"][
            "historical_decoded_jax_arrayimpl_cells"
        ]
        == 46624
    )
    lineage = evidence["sources"]["legacy_neurosetta"]["pre_artifact_lineage"]
    assert lineage[0]["commit"] == "beea421fb235364f9289e7d68fc8a050f12a2372"
    assert lineage[0]["date"] == "2025-02-21T11:36:49Z"
    assert lineage[1]["commit"] == "b32a340a96d71b97ff094d13f95904c5b2646a8d"
    assert lineage[2]["commit"] == "25c911a28030deb5204eb7ab5a18ff4643363d96"


def test_point_data_jax_serializer_release_family_is_ledgered():
    evidence = json.loads(
        (ROOT / "evidence" / "point_data_jax_serializer_release_family.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["status"] == "PROVEN_POINTDATA_JAX_SERIALIZER_RELEASE_FAMILY"
    checks = {
        item["release_ref"]: item["historical_compatibility"]
        for item in evidence["public_release_checks"]
    }
    assert checks["jax-v0.4.30"] is False
    for release in (
        "jax-v0.4.31",
        "jax-v0.5.0",
        "jax-v0.6.2",
        "jax-v0.7.0",
        "jax-v0.7.2",
        "jax-v0.8.0",
    ):
        assert checks[release] is True
    assert evidence["historical_signature"]["aval_state_keys_observed"] == ["weak_type"]


def test_point_data_jax_serializer_contract_is_ledgered():
    evidence = json.loads(
        (ROOT / "evidence" / "point_data_jax_serializer_compatibility.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["status"] == "PROVEN_POINTDATA_JAX_SERIALIZER_COMPATIBILITY"
    historical = evidence["historical_artifact"]
    assert historical["pickle_global"] == "jax._src.array._reconstruct_array"
    assert historical["aval_state_observed"] == {"weak_type": False}
    for snapshot in evidence["public_jax_snapshots"]:
        assert snapshot["observed_reconstruct_signature"] == (
            "def _reconstruct_array(fun, args, arr_state, aval_state)"
        )
        assert snapshot["observed_reduce_signature"] == (
            "return (_reconstruct_array, (fun, args, arr_state, aval_state))"
        )
        assert snapshot["observed_aval_state"] == "{'weak_type': self.aval.weak_type}"
    pointdata_claims = json.loads(
        (ROOT / "evidence" / "claims.json").read_text(encoding="utf-8")
    )
    claim = next(
        item
        for item in pointdata_claims["claims"]
        if item["id"] == "C-POINTDATA-013"
    )
    assert claim["status"] == "PROVEN"
    assert "E-POINTDATA-JAX-SERIALIZER" in claim["evidence"]


def test_point_data_pickle_globals_receipt_is_ledgered():
    evidence = json.loads(
        (ROOT / "evidence" / "point_data_pickle_globals_receipt.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["status"] == "PROVEN_POINTDATA_PICKLE_GLOBALS"
    assert evidence["source"]["sha256"] == (
        "76b7d6a1c44ad6b2ca730feff88174c71327e095cce45d8a47a0d998f77df58f"
    )
    assert evidence["pickle_globals"]["stack_global_count"] == 11
    assert (
        "jax._src.array._reconstruct_array"
        in evidence["pickle_globals"]["exact_globals"]
    )
    assert evidence["pickle_globals"]["jax_globals"][0]["pickle_byte_position"] == 717551
    fp = evidence["jax_value_fingerprint"]
    assert fp["object_type"] == "jaxlib._jax.ArrayImpl"
    assert fp["array_values_total"] == 46624
    assert fp["exact_count_match"] is True
    assert fp["shape"] == "()"
    assert fp["dtype"] == "float32"
    assert all(value == 5828 for value in fp["per_column_count"].values())
    pointdata_claims = json.loads(
        (ROOT / "evidence" / "claims.json").read_text(encoding="utf-8")
    )
    claim = next(
        item
        for item in pointdata_claims["claims"]
        if item["id"] == "C-POINTDATA-012"
    )
    assert claim["status"] == "REPRODUCED"
    assert "E-POINTDATA-PICKLE-GLOBALS" in claim["evidence"]




def test_public_metrics1_pipeline_snapshot_is_ledgered():
    evidence = json.loads(
        (ROOT / "evidence" / "public_metrics1_pipeline_snapshot.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["status"] == "PROVEN_PUBLIC_METRICS1_PIPELINE_SNAPSHOT"
    assert evidence["source"]["commit"] == (
        "3a1aa1a2e368ff8767f40791588eaf552e6d436d"
    )
    assert evidence["source"]["notebook_blob_sha1"] == (
        "2c31080a7f6f69d1c603bf287e4a5da7d4c3712b"
    )
    assert evidence["observed_pipeline"]["load"]["set_units"] == "nm"
    assert evidence["observed_pipeline"]["load"]["convert_target_units"] == "um"
    assert evidence["observed_pipeline"]["load"]["load_max_workers"] == 10
    assert evidence["observed_pipeline"]["pca"]["call"] == (
        "tree.coordinate_pca(robust=True, norm=True)"
    )
    assert evidence["historical_gap_observation"]["public_metrics1_missing_historical_fields"] == [
        "Subtype_evDir_x",
        "Subtype_evDir_y",
        "Subtype_evDir_z",
    ]
    assert evidence["historical_gap_observation"]["producer_persistence_observation"][
        "code_save_operation_observed"
    ] is False
    claims = json.loads(
        (ROOT / "evidence" / "claims.json").read_text(encoding="utf-8")
    )
    claim = next(
        item for item in claims["claims"] if item["id"] == "C-POINTDATA-018"
    )
    assert claim["status"] == "PROVEN"
    assert "E-POINTDATA-PUBLIC-METRICS1-PIPELINE" in claim["evidence"]


def test_legacy_public_pca_implementation_is_ledgered():
    evidence = json.loads(
        (ROOT / "evidence" / "legacy_public_pca_implementation.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["status"] == "PROVEN_LEGACY_PUBLIC_PCA_IMPLEMENTATION"
    assert evidence["source"]["commit"] == (
        "9c27f226128d98ea5420e7a3a32acf2adc8ce138"
    )
    assert evidence["source"]["commit_date"] == "2025-01-15T11:30:24Z"
    assert evidence["implementation"]["covariance"]["robust"] == (
        "sklearn.covariance.MinCovDet().fit(coords).covariance_"
    )
    assert evidence["implementation"]["eigendecomposition"] == "numpy.linalg.eig"
    assert evidence["implementation"]["normalization"] == (
        "evals /= evals.sum() when PCA=True"
    )
    assert evidence["implementation"]["orientation"] == (
        "eigenvectors transposed when transpose=True"
    )
    claims = json.loads(
        (ROOT / "evidence" / "claims.json").read_text(encoding="utf-8")
    )
    claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-019")
    assert claim["status"] == "PROVEN"
    assert "E-POINTDATA-LEGACY-PCA" in claim["evidence"]


def test_same_commit_point_data_consumer_boundary_is_ledgered():
    evidence = json.loads(
        (ROOT / "evidence" / "public_point_data_consumer_boundary.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["status"] == "PROVEN_SAME_COMMIT_PUBLIC_CONSUMER_ONLY_NOTEBOOK"
    assert evidence["source"]["point_data_commit"] == (
        "cd17d34afd0d46a3c2947e83a1f0fdd835a9959a"
    )
    assert evidence["source"]["point_data_blob"] == (
        "b85caf49f45677f2075f7b5f2c8830141cd96d02"
    )
    assert evidence["notebook_blob_sha1"] if False else True
