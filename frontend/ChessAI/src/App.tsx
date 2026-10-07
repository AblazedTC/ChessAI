import { useRef, useState } from "react";
import { Chess } from "chess.js";
import { Chessboard, type PieceDropHandlerArgs } from "react-chessboard";
import { customPieces } from "./customPieces";

export default function App() {
  const gameRef = useRef(new Chess());
  const game = gameRef.current;
  const [fen, setFen] = useState(game.fen());

  function onPieceDrop({ sourceSquare, targetSquare }: PieceDropHandlerArgs): boolean {
    if (!targetSquare) return false; // dropped outside the board

    try {
      game.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: "q",
      });
      setFen(game.fen());
      return true;
    } catch {
      return false; // illegal move: piece snaps back
    }
  }

  return (
    <div style={{ width: "min(90vw, 560px)", margin: "2rem auto" }}>
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
    </div>
  );
}