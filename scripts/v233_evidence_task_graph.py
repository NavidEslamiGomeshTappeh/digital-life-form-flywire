#!/usr/bin/env python3
"""Evidence-carrying, resumable DAG scheduler for Digital Life Form research."""
from __future__ import annotations
import argparse, hashlib, json, os, socket, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "V233-task-graph/v1"
ALLOWED_SCRIPTS = {
    "test_v229_recovery_runner.py",
    "test_v230_target_synapses.py",
    "test_v231_circuit_fingerprint.py",
    "test_evidence_ledger.py",
    "test_v231_evidence_engine.py",
    "scripts/test_v231_target_capsule.py",
    "scripts/test_v232_persistent_worker.py",
    "test_v231_audit.py",
}

def now(): return datetime.now(timezone.utc).isoformat()
def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)

def load_state(path):
    if not path.exists(): return {"schema": SCHEMA, "version": 1, "tasks": {}, "journal": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA: raise ValueError(f"unsupported state schema: {data.get('schema')}")
    return data

def journal(state, event, **data):
    state.setdefault("journal", []).append({"time": now(), "event": event, **data})
    state["journal"] = state["journal"][-4000:]

def validate_task(tid, task):
    missing = {"kind", "deps", "max_attempts", "status"} - set(task)
    if missing: raise ValueError(f"task {tid}: missing {sorted(missing)}")
    if not isinstance(task["deps"], list): raise ValueError(f"task {tid}: deps must be a list")
    if int(task["max_attempts"]) < 1: raise ValueError(f"task {tid}: max_attempts must be >= 1")

def merge_plan(state, plan):
    if plan.get("schema") != "V233-plan/v1": raise ValueError("unsupported plan schema")
    for tid, task in plan.get("tasks", {}).items():
        if tid in state["tasks"]:
            old = state["tasks"][tid]
            for key in ("kind", "deps", "payload", "max_attempts"):
                if old.get(key) != task.get(key): raise ValueError(f"task {tid}: immutable definition changed")
            continue
        state["tasks"][tid] = {
            "kind": task["kind"], "deps": list(task.get("deps", [])),
            "payload": dict(task.get("payload", {})), "max_attempts": int(task.get("max_attempts", 1)),
            "status": "PENDING", "attempts": 0, "created_at": now(), "updated_at": now()
        }
    for tid, task in state["tasks"].items():
        validate_task(tid, task)
        for dep in task["deps"]:
            if dep not in state["tasks"]: raise ValueError(f"task {tid}: unknown dependency {dep}")

def runnable(state, task):
    return task["status"] in {"PENDING", "FAILED"} and int(task["attempts"]) < int(task["max_attempts"]) and all(
        state["tasks"][d]["status"] == "DONE" for d in task["deps"])

def blocked(state, task):
    return any(state["tasks"][d]["status"] in {"BLOCKED", "FAILED"} and
               int(state["tasks"][d]["attempts"]) >= int(state["tasks"][d]["max_attempts"]) for d in task["deps"])

def execute_python_test(task, remaining):
    script = task["payload"].get("script")
    if script not in ALLOWED_SCRIPTS: raise RuntimeError(f"script not allowlisted: {script}")
    args = task["payload"].get("args", [])
    if not isinstance(args, list) or any(not isinstance(x, str) for x in args): raise ValueError("args must be a list of strings")
    timeout = min(float(task["payload"].get("timeout_seconds", 300)), max(1.0, remaining - 1.0))
    started = time.monotonic()
    p = subprocess.run([sys.executable, script, *args], text=True, capture_output=True, timeout=timeout)
    out, err = p.stdout[-12000:], p.stderr[-12000:]
    return {"status": "PASS" if p.returncode == 0 else "FAIL", "exit_code": p.returncode,
            "stdout_tail": out, "stderr_tail": err, "duration_seconds": round(time.monotonic()-started, 3),
            "output_digest": digest({"exit_code": p.returncode, "stdout": out, "stderr": err})}

def execute(task, remaining):
    if task["kind"] == "PYTHON_TEST": return execute_python_test(task, remaining)
    if task["kind"] == "NOOP_VERIFY": return {"status": "PASS", "result": "orchestration-verified", "payload_digest": digest(task["payload"])}
    raise RuntimeError(f"unregistered task kind: {task['kind']}")

def graph_status(state):
    statuses = [t["status"] for t in state["tasks"].values()]
    if statuses and all(s == "DONE" for s in statuses): return "COMPLETE"
    if any(s == "FAILED" for s in statuses): return "FAILED"
    if any(s == "PENDING" for s in statuses): return "RUNNABLE_OR_WAITING"
    if any(s == "RUNNING" for s in statuses): return "RUNNING"
    return "INCOMPLETE"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="v233_state/task_graph_state.json")
    ap.add_argument("--plan", default="v233_results/V233_plan.json")
    ap.add_argument("--budget-seconds", type=int, default=300)
    args = ap.parse_args()
    if args.budget_seconds < 5: raise SystemExit("--budget-seconds must be >= 5")
    state_path, plan_path = Path(args.state), Path(args.plan)
    state = load_state(state_path)
    merge_plan(state, json.loads(plan_path.read_text(encoding="utf-8")))
    state["worker"] = {"host": socket.gethostname(), "pid": os.getpid(), "started_at": now(), "budget_seconds": args.budget_seconds}
    atomic_write(state_path, state)
    deadline = time.monotonic() + args.budget_seconds
    journal(state, "RUN_STARTED", budget_seconds=args.budget_seconds, graph_status=graph_status(state))
    atomic_write(state_path, state)
    executed = 0
    while time.monotonic() < deadline:
        progress = False
        for tid, task in state["tasks"].items():
            if time.monotonic() >= deadline: break
            if task["status"] == "RUNNING": task["status"] = "PENDING"
            if blocked(state, task):
                if task["status"] != "BLOCKED":
                    task["status"] = "BLOCKED"; task["updated_at"] = now()
                    journal(state, "TASK_BLOCKED", task_id=tid); atomic_write(state_path, state)
                continue
            if not runnable(state, task): continue
            task["status"] = "RUNNING"; task["attempts"] += 1; task["updated_at"] = now()
            journal(state, "TASK_STARTED", task_id=tid, attempt=task["attempts"]); atomic_write(state_path, state)
            progress = True
            try:
                result = execute(task, deadline - time.monotonic())
                task["result"] = result
                if result.get("status") == "PASS":
                    task["status"] = "DONE"; task.pop("error", None); journal(state, "TASK_DONE", task_id=tid)
                else:
                    task["status"] = "FAILED"; task["error"] = "executor returned FAIL"; journal(state, "TASK_FAILED", task_id=tid, error=task["error"])
            except subprocess.TimeoutExpired:
                task["status"] = "FAILED"; task["error"] = "TimeoutExpired"; journal(state, "TASK_FAILED", task_id=tid, error=task["error"])
            except Exception as exc:
                task["status"] = "FAILED"; task["error"] = f"{type(exc).__name__}: {exc}"; journal(state, "TASK_FAILED", task_id=tid, error=task["error"])
            task["updated_at"] = now(); executed += 1; atomic_write(state_path, state)
        if not progress: break
    state["worker"]["finished_at"] = now(); state["worker"]["executed_this_run"] = executed; state["worker"]["graph_status"] = graph_status(state)
    state["worker"]["state_digest"] = digest({"tasks": state["tasks"], "journal_tail": state["journal"][-50:]})
    journal(state, "RUN_FINISHED", executed=executed, graph_status=state["worker"]["graph_status"]); atomic_write(state_path, state)
    print(json.dumps({"schema": SCHEMA, "executed": executed, "graph_status": state["worker"]["graph_status"], "digest": state["worker"]["state_digest"]}, indent=2))

if __name__ == "__main__": main()
