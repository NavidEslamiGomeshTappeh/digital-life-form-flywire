from __future__ import annotations

import tempfile
from pathlib import Path

from dlf_flywire.code_hand import CodeHand
from dlf_flywire.flydrones_adapter import FlyDronesRasterAdapter
from dlf_flywire.neural_gateway import IntentRule, NeuralIntentGateway
from dlf_flywire.neural_leader import NeuralLeaderBridge
from dlf_flywire.orchestrator import RunPlan, TaskOrchestrator

from flydrones.brain.brain import Brain
from flydrones.brain.synthetic import build_minifly

FLYDRONES_REVISION = "6519c8c0e35ae829faa98a5a02033343dd0b82d4"


def main() -> None:
    cfg = {
        "inputs": {"t4a-left": {"types": ["^T4a$"], "side": "L"}},
        "outputs": {
            "dng02-left": {"types": ["^DNg02$"], "side": "L"},
            "t4a-left-record": {"types": ["^T4a$"], "side": "L"},
        },
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

    selected_observation = signal.observations[0]
    gateway = NeuralIntentGateway(
        (
            IntentRule(
                capability="code.write",
                neuron_weights={selected_observation.neuron_id: 1.0},
                threshold=0.001,
                destination="code-workspace",
            ),
        )
    )
    candidate = gateway.select(signal.observations)

    with tempfile.TemporaryDirectory(prefix="dlf-flydrones-") as raw_dir:
        root = Path(raw_dir)
        hand = CodeHand(root, root / "state")
        base_plan = hand.build_plan(
            "flydrones_neural.py",
            "def add(a, b):\n    return a + b\n",
            "assert add(2, 3) == 5",
            permission_granted=True,
        )
        neural_create = NeuralLeaderBridge().build_step(
            candidate,
            step_id=base_plan.steps[0].step_id,
            action=base_plan.steps[0].action,
            operation_args=base_plan.steps[0].operation_args,
            permission_granted=True,
            dependencies=base_plan.steps[0].dependencies,
            idempotent=base_plan.steps[0].idempotent,
        )
        neural_plan = RunPlan((neural_create, base_plan.steps[1]))
        orchestrator = TaskOrchestrator(
            hand.orchestrator.executor,
            root / "orchestrator-state",
        )
        run_id, receipts = orchestrator.run(
            neural_plan,
            run_id="flydrones-neural-code-hand",
        )

        assert run_id == "flydrones-neural-code-hand"
        assert receipts["create-file"].status == "succeeded"
        assert receipts["test-file"].stdout.strip() == "CODE_HAND_TEST_PASS"

    print(
        "FlyDrones integration PASS: "
        f"neurons={brain.n_neurons} records={len(brain.record)} "
        f"raster_events={sum(len(pos) for _t, pos in brain.last_raster)} "
        f"observations={len(signal.observations)}"
    )
    print(f"source_revision={signal.source_revision}")
    print(f"adapter_sha256={signal.source_sha256}")
    print(f"selected_neuron={selected_observation.neuron_id}")
    print(f"neural_evidence_sha256={candidate.evidence_sha256}")
    print("neural_intent -> leader -> code_hand -> verifier PASS")


if __name__ == "__main__":
    main()
