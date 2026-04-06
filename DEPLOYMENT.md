# Deployment guide (Vercel frontend + Render backend + Render Postgres)

This guide keeps everything simple: no Docker/Kubernetes required for your workflow.

## 1) Backend: Render Postgres + web service

### A. Create Postgres DB
1. Go to Render dashboard → New → PostgreSQL.
2. Set name: `fbreflect-db` (or your name), plan: free/dev/prod.
3. Create and wait for `DATABASE_URL`.

### B. Create backend web service
1. Render → New → Web Service.
2. Connect to repository and choose directory: `/backend`.
3. Runtime: `Python` (render supports Python directly).
4. Build command:
   - `pip install -r requirements.txt`
5. Start command:
   - `gunicorn -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:$PORT --workers 2 --log-level info`
6. Health check path: `/health`.
7. Environment variables (secure):
   - `ENV=production`
   - `SECRET_KEY=<your-secret>`
   - `ALGORITHM=HS256`
   - `ACCESS_TOKEN_EXPIRE_MINUTES=60`
   - `DATABASE_URL=<render-postgres-url>`
   - `CORS_ORIGINS=https://<frontend-vercel-url>`
   - `COOKIE_DOMAIN=<frontend-host>` (optionally, if needed)

8. Deploy and verify `/health` returns `{"status":"ok"}`.

## 2) Frontend: Vercel

1. Vercel → New Project → Import from GitHub.
2. Select repository and root path: `/frontend`.
3. Build command: `npm install && npm run build`.
4. Output directory: `dist`.
5. Environment variable (production):
   - `VITE_API_URL=https://<render-backend-url>`
6. Deploy.
7. Verify app load and authentication API calls.

## 3) Local dev (optional)

### Backend
```bash
cd backend
python -m venv backendenv
source backendenv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Test local environment values
- `.env.example` files in both backend and frontend.

## 4) Validate cross-site auth
- Confirm `Login` sets cookie header `Set-Cookie: access_token=...; HttpOnly; Secure; SameSite=None`.
- Confirm frontend fetches with `credentials: include` in `src/api/users.js`.
- Confirm `backend/app.py` has `CORS` with `allow_credentials=True` and `CORS_ORIGINS` set to front end domain.

## 5) Health & safety checklist
- `/` and `/health` accessible.
- `/auth/register`, `/auth/login`, `/feedback/me` working.
- `CORS_ORIGINS` to a safe list.
- No wildcard CORS in production.
- Add GitHub Actions for automated lint/test/deploy.
