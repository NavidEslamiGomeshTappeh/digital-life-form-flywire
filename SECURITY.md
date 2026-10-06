# Security and scientific integrity

Software security and evidence integrity are release requirements.

## Reporting a software vulnerability

Please report a suspected software vulnerability through the repository's
private GitHub security channel rather than a public issue. Include:

- the affected component or file;
- the shortest reproducible description;
- impact and an example or proof of concept when safe to provide;
- the commit, release, or environment where the issue was observed.

Please allow time for triage and remediation before public disclosure. We will
acknowledge receipt, assess severity and affected versions, and publish a
coordinated fix or advisory when appropriate.

## Reporting scientific/provenance problems

Report evidence, provenance, coordinate, or interpretation problems through a
research-evidence GitHub issue. Security issues must remain in the private
security channel.

## Security controls

- No secrets belong in source control.
- Workflow permissions stay least-privilege.
- External-source failures remain visible.
- Historical binary evidence is hash-verified before deserialization.
- Pickle evidence is never accepted from arbitrary user input in CI.
- Security state never upgrades an unresolved scientific claim.
- GitHub Action dependencies are pinned to immutable full commit SHAs.

See docs/SECURITY_HARDENING.md for the current control record and the remaining
GitHub platform settings.

## Scope boundary

This policy covers the software, CI/CD, evidence-processing, provenance, and
research-integrity surfaces of this repository. It does not imply that every
GitHub platform security setting is enabled; those settings are tracked
separately and are marked complete only when live evidence supports the claim.
