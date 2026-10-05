from types import SimpleNamespace
from pathlib import Path

import pytest

from dlf_flywire.flydrones_adapter import FlyDronesAdapterError, FlyDronesRasterAdapter
from dlf_flywire.neural_gateway import IntentRule, NeuralIntentGateway


def fake_brain():
    return SimpleNamespace(
        connectome=SimpleNamespace(body_ids=[101, 202, 303]),
        record=[2, 0],
        last_raster=[
            (10.0, [0, 1]),
            (10.5, [0]),
            (20.0, [1]),
        ],
    )


def test_flydrones_raster_maps_recorded_positions_to_connectome_body_ids():
    signal = FlyDronesRasterAdapter.extract(
        fake_brain(),
        start_ms=10.0,
        end_ms=20.0,
        source_revision="6519c8c0e35ae829faa98a5a02033343dd0b82d4",
    )

    assert signal.adapter_version == FlyDronesRasterAdapter.VERSION
    assert signal.source_revision.endswith("dd0b82d4")
    assert len(signal.observations) == 2
    assert signal.observations == (
        signal.observations[0],
        signal.observations[1],
    )
    assert signal.observations[0].neuron_id == "malecns-body:101"
    assert signal.observations[0].spikes == 1
    assert signal.observations[1].neuron_id == "malecns-body:303"
    assert signal.observations[1].spikes == 2
    assert signal.observations[0].window_ms == 10.0
    assert len(signal.source_sha256) == 64


def test_flydrones_signal_fingerprint_is_deterministic():
    first = FlyDronesRasterAdapter.extract(
        fake_brain(),
        start_ms=10.0,
        end_ms=20.0,
        source_revision="rev-A",
    )
    second = FlyDronesRasterAdapter.extract(
        fake_brain(),
        start_ms=10.0,
        end_ms=20.0,
        source_revision="rev-A",
    )

    assert first.source_sha256 == second.source_sha256
    assert first.observations == second.observations


def test_flydrones_adapter_fails_closed_without_body_ids():
    brain = SimpleNamespace(
        connectome=SimpleNamespace(body_ids=None),
        record=[0],
        last_raster=[(1.0, [0])],
    )

    with pytest.raises(FlyDronesAdapterError, match="body_ids"):
        FlyDronesRasterAdapter.extract(
            brain,
            start_ms=0.0,
            end_ms=10.0,
            source_revision="rev-A",
        )


def test_flydrones_adapter_fails_closed_on_bad_record_position():
    brain = SimpleNamespace(
        connectome=SimpleNamespace(body_ids=[101]),
        record=[0],
        last_raster=[(1.0, [1])],
    )

    with pytest.raises(FlyDronesAdapterError, match="record position"):
        FlyDronesRasterAdapter.extract(
            brain,
            start_ms=0.0,
            end_ms=10.0,
            source_revision="rev-A",
        )


def test_flydrones_adapter_requires_non_empty_revision():
    with pytest.raises(FlyDronesAdapterError, match="source_revision"):
        FlyDronesRasterAdapter.extract(
            fake_brain(),
            start_ms=0.0,
            end_ms=10.0,
            source_revision="",
        )


def test_flydrones_signal_reaches_neural_gateway_without_biological_claim():
    signal = FlyDronesRasterAdapter.extract(
        fake_brain(), start_ms=10.0, end_ms=20.0, source_revision="rev-A"
    )
    gateway = NeuralIntentGateway((
        IntentRule(
            capability="bounded.test",
            neuron_weights={"malecns-body:303": 1.0},
            threshold=0.01,
        ),
    ))

    candidate = gateway.select(signal.observations)

    assert candidate.capability == "bounded.test"
    assert candidate.activated is True
    assert candidate.evidence_sha256


def test_flydrones_signal_fingerprint_changes_with_source_revision():
    first = FlyDronesRasterAdapter.extract(
        fake_brain(), start_ms=10.0, end_ms=20.0, source_revision="rev-A"
    )
    second = FlyDronesRasterAdapter.extract(
        fake_brain(), start_ms=10.0, end_ms=20.0, source_revision="rev-B"
    )
    assert first.source_sha256 != second.source_sha256
