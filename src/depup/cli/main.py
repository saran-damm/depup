from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Set

import typer
from rich.console import Console
from rich.table import Table

from depup.utils.logging_config import configure_logging

from depup.core.parsers.declaration_parser import DependencyParser
from depup.core.parsers.poetry_lock_parser import PoetryLockParser
from depup.core.parsers.pipfile_lock_parser import PipfileLockParser

from depup.core.environment_scanner import EnvironmentScanner
from depup.core.version_scanner import VersionScanner, VersionScannerError
from depup.core.upgrade_executor import UpgradeExecutor, PlannedUpgrade
from depup.core.models import VersionInfo, UpdateType

from depup.utils.render import (
    render_env_upgrade_table,
    render_file_upgrade_table,
    render_upgrade_summary,
    render_latest_env_table,
    render_env_table,
    render_latest_file_table,
    render_declared_file_table,
)

from depup.utils.upgrade_planner import build_upgrade_plans

from depup.utils.scan_utils import _has_outdated, _convert_to_jsonable
from depup.utils.upgrade_utils import (
    _perform_env_upgrades,
    select_upgradable_versions
)
from depup.utils.report_utils import generate_markdown_report

app = typer.Typer(help="Dependency Upgrade Advisor CLI")
console = Console()


# ---------------------------------------------------------------------
# GLOBAL CALLBACK
# ---------------------------------------------------------------------
@app.callback(invoke_without_command=True)
def main_callback(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """Global CLI entrypoint."""
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

    if check and not latest:
        console.print("[red]--check requires --latest[/red]")
        raise typer.Exit(2)

    # =========================================================
    # ENVIRONMENT MODE
    # =========================================================
    if env:
        console.print("[blue]Scanning installed environment packages...[/blue]")

        deps = EnvironmentScanner().scan()

        if not deps:
            console.print("[yellow]No installed packages detected.[/yellow]")
            raise typer.Exit(0)

        infos = _scan_versions(deps, latest)

        _render_scan_output(
            deps=deps,
            infos=infos,
            latest=latest,
            json_output=json_output,
            env=True,
        )

        if report:
            generate_markdown_report(
                output_path=report,
                deps=deps,
                infos=infos,
                title="Environment Dependency Report",
            )
            console.print(f"[green]Markdown report written to {report}[/green]")

        _exit_check_mode(infos, check)

    # =========================================================
    # FILE-BASED MODE
    # =========================================================
    project_root = path or Path.cwd()

    deps = DependencyParser(project_root).parse_all()
    deps.extend(PoetryLockParser(project_root).parse())
    deps.extend(PipfileLockParser(project_root).parse())

    if not deps:
        console.print(
            "[yellow]No dependency files found.[/yellow]\n"
            "Try:\n"
            "  • depup scan --env\n"
            "  • depup init (coming soon)\n"
        )
        raise typer.Exit(0)

    infos = _scan_versions(deps, latest)

    _render_scan_output(
        deps=deps,
        infos=infos,
        latest=latest,
        json_output=json_output,
        env=False,
    )

    if report:
        generate_markdown_report(
            output_path=report,
            deps=deps,
            infos=infos,
            title="Project Dependency Report",
        )
        console.print(f"[green]Markdown report written to {report}[/green]")

    _exit_check_mode(infos, check)


# ---------------------------------------------------------------------
# UPGRADE COMMAND
# ---------------------------------------------------------------------
@app.command("upgrade")
def upgrade_command(
    path: Optional[Path] = typer.Argument(
        None,
        help="Project root directory (defaults to current working directory).",
    ),
    only_patch: bool = typer.Option(False, "--only-patch"),
    only_minor: bool = typer.Option(False, "--only-minor"),
    only_major: bool = typer.Option(False, "--only-major"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    yes: bool = typer.Option(False, "--yes", "-y"),
    env: bool = typer.Option(False, "--env"),
    packages: Optional[List[str]] = typer.Argument(None),
) -> None:
    """
    Upgrade outdated dependencies.
    """

    pkg_filter: Optional[Set[str]] = {p.lower() for p in packages} if packages else None

    # =========================================================
    # ENVIRONMENT MODE
    # =========================================================
    if env:
        deps = EnvironmentScanner().scan()
        infos = VersionScanner().scan(deps)

        selected = select_upgradable_versions(
            infos,
            pkg_filter,
            only_patch,
            only_minor,
            only_major,
        )

        if not selected:
            console.print("[green]All environment packages are up to date![/green]")
            raise typer.Exit(0)

        render_env_upgrade_table(selected)

        if not (yes or dry_run) and not typer.confirm("Proceed with upgrades?"):
            raise typer.Exit(0)

        _perform_env_upgrades(selected, dry_run=dry_run)
        raise typer.Exit(0)

    # =========================================================
    # FILE-BASED MODE
    # =========================================================
    project_root = path or Path.cwd()
    deps = DependencyParser(project_root).parse_all()

    infos = VersionScanner().scan(deps)

    selected = select_upgradable_versions(
        infos,
        pkg_filter,
        only_patch,
        only_minor,
        only_major,
    )

    if not selected:
        console.print("[green]No matching upgrades found.[/green]")
        raise typer.Exit(0)

    plans = build_upgrade_plans(selected, deps, project_root)
    render_file_upgrade_table(plans, selected, dry_run)

    if not (yes or dry_run) and not typer.confirm("Proceed with upgrades?"):
        raise typer.Exit(0)

    results = UpgradeExecutor(project_root, deps).execute(plans, dry_run=dry_run)
    render_upgrade_summary(results)


# ---------------------------------------------------------------------
# INTERNAL HELPERS (CLI-SAFE)
# ---------------------------------------------------------------------
def _scan_versions(deps, latest: bool) -> List[VersionInfo]:
    if not latest:
        return [
            VersionInfo(
                name=d.name,
                current=d.version,
                latest=d.version,
                update_type=UpdateType.NONE,
            )
            for d in deps
        ]
    try:
        return VersionScanner().scan(deps)
    except VersionScannerError as exc:
        console.print(f"[red]Failed to scan versions: {exc}[/red]")
        raise typer.Exit(1)


def _render_scan_output(*, deps, infos, latest, json_output, env: bool) -> None:
    if json_output:
        console.print_json(data=_convert_to_jsonable(deps, infos))
        return

    if env:
        render_latest_env_table(deps, infos) if latest else render_env_table(deps)
    else:
        render_latest_file_table(deps, infos) if latest else render_declared_file_table(deps)


def _exit_check_mode(infos: List[VersionInfo], check: bool) -> None:
    if check:
        raise typer.Exit(1 if _has_outdated(infos) else 0)
    raise typer.Exit(0)
