"""Tests for input sanitization."""

import pytest

from api.middleware.sanitize import (
    sanitize_keyword,
    sanitize_location,
    sanitize_username,
)


class TestSanitizeKeyword:
    def test_removes_semicolon(self):
        assert "restoran" in sanitize_keyword("restoran; DROP TABLE")

    def test_removes_angle_brackets(self):
        result = sanitize_keyword("<script>restoran</script>")
        assert "<" not in result
        assert "script" in result or "restoran" in result

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            sanitize_keyword("   ")

    def test_trim_whitespace(self):
        assert sanitize_keyword("  restoran  ") == "restoran"


class TestSanitizeLocation:
    def test_none_returns_none(self):
        assert sanitize_location(None) is None

    def test_strip_whitespace(self):
        assert sanitize_location("  Jakarta  ") == "Jakarta"

    def test_blocked_chars_removed(self):
        result = sanitize_location("Jakarta; -- DROP")
        assert ";" not in result


class TestSanitizeUsername:
    def test_valid_username(self):
        assert sanitize_username("test_user") == "test_user"

    def test_dash_rejected(self):
        with pytest.raises(ValueError):
            sanitize_username("test-user")
