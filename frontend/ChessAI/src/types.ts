export type Mode = "ai" | "local";
export type Difficulty = "Easy" | "Normal" | "Hard" | "GM";
export type Side = "white" | "black";

export type GameSettings = {
  mode: Mode;
  difficulty: Difficulty; // only used when mode === "ai"
  color: Side;
};

// Search depth sent to the engine for each difficulty
export const DEPTH: Record<Difficulty, number> = {
  Easy: 1,
  Normal: 6,
  Hard: 9,
  GM: 12,
};
