from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from depup.utils.logging_config import configure_logging
from depup.core.parser import DependencyParser
from depup.core.version_scanner import VersionScanner, VersionScannerError
from depup.core.upgrade_executor import UpgradeExecutor, PlannedUpgrade

app = typer.Typer(help="Dependency Upgrade Advisor CLI")
console = Console()


@app.callback()
def main(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """
    Entry point for the depup CLI.
    """
    configure_logging(verbose=verbose)


@app.command("scan")
def scan(
    path: Optional[Path] = typer.Argument(
        None,
        dir_okay=True,
        readable=True,
        help="Project root directory (defaults to current working directory).",
    ),
    latest: bool = typer.Option(
        False,
        "--latest",
        help="Lookup latest versions on PyPI and show update type.",
    ),
) -> None:
    """
    Scan the project dependency files and list discovered dependencies.

    Use --latest to also query PyPI for the latest available versions and
    classify each update as patch/minor/major/none.
    """
    project_root = path or Path.cwd()

    parser = DependencyParser(project_root)
    deps = parser.parse_all()

    if not deps:
        console.print(
            "[yellow]No dependency files found or no dependencies parsed.[/yellow]"
        )
        raise typer.Exit(0)

    if latest:
        scanner = VersionScanner()
        try:
            infos = scanner.scan(deps)
        except VersionScannerError as exc:
            console.print(f"[red]Failed to scan versions: {exc}[/red]")
            raise typer.Exit(code=1)

        info_by_name = {info.name.lower(): info for info in infos}

        table = Table(title="Declared Dependencies (with latest versions)")
        table.add_column("Package Name", style="cyan")
        table.add_column("Declared Spec", style="green")
        table.add_column("Latest Version", style="yellow")
        table.add_column("Update Type", style="red")
        table.add_column("Source File", style="magenta")

        for dep in deps:
            info = info_by_name.get(dep.name.lower())
            latest_version = info.latest if info else ""
            update_type = info.update_type if info else "none"
            declared = dep.version or ""
            table.add_row(
                dep.name,
                declared,
                latest_version,
                update_type,
                dep.source_file.name,
            )
    else:
        table = Table(title="Declared Dependencies")
        table.add_column("Package Name", style="cyan")
        table.add_column("Version Spec", style="green")
        table.add_column("Source File", style="magenta")

        for dep in deps:
            version_spec = dep.version or ""
            table.add_row(dep.name, version_spec, dep.source_file.name)

    console.print(table)


@app.command("upgrade")
def upgrade(
    path: Optional[Path] = typer.Argument(
        None,
        dir_okay=True,
        readable=True,
        help="Project root directory (defaults to current working directory).",
    ),
    only_patch: bool = typer.Option(
        False,
        "--only-patch",
        help="Apply only patch-level updates.",
    ),
    only_minor: bool = typer.Option(
        False,
        "--only-minor",
        help="Apply only minor-level updates.",
    ),
    only_major: bool = typer.Option(
        False,
        "--only-major",
        help="Apply only major-level updates.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be upgraded without making any changes.",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Run non-interactively; do not prompt for confirmation.",
    ),
    packages: Optional[List[str]] = typer.Argument(
        None,
        help="Optional list of specific packages to upgrade.",
    ),
) -> None:
    """
    Upgrade outdated dependencies.

    By default, all available updates (patch/minor/major) are applied.
    Use --only-* flags and package names to restrict the scope.
    """
    project_root = path or Path.cwd()
    parser = DependencyParser(project_root)
    deps = parser.parse_all()

    if not deps:
        console.print("[yellow]No dependencies found to upgrade.[/yellow]")
        raise typer.Exit(0)

    scanner = VersionScanner()
    try:
        infos = scanner.scan(deps)
    except VersionScannerError as exc:
        console.print(f"[red]Failed to scan versions: {exc}[/red]")
        raise typer.Exit(code=1)

    pkg_filter = {p.lower() for p in packages} if packages else None

    def selected(info) -> bool:
        if info.update_type == "none":
            return False
        if pkg_filter and info.name.lower() not in pkg_filter:
            return False
        if only_patch and info.update_type != "patch":
            return False
        if only_minor and info.update_type != "minor":
            return False
        if only_major and info.update_type != "major":
            return False
        return True

    selected_infos = [i for i in infos if selected(i)]

    if not selected_infos:
        console.print("[green]No matching upgrades found.[/green]")
        raise typer.Exit(0)

    # Build plan objects
    plans: List[PlannedUpgrade] = []
    for info in selected_infos:
        dep_spec = next(
            (d for d in deps if d.name.lower() == info.name.lower()),
            None,
        )
        source_file = dep_spec.source_file if dep_spec else project_root / "requirements.txt"
        plans.append(
            PlannedUpgrade(
                name=info.name,
                current_spec=info.current,
                target_version=info.latest,
                source_file=source_file,
            )
        )

    # Show plan
    table = Table(title="Planned Upgrades (dry-run)" if dry_run else "Planned Upgrades")
    table.add_column("Package", style="cyan")
    table.add_column("Current Spec", style="green")
    table.add_column("Target Version", style="yellow")
    table.add_column("Update Type", style="red")
    table.add_column("Source File", style="magenta")

    info_by_name = {i.name.lower(): i for i in selected_infos}

    for plan in plans:
        info = info_by_name.get(plan.name.lower())
        update_type = info.update_type if info else ""
        table.add_row(
            plan.name,
            plan.current_spec or "",
            plan.target_version,
            update_type,
            plan.source_file.name,
        )

    console.print(table)

    if not dry_run and not yes:
        proceed = typer.confirm("Proceed with these upgrades?")
        if not proceed:
            console.print("[yellow]Aborted by user.[/yellow]")
            raise typer.Exit(0)

    executor = UpgradeExecutor(project_root, deps)
    results = executor.execute(plans, dry_run=dry_run)

    # Summary
    succeeded = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    console.print()
    console.print(
        f"[green]Upgrades succeeded: {len(succeeded)}[/green], "
        f"[red]failed: {len(failed)}[/red]"
    )

    if failed:
        for r in failed:
            console.print(f"[red]- {r.name}: {r.error}[/red]")
