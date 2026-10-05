from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .neural_gateway import NeuralObservation


class NeuralMappingError(ValueError):
    """Raised when a neural observation cannot be mapped safely."""


@dataclass(frozen=True)
class FunctionalNeuralLabel:
    neuron_id: str
    subtype: str
    contrast_path: str
    canonical_motion_direction: str
    identity_evidence: tuple[str, ...]
    functional_evidence: tuple[str, ...]


class EvidenceBackedNeuralMapping:
    """Map exact neuron IDs to evidence-backed functional labels.

    This layer deliberately stops before executable intent. A label such as
    "T4a / ON / front-to-back" is biological functional context, not a
    permission, capability, or Code Hand action.
    """

    def __init__(self, records: Mapping[str, Mapping[str, object]]) -> None:
        if not records:
            raise NeuralMappingError("mapping must not be empty")

        normalized: dict[str, FunctionalNeuralLabel] = {}
        for neuron_id, record in records.items():
            if not isinstance(neuron_id, str) or not neuron_id.strip():
                raise NeuralMappingError("mapping neuron IDs must be non-empty strings")

            subtype = record.get("subtype")
            contrast_path = record.get("contrast_path")
            direction = record.get("canonical_motion_direction")
            identity_evidence = record.get("identity_evidence")
            functional_evidence = record.get("functional_evidence")

            if not all(
                isinstance(value, str) and value.strip()
                for value in (subtype, contrast_path, direction)
            ):
                raise NeuralMappingError(
                    f"mapping entry {neuron_id!r} has invalid functional labels"
                )
            if not isinstance(identity_evidence, Sequence) or isinstance(
                identity_evidence, (str, bytes)
            ):
                raise NeuralMappingError(
                    f"mapping entry {neuron_id!r} has invalid identity evidence"
                )
            if not isinstance(functional_evidence, Sequence) or isinstance(
                functional_evidence, (str, bytes)
            ):
                raise NeuralMappingError(
                    f"mapping entry {neuron_id!r} has invalid functional evidence"
                )

            normalized[neuron_id] = FunctionalNeuralLabel(
                neuron_id=neuron_id,
                subtype=subtype,
                contrast_path=contrast_path,
                canonical_motion_direction=direction,
                identity_evidence=tuple(str(item) for item in identity_evidence),
                functional_evidence=tuple(str(item) for item in functional_evidence),
            )

        self._records = normalized

    @classmethod
    def from_stage_b_records(
        cls, anchors: Sequence[Mapping[str, object]]
    ) -> EvidenceBackedNeuralMapping:
        records = {}
        for anchor in anchors:
            root_id = anchor.get("root_id")
            if not isinstance(root_id, str) or not root_id.strip():
                raise NeuralMappingError("anchor root_id must be a non-empty string")
            functional_evidence = anchor.get("functional_evidence")
            if not isinstance(functional_evidence, Mapping):
                raise NeuralMappingError(
                    f"anchor {root_id!r} has no functional evidence record"
                )
            sources = functional_evidence.get("sources")
            if not isinstance(sources, Sequence) or isinstance(sources, (str, bytes)):
                raise NeuralMappingError(
                    f"anchor {root_id!r} has no functional evidence sources"
                )

            records[root_id] = {
                "subtype": anchor.get("subtype"),
                "contrast_path": anchor.get("contrast_path"),
                "canonical_motion_direction": anchor.get(
                    "canonical_motion_direction"
                ),
                "identity_evidence": anchor.get("identity_evidence"),
                "functional_evidence": [str(source) for source in sources],
            }
        return cls(records)

    def decode(
        self, observations: tuple[NeuralObservation, ...]
    ) -> tuple[FunctionalNeuralLabel, ...]:
        if not observations:
            raise NeuralMappingError("observations must not be empty")

        unknown = [item.neuron_id for item in observations if item.neuron_id not in self._records]
        if unknown:
            raise NeuralMappingError(
                f"no evidence-backed mapping exists for neuron IDs: {sorted(set(unknown))}"
            )

        return tuple(self._records[item.neuron_id] for item in observations)
