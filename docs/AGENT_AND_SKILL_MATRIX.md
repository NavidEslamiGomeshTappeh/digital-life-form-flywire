# Repository AI architecture

## Custom agents

- Research Lead — decomposes complex research tasks into evidence, implementation, verification and security work.
- Provenance Auditor — traces exact source chains and hashes.
- Connectome Engineer — implements connectivity and morphology extraction.
- Scientific Verifier — challenges biological wording against primary evidence.
- Security Auditor — reviews workflows, dependencies, provenance bypasses and unsafe execution.

Custom agent profiles live under .github/agents/.

## Agent skills

- provenance-audit — exact source-chain auditing.
- actions-debugging — reproducible Actions diagnosis.
- scientific-evidence — coordinate-frame and biological-claim separation.
- research-release — release-readiness checks.

Project skills live under .github/skills/.

GitHub documents project skills at .github/skills/<skill>/SKILL.md and repository custom agents under .github/agents/. Skills are opt-in and should be reviewed for prompt-injection or malicious-script risk before installing external skills.

The repository's source code and machine-readable evidence remain authoritative; agents and skills do not override scientific evidence.
