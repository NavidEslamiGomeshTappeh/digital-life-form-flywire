#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os
from pathlib import Path
import psycopg
ROOT=Path(__file__).resolve().parents[1]
def sha256_bytes(data: bytes)->str: return hashlib.sha256(data).hexdigest()
def load_json(path: Path)->dict: return json.loads(path.read_text(encoding="utf-8"))
def evidence_from_repo()->list[dict]:
    items=[]
    for rel, claim in [
        ("v229_results/V229_recovery_report.json","V229-ROOT-EXACT"),
        ("v230_results/V230_validation.json","V230-STRUCTURE"),
        ("v231_results/V231_structural_snapshot.json","V231-STRUCTURAL-FINGERPRINT"),
    ]:
        p=ROOT/rel
        if p.exists():
            raw=p.read_bytes()
            items.append({"claim_id":claim,"evidence_kind":"repository_artifact","status":"PASS","source":"git","source_ref":rel,"digest_sha256":sha256_bytes(raw),"payload":{"artifact":load_json(p)}})
    p=ROOT/"v230_results/V230_validation.json"
    if p.exists():
        raw=p.read_bytes()
        items.append({"claim_id":"V230-BIOLOGICAL-PROVENANCE","evidence_kind":"provenance_boundary","status":"UNKNOWN","source":"repository_artifact","source_ref":str(p.relative_to(ROOT)),"digest_sha256":sha256_bytes(raw),"payload":{"reason":"Repository audit explicitly states biological provenance is unverified."}})
    return items
def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--database-url",default=os.environ.get("NEON_DATABASE_URL"))
    ap.add_argument("--version",default="V238")
    args=ap.parse_args()
    if not args.database_url: raise SystemExit("NEON_DATABASE_URL is required")
    evidence=evidence_from_repo()
    plan_sha=sha256_bytes(json.dumps([{"claim_id":x["claim_id"],"status":x["status"],"digest":x["digest_sha256"]} for x in evidence],sort_keys=True,separators=(",",":")).encode())
    with psycopg.connect(args.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO research_runs(version,status,plan_sha256,metadata) VALUES (%s,%s,%s,%s::jsonb) RETURNING run_id",(args.version,"RUNNING",plan_sha,json.dumps({"bridge":"v238","evidence_count":len(evidence)})))
            run_id=cur.fetchone()[0]
            for x in evidence:
                cur.execute("INSERT INTO research_claims(claim_id,description,evidence_level,current_status,metadata) VALUES (%s,%s,%s,%s,%s::jsonb) ON CONFLICT (claim_id) DO UPDATE SET current_status=EXCLUDED.current_status,evidence_level=EXCLUDED.evidence_level,updated_at=now(),metadata=EXCLUDED.metadata",(x["claim_id"],"Persisted repository evidence claim","OBSERVED",x["status"],json.dumps({"source_ref":x["source_ref"]})))
                cur.execute("INSERT INTO evidence_records(run_id,claim_id,evidence_kind,status,source,source_ref,digest_sha256,payload) VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb)",(run_id,x["claim_id"],x["evidence_kind"],x["status"],x["source"],x["source_ref"],x["digest_sha256"],json.dumps(x["payload"])))
            final_status="INCOMPLETE" if any(x["status"]=="UNKNOWN" for x in evidence) else "PASS"
            cur.execute("UPDATE research_runs SET status=%s,finished_at=now() WHERE run_id=%s",(final_status,run_id))
        conn.commit()
    print(json.dumps({"version":args.version,"run_id":str(run_id),"status":final_status,"evidence_count":len(evidence),"plan_sha256":plan_sha},sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
