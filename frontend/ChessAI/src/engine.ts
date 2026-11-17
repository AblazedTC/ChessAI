// Runs Stockfish in the browser via WebAssembly (stockfish.js "lite single-threaded"
// build). The engine files are copied from node_modules/stockfish into
// public/stockfish by scripts/copy-engine.mjs before dev/build.
const ENGINE_URL = "/stockfish/stockfish-19-lite-single.js";

export type UciMove = { from: string; to: string; promotion?: string };

let worker: Worker | null = null;
let ready: Promise<Worker> | null = null;

function waitFor(w: Worker, send: string, expected: (line: string) => boolean, timeoutMs: number): Promise<string> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      cleanup();
      reject(new Error("The in-browser engine timed out."));
    }, timeoutMs);
    const onMessage = (e: MessageEvent) => {
      const line = String(e.data);
      if (expected(line)) {
        cleanup();
        resolve(line);
      }
    };
    const onError = () => {
      cleanup();
      reject(new Error("The in-browser engine crashed."));
    };
    function cleanup() {
      clearTimeout(timer);
      w.removeEventListener("message", onMessage);
      w.removeEventListener("error", onError);
    }
    w.addEventListener("message", onMessage);
    w.addEventListener("error", onError);
    w.postMessage(send);
  });
}

function reset() {
  worker?.terminate();
  worker = null;
  ready = null;
}

// Start the engine (downloads ~1.9 MB the first time, then cached by the browser)
export function loadEngine(): Promise<Worker> {
  if (!ready) {
    ready = (async () => {
      worker = new Worker(ENGINE_URL);
      await waitFor(worker, "uci", (l) => l === "uciok", 20_000);
      await waitFor(worker, "isready", (l) => l === "readyok", 20_000);
      return worker;
    })();
    ready.catch(reset);
  }
  return ready;
}

export async function getBestMove(fen: string, depth: number): Promise<UciMove> {
  const w = await loadEngine();
  w.postMessage(`position fen ${fen}`);
  try {
    const line = await waitFor(w, `go depth ${depth}`, (l) => l.startsWith("bestmove"), 30_000);
    const move = line.split(" ")[1];
    if (!move || move === "(none)") throw new Error("The engine did not return a move.");
    return { from: move.slice(0, 2), to: move.slice(2, 4), promotion: move[4] };
  } catch (err) {
    reset(); // a stuck or crashed engine is restarted on the next request
    throw err;
  }
}
