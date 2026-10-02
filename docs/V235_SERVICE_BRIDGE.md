# V235 Service Bridge

This milestone records what the connected service tools can actually prove at runtime and establishes a fail-closed boundary between ChatGPT-native service access and GitHub Actions.

## Verified now

- GitHub: repository read/write access is verified.
- Wolfram: a live calculation was executed successfully.
- TinyFish: a live public-web search was executed successfully.
- Supabase: the connector is present, but both available account links currently expose zero projects. No project was selected or modified.
- Neon: the connector is present, but the current connection is unscoped and requires a project ID. No Neon project was modified.

## Important boundary

Connecting a service to ChatGPT does not automatically place its credentials inside GitHub Actions. GitHub Actions uses repository/environment secrets for credentials, and those secrets must be configured in GitHub. The repository therefore never assumes that a ChatGPT connector implies CI credentials.

GitHub documents repository Actions secrets as the place for API keys/tokens, and recommends least-privilege credentials. Supabase documents GitHub Actions/CLI deployment using secrets such as a Supabase access token and project ID. Neon documents GitHub Actions integration using a Neon API key and project ID.

## Next bridge stage

When the relevant GitHub Actions secrets are available, the workflow can turn each service from unavailable-to-CI into an independently tested CI capability. Until then, the ledger remains the source of truth and the system fails closed.

## Evidence policy

A successful tool call is recorded as evidence of that tool's availability, not proof that the whole Digital Life Form system is scientifically correct. Scientific claims still require their own source-data and reproducibility evidence.
