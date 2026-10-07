# PROJECT CONTEXT — Digital Life Form / FlyWire

> **Canonical continuation file.**
>
> This file is the durable working memory for future ChatGPT/agent sessions.
> When the chat changes, **read this file first** before making scientific, architectural,
> provenance, security, or repository decisions.
>
> Last consolidated: **2026-10-07**
> Current product line: **Version 1.x only** (no V-numbered replacement series)

---

## 1. Project identity

Repository:

- https://github.com/NavidEslamiGomeshTappeh/digital-life-form-flywire
- Default branch: `main`
- Owner: `NavidEslamiGomeshTappeh`

The project is **not** the old abandoned V300–V510 brain-building direction.

The current project is a **provenance-first research-engineering toolkit for exact FlyWire/FAFB connectome evidence**.

The product idea is:

`source dataset -> exact release/materialization -> raw artifact -> deterministic transformation -> derived artifact -> independent validation -> claim status -> evidence bundle`

The project should eventually become an expandable verification/provenance layer that can operate beyond the initial four-neuron case and, where justified, across FlyWire and other connectome datasets.

### Core positioning

Do **not** position the project as:

- another generic FlyWire downloader;
- another whole-brain LIF simulator;
- another visualization demo;
- "the first project to use provenance" in FlyWire.

Position it as:

> **A claim-level, evidence-first provenance and verification system for connectomics: it traces scientific results from exact source data through deterministic derivations to independently checked artifacts, while explicitly separating observation, computation, corroboration, inference, and unresolved claims.**

A safer uniqueness statement is:

> "I did not find a comparable public example at the same end-to-end granularity for this exact class of artifact."

Never use an absolute "nobody else does provenance" claim.

---

## 2. Non-negotiable operating rules

These rules apply to every future session.

### Scientific honesty

1. Exact identifiers beat approximations.
2. A claim is not "proven" merely because code runs.
3. Separate:
   - **SOURCE OBSERVATION**
   - **DETERMINISTIC COMPUTATION**
   - **INDEPENDENT CORROBORATION**
   - **BIOLOGICAL INFERENCE**
   - **UNRESOLVED**
4. Never convert geometric proximity into biological compartment truth.
5. Never claim recovery of an unpublished/historical generator unless the actual implementation is found and demonstrated.
6. Never call synthetic test data "real scientific data".
7. Never call a demo/mocked path a scientific result.
8. Negative results and unresolved boundaries are first-class outputs.
9. Prefer fail-closed validation over silent approximation.
10. Any "big" claim must be backed by an implementation, test, and inspectable evidence.

### Engineering

1. No V281/V282-style version explosion.
2. Keep one unified expandable product.
3. Use semantic versions only when the public product changes materially: 1.1.0, 1.2.0, 2.0.0, etc.
4. Do not create busywork merely to generate commits.
5. Changes should be testable and traceable.
6. Security and reproducibility are part of the product, not decorations.
7. Preserve historical Git history; clean working tree names do not erase history.
8. Do not silently replace an unresolved historical artifact with a new approximation.

### Continuation protocol

At the start of a new project chat:

1. Read this file.
2. Read `README.md`.
3. Check current `main` commit/version.
4. Check open issues/PRs and recent CI/security state.
5. Continue from existing evidence; do not reconstruct the project from memory or invent missing steps.

---

## 2.5 Current 2026-10-07 maintenance state

- Main remains on the unified Version 1.x line; current released metadata remains **1.7.1**.
- `recovery.py` now rejects self-edges, invalid endpoints, disconnected skeletons, cycles, and non-tree edge counts before graph orientation. Regression coverage exists for invalid, disconnected, and cyclic skeleton inputs.
- `scripts/Run-Camera-FlyVis.ps1` now uses explicit venv entrypoints and checks native `pip`/`git`/FlyVis/`dlf-flywire` command exit codes so a failed command cannot silently lead to a later partial run.
- `tests/test_camera_launcher.py` statically guards the Windows launcher contract and its fail-closed native-command handling.
- GitHub Actions evidence at the latest completed point: **CI PASS** and **Security PASS** for commit `d03e3230a74ba02e2052b11f16c854d721d8ca6a`.
- The physical camera launcher remains a local-machine execution boundary; static CI coverage is not a claim that a physical camera was exercised by GitHub Actions.
- A bounded `NetworkCameraSource` now accepts explicit `rtsp://` or `rtsps://` endpoints through OpenCV, converts frames into the existing `VisionFrame` contract, redacts credentials/query secrets from provenance locators, and is exposed through `capture-network-camera`.
- A read-only `probe-camera-ptz` boundary now uses pinned `onvif-python==0.4.4` to inspect ONVIF PTZ profile/configuration tokens, current position/status, and continuous velocity ranges. It intentionally issues **no movement command**.
- A read-only `discover-network-cameras` boundary now uses ONVIF WS-Discovery to locate cameras on the local LAN without requiring a known IP address. Discovered host/port, XAddrs, types/scopes, and services are returned as a provenance receipt; no PTZ or configuration commands are issued.
- `NetworkCameraSource` now supports direct RTSP input and `resolve_rtsp_stream()` can obtain a live RTSP URI through the current `onvif-python==0.4.4` Media `GetStreamUri` API, injecting credentials only into the in-memory connection URI and recording only a redacted locator.
- `camera-flyvis` accepts either a direct RTSP URL or ONVIF host/credential environment variables and can therefore run the real network-camera stream through the existing BoxEye → pinned FlyVis pipeline.
- `Run-Network-Camera-FlyVis.ps1` and `.bat` provide a double-click Windows entry point that prepares `[vision,ptz]`, performs ONVIF discovery, and runs the ONVIF-to-RTSP-to-FlyVis path when the required environment variables are present.

## 3. The current scientific anchor case

The initial verified case consists of **four exact FAFB v783 neurons**:

| Cell | Root ID | VFB |
|---|---:|---|
| T4a | 720575940632008007 | VFB_fw077172 |
| T4c | 720575940616224414 | VFB_fw091869 |
| T5a | 720575940625571465 | VFB_fw056211 |
| T5c | 720575940617782941 | VFB_fw077474 |

Verified result set:

- **649 individual synapse-coordinate rows**
- **75 directed neuron pairs**
- exact **649/649** coordinate reproduction against the official Codex FAFB v783 individual-synapse product
- exact **75/75** pair-count correspondence against the official Codex FAFB v783 connections product
- independent frozen **Zenodo FAFB v783** corroboration of the midpoint mappings
- four morphology SWCs retained as project evidence
- published dendrite provenance confirmed
- published subtree-selection algorithm independently reproduced
- historical `Point_data.pkl` Git provenance reconstructed to the exact blob/SHA-256 level
- historical generator temporal boundary identified, but the original generator remains unresolved
- connectome structural snapshot: **138,584 vertices / 3,732,460 directed edges**
- compartment-boundary analysis: **331 rows anchored at the presynaptic endpoint / 318 at the postsynaptic endpoint**

These numbers are the current verified anchor. Do not silently update them when another FlyWire snapshot/version is discussed.

---

## 4. Morphology evidence

Four SWCs:

| Cell | Nodes | SHA-256 |
|---|---:|---|
| T4a | 880 | `d17623da9812d0f2ef53ab6aed4a9d89a2c2820d34aa0294af2ba434b6107c2a` |
| T4c | 898 | `7d9cc29226e092c233f35cfcf70f75ac137b8c9f8744a1ba319264f96da3857a` |
| T5a | 601 | `6d4d2a33cfea8525449b7a1508c6e6c2d9550034aac3774e6b2d64c4e76bae5c` |
| T5c | 577 | `83b287e914522b0b382e3e46d39ced36494ff257d835cac11d7f4243ae1d7745` |

Published dendrite provenance:

- all four roots occur exactly once in the pinned published `Neuron_ids.csv`
- all four have `Dendrite_used=True`

Published subtree-selection reproduction:

- T4a = 292 selected branch nodes
- T4c = 358
- T5a = 343
- T5c = 323

Known limitation:

- byte-for-byte identity between project SWCs and unpublished/internal study morphology is **not established**.

Do not turn the SWC result into a claim about the exact historical internal morphology file unless independently proven.

---

## 5. Historical Point_data provenance

Historical artifact:

- Repository: `borstlab/T4_T5_Dendrite_Morphology_Paper`
- Source commit: `cd17d34afd0d46a3c2947e83a1f0fdd835a9959a`
- Git blob: `b85caf49f45677f2075f7b5f2c8830141cd96d02`
- SHA-256: `76b7d6a1c44ad6b2ca730feff88174c71327e095cce45d8a47a0d998f77df58f`

Historical timeline:

- initial repository commit: `79cf52212935de6bddf996c9f46c0df89f5c5442` — 2025-12-09 19:26:04Z
- first `Point_data` commit: `cd17d34afd0d46a3c2947e83a1f0fdd835a9959a` — 2025-12-09 20:41:50Z
- public preprocessing commit: `8700efd40bccfa3e74ac7c4df02da83a968b9b52` — 2026-08-10 17:49:32Z
- public NeuRosetta Forest commit: `2f4e52c8d0ac4f284b9a15e5d147f6a130998495` — 2026-01-26 14:20:00Z

Conclusion:

> The currently public preprocessing is **not** a complete preserved historical generator record for the December 2025 `Point_data` artifact.

The original historical generator remains **UNRESOLVED**.

### 2026-10-04 release/internals audit
### 2026-10-04 legacy-toolchain finding

### 2026-10-04 earliest-public-release finding

### 2026-10-04 morphology crosscheck finding

The four project SWCs were re-run through the same published/legacy subtree root-selection logic and compared against the four historical Point_data morphology anchors. The selected roots remain 292/358/343/323, but the downstream morphology metrics do not exactly match Point_data: T4a 212 vs 222 segments, T4c 211 vs 205, T5a 180 vs 134, T5c 152 vs 152; cable lengths also differ for all four. T5c is the only exact segment-count match, while leaf/branch counts still differ. This is stronger evidence of a morphology-materialization or manual-correction boundary than of an algorithm-selection boundary.

The public legacy Neurosetta SWC reader was also inspected directly: it reads x/y/z into graph coordinates without an alignment or scaling step. Therefore the large Point_data coordinate-frame discrepancy cannot be attributed to an automatic legacy SWC-import transform.

A global GitHub search for the exact preprocessing path, PP3 call, and related unique code fragments found only the public Borstlab paper repository, not an independent fork/copy containing the missing producer.


A January 16, 2026 Zenodo software release was located:

- Zenodo record 18269709, version Submission_release, archive MD5 6ce666c93c0d907e228442528796bc0e, about 99 MB.
- Its Data/Point_data.pkl is the exact historical Git blob b85caf49f45677f2075f7b5f2c8830141cd96d02, the same artifact first committed on 2025-12-09.
- The release contains the downstream analysis notebooks, source modules, Neuron_ids.csv, and conda-environment.yml.
- It does not contain PP1_Fetch_flywire, PP2_nr_conversion, PP3_Dendrite_extraction, PP4_Global_allignment, or PP5_Mesh_generation.
- The release is 18 public Git commits ahead of the Point_data commit on the Submission_release branch, so it preserves a dated downstream snapshot without exposing the upstream morphology producer.
- Zenodo also records a Software Heritage snapshot for this release, providing a second immutable archival route to the same historical release.

Interpretation: this materially strengthens the historical endpoint for the Point_data artifact, but the upstream Reduced_dendrites/.nr generation stage is still missing from the located public release. The exact December producer remains UNRESOLVED.

A GitHub Actions binary/decode audit now reselected all four anchors by exact FAFB v783 Root ID, requiring one unique row per anchor in both snapshots. Run 37481554712 completed successfully. The historical pickle is Protocol 5 and contains 46,624 decoded `jaxlib._jax.ArrayImpl` cells across the eight PCA/angle/vector metric columns (exactly 5,828 rows × 8 columns), plus 11,656 string cells. This proves a concrete JAX serialization/runtime boundary in the historical artifact, but it does not identify the code path that produced those arrays.

The snapshot ledger was corrected to preserve the full 64-bit Root IDs without numeric coercion. The four verified IDs are 720575940632008007, 720575940616224414, 720575940625571465, and 720575940617782941. The exact-ID receipt is stored in `evidence/point_data_pickle_decode_receipt.json`.

The previous nearest-coordinate row-selection method is now explicitly superseded for this boundary. Coordinate proximity remains a diagnostic only; anchor identity in the evidence ledger is ID-exact.


A separate public repository, NikDrummond/Neurosetta_legacy_v0.0.1, provides a historically plausible but unproven predecessor path for the missing morphology stage:

- Subtree extraction and dendrite-root selection existed by commit 94ff9e5a956d5a91c40bb386f33e3dfa60896987 (2025-04-18).
- A July 29, 2025 fix (9816dad67180ebf5937ae05316ae14d1f190aae4) explicitly changed optimal_partition_root() to score a simplified graph and map the selected simplified root coordinate back to the full neuron with nearest_vertex().
- Coordinate transformation/scaling functionality predates the Point_data artifact: commit e0de7d65c2618f06edf4ec9f3e630bab5f524399 (2024-10-21) added transforming/scaling functions, and the current legacy transformations.py contains align_neuron(), snap_to_axis(), and coordinate_scale().
- The legacy repository's latest public commit before the December 2025 Point_data artifact is 25c911a28030deb5204eb7ab5a18ff4643363d96 on 2025-07-31.

This is **contextual evidence only**. No inspected artifact links a specific legacy commit or parameter set to the December 2025 Point_data execution. The legacy path is therefore technically plausible but remains UNRESOLVED as historical provenance.


Additional direct reconstruction established:

- The December 9, 2025 Point_data commit cd17d34afd0d46a3c2947e83a1f0fdd835a9959a contains only Data/Point_data.pkl; the contemporaneous ANOVA_analysis.ipynb consumes that artifact but does not expose its producer.
- The current public paper repository preprocessing notebooks PP1–PP5 and Metrics1_Point_data are published later, in the 2026-08-10 update.
- The public Zenodo data archive contains point_data.pkl, vertex_data.pkl, edge_data.pkl, bifurcation_data.pkl, deviation_data.pkl, contour data, columns, and readme; it does not list Reduced_dendrites or .nr intermediate morphology trees.
- The public NeuRosetta import_swc path declares units without rescaling geometry; convert_units performs explicit coordinate rescaling. align_forest performs centering/PCA rotation and does not introduce a scale factor.
- The deterministic published-subtree root-node comparison was rerun on all four project SWCs and still fails by hundreds of micrometres against the historical Point_data roots.
- A fitted four-point similarity transform gives about 9.6 µm RMS residual with scale about 2.7055, but this is INFERENCE_ONLY and is not accepted as historical provenance.


New chronology finding (2026-10-04):
- The historical `Point_data.pkl` first appeared in the source repository at commit `cd17d34afd0d46a3c2947e83a1f0fdd835a9959a` on 2025-12-09 20:41:50+01:00.
- The public `NikDrummond/NeuRosetta` repository itself begins earlier (2025-10-21), so repository existence alone is not evidence that the December pipeline used the public implementation.
- In that public repository, the documented Forest/parallel SWC IO used by the later paper notebooks first appears at `2f4e52c8d0ac4f284b9a15e5d147f6a130998495` on 2026-01-26; explicit current-repository subtree/reduction work appears later in April 2026.
- A separate `NikDrummond/Neurosetta_legacy_v0.0.1` repository contains a subtree implementation by commit `94ff9e5a956d5a91c40bb386f33e3dfa60896987` dated 2025-04-18, plus earlier `.nr` support. Therefore a private/local or legacy NeuRosetta-based route before December 2025 cannot be excluded.
- The current public paper preprocessing notebooks (`PP1`–`PP5`) were added in the 2026-08-10 repository update `8700efd40bccfa3e74ac7c4df02da83a968b9b52`, after the historical artifact already existed.
- Full public Git-DAG reconstruction adds an important boundary: the paper repository started at 2025-12-09T19:26:04Z; `Notebooks/ANOVA_analysis.ipynb` was added at 19:40:07Z and already consumed `/home/nik/Desktop/Software/T45_Morpho_data/Data/Pickled_data/Point_data.pkl`; `Data/Point_data.pkl` was then added independently in commits `cd17d34afd0d46a3c2947e83a1f0fdd835a9959a` and `fe9779d4ca425613eec44b19e961610d117e7232`, both with the same parent, same tree, and exact same blob `b85caf49f45677f2075f7b5f2c8830141cd96d02`, followed by merge commit `8a38537f55371de369f80c50778915afb5d954b4`. The public `Data/Neuron_ids.csv` appeared only on 2025-12-16. Therefore the exposed December repository history demonstrates an **artifact-ingest boundary**, not a producer implementation. The missing generator remains outside the exposed public history or in a private/local environment.
- The January 2026 Zenodo `Submission_release` archive independently preserves `Point_data.pkl` and downstream analysis artifacts but omits PP1–PP5 preprocessing notebooks and `Reduced_dendrites/`. This is an archived-release content boundary, not proof that the omitted producer never existed.
- V230-to-Point_data linkage is now explicitly classified as an anchor-ID bridge only: the 649 canonical synapse-coordinate rows contain 62 endpoint root IDs and 75 directed neuron pairs, and all four Point_data anchors participate in those rows. There is no row-level key connecting a synapse record to a specific historical morphology row, reduced-tree artifact, manual-edit record, or Point_data generation run.
- Software-family lineage is now separately tracked: `NikDrummond/Neurosetta_old` begins in 2023 with simplification and rotation code; `NikDrummond/Neurosetta_legacy_v0.0.1` contains transformation/scaling code by 2024-10-21, subtree logic by 2025-04-18, and the simplified-root mapping fix by 2025-07-29. The public `NikDrummond/NeuRosetta` GUI implementation enters its public history only in April 2026, with a commit message referring to an older GUI. This establishes plausible pre-artifact software-family context, not exact December producer provenance.
- The runtime evidence has its own temporal boundary: the first public `conda-environment.yml` appeared on 2026-01-16 as `T45_paper` and does not declare NeuRosetta, while the December 2025 ANOVA notebook records a `neurosetta` kernel. Therefore the later release environment cannot identify the exact December NeuRosetta installation or revision.
- The published 2026 paper provides two explicit morphology-review boundaries: soma-root correctness is manually verified/corrected before automated subtree selection, and a second manual review verifies the complete dendritic subtree and may correct individual routing/skeletonization errors. Global population alignment and individual PCA/scaling are separate geometry operations. Thus the project's successful reproduction of the automated root-selection algorithm cannot establish final morphology identity; the missing historical per-neuron manual edits and any exact December geometry operations remain **UNRESOLVED**.
- Conclusion: the public record now narrows the provenance problem but does not recover the exact December 2025 generator, exact software commit, exact morphology materialization, or exact execution environment. The generator remains **UNRESOLVED**.

---

## 6. The most important scientific boundary

For a synapse coordinate, there are multiple distinct facts:

1. where the source data places the synaptic coordinate;
2. how a midpoint/coordinate transform is deterministically calculated;
3. which endpoint/root/SWC it is near;
4. whether independent public artifacts reproduce the same result;
5. what biological compartment that coordinate actually belongs to.

The first four can be evidence-backed.

The fifth may remain unresolved.

**Geometry is evidence about geometry. It is not automatically biological compartment truth.**

This distinction must remain visible in future README/docs/results.

---

## 7. Security state and lesson

Version 1.0.1 was hardened after security review found:

- `PYSEC-2026-2447 / CVE-2025-69872` affecting `diskcache`
- vulnerable dependency chain through `fafbseg==3.2.2`

Mitigation implemented:

- core runtime dependencies changed to `[]`
- obsolete `requirements.txt` removed
- morphology recovery replaced with a direct Python standard-library decoder for the published Neuroglancer FAFB v783 skeleton format
- GitHub Actions pinned to immutable full commit SHAs
- security documentation added
- tests added for malformed/invalid decoder cases
- CI regression test rejects unpinned workflow actions

Main V1.0.1 CI previously passed:

- lint
- compile
- tests
- canonical validation
- distribution build
- wheel install smoke

Security workflow previously had:

- Scorecard success
- CodeQL running at last detailed inspection
- Dependency Review blocked by the GitHub Dependency Graph platform setting

Platform security items tracked in **Issue #16**:

- protect `main`
- require relevant CI/security status checks
- enable Dependency Graph
- verify Dependabot alerts/security updates
- verify Secret Scanning / Push Protection
- repository description/topics
- optional GitHub Project

Connector limitation already known:

- GitHub connector did not expose branch-ref deletion or release/tag creation, so old V-numbered branch refs may remain even after V1 working-tree cleanup.
- No `v1.0.0` GitHub Release/tag was created through the connector.

Never claim those platform items are complete until directly verified.

---

# 8. FlyWire ecosystem research — the important conclusions

The ecosystem has moved far beyond simple data access.

A useful map:

### A. Data / infrastructure

- FlyWire / Codex / CAVE
- `flywire_annotations`
- `CAVEclient`
- `FlyConnectome`

Lesson: exact versioning, annotation releases, and public data access already exist. Our differentiation must be above raw access.

### B. Morphology / neuroanatomy

- `navis`
- `fafbseg`

Lesson: loading/querying skeletons, meshes, annotations, and coordinates is already mature. We should integrate with that ecosystem rather than reimplement it unnecessarily.

### C. Network analysis / connectome computation

- `flywire-network-analysis`
- `cocoa`
- `connectome_interpreter`

Lesson: graph analysis is already broad and scientifically deep. "We analyze the FlyWire graph" is not distinctive enough.

### D. Whole-brain simulation

- `eonsystemspbc/fly-brain`
- Shiu et al. model derivatives
- `snedea/flybrain`
- `mikewolak/flysim`
- `vshapenko/flypoke`
- `suifei/flywire-fly-lab`
- other 2026 FlyWire simulation projects

Lesson: whole-brain simulation is now crowded.

### E. Embodied brain/body systems

- `NeLy-EPFL/flygym`
- `TuragaLab/flybody`
- `flywire-fly-lab`
- `Recluse/FLY-lab`
- 2026 FlyWire + NeuroMechFly hybrids

Lesson: connecting a brain to a body and measuring behavior is also increasingly populated.

### F. Browser / game / robotics demonstrations

- `snedea/flybrain`
- `FlyDrones`
- `Open-Fly`
- `fly-api`
- `flypoke`

Lesson: UX, browser demos, one-interaction experiments, and clear visual stories can produce attention.

### G. Reproducibility / scientific auditing

Important examples show that pieces of our intended philosophy already exist:

- `flywire-nt-consistency`: anomaly -> candidate -> literature validation -> corrected/accepted/unresolved status
- `flywire-fly-lab`: reproduction ledger with reproduced/partial/negative/not-done/blocked
- `FLY-lab`: identical body/control comparisons and controls catching real errors
- `flyconnectome/natmcp`: provenance fields such as source/signature/dataset/package/find_doc and on-disk manifests with Git SHA/package version
- `flyconnectome/aedes`: source/build provenance in a focused pipeline
- `flyconnectome/bigclust2`: explicit reproducibility rules around commit/seed/currentness

Conclusion:

> Provenance and reproducibility are not new ideas in FlyWire.
> The opportunity is to make them **cross-artifact, claim-level, end-to-end, machine-checkable, and independently validated** in one coherent product.

---

## 9. Current competitive/attention lessons

A project can have major scientific value and few GitHub stars.

GitHub attention tends to increase when a project has:

- one-sentence understandable story;
- immediate demo or interaction;
- broader application;
- visible numerical benchmark;
- reproducible command;
- compelling visualization;
- clear honesty about what is engineered vs biological.

Scientific trust tends to increase when a project has:

- exact dataset/version;
- controls or null models;
- fixed protocol;
- independent validation;
- negative results;
- claim-level reproducibility;
- hashes and immutable artifacts.

Therefore our strategy should be:

> **Rigor as the core, usability as the multiplier.**

Not:

> "Make a flashy demo and hope the scientific provenance is enough."

---

## 10. New 2026 findings that change our strategy

Recent public projects show several capabilities becoming commonplace:

1. **Whole-brain FlyWire LIF simulation** is no longer unusual.
2. **Embodiment in realistic bodies** is becoming common.
3. **Browser/game interfaces** make connectome research accessible.
4. **Shuffle controls and negative controls** are increasingly used.
5. **Cross-connectome comparisons** are emerging.
6. **Connectome-specific normalization/provenance** is becoming important.
7. Some public projects now explicitly expose reproduction ledgers and known mistakes.

A recent 2026 example, `theflyRH/thefly-brain`, demonstrates a particularly strong presentation pattern: real v783 data, an explicit shuffled-connectome control, reproducible GitHub Actions, and a concrete external application. This is excellent for attention, but it is not the same product category as our provenance/audit layer. See: https://github.com/theflyRH/thefly-brain

Other 2026 examples:

- `suifei/flywire-fly-lab`: https://github.com/suifei/flywire-fly-lab
- `Recluse/FLY-lab`: https://github.com/Recluse/FLY-lab
- `snedea/flybrain`: https://github.com/snedea/flybrain
- `mikewolak/flysim`: https://github.com/mikewolak/flysim
- `rndlabsoy/fly-brain-full`: https://github.com/rndlabsoy/fly-brain-full
- `flyconnectome/flywire_annotations`: https://github.com/flyconnectome/flywire_annotations

These should be treated as living ecosystem references, not as proof that any project is biologically correct.

---

# 11. What makes our existing case potentially valuable

The strongest current asset is **not** the number 649 by itself.

It is the chain:

`four exact roots
 -> published source identifiers
 -> exact synapse-coordinate rows
 -> deterministic coordinate derivation
 -> independent Codex reproduction
 -> independent Zenodo corroboration
 -> morphology/SWC hashes
 -> published dendrite provenance
 -> deterministic subtree selection
 -> historical Point_data blob identity
 -> explicit historical generator gap
`

That chain is auditable.

The high-value object should eventually be a **click-through evidence record** for each important scientific result.

For a single synapse, the ideal record would show:

- source dataset/release;
- exact root IDs;
- source product;
- raw coordinate;
- derivation formula;
- transform and units;
- output coordinate;
- morphology/SWC identity + hash;
- independent comparison;
- claim status;
- biological interpretation status;
- unresolved items.

That is much stronger than a CSV containing a coordinate with no provenance.

---

# 12. Three future "killer" capabilities

These are the highest-value product directions identified by the research.

## 12.1 Claim Ledger

Represent each important statement as:

`claim -> evidence -> reproduction -> status -> notes`

Example statuses:

- REPRODUCED
- INDEPENDENTLY_CORROBORATED
- PARTIAL
- NEGATIVE_RESULT
- BLOCKED
- UNRESOLVED
- INFERENCE_ONLY

A claim must point to exact evidence rather than only prose.

## 12.2 Universal Provenance Manifest

Every derived artifact should be able to declare:

- source dataset;
- exact release/materialization;
- source artifact identifier;
- retrieval/materialization date where relevant;
- code commit;
- package/tool version;
- parameters;
- coordinate frame/units;
- input hashes;
- output hashes;
- validation results;
- environment information.

The manifest should be machine-readable as well as human-readable.

## 12.3 Cross-source Validator

Compare the same object/result across independent public sources, for example:

`Codex <-> Zenodo <-> Git blob <-> SWC <-> paper/dataset metadata`

The validator should expose:

- exact match;
- transformed match;
- mismatch;
- missing;
- unresolved.

This is the capability most aligned with the project's current evidence.

## 12.4 Record-level lineage

Each canonical synapse tuple now has a stable deterministic tuple identifier. The lineage index binds that record to the existing Codex exact-tuple and Zenodo exact-midpoint evidence receipts, while keeping biological compartment status UNRESOLVED.

---

# 13. What the project should NOT become

Avoid building the following simply because they are fashionable:

- a generic LIF simulator;
- a browser demo with no audit trail;
- a huge unstructured dataset mirror;
- a pile of milestone folders;
- a "magic" AI analyst that summarizes without evidence;
- a system that hides failed checks;
- a provenance framework that merely records URLs without immutable identities/hashes;
- a coordinate viewer that implies biological certainty.

---

# 14. Expansion path

The correct expansion is horizontal before vertical.

### Stage A — Strengthen the evidence engine

Make the current four-neuron case completely machine-auditable:

`source -> transform -> evidence -> independent validator -> claim ledger`

### Stage B — Generalize the schema

Allow the same provenance contract to describe:

- neuron IDs;
- morphology;
- synapse coordinates;
- connection tables;
- annotations;
- derived graph metrics;
- simulations;
- figure/table reproduction.

### Stage C — Cross-version validation

Make dataset version changes explicit:

`v783 -> later release`

Never silently mix root IDs, annotations, synapses, and morphology from different materializations.

### Stage D — Cross-connectome validation

Only after the contract is stable:

- FlyWire / FAFB
- MaleCNS
- BANC
- MANC
- other compatible connectome sources

### Stage E — Public evidence interface

A researcher should be able to click a result and answer:

> "Where exactly did this number come from?"

within a few steps.

---

# 15. What counts as success

The project's strongest long-term success metric should not be GitHub stars.

A stronger metric is:

> **How many important scientific claims can a third party trace from conclusion to immutable evidence and independently reproduce?**

Secondary metrics:

- percentage of claims with exact source identity;
- percentage independently validated;
- number of unresolved boundaries made explicit;
- reproducibility pass rate;
- time required for a new researcher to audit one claim;
- number of datasets/sources supported by the same provenance contract.

Stars, forks, traffic, and demos are useful for attention but are not scientific validation.

---

# 16. Current repository status snapshot

V1.7.1 is the current implementation target after validating the FlyVis continuous-response runtime, hardening immutable FlyVis source installation, promoting the validated FlyVis proof to a 1.6.0 release, adding release-receipt version consistency auditing, and exposing claim-to-evidence tracing through the API and CLI. The previous V1.0.1 main commit was:

`26624626bd3c8291898df5c1bc844c5dba9c4172`

V1.2.1 package state:

- core runtime dependencies: none
- direct skeleton decoder
- canonical evidence and four SWCs retained
- security hardening merged
- workflow actions pinned to immutable SHAs
- tests and CI in place

Known GitHub platform gap:

- Issue #16 remains the tracking point for settings unavailable/unfinished through the connector.

Remember:

> **Do not infer platform state from old screenshots or old chat messages. Re-check it when it matters.**

---

# 17. Primary files to consult

Start here:

1. `PROJECT_CONTEXT.md` — this file; durable project/agent memory.
2. `README.md` — public project face.
3. `VERSION` — current semantic version.
4. `CHANGELOG.md` — product history.
5. `docs/REPRODUCIBILITY.md` — reproducibility contract.
6. `docs/SECURITY_HARDENING.md` — security work.
7. `SECURITY.md` — security policy.
8. `evidence/` — canonical machine-readable evidence.
9. `data/morphology/` — four exact SWCs.
10. `tests/` — regression contract.
11. `docs/FLYVIS_ACTIVITY_BOUNDARY.md` — continuous model-response boundary and upstream pin.

For provenance research, do not rely only on README prose. Inspect evidence files and code paths.

---

# 18. Decision history that must not be lost

- V-numbered working tree was consolidated into V1.
- Historical Git history remains available for audit.
- V1 is the unified product line.
- The original Point_data generator is still unresolved.
- V1.1.0 added the machine-checkable claim ledger and artifact-integrity contract; V1.2.0 added frozen cross-source receipts; V1.2.1 bound those receipts to explicit proof executions; V1.2.2 bound the independent-corroboration claim directly to those receipts and added regression coverage for explicit manifest self-exclusion; V1.3.0 adds deterministic record-level lineage for all 649 canonical synapse rows; V1.3.1 adds byte-for-byte CI regeneration verification of that artifact; V1.4.0 adds the first concrete Code Hand create/test path; V1.5.0 adds guarded Code Hand edit execution with exact SHA-256 preconditions and atomic replacement; V1.5.1 added bounded Neural → Leader execution, the verified FlyDrones simulator integration boundary, and a separate FlyVis continuous-response provenance boundary. V1.6.0 validated that FlyVis path end-to-end on GitHub Actions using the pinned v1.2.0 revision and official preferred-direction implementation, hardened source checkout to an immutable commit, and added release-receipt version consistency enforcement. V1.7.0 adds a fail-closed claim-to-evidence trace API/CLI so a claim ID resolves to immutable evidence artifacts. V1.7.1 adds an explicit FlyVis continuous-activity semantics guard and fail-closed rejection of direct spike-contract conversion.
- The direct skeleton decoder exists partly to remove the vulnerable `fafbseg -> diskcache` runtime chain.
- Exact reproduction is valued above "close enough".
- Independent corroboration is valued above self-consistency.
- A failed or unresolved check is valuable information and should remain visible.
- The four-neuron/649-row dataset is a **case study/proof of capability**, not the final scope of the product.

---

# 19. Research-source watchlist

These repositories are useful references for future design reviews:

| Area | Reference |
|---|---|
| Whole-brain simulation | https://github.com/eonsystemspbc/fly-brain |
| Embodied AI | https://github.com/NeLy-EPFL/flygym |
| Neuroanatomy tooling | https://github.com/navis-org/navis |
| Interactive fly circuits | https://github.com/FlyBrainLab/FlyBrainLab |
| FlyWire data access | https://github.com/seung-lab/FlyConnectome |
| Connectome graph analysis | https://github.com/murthylab/flywire-network-analysis |
| Comparative connectomics | https://github.com/flyconnectome/cocoa |
| Effective connectivity | https://github.com/YijieYin/connectome_interpreter |
| Reproducible whole-brain lab | https://github.com/suifei/flywire-fly-lab |
| Controlled connectome/body comparison | https://github.com/Recluse/FLY-lab |
| Neurotransmitter consistency audit | https://github.com/jsonljn/flywire-nt-consistency |
| FlyWire annotations | https://github.com/flyconnectome/flywire_annotations |
| Robotics demo | https://github.com/SpikeCalls/FlyDrones |
| Connectome-constrained visual response model | https://github.com/TuragaLab/flyvis |
| Browser whole-brain demo | https://github.com/snedea/flybrain |
| Deterministic Apple Silicon sim | https://github.com/mikewolak/flysim |
| One-interaction neuron probing | https://github.com/vshapenko/flypoke |
| Cross-connectome normalization study | https://github.com/Pronexsteam/brainlab |
| 2026 embodied whole-brain preprint | https://github.com/rndlabsoy/fly-brain-full |
| 2026 reproducible applied brain | https://github.com/theflyRH/thefly-brain |

This list is a **watchlist**, not an endorsement and not a claim of scientific correctness.

---

# 20. The one-paragraph memory

**Digital Life Form — FlyWire V1 is a provenance-first verification/research-engineering system, not another FlyWire simulator. Its current proof case is four exact FAFB v783 neurons, 649 synapse-coordinate rows, 75 directed pairs, four hashed SWCs, reproduced against official Codex and independently corroborated with frozen Zenodo data. The project has also reconstructed the exact historical Point_data Git artifact but has not recovered its original December 2025 generator, and that gap must remain explicit. The strategic opportunity identified from the broader 2026 FlyWire ecosystem is to build a claim ledger, universal provenance manifest, and cross-source validator that trace scientific results from exact source materialization through deterministic transformations to independently checked outputs. Whole-brain simulation, embodiment, browser demos, and graph analysis are already crowded; our differentiation is evidence lineage, auditability, independent validation, and explicit unresolved boundaries. Keep the product unified under semantic Version 1.x/2.x, avoid V-number proliferation, never turn geometry into biological truth, and never make novelty or scientific-validity claims beyond the evidence.**

---

## 21. Continuation checkpoint

When a new chat says only "ادامه بده", interpret it as:

> Continue from `PROJECT_CONTEXT.md`, inspect the live repository state, preserve the scientific boundaries, and advance the highest-value unresolved item without losing provenance.

Do not restart the research from zero.
Do not ask the user to repeat project context already recorded here.
Do not assume old chat state is newer than the repository.


---

# 19. 2026-10-04 Agent Reach architectural reference

A current inspection of `Panniantong/Agent-Reach` main at commit `a19a171fa980a0785849596492e0af4db800c82f` (version `1.5.0` in that tree) produced a useful architecture reference.

Agent Reach is explicitly a **capability layer**, not a replacement for the underlying tools. Its strongest patterns for Digital Life Form are:

- capability-level abstraction above concrete implementations;
- ordered backend candidates with an observable active backend;
- real execution probes rather than command/file existence checks;
- explicit distinction between missing, broken, timeout, error, and healthy states;
- per-capability fault isolation so one broken channel does not abort the full doctor report;
- safe/default check-only behavior for environment changes;
- dry-run and explicit authorization boundaries;
- skills/documentation as an operational contract for agents.

These patterns fit the planned Leader → Web/Computer/Code Hand → Verifier architecture, but Agent Reach itself is **not** being added as a V1 runtime dependency.

The project-specific adaptation is recorded in [docs/AGENT_CAPABILITY_LAYER.md](docs/AGENT_CAPABILITY_LAYER.md).

The critical difference is that Digital Life Form must add scientific execution receipts and independent verification:

`intent/policy -> capability doctor -> backend selection -> execution -> checkpoint/recovery -> artifact receipt -> verifier -> claim ledger`

Therefore a healthy backend can establish **capability availability**, but can never by itself establish a scientific claim.

Do not mark the capability layer implemented until actual code, tests, failure/recovery cases, and inspectable execution receipts exist.

# 22. 2026-10-04 Code Hand implementation

Version 1.5.1 maintains the concrete Hand implementation in src/dlf_flywire/code_hand.py and adds the bounded Neural → Leader path around it.

Current Code Hand contract:
- create one new UTF-8 source file inside an explicit workspace;
- edit one existing UTF-8 source file only when its exact SHA-256 precondition matches;
- reject absolute/traversal paths and invalid edit targets;
- require explicit permission;
- execute explicit Python assertions against the generated or edited file;
- route operations through PolicyGate -> CapabilityDoctor -> ExecutionEngine -> independent verify_run();
- persist sealed receipts and checkpoint state;
- re-hash the resulting file after execution;
- use same-directory temporary-file replacement for edits so a failed precondition does not mutate the original bytes.

CI exercises the real CodeHand API. The smoke test creates code_hand_demo.py, tests it, edits it using the returned content SHA-256, tests the edited version, and prints the execution receipts plus independent verification.

The first Hand remains deliberately narrow. It is not yet a general autonomous coding agent, remote repository editor, web agent, installer, or desktop controller.


## 9. Neural → Leader execution boundary — 2026-10-05

Version 1.5.1 adds the first explicit software boundary between a bounded neural observation and the existing Leader/Code Hand stack.

Implemented components:

- src/dlf_flywire/neural_gateway.py: bounded sparse observations → deterministic intent candidates, with observation-set SHA-256 fingerprinting;
- src/dlf_flywire/neural_leader.py: activated candidate → normal TaskStep;
- tests/test_neural_gateway.py: deterministic selection, fail-closed behavior, mixed-window rejection, and permission-boundary tests;
- docs/NEURAL_BOUNDARY.md: scientific and security boundaries;
- tests/test_neural_leader_integration.py: integration regression proving the neural-selected capability can reach the existing Code Hand execution contract.

Critical boundary: the current neural channels are explicitly opaque/synthetic. This proves an engineering interface, not biological control by the four FlyWire neurons. Neural activity cannot grant permission, enable network access, enable system mutation, bypass policy, or bypass independent verification.

Stage A is now implemented and externally executed against the pinned FlyDrones simulator source.

The real GitHub Actions integration receipt is recorded at `evidence/flydrones_integration_receipt.json`:
- DLF commit under test: `f265f5c6531758ebf1d0a9f9db272bac4ac159b7`;
- FlyDrones source: `6519c8c0e35ae829faa98a5a02033343dd0b82d4`;
- workflow run: `37268962019`, job `111631676624`;
- observed FlyDrones model: 850 neurons, 63 recorded neurons, 384 raster events, 48 mapped observations;
- adapter fingerprint: `2b11ad4d17e5f52c49e13a346c89cfff00831dd97ea44c561c3c356ff85aaa69`;
- neural evidence fingerprint: `25edb4d54032e54e15806f11d2aa23c6ec84e587ce328c2a3f4f9ed21dea169f`;
- final execution assertion: `neural_intent -> leader -> code_hand -> verifier PASS`.
- the newer full-source receipt is stored at `evidence/flydrones_integration_receipt_2.json`; its source snapshot SHA-256 is `d647d6d4ab9adfdd546de74dfae3db8f273b860eebff289044118cd4fd6f30eb`, while the extraction fingerprint is `2b11ad4d17e5f52c49e13a346c89cfff00831dd97ea44c561c3c356ff85aaa69`.

This is a real simulator-to-runtime integration result. MiniFly is synthetic; the receipt is not evidence that the four FAFB v783 T4/T5 neurons biologically control Code Hand.

Stage B is now partially implemented in `evidence/neural_mapping_stage_b.json`: the four exact project roots are linked to their T4/T5 subtype identities and literature-supported ON/OFF plus canonical motion-direction properties. `src/dlf_flywire/neural_mapping.py` provides an executable `EvidenceBackedNeuralMapping` decoder for those labels and fails closed on unmapped identities. This establishes subtype-level functional evidence and a reproducible software decoder, not individual electrical recordings and not a Code Hand command mapping.

A separate FlyVis boundary is now implemented as `src/dlf_flywire/flyvis_adapter.py`. Frozen upstream reference: `TuragaLab/flyvis` v1.2.0, commit `92b3845cc426dd309a1a0e1b3890156c42e14021`, pretrained-model archive SHA-256 `71c78d4070556a536b13b23ee3139cd2788aa2a9d07d430a223b4edead281db1`. The adapter accepts continuous T4a/T4c/T5a/T5c model-response traces and records separate trace/source fingerprints. It deliberately does not create `NeuralObservation`, because the published FlyVis responses are continuous values in arbitrary units. This is model/cell-type evidence, not individual activity evidence for the four exact FAFB roots and not a Code Hand capability assignment. See `docs/FLYVIS_ACTIVITY_BOUNDARY.md`.

The next scientific boundary remains evidence-backed mapping from observed activity in these identities to a functional intent, followed by controlled closed-loop experiments.
