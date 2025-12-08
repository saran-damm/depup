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

import concurrent.futures
import requests
from typing import List, Optional
from packaging.version import parse as parse_version

from depup.core.models import DependencySpec, VersionInfo


class VersionScannerError(Exception):
    pass


class VersionScanner:
    PYPI_URL = "https://pypi.org/pypi/{package}/json"
    TIMEOUT = 5
    MAX_WORKERS = 10

    IGNORE = {
        "pip", "setuptools", "wheel", "pkginfo",
        "distlib", "virtualenv", "pip-tools",
        "typing-extensions", "charset-normalizer",
        "idna", "urllib3",
    }

    def scan(self, deps: List[DependencySpec]) -> List[VersionInfo]:
        deps = [d for d in deps if d.name.lower() not in self.IGNORE]

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            future_map = {
                executor.submit(self._fetch_version_info, dep): dep
                for dep in deps
            }

            for future in concurrent.futures.as_completed(future_map):
                dep = future_map[future]
                try:
                    info = future.result()
                except Exception as exc:
                    raise VersionScannerError(f"Failed to scan {dep.name}: {exc}")
                if info:
                    results.append(info)

        return results

    def _fetch_version_info(self, dep: DependencySpec) -> Optional[VersionInfo]:
        pkg = dep.name

        try:
            response = requests.get(
                self.PYPI_URL.format(package=pkg),
                timeout=self.TIMEOUT,
            )
        except Exception as exc:
            raise RuntimeError(f"Network error fetching {pkg}: {exc}")

        if response.status_code != 200:
            return VersionInfo(pkg, dep.version or "", "", "none")

        data = response.json()

        # 🚀 ALWAYS USE info.version (the PEP440-canonical latest version)
        latest = data["info"].get("version", "")

        update_type = self._classify(dep.version, latest)

        return VersionInfo(pkg, dep.version or "", latest, update_type)
    
    def _normalize_declared(self, version: Optional[str]) -> Optional[str]:
        if not version:
            return None

        # Remove specifier operators like ==, >=, <=, ~=
        for op in ("==", ">=", "<=", "~=", ">", "<"):
            if version.startswith(op):
                return version[len(op):]

        # In case there are spaces or weird formatting
        return version.strip()


    def _classify(self, current: Optional[str], latest: str) -> str:
        current = self._normalize_declared(current)

        if not current:
            return "major"

        try:
            c = parse_version(current)
            l = parse_version(latest)
        except Exception:
            return "major"

        if l <= c:
            return "none"

        # Major/minor/patch logic
        if getattr(l, "major", None) > getattr(c, "major", None):
            return "major"
        if getattr(l, "minor", None) > getattr(c, "minor", None):
            return "minor"
        return "patch"

