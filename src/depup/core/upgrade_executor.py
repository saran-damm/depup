"""
Upgrade executor.

Responsible for:
- Taking a list of planned upgrades (packages and target versions).
- Running `pip install --upgrade` for each package (unless dry-run).
- Updating dependency declarations in:
  - requirements.txt
  - pyproject.toml (PEP 621 + Poetry)
  - Pipfile (packages and dev-packages)

This uses a minimal, safe strategy:
- For requirements.txt: rewrite pinned/ranged versions on matching lines.
- For pyproject.toml:
    - [project].dependencies: rewrite only the version number, keep operator.
    - [tool.poetry.dependencies]: rewrite only the version number, keep operator.
- For Pipfile:
    - [packages] / [dev-packages]: rewrite only non-wildcard version strings.
"""

from __future__ import annotations

import logging
import re
import sys
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any

import tomllib
import tomli_w

from depup.core.exceptions import DepupError
from depup.core.models import DependencySpec

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PlannedUpgrade:
    """
    A single planned package upgrade.

    Attributes:
        name: Package name.
        current_spec: Current version specifier string (e.g. '==1.2.3' or '>=1.0'), may be None.
        target_version: Concrete version to upgrade to (e.g. '2.0.1').
        source_file: File where this dependency was originally declared.
    """

    name: str
    current_spec: Optional[str]
    target_version: str
    source_file: Path


@dataclass(frozen=True)
class UpgradeResult:
    """
    Result of executing a single upgrade.

    Attributes:
        name: Package name.
        from_version: String representation of the previous spec (may be None).
        to_version: Target version attempted.
        success: True if upgrade succeeded (or dry-run), False otherwise.
        error: Optional error message, if any.
        dry_run: True if no actual installation was performed.
    """

    name: str
    from_version: Optional[str]
    to_version: str
    success: bool
    error: Optional[str]
    dry_run: bool


class UpgradeExecutionError(DepupError):
    """Raised when a package upgrade fails at the executor level."""


class UpgradeExecutor:
    """
    Executes dependency upgrades for a project.

    Initialized with:
        project_root: Path to the project.
        dependencies: List of DependencySpec parsed from supported files.
    """

    def __init__(self, project_root: Path, dependencies: List[DependencySpec]) -> None:
        self.project_root = project_root
        self.dependencies = dependencies

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def execute(self, plans: List[PlannedUpgrade], dry_run: bool = False) -> List[UpgradeResult]:
        """
        Execute the given list of planned upgrades.

        Args:
            plans: List of PlannedUpgrade describing what to upgrade.
            dry_run: If True, no changes are made; commands are only logged.

        Returns:
            List of UpgradeResult objects describing the outcome for each package.
        """
        results: List[UpgradeResult] = []

        for plan in plans:
            logger.info("Processing upgrade for %s -> %s", plan.name, plan.target_version)

            if dry_run:
                logger.info("Dry-run: would run pip install --upgrade %s==%s", plan.name, plan.target_version)
                results.append(
                    UpgradeResult(
                        name=plan.name,
                        from_version=plan.current_spec,
                        to_version=plan.target_version,
                        success=True,
                        error=None,
                        dry_run=True,
                    )
                )
                continue

            try:
                self._run_pip_upgrade(plan)
                self._update_dependency_files(plan)
            except Exception as exc:
                logger.error("Upgrade failed for %s: %s", plan.name, exc)
                results.append(
                    UpgradeResult(
                        name=plan.name,
                        from_version=plan.current_spec,
                        to_version=plan.target_version,
                        success=False,
                        error=str(exc),
                        dry_run=False,
                    )
                )
                continue

            results.append(
                UpgradeResult(
                    name=plan.name,
                    from_version=plan.current_spec,
                    to_version=plan.target_version,
                    success=True,
                    error=None,
                    dry_run=False,
                )
            )

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _run_pip_upgrade(self, plan: PlannedUpgrade) -> None:
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    f"{plan.name}=={plan.target_version}",
                ],
                check=True,
                text=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as exc:
            logger.error("pip install failed for %s: %s", plan.name, exc.stderr)
            raise UpgradeExecutionError(
                f"pip install failed for {plan.name}: {exc.stderr}"
            ) from exc
        
    def _backup_file(self, path: Path) -> None:
        backup = path.with_suffix(path.suffix + ".depup.bak")
        if not backup.exists():
            backup.write_text(path.read_text())

    def _update_dependency_files(self, plan: PlannedUpgrade) -> None:
        """
        Update dependency declarations in supported files after a successful upgrade.

        - requirements.txt
        - pyproject.toml
        - Pipfile
        """
        matching_specs = [
            d for d in self.dependencies if d.name.lower() == plan.name.lower()
        ]

        for spec in matching_specs:
            if spec.source_file.name == "requirements.txt":
                self._update_requirements_entry(spec.source_file, spec.name, plan.target_version)
            elif spec.source_file.name == "pyproject.toml":
                self._update_pyproject(spec.source_file, spec.name, plan.target_version)
            elif spec.source_file.name == "Pipfile":
                self._update_pipfile(spec.source_file, spec.name, plan.target_version)

    # ----------------- requirements.txt -------------------------------- #
    def _update_requirements_entry(self, path: Path, package: str, new_version: str) -> None:
        """
        Rewrite a single package line in requirements.txt to point to new_version.

        Only lines that match `<package><op><version>` are changed. Operators and comments are preserved.

        Example:
            requests==1.0.0   -> requests==2.0.0
            requests>=1.0.0   -> requests>=2.0.0
        """
        if not path.exists():
            logger.warning("requirements.txt file %s does not exist", path)
            return

        logger.info("Updating %s entry for %s to version %s", path, package, new_version)
        lines = path.read_text().splitlines()
        updated_lines: List[str] = []

        pattern = re.compile(
            rf"^(\s*)({re.escape(package)})(\s*[<>=!~]+)([^;\s]+)(.*)$",
            re.IGNORECASE,
        )

        for line in lines:
            match = pattern.match(line)
            if match:
                prefix_ws, name, op, _old_version, suffix = match.groups()
                new_line = f"{prefix_ws}{name}{op}{new_version}{suffix}"
                updated_lines.append(new_line)
            else:
                updated_lines.append(line)

        self._backup_file(path)
        path.write_text("\n".join(updated_lines) + "\n")

    # ----------------- pyproject.toml ---------------------------------- #
    def _update_pyproject(self, path: Path, package: str, new_version: str) -> None:
        """
        Update pyproject.toml dependency declarations for a given package.

        Supported:
        - [project].dependencies (PEP 621, list of strings)
        - [tool.poetry.dependencies] (simple string values)
        """
        if not path.exists():
            logger.warning("pyproject.toml file %s does not exist", path)
            return

        content = path.read_text()
        data: Dict[str, Any] = tomllib.loads(content)
        updated = False

        # PEP 621: [project].dependencies = [ "pkg>=1.0", "other" ]
        project_section = data.get("project")
        if project_section and isinstance(project_section.get("dependencies"), list):
            new_deps: List[str] = []
            for dep_str in project_section["dependencies"]:
                new_dep_str = self._rewrite_pep621_entry(dep_str, package, new_version)
                if new_dep_str != dep_str:
                    updated = True
                new_deps.append(new_dep_str)
            project_section["dependencies"] = new_deps

        # Poetry: [tool.poetry.dependencies]
        tool = data.get("tool") or {}
        poetry = tool.get("poetry") or {}
        poetry_deps = poetry.get("dependencies")

        if isinstance(poetry_deps, dict):
            for name, value in list(poetry_deps.items()):
                if name.lower() != package.lower():
                    continue
                if isinstance(value, str):
                    new_value = self._rewrite_version_literal(value, new_version)
                    if new_value != value:
                        poetry_deps[name] = new_value
                        updated = True
                else:
                    logger.info(
                        "Skipping complex Poetry dependency for %s in %s (non-string value).",
                        package,
                        path,
                    )

        if updated:
            logger.info("Writing updated pyproject.toml for %s", package)
            self._backup_file(path)
            path.write_text(tomli_w.dumps(data))

    def _rewrite_pep621_entry(self, dep_str: str, package: str, new_version: str) -> str:
        """
        Rewrite a single PEP 621 dependency string if it matches `package`.

        Example:
            "requests>=2.30.0" -> "requests>=2.31.0"
            "numpy"            -> unchanged (no version to rewrite)
        """
        ops = ["==", ">=", "<=", "~=", "!=", "<", ">"]
        for op in ops:
            if op in dep_str:
                name_part, version_part = dep_str.split(op, 1)
                name = name_part.strip()
                if name.lower() != package.lower():
                    return dep_str
                return f"{name}{op}{new_version}"
        return dep_str

    def _rewrite_version_literal(self, spec: str, new_version: str) -> str:
        """
        Rewrite a simple version literal string, keeping the operator.

        Examples:
            ">=2.30.0" -> ">=2.31.0"
            "==1.2.3"  -> "==2.0.0"
            "*"        -> "*" (unchanged)
        """
        spec = spec.strip()
        if spec == "*" or spec == "":
            return spec

        ops = ["==", ">=", "<=", "~=", "!=", "<", ">"]
        for op in ops:
            if op in spec:
                prefix, _old = spec.split(op, 1)
                return f"{prefix.strip()}{op}{new_version}"
        # If no operator, leave as-is (minimal strategy)
        return spec

    # ----------------- Pipfile ----------------------------------------- #
    def _update_pipfile(self, path: Path, package: str, new_version: str) -> None:
        """
        Update Pipfile dependency declarations for a given package.

        Supported:
        - [packages]
        - [dev-packages]

        Only simple string values are updated; wildcard "*" is left as-is.
        """
        if not path.exists():
            logger.warning("Pipfile %s does not exist", path)
            return

        content = path.read_text()
        data: Dict[str, Any] = tomllib.loads(content)
        updated = False

        for section_name in ("packages", "dev-packages"):
            section = data.get(section_name)
            if isinstance(section, dict):
                for name, value in list(section.items()):
                    if name.lower() != package.lower():
                        continue
                    if isinstance(value, str):
                        new_value = self._rewrite_version_literal(value, new_version)
                        if new_value != value:
                            section[name] = new_value
                            updated = True
                    else:
                        logger.info(
                            "Skipping complex Pipfile entry for %s in section [%s] (non-string value).",
                            package,
                            section_name,
                        )

        if updated:
            logger.info("Writing updated Pipfile for %s", package)
            self._backup_file(path)
            path.write_text(tomli_w.dumps(data))
