from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from numbers import Real


class FlyVisAdapterError(ValueError):
    """Raised when a FlyVis response trace cannot be mapped safely."""


@dataclass(frozen=True)
class FlyVisResponseSignal:
    """A provenance-bearing continuous response trace from a FlyVis model.

    FlyVis produces continuous model responses in arbitrary units. This object
    therefore remains outside the spike-based NeuralObservation contract.
    """

    cell_type: str
    responses: tuple[float, ...]
    start_ms: float
    dt_ms: float
    source_revision: str
    model_artifact_sha256: str
    response_sha256: str
    source_sha256: str
    adapter_version: str


class FlyVisResponseAdapter:
    """Validate and fingerprint FlyVis cell-type response traces.

    This adapter intentionally does not import FlyVis or convert continuous
    response values into spike counts. The caller must provide the exact
    upstream revision and immutable model-artifact digest.
    """

    VERSION = "1"
    SUPPORTED_CELL_TYPES = frozenset({"T4a", "T4c", "T5a", "T5c"})

    @classmethod
    def extract(
        cls,
        responses: Sequence[Real],
        *,
        cell_type: str,
        start_ms: Real,
        dt_ms: Real,
        source_revision: str,
        model_artifact_sha256: str,
    ) -> FlyVisResponseSignal:
        cls._validate_cell_type(cell_type)
        cls._validate_time(start_ms, dt_ms)
        cls._validate_revision(source_revision)
        cls._validate_digest(model_artifact_sha256, "model_artifact_sha256")

        if not responses:
            raise FlyVisAdapterError("responses must not be empty")

        normalized: list[float] = []
        for index, value in enumerate(responses):
            if isinstance(value, bool) or not isinstance(value, Real):
                raise FlyVisAdapterError(
                    f"response value {index} must be a finite real number"
                )
            value_float = float(value)
            if not math.isfinite(value_float):
                raise FlyVisAdapterError(
                    f"response value {index} must be a finite real number"
                )
            normalized.append(value_float)

        response_payload = {
            "adapter_version": cls.VERSION,
            "cell_type": cell_type,
            "dt_ms": float(dt_ms),
            "responses": normalized,
            "start_ms": float(start_ms),
        }
        response_sha256 = cls._hash_payload(response_payload)
        source_sha256 = cls._hash_payload(
            {
                **response_payload,
                "model_artifact_sha256": model_artifact_sha256,
                "source_revision": source_revision,
            }
        )
        return FlyVisResponseSignal(
            cell_type=cell_type,
            responses=tuple(normalized),
            start_ms=float(start_ms),
            dt_ms=float(dt_ms),
            source_revision=source_revision,
            model_artifact_sha256=model_artifact_sha256,
            response_sha256=response_sha256,
            source_sha256=source_sha256,
            adapter_version=cls.VERSION,
        )

    @classmethod
    def _validate_cell_type(cls, cell_type: str) -> None:
        if not isinstance(cell_type, str) or cell_type not in cls.SUPPORTED_CELL_TYPES:
            allowed = ", ".join(sorted(cls.SUPPORTED_CELL_TYPES))
            raise FlyVisAdapterError(
                f"cell_type must be one of the project-supported FlyVis types: {allowed}"
            )

    @staticmethod
    def _validate_time(start_ms: Real, dt_ms: Real) -> None:
        if (
            isinstance(start_ms, bool)
            or isinstance(dt_ms, bool)
            or not isinstance(start_ms, Real)
            or not isinstance(dt_ms, Real)
            or not math.isfinite(float(start_ms))
            or not math.isfinite(float(dt_ms))
            or float(dt_ms) <= 0
        ):
            raise FlyVisAdapterError(
                "start_ms must be finite and dt_ms must be a finite value greater than zero"
            )

    @staticmethod
    def _validate_revision(source_revision: str) -> None:
        if not isinstance(source_revision, str) or not source_revision.strip():
            raise FlyVisAdapterError("source_revision must not be empty")

    @staticmethod
    def _validate_digest(value: str, field: str) -> None:
        if (
            not isinstance(value, str)
            or not re.fullmatch(r"[0-9a-fA-F]{64}", value)
        ):
            raise FlyVisAdapterError(f"{field} must be a 64-character SHA-256 hex digest")

    @staticmethod
    def _hash_payload(payload: dict[str, object]) -> str:
        return hashlib.sha256(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
