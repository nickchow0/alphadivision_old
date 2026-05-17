# services/research/tests/test_main.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

import unittest
from unittest.mock import patch, MagicMock


class TestHealthRoute(unittest.TestCase):
    def setUp(self):
        from main import app
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_health_returns_ok(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), {"status": "ok"})
