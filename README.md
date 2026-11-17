## Tech Stack
React

Python

FastAPI

## Deployment
Frontend on Vercel, backend on Render — see [DEPLOYMENT.md](./DEPLOYMENT.md).

## Chess Engine
The AI runs Stockfish in the browser via WebAssembly ([stockfish.js](https://github.com/nmrugg/stockfish.js), GPL-3.0, lite single-threaded build). The engine files are copied into `frontend/ChessAI/public/stockfish` automatically by `npm run dev` / `npm run build`.

If the in-browser engine fails to load, the frontend falls back to the backend, which calls the hosted Stockfish API at https://chess-api.com/.

## Piece Assests Credit
Wikipedia user: Cburnett, CC BY-SA 3.0 <https://creativecommons.org/licenses/by-sa/3.0>, via Wikimedia Commons

## React Chess Link
https://react-chessboard.vercel.app/?path=/docs/get-started--docs