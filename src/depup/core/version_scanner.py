"""
Version Scanner

Responsible for:
- Extracting declared package versions from DependencySpec objects
- Looking up the latest version on PyPI
- Comparing current vs latest using packaging.version
- Classifying update types: patch, minor, major

This module does not perform installs; it only reports version metadata.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from typing import List, Optional

from packaging.version import Version, InvalidVersion

from depup.core.parser import DependencySpec
from depup.core.exceptions import DepupError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VersionInfo:
    """
    Represents upgrade metadata for a package.

    Attributes:
        name: Package name
        current: Current declared version (may be None)
        latest: Latest version available on PyPI
        update_type: "patch" | "minor" | "major" | "none"
    """
    name: str
    current: Optional[str]
    latest: str
    update_type: str


class VersionScannerError(DepupError):
    """Raised when version scanning fails for any package."""


class VersionScanner:
    """
    Scans packages for available updates using PyPI.

    Usage:
    -------
    scanner = VersionScanner()
    results = scanner.scan(dependencies)
    """

    def scan(self, dependencies: List[DependencySpec]) -> List[VersionInfo]:
        results: List[VersionInfo] = []

        for dep in dependencies:
            try:
                latest = self._get_latest_from_pypi(dep.name)
                update_type = self._classify_update(dep.version, latest)
                results.append(
                    VersionInfo(
                        name=dep.name,
                        current=dep.version,
                        latest=latest,
                        update_type=update_type,
                    )
                )
            except Exception as e:
                raise VersionScannerError(f"Failed to scan version for {dep.name}: {e}")

        return results

    # ------------------------------------------------------------------
    # Get latest version from PyPI via pip index
    # ------------------------------------------------------------------
    def _get_latest_from_pypi(self, package: str) -> str:
        """
        Uses `pip index versions <package>` to retrieve available versions.

        Example output:
            requests (2.31.0)
            Available versions: 2.31.0, 2.30.0, ...

        This avoids hitting PyPI JSON API directly and respects env settings.
        """
        try:
            result = subprocess.run(
                ["pip", "index", "versions", package],
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            logger.error("pip index failed for %s: %s", package, e.stderr)
            raise VersionScannerError(f"pip index failed for {package}")

        lines = result.stdout.splitlines()
        for line in lines:
            line = line.strip()
            if line.startswith("Available versions:"):
                versions = (
                    line.replace("Available versions:", "")
                    .strip()
                    .split(", ")
                )
                latest = versions[0]
                return latest

        raise VersionScannerError(f"No version info found for {package}")

    # ------------------------------------------------------------------
    # Update classification
    # ------------------------------------------------------------------
    def _classify_update(self, declared: Optional[str], latest: str) -> str:
        """
        Classify patch/minor/major update using packaging.version.
        """
        try:
            latest_v = Version(latest)
        except InvalidVersion:
            return "none"

        if not declared:
            return "none"

        # extract declared version specifier like >=1.0, ==2.3
        # we take the version part after operators
        for op in ["==", ">=", "<=", "~=", "!=", "<", ">"]:
            if op in declared:
                declared_raw = declared.split(op)[-1].strip()
                break
        else:
            declared_raw = declared.strip()

        try:
            current_v = Version(declared_raw)
        except InvalidVersion:
            return "none"

        if latest_v <= current_v:
            return "none"

        if latest_v.major > current_v.major:
            return "major"
        if latest_v.minor > current_v.minor:
            return "minor"
        if latest_v.micro > current_v.micro:
            return "patch"

        return "none"
