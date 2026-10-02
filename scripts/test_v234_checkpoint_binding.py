#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, sys, tempfile

def main():
    with tempfile.TemporaryDirectory() as td:
        state=Path(td)/"state.json"
        plan=Path(td)/"plan.json"
        plan.write_text(json.dumps({"schema":"V233-plan/v1","tasks":{
            "a":{"kind":"NOOP_VERIFY","deps":[],"payload":{"x":1},"max_attempts":1}
        }}),encoding="utf-8")
        cmd=[sys.executable,"scripts/v233_evidence_task_graph.py","--state",str(state),
             "--plan",str(plan),"--budget-seconds","10"]
        p=subprocess.run(cmd,capture_output=True,text=True)
        assert p.returncode==0,p.stderr
        s=json.loads(state.read_text())
        assert s["checkpoint_schema"]=="V234-checkpoint/v1"
        assert len(s["plan_sha256"])==64
        plan.write_text(json.dumps({"schema":"V233-plan/v1","tasks":{
            "a":{"kind":"NOOP_VERIFY","deps":[],"payload":{"x":2},"max_attempts":1}
        }}),encoding="utf-8")
        p=subprocess.run(cmd,capture_output=True,text=True)
        assert p.returncode!=0
        assert "plan digest mismatch" in (p.stderr+p.stdout)
    print("V234 checkpoint binding tests: PASS")

if __name__ == "__main__":
    main()
