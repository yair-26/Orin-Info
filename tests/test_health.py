import unittest

try:
    from fastapi.testclient import TestClient
    from core.app import app
except ImportError:  # fastapi/httpx not installed in this environment
    TestClient = None


@unittest.skipIf(TestClient is None, "fastapi/httpx not installed")
class ApiTests(unittest.TestCase):
    def setUp(self):
        self.c = TestClient(app)

    def test_health(self):
        r = self.c.get("/health")
        self.assertEqual((r.status_code, r.json()), (200, {"status": "ok"}))

    def test_calls_list_and_detail(self):
        rows = self.c.get("/calls", params={"limit": 3}).json()
        self.assertEqual(len(rows), 3)
        d = self.c.get(f"/calls/{rows[0]['call_id']}")
        self.assertEqual(d.status_code, 200)
        self.assertIn("cost_breakdown", d.json())
        self.assertEqual(self.c.get("/calls/nope").status_code, 404)

    def test_summary(self):
        self.assertEqual(self.c.get("/summary").json()["calls_count"], 12)
