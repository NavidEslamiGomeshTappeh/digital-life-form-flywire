# Reproducibility — Version 1.2.1

## Local checks

python -m ruff check .
python -m pytest -q
python -m dlf_flywire validate
python -m dlf_flywire audit
python -m dlf_flywire verify-sources
python -m build

## Exact morphology recovery

dlf-flywire recover --dataset 783 --output data/morphology

V1.0.1 reads the public FAFB v783 Neuroglancer skeleton endpoint directly. The
reader implements the official precomputed skeleton binary format: vertex count,
edge count, float32 vertex positions, uint32 edge pairs, and declared vertex
attributes. The resulting graph is deterministically oriented into SWC parent
relationships and structurally validated before the command reports PASS.

## Evidence

The committed files in evidence/ are the canonical Version 1 scientific record. The claim ledger declares the status of each important statement, while artifact_manifest.json binds critical files to immutable content identities. CI and the local audit command verify the resulting contract.

Historical external sources are referenced by immutable commits, Git blobs, dataset identifiers, and (for the two frozen cross-source receipts) the exact recorded GitHub Actions proof runs.

The Git history remains available for forensic reconstruction of earlier experiments, but the working tree contains only the consolidated product.
