import json
import shutil
import subprocess
import sys
from pathlib import Path

from dlf_flywire import __version__
from dlf_flywire.provenance import (
    ProvenanceError,
    audit_provenance,
    git_blob_sha1,
    validate_artifact_manifest,
    validate_claim_ledger,
    validate_evidence_manifest_version,
    trace_claim,
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
    assert report["receipts_checked"] == 4
    assert report["historical_receipts_without_version"] == 1


def test_flyvis_claim_traces_to_immutable_evidence():
    report = trace_claim(ROOT, "C-FLYVIS-RUNTIME-001")
    assert report["status"] == "PASS_CLAIM_TRACE"
    assert report["product_version"] == __version__
    assert report["claim"]["status"] == "REPRODUCED"
    assert [item["id"] for item in report["evidence"]] == ["E-FLYVIS-RUNTIME"]
    assert report["evidence"][0]["path"] == "src/dlf_flywire/flyvis_runtime.py"


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
