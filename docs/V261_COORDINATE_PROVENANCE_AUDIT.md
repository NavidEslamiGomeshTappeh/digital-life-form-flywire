# V261 — Coordinate-frame-aware provenance audit

V261 is the corrective layer after V259.

The historical T4/T5 study publishes Point_data containing exact FlyWire IDs and dendrite-root coordinates. The project also has exact V229 SWCs. These are linked by identity, but the repository does not establish that both pipelines use an identical coordinate frame or identical skeleton geometry.

## What V261 proves

- The four exact project root IDs occur in the immutable historical Point_data source.
- The published source blob is verified before deserialization.
- Published dendrite root coordinates and morphology metrics are preserved as source facts.
- Raw distance between published points and V229 coordinates is retained only as a diagnostic.
- The V258 automatic subtree candidate is compared numerically with published reduced-dendrite metrics.

## Coordinate rule

STUDY_NATIVE_FLYWIRE_PIPELINE and V229_PROJECT_SWC_NATIVE are separate frames unless a deterministic transform is independently established.

A raw coordinate distance therefore cannot produce a provenance PASS/FAIL result.

## What V261 does not prove

- A common rigid or affine transform between the two pipelines.
- Bitwise identity between V229 SWCs and the study's internal .nr forests.
- Recovery of manual dendrite corrections.
- Individual synaptic-cleft biological compartment identity.

This version deliberately rejects semantic overreach.
