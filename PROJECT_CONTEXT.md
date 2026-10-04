# PROJECT CONTEXT — Digital Life Form / FlyWire

> **Canonical continuation file.**
>
> This file is the durable working memory for future ChatGPT/agent sessions.
> When the chat changes, **read this file first** before making scientific, architectural,
> provenance, security, or repository decisions.
>
> Last consolidated: **2026-10-04**
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
- Source commit: `56901ad1853b44aeca15504cd908fa4c31009a3e`
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

V1.3.1 is the current implementation target after adding byte-for-byte lineage regeneration verification. The previous V1.0.1 main commit was:

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

For provenance research, do not rely only on README prose. Inspect evidence files and code paths.

---

# 18. Decision history that must not be lost

- V-numbered working tree was consolidated into V1.
- Historical Git history remains available for audit.
- V1 is the unified product line.
- The original Point_data generator is still unresolved.\n- V1.1.0 added the machine-checkable claim ledger and artifact-integrity contract; V1.2.0 added frozen cross-source receipts; V1.2.1 bound those receipts to explicit proof executions; V1.2.2 bound the independent-corroboration claim directly to those receipts and added regression coverage for explicit manifest self-exclusion; V1.3.0 adds deterministic record-level lineage for all 649 canonical synapse rows; V1.3.1 adds byte-for-byte CI regeneration verification of that artifact.
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
