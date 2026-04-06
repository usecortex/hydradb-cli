"""Configuration commands: show, set."""

from typing import Optional

import typer

from hydradb_cli.config import get_full_config, save_config
from hydradb_cli.output import print_error, print_json, print_result, get_output_format
from hydradb_cli.utils.common import mask_api_key

app = typer.Typer(help="View and manage CLI configuration.")

VALID_KEYS = {"api_key", "tenant_id", "sub_tenant_id", "base_url"}


@app.command()
def show() -> None:
    """Show current CLI configuration.

    Displays all configured values and their sources (environment variable
    or config file). API keys are masked for security.

    Examples:

        hydradb config show

        hydradb config show --output json
    """
    cfg = get_full_config()

    if get_output_format() == "json":
        safe_cfg = dict(cfg)
        if safe_cfg.get("api_key"):
            key = safe_cfg["api_key"]
            safe_cfg["api_key"] = mask_api_key(key)
        print_json(safe_cfg)
        return

    typer.echo("  HydraDB CLI Configuration\n")

    api_key = cfg.get("api_key")
    if api_key:
        masked = mask_api_key(api_key)
        typer.echo(f"  api_key:        {masked} (source: {cfg['api_key_source']})")
    else:
        typer.echo("  api_key:        (not set)")

    tenant_id = cfg.get("tenant_id")
    typer.echo(f"  tenant_id:      {tenant_id or '(not set)'}" + (
        f" (source: {cfg['tenant_id_source']})" if tenant_id else ""
    ))

    sub_tenant = cfg.get("sub_tenant_id")
    typer.echo(f"  sub_tenant_id:  {sub_tenant or '(not set)'}")

    typer.echo(f"  base_url:       {cfg['base_url']}")
    typer.echo(f"\n  Config file:    {cfg['config_file']}")


@app.command("set")
def set_value(
    key: str = typer.Argument(help=f"Config key to set. Valid keys: {', '.join(sorted(VALID_KEYS))}"),
    value: str = typer.Argument(help="Value to set."),
) -> None:
    """Set a configuration value.

    Values are saved to ~/.hydradb/config.json. Environment variables
    always take precedence over file-based config.

    Examples:

        hydradb config set tenant_id my-tenant

        hydradb config set base_url https://api.hydradb.com
    """
    if key not in VALID_KEYS:
        print_error(f"Unknown config key '{key}'. Valid keys: {', '.join(sorted(VALID_KEYS))}")

    save_config(**{key: value})

    result = {"success": True, "key": key, "message": f"Set {key} in config."}
    print_result(result, lambda r: f"  Set '{key}' in ~/.hydradb/config.json")
