from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

ALLOWED_CLASSIFICATIONS = {
    "SOURCE_OBSERVATION",
    "DETERMINISTIC_COMPUTATION",
    "INDEPENDENT_CORROBORATION",
    "BIOLOGICAL_INFERENCE",
    "UNRESOLVED",
}
ALLOWED_STATUSES = {
    "PROVEN",
    "REPRODUCED",
    "INDEPENDENTLY_CORROBORATED",
    "PARTIAL",
    "NEGATIVE_RESULT",
    "BLOCKED",
    "UNRESOLVED",
    "INFERENCE_ONLY",
}
ALLOWED_IDENTITY_TYPES = {"sha256", "git_blob_sha1"}


class ProvenanceError(RuntimeError):
    """Raised when the machine-checkable evidence contract is invalid."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProvenanceError(f"invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProvenanceError(f"expected JSON object: {path}")
    return value


def _safe_relative_path(value: Any) -> Path:
    if not isinstance(value, str) or not value:
        raise ProvenanceError("artifact path must be a non-empty string")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ProvenanceError(f"unsafe artifact path: {value}")
    return path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _read_project_version(root: Path) -> str:
    version_file = (root / "VERSION").read_text(encoding="utf-8").strip()
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    package_init = (root / "src" / "dlf_flywire" / "__init__.py").read_text(
        encoding="utf-8"
    )

    project_match = re.search(r'^version\s*=\s*"([^"]+)"$', pyproject, re.MULTILINE)
    package_match = re.search(r'__version__\s*=\s*"([^"]+)"', package_init)
    versions = [version_file]
    if project_match:
        versions.append(project_match.group(1))
    else:
        raise ProvenanceError("pyproject.toml has no parseable project version")
    if package_match:
        versions.append(package_match.group(1))
    else:
        raise ProvenanceError("package __version__ is not parseable")

    if len(set(versions)) != 1:
        raise ProvenanceError(f"version drift detected: {versions}")
    return versions[0]


def validate_artifact_manifest(root: Path) -> dict[str, Any]:
    manifest_path = root / "evidence" / "artifact_manifest.json"
    manifest = _load_json(manifest_path)
    version = _read_project_version(root)

    if manifest.get("schema_version") != 1:
        raise ProvenanceError("unsupported artifact manifest schema")
    if manifest.get("product_version") != version:
        raise ProvenanceError(
            f"artifact manifest version {manifest.get('product_version')!r} != {version!r}"
        )

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ProvenanceError("artifact manifest must contain a non-empty artifacts list")

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    checked = 0

    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise ProvenanceError("artifact entry must be an object")
        artifact_id = artifact.get("id")
        if not isinstance(artifact_id, str) or not artifact_id:
            raise ProvenanceError("artifact id must be a non-empty string")
        if artifact_id in seen_ids:
            raise ProvenanceError(f"duplicate artifact id: {artifact_id}")
        seen_ids.add(artifact_id)

        relative = _safe_relative_path(artifact.get("path"))
        relative_text = relative.as_posix()
        if relative_text in seen_paths:
            raise ProvenanceError(f"duplicate artifact path: {relative_text}")
        seen_paths.add(relative_text)

        path = root / relative
        if not path.is_file():
            raise ProvenanceError(f"missing artifact: {relative_text}")

        identity = artifact.get("identity")
        if not isinstance(identity, dict):
            raise ProvenanceError(f"missing identity for {artifact_id}")
        identity_type = identity.get("type")
        expected = identity.get("value")
        if identity_type not in ALLOWED_IDENTITY_TYPES or not isinstance(expected, str):
            raise ProvenanceError(f"invalid identity for {artifact_id}")

        if identity_type == "sha256":
            observed = sha256_file(path)
        else:
            observed = git_blob_sha1(path)

        if observed != expected:
            raise ProvenanceError(
                f"artifact integrity mismatch for {artifact_id}: "
                f"expected {expected}, observed {observed}"
            )
        checked += 1

    return {
        "status": "PASS",
        "product_version": version,
        "artifacts_checked": checked,
        "artifact_ids": sorted(seen_ids),
    }


def validate_claim_ledger(root: Path) -> dict[str, Any]:
    claims_path = root / "evidence" / "claims.json"
    ledger = _load_json(claims_path)
    version = _read_project_version(root)

    if ledger.get("schema_version") != 1:
        raise ProvenanceError("unsupported claim ledger schema")
    if ledger.get("product_version") != version:
        raise ProvenanceError(
            f"claim ledger version {ledger.get('product_version')!r} != {version!r}"
        )

    claims = ledger.get("claims")
    if not isinstance(claims, list) or not claims:
        raise ProvenanceError("claim ledger must contain a non-empty claims list")

    artifact_manifest = _load_json(root / "evidence" / "artifact_manifest.json")
    artifact_ids = {
        item.get("id")
        for item in artifact_manifest.get("artifacts", [])
        if isinstance(item, dict)
    }

    seen_claims: set[str] = set()
    counts: dict[str, int] = {}
    for claim in claims:
        if not isinstance(claim, dict):
            raise ProvenanceError("claim entry must be an object")

        claim_id = claim.get("id")
        statement = claim.get("statement")
        classification = claim.get("classification")
        status = claim.get("status")
        evidence = claim.get("evidence")

        if not isinstance(claim_id, str) or not claim_id:
            raise ProvenanceError("claim id must be a non-empty string")
        if claim_id in seen_claims:
            raise ProvenanceError(f"duplicate claim id: {claim_id}")
        seen_claims.add(claim_id)

        if not isinstance(statement, str) or not statement.strip():
            raise ProvenanceError(f"empty claim statement: {claim_id}")
        if classification not in ALLOWED_CLASSIFICATIONS:
            raise ProvenanceError(f"invalid claim classification: {claim_id}")
        if status not in ALLOWED_STATUSES:
            raise ProvenanceError(f"invalid claim status: {claim_id}")
        if not isinstance(evidence, list) or not evidence:
            raise ProvenanceError(f"claim has no evidence references: {claim_id}")
        missing_refs = [ref for ref in evidence if ref not in artifact_ids]
        if missing_refs:
            raise ProvenanceError(
                f"claim {claim_id} references unknown artifacts: {missing_refs}"
            )

        if status == "UNRESOLVED" and not claim.get("caveats"):
            raise ProvenanceError(
                f"unresolved claim must declare caveats: {claim_id}"
            )

        counts[status] = counts.get(status, 0) + 1

    return {
        "status": "PASS",
        "product_version": version,
        "claims_checked": len(claims),
        "status_counts": dict(sorted(counts.items())),
    }


def validate_evidence_manifest_version(root: Path) -> dict[str, str]:
    version = _read_project_version(root)
    manifest = _load_json(root / "evidence" / "manifest.json")
    observed = manifest.get("product_version")
    if observed != version:
        raise ProvenanceError(
            f"evidence/manifest.json version {observed!r} != {version!r}"
        )
    return {"status": "PASS", "product_version": version}


def audit_provenance(root: Path) -> dict[str, Any]:
    version = _read_project_version(root)
    artifact = validate_artifact_manifest(root)
    claims = validate_claim_ledger(root)
    evidence_manifest = validate_evidence_manifest_version(root)
    return {
        "status": "PASS",
        "product_version": version,
        "artifact_manifest": artifact,
        "claim_ledger": claims,
        "evidence_manifest": evidence_manifest,
    }
