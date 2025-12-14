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
from depup.core.environment_scanner import EnvironmentScanner
from depup.core.models import VersionInfo, UpdateType
from depup.core.poetry_lock_parser import PoetryLockParser
from depup.core.pipfile_lock_parser import PipfileLockParser
from depup.utils.report_utils import generate_markdown_report

from depup.utils.render import *
from depup.utils.upgrade_utils import *
from depup.utils.scan_utils import *

app = typer.Typer(help="Dependency Upgrade Advisor CLI")
console = Console()


@app.callback()
def main_callback(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """Main entry point."""
    configure_logging(verbose=verbose)


# ---------------------------------------------------------------------
# SCAN COMMAND
# ---------------------------------------------------------------------
@app.command("scan")
def scan_command(
    path: Optional[Path] = typer.Argument(
        None,
        help="Project root directory (defaults to current working directory).",
    ),
    latest: bool = typer.Option(
        False,
        "--latest",
        help="Lookup latest versions on PyPI and classify update types.",
    ),
    env: bool = typer.Option(
        False,
        "--env",
        help="Scan installed environment instead of dependency files.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output results in JSON format instead of table.",
    ),
    check: bool = typer.Option(
        False,
        "--check",
        help="Exit with non-zero status if outdated dependencies are found.",
    ),
    report: Optional[Path] = typer.Option(
        None,
        "--report",
        help="Write scan results to a Markdown report file.",
    ),
) -> None:
    """
    Scan dependency files or installed environment for outdated dependencies.
    """

    # Enforce check requires latest
    if check and not latest:
        console.print("[red]--check requires --latest[/red]")
        raise typer.Exit(2)

    # ---------------------------------------------------------
    # ENVIRONMENT MODE
    # ---------------------------------------------------------
    if env:
        console.print("[blue]Scanning installed environment packages...[/blue]")

        scanner = EnvironmentScanner()
        deps = scanner.scan()

        if not deps:
            console.print("[yellow]No installed packages detected.[/yellow]")
            raise typer.Exit(0)

        if latest:
            version_scanner = VersionScanner()
            try:
                infos = version_scanner.scan(deps)
            except VersionScannerError as exc:
                console.print(f"[red]Failed to scan versions: {exc}[/red]")
                raise typer.Exit(1)
        else:
            infos = [
                VersionInfo(
                    name=d.name,
                    current=d.version,
                    latest=d.version,
                    update_type=UpdateType.NONE,
                )
                for d in deps
            ]

        # JSON OUTPUT
        if json_output:
            console.print_json(data=_convert_to_jsonable(deps, infos))
        else:
            if latest:
                _render_latest_env_table(deps, infos)
            else:
                _render_env_table(deps)

        if report:
            generate_markdown_report(
                output_path=report,
                deps=deps,
                infos=infos,
                title="Environment Dependency Report",
            )
            console.print(f"[green]Markdown report written to {report}[/green]")

        # CHECK MODE
        if check:
            if _has_outdated(infos):
                raise typer.Exit(1)
            raise typer.Exit(0)

        raise typer.Exit(0)

    # ---------------------------------------------------------
    # FILE-BASED MODE
    # ---------------------------------------------------------
    project_root = path or Path.cwd()
    parser = DependencyParser(project_root)
    deps = parser.parse_all()

    # Poetry lockfile (read-only)
    poetry_parser = PoetryLockParser(project_root)
    poetry_deps = poetry_parser.parse()
    if poetry_deps:
        deps.extend(poetry_deps)

    # Pipfile.lock (read-only)
    pipfile_parser = PipfileLockParser(project_root)
    pipfile_deps = pipfile_parser.parse()
    if pipfile_deps:
        deps.extend(pipfile_deps)

    if not deps:
        console.print(
            "[yellow]No dependency files found.[/yellow]\n"
            "Try:\n"
            "  • depup scan --env\n"
            "  • depup init (coming soon)\n"
        )
        raise typer.Exit(0)

    if latest:
        version_scanner = VersionScanner()
        try:
            infos = version_scanner.scan(deps)
        except VersionScannerError as exc:
            console.print(f"[red]Failed to scan versions: {exc}[/red]")
            raise typer.Exit(1)
    else:
        infos = [
            VersionInfo(
                name=d.name,
                current=d.version,
                latest=d.version,
                update_type=UpdateType.NONE,
            )
            for d in deps
        ]

    # JSON OUTPUT
    if json_output:
        console.print_json(data=_convert_to_jsonable(deps, infos))
    else:
        if latest:
            _render_latest_file_table(deps, infos)
        else:
            _render_declared_file_table(deps)

    if report:
        generate_markdown_report(
            output_path=report,
            deps=deps,
            infos=infos,
            title="Project Dependency Report",
        )
        console.print(f"[green]Markdown report written to {report}[/green]")

    # CHECK MODE
    if check:
        if _has_outdated(infos):
            raise typer.Exit(1)
        raise typer.Exit(0)


# ---------------------------------------------------------------------
# UPGRADE COMMAND
# ---------------------------------------------------------------------
@app.command("upgrade")
def upgrade_command(
    path: Optional[Path] = typer.Argument(
        None,
        help="Project root directory (defaults to current working directory).",
    ),
    only_patch: bool = typer.Option(False, "--only-patch", help="Upgrade only patch-level updates."),
    only_minor: bool = typer.Option(False, "--only-minor", help="Upgrade only minor-level updates."),
    only_major: bool = typer.Option(False, "--only-major", help="Upgrade only major-level updates."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show upgrades without applying them."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts."),
    env: bool = typer.Option(False, "--env", help="Upgrade installed environment packages instead of project files."),
    packages: Optional[List[str]] = typer.Argument(
        None,
        help="Optional list of package names to upgrade.",
    ),
) -> None:
    """
    Upgrade outdated dependencies.

    Supports:
      - File-based upgrades
      - Environment upgrades (--env)
    """

    pkg_filter = {p.lower() for p in packages} if packages else None

    # =========================================================
    # ENVIRONMENT MODE
    # =========================================================
    if env:
        console.print("[blue]Scanning installed environment packages...[/blue]")

        env_scanner = EnvironmentScanner()
        deps = env_scanner.scan()

        if not deps:
            console.print("[yellow]No installed packages found.[/yellow]")
            raise typer.Exit(0)

        version_scanner = VersionScanner()
        try:
            infos = version_scanner.scan(deps)
        except VersionScannerError as exc:
            console.print(f"[red]Failed to scan versions: {exc}[/red]")
            raise typer.Exit(1)

        outdated = [
            i
            for i in infos
            if i.update_type != UpdateType.NONE and (not pkg_filter or i.name.lower() in pkg_filter)
        ]

        if not outdated:
            console.print("[green]All environment packages are up to date![/green]")
            raise typer.Exit(0)

        table = Table(title="Environment Upgrade Plan")
        table.add_column("Package", style="cyan")
        table.add_column("Current", style="green")
        table.add_column("Latest", style="yellow")
        table.add_column("Update Type", style="red")

        for i in outdated:
            table.add_row(i.name, i.current, i.latest, i.update_type)

        console.print(table)

        if not (yes or dry_run):
            if not typer.confirm("Proceed with upgrading environment packages?"):
                console.print("[yellow]Aborted.[/yellow]")
                raise typer.Exit(0)

        _perform_env_upgrades(outdated, dry_run=dry_run)
        raise typer.Exit(0)

    # =========================================================
    # FILE-BASED MODE
    # =========================================================
    project_root = path or Path.cwd()
    parser = DependencyParser(project_root)
    deps = parser.parse_all()

    if not deps:
        console.print("[yellow]No dependency files found to upgrade.[/yellow]")
        console.print("Try [cyan]depup upgrade --env[/cyan] to upgrade installed packages.")
        raise typer.Exit(0)

    version_scanner = VersionScanner()
    try:
        infos = version_scanner.scan(deps)
    except VersionScannerError as exc:
        console.print(f"[red]Failed to scan versions: {exc}[/red]")
        raise typer.Exit(1)

    def selected(info: VersionInfo) -> bool:
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

    plans: List[PlannedUpgrade] = []
    for info in selected_infos:
        dep_spec = next((d for d in deps if d.name.lower() == info.name.lower()), None)
        source_file = dep_spec.source_file if dep_spec else project_root / "requirements.txt"

        plans.append(
            PlannedUpgrade(
                name=info.name,
                current_spec=info.current,
                target_version=info.latest,
                source_file=source_file,
            )
        )

    table = Table(title="Planned Upgrades (dry-run)" if dry_run else "Planned Upgrades")
    table.add_column("Package", style="cyan")
    table.add_column("Current Spec", style="green")
    table.add_column("Target Version", style="yellow")
    table.add_column("Update Type", style="red")
    table.add_column("Source File", style="magenta")

    info_by_name = {i.name.lower(): i for i in selected_infos}

    for plan in plans:
        info = info_by_name.get(plan.name.lower())
        table.add_row(
            plan.name,
            plan.current_spec or "",
            plan.target_version,
            info.update_type if info else "",
            plan.source_file.name,
        )

    console.print(table)

    if not dry_run and not yes:
        if not typer.confirm("Proceed with these upgrades?"):
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit(0)

    executor = UpgradeExecutor(project_root, deps)
    results = executor.execute(plans, dry_run=dry_run)

    succeeded = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    console.print()
    console.print(
        f"[green]Upgrades succeeded: {len(succeeded)}[/green], "
        f"[red]failed: {len(failed)}[/red]"
    )

    for r in failed:
        console.print(f"[red]- {r.name}: {r.error}[/red]")
