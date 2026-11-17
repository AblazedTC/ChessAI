import type { PieceRenderObject } from "react-chessboard";

import wP from "./assets/WhitePawn.png";
import wN from "./assets/WhiteKnight.png";
import wB from "./assets/WhiteBishop.png";
import wR from "./assets/WhiteRook.png";
import wQ from "./assets/WhiteQueen.png";
import wK from "./assets/WhiteKing.png";
import bP from "./assets/BlackPawn.png";
import bN from "./assets/BlackKnight.png";
import bB from "./assets/BlackBishop.png";
import bR from "./assets/BlackRook.png";
import bQ from "./assets/BlackQueen.png";
import bK from "./assets/BlackKing.png";

// White pieces get a dark outline shadow so they don't blend into the light squares
const makePiece = (src: string, white = false) => () => (
  <img
    src={src}
    alt=""
    draggable={false}
    style={{
      width: "100%",
      height: "100%",
      objectFit: "contain",
      filter: white ? "drop-shadow(0 0 1px rgba(0, 0, 0, 0.9))" : undefined,
    }}
  />
);

export const customPieces: PieceRenderObject = {
  wP: makePiece(wP, true),
  wN: makePiece(wN, true),
  wB: makePiece(wB, true),
  wR: makePiece(wR, true),
  wQ: makePiece(wQ, true),
  wK: makePiece(wK, true),
  bP: makePiece(bP),
  bN: makePiece(bN),
  bB: makePiece(bB),
  bR: makePiece(bR),
  bQ: makePiece(bQ),
  bK: makePiece(bK),
};