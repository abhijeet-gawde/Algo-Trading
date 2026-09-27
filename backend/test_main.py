import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main


class FakeKite:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.access_token = ""

    def generate_session(self, request_token: str, api_secret: str) -> dict[str, str]:
        assert request_token == "request-token"
        assert api_secret == "api-secret"
        return {"access_token": "private-access-token"}

    def set_access_token(self, access_token: str) -> None:
        self.access_token = access_token

    def profile(self) -> dict[str, object]:
        return {
            "user_name": "Example User",
            "user_id": "AB1234",
            "products": ["CNC", "MIS"],
            "exchanges": ["NSE", "BSE"],
            "access_token": self.access_token,
        }


class SessionApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_token_file = main.TOKEN_FILE
        main.TOKEN_FILE = Path(self.temp_dir.name) / "token.json"

    def tearDown(self) -> None:
        main.TOKEN_FILE = self.original_token_file
        self.temp_dir.cleanup()

    def test_login_persists_token_without_returning_it(self) -> None:
        with patch.object(main, "KiteConnect", FakeKite):
            response = main.login(
                main.LoginRequest(
                    api_key="api-key",
                    api_secret="api-secret",
                    request_token="request-token",
                )
            )

        self.assertEqual(response, {"authenticated": True})
        self.assertNotIn("private-access-token", str(response))
        self.assertEqual(
            main.read_session(),
            {"api_key": "api-key", "access_token": "private-access-token"},
        )

    def test_saved_session_and_profile_do_not_expose_token(self) -> None:
        main.save_session("api-key", "private-access-token")
        with patch.object(main, "KiteConnect", FakeKite):
            self.assertEqual(main.session_status(), {"authenticated": True})
            response = main.profile()

        self.assertEqual(response["user_name"], "Example User")
        self.assertEqual(response["products"], ["CNC", "MIS"])
        self.assertNotIn("access_token", response)
        self.assertNotIn("private-access-token", str(response))

    def test_logout_removes_saved_session(self) -> None:
        main.save_session("api-key", "private-access-token")
        self.assertEqual(main.logout(), {"authenticated": False})
        self.assertIsNone(main.read_session())


if __name__ == "__main__":
    unittest.main()