import unittest

try:
    from fastapi.testclient import TestClient
    from core.app import app
except ImportError:  # fastapi not installed in this environment
    TestClient = None


@unittest.skipIf(TestClient is None, "fastapi/httpx not installed")
class HealthTests(unittest.TestCase):
    def test_health_returns_200(self):
        r = TestClient(app).get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"status": "ok"})
