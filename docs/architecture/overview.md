# Architecture Overview

depup is designed as a modular, extensible CLI tool.

---

## High-level architecture

```mermaid
flowchart LR
    CLI[depup CLI]
    Parser[Dependency Parsers]
    Scanner[Version Scanner]
    PyPI[PyPI API]
    Executor[Upgrade Executor]
    Reports[Reports]

    CLI --> Parser
    Parser --> Scanner
    Scanner --> PyPI
    Scanner --> CLI
    CLI --> Executor
    Executor --> Reports
```

---

## Core components

### CLI Layer

* Typer-based interface
* Handles flags, output, and exit codes

### Parsers

* Parse dependency declarations and lockfiles
* Normalize dependencies into a common model

### Version Scanner

* Queries PyPI
* Compares versions
* Classifies update impact

### Upgrade Executor

* Applies upgrades safely
* Updates dependency files

### Reporting

* JSON output
* Markdown reports
* CI-friendly results