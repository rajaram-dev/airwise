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
| `GEMINI_MODEL` | No | `gemini-3.5-flash-lite` | Main Gemini model |
| `GEMINI_FALLBACK_MODELS` | No | `gemini-flash-lite-latest,gemini-2.5-flash` | Tried in order if the main model fails |
| `AI_CACHE_TTL_SECONDS` | No | `3600` | Reuse identical AI plan wording (saves quota) |
| `ALLOWED_ORIGINS` | No | `http://localhost:8000` | CORS allow-list, comma-separated |
| `CACHE_TTL_SECONDS` | No | `600` | Air data cache TTL |
| `RATE_LIMIT_PLAN` | No | `10/minute` | Plan rate limit per IP |
| `RATE_LIMIT_CHAT` | No | `20/minute` | Chat rate limit per IP |
| `LOG_LEVEL` | No | `INFO` | Log verbosity |

## 4. Deploy to Render (free tier) — Blueprint

All settings live in [`render.yaml`](../render.yaml), so deployment is a few clicks:

1. Sign in at https://render.com with the GitHub account that owns the repo.
2. **New → Blueprint** → choose the `airwise` repository → Render reads `render.yaml`.
3. When asked, paste your Gemini key into **GEMINI_API_KEY** (marked `sync: false`, so it is
   stored only in Render, never in the repo).
4. Click **Apply / Deploy**. The first build takes a few minutes; Render checks
   `/api/v1/health` before sending traffic.
5. Open the `https://airwise-….onrender.com` URL and put it in the README.

What the blueprint sets: Python 3.12, `pip install -r requirements.txt`, start command
`uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers`, `FORWARDED_ALLOW_IPS=*`
(trust Render's proxy so per-IP rate limits and HTTPS detection use the real client), health
check, auto-deploy on every push to `main`.

`ALLOWED_ORIGINS` does not need changing: the page and the API are served from the same origin.

Note: free Render services sleep when idle; the first request can take ~30–60 s. Open the demo
link once before recording the video or before judging windows.

## 5. Alternative: Docker (any host, e.g. Cloud Run, Railway)

The repo includes a [`Dockerfile`](../Dockerfile) (Python 3.12 slim, non-root user, port from
`$PORT`) and a `.dockerignore` that keeps `.env`, tests, docs and original images out of the image.

```bash
docker build -t airwise .
docker run -p 8080:8080 -e GEMINI_API_KEY=your-key airwise
```

## 6. Submission checklist

- [ ] Repo is **public**, only branch is `main`, size < 10 MB
- [ ] README complete: vertical, approach, how it works, assumptions, live link, video link
- [ ] No secrets in repo or history
- [ ] CI green
- [x] Live demo opens and generates a plan (https://airwise-cuu3.onrender.com)
- [ ] Demo video uploaded (YouTube unlisted or Drive with access) and linked
- [ ] Submission attempt count tracked (max 3)
