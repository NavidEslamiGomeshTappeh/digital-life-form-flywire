from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .capabilities import CapabilitySpec

PolicyStatus = Literal["allow", "deny"]


class PolicyDenied(RuntimeError):
    pass


@dataclass(frozen=True)
class ExecutionIntent:
    capability: str
    action: str
    destination: str
    risk_tier: int
    permission_granted: bool
    network_access: bool = False
    system_mutation: bool = False

    def __post_init__(self) -> None:
        if not self.capability.strip() or not self.action.strip():
            raise ValueError("capability and action must not be empty")
        if not self.destination.strip():
            raise ValueError("destination must not be empty")
        if self.risk_tier not in {0, 1, 2}:
            raise ValueError("risk_tier must be 0, 1, or 2")


@dataclass(frozen=True)
class PolicyDecision:
    status: PolicyStatus
    reason: str
    checks: dict[str, bool]

    @property
    def allowed(self) -> bool:
        return self.status == "allow"

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "reason": self.reason,
            "checks": dict(self.checks),
        }


@dataclass(frozen=True)
class PolicyGate:
    max_risk_tier: int = 0
    allow_network: bool = False
    allow_system_mutation: bool = False

    def __post_init__(self) -> None:
        if self.max_risk_tier not in {0, 1, 2}:
            raise ValueError("max_risk_tier must be 0, 1, or 2")

    def evaluate(
        self,
        capability: CapabilitySpec,
        intent: ExecutionIntent,
    ) -> PolicyDecision:
        checks = {
            "capability_matches": intent.capability == capability.name,
            "action_present": bool(intent.action.strip()),
            "destination_present": bool(intent.destination.strip()),
            "risk_within_limit": (
                intent.risk_tier <= self.max_risk_tier
                and capability.tier <= self.max_risk_tier
            ),
            "permission_granted": intent.permission_granted,
            "network_allowed": not intent.network_access or self.allow_network,
            "system_mutation_allowed": (
                not intent.system_mutation or self.allow_system_mutation
            ),
        }
        for name, passed in checks.items():
            if not passed:
                return PolicyDecision(
                    status="deny",
                    reason=f"policy check failed: {name}",
                    checks=checks,
                )
        return PolicyDecision(
            status="allow",
            reason="all policy checks passed",
            checks=checks,
        )
