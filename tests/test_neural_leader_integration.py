from dlf_flywire.code_hand import CodeHand
from dlf_flywire.neural_gateway import (
    IntentRule,
    NeuralIntentGateway,
    NeuralObservation,
)
from dlf_flywire.neural_leader import NeuralLeaderBridge
from dlf_flywire.orchestrator import RunPlan, TaskOrchestrator


def test_neural_selection_reaches_code_hand_execution_contract(tmp_path):
    hand = CodeHand(tmp_path, tmp_path / "state")
    base_plan = hand.build_plan(
        "neural_selected.py",
        "def add(a, b):\n    return a + b\n",
        "assert add(2, 3) == 5",
        permission_granted=True,
    )

    gateway = NeuralIntentGateway(
        (
            IntentRule(
                capability="code.write",
                neuron_weights={"visual-channel-A": 1.0},
                threshold=0.01,
                destination="code-workspace",
            ),
        )
    )
    candidate = gateway.select(
        (NeuralObservation("visual-channel-A", spikes=2, window_ms=100),)
    )
    neural_create = NeuralLeaderBridge().build_step(
        candidate,
        step_id=base_plan.steps[0].step_id,
        action=base_plan.steps[0].action,
        operation_args=base_plan.steps[0].operation_args,
        permission_granted=True,
        idempotent=base_plan.steps[0].idempotent,
    )
    neural_plan = RunPlan((neural_create, base_plan.steps[1]))

    orchestrator = TaskOrchestrator(hand.orchestrator.executor, tmp_path / "state")
    _run_id, receipts = orchestrator.run(neural_plan, run_id="neural-code-hand")
    assert receipts["create-file"].status == "succeeded"
    assert receipts["test-file"].stdout.strip() == "CODE_HAND_TEST_PASS"
