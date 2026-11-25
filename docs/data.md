# Data — AirWise

> This file replaces a traditional `database.md`. **AirWise has no database.** It stores no user
> data on the server. This is a deliberate security and privacy decision.

## 1. Data sources

| Source | Endpoint | Auth | Used for |
|---|---|---|---|
| Open-Meteo Air Quality | `https://air-quality-api.open-meteo.com/v1/air-quality` | None | Current + hourly AQI, PM2.5, PM10, NO₂, O₃ |
| Open-Meteo Geocoding | `https://geocoding-api.open-meteo.com/v1/search` | None | City name → lat/lon, timezone |
| Google Gemini | `google-genai` SDK | API key (server only) | Plan wording, chat |
| Recommendation catalogue | `app/rules/catalog.py` | — | Static recommendation data + impact factors |

Open-Meteo data is licensed CC BY 4.0 and its free tier is for non-commercial use; attribution
is shown in the footer.

### Air quality request

```
GET /v1/air-quality?latitude=28.61&longitude=77.21
    &current=us_aqi,pm2_5,pm10,nitrogen_dioxide,ozone
    &hourly=us_aqi,pm2_5
    &forecast_days=2&timezone=auto
```

## 2. Data models (Pydantic)

### UserProfile (request input, never stored)

| Field | Type | Values / limits |
|---|---|---|
| `latitude` | float | −90 … 90 |
| `longitude` | float | −180 … 180 |
| `location_name` | str | ≤ 100 chars, display only |
| `household.children` | bool | under 12 at home |
| `household.elderly` | bool | 65+ at home |
| `household.respiratory_condition` | bool | asthma, COPD, heart condition |
| `household.pregnant` | bool | |
| `commute_mode` | enum | `car`, `two_wheeler`, `bus`, `metro`, `walk`, `cycle`, `wfh` |
| `commute_minutes` | int | 0 … 240 (one way) |
| `commute_km` | float | 0 … 150 (one way, optional; estimated from minutes if missing) |
| `cooking_fuel` | enum | `lpg`, `png`, `electric`, `biomass`, `kerosene` |
| `heating` | enum | `none`, `electric`, `gas`, `wood`, `coal` |
| `has_air_purifier` | bool | |
| `outdoor_activity` | enum | `none`, `morning_walk`, `evening_walk`, `sports` |
| `language` | enum | `en`, `hi` |

### AirReading

`aqi: int`, `category: AqiCategory`, `pm2_5: float`, `pm10: float`, `no2: float | None`,
`o3: float | None`, `dominant_pollutant: str`, `observed_at: datetime`, `timezone: str`

### HourlyForecast

`hours: list[{ time: datetime, aqi: int, pm2_5: float }]` — next 24 h.

### Plan (response)

See [api.md](api.md#post-apiv1plan). Contains `air`, `risk`, `best_windows`,
`recommendations[]` (each with `impact`), `summary`, `source`, `disclaimer`.

### Recommendation catalogue entry

```python
CatalogItem(
    id="commute_metro",
    category=RecommendationCategory.ALTERNATIVE,  # routine | indoor | alternative
    priority=72,  # higher = shown first
    applies=_commute_switch_applies,  # (RuleContext) -> bool
    title=_fixed("Take the metro or bus instead of driving"),  # default text (fallback)
    action=_fixed("..."),
    why=_fixed("..."),
    impact=_commute_switch_impact,  # (RuleContext) -> Impact
)
```

## 3. Caching

| Data | Key | TTL | Store |
|---|---|---|---|
| Air quality | `aq:{lat:.2f}:{lon:.2f}` | 600 s | In-memory TTL cache (max 512 entries) |
| Geocoding | `geo:{query.lower()}` | 24 h | In-memory TTL cache (max 1024 entries) |
| AI output | not cached | — | Personalised; not reused across users |

Rounding coordinates to 2 decimals (~1 km) increases cache hits and avoids storing precise
locations.

## 4. Client-side storage

- **Opt-in only:** "Remember my answers on this device" checkbox.
- Stores the profile (no name, no precise location) in `localStorage` under `airwise.profile.v1`.
- "Forget my data" button clears it.
- Reads/writes wrapped in `try/catch`; the app works without it.

## 5. Privacy

- No accounts, no cookies, no analytics, no server-side storage of profiles or chat.
- Logs never contain profile fields, coordinates beyond 1 decimal, or chat text.
- Data sent to Gemini: compact profile flags + selected recommendations + user's chat message.
  No names, no exact coordinates. This is stated in the UI footer.

## 6. Retention

Nothing is retained server-side beyond the in-memory cache TTLs above. Restarting the server
clears all cached data.
