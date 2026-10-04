from pathlib import Path

from dlf_flywire import __version__
from dlf_flywire.provenance import (
    ProvenanceError,
    audit_provenance,
    git_blob_sha1,
    validate_claim_ledger,
    validate_evidence_manifest_version,
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


def test_evidence_manifest_version_is_current():
    report = validate_evidence_manifest_version(ROOT)
    assert report["product_version"] == __version__


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
      "product_version": "1.1.0",
      "artifacts": [{
        "id": "E-BAD",
        "path": "../outside.txt",
        "identity": {"type": "sha256", "value": "00"}
      }]
    }"""
    (evidence / "artifact_manifest.json").write_text(manifest, encoding="utf-8")
    (tmp_path / "outside.txt").write_text("unexpected", encoding="utf-8")

    from dlf_flywire.provenance import validate_artifact_manifest

    try:
        validate_artifact_manifest(tmp_path)
    except ProvenanceError as exc:
        assert "unsafe artifact path" in str(exc)
    else:
        raise AssertionError("unsafe artifact path was accepted")
