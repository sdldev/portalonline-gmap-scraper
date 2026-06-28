"""Tests for API key auth and RBAC middleware."""



class TestAuthMiddleware:
    def test_auth_module_imports(self):
        """Verify auth module imports correctly."""
        from portalonline_gmap_scraper.api.middleware.auth import (
            require_admin,
            require_user,
            verify_api_key,
        )
        assert require_admin is not None
        assert require_user is not None
        assert verify_api_key is not None
