import typer
from pathlib import Path
from typing import Optional
from rich.table import Table
from rich.console import Console

from depup.utils.logging_config import configure_logging
from depup.core.parser import DependencyParser

app = typer.Typer(help="Dependency Upgrade Advisor CLI")
console = Console()


@app.callback()
def main(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    )
):
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
    )
):
    """
    Scan the project dependency files and list discovered dependencies.
    """
    project_root = path or Path.cwd()

    parser = DependencyParser(project_root)
    deps = parser.parse_all()

    if not deps:
        console.print("[yellow]No dependency files found or no dependencies parsed.[/yellow]")
        raise typer.Exit(0)

    table = Table(title="Declared Dependencies")
    table.add_column("Package Name", style="cyan")
    table.add_column("Version Spec", style="green")
    table.add_column("Source File", style="magenta")

    for dep in deps:
        version = dep.version if dep.version else ""
        table.add_row(dep.name, version, str(dep.source_file.name))

    console.print(table)
