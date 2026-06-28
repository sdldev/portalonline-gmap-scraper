"""Tests for configuration module."""

from portalonline_gmap_scraper.config import (
    BATCH_SIZE,
    COOLDOWN_SEC,
    CSV_FILENAME,
    DEBUG,
    HEADLESS,
    MAX_TABS,
    MEM_LIMIT_MB,
    PROCESS_NICE,
    SAVE_AS_CSV,
    TARGET_LEADS,
)


class TestConfigDefaults:
    def test_target_leads_default(self):
        assert TARGET_LEADS == 25

    def test_max_tabs_default(self):
        assert MAX_TABS == 1

    def test_headless_default(self):
        assert HEADLESS is True

    def test_debug_default(self):
        assert DEBUG is False

    def test_save_as_csv_default(self):
        assert SAVE_AS_CSV is True

    def test_csv_filename_default(self):
        assert CSV_FILENAME == "scraped_data.csv"

    def test_batch_size_default(self):
        assert BATCH_SIZE == 8

    def test_cooldown_sec_default(self):
        assert COOLDOWN_SEC == 4

    def test_process_nice_default(self):
        assert PROCESS_NICE == 10

    def test_mem_limit_mb_default(self):
        assert MEM_LIMIT_MB == 1536


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
