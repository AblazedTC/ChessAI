import asyncio
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from main import app, fetch_engine_move

START_FEN = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"


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


class MoveEndpointTests(unittest.TestCase):
    def post_move(self, engine_result, body=None):
        mock = AsyncMock(side_effect=engine_result) if isinstance(engine_result, Exception) else AsyncMock(return_value=engine_result)
        with patch("main.fetch_engine_move", mock), TestClient(app) as client:
            return client.post("/api/move", json=body or {"fen": START_FEN, "depth": 5})

    def test_returns_engine_move(self) -> None:
        response = self.post_move({"move": "e7e5", "san": "e5", "eval": 0.3})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["from_square"], "e7")
        self.assertEqual(response.json()["to_square"], "e5")
        self.assertIsNone(response.json()["promotion"])

    def test_promotion_move(self) -> None:
        response = self.post_move({"move": "a2a1q"})
        self.assertEqual(response.json()["promotion"], "q")

    def test_engine_unreachable_returns_502(self) -> None:
        response = self.post_move(httpx.ConnectError("down"))
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["detail"], "Could not reach the chess engine.")

    def test_engine_error_payload_returns_502(self) -> None:
        response = self.post_move({"type": "error", "text": "Invalid FEN"})
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["detail"], "Invalid FEN")

    def test_rejects_out_of_range_depth(self) -> None:
        response = self.post_move({"move": "e7e5"}, {"fen": START_FEN, "depth": 99})
        self.assertEqual(response.status_code, 422)


class EngineRetryTests(unittest.TestCase):
    def run_fetch(self, statuses):
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            status = statuses[len(calls)]
            calls.append(status)
            return httpx.Response(status, json={"move": "e7e5"})

        async def go():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                return await fetch_engine_move(client, START_FEN, 5)

        with patch("main.asyncio.sleep", AsyncMock()):
            return asyncio.run(go()), calls

    def test_retries_rate_limit_then_succeeds(self) -> None:
        result, calls = self.run_fetch([429, 503, 200])
        self.assertEqual(result["move"], "e7e5")
        self.assertEqual(calls, [429, 503, 200])

    def test_gives_up_after_max_attempts(self) -> None:
        with self.assertRaises(httpx.HTTPStatusError):
            self.run_fetch([503, 503, 503])

    def test_does_not_retry_client_errors(self) -> None:
        with self.assertRaises(httpx.HTTPStatusError):
            self.run_fetch([400])
