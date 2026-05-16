"""Tests for watchdog.py."""
import subprocess
import unittest
from unittest.mock import MagicMock, patch, call

import requests


class TestSendDiscord(unittest.TestCase):
    @patch("watchdog.watchdog.requests.post")
    def test_sends_post_to_webhook(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()
        from watchdog.watchdog import send_discord
        send_discord("https://discord.test/webhook", "hello")
        mock_post.assert_called_once_with(
            "https://discord.test/webhook",
            json={"content": "hello"},
            timeout=10,
        )

    @patch("watchdog.watchdog.requests.post")
    def test_raises_on_http_error(self, mock_post):
        mock_post.return_value.raise_for_status.side_effect = Exception("bad")
        from watchdog.watchdog import send_discord
        with self.assertRaises(Exception):
            send_discord("https://discord.test/webhook", "hello")


class TestSendEmail(unittest.TestCase):
    @patch("watchdog.watchdog.SendGridAPIClient")
    @patch("watchdog.watchdog.Mail")
    def test_sends_email_via_sendgrid(self, mock_mail_cls, mock_sg_cls):
        mock_sg = MagicMock()
        mock_sg_cls.return_value = mock_sg
        mock_mail = MagicMock()
        mock_mail_cls.return_value = mock_mail

        from watchdog.watchdog import send_email
        send_email("key", "from@x.com", "to@x.com", "Subject", "Body")

        mock_mail_cls.assert_called_once_with(
            from_email="from@x.com",
            to_emails="to@x.com",
            subject="Subject",
            plain_text_content="Body",
        )
        mock_sg.send.assert_called_once_with(mock_mail)


if __name__ == "__main__":
    unittest.main()
