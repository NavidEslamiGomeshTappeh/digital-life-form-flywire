#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, sys, tempfile
def main():
    with tempfile.TemporaryDirectory() as td:
        state=Path(td)/"state.json"
        cmd=[sys.executable,"scripts/v232_persistent_worker.py","--state",str(state),"--budget-seconds","10","--task","a|NOOP_VERIFY","--task","b|NOOP_VERIFY"]
        p=subprocess.run(cmd,capture_output=True,text=True); assert p.returncode==0,p.stderr
        s=json.loads(state.read_text()); assert s["tasks"]["a"]["status"]=="DONE"; assert s["tasks"]["b"]["status"]=="DONE"
        p=subprocess.run(cmd,capture_output=True,text=True); assert p.returncode==0,p.stderr
        s2=json.loads(state.read_text()); assert s2["tasks"]["a"]["attempts"]==1; assert any(x["event"]=="RUN_FINISHED" for x in s2["journal"])
    print("V232 persistent worker tests: PASS")
if __name__=="__main__": main()
