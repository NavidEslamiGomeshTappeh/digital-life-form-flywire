import pytest

from dlf_flywire.neural_gateway import (
    IntentRule,
    NeuralGatewayError,
    NeuralIntentGateway,
    NeuralObservation,
)
from dlf_flywire.neural_leader import NeuralLeaderBridge


def gateway():
    return NeuralIntentGateway(
        (
            IntentRule(
                capability="code.write",
                neuron_weights={"vision-A": 1.0, "vision-B": 0.5},
                threshold=0.02,
            ),
            IntentRule(
                capability="code.test.python",
                neuron_weights={"vision-A": 0.2, "vision-B": 0.2},
                threshold=0.02,
            ),
        )
    )


def test_neural_signal_selects_leader_capability_deterministically():
    observations = (
        NeuralObservation("vision-A", spikes=3, window_ms=100),
        NeuralObservation("vision-B", spikes=2, window_ms=100),
    )
    candidate = gateway().select(observations)

    assert candidate.capability == "code.write"
    assert candidate.activated is True
    assert candidate.score == pytest.approx(0.04)
    assert len(candidate.evidence_sha256) == 64


def test_neural_signal_becomes_a_normal_leader_step_without_granting_permission():
    candidate = gateway().select(
        (
            NeuralObservation("vision-A", spikes=3, window_ms=100),
            NeuralObservation("vision-B", spikes=2, window_ms=100),
        )
    )
    step = NeuralLeaderBridge().build_step(
        candidate,
        step_id="neural-code-write",
        action="Code Hand create source file",
        operation_args=("-c", "print('bounded')"),
    )

    assert step.capability == "code.write"
    assert step.permission_granted is False
    assert step.network_access is False
    assert step.system_mutation is False


def test_neural_gateway_rejects_mixed_windows():
    with pytest.raises(NeuralGatewayError, match="one time window"):
        gateway().evaluate(
            (
                NeuralObservation("vision-A", 1, 100),
                NeuralObservation("vision-B", 1, 200),
            )
        )


def test_neural_gateway_fails_closed_when_no_intent_activates():
    with pytest.raises(NeuralGatewayError, match="no neural intent"):
        gateway().select((NeuralObservation("vision-A", 0, 100),))



def test_neural_observation_accepts_fractional_millisecond_windows():
    observation = NeuralObservation("vision-A", spikes=1, window_ms=0.5)
    assert observation.window_ms == 0.5


def test_neural_observation_rejects_non_integer_spike_counts():
    with pytest.raises(NeuralGatewayError, match="spikes"):
        NeuralObservation("vision-A", spikes=1.5, window_ms=100)

    with pytest.raises(NeuralGatewayError, match="spikes"):
        NeuralObservation("vision-A", spikes=True, window_ms=100)
