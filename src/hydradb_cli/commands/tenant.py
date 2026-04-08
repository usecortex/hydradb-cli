"""Tenant management commands."""

import httpx
import typer
from rich.panel import Panel

from hydradb_cli.client import HydraDBClientError
from hydradb_cli.output import make_kv_table, make_table, print_error, print_result, spinner
from hydradb_cli.utils.common import get_client, handle_api_error, handle_network_error, require_tenant_id

app = typer.Typer(help="Manage tenants.")


@app.command()
def create(
    tenant_id: str = typer.Argument(help="Unique tenant identifier."),
    embeddings: bool = typer.Option(
        False,
        "--embeddings",
        help="Create as an embeddings tenant.",
    ),
    embeddings_dimension: int | None = typer.Option(
        None,
        "--embeddings-dimension",
        help="Embedding vector dimensions (required if --embeddings is set).",
    ),
) -> None:
    """Create a new tenant."""
    if not tenant_id.strip():
        print_error("Tenant ID cannot be empty.")

    if embeddings and embeddings_dimension is None:
        print_error("--embeddings-dimension is required when --embeddings is set.")

    client = get_client()
    try:
        with spinner("Creating tenant..."):
            result = client.create_tenant(
                tenant_id=tenant_id,
                is_embeddings_tenant=embeddings or None,
                embeddings_dimension=embeddings_dimension,
            )
        print_result(
            result,
            lambda r: f"[green]\u2713[/green] Tenant [bold]{tenant_id}[/bold] created successfully.",
        )
    except HydraDBClientError as e:
        handle_api_error(e)
    except httpx.RequestError as e:
        handle_network_error(e)


@app.command()
def monitor(
    tenant_id_arg: str | None = typer.Argument(
        None,
        help="Tenant ID to monitor. Uses default if not specified.",
        metavar="TENANT_ID",
    ),
    tenant_id: str | None = typer.Option(
        None,
        "--tenant-id",
        help="Tenant ID (alternative to positional argument).",
        hidden=True,
    ),
) -> None:
    """Get tenant infrastructure status and statistics."""
    tid = require_tenant_id(tenant_id or tenant_id_arg)
    client = get_client()
    try:
        with spinner("Fetching tenant stats..."):
            result = client.monitor_tenant(tid)

        def fmt(r: dict):
            if not isinstance(r, dict):
                return str(r)
            pairs = [(k, str(v)) for k, v in r.items() if k != "tenant_id"]
            table = make_kv_table(pairs)
            return Panel(
                table,
                title=f"[bold cyan]/// Tenant: {tid}[/bold cyan]",
                border_style="cyan",
                padding=(0, 1),
            )

        print_result(result, fmt)
    except HydraDBClientError as e:
        handle_api_error(e)
    except httpx.RequestError as e:
        handle_network_error(e)


@app.command("list-sub-tenants")
def list_sub_tenants(
    tenant_id_arg: str | None = typer.Argument(
        None,
        help="Tenant ID. Uses default if not specified.",
        metavar="TENANT_ID",
    ),
    tenant_id: str | None = typer.Option(
        None,
        "--tenant-id",
        help="Tenant ID (alternative to positional argument).",
        hidden=True,
    ),
) -> None:
    """List all sub-tenant IDs for a tenant."""
    tid = require_tenant_id(tenant_id or tenant_id_arg)
    client = get_client()
    try:
        with spinner("Listing sub-tenants..."):
            result = client.list_sub_tenants(tid)

        def fmt(r: dict):
            sub_ids = r.get("sub_tenant_ids", [])
            if not sub_ids:
                return f"[dim]No sub-tenants found for tenant '{tid}'.[/dim]"
            rows = [[sid] for sid in sub_ids]
            return make_table("Sub-Tenant ID", rows=rows, title=f"Sub-tenants for '{tid}'")

        print_result(result, fmt)
    except HydraDBClientError as e:
        handle_api_error(e)
    except httpx.RequestError as e:
        handle_network_error(e)


@app.command()
def delete(
    tenant_id: str = typer.Argument(help="Tenant ID to delete."),
    confirm: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt.",
    ),
) -> None:
    """Delete a tenant and all its data. This action is irreversible."""
    if not tenant_id.strip():
        print_error("Tenant ID cannot be empty.")

    if not confirm:
        typer.confirm(
            f"Are you sure you want to delete tenant '{tenant_id}' and ALL its data?",
            abort=True,
        )
    client = get_client()
    try:
        with spinner("Deleting tenant..."):
            result = client.delete_tenant(tenant_id)
        print_result(
            result,
            lambda r: f"[green]\u2713[/green] Tenant [bold]{tenant_id}[/bold] deleted.",
        )
    except HydraDBClientError as e:
        handle_api_error(e)
    except httpx.RequestError as e:
        handle_network_error(e)
