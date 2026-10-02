#!/usr/bin/env python3
"""Fail-closed validator for the V235 external-service capability ledger."""
from __future__ import annotations
import json
from pathlib import Path

LEDGER = Path("v235_results/V235_service_capability_ledger.json")
ALLOWED = {"VERIFIED", "CONNECTED_BUT_NO_PROJECT_VISIBLE", "CONNECTED_TOOL_UNSCOPED", "UNKNOWN", "INCOMPLETE"}

def main() -> int:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    if data.get("schema") != "V235-service-capability-ledger/v1":
        raise SystemExit("invalid ledger schema")
    services = data.get("services")
    if not isinstance(services, dict) or not services:
        raise SystemExit("empty service ledger")
    for name, item in services.items():
        status = item.get("status")
        if status not in ALLOWED:
            raise SystemExit(f"{name}: unsupported status {status!r}")
        if not item.get("evidence"):
            raise SystemExit(f"{name}: missing evidence")
        if status != "VERIFIED" and item.get("fail_closed") is not True and name in {"supabase", "neon"}:
            raise SystemExit(f"{name}: unavailable access must be fail-closed")
    print("V235_SERVICE_LEDGER_PASS")
    for name, item in services.items():
        print(f"{name}: {item['status']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
