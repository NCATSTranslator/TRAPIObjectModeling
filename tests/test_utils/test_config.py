"""Tests for translator_tom.utils.config."""

import pytest

from translator_tom.utils.config import TRAPI_CONFIG, HashRepEnum, TRAPIConfig


class TestHashRepEnum:
    def test_values(self):
        assert HashRepEnum.HEX.value == 1
        assert HashRepEnum.B32.value == 2
        assert HashRepEnum.B64.value == 3

    def test_int_subclass(self):
        # The enum is `int, Enum`, so members behave as ints.
        assert int(HashRepEnum.B64) == 3
        assert HashRepEnum.B64 == 3


class TestTRAPIConfigDefaults:
    def test_singleton_uses_defaults(self):
        # Sanity check that the imported singleton matches a freshly-built one
        # under the test environment (no overriding env vars set).
        assert TRAPI_CONFIG.biolink_version == TRAPIConfig().biolink_version
        assert TRAPI_CONFIG.schema_version == TRAPIConfig().schema_version


class TestTRAPIConfigEnvOverride:
    def test_env_overrides_defaults(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("BIOLINK_VERSION", "9.9.9")
        monkeypatch.setenv("SCHEMA_VERSION", "2.0.0")
        cfg = TRAPIConfig()
        assert cfg.biolink_version == "9.9.9"
        assert cfg.schema_version == "2.0.0"

    def test_env_is_case_insensitive(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("biolink_version", "1.2.3")
        cfg = TRAPIConfig()
        assert cfg.biolink_version == "1.2.3"

    def test_env_takes_priority_over_init(self, monkeypatch: pytest.MonkeyPatch):
        # settings_customise_sources lists env_settings before init_settings,
        # so the env value wins.
        monkeypatch.setenv("BIOLINK_VERSION", "from-env")
        cfg = TRAPIConfig(biolink_version="from-init")
        assert cfg.biolink_version == "from-env"

    def test_init_used_when_env_absent(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("BIOLINK_VERSION", raising=False)
        cfg = TRAPIConfig(biolink_version="from-init")
        assert cfg.biolink_version == "from-init"
