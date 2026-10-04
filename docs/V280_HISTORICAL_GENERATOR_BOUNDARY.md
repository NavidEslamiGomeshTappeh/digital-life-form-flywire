# V280 — Historical Generator Boundary

## Purpose

V280 establishes a hard temporal boundary for historical provenance of the published `Point_data.pkl`.

The question is not whether the later public preprocessing notebooks can reproduce the four V229 SWCs. V258 already establishes that algorithmic regression. The V280 question is narrower:

> Was the currently public PP1/PP3 preprocessing implementation already present in the study repository when the historical `Point_data.pkl` was first committed?

## Evidence

Pinned study repository:

`borstlab/T4_T5_Dendrite_Morphology_Paper`

### 1. Repository creation

Initial commit:

- SHA: `79cf52212935de6bddf996c9f46c0df89f5c5442`
- Time: 2025-12-09T19:26:04Z
- Message: `Initial commit`
- Files in the commit: `.gitignore`, `README.md`

The initial commit does not contain:

- `Notebooks/PP1_Fetch_flywire.ipynb`
- `Notebooks/PP3_Dendrite_extraction.ipynb`
- any published Point_data file.

### 2. First historical Point_data object

First Point_data commit:

- SHA: `cd17d34afd0d46a3c2947e83a1f0fdd835a9959a`
- Time: 2025-12-09T20:41:50Z
- Message: `A point value metrics data`
- Added path: `Data/Point_data.pkl`

A subsequent near-identical Point_data commit followed 29 seconds later:

- SHA: `fe9779d4ca425613eec44b19e961610d117e7232`
- Time: 2025-12-09T20:42:19Z
- Message: `Point value metrics data`

Neither commit contains the later PP1/PP3 preprocessing notebooks.

The first Point_data commit therefore predates the public PP1/PP3 implementation currently visible in the study repository.

### 3. Public preprocessing release

The public preprocessing notebooks were added much later in:

- SHA: `8700efd40bccfa3e74ac7c4df02da83a968b9b52`
- Time: 2026-08-10T17:49:32Z
- Message: `Paper submission update. Remove tracked Data artifacts and add preprocessing notebooks and revised analysis code.`

That commit introduced the currently visible preprocessing notebooks, including:

- `Notebooks/PP1_Fetch_flywire.ipynb`
- `Notebooks/PP3_Dendrite_extraction.ipynb`

The later PP1 notebook shows the public workflow explicitly:

`FlyWire mesh → navis skeletonize() → 100 nm resampling → SWC`

The later PP3 notebook shows:

`SWC/.nr forest → flag filtering → convert_forest_to_subtrees() → reduced dendrites → Point_data`

These are valuable reproducibility artifacts, but their 2026 publication date prevents them from being treated as proof of the exact December 2025 historical generator.

## Consequence

V280 closes one specific provenance loophole:

**The currently public preprocessing notebooks cannot be the complete historical source record for the original December 2025 Point_data solely on repository chronology, because those notebooks were committed approximately eight months after the first Point_data object.**

This does not prove that the historical generation code was different. It proves that the currently public repository does not preserve that original code at the time the historical Point_data entered Git.

## What remains open

The historical generator identity remains unresolved until one of the following is recovered:

1. an original pre-December-2025 SWC/mesh/.nr artifact;
2. the original private/local preprocessing code;
3. a preserved environment/toolchain snapshot used before the public 2026 release;
4. an independent source that pins the exact historical FlyWire/FAFB materialization and skeletonization behavior.

V280 therefore classifies the result as:

**PROVEN temporal boundary / UNRESOLVED historical generator identity**

No biological identity is inferred from chronology alone.

## Reproducibility

Run:

`python scripts/v280_historical_generator_boundary.py`

The script fetches the pinned immutable commits from the study repository and verifies the presence/absence of the relevant paths. It writes:

`v280_results/V280_historical_generator_boundary.json`

The companion GitHub Actions workflow repeats the same test on every relevant repository change and on manual dispatch.
