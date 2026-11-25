# Architecture — AirWise

## 1. Overview

A single FastAPI service serves both the JSON API and the static frontend. There is no database.
External calls go to Open-Meteo (air quality, geocoding) and Gemini (text generation).

```
┌──────────────────────────┐        ┌───────────────────────────────────────────────┐
│ Browser                  │        │ FastAPI app                                   │
│  static/index.html       │  HTTPS │  core/  security headers, rate limit, errors  │
│  js/ (ES modules)        ├───────►│  api/   routes → validate with Pydantic       │
│  - api.js  fetch wrapper │        │   │                                           │
│  - render/*  DOM output  │        │   ▼                                           │
│  - chat.js               │        │  rules/  aqi · risk · windows ·               │
└──────────────────────────┘        │          recommendations · impact  (pure)     │
                                    │   │                                           │
                                    │   ▼                                           │
                                    │  services/ air_quality ─► Open-Meteo AQ API   │
                                    │            geocoding   ─► Open-Meteo Geocode  │
                                    │            gemini      ─► Gemini API          │
                                    │            cache (in-memory TTL)              │
                                    └───────────────────────────────────────────────┘
```

## 2. Design principles

1. **Rules decide, AI explains.** Business logic is deterministic and testable; the LLM only
   writes language. See [ai-design.md](ai-design.md).
2. **Pure core, thin edges.** `rules/` has no I/O — easy to test. `services/` wrap all I/O.
3. **Fail soft.** If Gemini fails → rule-based text. If Open-Meteo fails → clear error, no crash.
4. **Stateless server.** No sessions, no database; horizontal scaling is trivial.

## 3. Folder structure

```
app/
  main.py                # app factory: middleware, routers, static mount
  config.py              # Settings (pydantic-settings) loaded from env
  api/
    routes.py            # /api/v1: health, geocode, air, plan, chat (with rate limits)
    deps.py              # Services container + dependency; wires real clients
  models/
    profile.py           # UserProfile, Household, enums
    chat.py              # ChatRequest, ChatContext, ChatResponse
    air.py               # AirReading, ForecastHour, AirData
    plan.py              # Plan, Recommendation, Impact, Risk, TimeWindow
  rules/
    aqi.py               # AQI categories and thresholds (constants)
    context.py           # RuleContext: risk + windows computed once per request
    risk.py              # risk level from AQI + sensitivity
    windows.py           # best outdoor windows from forecast
    catalog.py           # recommendation catalogue (data)
    recommendations.py   # select + rank applicable recommendations
    impact.py            # compute impact numbers
    outlook.py           # 24-hour trend + insights (vs yesterday, WHO guideline)
    audience.py          # do/avoid tips for children, adults, sensitive people, pregnancy
  services/
    air_quality.py       # Open-Meteo client
    geocoding.py         # Open-Meteo geocoding client
    gemini.py            # Gemini wrapper: schema validation, number guard, timeout
    prompts.py           # versioned prompt constants (PLAN_SYSTEM_PROMPT_V2, CHAT_SYSTEM_PROMPT_V2)
    chat.py              # scoped follow-up chat with fallback
    plan_builder.py      # orchestrates: air → rules → AI → merge
  core/
    security.py          # headers, body-size limit, cache policy, rate limiter
    errors.py            # domain exceptions
    handlers.py          # exception -> safe JSON error responses
    logging.py           # structured logging without PII
static/
  index.html
  img/  sky-*.webp · person-*.webp · branch.webp  (optimised illustrations)
  css/  tokens.css · base.css · components.css
  js/   main.js · api.js · state.js · chat.js
        render/ air.js · chart.js · plan.js · form.js
        utils/  aqi.js · art.js · chart.js · format.js · dom.js · icons.js · markdown.js
tests/
  unit/         # rules/*, models
  integration/  # API routes with mocked services
  frontend/     # node:test for js/utils
docs/
```

## 4. Request flow — `POST /api/v1/plan`

1. Route validates `PlanRequest` (Pydantic) → 422 on bad input.
2. `plan_builder` gets air data via `air_quality` (cache hit → no network call).
3. `rules.risk` → risk level + reasons.
4. `rules.windows` → best outdoor windows (next 24 h, 06:00–22:00 local).
5. `rules.recommendations` → applicable items from `catalog`, ranked.
6. `rules.impact` → numbers per item (computed from forecast where possible).
7. `services.gemini` → summary + friendly wording, validated against JSON schema.
8. Merge AI text into rule items **by id**; numbers always from rules.
9. On any AI failure → use catalogue default text; `source: "rules"`.
10. Return `Plan` JSON.

## 5. Performance (Efficiency)

| Technique | Detail |
|---|---|
| Caching | Air data cached per rounded lat/lon (2 dp) for `CACHE_TTL_SECONDS` (600 s). Geocode cached 24 h. |
| One AI call per plan | Summary + all item wording in a single structured request. |
| Small AI payload | Send only selected items and a compact profile, not raw forecast. |
| Async I/O | `httpx.AsyncClient` shared per app; timeouts on every call (AQ 8 s, Gemini 15 s). |
| Lean frontend | No framework, no web fonts, no images except inline SVG icons; target < 100 KB. |
| Static caching | `Cache-Control` for `/static` assets. |
| Compression | GZip middleware for JSON and static responses. |

## 6. Error handling

| Failure | Behaviour |
|---|---|
| Invalid input | 422 with field errors (no stack traces) |
| Location not found | 404 `{ "error": "location_not_found" }` |
| Open-Meteo down/timeout | 503 `{ "error": "air_data_unavailable" }`, UI shows retry |
| Gemini error/timeout/invalid JSON | Plan still returned with `source: "rules"` |
| Rate limit exceeded | 429 with `Retry-After` |
| Unexpected | 500 generic message; details logged server-side only |

## 7. Configuration

All config via environment variables, loaded once in `config.py`. See `.env.example`.

## 8. Key decisions

| Decision | Reason |
|---|---|
| No database | No user data to store → smaller attack surface, simpler deploy |
| FastAPI | Async, built-in validation and OpenAPI docs |
| Vanilla JS | Performance, accessibility control, zero build step, small repo |
| Open-Meteo | Free, no key, hourly forecast for any coordinate |
| Gemini | Free tier, structured JSON output support |
