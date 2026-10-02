# V237 — GitHub Actions credential boundary

This bridge is designed as a read-only project-enumeration boundary inside GitHub Actions.

The intended runtime inputs are repository Actions secrets for the Supabase Management API and Neon API, plus an optional Neon organization identifier. Secret values must never be written to repository files or evidence artifacts.

Evidence semantics:
- missing credential: UNKNOWN
- HTTP/network error: FAIL
- successful authenticated project enumeration: PASS
- evidence contains only status, HTTP status, and counts

No database mutation, authentication change, deployment, branch creation, or schema change belongs in this boundary.

The implementation is intentionally not considered proven until an actual GitHub Actions run demonstrates the authenticated path.
