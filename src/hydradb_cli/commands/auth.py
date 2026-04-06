"""Authentication commands: login, logout, whoami."""

import sys
from typing import Optional

import typer
from rich.panel import Panel

from hydradb_cli.client import HydraDBClient, HydraDBClientError
from hydradb_cli.config import (
    clear_config,
    get_full_config,
    save_config,
)
from hydradb_cli.output import (
    console,
    get_output_format,
    make_kv_table,
    print_error,
    print_json,
    print_result,
    print_warning,
    spinner,
)
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
    if api_key is None:
        if sys.stdin.isatty():
            api_key = typer.prompt("Enter your HydraDB API key", hide_input=True)
        else:
            print_error("No API key provided. Use --api-key or run interactively.")

    if not api_key or not api_key.strip():
        print_error("API key cannot be empty.")

    validation_warning: Optional[str] = None

    with HydraDBClient(api_key=api_key, base_url=base_url) as client:
        if tenant_id:
            with spinner("Validating credentials..."):
                try:
                    client.monitor_tenant(tenant_id)
                except HydraDBClientError as e:
                    if e.status_code == 401:
                        print_error("Invalid API key. Authentication failed.")
                    elif e.status_code == 403:
                        validation_warning = (
                            "API key was rejected by the server (HTTP 403). "
                            "It may be invalid or lack permission for this tenant. "
                            "Credentials saved \u2014 verify with 'hydradb tenant monitor'."
                        )
                    elif e.status_code != 0:
                        validation_warning = (
                            f"Could not validate against tenant '{tenant_id}' "
                            f"(HTTP {e.status_code}). Credentials saved \u2014 verify with 'hydradb whoami'."
                        )
                except Exception:
                    validation_warning = (
                        "Could not reach the API to validate credentials. "
                        "Credentials saved \u2014 verify with 'hydradb whoami'."
                    )

    save_config(
        api_key=api_key,
        tenant_id=tenant_id,
        sub_tenant_id=sub_tenant_id,
        base_url=base_url,
    )

    def fmt(r: dict):
        lines = [
            "[green]\u2713[/green] Logged in to HydraDB",
            f"  [dim]Credentials saved to ~/.hydradb/config.json[/dim]",
        ]
        if tenant_id:
            lines.append(f"  [cyan]Tenant:[/cyan] {tenant_id}")
        if validation_warning:
            lines.append(f"\n  [yellow]![/yellow] {validation_warning}")
        return Panel(
            "\n".join(lines),
            border_style="green" if not validation_warning else "yellow",
            padding=(0, 1),
        )

    result = {
        "success": True,
        "message": "Logged in to HydraDB. Credentials saved to ~/.hydradb/config.json",
        "tenant_id": tenant_id,
    }
    if validation_warning:
        result["warning"] = validation_warning
    print_result(result, fmt)


def logout() -> None:
    """Remove stored credentials."""
    clear_config()
    print_result(
        {"success": True, "message": "Logged out. Credentials removed."},
        lambda r: "[green]\u2713[/green] Logged out. Credentials removed from ~/.hydradb/config.json",
    )


def whoami() -> None:
    """Show current authentication status and configuration."""
    cfg = get_full_config()

    if get_output_format() == "json":
        safe_cfg = dict(cfg)
        if safe_cfg.get("api_key"):
            key = safe_cfg["api_key"]
            safe_cfg["api_key"] = mask_api_key(key)
        print_json(safe_cfg)
        return

    api_key = cfg.get("api_key")
    pairs: list[tuple[str, str]] = []

    if api_key:
        masked = mask_api_key(api_key)
        pairs.append(("API Key", f"{masked} [dim]({cfg['api_key_source']})[/dim]"))
    else:
        pairs.append(("API Key", "[dim]Not configured[/dim]"))

    tenant_id = cfg.get("tenant_id")
    if tenant_id:
        pairs.append(("Tenant ID", f"{tenant_id} [dim]({cfg['tenant_id_source']})[/dim]"))
    else:
        pairs.append(("Tenant ID", "[dim]Not configured[/dim]"))

    sub_tenant = cfg.get("sub_tenant_id")
    if sub_tenant:
        pairs.append(("Sub-Tenant ID", sub_tenant))

    pairs.append(("Base URL", cfg["base_url"]))
    pairs.append(("Config File", cfg["config_file"]))

    table = make_kv_table(pairs)
    panel = Panel(table, title="[bold cyan]/// Identity[/bold cyan]", border_style="cyan", padding=(0, 1))
    console.print(panel)
