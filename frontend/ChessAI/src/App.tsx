import { useEffect, useState } from "react";
import { Chess } from "chess.js";
import { Chessboard, type PieceDropHandlerArgs } from "react-chessboard";
import { customPieces } from "./customPieces";

// Backend origin, e.g. "https://chessai-api.onrender.com". Empty in dev so
// requests go to "/api/..." and are proxied by Vite to the local backend.
const API_BASE_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/+$/, "");

// Engine search depth per difficulty (1-18: higher = stronger but slower)
const DEPTHS = { Easy: 1, Normal: 6, Hard: 9, GM: 12 } as const;
type Difficulty = keyof typeof DEPTHS;
const DIFFICULTIES = Object.keys(DEPTHS) as Difficulty[];

const SAVE_KEY = "chessai-game";

function loadSave(): { fen?: string; difficulty?: Difficulty } {
  try {
    return JSON.parse(localStorage.getItem(SAVE_KEY) ?? "{}");
  } catch {
    return {};
  }
}

function createGame(): Chess {
  const game = new Chess();
  const { fen } = loadSave();
  if (fen) {
    try {
      game.load(fen);
    } catch {
      // ignore a corrupt save and start fresh
    }
  }
  return game;
}

type EngineMove = {
  move: string;
  from_square: string;
  to_square: string;
  promotion: string | null;
};

function getStatus(game: Chess, thinking: boolean): string {
  if (game.isCheckmate()) return game.turn() === "w" ? "Checkmate — the AI wins." : "Checkmate — you win!";
  if (game.isStalemate()) return "Draw by stalemate.";
  if (game.isDraw()) return "Draw.";
  if (thinking) return "AI is thinking…";
  const check = game.inCheck() ? " — check!" : "";
  return game.turn() === "w" ? `Your move (white)${check}` : `AI to move${check}`;
}

export default function App() {
  // One Chess object for the whole session; chess.js updates it in place
  const [game] = useState(createGame);
  const [fen, setFen] = useState(game.fen());
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty>(() => {
    const saved = loadSave().difficulty;
    return saved && saved in DEPTHS ? saved : "Normal";
  });

  // Keep the game across refreshes / closing the tab
  useEffect(() => {
    try {
      localStorage.setItem(SAVE_KEY, JSON.stringify({ fen, difficulty }));
    } catch {
      // storage unavailable (e.g. private mode): game just won't persist
    }
  }, [fen, difficulty]);

  // Wake the backend on page load so a cold start doesn't delay the first AI move
  useEffect(() => {
    fetch(`${API_BASE_URL}/health`).catch(() => {});
  }, []);

  async function playAiMove() {
    setThinking(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/move`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fen: game.fen(), depth: DEPTHS[difficulty] }),
        signal: AbortSignal.timeout(60_000),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail ?? `Server error ${response.status}`);
      }
      const data: EngineMove = await response.json();
      game.move({
        from: data.from_square,
        to: data.to_square,
        promotion: data.promotion ?? undefined,
      });
      setFen(game.fen());
    } catch (err) {
      if (err instanceof DOMException && err.name === "TimeoutError") {
        setError("The chess engine took too long to respond.");
      } else {
        setError(err instanceof Error ? err.message : "The AI move failed.");
      }
    } finally {
      setThinking(false);
    }
  }

  function onPieceDrop({ sourceSquare, targetSquare }: PieceDropHandlerArgs): boolean {
    // Only allow moves on the player's turn, while the AI is idle
    if (!targetSquare || thinking || game.turn() !== "w" || game.isGameOver()) return false;

    try {
      game.move({ from: sourceSquare, to: targetSquare, promotion: "q" });
    } catch {
      return false; // illegal move: piece snaps back
    }
    setFen(game.fen());

    if (!game.isGameOver()) void playAiMove();
    return true;
  }

  function newGame() {
    game.reset();
    setFen(game.fen());
    setError(null);
  }

  function changeDifficulty() {
    setDifficulty(DIFFICULTIES[(DIFFICULTIES.indexOf(difficulty) + 1) % DIFFICULTIES.length]);
  }

  const aiStuck = !thinking && game.turn() === "b" && !game.isGameOver();

  return (
    <div style={{ width: "min(90vw, 560px)", margin: "2rem auto", textAlign: "center" }}>
      <p style={{ fontSize: "1.2rem", fontWeight: 600, margin: "0 0 1rem" }}>{getStatus(game, thinking)}</p>

      <Chessboard
        options={{
          position: fen,
          onPieceDrop,
          pieces: customPieces,
          boardOrientation: "white",
          lightSquareStyle: { backgroundColor: "#f0d9b5" },
          darkSquareStyle: { backgroundColor: "#b58863" },
        }}
      />

      {error && <p style={{ color: "#c0392b", marginTop: "1rem" }}>⚠ {error}</p>}

      <div style={{ display: "flex", gap: "0.75rem", justifyContent: "center", marginTop: "1rem" }}>
        <button onClick={newGame} disabled={thinking}>New game</button>
        <button id={"difficulty-button"} onClick={changeDifficulty} title="Click to change AI difficulty">
          AI: {difficulty} (depth {DEPTHS[difficulty]})
        </button>
        {aiStuck && <button onClick={() => void playAiMove()}>Retry AI move</button>}
      </div>
    </div>
  );
}
