from __future__ import annotations
import argparse

from .constants import ROOTS

def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="dlf-flywire")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    r = sub.add_parser("recover")
    r.add_argument("--dataset", type=int, default=783)
    r.add_argument("--output", default="data/morphology")
    r.add_argument("--root", action="append", choices=list(ROOTS))
    a = p.parse_args(argv)

    if a.command == "validate":
        from .validation import main as validate_main
        return validate_main()

    import sys
    from .recovery import main as recovery_main
    sys.argv = ["dlf-flywire-recover", "--dataset", str(a.dataset), "--output", a.output]
    for root in a.root or []:
        sys.argv.extend(["--root", root])
    return recovery_main()
