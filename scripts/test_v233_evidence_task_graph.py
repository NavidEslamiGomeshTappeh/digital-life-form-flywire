#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, sys, tempfile

def main():
    with tempfile.TemporaryDirectory() as td:
        state=Path(td)/"state.json"; plan=Path(td)/"plan.json"
        plan.write_text(json.dumps({"schema":"V233-plan/v1","tasks":{
            "a":{"kind":"NOOP_VERIFY","deps":[],"payload":{"x":1},"max_attempts":1},
            "b":{"kind":"NOOP_VERIFY","deps":["a"],"payload":{"x":2},"max_attempts":1},
            "c":{"kind":"NOOP_VERIFY","deps":["b"],"payload":{"x":3},"max_attempts":1}}}),encoding="utf-8")
        cmd=[sys.executable,"scripts/v233_evidence_task_graph.py","--state",str(state),"--plan",str(plan),"--budget-seconds","10"]
        p=subprocess.run(cmd,capture_output=True,text=True); assert p.returncode==0,p.stderr
        s=json.loads(state.read_text()); assert all(t["status"]=="DONE" for t in s["tasks"].values()); assert s["worker"]["graph_status"]=="COMPLETE"
        bad=Path(td)/"bad.json"
        bad.write_text(json.dumps({"schema":"V233-plan/v1","tasks":{
            "bad":{"kind":"PYTHON_TEST","deps":[],"payload":{"script":"not-allowlisted.py"},"max_attempts":1},
            "downstream":{"kind":"NOOP_VERIFY","deps":["bad"],"payload":{},"max_attempts":1}}}),encoding="utf-8")
        bs_path=Path(td)/"bad-state.json"
        p=subprocess.run([sys.executable,"scripts/v233_evidence_task_graph.py","--state",str(bs_path),"--plan",str(bad),"--budget-seconds","10"],capture_output=True,text=True)
        assert p.returncode==0,p.stderr
        bs=json.loads(bs_path.read_text()); assert bs["tasks"]["bad"]["status"]=="FAILED"; assert bs["tasks"]["downstream"]["status"]=="BLOCKED"
    print("V233 evidence task graph tests: PASS")
if __name__=="__main__": main()
