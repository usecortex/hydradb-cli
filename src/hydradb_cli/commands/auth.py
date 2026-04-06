"""Authentication commands: login, logout, whoami."""

import sys
from typing import Optional

import typer

from hydradb_cli.client import HydraDBClient, HydraDBClientError
from hydradb_cli.config import (
    clear_config,
    get_full_config,
    save_config,
)
from hydradb_cli.output import print_error, print_json, print_result, get_output_format
from hydradb_cli.utils.common import mask_api_key


def login(
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        help="Your HydraDB API key (Bearer token).",
    ),
    tenant_id: Optional[str] = typer.Option(
        None,
        "--tenant-id",
        help="Default tenant ID to use for all commands.",
    ),
    sub_tenant_id: Optional[str] = typer.Option(
        None,
        "--sub-tenant-id",
        help="Default sub-tenant ID.",
    ),
    base_url: Optional[str] = typer.Option(
        None,
        "--base-url",
        help="Custom API base URL (default: https://api.hydradb.com).",
    ),
) -> None:
    """Authenticate with HydraDB and save credentials locally.

    Your API key is stored in ~/.hydradb/config.json with restricted permissions.

    For interactive use, omit --api-key and you will be prompted.
    For agents/scripts, always pass --api-key explicitly.
    """
    # Prompt interactively only if --api-key not provided and stdin is a TTY
    if api_key is None:
        if sys.stdin.isatty():
            api_key = typer.prompt("Enter your HydraDB API key", hide_input=True)
        else:
            print_error("No API key provided. Use --api-key or run interactively.")

    if not api_key:
        print_error("API key cannot be empty.")

    # Validate the API key by making a test request
    with HydraDBClient(api_key=api_key, base_url=base_url) as client:
        if tenant_id:
            try:
                client.monitor_tenant(tenant_id)
            except HydraDBClientError as e:
                if e.status_code == 401:
                    print_error("Invalid API key. Authentication failed.")
                # Other errors are OK — tenant might not exist yet
            except Exception:
                # Network errors (ConnectError, TimeoutException, etc.) are
                # non-fatal during login — we still save credentials.
                pass

    save_config(
        api_key=api_key,
        tenant_id=tenant_id,
        sub_tenant_id=sub_tenant_id,
        base_url=base_url,
    )

    result = {
        "success": True,
        "message": "Logged in to HydraDB. Credentials saved to ~/.hydradb/config.json",
        "tenant_id": tenant_id,
    }
    print_result(result, lambda r: (
        f"  Logged in to HydraDB. Credentials saved to ~/.hydradb/config.json"
        + (f"\n  Default tenant: {tenant_id}" if tenant_id else "")
    ))


def logout() -> None:
    """Remove stored credentials."""
    clear_config()
    print_result(
        {"success": True, "message": "Logged out. Credentials removed."},
        lambda r: "  Logged out. Credentials removed from ~/.hydradb/config.json",
    )


def whoami() -> None:
    """Show current authentication status and configuration."""
    cfg = get_full_config()

    if get_output_format() == "json":
        # Mask the API key in JSON output
        safe_cfg = dict(cfg)
        if safe_cfg.get("api_key"):
            key = safe_cfg["api_key"]
            safe_cfg["api_key"] = mask_api_key(key)
        print_json(safe_cfg)
        return

    api_key = cfg.get("api_key")
    if api_key:
        masked = mask_api_key(api_key)
        typer.echo(f"  API Key:        {masked} (source: {cfg['api_key_source']})")
    else:
        typer.echo("  API Key:        Not configured")

    tenant_id = cfg.get("tenant_id")
    if tenant_id:
        typer.echo(f"  Tenant ID:      {tenant_id} (source: {cfg['tenant_id_source']})")
    else:
        typer.echo("  Tenant ID:      Not configured")

    sub_tenant = cfg.get("sub_tenant_id")
    if sub_tenant:
        typer.echo(f"  Sub-Tenant ID:  {sub_tenant}")

    typer.echo(f"  Base URL:       {cfg['base_url']}")
    typer.echo(f"  Config File:    {cfg['config_file']}")
