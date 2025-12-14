"""
Dependency file parser.

Parses supported dependency declaration files:
- requirements.txt
- pyproject.toml (PEP 621 and Poetry)
- Pipfile

Normalizes all dependencies into DependencySpec.
"""

from __future__ import annotations

import logging
import re
import tomllib
from pathlib import Path
from typing import Dict, List, Optional

from depup.core.exceptions import InvalidDependencyFileError
from depup.core.models import DependencySpec

logger = logging.getLogger(__name__)


class DependencyParser:
    """
    Entry point for parsing project dependency files.
    """

    SUPPORTED_FILES: tuple[str, ...] = (
        "requirements.txt",
        "pyproject.toml",
        "Pipfile",
    )

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    def parse_all(self) -> List[DependencySpec]:
        """
        Parse all supported dependency files found in the project root.
        """
        results: List[DependencySpec] = []

        logger.debug(
            "Scanning project root for dependency files in %s",
            self.project_root,
        )

        for file_name in self.SUPPORTED_FILES:
            file_path = self.project_root / file_name
            if not file_path.exists():
                continue

            parsed = self._parse_file(file_path)
            if parsed is None:
                raise InvalidDependencyFileError(
                    f"Parser for {file_path} returned no data."
                )

            results.extend(parsed)

        return results

    # ------------------------------------------------------------------
    # Dispatcher
    # ------------------------------------------------------------------
    def _parse_file(self, file_path: Path) -> List[DependencySpec]:
        if file_path.name == "requirements.txt":
            return self._parse_requirements(file_path)

        if file_path.name == "pyproject.toml":
            return self._parse_pyproject(file_path)

        if file_path.name == "Pipfile":
            return self._parse_pipfile(file_path)

        raise InvalidDependencyFileError(f"Unsupported file format: {file_path}")

    # ------------------------------------------------------------------
    # requirements.txt
    # ------------------------------------------------------------------
    def _parse_requirements(self, path: Path) -> List[DependencySpec]:
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
            deps.append(
                DependencySpec(
                    name=name.lower(),
                    version=version,
                    source_file=path,
                )
            )

        return deps

    # ------------------------------------------------------------------
    # pyproject.toml
    # ------------------------------------------------------------------
    def _parse_pyproject(self, path: Path) -> List[DependencySpec]:
        with path.open("rb") as f:
            data = tomllib.load(f)

        deps: List[DependencySpec] = []

        # PEP 621
        project_section: Optional[Dict] = data.get("project")
        if project_section:
            for item in project_section.get("dependencies", []):
                name, version = self._split_pep621_dependency(item)
                deps.append(
                    DependencySpec(
                        name=name.lower(),
                        version=version,
                        source_file=path,
                    )
                )

        # Poetry
        poetry_deps = (
            data.get("tool", {})
            .get("poetry", {})
            .get("dependencies", {})
        )

        for name, version in poetry_deps.items():
            if name.lower() == "python":
                continue

            deps.append(
                DependencySpec(
                    name=name.lower(),
                    version=str(version),
                    source_file=path,
                )
            )

        return deps

    def _split_pep621_dependency(
        self,
        dep: str,
    ) -> tuple[str, Optional[str]]:
        """
        Split a PEP 621 dependency string into name and version specifier.
        """
        dep = dep.strip()

        match = re.match(
            r"^([a-zA-Z0-9_\-]+)\s*(.*)?$",
            dep,
        )
        if not match:
            return dep, None

        name = match.group(1)
        version = match.group(2) or None

        return name, version

    # ------------------------------------------------------------------
    # Pipfile
    # ------------------------------------------------------------------
    def _parse_pipfile(self, path: Path) -> List[DependencySpec]:
        with path.open("rb") as f:
            data = tomllib.load(f)

        deps: List[DependencySpec] = []

        for section_name in ("packages", "dev-packages"):
            section = data.get(section_name, {})
            for name, version in section.items():
                deps.append(
                    DependencySpec(
                        name=name.lower(),
                        version=str(version),
                        source_file=path,
                    )
                )

        return deps
