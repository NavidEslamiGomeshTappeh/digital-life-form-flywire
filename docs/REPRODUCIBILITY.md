# Reproducibility

## Local checks

python -m ruff check .
python -m pytest -q
python -m dlf_flywire validate
python -m build

## Exact morphology recovery

dlf-flywire recover --dataset 783 --output data/morphology

The command validates the returned source root ID before writing each SWC.

## Evidence

The committed files in evidence/ are the canonical V1 scientific record. CI verifies their structural invariants and the exact hashes of the four morphology files.

Historical external sources are referenced by immutable commits, Git blobs or dataset identifiers inside the evidence record.

The Git history remains available for forensic reconstruction of earlier experiments, but the working tree contains only the consolidated product.
