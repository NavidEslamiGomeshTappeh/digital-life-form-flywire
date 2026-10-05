from __future__ import annotations

import math

import pytest
from dlf_flywire.flyvis_adapter import (
    FlyVisAdapterError,
    FlyVisResponseAdapter,
)


MODEL_SHA = "a" * 64


def test_flyvis_adapter_preserves_continuous_trace_without_spike_conversion():
    signal = FlyVisResponseAdapter.extract(
        [0.25, -0.5, 1.0],
        cell_type="T4c",
        start_ms=-1.0,
        dt_ms=5.0,
        source_revision="92b3845cc426dd309a1a0e1b3890156c42e14021",
        model_artifact_sha256=MODEL_SHA,
    )

    assert signal.cell_type == "T4c"
    assert signal.responses == (0.25, -0.5, 1.0)
    assert signal.start_ms == -1.0
    assert signal.dt_ms == 5.0
    assert signal.adapter_version == FlyVisResponseAdapter.VERSION
    assert len(signal.response_sha256) == 64
    assert len(signal.source_sha256) == 64
    assert signal.response_sha256 != signal.source_sha256


def test_flyvis_response_fingerprint_is_deterministic():
    kwargs = {
        "cell_type": "T5a",
        "start_ms": 0.0,
        "dt_ms": 5.0,
        "source_revision": "rev-A",
        "model_artifact_sha256": MODEL_SHA,
    }

    first = FlyVisResponseAdapter.extract([0.0, 1.5, 2.0], **kwargs)
    second = FlyVisResponseAdapter.extract([0.0, 1.5, 2.0], **kwargs)

    assert first.response_sha256 == second.response_sha256
    assert first.source_sha256 == second.source_sha256


def test_flyvis_source_fingerprint_changes_with_model_revision():
    first = FlyVisResponseAdapter.extract(
        [0.0, 1.0],
        cell_type="T4a",
        start_ms=0.0,
        dt_ms=5.0,
        source_revision="rev-A",
        model_artifact_sha256=MODEL_SHA,
    )
    second = FlyVisResponseAdapter.extract(
        [0.0, 1.0],
        cell_type="T4a",
        start_ms=0.0,
        dt_ms=5.0,
        source_revision="rev-B",
        model_artifact_sha256=MODEL_SHA,
    )

    assert first.response_sha256 == second.response_sha256
    assert first.source_sha256 != second.source_sha256


def test_flyvis_response_fingerprint_changes_with_trace():
    first = FlyVisResponseAdapter.extract(
        [0.0, 1.0],
        cell_type="T4a",
        start_ms=0.0,
        dt_ms=5.0,
        source_revision="rev-A",
        model_artifact_sha256=MODEL_SHA,
    )
    second = FlyVisResponseAdapter.extract(
        [0.0, 1.1],
        cell_type="T4a",
        start_ms=0.0,
        dt_ms=5.0,
        source_revision="rev-A",
        model_artifact_sha256=MODEL_SHA,
    )

    assert first.response_sha256 != second.response_sha256
    assert first.source_sha256 != second.source_sha256


@pytest.mark.parametrize(
    ("cell_type", "expected"),
    [
        ("T4b", "cell_type"),
        ("", "cell_type"),
    ],
)
def test_flyvis_adapter_rejects_unmapped_cell_type(cell_type, expected):
    with pytest.raises(FlyVisAdapterError, match=expected):
        FlyVisResponseAdapter.extract(
            [1.0],
            cell_type=cell_type,
            start_ms=0.0,
            dt_ms=5.0,
            source_revision="rev-A",
            model_artifact_sha256=MODEL_SHA,
        )


def test_flyvis_adapter_rejects_nonfinite_response():
    with pytest.raises(FlyVisAdapterError, match="response value"):
        FlyVisResponseAdapter.extract(
            [1.0, math.nan],
            cell_type="T5c",
            start_ms=0.0,
            dt_ms=5.0,
            source_revision="rev-A",
            model_artifact_sha256=MODEL_SHA,
        )


def test_flyvis_adapter_rejects_bad_model_digest():
    with pytest.raises(FlyVisAdapterError, match="model_artifact_sha256"):
        FlyVisResponseAdapter.extract(
            [1.0],
            cell_type="T4a",
            start_ms=0.0,
            dt_ms=5.0,
            source_revision="rev-A",
            model_artifact_sha256="not-a-sha",
        )


def test_flyvis_adapter_rejects_zero_or_negative_dt():
    for dt in (0.0, -1.0):
        with pytest.raises(FlyVisAdapterError, match="dt_ms"):
            FlyVisResponseAdapter.extract(
                [1.0],
                cell_type="T4a",
                start_ms=0.0,
                dt_ms=dt,
                source_revision="rev-A",
                model_artifact_sha256=MODEL_SHA,
            )
