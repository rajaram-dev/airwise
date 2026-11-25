# Deployment — AirWise

## 1. Requirements

- Python 3.11+
- Node 20+ (only to run frontend tests)
- A Gemini API key from https://aistudio.google.com (free)

## 2. Run locally

```bash
git clone <repo-url>
cd <repo>
python -m venv .venv
.venv\Scripts\activate                    # Windows
# source .venv/bin/activate               # macOS / Linux
pip install -r requirements.txt -r requirements-dev.txt
copy .env.example .env                    # cp on macOS / Linux; then set GEMINI_API_KEY
uvicorn app.main:app --reload
```

Open http://localhost:8000 · API docs at http://localhost:8000/docs.

Without a `GEMINI_API_KEY` the app still works in rule-based mode.

## 3. Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | No* | — | Enables AI wording and chat (*rules-only mode without it) |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Gemini model name |
| `ALLOWED_ORIGINS` | No | `http://localhost:8000` | CORS allow-list, comma-separated |
| `CACHE_TTL_SECONDS` | No | `600` | Air data cache TTL |
| `RATE_LIMIT_PLAN` | No | `10/minute` | Plan rate limit per IP |
| `RATE_LIMIT_CHAT` | No | `20/minute` | Chat rate limit per IP |
| `LOG_LEVEL` | No | `INFO` | Log verbosity |

## 4. Deploy to Render (free tier)

1. Push the repo to GitHub (public, `main` only).
2. Render → **New → Web Service** → connect the repo.
3. Settings:
   - Runtime: Python
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers`
   - Health check path: `/api/v1/health`
4. Add environment variables (above) in **Environment** — set `ALLOWED_ORIGINS` to the Render URL.
5. Deploy and put the live URL in the README.

Note: free Render services sleep when idle; the first request can take ~30–60 s. Open the demo
link once before recording the video or before judging windows.

## 5. Alternative: Docker (any host, e.g. Cloud Run, Railway)

A `Dockerfile` will be added with the code:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY static ./static
RUN useradd --create-home appuser
USER appuser
ENV PORT=8080
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers"]
```

## 6. Submission checklist

- [ ] Repo is **public**, only branch is `main`, size < 10 MB
- [ ] README complete: vertical, approach, how it works, assumptions, live link, video link
- [ ] No secrets in repo or history
- [ ] CI green
- [ ] Live demo opens and generates a plan
- [ ] Demo video uploaded (YouTube unlisted or Drive with access) and linked
- [ ] Submission attempt count tracked (max 3)
