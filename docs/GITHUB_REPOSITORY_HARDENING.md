# GitHub repository hardening

## Implemented in the repository
- Repository custom Copilot instructions.
- Repository-level custom agents under .github/agents.
- Dependabot configuration for Python and GitHub Actions.
- Dependency Review on pull requests.
- CodeQL workflow for Python.
- OpenSSF Scorecard workflow.
- Pull-request and research issue forms.
- Code of Conduct and Accessibility statement.

## Platform controls still requiring authenticated GitHub settings
1. Enable the Dependency graph.
2. Enable Dependabot alerts and Dependabot security updates.
3. Enable Secret scanning and push protection where available.
4. Confirm the chosen CodeQL setup in Security and quality.
5. Protect main against force-push and deletion.
6. Require the unique research gate check before merging.
7. Restrict Actions execution to trusted actors/events where appropriate.
8. Add a concise repository description and scientific topics.
9. Decide on and add a license for original project code; third-party datasets remain governed by upstream terms.
10. Decide whether the GitHub Wiki is desired.

## Scientific integrity rule
Security and repository settings must never be used to make an unresolved scientific claim appear proven.
