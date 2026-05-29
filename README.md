# Snip — URL Shortener Backend

A fast, lightweight URL shortener API built with **FastAPI** + **PostgreSQL**.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/shorten` | Shorten a URL |
| `GET` | `/{short_code}` | Redirect to original URL (301) |
| `GET` | `/api/stats/{short_code}` | Get click stats |
| `GET` | `/` | Health check |

### POST /api/shorten

```json
// Request
{ "url": "https://example.com/really/long/path" }

// Response (201)
{ "short_code": "a8f3k2", "short_url": "https://kennyy.me/a8f3k2" }
```

### GET /api/stats/{short_code}

```json
// Response
{
  "url": "https://example.com/really/long/path",
  "short_code": "a8f3k2",
  "short_url": "https://kennyy.me/a8f3k2",
  "clicks": 42,
  "created_at": "2026-05-29T08:00:00+00:00"
}
```

---

## Local Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your local Postgres credentials

# Run the server
uvicorn main:app --reload --port 8000
```

The API docs are available at [localhost:8000/docs](http://localhost:8000/docs).

---

## Deploy to Railway

### 1. Create a Railway project

Go to [railway.app](https://railway.app) and create a new project.

### 2. Add a PostgreSQL database

- Click **"+ New"** → **Database** → **PostgreSQL**
- Railway will provision a Postgres instance automatically

### 3. Deploy the backend

- Click **"+ New"** → **GitHub Repo** (connect your repo)
- Set the **Root Directory** to `backend`
- Railway will auto-detect the Python app

### 4. Configure environment variables

In the service **Settings → Variables**, add:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (use the Railway reference) |
| `BASE_URL` | `https://kennyy.me` (your production domain) |
| `ALLOWED_ORIGINS` | `https://kennyy.me` |

### 5. Set the start command

In **Settings → Deploy → Start Command**:

```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 6. Add a custom domain (optional)

Under **Settings → Networking → Public Networking**, generate a Railway domain or add your custom domain.

### 7. Verify

```bash
curl https://your-domain.railway.app/
# → {"status":"ok","service":"snip"}

curl -X POST https://your-domain.railway.app/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://google.com"}'
# → {"short_code":"abc123","short_url":"https://kennyy.me/abc123"}
```

---

## Project Structure

```
backend/
├── main.py            # FastAPI app — routes + middleware
├── models.py          # SQLAlchemy ORM models
├── database.py        # DB engine + session setup
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
└── README.md          # This file
```
