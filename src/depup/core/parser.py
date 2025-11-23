"""
Dependency file parser.

This module is responsible for parsing supported dependency files:
- requirements.txt
- pyproject.toml (PEP 621 or Poetry-style)
- Pipfile

It normalizes all dependencies into a common structure:
    List[DependencySpec] (dataclass)

This module does **not** check PyPI versions. It only extracts declared versions
from the project's dependency files.

Future-ready:
- Additional file formats can be added easily (e.g., conda environment.yml)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict

import tomllib  # Python 3.11+, falls back via pyproject later
import re

from depup.core.exceptions import InvalidDependencyFileError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DependencySpec:
    """
    Represents a single declared dependency in the project.

    Attributes:
        name: Package name (normalized)
        version: Version specifier string (may be None)
        source_file: Path to the file where it was declared
    """
    name: str
    version: Optional[str]
    source_file: Path


class DependencyParser:
    """
    Main entrypoint for parsing project dependency files.

    Usage:
    -------
    parser = DependencyParser(project_root=Path("."))
    deps = parser.parse_all()
    """

    SUPPORTED_FILES = ["requirements.txt", "pyproject.toml", "Pipfile"]

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def parse_all(self) -> List[DependencySpec]:
        """
        Parse all supported dependency files found in the project root.
        """
        results: List[DependencySpec] = []
        logger.debug("Scanning project root for dependency files...")

        for file_name in self.SUPPORTED_FILES:
            file_path = self.project_root / file_name
            if file_path.exists():
                logger.info(f"Parsing dependency file: {file_path}")
                results.extend(self._parse_file(file_path))

        return results

    # -------------------------------
    # File dispatching
    # -------------------------------
    def _parse_file(self, file_path: Path) -> List[DependencySpec]:
        if file_path.name == "requirements.txt":
            return self._parse_requirements(file_path)

        if file_path.name == "pyproject.toml":
            return self._parse_pyproject(file_path)

        if file_path.name == "Pipfile":
            return self._parse_pipfile(file_path)

        raise InvalidDependencyFileError(f"Unsupported file format: {file_path}")

    # -------------------------------
    # requirements.txt
    # -------------------------------
    def _parse_requirements(self, path: Path) -> List[DependencySpec]:
        deps: List[DependencySpec] = []
        pattern = re.compile(r"^([a-zA-Z0-9_\-]+)([<>=!~].+)?$")

        for line in path.read_text().splitlines():
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            match = pattern.match(line)
            if not match:
                logger.warning(f"Skipping unrecognized requirement line: {line}")
                continue

            name, version = match.group(1), match.group(2)
            deps.append(DependencySpec(name=name, version=version, source_file=path))

        return deps

    # -------------------------------
    # pyproject.toml
    # -------------------------------
    def _parse_pyproject(self, path: Path) -> List[DependencySpec]:
        data = tomllib.loads(path.read_text())
        deps: List[DependencySpec] = []

        # PEP 621: [project] > dependencies
        project_section: Optional[Dict] = data.get("project")
        if project_section and "dependencies" in project_section:
            for item in project_section["dependencies"]:
                name, version = self._split_pep621_dependency(item)
                deps.append(DependencySpec(name=name, version=version, source_file=path))

        # Poetry: [tool.poetry.dependencies]
        poetry_section = (
            data.get("tool", {})
            .get("poetry", {})
            .get("dependencies", {})
        )

        for name, version in poetry_section.items():
            if name.lower() == "python":
                continue  # not a depe
