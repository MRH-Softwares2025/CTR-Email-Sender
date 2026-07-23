import unittest

from smtp_utils import resolve_smtp_credentials


class SmtpUtilsTests(unittest.TestCase):
    def test_prefers_settings_over_environment(self):
        settings = {"gmail_email": "settings@example.com", "app_password": "settings-pass"}
        env = {"GMAIL_EMAIL": "env@example.com", "GMAIL_APP_PASSWORD": "env-pass"}

        self.assertEqual(resolve_smtp_credentials(settings, env), ("settings@example.com", "settings-pass"))

    def test_falls_back_to_environment_when_settings_missing(self):
        settings = {}
        env = {"GMAIL_EMAIL": "env@example.com", "GMAIL_APP_PASSWORD": "env-pass"}

        self.assertEqual(resolve_smtp_credentials(settings, env), ("env@example.com", "env-pass"))

    def test_returns_empty_values_when_nothing_is_configured(self):
        self.assertEqual(resolve_smtp_credentials({}, {}), ("", ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
