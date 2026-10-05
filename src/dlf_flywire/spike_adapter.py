from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


class SpikeAdapterError(ValueError):
    """Raised when a recorded spike train is malformed."""


@dataclass(frozen=True)
class SpikeEvent:
    neuron_id: str
    timestamp_ms: int

    def __post_init__(self) -> None:
        if not self.neuron_id.strip():
            raise SpikeAdapterError("neuron_id must not be empty")
        if (
            isinstance(self.timestamp_ms, bool)
            or not isinstance(self.timestamp_ms, int)
            or self.timestamp_ms < 0
        ):
            raise SpikeAdapterError("timestamp_ms must be a non-negative integer")


@dataclass(frozen=True)
class SpikeWindow:
    start_ms: int
    end_ms: int
    events: tuple[SpikeEvent, ...]
    source_sha256: str

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms

    def observations(self):
        from .neural_gateway import NeuralObservation

        counts: dict[str, int] = {}
        for event in self.events:
            counts[event.neuron_id] = counts.get(event.neuron_id, 0) + 1
        return tuple(
            NeuralObservation(neuron_id, count, self.duration_ms)
            for neuron_id, count in sorted(counts.items())
        )


class SpikeTrainAdapter:
    """Load a deterministic JSON spike recording and preserve its provenance."""

    @staticmethod
    def load(path: str | Path, *, start_ms: int, end_ms: int) -> SpikeWindow:
        if isinstance(start_ms, bool) or isinstance(end_ms, bool) or end_ms <= start_ms:
            raise SpikeAdapterError("end_ms must be greater than start_ms")

        source = Path(path)
        raw = source.read_bytes()
        source_sha256 = hashlib.sha256(raw).hexdigest()
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SpikeAdapterError("spike source must be valid UTF-8 JSON") from exc

        if not isinstance(payload, list):
            raise SpikeAdapterError("spike source must be a JSON list")

        events = []
        for item in payload:
            if not isinstance(item, dict):
                raise SpikeAdapterError("each spike event must be an object")
            event = SpikeEvent(str(item.get("neuron_id", "")), item.get("timestamp_ms", -1))
            if start_ms <= event.timestamp_ms < end_ms:
                events.append(event)

        events.sort(key=lambda event: (event.timestamp_ms, event.neuron_id))
        return SpikeWindow(start_ms, end_ms, tuple(events), source_sha256)
