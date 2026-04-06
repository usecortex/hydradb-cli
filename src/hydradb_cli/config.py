"""Configuration management for HydraDB CLI.

Handles API key storage, tenant defaults, and base URL configuration.
Config is stored in ~/.hydradb/config.json.
Environment variables override file-based config.
"""

import json
import os
from pathlib import Path
from typing import Optional

# Environment variable names (aligned with MCP plugin and OpenClaw conventions)
ENV_API_KEY = "HYDRA_DB_API_KEY"
ENV_TENANT_ID = "HYDRA_DB_TENANT_ID"
ENV_SUB_TENANT_ID = "HYDRA_DB_SUB_TENANT_ID"
ENV_BASE_URL = "HYDRA_DB_BASE_URL"

DEFAULT_BASE_URL = "https://api.hydradb.com"
CONFIG_DIR = Path.home() / ".hydradb"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _read_config_file() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _write_config_file(data: dict) -> None:
    _ensure_config_dir()
    CONFIG_FILE.write_text(json.dumps(data, indent=2) + "\n")
    # Restrict permissions on config file (contains API key)
    CONFIG_FILE.chmod(0o600)


def get_api_key() -> Optional[str]:
    """Get API key from env var or config file."""
    env_val = os.environ.get(ENV_API_KEY)
    if env_val:
        return env_val
    return _read_config_file().get("api_key")


def get_tenant_id() -> Optional[str]:
    """Get default tenant ID from env var or config file."""
    env_val = os.environ.get(ENV_TENANT_ID)
    if env_val:
        return env_val
    return _read_config_file().get("tenant_id")


def get_sub_tenant_id() -> Optional[str]:
    """Get default sub-tenant ID from env var or config file."""
    env_val = os.environ.get(ENV_SUB_TENANT_ID)
    if env_val:
        return env_val
    return _read_config_file().get("sub_tenant_id")


def get_base_url() -> str:
    """Get API base URL from env var or config file."""
    env_val = os.environ.get(ENV_BASE_URL)
    if env_val:
        return env_val.rstrip("/")
    return _read_config_file().get("base_url", DEFAULT_BASE_URL)


def save_config(
    api_key: Optional[str] = None,
    tenant_id: Optional[str] = None,
    sub_tenant_id: Optional[str] = None,
    base_url: Optional[str] = None,
) -> None:
    """Save configuration values to config file."""
    data = _read_config_file()
    if api_key is not None:
        data["api_key"] = api_key
    if tenant_id is not None:
        data["tenant_id"] = tenant_id
    if sub_tenant_id is not None:
        data["sub_tenant_id"] = sub_tenant_id
    if base_url is not None:
        data["base_url"] = base_url.rstrip("/")
    _write_config_file(data)


def clear_config() -> None:
    """Remove the config file."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()


def get_full_config() -> dict:
    """Return the resolved config (env vars override file values)."""
    file_cfg = _read_config_file()
    return {
        "api_key": get_api_key(),
        "tenant_id": get_tenant_id(),
        "sub_tenant_id": get_sub_tenant_id(),
        "base_url": get_base_url(),
        "config_file": str(CONFIG_FILE),
        "api_key_source": "env" if os.environ.get(ENV_API_KEY) else ("file" if file_cfg.get("api_key") else "none"),
        "tenant_id_source": "env" if os.environ.get(ENV_TENANT_ID) else ("file" if file_cfg.get("tenant_id") else "none"),
    }
