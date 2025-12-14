from __future__ import annotations
from typing import Iterable, List, Optional, Set
from depup.core.models import VersionInfo, UpdateType
from rich.console import Console

console = Console()

def select_upgradable_versions(
    infos: Iterable[VersionInfo],
    pkg_filter: Optional[Set[str]] = None,
    only_patch: bool = False,
    only_minor: bool = False,
    only_major: bool = False,
) -> List[VersionInfo]:
    """
    Filter VersionInfo objects based on update type and optional package constraints.

    Args:
        infos: Iterable of VersionInfo objects to filter.
        pkg_filter: Optional set of package names (lowercase) to include.
        only_patch: Include only patch-level updates.
        only_minor: Include only minor-level updates.
        only_major: Include only major-level updates.

    Returns:
        A list of VersionInfo objects matching the criteria.
    """

    allowed_update_types = _resolve_allowed_update_types(
        only_patch=only_patch,
        only_minor=only_minor,
        only_major=only_major,
    )

    selected: List[VersionInfo] = []

    for info in infos:
        # Skip already up-to-date packages
        if info.update_type == UpdateType.NONE:
            continue

        # Package filter (if provided)
        if pkg_filter and info.name.lower() not in pkg_filter:
            continue

        # Update-type filter
        if info.update_type not in allowed_update_types:
            continue

        selected.append(info)

    return selected


def _resolve_allowed_update_types(
    *,
    only_patch: bool,
    only_minor: bool,
    only_major: bool,
) -> Set[UpdateType]:
    """
    Determine which update types are allowed based on CLI flags.

    If no flags are provided, all update types are allowed.
    """

    if not (only_patch or only_minor or only_major):
        return {
            UpdateType.PATCH,
            UpdateType.MINOR,
            UpdateType.MAJOR,
        }

    allowed: Set[UpdateType] = set()

    if only_patch:
        allowed.add(UpdateType.PATCH)
    if only_minor:
        allowed.add(UpdateType.MINOR)
    if only_major:
        allowed.add(UpdateType.MAJOR)

    return allowed


def _perform_env_upgrades(infos: List[VersionInfo], dry_run: bool = False):
    import subprocess

    for info in infos:
        pkg = info.name
        target = info.latest

        if dry_run:
            console.print(f"[cyan]Would upgrade {pkg} → {target}[/cyan]")
            continue

        console.print(f"[blue]Upgrading {pkg} → {target}...[/blue]")

        try:
            subprocess.run(
                ["pip", "install", "-U", f"{pkg}=={target}"],
                check=True,
            )
            console.print(f"[green]✓ {pkg} upgraded successfully[/green]")
        except subprocess.CalledProcessError as exc:
            console.print(f"[red]✗ Failed to upgrade {pkg}: {exc}[/red]")

__all__ = [
    "_perform_env_upgrades",
    "select_upgradable_versions",
    
]