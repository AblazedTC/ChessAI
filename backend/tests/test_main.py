import unittest

from fastapi.testclient import TestClient

from main import app


class AppTests(unittest.TestCase):
    def test_root(self) -> None:
        with TestClient(app) as client:
            response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Welcome to the ChessAI API"})

    def test_health(self) -> None:
        with TestClient(app) as client:
            response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_openapi(self) -> None:
        with TestClient(app) as client:
            response = client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        schema = response.json()
        self.assertEqual(schema["info"]["title"], "ChessAI API")
        self.assertIn("/", schema["paths"])
        self.assertIn("/health", schema["paths"])
