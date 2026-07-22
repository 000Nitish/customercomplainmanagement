# Deployment Guide (Supabase + Render/Vercel)

## Architecture for Production

```
Vercel (Frontend)  →  Render/Railway (FastAPI)  →  Supabase PostgreSQL
     React              LangGraph + Groq              Managed Postgres
```

## Step 1: Supabase Project Setup

1. Go to [supabase.com](https://supabase.com) → **New Project**
2. Choose region close to your backend host
3. Save the database password securely

### Get connection strings

**Supabase Dashboard → Project Settings → Database → Connection string**

| Use case | Connection type | Port |
|----------|--------------|------|
| App runtime (`DATABASE_URL`) | **Session pooler** | 5432 |
| Alembic migrations (`DIRECT_URL`) | **Direct connection** | 5432 |

Example (replace placeholders):

```env
DATABASE_URL=postgresql://postgres.abcdefghijklmnop:[PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:5432/postgres
DIRECT_URL=postgresql://postgres:[PASSWORD]@db.abcdefghijklmnop.supabase.co:5432/postgres
```

> **Password tip:** If your password has special characters (`@`, `#`, `%`), URL-encode them in the connection string.

### Create tables

**Option A — Alembic (recommended)**

```bash
cd backend
pip install -r requirements.txt
# Set DATABASE_URL and DIRECT_URL in .env first
alembic upgrade head
```

**Option B — Supabase SQL Editor**

Copy and run [`supabase_schema.sql`](./supabase_schema.sql) in **SQL Editor**.

---

## Step 2: Deploy Backend (Render)

1. Push repo to GitHub
2. [Render](https://render.com) → **New Web Service** → connect repo
3. Settings:

| Setting | Value |
|---------|-------|
| Root Directory | `backend` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Environment | Python 3 |

4. **Environment Variables:**

```
GROQ_API_KEY=gsk_...
DATABASE_URL=postgresql://postgres.[ref]:[pass]@...pooler.supabase.com:5432/postgres
DIRECT_URL=postgresql://postgres:[pass]@db.[ref].supabase.co:5432/postgres
FRONTEND_URL=https://your-frontend.vercel.app
UPLOAD_DIR=/tmp/uploads
```

5. After first deploy, run migrations (Render Shell or locally with same env):

```bash
alembic upgrade head
```

Backend URL example: `https://pharma-qms-api.onrender.com`

---

## Step 3: Deploy Frontend (Vercel)

1. [Vercel](https://vercel.com) → **Import Project** → select repo
2. Settings:

| Setting | Value |
|---------|-------|
| Root Directory | `frontend` |
| Build Command | `npm run build` |
| Output Directory | `dist` |
| Framework | Vite |

3. **Environment Variable:**

```
VITE_API_URL=https://pharma-qms-api.onrender.com
```

4. Redeploy after adding the env var.

---

## Step 4: Verify

- Backend health: `GET https://your-api.onrender.com/health`
- API docs: `https://your-api.onrender.com/docs`
- Frontend loads dashboard with seed complaints (created on first backend startup)

---

## Alternative: Railway (Backend)

`backend/railway.toml` is included. Deploy with:

```bash
cd backend
railway login
railway init
railway up
```

Set the same env vars in Railway dashboard.

---

## Supabase-specific notes

- **SSL** is auto-enabled when the host contains `supabase.co` / `supabase.com`
- Use **Session pooler** for FastAPI long-running processes
- Use **Direct URL** only for migrations — not for app runtime on port 6543 transaction pooler unless you use NullPool
- **Uploads:** Render ephemeral disk — for production file storage, migrate to Supabase Storage (future enhancement)
- **Free tier:** Supabase pauses inactive projects; wake before demo

---

## Local dev with Supabase (no local Postgres)

```bash
cp .env.example .env
# Paste Supabase DATABASE_URL + DIRECT_URL

cd backend && pip install -r requirements.txt && alembic upgrade head
uvicorn app.main:app --reload

cd frontend && npm install && npm run dev
```

No local PostgreSQL install needed.
