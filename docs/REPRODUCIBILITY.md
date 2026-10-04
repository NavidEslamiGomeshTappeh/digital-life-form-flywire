# Reproducibility

## Local checks

python -m ruff check .
python -m pytest -q
python -m dlf_flywire validate
python -m build

## Exact morphology recovery

dlf-flywire recover --dataset 783 --output data/morphology

V1.0.1 reads the public FAFB v783 Neuroglancer skeleton endpoint directly. The
reader implements the official precomputed skeleton binary format: vertex count,
edge count, float32 vertex positions, uint32 edge pairs, and declared vertex
attributes. The resulting graph is deterministically oriented into SWC parent
relationships and structurally validated before the command reports PASS.

## Evidence

The committed files in evidence/ are the canonical V1 scientific record. CI verifies their structural invariants and the exact hashes of the four morphology files.

Historical external sources are referenced by immutable commits, Git blobs or dataset identifiers inside the evidence record.

The Git history remains available for forensic reconstruction of earlier experiments, but the working tree contains only the consolidated product.
