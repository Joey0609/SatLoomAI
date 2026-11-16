from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.api.deps import get_credentials, get_wiki_manager
from app.core.config import load_accounts, load_credentials
from app.core.errors import ConfigError
from app.main import create_app


class CredentialsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.server_dir = Path(self.temp_dir.name)
        self.accounts = [
            {"username": "账户一", "password": "secret-one"},
            {"username": "账户二", "password": " secret-two "},
        ]

    def write_credentials(self, data):
        (self.server_dir / "credentials.json").write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )

    def test_single_account_formats_do_not_prompt(self):
        for data in (self.accounts[0], {"accounts": self.accounts[:1]}):
            with self.subTest(data=data), patch("builtins.input") as prompt:
                self.write_credentials(data)
                for interactive in (False, True):
                    creds = load_credentials(self.server_dir, interactive=interactive)
                    self.assertEqual(creds.username, "账户一")
                    self.assertEqual(creds.password, "secret-one")
                prompt.assert_not_called()

    def test_multiple_accounts_select_and_preserve_password(self):
        self.write_credentials({"accounts": self.accounts})
        for selection, account in enumerate(self.accounts, start=1):
            with self.subTest(selection=selection):
                output = io.StringIO()
                with patch("builtins.input", return_value=f" {selection} ") as prompt:
                    with redirect_stdout(output):
                        creds = load_credentials(self.server_dir, interactive=True)
                self.assertEqual(creds.username, account["username"])
                self.assertEqual(creds.password, account["password"])
                prompt.assert_called_once()
                for item in self.accounts:
                    self.assertIn(item["username"], output.getvalue())
                    self.assertNotIn(item["password"], output.getvalue())
                    self.assertNotIn(item["password"], repr(creds))

    def test_invalid_selection_retries(self):
        self.write_credentials({"accounts": self.accounts})
        with patch("builtins.input", side_effect=["", "text", "0", "-1", "3", "2"]) as prompt:
            with redirect_stdout(io.StringIO()):
                creds = load_credentials(self.server_dir, interactive=True)
        self.assertEqual(creds.username, "账户二")
        self.assertEqual(prompt.call_count, 6)

    def test_noninteractive_multiple_accounts_fail_without_prompt(self):
        self.write_credentials({"accounts": self.accounts})
        with patch("builtins.input") as prompt:
            with self.assertRaises(ConfigError) as raised:
                load_credentials(self.server_dir)
        self.assertEqual(raised.exception.code, "credentials_selection_required")
        prompt.assert_not_called()

    def test_unavailable_stdin_fails_without_selecting_an_account(self):
        self.write_credentials({"accounts": self.accounts})
        for error in (EOFError, OSError):
            with self.subTest(error=error), patch("builtins.input", side_effect=error):
                with redirect_stdout(io.StringIO()), self.assertRaises(ConfigError) as raised:
                    load_credentials(self.server_dir, interactive=True)
                self.assertEqual(raised.exception.code, "credentials_selection_required")

    def test_invalid_configurations_are_rejected(self):
        invalid = [
            [], None, {}, {"accounts": []}, {"accounts": {}},
            {"accounts": [None]}, {"accounts": [self.accounts[0], {}]},
            {"username": " ", "password": "secret"},
            {"username": "user", "password": ""},
            {"username": "user", "password": None},
            {"username": 123, "password": "secret"},
        ]
        for data in invalid:
            with self.subTest(data=data):
                self.write_credentials(data)
                with self.assertRaises(ConfigError):
                    load_accounts(self.server_dir)

    def test_missing_and_malformed_files_are_rejected(self):
        with self.assertRaises(ConfigError) as raised:
            load_accounts(self.server_dir)
        self.assertEqual(raised.exception.code, "config_not_found")
        (self.server_dir / "credentials.json").write_text("{", encoding="utf-8")
        with self.assertRaises(ConfigError) as raised:
            load_accounts(self.server_dir)
        self.assertEqual(raised.exception.code, "config_invalid_json")

    def test_startup_keeps_selected_credentials_for_requests(self):
        self.write_credentials({"accounts": self.accounts})
        (self.server_dir / "config.json").write_text(json.dumps({
            "site": {"base_url": "https://example.invalid/", "host": "example.invalid"},
            "server": {},
        }), encoding="utf-8")
        with (
            patch("builtins.input", return_value="2") as prompt,
            patch("app.main.WikiClientManager") as manager,
            patch("app.main.PageListService"),
            patch("app.main.setup_logging"),
            redirect_stdout(io.StringIO()),
        ):
            app = create_app(self.server_dir)
            request = SimpleNamespace(app=app)
            creds = get_credentials(request)
            self.assertEqual(creds.username, "账户二")
            self.assertIs(manager.call_args.args[1], creds)
            self.assertIs(get_wiki_manager(request), manager.return_value)
            manager.return_value.ensure_login.assert_called_once_with()
            prompt.assert_called_once()


if __name__ == "__main__":
    unittest.main()
