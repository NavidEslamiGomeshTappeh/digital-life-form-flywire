from __future__ import annotations

import argparse
from pathlib import Path

from .constants import ROOTS


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recover exact FlyWire FAFB v783 skeletons."
    )
    parser.add_argument("--dataset", type=int, default=783)
    parser.add_argument("--output", type=Path, default=Path("data/morphology"))
    parser.add_argument("--root", action="append", choices=list(ROOTS))
    args = parser.parse_args()

    if args.dataset != 783:
        raise SystemExit("Version 1 validates the FAFB v783 recovery path only.")

    try:
        import navis
        from fafbseg import flywire
    except ImportError as exc:
        raise SystemExit("Install package dependencies before recovery.") from exc

    args.output.mkdir(parents=True, exist_ok=True)
    for name in args.root or list(ROOTS):
        root_id = ROOTS[name]
        neurons = flywire.get_skeletons(root_id, dataset=783, progress=False)
        if isinstance(neurons, navis.NeuronList):
            if len(neurons) != 1:
                raise SystemExit(f"{name}: endpoint returned {len(neurons)} neurons")
            neuron = neurons[0]

        source_id = int(neuron.id)
        if source_id != root_id:
            raise SystemExit(
                f"{name}: source root mismatch: requested {root_id}, got {source_id}"
            )

        output = args.output / f"{name}.swc"
        navis.write_swc(neuron, output)
        print(f"PASS {name} root={root_id} output={output}")

    return 0
