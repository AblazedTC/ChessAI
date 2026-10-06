from fastapi import FastAPI

app = FastAPI(
    title="ChessAI API",
    description="Backend API for ChessAI.",
    version="0.1.0",
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to the ChessAI API"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}