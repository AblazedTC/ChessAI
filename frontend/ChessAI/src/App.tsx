import { useState } from "react";
import { Chess } from "chess.js";
import { Chessboard, type PieceDropHandlerArgs } from "react-chessboard";
import { customPieces } from "./customPieces";

var AI_DEPTH = 12; // 1-18: higher = stronger but slower

type Difficulty = "Easy" | "Normal" | "Hard" | "GM";

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
  const [game] = useState(() => new Chess());
  const [fen, setFen] = useState(game.fen());
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty>("Normal");

  async function playAiMove() {
    setThinking(true);
    setError(null);
    try {
      const response = await fetch("/api/move", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fen: game.fen(), depth: AI_DEPTH }),
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
      setError(err instanceof Error ? err.message : "The AI move failed.");
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
    switch (difficulty) {
      case "Easy":
        setDifficulty("Normal");
        AI_DEPTH = 6;
        break;
      case "Normal":
        setDifficulty("Hard");
        AI_DEPTH = 9;
        break;
      case "Hard":
        setDifficulty("GM");
        AI_DEPTH = 12;
        break;
      case "GM":
        setDifficulty("Easy");
        AI_DEPTH = 1;
        break;
    }
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
        <button id={"difficulty-button"} onClick={changeDifficulty}>{difficulty}</button>
        {aiStuck && <button onClick={() => void playAiMove()}>Retry AI move</button>}
      </div>
    </div>
  );
}
