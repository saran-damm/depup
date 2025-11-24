# depup — Dependency Upgrade Advisor

[![PyPI Version](https://img.shields.io/pypi/v/depup.svg)](https://pypi.org/project/depup/)
![Python Versions](https://img.shields.io/pypi/pyversions/depup.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
[![Docs](https://img.shields.io/badge/docs-coming--soon-blue)](https://example.com)
![CI](https://github.com/saran-damm/depup/actions/workflows/ci.yml/badge.svg)
![Publish](https://github.com/saran-damm/depup/actions/workflows/publish.yml/badge.svg)

**Depup** is a modern Python CLI tool that helps developers keep their project dependencies up-to-date, safe, and maintainable. It automatically:

- Scans for declared dependencies  
- Detects updates on PyPI  
- Classifies semantic versioning impact (patch/minor/major)  
- Prepares upgrade paths  
- (Future) Provides AI-assisted upgrade analysis and code fixes

This tool is built for modern development workflows and future integration with AI agents (Cursor, Windsurf, Continue) via MCP.

---

## 🚀 Features

### ✅ Current Features
- Parse `requirements.txt`, `pyproject.toml`, and `Pipfile`
- Display declared package versions
- Fetch latest versions from PyPI (`depup scan --latest`)
- Categorize updates by semantic version (patch/minor/major)
- Clean, colorized CLI output via Typer + Rich

### 🧭 Roadmap (Planned)
- Automated safe upgrades via `depup upgrade`
- Dependency file rewriting after upgrades
- Post-upgrade code scanning
- Markdown/HTML upgrade reports
- LLM-powered changelog summarization
- MCP Agent integration for AI IDEs

---

## Installation

``` bash
pip install depup
```

Or with `uv`:

```bash
uv tool install depup
```
---

## 📘 Usage

### List declared dependencies

```bash
depup scan
```

### Show latest available versions from PyPI

```bash
depup scan --latest
```

Example output:

```
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Package Name ┃ Declared Spec┃ Latest Version┃ Update Type  ┃ Source File  ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ typer        │ >=0.12       │ 0.12.3        │ patch        │ pyproject.toml
│ packaging    │ >=24.0       │ 24.1.0        │ patch        │ pyproject.toml
│ rich         │ >=13.0       │ 13.7.1        │ patch        │ pyproject.toml
└──────────────┴──────────────┴───────────────┴──────────────┴──────────────┘
```

---

## 📂 Supported Dependency Files

* `requirements.txt`
* `pyproject.toml` (PEP 621 and Poetry)
* `Pipfile`

---

## 🧪 Testing

```bash
pytest -q
```

---

## 🧱 Project Structure

```text
src/depup/
    cli/
    core/
    reporting/
    scanning/
    utils/
tests/
pyproject.toml
README.md
CHANGELOG.md
LICENSE
```

---

## 🔖 Version Management

We use **bump2version** to automate versioning:

```bash
bump2version patch  # 0.1.1 → 0.1.2
bump2version minor  # 0.1.1 → 0.2.0
bump2version major  # 0.1.1 → 1.0.0
```

---

## 📄 License

This project is licensed under the MIT License — see the `LICENSE` file for details.

---

## 🤝 Contributing

Contributions are welcome!
Feel free to open issues or submit PRs.

---

## ⭐ Acknowledgements

This project is inspired by modern dependency management workflows and the architecture outlined in the technical design document.
