# Deploying ChessAI

The app is deployed as two services:

| Part     | Host   | Source directory    | Config file                    |
| -------- | ------ | ------------------- | ------------------------------ |
| Backend  | Render | `backend/`          | `render.yaml` (repo root)      |
| Frontend | Vercel | `frontend/ChessAI/` | `frontend/ChessAI/vercel.json` |

The frontend calls the backend directly from the browser, so the backend
must allow the frontend's origin via CORS (`ALLOWED_ORIGINS`), and the
frontend must know the backend's URL (`VITE_API_URL`).

## 1. Backend on Render

1. In the Render dashboard choose **New → Blueprint** and select this
   repository (and the branch you want to deploy).
2. Render reads `render.yaml` and creates the `chessai-api` web service:
   - Root directory: `backend`
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Health check: `GET /health`
3. When prompted, set `ALLOWED_ORIGINS`. You can leave it blank for now and
   fill it in after the frontend is deployed (step 2). Preview deployments on
   `*.vercel.app` are always allowed.
4. After the first deploy, note the service URL, e.g.
   `https://chessai-api.onrender.com`. Visit `/health` to confirm it returns
   `{"status": "ok"}`.

Environment variables:

| Name              | Required | Description                                                                 |
| ----------------- | -------- | --------------------------------------------------------------------------- |
| `ALLOWED_ORIGINS` | yes      | Comma-separated frontend origins, e.g. `https://chessai.vercel.app`         |
| `CHESS_API_URL`   | no       | Stockfish endpoint (defaults to `https://chess-api.com/v1`)                 |
| `PYTHON_VERSION`  | no       | Pinned in `render.yaml` and `backend/.python-version` (3.13.9)              |

> The free Render plan spins the service down after inactivity; the first
> request after idling can take ~30–60 s.

## 2. Frontend on Vercel

1. In Vercel choose **Add New → Project** and import this repository.
2. Set **Root Directory** to `frontend/ChessAI`. Vercel detects Vite and uses
   `npm run build` / `dist` (also declared in `vercel.json`).
3. Under **Environment Variables** add:

   | Name           | Value                                             |
   | -------------- | ------------------------------------------------- |
   | `VITE_API_URL` | Your Render URL, e.g. `https://chessai-api.onrender.com` (no trailing slash) |

   `VITE_*` variables are baked in at build time, so redeploy after changing it.
4. Deploy. Note the production URL, e.g. `https://chessai.vercel.app`.

## 3. Connect the two

1. Back in Render, set `ALLOWED_ORIGINS` on `chessai-api` to the Vercel
   production URL from step 2 (comma-separate multiple origins). Render
   redeploys automatically.
2. Open the Vercel URL, make a move, and confirm the AI responds. If the
   browser console shows a CORS error, double-check `ALLOWED_ORIGINS` matches
   the origin exactly (scheme + host, no path or trailing slash).

## Local development

Nothing changes locally: leave `VITE_API_URL` unset (see
`frontend/ChessAI/.env.example`) and Vite proxies `/api/*` to
`http://127.0.0.1:8000`, which is already in the backend's default
`ALLOWED_ORIGINS`.
