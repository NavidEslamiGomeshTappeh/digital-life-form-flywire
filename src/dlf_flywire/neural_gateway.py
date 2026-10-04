from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping


class NeuralGatewayError(ValueError):
    """Raised when a neural observation cannot be converted safely."""


@dataclass(frozen=True)
class NeuralObservation:
    neuron_id: str
    spikes: int
    window_ms: int

    def __post_init__(self) -> None:
        if not self.neuron_id.strip():
            raise NeuralGatewayError("neuron_id must not be empty")
        if isinstance(self.spikes, bool) or self.spikes < 0:
            raise NeuralGatewayError("spikes must be a non-negative integer")
        if isinstance(self.window_ms, bool) or self.window_ms <= 0:
            raise NeuralGatewayError("window_ms must be a positive integer")


@dataclass(frozen=True)
class IntentRule:
    """Configuration-owned mapping; neuron IDs have no built-in meaning."""

    capability: str
    neuron_weights: Mapping[str, float]
    threshold: float = 1.0
    risk_tier: int = 0
    destination: str = "local-process"

    def __post_init__(self) -> None:
        if not self.capability.strip():
            raise NeuralGatewayError("capability must not be empty")
        if not self.neuron_weights:
            raise NeuralGatewayError("neuron_weights must not be empty")
        if self.threshold <= 0:
            raise NeuralGatewayError("threshold must be positive")
        if self.risk_tier not in {0, 1, 2}:
            raise NeuralGatewayError("risk_tier must be 0, 1, or 2")
        if not self.destination.strip():
            raise NeuralGatewayError("destination must not be empty")


@dataclass(frozen=True)
class IntentCandidate:
    capability: str
    score: float
    threshold: float
    activated: bool
    risk_tier: int
    destination: str
    evidence_sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "capability": self.capability,
            "score": self.score,
            "threshold": self.threshold,
            "activated": self.activated,
            "risk_tier": self.risk_tier,
            "destination": self.destination,
            "evidence_sha256": self.evidence_sha256,
        }


class NeuralIntentGateway:
    """Convert bounded neural observations into Leader-readable candidates.

    This bridge does not claim that FlyWire neurons already control Code Hand.
    """

    def __init__(self, rules: tuple[IntentRule, ...]) -> None:
        if not rules:
            raise NeuralGatewayError("at least one intent rule is required")
        capabilities = [rule.capability for rule in rules]
        if len(capabilities) != len(set(capabilities)):
            raise NeuralGatewayError("duplicate capability rules")
        self.rules = rules

    @staticmethod
    def _evidence_hash(observations: tuple[NeuralObservation, ...]) -> str:
        payload = [
            {
                "neuron_id": item.neuron_id,
                "spikes": item.spikes,
                "window_ms": item.window_ms,
            }
            for item in sorted(
                observations, key=lambda item: (item.neuron_id, item.window_ms)
            )
        ]
        return hashlib.sha256(
            json.dumps(
                payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()

    def evaluate(
        self, observations: tuple[NeuralObservation, ...]
    ) -> tuple[IntentCandidate, ...]:
        if not observations:
            raise NeuralGatewayError("observations must not be empty")
        windows = {item.window_ms for item in observations}
        if len(windows) != 1:
            raise NeuralGatewayError("all observations must share one time window")

        rates = {
            item.neuron_id: item.spikes / item.window_ms
            for item in observations
        }
        evidence_sha256 = self._evidence_hash(observations)
        candidates = []
        for rule in self.rules:
            score = sum(
                rates.get(neuron_id, 0.0) * weight
                for neuron_id, weight in rule.neuron_weights.items()
            )
            candidates.append(
                IntentCandidate(
                    capability=rule.capability,
                    score=score,
                    threshold=rule.threshold,
                    activated=score >= rule.threshold,
                    risk_tier=rule.risk_tier,
                    destination=rule.destination,
                    evidence_sha256=evidence_sha256,
                )
            )
        return tuple(
            sorted(candidates, key=lambda item: (-item.score, item.capability))
        )

    def select(self, observations: tuple[NeuralObservation, ...]) -> IntentCandidate:
        candidates = self.evaluate(observations)
        active = [candidate for candidate in candidates if candidate.activated]
        if not active:
            raise NeuralGatewayError("no neural intent crossed its activation threshold")
        return active[0]
