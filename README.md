# AirWise — Urban Air Quality Assistant

> A GenAI-powered assistant that helps families and communities get through severe winter smog with
> personalised low-emission routines, indoor air quality hacks and sustainable alternatives — and
> explains the direct impact of every choice.

**Challenge:** PromptWars Virtual — Challenge 6: Urban Air Quality Assistant
**Live demo:** _TBD_ · **Demo video:** _TBD_

---

## 1. Chosen vertical

**Urban Air Quality Assistant.** Our persona is a household living in a city with severe winter
smog (e.g. Delhi NCR, Lahore, Beijing) that needs practical, daily, location-aware guidance — not
generic advice.

## 2. Approach and logic

AirWise uses a **"rules decide, AI explains"** design:

1. **Live data** — current and 24-hour forecast air quality for the user's location
   (Open-Meteo Air Quality API, no API key needed).
2. **Deterministic rules engine** — decides the user's risk level, the cleanest outdoor time
   windows, and which recommendations apply to their household and lifestyle. It also computes the
   impact numbers (exposure reduction %, CO₂ saved). This logic is fully unit-tested.
3. **Gemini (GenAI)** — turns those decisions into a friendly, personalised daily plan and answers
   follow-up questions in chat. Gemini **never invents numbers**: every figure shown comes from the
   rules engine.
4. **Graceful fallback** — if the AI is unavailable, the user still gets the rule-based plan.

## 3. How the solution works

```
User profile + location
        │
        ▼
Open-Meteo AQI (current + 24h forecast) ──► Rules engine ──► Gemini ──► Personalised plan
                                             (risk, windows,   (wording,    (routine, indoor tips,
                                              recommendations,  priority)    greener swaps, impact)
                                              impact numbers)
```

The user gets:
- **Today's air** — AQI, category, health meaning (colour + icon + text).
- **Your daily routine** — when to go out, exercise, ventilate, commute.
- **Indoor air hacks** — purifier use, ventilation timing, avoiding indoor pollution sources.
- **Greener swaps** — lower-emission alternatives, each with its impact.
- **Ask AirWise** — chat for questions like "Can my child play outside at 5 pm?"
- **Advice for each person at home** — separate do/avoid tips for children, adults, sensitive people and pregnancy.
- **Insights and outlook** — change against yesterday, PM2.5 against the WHO guideline, and the 24-hour trend.

## 4. Assumptions

- Air quality is reported on the **US EPA AQI** scale (provided by Open-Meteo). Indian NAQI uses
  different breakpoints; we document this rather than convert.
- Impact figures are **estimates** based on published emission factors and studies
  (see [docs/ai-design.md](docs/ai-design.md#impact-methodology)). Values computed from the live
  forecast are labelled "computed"; catalogue values are labelled "estimated".
- AirWise gives general wellbeing guidance, **not medical advice**.
- No account or database: nothing about the user is stored on the server.

## 5. Tech stack

| Layer | Choice |
|---|---|
| Backend | Python 3.11+, FastAPI, httpx, Pydantic v2 |
| GenAI | Google Gemini API (`google-genai` SDK) |
| Data | Open-Meteo Air Quality + Geocoding APIs; OpenStreetMap Nominatim for place names |
| Frontend | Vanilla HTML, CSS, JavaScript (ES modules) — no build step |
| Testing | pytest, respx, Node built-in test runner |
| Quality | ruff, mypy, pip-audit, GitHub Actions |

Why vanilla JS? Fast loads, a tiny repo, full control over accessibility and zero build tooling.

## 6. Quick start

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
copy .env.example .env          # then add your GEMINI_API_KEY
uvicorn app.main:app --reload
```

Open http://localhost:8000.

## 7. Testing

```bash
pytest --cov=app        # backend
node --test "tests/frontend/*.test.js"   # frontend
```

## 8. Documentation

| Doc | Purpose |
|---|---|
| [PRD](docs/PRD.md) | Problem, personas, requirements |
| [Architecture](docs/architecture.md) | System design, folder structure, performance |
| [Design system](docs/design-system.md) | Tokens, components, AQI colour scale |
| [Accessibility](docs/accessibility.md) | WCAG 2.2 AA commitments |
| [Data](docs/data.md) | Data sources, models, caching, privacy |
| [AI design](docs/ai-design.md) | Prompts, guardrails, impact methodology |
| [API](docs/api.md) | Endpoint contracts |
| [Security](docs/security.md) | Threat model and controls |
| [Code style](docs/code-style.md) | Conventions |
| [Testing](docs/testing.md) | Test strategy |
| [Deployment](docs/deployment.md) | Run and deploy |
| [AGENTS.md](AGENTS.md) | Rules for AI coding agents |
