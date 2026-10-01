# Release Process

1. Run the local compile and unit tests.
2. Run the network probe.
3. Inspect the recovery report and hashes.
4. Update CHANGELOG.md and RELEASE_NOTES.md.
5. Confirm that no placeholder or substituted neuron is included.
6. Create a Git tag/release through GitHub when the release tooling is available.

Important: a software-test PASS must never be described as successful external-data recovery without a corresponding recovery report.