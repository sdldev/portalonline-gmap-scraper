"""Tests for configuration module."""

import importlib

import pytest


@pytest.fixture()
def _isolated_config(monkeypatch, tmp_path):
    """Reload config with no .env file and no relevant env vars set."""

    import portalonline_gmap_scraper.config as config_module

    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **kw: None)
    env_vars = [
        "LEADS",
        "MAX_TAB_ALLOWED",
        "HEADLESS",
        "MAX_RETRIES",
        "BATCH_SIZE",
        "COOLDOWN_SEC",
        "PROCESS_NICE",
        "MEM_LIMIT_MB",
        "CPU_LIMIT_PERCENT",
        "MAX_URLS_PER_QUERY",
        "INTER_QUERY_COOLDOWN",
        "DEBUG",
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)
    importlib.reload(config_module)
    yield config_module


class TestConfigDefaults:
    def test_target_leads_default(self, _isolated_config):
        assert _isolated_config.TARGET_LEADS == 25

    def test_max_tabs_default(self, _isolated_config):
        assert _isolated_config.MAX_TABS == 1

    def test_headless_default(self, _isolated_config):
        assert _isolated_config.HEADLESS is True

    def test_debug_default(self, _isolated_config):
        assert _isolated_config.DEBUG is False

    def test_save_as_csv_default(self, _isolated_config):
        assert _isolated_config.SAVE_AS_CSV is True

    def test_csv_filename_default(self, _isolated_config):
        assert _isolated_config.CSV_FILENAME == "scraped_data.csv"

    def test_batch_size_default(self, _isolated_config):
        assert _isolated_config.BATCH_SIZE == 5

    def test_cooldown_sec_default(self, _isolated_config):
        assert _isolated_config.COOLDOWN_SEC == 8.0

    def test_process_nice_default(self, _isolated_config):
        assert _isolated_config.PROCESS_NICE == 15

    def test_mem_limit_mb_default(self, _isolated_config):
        assert _isolated_config.MEM_LIMIT_MB == 8192


class TestConfigFromEnv:
    def test_target_leads_from_env(self, monkeypatch):
        import importlib

        import portalonline_gmap_scraper.config as config_module

        monkeypatch.setenv("LEADS", "50")
        importlib.reload(config_module)
        assert config_module.TARGET_LEADS == 50

    def test_max_tabs_from_env(self, monkeypatch):
        import importlib

        import portalonline_gmap_scraper.config as config_module

        monkeypatch.setenv("MAX_TAB_ALLOWED", "4")
        importlib.reload(config_module)
        assert config_module.MAX_TABS == 4

    def test_headless_false_from_env(self, monkeypatch):
        import importlib

        import portalonline_gmap_scraper.config as config_module

        monkeypatch.setenv("HEADLESS", "false")
        importlib.reload(config_module)
        assert config_module.HEADLESS is False

    def test_debug_true_from_env(self, monkeypatch):
        import importlib

        import portalonline_gmap_scraper.config as config_module

        monkeypatch.setenv("DEBUG", "true")
        importlib.reload(config_module)
        assert config_module.DEBUG is True

    def test_batch_size_from_env(self, monkeypatch):
        import importlib

        import portalonline_gmap_scraper.config as config_module

        monkeypatch.setenv("BATCH_SIZE", "10")
        importlib.reload(config_module)
        assert config_module.BATCH_SIZE == 10

    def test_cooldown_from_env(self, monkeypatch):
        import importlib

        import portalonline_gmap_scraper.config as config_module

        monkeypatch.setenv("COOLDOWN_SEC", "20")
        importlib.reload(config_module)
        assert config_module.COOLDOWN_SEC == 20

    def test_process_nice_from_env(self, monkeypatch):
        import importlib

        import portalonline_gmap_scraper.config as config_module

        monkeypatch.setenv("PROCESS_NICE", "15")
        importlib.reload(config_module)
        assert config_module.PROCESS_NICE == 15

    def test_mem_limit_from_env(self, monkeypatch):
        import importlib

        import portalonline_gmap_scraper.config as config_module

        monkeypatch.setenv("MEM_LIMIT_MB", "1024")
        importlib.reload(config_module)
        assert config_module.MEM_LIMIT_MB == 1024
