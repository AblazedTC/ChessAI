import { useState } from "react";
import type { Difficulty, GameSettings, Mode, Side } from "./types";
import "./StartScreen.css";

type Props = { onStart: (settings: GameSettings) => void };

const DIFFICULTIES: { value: Difficulty; hint: string }[] = [
  { value: "Easy", hint: "Cannot see more than a move ahead" },
  { value: "Normal", hint: "Solid play; gives the average player a chance" },
  { value: "Hard", hint: "Strong play; difficult for most people" },
  { value: "GM", hint: "Grandmaster level play" },
];

const COLORS: { value: Side | "random"; label: string; glyph: string }[] = [
  { value: "white", label: "White", glyph: "♔" },
  { value: "random", label: "Random", glyph: "♔♚" },
  { value: "black", label: "Black", glyph: "♚" },
];

export default function StartScreen({ onStart }: Props) {
  const [mode, setMode] = useState<Mode>("ai");
  const [difficulty, setDifficulty] = useState<Difficulty>("Normal");
  const [color, setColor] = useState<Side | "random">("white");

  function start() {
    const resolved: Side = color === "random" ? (Math.random() < 0.5 ? "white" : "black") : color;
    onStart({ mode, difficulty, color: resolved });
  }

  return (
    <main className="start">
      <h1 className="start-title">ChessAI</h1>

      <section className="start-section">
        <h2>Opponent</h2>
        <div className="seg seg-2" role="radiogroup" aria-label="Opponent">
          <button role="radio" aria-checked={mode === "ai"} onClick={() => setMode("ai")}>
            Computer
          </button>
          <button role="radio" aria-checked={mode === "local"} onClick={() => setMode("local")}>
            Another person
          </button>
        </div>
        {mode === "local" && <p className="start-note">Two players share this screen and take turns.</p>}
      </section>

      {mode === "ai" && (
        <>
          <section className="start-section">
            <h2>Difficulty</h2>
            <div className="seg seg-4" role="radiogroup" aria-label="Difficulty">
              {DIFFICULTIES.map((d) => (
                <button
                  key={d.value}
                  role="radio"
                  aria-checked={difficulty === d.value}
                  onClick={() => setDifficulty(d.value)}
                >
                  {d.value}
                </button>
              ))}
            </div>
            <p className="start-note">{DIFFICULTIES.find((d) => d.value === difficulty)?.hint}</p>
          </section>

          <section className="start-section">
            <h2>Play as</h2>
            <div className="seg seg-3 seg-color" role="radiogroup" aria-label="Your color">
              {COLORS.map((c) => (
                <button
                  key={c.value}
                  role="radio"
                  aria-checked={color === c.value}
                  onClick={() => setColor(c.value)}
                >
                  <span className="glyph" aria-hidden="true">{c.glyph}</span>
                  {c.label}
                </button>
              ))}
            </div>
          </section>
        </>
      )}

      <button className="start-go" onClick={start}>
        Start game
      </button>
    </main>
  );
}
