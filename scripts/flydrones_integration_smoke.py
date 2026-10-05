from dlf_flywire.flydrones_adapter import FlyDronesRasterAdapter

from flydrones.brain.brain import Brain
from flydrones.brain.synthetic import build_minifly

FLYDRONES_REVISION = "6519c8c0e35ae829faa98a5a02033343dd0b82d4"


def main() -> None:
    cfg = {
        "inputs": {"t4a-left": {"types": ["^T4a$"], "side": "L"}},
        "outputs": {"dng02-left": {"types": ["^DNg02$"], "side": "L"}},
        "brain": {"record_neurons": 32, "seed": 7},
    }
    brain = Brain(build_minifly(seed=7), cfg, seed=7)
    assert brain.connectome.body_ids is not None
    assert len(brain.record) > 0
    brain.stimulate("t4a-left", hz=10000.0, ms=20.0)
    assert brain.last_raster, "FlyDrones produced no recorded spikes"

    signal = FlyDronesRasterAdapter.extract(
        brain,
        start_ms=0.0,
        end_ms=20.0,
        source_revision=FLYDRONES_REVISION,
    )
    assert signal.observations
    assert signal.source_sha256
    assert all(obs.neuron_id.startswith("malecns-body:") for obs in signal.observations)
    print(f"FLYDrones integration PASS: neurons={brain.n_neurons} records={len(brain.record)}")
    print(f"raster_events={sum(len(pos) for _t, pos in brain.last_raster)} observations={len(signal.observations)}")
    print(f"adapter_sha256={signal.source_sha256}")


if __name__ == "__main__":
    main()