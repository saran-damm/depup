"""
Version Scanner

Responsible for:
- Fetching latest versions from PyPI
- Comparing declared vs latest versions
- Classifying update types safely
"""

from __future__ import annotations

import concurrent.futures
import logging
from typing import List, Optional

import requests
from packaging.version import InvalidVersion, Version, parse as parse_version

from depup.core.models import DependencySpec, VersionInfo, UpdateType

logger = logging.getLogger(__name__)


class VersionScannerError(Exception):
    """Raised when a fatal version scanning error occurs."""


class VersionScanner:
    PYPI_URL = "https://pypi.org/pypi/{package}/json"
    TIMEOUT = 5
    MAX_WORKERS = 10

    IGNORE = {
        "pip",
        "setuptools",
        "wheel",
        "pkginfo",
        "distlib",
        "virtualenv",
        "pip-tools",
        "typing-extensions",
        "charset-normalizer",
        "idna",
        "urllib3",
    }

    def __init__(self) -> None:
        self._session = requests.Session()

    def scan(self, deps: List[DependencySpec]) -> List[VersionInfo]:
        filtered = [d for d in deps if d.name.lower() not in self.IGNORE]
        results: List[VersionInfo] = []

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.MAX_WORKERS
        ) as executor:
            futures = {
                executor.submit(self._fetch_version_info, dep): dep
                for dep in filtered
            }

            for future in concurrent.futures.as_completed(futures):
                info = future.result()
                if info:
                    results.append(info)

        return results

    def _fetch_version_info(self, dep: DependencySpec) -> VersionInfo:
        pkg = dep.name

        try:
            response = self._session.get(
                self.PYPI_URL.format(package=pkg),
                timeout=self.TIMEOUT,
            )
        except Exception as exc:
            logger.warning("Network error fetching %s: %s", pkg, exc)
            return self._safe_info(dep)

        if response.status_code != 200:
            return self._safe_info(dep)

        try:
            data = response.json()
            latest = data["info"].get("version")
        except Exception as exc:
            logger.warning("Invalid JSON for %s: %s", pkg, exc)
            return self._safe_info(dep)

        update_type = self._classify(dep.version, latest)

        return VersionInfo(
            name=pkg,
            current=self._normalize_declared(dep.version),
            latest=latest,
            update_type=update_type,
        )

    def _safe_info(self, dep: DependencySpec) -> VersionInfo:
        """
        Return a safe fallback VersionInfo when resolution fails.
        """
        return VersionInfo(
            name=dep.name,
            current=self._normalize_declared(dep.version),
            latest=None,
            update_type=UpdateType.NONE,
        )

    def _normalize_declared(self, version: Optional[str]) -> Optional[str]:
        if not version:
            return None

        version = version.strip()
        for op in ("==", ">=", "<=", "~=", ">", "<"):
            if version.startswith(op):
                return version[len(op):].strip()

        return version

    def _classify(
        self,
        current: Optional[str],
        latest: Optional[str],
    ) -> UpdateType:
        if not current or not latest:
            return UpdateType.NONE

        try:
            current_v = parse_version(current)
            latest_v = parse_version(latest)
        except InvalidVersion:
            return UpdateType.NONE

        if not isinstance(current_v, Version) or not isinstance(latest_v, Version):
            return UpdateType.NONE

        if latest_v <= current_v:
            return UpdateType.NONE

        if latest_v.major > current_v.major:
            return UpdateType.MAJOR
        if latest_v.minor > current_v.minor:
            return UpdateType.MINOR
        return UpdateType.PATCH
