#!/usr/bin/env python3
import json
from pathlib import Path

p=Path("v236_results/V236_live_service_evidence.json")
d=json.loads(p.read_text(encoding="utf-8"))
assert d["schema"]=="V236-live-service-evidence/v1"
assert d["services"]["tinyfish"]["status"]=="PASS"
assert d["services"]["wolfram"]["status"]=="PASS"
assert abs(d["services"]["wolfram"]["outputs"]["edges_per_vertex"]-26.9328)<1e-4
assert abs(d["services"]["wolfram"]["outputs"]["twice_edges_per_vertex"]-53.8657)<1e-4
print("V236_LIVE_SERVICE_EVIDENCE_PASS")
