from dlf_flywire.neural_gateway import (
    IntentRule,
    NeuralIntentGateway,
    NeuralObservation,
)


def test_neural_candidate_has_stable_evidence_fingerprint():
    gateway = NeuralIntentGateway(
        (
            IntentRule(
                capability="code.write",
                neuron_weights={"channel": 1.0},
                threshold=0.01,
            ),
        )
    )
    observations = (NeuralObservation("channel", spikes=2, window_ms=100),)
    first = gateway.select(observations)
    second = gateway.select(observations)
    assert first.to_dict() == second.to_dict()
    assert first.evidence_sha256
