from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


class CrossSourceValidationError(RuntimeError):
    """Raised when frozen cross-source evidence is inconsistent."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CrossSourceValidationError(f"invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CrossSourceValidationError(f"expected JSON object: {path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hex(value: Any, length: int, field: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(rf"[0-9a-f]{{{length}}}", value):
        raise CrossSourceValidationError(f"invalid {field}")
    return value


def _positive_int(value: Any, field: str) -> int:
    if not isinstance(value, int) or value < 0:
        raise CrossSourceValidationError(f"invalid {field}")
    return value


def _safe_relative_path(value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value:
        raise CrossSourceValidationError(f"invalid {field}")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise CrossSourceValidationError(f"unsafe {field}: {value}")
    return path


def validate_cross_source_receipts(root: Path) -> dict[str, Any]:
    path = root / "evidence" / "source_receipts.json"
    receipt = _load_json(path)

    if receipt.get("schema_version") != 1:
        raise CrossSourceValidationError("unsupported source receipt schema")

    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if receipt.get("product_version") != version:
        raise CrossSourceValidationError(
            f"source receipt version {receipt.get('product_version')!r} != {version!r}"
        )

    canonical = receipt.get("canonical_reference")
    if not isinstance(canonical, dict):
        raise CrossSourceValidationError("missing canonical_reference")

    canonical_path_value = canonical.get("path")
    canonical_path = root / _safe_relative_path(
        canonical_path_value, "canonical reference path"
    )
    if not canonical_path.is_file():
        raise CrossSourceValidationError(
            f"canonical reference artifact missing: {canonical_path_value}"
        )

    expected_sha256 = _hex(canonical.get("sha256"), 64, "canonical SHA-256")
    observed_sha256 = sha256_file(canonical_path)
    if observed_sha256 != expected_sha256:
        raise CrossSourceValidationError(
            f"canonical artifact SHA-256 mismatch: expected {expected_sha256}, "
            f"observed {observed_sha256}"
        )

    expected_rows = _positive_int(canonical.get("rows"), "canonical row count")
    with canonical_path.open(encoding="utf-8", newline="") as fh:
        row_count = max(sum(1 for _ in fh) - 1, 0)
    if row_count != expected_rows:
        raise CrossSourceValidationError(
            f"canonical row count mismatch: expected {expected_rows}, observed {row_count}"
        )

    sources = receipt.get("sources")
    if not isinstance(sources, list) or len(sources) < 2:
        raise CrossSourceValidationError(
            "at least two source receipts are required for cross-source validation"
        )

    source_ids: set[str] = set()
    providers: set[str] = set()
    artifacts: set[str] = set()
    workflow_runs: set[int] = set()
    releases: set[str] = set()
    reports: list[dict[str, Any]] = []

    for source in sources:
        if not isinstance(source, dict):
            raise CrossSourceValidationError("source receipt must be an object")

        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id:
            raise CrossSourceValidationError("source receipt id must be non-empty")
        if source_id in source_ids:
            raise CrossSourceValidationError(
                f"duplicate source receipt id: {source_id}"
            )
        source_ids.add(source_id)

        provider = source.get("provider")
        if not isinstance(provider, str) or not provider:
            raise CrossSourceValidationError(f"missing provider for {source_id}")
        if provider in providers:
            raise CrossSourceValidationError(
                f"source providers must be distinct: {provider}"
            )
        providers.add(provider)

        artifact = source.get("artifact")
        if not isinstance(artifact, str) or not artifact:
            raise CrossSourceValidationError(f"missing artifact for {source_id}")
        if artifact in artifacts:
            raise CrossSourceValidationError(
                f"source artifacts must be distinct: {artifact}"
            )
        artifacts.add(artifact)

        proof = source.get("proof")
        if not isinstance(proof, dict):
            raise CrossSourceValidationError(f"missing proof metadata for {source_id}")

        workflow_run_id = _positive_int(
            proof.get("workflow_run_id"), f"{source_id} workflow_run_id"
        )
        if workflow_run_id <= 0:
            raise CrossSourceValidationError(f"invalid workflow_run_id for {source_id}")
        if workflow_run_id in workflow_runs:
            raise CrossSourceValidationError(
                f"proof workflow run ids must be distinct: {workflow_run_id}"
            )
        workflow_runs.add(workflow_run_id)

        proof_artifact = _safe_relative_path(
            proof.get("artifact"), f"{source_id} proof artifact"
        )
        proof_path = root / proof_artifact
        if not proof_path.is_file():
            raise CrossSourceValidationError(
                f"missing proof artifact for {source_id}: {proof_artifact.as_posix()}"
            )

        source_url = proof.get("source_url")
        if not isinstance(source_url, str) or not source_url.startswith(
            ("https://", "http://")
        ):
            raise CrossSourceValidationError(f"invalid proof source URL for {source_id}")

        release = source.get("dataset")
        if not isinstance(release, str) or not release:
            raise CrossSourceValidationError(
                f"missing dataset release for {source_id}"
            )
        releases.add(release)

        matches = _positive_int(
            source.get("exact_matches"), f"{source_id} exact_matches"
        )
        if matches != expected_rows:
            raise CrossSourceValidationError(
                f"{source_id} exact match count {matches} != canonical rows {expected_rows}"
            )

        missing = _positive_int(
            source.get("missing_matches"), f"{source_id} missing_matches"
        )
        duplicates = _positive_int(
            source.get("duplicate_matches"), f"{source_id} duplicate_matches"
        )
        if missing != 0 or duplicates != 0:
            raise CrossSourceValidationError(
                f"{source_id} is not exact: missing={missing}, duplicates={duplicates}"
            )

        report: dict[str, Any] = {
            "id": source_id,
            "provider": provider,
            "artifact": artifact,
            "dataset": release,
            "proof": {
                "workflow_run_id": workflow_run_id,
                "artifact": proof_artifact.as_posix(),
                "source_url": source_url,
            },
            "exact_matches": matches,
            "missing_matches": missing,
            "duplicate_matches": duplicates,
        }

        if source.get("source_sha256") is not None:
            report["source_sha256"] = _hex(
                source["source_sha256"], 64, f"{source_id} source SHA-256"
            )
        if source.get("source_md5") is not None:
            report["source_md5"] = _hex(
                source["source_md5"], 32, f"{source_id} source MD5"
            )
        if source.get("mapping_sha256") is not None:
            report["mapping_sha256"] = _hex(
                source["mapping_sha256"], 64, f"{source_id} mapping SHA-256"
            )

        reports.append(report)

    if releases != {"FAFB v783"}:
        raise CrossSourceValidationError(
            f"cross-source release mismatch: {sorted(releases)}"
        )

    if len(source_ids) < 2 or len(providers) < 2:
        raise CrossSourceValidationError(
            "source independence requires at least two distinct providers"
        )
    if len(workflow_runs) < 2:
        raise CrossSourceValidationError(
            "source proof records must use distinct workflow run ids"
        )

    return {
        "status": "PASS_FROZEN_CROSS_SOURCE_RECEIPTS",
        "product_version": version,
        "canonical_rows": expected_rows,
        "canonical_sha256": observed_sha256,
        "independent_source_receipts": len(reports),
        "sources": reports,
        "limitation": (
            "This validates immutable source receipts and proof metadata; "
            "it does not re-download or re-run the 9.5 GB Zenodo source."
        ),
    }
