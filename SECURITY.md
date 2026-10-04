# Security and scientific integrity

Software security and evidence integrity are release requirements.

- No secrets belong in source control.
- Workflow permissions stay least-privilege.
- External-source failures remain visible.
- Historical binary evidence is hash-verified before deserialization.
- Pickle evidence is never accepted from arbitrary user input in CI.
- Security state never upgrades an unresolved scientific claim.

Report software vulnerabilities through the repository's private GitHub security channel. Report provenance/scientific issues through the research-evidence issue form.
