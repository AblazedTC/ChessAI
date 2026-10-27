import os

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Stockfish engine hosted by https://chess-api.com/
CHESS_API_URL = os.getenv("CHESS_API_URL", "https://chess-api.com/v1")

# Comma-separated list of browser origins allowed to call this API,
# e.g. "https://chessai.vercel.app,http://localhost:5173"
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]

app = FastAPI(
    title="ChessAI API",
    description="Backend API for ChessAI.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    # Allow every Vercel preview deployment of the frontend as well
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class MoveRequest(BaseModel):
    fen: str = Field(min_length=1, description="Current board position in FEN notation")
    depth: int = Field(default=12, ge=1, le=18, description="Engine search depth (chess-api.com allows up to 18)")


class MoveResponse(BaseModel):
    move: str  # e.g. "e7e5", or "e7e8q" for a promotion
    from_square: str
    to_square: str
    promotion: str | None = None
    san: str | None = None
    eval: float | None = None


async def fetch_engine_move(fen: str, depth: int) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(CHESS_API_URL, json={"fen": fen, "depth": depth})
        response.raise_for_status()
        return response.json()


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to the ChessAI API"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/move", response_model=MoveResponse)
async def best_move(request: MoveRequest) -> MoveResponse:
    try:
        data = await fetch_engine_move(request.fen, request.depth)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Could not reach the chess engine.") from exc

    move = data.get("move") or data.get("lan")
    if not isinstance(move, str) or len(move) < 4:
        raise HTTPException(status_code=502, detail=data.get("text") or "The engine did not return a move.")

    return MoveResponse(
        move=move,
        from_square=move[:2],
        to_square=move[2:4],
        promotion=move[4:5] or None,
        san=data.get("san"),
        eval=data.get("eval"),
    )
