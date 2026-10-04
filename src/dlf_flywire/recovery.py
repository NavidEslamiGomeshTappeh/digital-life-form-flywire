from __future__ import annotations
import argparse
from pathlib import Path
from .constants import ROOTS

def main() -> int:
    p=argparse.ArgumentParser(description="Recover exact FlyWire FAFB v783 skeletons.")
    p.add_argument("--dataset",type=int,default=783)
    p.add_argument("--output",type=Path,default=Path("data/morphology"))
    p.add_argument("--root",action="append",choices=list(ROOTS))
    a=p.parse_args()
    if a.dataset!=783:
        raise SystemExit("Version 1 validates the FAFB v783 recovery path only.")
    try:
        from fafbseg import flywire
        import navis
    except ImportError as exc:
        raise SystemExit("Install package dependencies before recovery.") from exc
    a.output.mkdir(parents=True,exist_ok=True)
    for name in a.root or list(ROOTS):
        rid=ROOTS[name]
        n=flywire.get_skeletons(rid,dataset=783,progress=False)
        if isinstance(n,navis.NeuronList):
            if len(n)!=1: raise SystemExit(f"{name}: endpoint returned {len(n)} neurons")
            n=n[0]
        source_id=int(getattr(n,"id"))
        if source_id!=rid:
            raise SystemExit(f"{name}: source root mismatch: requested {rid}, got {source_id}")
        out=a.output/f"{name}.swc"
        navis.write_swc(n,out)
        print(f"PASS {name} root={rid} output={out}")
    return 0
