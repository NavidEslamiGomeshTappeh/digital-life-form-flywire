# V238 — Neon Evidence Bridge

Persists checked-in repository evidence into Neon.

Safety:
- Reads evidence artifacts only.
- Does not download FlyWire data.
- Does not modify scientific source artifacts.
- Preserves UNKNOWN provenance.
- No credential is stored in the repository.

Required GitHub Actions secret: NEON_DATABASE_URL

Writes to research_runs, research_claims, and evidence_records.

V229 exact-root evidence and V231 structural evidence are persisted.
V230 structural evidence is persisted, but V230 biological provenance remains UNKNOWN until the canonical FAFB v783 source is actually probed.
