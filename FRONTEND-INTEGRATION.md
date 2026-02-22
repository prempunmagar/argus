# Frontend Integration Guide (Backend → Frontend)

This document is for the **frontend team**. It describes the **config and env changes** needed to connect the dashboard to the Argus backend — whether the backend is running via **Docker** or **locally** — and how to run and test.

The frontend already has its own docs; this only covers **connecting to the backend**.

---

## 1. What the backend exposes

- **REST API base:** `http://localhost:8000/api/v1` (when backend runs on default port)
- **WebSocket (dashboard):** `ws://localhost:8000/ws/dashboard` (JWT via `?token=...`)

Backend CORS is configured to allow `http://localhost:3000` and `http://localhost:5173` (Vite default), so the dev server can call the API without CORS errors.

---

## 2. Frontend env / config (what to set)

The frontend uses **Vite**, so all env vars must be prefixed with `VITE_` to be available in the app.

Create a file in the **frontend** repo root:

**`frontend/.env`** or **`frontend/.env.local`**

```env
# Point to the Argus backend (Docker or local)
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws/dashboard
```

- **If these are not set**, the app falls back to the same defaults (`localhost:8000`) but some features use **mock data** instead of the real API. Setting them ensures the dashboard talks to the real backend.
- **If the backend runs on another host/port** (e.g. another machine or port), change the host/port in both vars (e.g. `http://192.168.1.10:8000/api/v1` and `ws://192.168.1.10:8000/ws/dashboard`).

No other frontend config changes are required; the app already reads `VITE_API_URL` and `VITE_WS_URL` in `src/lib/api.ts` and `src/hooks/useWebSocket.ts`.

---

## 3. Connecting to the Docker setup

When the backend runs in Docker (from the **project root**):

```bash
docker compose up -d
```

- The API is available at **`http://localhost:8000`** (mapped from the container).
- The frontend runs **on your machine** (not in Docker). Use the same URLs as above.

**Steps for frontend:**

1. From project root, start the backend:  
   `docker compose up -d`
2. In the **frontend** directory, ensure `frontend/.env` (or `.env.local`) contains:
   - `VITE_API_URL=http://localhost:8000/api/v1`
   - `VITE_WS_URL=ws://localhost:8000/ws/dashboard`
3. Install and run the frontend (e.g. `npm install && npm run dev`).
4. Open the app (e.g. `http://localhost:5173`) and log in with the seed user (see below). The dashboard will use the backend in Docker.

---

## 4. Connecting to a locally run backend (no Docker)

When the backend is run directly on the host (e.g. for backend development):

```bash
cd backend
# create/use venv, then e.g.:
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- The API is still at **`http://localhost:8000`** (and WebSocket at `ws://localhost:8000/ws/dashboard`).
- Use the **same** `frontend/.env` (or `.env.local`) as in section 2. No change needed from the Docker case if the backend is on the same machine and port.

---

## 5. Quick test checklist

1. **Backend up:** Docker (`docker compose up -d`) or local (`uvicorn` on port 8000).
2. **Frontend env:** `VITE_API_URL` and `VITE_WS_URL` set in `frontend/.env` or `frontend/.env.local` (see section 2).
3. **Restart dev server:** After changing `.env`, restart the Vite dev server so it picks up the new values.
4. **Login:** Use the seed user:
   - Email: `demo@argus.dev`
   - Password: `argus2026`
5. **Smoke test:** Open dashboard, check transactions/categories/agent keys load from the API (not mock). Open WebSocket-backed views (e.g. real-time updates) if applicable.

---

## 6. Summary table

| Scenario              | Backend command / setup      | Frontend env (in `frontend/`)                                                                 |
|-----------------------|-----------------------------|------------------------------------------------------------------------------------------------|
| Backend in Docker     | `docker compose up -d`      | `VITE_API_URL=http://localhost:8000/api/v1`<br>`VITE_WS_URL=ws://localhost:8000/ws/dashboard`   |
| Backend run locally   | `uvicorn` on port 8000      | Same as above                                                                                  |
| Backend on other host | e.g. `http://HOST:8000`     | `VITE_API_URL=http://HOST:8000/api/v1`<br>`VITE_WS_URL=ws://HOST:8000/ws/dashboard`             |

No other config or env changes are required on the frontend to connect to the Docker setup or to run and test against the backend.
