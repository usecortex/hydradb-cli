"""HydraDB CLI — Agent-friendly command line interface for HydraDB.

The context layer for AI. Manage memories, recall context, and ingest
knowledge from the terminal.

Usage:
    hydradb <command> [options]

Commands are organized by resource:
    login/logout/whoami  Authentication
    tenant               Tenant management
    memories             User memory operations
    knowledge            Knowledge base ingestion
    recall               Context retrieval (full, preferences, keyword)
    fetch                Inspect stored data and relations
    config               CLI configuration
"""

from typing import Optional

import typer

from hydradb_cli import __version__
from hydradb_cli.commands import auth, config_cmd, fetch, knowledge, memories, recall, tenant
from hydradb_cli.output import console, set_output_format

app = typer.Typer(
    name="hydradb",
    help=(
        "[bold cyan]///[/bold cyan] HydraDB CLI\n\n"
        "The context layer for AI — manage memories, recall context, "
        "and ingest knowledge from the terminal."
    ),
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def _version_callback(value: bool) -> None:
    if value:
        console.print(
            f"[bold cyan]///[/bold cyan] [bold]hydradb-cli[/bold] {__version__}"
        )
        raise typer.Exit()


@app.callback()
def main(
    output: str = typer.Option(
        "human",
        "--output",
        "-o",
        help="Output format: 'human' (default) or 'json'.",
        envvar="HYDRADB_OUTPUT",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """[bold cyan]///[/bold cyan] HydraDB CLI — The context layer for AI, from the terminal."""
    if output not in ("human", "json"):
        typer.echo(f"Error: --output must be 'human' or 'json', got '{output}'", err=True)
        raise typer.Exit(code=1)
    set_output_format(output)


app.command(name="login", help="Authenticate with HydraDB and save credentials.")(auth.login)
app.command(name="logout", help="Remove stored credentials.")(auth.logout)
app.command(name="whoami", help="Show current authentication status.")(auth.whoami)

app.add_typer(tenant.app, name="tenant", help="[bold]Tenant[/bold] management.")
app.add_typer(memories.app, name="memories", help="[bold]Memory[/bold] operations.")
app.add_typer(knowledge.app, name="knowledge", help="[bold]Knowledge[/bold] base ingestion.")
app.add_typer(recall.app, name="recall", help="[bold]Context[/bold] retrieval.")
app.add_typer(fetch.app, name="fetch", help="[bold]Inspect[/bold] stored data and relations.")
app.add_typer(config_cmd.app, name="config", help="CLI [bold]configuration[/bold].")


if __name__ == "__main__":
    app()
