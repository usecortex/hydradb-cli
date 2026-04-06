"""Common utilities shared across CLI commands."""

from typing import Optional

import typer

from hydradb_cli.client import HydraDBClient, HydraDBClientError
from hydradb_cli.config import get_api_key, get_tenant_id, get_sub_tenant_id
from hydradb_cli.output import print_error


def mask_api_key(key: str) -> str:
    """Mask an API key for display, showing only prefix and suffix."""
    if len(key) > 12:
        return f"{key[:8]}...{key[-4:]}"
    return "***"


def require_api_key() -> str:
    """Get the API key or exit with a helpful error."""
    key = get_api_key()
    if not key:
        print_error(
            "No API key configured. Run 'hydradb login' or set HYDRA_DB_API_KEY environment variable."
        )
    return key  # type: ignore[return-value]


def require_tenant_id(tenant_id: Optional[str] = None) -> str:
    """Get tenant ID from argument, config, or exit with error."""
    tid = tenant_id or get_tenant_id()
    if not tid:
        print_error(
            "No tenant ID specified. Use --tenant-id or run 'hydradb config set tenant_id <id>'."
        )
    return tid  # type: ignore[return-value]


def resolve_sub_tenant_id(sub_tenant_id: Optional[str] = None) -> Optional[str]:
    """Get sub-tenant ID from argument or config (may be None)."""
    return sub_tenant_id or get_sub_tenant_id()


def get_client() -> HydraDBClient:
    """Create an authenticated HydraDB client or exit with error."""
    api_key = require_api_key()
    return HydraDBClient(api_key=api_key)


def handle_api_error(e: HydraDBClientError) -> None:
    """Format and print an API error, then exit."""
    if e.status_code == 401:
        print_error("Authentication failed. Check your API key.")
    elif e.status_code == 403:
        print_error("Access denied. Your API key may not have permission for this operation.")
    elif e.status_code == 404:
        print_error(f"Not found: {e.detail}")
    elif e.status_code == 429:
        print_error("Rate limited. Please wait and try again.")
    else:
        print_error(f"API error (HTTP {e.status_code}): {e.detail}")
