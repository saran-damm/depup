from __future__ import annotations

from pathlib import Path
from typing import List

from rich.console import Console
from rich.table import Table

from depup.core.models import DependencySpec, VersionInfo, UpdateType
from depup.core.upgrade_executor import PlannedUpgrade, UpgradeResult

console = Console()


# ---------------------------------------------------------------------
# TABLE RENDERERS
# ---------------------------------------------------------------------
def render_env_upgrade_table(infos: List[VersionInfo]) -> None:
    table = Table(title="Environment Upgrade Plan")
    table.add_column("Package", style="cyan")
    table.add_column("Current", style="green")
    table.add_column("Latest", style="yellow")
    table.add_column("Update Type", style="red")

    for info in infos:
        table.add_row(info.name, info.current, info.latest, info.update_type)

    console.print(table)


def render_file_upgrade_table(plans: List[PlannedUpgrade], infos: List[VersionInfo], dry_run: bool) -> None:
    table = Table(title="Planned Upgrades (dry-run)" if dry_run else "Planned Upgrades")
    table.add_column("Package", style="cyan")
    table.add_column("Current Spec", style="green")
    table.add_column("Target Version", style="yellow")
    table.add_column("Update Type", style="red")
    table.add_column("Source File", style="magenta")

    info_by_name = {i.name.lower(): i for i in infos}

    for plan in plans:
        info = info_by_name.get(plan.name.lower())
        table.add_row(
            plan.name,
            plan.current_spec or "",
            plan.target_version,
            info.update_type if info else "unknown",
            plan.source_file.name,
        )

    console.print(table)


# ---------------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------------
def render_upgrade_summary(results: List[UpgradeResult]) -> None:
    succeeded = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    console.print()
    console.print(
        f"[green]Upgrades succeeded: {len(succeeded)}[/green], "
        f"[red]failed: {len(failed)}[/red]"
    )

    for r in failed:
        console.print(f"[red]- {r.name}: {r.error}[/red]")


# ---------------------------------------------------------------------
# ENVIRONMENT TABLES
# ---------------------------------------------------------------------
def render_env_table(deps: List[DependencySpec]) -> None:
    table = Table(title="Installed Environment Packages")
    table.add_column("Package", style="cyan")
    table.add_column("Version", style="green")

    for dep in deps:
        table.add_row(dep.name, dep.version or "")

    console.print(table)


def render_latest_env_table(deps: List[DependencySpec], infos: List[VersionInfo]) -> None:
    info_by_name = {i.name.lower(): i for i in infos}

    table = Table(title="Installed Packages (with latest versions)")
    table.add_column("Package", style="cyan")
    table.add_column("Installed", style="green")
    table.add_column("Latest", style="yellow")
    table.add_column("Update Type", style="red")

    for dep in deps:
        info = info_by_name.get(dep.name.lower())
        table.add_row(
            dep.name,
            dep.version or "",
            info.latest if info else "",
            info.update_type if info else UpdateType.NONE,
        )

    console.print(table)


# ---------------------------------------------------------------------
# FILE-BASED TABLES
# ---------------------------------------------------------------------
def render_declared_file_table(deps: List[DependencySpec]) -> None:
    table = Table(title="Declared Dependencies")
    table.add_column("Package", style="cyan")
    table.add_column("Version Spec", style="green")
    table.add_column("Source File", style="magenta")

    for dep in deps:
        table.add_row(dep.name, dep.version or "", dep.source_file.name)

    console.print(table)


def render_latest_file_table(deps: List[DependencySpec], infos: List[VersionInfo]) -> None:
    info_by_name = {i.name.lower(): i for i in infos}

    table = Table(title="Declared Dependencies (with latest versions)")
    table.add_column("Package", style="cyan")
    table.add_column("Declared Spec", style="green")
    table.add_column("Latest Version", style="yellow")
    table.add_column("Update Type", style="red")
    table.add_column("Source File", style="magenta")

    for dep in deps:
        info = info_by_name.get(dep.name.lower())
        table.add_row(
            dep.name,
            dep.version or "",
            info.latest if info else "",
            info.update_type if info else UpdateType.NONE,
            dep.source_file.name,
        )

    console.print(table)
