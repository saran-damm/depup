# Changelog

All notable changes to this project will be documented in this file.

The format follows **Semantic Versioning**: https://semver.org/

---

## [0.1.0] - 2025-11-24
### Added
- Initial public release of `depup`
- CLI command: `depup scan`
- Dependency parser supporting:
  - requirements.txt
  - pyproject.toml (PEP 621 + Poetry)
  - Pipfile
- `depup scan --latest` with:
  - PyPI version lookup via `pip index`
  - Semantic version classification (patch/minor/major)
- Rich-powered CLI table outputs
- Logging framework
- Base project structure (`src/depup/*`)
- MIT License
- Initial README for PyPI & GitHub

---

## [Unreleased]
### Planned
- Upgrade executor (`depup upgrade`)
- Dependency file rewriting after upgrades
- Markdown/HTML report generator
- Post-upgrade code scanning
- LLM-assisted changelog summarization
- MCP agent integration for IDEs