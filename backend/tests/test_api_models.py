"""Tests for Pydantic models and validators."""

import pytest
from pydantic import ValidationError

from api.models import (
    JobCreate,
    UserCreate,
    UserUpdate,
)


class TestUserCreate:
    def test_valid_username(self):
        u = UserCreate(username="test_user")
        assert u.username == "test_user"

    def test_username_blocked_chars(self):
        with pytest.raises(ValidationError):
            UserCreate(username="test-user")

    def test_username_empty(self):
        with pytest.raises(ValidationError):
            UserCreate(username="")

    def test_username_too_long(self):
        with pytest.raises(ValidationError):
            UserCreate(username="a" * 51)


class TestUserUpdate:
    def test_partial_update(self):
        u = UserUpdate(username="newuser")
        assert u.username == "newuser"
        assert u.role is None

    def test_username_validation_on_update(self):
        with pytest.raises(ValidationError):
            UserUpdate(username="bad name")


class TestJobCreate:
    def test_valid_job(self):
        j = JobCreate(keyword="restoran", location="Jakarta")
        assert j.keyword == "restoran"
        assert j.target == 25

    def test_keyword_sanitize_sql_injection(self):
        j = JobCreate(keyword="restoran'; DROP TABLE users;--")
        assert ";" not in j.keyword
        assert "--" not in j.keyword

    def test_keyword_strip_blocked(self):
        j = JobCreate(keyword="<script>restoran</script>")
        assert "<" not in j.keyword

    def test_target_out_of_range(self):
        with pytest.raises(ValidationError):
            JobCreate(keyword="test", target=0)

    def test_target_max(self):
        with pytest.raises(ValidationError):
            JobCreate(keyword="test", target=501)

    def test_keyword_too_long(self):
        with pytest.raises(ValidationError):
            JobCreate(keyword="a" * 201)

    def test_location_too_long(self):
        with pytest.raises(ValidationError):
            JobCreate(keyword="test", location="a" * 101)

    def test_category_variations_max(self):
        with pytest.raises(ValidationError):
            JobCreate(keyword="test", category_variations=["a"] * 11)
