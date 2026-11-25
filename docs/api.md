# API — AirWise

Base path: `/api/v1` · Format: JSON · Interactive docs: `/docs` (FastAPI OpenAPI).

All error responses use:

```json
{ "error": "machine_code", "message": "Human-readable message" }
```

| Status | `error` codes |
|---|---|
| 400 | `bad_request` |
| 404 | `location_not_found` |
| 422 | `validation_error` (includes `details[]`) |
| 429 | `rate_limited` (with `Retry-After` header) |
| 503 | `air_data_unavailable` |
| 500 | `internal_error` |

---

## GET /api/v1/health

Liveness check.

```json
{ "status": "ok", "version": "1.0.0" }
```

---

## GET /api/v1/geocode?q={query}

`q`: 2–100 chars. Returns up to 5 matches.

```json
{
  "results": [
    { "name": "Delhi", "country": "India", "admin1": "Delhi",
      "latitude": 28.65, "longitude": 77.23, "timezone": "Asia/Kolkata" }
  ]
}
```

---

## GET /api/v1/reverse-geocode?lat={lat}&lon={lon}

Town or city name for a coordinate (used after "Use my current location"). Coordinates are
rounded to 2 decimals (~1 km) before the lookup. 404 `location_not_found` if no named place.

```json
{ "name": "Lucknow", "country": "India", "admin1": "Uttar Pradesh",
  "latitude": 26.85, "longitude": 80.95, "timezone": "UTC" }
```

---

## GET /api/v1/air?lat={lat}&lon={lon}

Current reading + next 24 h forecast.

```json
{
  "current": {
    "aqi": 287, "category": "very_unhealthy", "category_label": "Very Unhealthy",
    "pm2_5": 212.4, "pm10": 340.1, "dominant_pollutant": "pm2_5",
    "observed_at": "2026-11-25T09:00:00+05:30",
    "health_message": "Everyone may experience health effects. Avoid outdoor exertion."
  },
  "forecast": [ { "time": "2026-11-25T10:00:00+05:30", "aqi": 279, "pm2_5": 205.0 } ],
  "timezone": "Asia/Kolkata"
}
```

---

## POST /api/v1/plan

Rate limit: `RATE_LIMIT_PLAN` (default 10/minute per IP).

### Request

```json
{
  "latitude": 28.61, "longitude": 77.21, "location_name": "Delhi",
  "household": { "children": true, "elderly": false, "respiratory_condition": true, "pregnant": false },
  "commute_mode": "car", "commute_minutes": 35, "commute_km": 12,
  "cooking_fuel": "lpg", "heating": "none", "has_air_purifier": false,
  "outdoor_activity": "evening_walk", "language": "en"
}
```

### Response

```json
{
  "location": { "name": "Delhi", "latitude": 28.61, "longitude": 77.21 },
  "air": { "aqi": 287, "category": "very_unhealthy", "category_label": "Very Unhealthy", "pm2_5": 212.4 },
  "risk": { "level": "severe", "reasons": ["Very Unhealthy air", "Child with a respiratory condition at home"] },
  "best_windows": [
    { "start": "2026-11-25T14:00:00+05:30", "end": "2026-11-25T16:00:00+05:30",
      "avg_aqi": 182, "avg_pm2_5": 110.5 }
  ],
  "recommendations": [
    {
      "id": "shift_activity_window",
      "category": "routine",
      "title": "Move your evening walk to 2–4 pm",
      "action": "Air is cleanest this afternoon. Keep the walk gentle and under 30 minutes.",
      "why": "Smog builds up after sunset when the air cools and traps pollution near the ground.",
      "impact": { "exposure_reduction_pct": 35, "co2_kg_saved_per_day": null, "note": null, "basis": "computed" },
      "priority": 90
    }
  ],
  "summary": "Delhi's air is Very Unhealthy today...",
  "outlook": { "trend": "steady", "headline": "Likely to remain Very Unhealthy over the next 24 hours." },
  "insights": [
    "Air quality is 18% worse than this time yesterday.",
    "PM2.5 is 14 times the WHO daily guideline of 15 µg/m³.",
    "Main pollutant: PM2.5, fine particles from traffic, burning and dust."
  ],
  "audiences": [
    { "audience": "children", "title": "For children", "subtitle": "Higher risk from today's air.",
      "tips": [ { "kind": "avoid", "text": "Avoid outdoor play and sports." } ] }
  ],
  "source": "ai",
  "disclaimer": "General guidance, not medical advice.",
  "generated_at": "2026-11-25T09:02:11+05:30"
}
```

- `category` ∈ `good`, `moderate`, `unhealthy_sensitive`, `unhealthy`, `very_unhealthy`, `hazardous`
- `risk.level` ∈ `low`, `moderate`, `high`, `severe`
- `recommendations[].category` ∈ `routine`, `indoor`, `alternative`
- `impact.basis` ∈ `computed`, `estimated`
- `impact.note`: qualitative impact text when no number applies (e.g. "Large reduction in indoor smoke")
- `best_windows` is empty when no daytime hour is clean enough for this household
- `outlook.trend` ∈ `improving`, `steady`, `worsening`
- `audiences[].audience` ∈ `children`, `adults`, `sensitive` (older adults, asthma, heart or lung conditions), `pregnancy` (adults always; others only if present at home); `tips[].kind` ∈ `do`, `avoid`
- `source` ∈ `ai`, `rules`

---

## POST /api/v1/chat

Rate limit: `RATE_LIMIT_CHAT` (default 20/minute per IP).

### Request

```json
{
  "message": "Can my son play cricket outside at 5 pm?",
  "context": {
    "location_name": "Delhi", "aqi": 287, "risk_level": "severe",
    "summary": "…", "item_titles": ["Move your evening walk to 2–4 pm"]
  },
  "history": [ { "role": "user", "text": "…" }, { "role": "assistant", "text": "…" } ],
  "language": "en"
}
```

Limits: `message` 1–500 chars; `history` ≤ 6 items, each ≤ 1000 chars.

### Response

```json
{ "reply": "At 5 pm the air is forecast to be Very Unhealthy…", "source": "ai" }
```

If Gemini is unavailable: `source: "unavailable"` with a short message suggesting the plan cards.
