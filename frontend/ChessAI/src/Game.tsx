import { useEffect, useRef, useState } from "react";
import { Chess } from "chess.js";
import { Chessboard, type PieceDropHandlerArgs } from "react-chessboard";
import { customPieces } from "./customPieces";
import { DEPTH, type GameSettings } from "./types";
import "./Game.css";

type EngineMove = {
  move: string;
  from_square: string;
  to_square: string;
  promotion: string | null;
};

function getStatus(game: Chess, thinking: boolean, settings: GameSettings): string {
  const humanChar = settings.color === "white" ? "w" : "b";
  const vsAi = settings.mode === "ai";

  if (game.isCheckmate()) {
    const loser = game.turn();
    if (vsAi) return loser === humanChar ? "Checkmate — the AI wins." : "Checkmate — you win!";
    return loser === "w" ? "Checkmate — Black wins." : "Checkmate — White wins.";
  }
  if (game.isStalemate()) return "Draw by stalemate.";
  if (game.isDraw()) return "Draw.";
  if (thinking) return "AI is thinking…";

  const check = game.inCheck() ? " — check!" : "";
  if (vsAi) return game.turn() === humanChar ? `Your move${check}` : `AI to move${check}`;
  return `${game.turn() === "w" ? "White" : "Black"} to move${check}`;
}

type Props = { settings: GameSettings; onExit: () => void };

export default function Game({ settings, onExit }: Props) {
  const [game] = useState(() => new Chess());
  const [fen, setFen] = useState(game.fen());
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const vsAi = settings.mode === "ai";
  const humanChar = settings.color === "white" ? "w" : "b";
  const aiChar = humanChar === "w" ? "b" : "w";
  const depth = DEPTH[settings.difficulty];

  async function playAiMove() {
    setThinking(true);
    setError(null);
    try {
      const response = await fetch("/api/move", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fen: game.fen(), depth }),
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

  const openedRef = useRef(false);
  useEffect(() => {
    if (openedRef.current) return;
    openedRef.current = true;
    if (vsAi && aiChar === "w") void playAiMove();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function onPieceDrop({ sourceSquare, targetSquare }: PieceDropHandlerArgs): boolean {
    if (!targetSquare || thinking || game.isGameOver()) return false;
    if (vsAi && game.turn() !== humanChar) return false;

    try {
      game.move({ from: sourceSquare, to: targetSquare, promotion: "q" });
    } catch {
      return false; // illegal move: piece snaps back
    }
    setFen(game.fen());

    if (vsAi && !game.isGameOver()) void playAiMove();
    return true;
  }

  function newGame() {
    game.reset();
    setFen(game.fen());
    setError(null);
    if (vsAi && aiChar === "w") void playAiMove();
  }

  const aiStuck = vsAi && !thinking && game.turn() === aiChar && !game.isGameOver();

  return (
    <div style={{ width: "min(90vw, 560px)", margin: "2rem auto", textAlign: "center" }}>
      <p style={{ fontSize: "1.2rem", fontWeight: 600, margin: "0 0 0.25rem" }}>
        {getStatus(game, thinking, settings)}
      </p>
      <p style={{ margin: "0 0 1rem", opacity: 0.7 }}>
        {vsAi ? `vs AI (${settings.difficulty}) · you are ${settings.color}` : "Two players"}
      </p>

      <Chessboard
        options={{
          position: fen,
          onPieceDrop,
          pieces: customPieces,
          boardOrientation: vsAi ? settings.color : "white",
          lightSquareStyle: { backgroundColor: "#f0d9b5" },
          darkSquareStyle: { backgroundColor: "#b58863" },
        }}
      />

      {error && <p style={{ color: "#c0392b", marginTop: "1rem" }}>⚠ {error}</p>}

      <div className="game-actions">
        <button className="game-btn" onClick={newGame} disabled={thinking}>New game</button>
        <button className="game-btn" onClick={onExit}>Main menu</button>
        {aiStuck && <button className="game-btn" onClick={() => void playAiMove()}>Retry AI move</button>}
      </div>
    </div>
  );
}