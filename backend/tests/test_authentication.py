"""Authentication boundary tests that do not configure a real shared password."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app, current_user


class AuthenticationApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_login_sets_an_httponly_session_cookie(self):
        user = {
            "id": "00000000-0000-0000-0000-000000000001",
            "username": "caine",
            "display_name": "Caine",
        }
        with patch("main.authenticate", return_value=("opaque-token", user)):
            response = self.client.post(
                "/auth/login",
                json={"username": "caine", "password": "shared-password"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["display_name"], "Caine")
        cookie = response.headers["set-cookie"].lower()
        self.assertIn("httponly", cookie)
        self.assertIn("samesite=lax", cookie)
        self.assertNotIn("opaque-token", response.text)

    def test_login_supports_secure_cross_site_cookie_in_production(self):
        user = {
            "id": "00000000-0000-0000-0000-000000000001",
            "username": "caine",
            "display_name": "Caine",
        }
        environment = {
            "PAYCHECKER_COOKIE_SECURE": "true",
            "PAYCHECKER_COOKIE_SAMESITE": "none",
        }
        with (
            patch.dict("os.environ", environment),
            patch("main.authenticate", return_value=("opaque-token", user)),
        ):
            response = self.client.post(
                "/auth/login",
                json={"username": "caine", "password": "shared-password"},
            )

        cookie = response.headers["set-cookie"].lower()
        self.assertIn("secure", cookie)
        self.assertIn("samesite=none", cookie)

    def test_invalid_login_uses_one_generic_message(self):
        with patch("main.authenticate", return_value=None):
            response = self.client.post(
                "/auth/login",
                json={"username": "unknown", "password": "wrong"},
            )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid username or password.")

    def test_anonymous_users_can_list_builtins_but_cannot_save(self):
        listing = self.client.get("/rule-configurations")
        self.assertEqual(listing.status_code, 200)
        self.assertTrue(listing.json())
        self.assertTrue(all(item["kind"] == "builtin" for item in listing.json()))

        response = self.client.post(
            "/rule-configurations",
            json={
                "base_award": "fast_food",
                "name": "Anonymous copy",
                "source": "class FastFoodAward2026Rules:\n    pass\n",
            },
        )
        self.assertEqual(response.status_code, 401)

    def test_current_user_endpoint_returns_only_public_user_fields(self):
        app.dependency_overrides[current_user] = lambda: {
            "id": "00000000-0000-0000-0000-000000000001",
            "username": "simon",
            "display_name": "Simon",
            "is_active": True,
            "password_hash": "must-not-leak",
        }
        response = self.client.get("/auth/me")
        self.assertEqual(
            response.json(),
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "username": "simon",
                "display_name": "Simon",
            },
        )


if __name__ == "__main__":
    unittest.main()
