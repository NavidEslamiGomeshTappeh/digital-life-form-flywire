#!/usr/bin/env python3
"""Resumable worker for long-running biological-data research."""
from __future__ import annotations
import argparse, hashlib, json, os, socket, time
from datetime import datetime, timezone
from pathlib import Path
SCHEMA="V232-worker/v1"
def now(): return datetime.now(timezone.utc).isoformat()
def digest(obj): return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def load(path):
    if not path.exists(): return {"schema":SCHEMA,"version":1,"tasks":{},"journal":[]}
    return json.loads(path.read_text(encoding="utf-8"))
def atomic_write(path,data):
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8"); os.replace(tmp,path)
def ensure_task(state,task_id,kind,payload):
    state["tasks"].setdefault(task_id,{"kind":kind,"payload":payload,"status":"PENDING","attempts":0,"created_at":now(),"updated_at":now()})
def journal(state,event,**data):
    state["journal"].append({"time":now(),"event":event,**data})
    if len(state["journal"])>2000: state["journal"]=state["journal"][-2000:]
def execute(task):
    if task["kind"]=="NOOP_VERIFY":
        return {"result":"orchestration-verified","payload_digest":digest(task["payload"])}
    raise RuntimeError(f"unregistered task kind: {task['kind']}")
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--state",default="v232_state/worker_state.json"); ap.add_argument("--budget-seconds",type=int,default=300); ap.add_argument("--task",action="append",default=[]); ap.add_argument("--force",action="store_true"); args=ap.parse_args()
    if args.budget_seconds<5: raise SystemExit("--budget-seconds must be >= 5")
    path=Path(args.state); path.parent.mkdir(parents=True,exist_ok=True); state=load(path); state["schema"]=SCHEMA
    state["worker"]={"host":socket.gethostname(),"pid":os.getpid(),"started_at":now(),"budget_seconds":args.budget_seconds}
    for spec in args.task:
        parts=spec.split("|",1)
        if len(parts)!=2: raise SystemExit("task must be ID|KIND")
        ensure_task(state,parts[0],parts[1],{})
    atomic_write(path,state); deadline=time.monotonic()+args.budget_seconds; journal(state,"RUN_STARTED",budget_seconds=args.budget_seconds); atomic_write(path,state); executed=0
    for task_id,task in list(state["tasks"].items()):
        if time.monotonic()>=deadline: journal(state,"BUDGET_EXHAUSTED",executed=executed); break
        if task["status"]=="DONE" and not args.force: continue
        if task["status"]=="RUNNING": task["status"]="PENDING"
        task["status"]="RUNNING"; task["attempts"]+=1; task["updated_at"]=now(); journal(state,"TASK_STARTED",task_id=task_id,attempt=task["attempts"]); atomic_write(path,state)
        try:
            task["result"]=execute(task); task["status"]="DONE"; task.pop("error",None); task["updated_at"]=now(); journal(state,"TASK_DONE",task_id=task_id)
        except Exception as exc:
            task["status"]="FAILED"; task["error"]=f"{type(exc).__name__}: {exc}"; task["updated_at"]=now(); journal(state,"TASK_FAILED",task_id=task_id,error=task["error"])
        executed+=1; atomic_write(path,state)
    state["worker"]["finished_at"]=now(); state["worker"]["executed_this_run"]=executed; state["worker"]["state_digest"]=digest({"tasks":state["tasks"],"journal_tail":state["journal"][-20:]}); journal(state,"RUN_FINISHED",executed=executed); atomic_write(path,state)
    print(json.dumps({"schema":SCHEMA,"executed":executed,"state":str(path),"digest":state["worker"]["state_digest"]},indent=2))
if __name__=="__main__": main()
