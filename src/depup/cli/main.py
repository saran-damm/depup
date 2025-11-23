import typer
from depup.utils.logging_config import configure_logging

app = typer.Typer(help="Dependency Upgrade Advisor CLI")

@app.callback()
def main(verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")):
    """
    Entry point for the depup CLI.
    """
    configure_logging(verbose=verbose)
