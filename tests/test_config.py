"""Tests for hydradb_cli.config module."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from hydradb_cli.config import (
    CONFIG_FILE,
    DEFAULT_BASE_URL,
    ENV_API_KEY,
    ENV_BASE_URL,
    ENV_SUB_TENANT_ID,
    ENV_TENANT_ID,
    clear_config,
    get_api_key,
    get_base_url,
    get_full_config,
    get_sub_tenant_id,
    get_tenant_id,
    save_config,
)


@pytest.fixture(autouse=True)
def clean_config(tmp_path, monkeypatch):
    """Use a temp config dir for all tests."""
    config_dir = tmp_path / ".hydradb"
    config_file = config_dir / "config.json"
    monkeypatch.setattr("hydradb_cli.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("hydradb_cli.config.CONFIG_FILE", config_file)
    # Clear env vars
    for var in (ENV_API_KEY, ENV_TENANT_ID, ENV_SUB_TENANT_ID, ENV_BASE_URL):
        monkeypatch.delenv(var, raising=False)
    yield config_file


class TestSaveAndReadConfig:
    def test_save_and_read_api_key(self, clean_config):
        save_config(api_key="test-key-123")
        assert get_api_key() == "test-key-123"

    def test_save_and_read_tenant_id(self, clean_config):
        save_config(tenant_id="my-tenant")
        assert get_tenant_id() == "my-tenant"

    def test_save_and_read_sub_tenant_id(self, clean_config):
        save_config(sub_tenant_id="sub-1")
        assert get_sub_tenant_id() == "sub-1"

    def test_save_and_read_base_url(self, clean_config):
        save_config(base_url="https://custom.api.com/")
        assert get_base_url() == "https://custom.api.com"  # trailing slash stripped

    def test_save_multiple_values(self, clean_config):
        save_config(api_key="key1", tenant_id="t1")
        assert get_api_key() == "key1"
        assert get_tenant_id() == "t1"

    def test_save_preserves_existing(self, clean_config):
        save_config(api_key="key1")
        save_config(tenant_id="t1")
        assert get_api_key() == "key1"
        assert get_tenant_id() == "t1"

    def test_config_file_permissions(self, clean_config):
        save_config(api_key="secret")
        assert oct(clean_config.stat().st_mode)[-3:] == "600"


class TestEnvVarOverride:
    def test_env_overrides_api_key(self, clean_config, monkeypatch):
        save_config(api_key="file-key")
        monkeypatch.setenv(ENV_API_KEY, "env-key")
        assert get_api_key() == "env-key"

    def test_env_overrides_tenant_id(self, clean_config, monkeypatch):
        save_config(tenant_id="file-tenant")
        monkeypatch.setenv(ENV_TENANT_ID, "env-tenant")
        assert get_tenant_id() == "env-tenant"

    def test_env_overrides_base_url(self, clean_config, monkeypatch):
        save_config(base_url="https://file.api.com")
        monkeypatch.setenv(ENV_BASE_URL, "https://env.api.com")
        assert get_base_url() == "https://env.api.com"


class TestDefaults:
    def test_default_base_url(self, clean_config):
        assert get_base_url() == DEFAULT_BASE_URL

    def test_no_api_key_returns_none(self, clean_config):
        assert get_api_key() is None

    def test_no_tenant_id_returns_none(self, clean_config):
        assert get_tenant_id() is None

    def test_no_sub_tenant_returns_none(self, clean_config):
        assert get_sub_tenant_id() is None


class TestClearConfig:
    def test_clear_removes_file(self, clean_config):
        save_config(api_key="key")
        assert clean_config.exists()
        clear_config()
        assert not clean_config.exists()

    def test_clear_nonexistent_is_safe(self, clean_config):
        clear_config()  # Should not raise


class TestGetFullConfig:
    def test_full_config_structure(self, clean_config):
        save_config(api_key="k", tenant_id="t")
        cfg = get_full_config()
        assert cfg["api_key"] == "k"
        assert cfg["tenant_id"] == "t"
        assert cfg["base_url"] == DEFAULT_BASE_URL
        assert cfg["api_key_source"] == "file"
        assert cfg["tenant_id_source"] == "file"
        assert "config_file" in cfg

    def test_full_config_env_source(self, clean_config, monkeypatch):
        monkeypatch.setenv(ENV_API_KEY, "env-k")
        cfg = get_full_config()
        assert cfg["api_key_source"] == "env"

    def test_full_config_no_source(self, clean_config):
        cfg = get_full_config()
        assert cfg["api_key_source"] == "none"
        assert cfg["tenant_id_source"] == "none"


class TestCorruptConfig:
    def test_corrupt_json_returns_empty(self, clean_config):
        clean_config.parent.mkdir(parents=True, exist_ok=True)
        clean_config.write_text("not valid json{{{")
        assert get_api_key() is None
        assert get_tenant_id() is None
