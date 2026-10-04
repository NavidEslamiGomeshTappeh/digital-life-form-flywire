from __future__ import annotations

from dataclasses import dataclass

from .neural_gateway import IntentCandidate
from .orchestrator import TaskStep


@dataclass(frozen=True)
class NeuralLeaderBridge:
    """Turn a selected neural candidate into a normal Leader task.

    Neural activity may select a capability, but it never grants permission,
    expands risk, enables networking, or changes system-mutation policy.
    """

    def build_step(
        self,
        candidate: IntentCandidate,
        *,
        step_id: str,
        action: str,
        operation_args: tuple[str, ...] = (),
        permission_granted: bool = False,
        dependencies: tuple[str, ...] = (),
        idempotent: bool = False,
        network_access: bool = False,
        system_mutation: bool = False,
    ) -> TaskStep:
        if not candidate.activated:
            raise ValueError("inactive neural candidate cannot become a Leader step")
        if not step_id.strip() or not action.strip():
            raise ValueError("step_id and action must not be empty")

        return TaskStep(
            step_id=step_id,
            capability=candidate.capability,
            action=action,
            destination=candidate.destination,
            risk_tier=candidate.risk_tier,
            permission_granted=permission_granted,
            operation_args=operation_args,
            dependencies=dependencies,
            idempotent=idempotent,
            network_access=network_access,
            system_mutation=system_mutation,
        )
