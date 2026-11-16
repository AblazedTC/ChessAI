

"""
This is the runnable backend tests for the ChessAI FastAPI application.

Run from the ChessAI-main directory with:
    python -m pip install -r backend/requirements.txt
    python -m pip install pytest pytest-asyncio
    python -m pytest tests/backend_tests/test_backend.py -v

The engine is utilized mocked unit tests, tests are deterministic and do not make
requests to chess-api.com!!!

These tests solely focus the current backend API;
"""

import asyncio
import time
from typing import Any

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend import main as backend_main

app = backend_main.app


@pytest_asyncio.fixture
async def client():
    """An async HTTP client that calls the FastAPI app in-process."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client


def mock_engine(monkeypatch: pytest.MonkeyPatch, result: Any = None, error: Exception | None = None):
    """Replace the external chess-engine call with a controlled result."""
    calls: list[tuple[str, int]] = []

    async def fake_fetch_engine_move(fen: str, depth: int) -> dict:
        calls.append((fen, depth))
        if error is not None:
            raise error
        return result if result is not None else {"move": "e2e4", "san": "e4", "eval": 0.25}

    monkeypatch.setattr(backend_main, "fetch_engine_move", fake_fetch_engine_move)
    return calls




@pytest.mark.asyncio
async def  test_req_085_malformed_move_input_does_not_crash_application(client):
    """
    REQ-085: Verify that illegal or malformed move input does not crash the application.
    """
    # 1. SETUP: Identify a standard active chess session layout state.
    # 2. ACT: Send an explicitly corrupted, nonsense string payload to the move validator (e.g., move_uci = "DROP_TABLE_CHESS").
    # 3. ASSERT: Verify the backend catches the parsing anomaly gracefully, returns a standard validation error code,
    #    and keeps the application server thread active without a system crash.
    missing_fen = await client.post("/api/move", json={"depth": 12})
    empty_fen = await client.post("/api/move", json={"fen": "", "depth": 12})
    invalid_depth_low = await client.post("/api/move", json={"fen": "some-fen", "depth": 0})
    invalid_depth_high = await client.post("/api/move", json={"fen": "some-fen", "depth": 19})
    wrong_json_type = await client.post("/api/move", json="DROP_TABLE_CHESS")

    assert missing_fen.status_code == 422
    assert empty_fen.status_code == 422
    assert invalid_depth_low.status_code == 422
    assert invalid_depth_high.status_code == 422
    assert wrong_json_type.status_code == 422

    # The application remains responsive after malformed requests.
    health = await client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}


@pytest.mark.asyncio
async def  test_req_086_malformed_move_input_does_not_corrupt_game_state(client, monkeypatch):
    """
    REQ-086: Verify that illegal or malformed move input does not corrupt the game state.
    """
    # 1. SETUP: Record the clean, valid board FEN string metrics immediately before executing an attack test.
    # 2. ACT: Submit a series of completely malformed coordinate values or illegal data payloads to the game engine.
    # 3. ASSERT: Re-verify the board parameters post-attack; confirm that the active board layout state remains
    #    completely intact, uncorrupted, and exactly identical to the initial pre-test FEN string.
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    calls = mock_engine(monkeypatch)

    before = await client.post("/api/move", json={"fen": fen, "depth": 12})
    malformed = await client.post("/api/move", json={"fen": "", "depth": 12})
    after = await client.post("/api/move", json={"fen": fen, "depth": 12})

    assert before.status_code == 200
    assert malformed.status_code == 422
    assert after.status_code == 200
    assert calls == [(fen, 12), (fen, 12)]
    assert before.json() == after.json()

    # Note: the current backend does not own or store a board/game state. This
    # verifies request isolation, not a chess-engine board-state implementation.


@pytest.mark.asyncio
async def  test_req_087_maintain_active_game_session_without_performance_degradation(client,monkeypatch):
    """
    REQ-087: Verify that the application can maintain one active game session without performance degradation.
    """
    # 1. SETUP: Open an active gameplay layout loop tracking operational resource allocations.
    # 2. ACT: Loop action: Repeatedly launch a match, execute a few moves, exit back to the menu, and spin up a new game.
    # 3. ASSERT: Verify that memory allocation charts remain level and do not drift or leak,
    #    ensuring the interface retains high responsiveness over extended play periods.
    calls = mock_engine(monkeypatch)
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    for _ in range(25):
        response = await client.post("/api/move", json={"fen": fen, "depth": 8})
        assert response.status_code == 200
        assert response.json()["move"] == "e2e4"

    assert len(calls) == 25
    assert all(call == (fen, 8) for call in calls)

    # This is a repeated-request smoke test. Measuring memory leaks requires a
    # longer-running integration/load test and resource monitoring.

@pytest.mark.asyncio
async def  test_req_094_application_bypasses_persistent_user_profiles(client, monkeypatch):
    """
    REQ-094: Verify that the application does not require a user account, login, or persistent profile.
    """
    # 1. SETUP: Initialize a totally fresh browser_tests incognito/private session window container.
    # 2. ACT: Navigate directly to the game URL link.
    # 3. ASSERT: Confirm that the Main Menu is immediately available and allows starting matches
    #    without throwing forced login walls, profile prompt overlays, or account authentication checks.
    mock_engine(monkeypatch)
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    root_response = await client.get("/")
    move_response = await client.post("/api/move", json={"fen": fen, "depth": 12})

    assert root_response.status_code == 200
    assert move_response.status_code == 200
    assert "login" not in {route.path for route in app.routes}
    assert "register" not in {route.path for route in app.routes}

    # This only verifies backend routes. The frontend must be tested separately
    # to establish that the main menu is accessible without authentication.


@pytest.mark.asyncio
async def  test_req_095_zero_pii_collected_stored_or_transmitted(client, monkeypatch):
    """
    REQ-095: Verify that no personally identifiable information is collected, stored, or transmitted by the MVP.
    """
    # 1. SETUP: Attach a local tracker evaluating localStorage, sessionStorage, and outbound payloads.
    # 2. ACT: Step through a normal game setup and play routine.
    # 3. ASSERT: Audit the captured data logs to confirm that zero telemetry records contain names,
    #    IP addresses, unique tracker fingerprints, or any form of Personally Identifiable Information (PII).
    calls = mock_engine(monkeypatch)
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    response = await client.post("/api/move", json={"fen": fen, "depth": 12})

    assert response.status_code == 200
    assert calls == [(fen, 12)]
    assert set(backend_main.MoveRequest.model_fields) == {"fen", "depth"}
    assert set(response.json()).issubset(
        {"move", "from_square", "to_square", "promotion", "san", "eval"}
    )

    # This checks the backend's request/response contract, not all browser
    # storage, server logs, hosting-provider logs, or third-party retention.


@pytest.mark.asyncio
async def  test_req_097_comprehensive_regression_testing_sweeps(client, monkeypatch):
    """
    REQ-097: Perform regression testing after bug fixes to verify that previously working
             chess functionality remains operational.
    """
    # 1. SETUP: Pull down a fresh code commit that contains a recent development bug fix.
    # 2. ACT: Re-execute the complete suite of previously passing verification checks across all test files.
    # 3. ASSERT: Ensure that old, historic core functionalities (such as standard piece movement rules
    #    or main menu routing layers) continue to return successful flags without encountering side-effect breaks.
    mock_engine(monkeypatch, {"move": "e2e4", "san": "e4", "eval": 0.3})

    root_response = await client.get("/")
    health_response = await client.get("/health")
    docs_response = await client.get("/openapi.json")
    move_response = await client.post(
        "/api/move",
        json={"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "depth": 12},
    )

    assert root_response.status_code == 200
    assert root_response.json() == {"message": "Welcome to the ChessAI API"}
    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}
    assert docs_response.status_code == 200
    assert "/api/move" in docs_response.json()["paths"]
    assert move_response.status_code == 200
    assert move_response.json() == {
        "move": "e2e4",
        "from_square": "e2",
        "to_square": "e4",
        "promotion": None,
        "san": "e4",
        "eval": 0.3,
    }

@pytest.mark.asyncio
async def test_req_060_hard_ai_calculates_within_time_limit(client, monkeypatch):
    """
    REQ-060: Verify that the AI returns a move within a few seconds on the highest difficulty
             under normal conditions.
    """
    # 1. SETUP: Initialize a very complex board layout with high numbers of branching move pathways
    # 2. ACT: Start a timer right as a move request is sent to the "Hard" AI engine configuration
    # 3. ASSERT: Stop the timer the moment the API completes its transaction. Check that
    #    the elapsed time does not breach the acceptable performance limit (e.g., duration < 3.0 seconds)
    calls = mock_engine(monkeypatch, {"move": "e2e4", "san": "e4", "eval": 0.1})
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    started = time.perf_counter()
    response = await client.post("/api/move", json={"fen": fen, "depth": 18})
    elapsed = time.perf_counter() - started

    assert response.status_code == 200
    assert calls == [(fen, 18)]
    assert elapsed < 3.0

    # The current API has no easy/medium/hard setting; depth 18 is its maximum.
    # Because the engine is mocked, this measures API overhead, not Stockfish
    # calculation time. A real-engine performance test must be an integration test.

@pytest.mark.asyncio
async def  test_req_104_performance_testing_human_and_ai_latencies(client, monkeypatch):
    """
    REQ-104: Perform performance testing of human moves and AI response time under normal conditions.
    """
    # 1. SETUP: Establish performance metric timers within the move dispatch loop.
    # 2. ACT: Step A: Measure time delta from human board square click to DOM frame update.
    #    Step B: Measure latency from AI turn event to AI backend move return.
    # 3. ASSERT: Verify that human clicks complete visually within 1.0 second and AI calculations
    #    adhere strictly to difficulty constraint parameters.
    mock_engine(monkeypatch, {"move": "e2e4", "san": "e4", "eval": 0.0})
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    durations = []

    for _ in range(10):
        started = time.perf_counter()
        response = await client.post("/api/move", json={"fen": fen, "depth": 12})
        durations.append(time.perf_counter() - started)
        assert response.status_code == 200

    assert max(durations) < 1.0

    # Mocked API latency excludes external engine/network time. Human click-to-DOM
    # latency must be measured with browser automation, not a backend unit test.

#additional api testing

@pytest.mark.asyncio
async def test_api_returns_502_when_engine_request_fails(client, monkeypatch):
    """A failed external engine request is translated into a controlled HTTP error."""
    mock_engine(monkeypatch, error=httpx.ConnectError("connection refused"))
    response = await client.post(
        "/api/move",
        json={"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "depth": 12},
    )
    assert response.status_code == 502
    assert response.json()["detail"] == "Could not reach the chess engine."


@pytest.mark.asyncio
async def test_api_returns_502_when_engine_does_not_provide_a_move(client, monkeypatch):
    """Missing or malformed engine moves are rejected instead of returned as success."""
    for bad_result in ({}, {"move": None, "text": "No move available"}, {"move": "abc"}):
        mock_engine(monkeypatch, result=bad_result)
        response = await client.post(
            "/api/move",
            json={"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "depth": 12},
        )
        assert response.status_code == 502


@pytest.mark.asyncio
async def test_api_parses_promotion_move(client, monkeypatch):
    """Promotion UCI moves expose the promotion piece in the response."""
    mock_engine(monkeypatch, {"move": "e7e8q", "san": "e8=Q", "eval": 4.5})
    response = await client.post(
        "/api/move",
        json={"fen": "4k3/4P3/8/8/8/8/8/4K3 w - - 0 1", "depth": 12},
    )
    assert response.status_code == 200
    assert response.json()["move"] == "e7e8q"
    assert response.json()["from_square"] == "e7"
    assert response.json()["to_square"] == "e8"
    assert response.json()["promotion"] == "q"