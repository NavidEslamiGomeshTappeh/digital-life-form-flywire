---
name: provenance-audit
description: Trace and verify exact source-to-result chains in this connectomics repository.
---

For every provenance task:
1. Start from the exact target identifier.
2. Pin the strongest immutable source available.
3. Record commit, version, blob, checksum and artifact identifiers.
4. Reproduce the transformation deterministically.
5. Fail closed on missing or ambiguous source data.
6. Separate direct source facts, computation, inference and unresolved claims.
7. Inspect generated artifacts, not only source code.
8. Report exact evidence and remaining limits.
