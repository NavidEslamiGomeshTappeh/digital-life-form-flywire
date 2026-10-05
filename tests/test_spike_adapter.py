import json


import pytest

from dlf_flywire.neural_gateway import IntentRule, NeuralIntentGateway
from dlf_flywire.spike_adapter import SpikeAdapterError, SpikeTrainAdapter


def test_spike_adapter_preserves_source_and_builds_observations():
    root = Path(__file__).parent / "fixtures"
    window = SpikeTrainAdapter.load(root / "spike_recording.json", start_ms=0, end_ms=100)

    assert len(window.events) == 3
    assert window.source_sha256
    observations = window.observations()
    assert observations[0].neuron_id == "visual-channel-A"
    assert observations[0].spikes == 2
    assert observations[0].window_ms == 100


def test_real_recording_can_reach_intent_gateway():
    root = Path(__file__).parent / "fixtures"
    window = SpikeTrainAdapter.load(root / "spike_recording.json", start_ms=0, end_ms=100)
    gateway = NeuralIntentGateway((
        IntentRule(
            capability="code.write",
            neuron_weights={"visual-channel-A": 1.0},
            threshold=0.01,
            destination="code-workspace",
        ),
    ))
    candidate = gateway.select(window.observations())
    assert candidate.activated is True
    assert candidate.evidence_sha256


def test_malformed_spike_source_fails_closed(tmp_path):
    source = tmp_path / "bad.json"
    source.write_text("not-json", encoding="utf-8")
    with pytest.raises(SpikeAdapterError):
        SpikeTrainAdapter.load(source, start_ms=0, end_ms=100)


@pytest.mark.parametrize(
    ("payload", "expected_error"),
    [
        ([{"neuron_id": "A", "timestamp_ms": "10"}], "timestamp_ms"),
        ([{"neuron_id": "A", "timestamp_ms": True}], "timestamp_ms"),
        ([{"timestamp_ms": 10}], "neuron_id"),
    ],
)
def test_malformed_spike_event_fields_fail_closed(tmp_path, payload, expected_error):
    source = tmp_path / "bad-event.json"
    source.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(SpikeAdapterError, match=expected_error):
        SpikeTrainAdapter.load(source, start_ms=0, end_ms=100)
