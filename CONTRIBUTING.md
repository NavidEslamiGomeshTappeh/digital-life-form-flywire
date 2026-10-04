# Contributing

Version 1 is the stable project baseline. Changes should improve the reusable system rather than create another milestone-specific product directory.

Before a pull request:
1. python -m ruff check .
2. python -m pytest -q
3. python -m dlf_flywire validate
4. confirm README, citation metadata and evidence remain consistent.

Do not weaken scientific boundaries or tests merely to make CI green.
