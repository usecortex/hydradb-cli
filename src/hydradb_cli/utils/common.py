"""Common utilities shared across CLI commands."""

import sys

import httpx

from hydradb_cli.client import HydraDBClient, HydraDBClientError
from hydradb_cli.config import get_api_key, get_sub_tenant_id, get_tenant_id
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
        print_error("No API key configured. Run 'hydradb login' or set HYDRA_DB_API_KEY environment variable.")
    return key  # type: ignore[return-value]


def require_tenant_id(tenant_id: str | None = None) -> str:
    """Get tenant ID from argument, config, or exit with error."""
    tid = tenant_id or get_tenant_id()
    if not tid or not tid.strip():
        print_error("No tenant ID specified. Use --tenant-id or run 'hydradb config set tenant_id <id>'.")
    return tid  # type: ignore[return-value]


def resolve_sub_tenant_id(sub_tenant_id: str | None = None) -> str | None:
    """Get sub-tenant ID from argument or config (may be None)."""
    return sub_tenant_id or get_sub_tenant_id()


def get_client() -> HydraDBClient:
    """Create an authenticated HydraDB client or exit with error."""
    api_key = require_api_key()
    return HydraDBClient(api_key=api_key)


def _extract_error_message(detail: str) -> str:
    """Pull a human-readable message out of structured or raw error details."""
    import ast

    try:
        parsed = ast.literal_eval(detail)
        if isinstance(parsed, dict):
            return parsed.get("message") or parsed.get("detail") or str(parsed)
        return str(parsed)
    except Exception:
        return detail


def handle_api_error(e: HydraDBClientError) -> None:
    """Format and print an API error, then exit."""
    if e.status_code == 0:
        print_error(f"Connection error: {e.detail}")
    elif e.status_code == 401:
        print_error("Authentication failed. Check your API key or run 'hydradb login'.")
    elif e.status_code == 403:
        print_error("Access denied. Your API key may not have permission for this operation.")
    elif e.status_code == 404:
        msg = _extract_error_message(e.detail)
        print_error(f"Not found: {msg}")
    elif e.status_code == 422:
        msg = _extract_error_message(e.detail)
        print_error(f"Invalid request: {msg}")
    elif e.status_code == 429:
        print_error("Rate limited. Please wait and try again.")
    elif e.status_code == 500:
        msg = _extract_error_message(e.detail)
        if "tenant collection statistics" in msg.lower():
            print_error(
                "Could not retrieve tenant stats. The tenant may not exist or the backend is temporarily unavailable."
            )
        elif "memory service" in msg.lower():
            print_error("Memory service is temporarily unavailable. Please try again.")
        else:
            print_error(f"Server error: {msg}")
    else:
        msg = _extract_error_message(e.detail)
        print_error(f"API error (HTTP {e.status_code}): {msg}")


def handle_network_error(e: httpx.RequestError) -> None:
    """Format and print a network-level error, then exit."""
    print_error(f"Network error: Unable to reach the HydraDB API. Check your connection and base URL. ({e})")


def validate_range(value: float, name: str, low: float, high: float) -> None:
    """Validate a numeric value is within [low, high], or exit with error."""
    if value < low or value > high:
        print_error(f"--{name} must be between {low} and {high}, got {value}")


def require_non_empty(value: str | None, name: str) -> str:
    """Validate a string is non-empty/non-whitespace, or exit with error."""
    if not value or not value.strip():
        print_error(f"{name} cannot be empty.")
    return value.strip()  # type: ignore[union-attr]


def read_stdin_safe() -> str | None:
    """Read from stdin if data is available, without hanging.

    Returns the stripped content or None if nothing is available.
    """
    if sys.stdin.isatty():
        return None

    import select

    try:
        ready, _, _ = select.select([sys.stdin], [], [], 0.1)
        if ready:
            data = sys.stdin.read().strip()
            return data if data else None
    except (OSError, ValueError):
        pass
    return None
