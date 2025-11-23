"""
Dependency file parser.

This module is responsible for parsing supported dependency files:
- requirements.txt
- pyproject.toml (PEP 621 or Poetry-style)
- Pipfile

It normalizes all dependencies into a common structure: DependencySpec.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import tomllib  # Python 3.11+

from depup.core.exceptions import InvalidDependencyFileError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DependencySpec:
    """
    Represents a single declared dependency in the project.

    Attributes:
        name: Package name (normalized).
        version: Version specifier string (may be None).
        source_file: Path to the file where it was declared.
    """

    name: str
    version: Optional[str]
    source_file: Path


class DependencyParser:
    """
    Main entrypoint for parsing project dependency files.

    Usage:
        parser = DependencyParser(project_root=Path("."))
        deps = parser.parse_all()
    """

    SUPPORTED_FILES = ["requirements.txt", "pyproject.toml", "Pipfile"]

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    def parse_all(self) -> List[DependencySpec]:
        """
        Parse all supported dependency files found in the project root.
        """
        results: List[DependencySpec] = []
        logger.debug("Scanning project root for dependency files in %s", self.project_root)

        for file_name in self.SUPPORTED_FILES:
            file_path = self.project_root / file_name
            if file_path.exists():
                logger.info("Parsing dependency file: %s", file_path)
                parsed = self._parse_file(file_path)
                # Defensive: avoid None causing TypeError in extend
                if parsed is None:
                    raise InvalidDependencyFileError(
                        f"Parser for {file_path} returned no data (None)."
                    )
                results.extend(parsed)

        return results

    # ---------------------------------------------------------------------
    # File dispatching
    # ---------------------------------------------------------------------
    def _parse_file(self, file_path: Path) -> List[DependencySpec]:
        """
        Dispatch to the appropriate parser based on file name.
        """
        if file_path.name == "requirements.txt":
            return self._parse_requirements(file_path)

        if file_path.name == "pyproject.toml":
            return self._parse_pyproject(file_path)

        if file_path.name == "Pipfile":
            return self._parse_pipfile(file_path)

        raise InvalidDependencyFileError(f"Unsupported file format: {file_path}")

    # ---------------------------------------------------------------------
    # requirements.txt
    # ---------------------------------------------------------------------
    def _parse_requirements(self, path: Path) -> List[DependencySpec]:
        """
        Parse a requirements.txt style file.

        Supports lines like:
            requests==2.31.0
            numpy>=1.20
        Ignores comments and blank lines.
        """
        deps: List[DependencySpec] = []
        pattern = re.compile(r"^([a-zA-Z0-9_\-]+)\s*([<>=!~].+)?$")

        for raw_line in path.read_text().splitlines():
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            match = pattern.match(line)
            if not match:
                logger.warning("Skipping unrecognized requirement line: %s", line)
                continue

            name, version = match.group(1), match.group(2)
            deps.append(DependencySpec(name=name, version=version, source_file=path))

        return deps

    # ---------------------------------------------------------------------
    # pyproject.toml
    # ---------------------------------------------------------------------
    def _parse_pyproject(self, path: Path) -> List[DependencySpec]:
        """
        Parse a pyproject.toml file.

        Supports:
        - [project] dependencies (PEP 621)
        - [tool.poetry.dependencies] (Poetry-style)
        """
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

        if poetry_section:
            for name, version in poetry_section.items():
                if name.lower() == "python":
                    continue  # not a package dependency
                deps.append(
                    DependencySpec(name=name, version=str(version), source_file=path)
                )

        return deps

    def _split_pep621_dependency(self, dep: str) -> tuple[str, Optional[str]]:
        """
        Split a PEP 621 dependency string.

        Examples:
            "requests>=2.0" -> ("requests", ">=2.0")
            "numpy"         -> ("numpy", None)
        """
        if any(op in dep for op in (">=", "<=", "==", "!=", "<", ">", "~=")):
            parts = re.split(r"([<>=!~!].+)", dep, maxsplit=1)
            name = parts[0]
            version = parts[1] if len(parts) > 1 else None
            return name, version

        return dep, None

    # ---------------------------------------------------------------------
    # Pipfile
    # ---------------------------------------------------------------------
    def _parse_pipfile(self, path: Path) -> List[DependencySpec]:
        """
        Parse a Pipfile (TOML).

        Supports:
            [packages]
            [dev-packages]
        """
        data = tomllib.loads(path.read_text())
        deps: List[DependencySpec] = []

        for section_name in ("packages", "dev-packages"):
            section = data.get(section_name, {})
            for name, version in section.items():
                deps.append(
                    DependencySpec(name=name, version=str(version), source_file=path)
                )

        return deps
