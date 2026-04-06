"""Tenant management commands."""

from typing import Optional

import httpx
import typer

from hydradb_cli.client import HydraDBClientError
from hydradb_cli.output import print_error, print_result
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
    embeddings_dimension: Optional[int] = typer.Option(
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
        result = client.create_tenant(
            tenant_id=tenant_id,
            is_embeddings_tenant=embeddings or None,
            embeddings_dimension=embeddings_dimension,
        )
        print_result(result, lambda r: f"  Tenant '{tenant_id}' created successfully.")
    except HydraDBClientError as e:
        handle_api_error(e)
    except httpx.RequestError as e:
        handle_network_error(e)


@app.command()
def monitor(
    tenant_id_arg: Optional[str] = typer.Argument(
        None, help="Tenant ID to monitor. Uses default if not specified.",
        metavar="TENANT_ID",
    ),
    tenant_id: Optional[str] = typer.Option(
        None, "--tenant-id", help="Tenant ID (alternative to positional argument).",
        hidden=True,
    ),
) -> None:
    """Get tenant infrastructure status and statistics."""
    tid = require_tenant_id(tenant_id or tenant_id_arg)
    client = get_client()
    try:
        result = client.monitor_tenant(tid)

        def fmt(r: dict) -> str:
            lines = [f"  Tenant: {tid}"]
            if isinstance(r, dict):
                for key, val in r.items():
                    if key not in ("tenant_id",):
                        lines.append(f"  {key}: {val}")
            return "\n".join(lines)

        print_result(result, fmt)
    except HydraDBClientError as e:
        handle_api_error(e)
    except httpx.RequestError as e:
        handle_network_error(e)


@app.command("list-sub-tenants")
def list_sub_tenants(
    tenant_id_arg: Optional[str] = typer.Argument(
        None, help="Tenant ID. Uses default if not specified.",
        metavar="TENANT_ID",
    ),
    tenant_id: Optional[str] = typer.Option(
        None, "--tenant-id", help="Tenant ID (alternative to positional argument).",
        hidden=True,
    ),
) -> None:
    """List all sub-tenant IDs for a tenant."""
    tid = require_tenant_id(tenant_id or tenant_id_arg)
    client = get_client()
    try:
        result = client.list_sub_tenants(tid)

        def fmt(r: dict) -> str:
            sub_ids = r.get("sub_tenant_ids", [])
            if not sub_ids:
                return f"  No sub-tenants found for tenant '{tid}'."
            lines = [f"  Sub-tenants for '{tid}':"]
            for sid in sub_ids:
                lines.append(f"    - {sid}")
            return "\n".join(lines)

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
        result = client.delete_tenant(tenant_id)
        print_result(result, lambda r: f"  Tenant '{tenant_id}' deleted.")
    except HydraDBClientError as e:
        handle_api_error(e)
    except httpx.RequestError as e:
        handle_network_error(e)
