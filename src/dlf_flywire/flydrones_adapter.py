from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from numbers import Integral, Real

from .neural_gateway import NeuralObservation


class FlyDronesAdapterError(ValueError):
    """Raised when a FlyDrones raster cannot be mapped safely."""


@dataclass(frozen=True)
class FlyDronesSignal:
    """A provenance-bearing neural window extracted from a FlyDrones Brain."""

    observations: tuple[NeuralObservation, ...]
    start_ms: float
    end_ms: float
    source_revision: str
    source_sha256: str
    extraction_sha256: str
    adapter_version: str


class FlyDronesRasterAdapter:
    """Map FlyDrones recorded raster positions to stable MaleCNS body IDs.

    The adapter intentionally imports no FlyDrones package. It consumes the
    public runtime shape exposed by Brain: last_raster, record, and
    connectome.body_ids. The source revision must be supplied by the caller
    so provenance is explicit rather than inferred.
    """

    VERSION = "1"

    @classmethod
    def extract(
        cls,
        brain: object,
        *,
        start_ms: Real,
        end_ms: Real,
        source_revision: str,
    ) -> FlyDronesSignal:
        cls._validate_window(start_ms, end_ms)
        if not isinstance(source_revision, str) or not source_revision.strip():
            raise FlyDronesAdapterError("source_revision must not be empty")

        try:
            connectome = brain.connectome
            body_ids = connectome.body_ids
            record = brain.record
            raster = brain.last_raster
        except AttributeError as exc:
            raise FlyDronesAdapterError(
                "brain must expose connectome.body_ids, record, and last_raster"
            ) from exc

        if body_ids is None:
            raise FlyDronesAdapterError("connectome.body_ids is required")
        try:
            body_count = len(body_ids)
            record_count = len(record)
        except TypeError as exc:
            raise FlyDronesAdapterError("body_ids and record must be sized sequences") from exc

        raw_raster: list[tuple[float, list[int]]] = []
        events: list[tuple[float, str]] = []
        for entry in raster:
            try:
                timestamp_ms, positions = entry
            except (TypeError, ValueError) as exc:
                raise FlyDronesAdapterError(
                    "each last_raster item must be (timestamp_ms, recorded_positions)"
                ) from exc

            cls._validate_timestamp(timestamp_ms)
            timestamp = float(timestamp_ms)
            in_window = float(start_ms) <= timestamp < float(end_ms)

            try:
                iterator = iter(positions)
            except TypeError as exc:
                raise FlyDronesAdapterError("recorded_positions must be iterable") from exc

            canonical_positions: list[int] = []
            for position in iterator:
                if isinstance(position, bool) or not isinstance(position, Integral):
                    raise FlyDronesAdapterError(
                        "raster record position must be an integer"
                    )
                record_position = int(position)
                canonical_positions.append(record_position)
                if not 0 <= record_position < record_count:
                    raise FlyDronesAdapterError(
                        f"record position {record_position} is outside Brain.record"
                    )

                neuron_index = record[record_position]
                if isinstance(neuron_index, bool) or not isinstance(neuron_index, Integral):
                    raise FlyDronesAdapterError(
                        "Brain.record neuron indices must be integers"
                    )
                neuron_index = int(neuron_index)
                if not 0 <= neuron_index < body_count:
                    raise FlyDronesAdapterError(
                        f"Brain.record neuron index {neuron_index} is outside body_ids"
                    )

                body_id = body_ids[neuron_index]
                if isinstance(body_id, bool) or not isinstance(body_id, Integral):
                    raise FlyDronesAdapterError(
                        "connectome.body_ids must contain integer body IDs"
                    )
                if in_window:
                    events.append((timestamp, f"malecns-body:{int(body_id)}"))
            raw_raster.append((timestamp, canonical_positions))

        duration_ms = float(end_ms) - float(start_ms)
        counts: dict[str, int] = {}
        for _timestamp, neuron_id in events:
            counts[neuron_id] = counts.get(neuron_id, 0) + 1

        observations = tuple(
            NeuralObservation(neuron_id, count, duration_ms)
            for neuron_id, count in sorted(counts.items())
        )
        source_sha256 = cls._source_snapshot_fingerprint(
            source_revision,
            tuple(int(body_id) for body_id in body_ids),
            tuple(int(neuron_index) for neuron_index in record),
            tuple(raw_raster),
        )
        extraction_sha256 = cls._extraction_fingerprint(
            source_revision,
            float(start_ms),
            float(end_ms),
            tuple(sorted(events)),
        )
        return FlyDronesSignal(
            observations=observations,
            start_ms=float(start_ms),
            end_ms=float(end_ms),
            source_revision=source_revision,
            source_sha256=source_sha256,
            extraction_sha256=extraction_sha256,
            adapter_version=cls.VERSION,
        )

    @staticmethod
    def _validate_window(start_ms: Real, end_ms: Real) -> None:
        if (
            isinstance(start_ms, bool)
            or isinstance(end_ms, bool)
            or not isinstance(start_ms, Real)
            or not isinstance(end_ms, Real)
            or not math.isfinite(float(start_ms))
            or not math.isfinite(float(end_ms))
            or float(end_ms) <= float(start_ms)
        ):
            raise FlyDronesAdapterError("end_ms must be a finite real value greater than start_ms")

    @staticmethod
    def _validate_timestamp(timestamp_ms: object) -> None:
        if (
            isinstance(timestamp_ms, bool)
            or not isinstance(timestamp_ms, Real)
            or not math.isfinite(float(timestamp_ms))
            or float(timestamp_ms) < 0
        ):
            raise FlyDronesAdapterError("raster timestamp_ms must be a finite non-negative real value")

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

    @classmethod
    def _source_snapshot_fingerprint(
        cls,
        source_revision: str,
        body_ids: tuple[int, ...],
        record: tuple[int, ...],
        raster: tuple[tuple[float, list[int]], ...],
    ) -> str:
        return cls._hash_payload(
            {
                "adapter_version": cls.VERSION,
                "body_ids": list(body_ids),
                "raster": [
                    {"positions": positions, "timestamp_ms": timestamp}
                    for timestamp, positions in raster
                ],
                "record": list(record),
                "source_revision": source_revision,
            }
        )

    @classmethod
    def _extraction_fingerprint(
        cls,
        source_revision: str,
        start_ms: float,
        end_ms: float,
        events: tuple[tuple[float, str], ...],
    ) -> str:
        return cls._hash_payload(
            {
                "adapter_version": cls.VERSION,
                "end_ms": end_ms,
                "events": [
                    {"neuron_id": neuron_id, "timestamp_ms": timestamp}
                    for timestamp, neuron_id in events
                ],
                "source_revision": source_revision,
                "start_ms": start_ms,
            }
        )
