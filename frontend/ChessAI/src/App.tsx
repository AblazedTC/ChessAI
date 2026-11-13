import { useState } from "react";
import StartScreen from "./StartScreen";
import Game from "./Game";
import type { GameSettings } from "./types";

export default function App() {
  const [settings, setSettings] = useState<GameSettings | null>(null);

  if (!settings) return <StartScreen onStart={setSettings} />;
  return <Game settings={settings} onExit={() => setSettings(null)} />;
}
