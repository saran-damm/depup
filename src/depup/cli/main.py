from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from depup.utils.logging_config import configure_logging
from depup.core.parser import DependencyParser
from depup.core.version_scanner import VersionScanner, VersionScannerError

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

    version_info_by_name = {}

    if latest:
        scanner = VersionScanner()
        try:
            infos = scanner.scan(deps)
        except VersionScannerError as exc:
            console.print(f"[red]Failed to scan versions: {exc}[/red]")
            raise typer.Exit(code=1)

        # Index by lowercase package name
        version_info_by_name = {info.name.lower(): info for info in infos}

        table = Table(title="Declared Dependencies (with latest versions)")
        table.add_column("Package Name", style="cyan")
        table.add_column("Declared Spec", style="green")
        table.add_column("Latest Version", style="yellow")
        table.add_column("Update Type", style="red")
        table.add_column("Source File", style="magenta")

        for dep in deps:
            info = version_info_by_name.get(dep.name.lower())
            latest_version = info.latest if info else ""
            update_type = info.update_type if info else "none"
            declared = dep.version or ""
            table.add_row(dep.name, declared, latest_version, update_type, dep.source_file.name)

    else:
        table = Table(title="Declared Dependencies")
        table.add_column("Package Name", style="cyan")
        table.add_column("Version Spec", style="green")
        table.add_column("Source File", style="magenta")

        for dep in deps:
            version_spec = dep.version or ""
            table.add_row(dep.name, version_spec, dep.source_file.name)

    console.print(table)
