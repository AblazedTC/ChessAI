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

const makePiece = (src: string) => () => (
  <img
    src={src}
    alt=""
    draggable={false}
    style={{ width: "100%", height: "100%", objectFit: "contain" }}
  />
);

export const customPieces: PieceRenderObject = {
  wP: makePiece(wP),
  wN: makePiece(wN),
  wB: makePiece(wB),
  wR: makePiece(wR),
  wQ: makePiece(wQ),
  wK: makePiece(wK),
  bP: makePiece(bP),
  bN: makePiece(bN),
  bB: makePiece(bB),
  bR: makePiece(bR),
  bQ: makePiece(bQ),
  bK: makePiece(bK),
};