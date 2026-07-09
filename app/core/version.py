"""
Single source of truth for the application version.

Kept in sync with the `version` field in pyproject.toml automatically
by `bump-my-version` (see [tool.bumpversion] in pyproject.toml and
`make bump-patch` / `make bump-minor` / `make bump-major`).

Do not edit this value by hand — always use the make targets, so
pyproject.toml, this file, the git tag, and the CHANGELOG entry all
move together in one commit.
"""
__version__ = "0.1.0"