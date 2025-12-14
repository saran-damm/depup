# depup Documentation

**depup** is a dependency upgrade advisor for Python projects.  
It helps teams **understand**, **monitor**, and **safely upgrade** dependencies
across files, lockfiles, and environments.

---

## Why depup?

Most Python projects struggle with:

- Dependencies scattered across multiple files
- No visibility into outdated packages
- Risky upgrades without knowing impact
- CI failures caused by unnoticed dependency drift

depup solves this by providing:

- A single view of all dependencies
- Clear semantic version impact (patch / minor / major)
- CI-friendly checks
- Safe and explainable upgrade workflows

---

## What depup does today (v0.9.0)

- Scans project dependency files and lockfiles
- Scans installed environments
- Fetches latest versions from PyPI
- Classifies update impact
- Supports JSON and Markdown reports
- Provides CI-friendly exit codes

---

## Getting Started

👉 Start here: [Quick Start](quickstart.md)  
👉 Install depup: [Installation](installation.md)

---

## Who is depup for?

- Developers maintaining Python projects
- Teams enforcing dependency hygiene in CI
- Open-source maintainers
- AI-assisted developer tools (future MCP integration)

---

## Roadmap

See the planned evolution of depup in the [Roadmap](roadmap.md).
