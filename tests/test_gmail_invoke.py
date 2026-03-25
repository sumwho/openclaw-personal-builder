import json
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "gmail-organizer"
    / "scripts"
    / "invoke_gmail.py"
)
MODULE_SPEC = importlib.util.spec_from_file_location("invoke_gmail", MODULE_PATH)
invoke_gmail = importlib.util.module_from_spec(MODULE_SPEC)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
MODULE_SPEC.loader.exec_module(invoke_gmail)


class GmailInvokeTests(unittest.TestCase):
    def test_load_env_local(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env.local"
            env_path.write_text("GMAIL_ACCOUNT=test@example.com\n# comment\nEMPTY=\n", encoding="utf-8")
            data = invoke_gmail.load_env_local(env_path)
        self.assertEqual(data["GMAIL_ACCOUNT"], "test@example.com")
        self.assertEqual(data["EMPTY"], "")

    def test_status_without_credentials(self):
        with mock.patch.object(invoke_gmail, "gog_available", return_value=True), mock.patch.object(
            invoke_gmail, "credentials_path", return_value=Path("/tmp/missing-credentials.json")
        ), mock.patch.object(
            invoke_gmail,
            "run_command",
            side_effect=[
                mock.Mock(stdout="config_exists\tfalse\n", stderr="", returncode=0),
                mock.Mock(stdout="No OAuth client credentials stored\n", stderr="", returncode=0),
                mock.Mock(stdout="", stderr="watch state not found; run gmail watch start\n", returncode=1),
            ],
        ):
            result = invoke_gmail.status("user@example.com")
        self.assertTrue(result["ok"])
        self.assertFalse(result["oauth_credentials_present"])
        self.assertIn("gog auth credentials set", "\n".join(result["next_steps"]))

    def test_search_messages_reports_missing_oauth_credentials(self):
        completed = mock.Mock(
            returncode=1,
            stdout="",
            stderr="OAuth client credentials missing (OAuth client ID JSON).",
        )
        with mock.patch.object(invoke_gmail, "run_command", return_value=completed), mock.patch.object(
            invoke_gmail, "credentials_path", return_value=Path("/tmp/credentials.json")
        ):
            result = invoke_gmail.search_messages("user@example.com", "label:inbox", 5)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "oauth_credentials_missing")
        self.assertEqual(result["account"], "user@example.com")

    def test_normalize_message_uses_headers(self):
        message = {
            "id": "msg-1",
            "threadId": "thr-1",
            "snippet": "hello",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test subject"},
                    {"name": "From", "value": "Boss <boss@example.com>"},
                    {"name": "Date", "value": "Mon, 10 Mar 2026 08:00:00 +0000"},
                ]
            },
        }
        result = invoke_gmail.normalize_message(message)
        self.assertEqual(result["id"], "msg-1")
        self.assertEqual(result["subject"], "Test subject")
        self.assertIn("boss@example.com", result["from"])

    def test_main_missing_account(self):
        with mock.patch.object(invoke_gmail, "default_account", return_value=""), mock.patch(
            "sys.argv", ["invoke_gmail.py", "latest"]
        ), mock.patch("sys.stdout") as stdout:
            code = invoke_gmail.main()
        self.assertEqual(code, 1)
        output = "".join(call.args[0] for call in stdout.write.call_args_list)
        payload = json.loads(output)
        self.assertEqual(payload["error_code"], "missing_account")


if __name__ == "__main__":
    unittest.main()
