# Product Requirements Document — AirWise

| | |
|---|---|
| **Product** | AirWise — Urban Air Quality Assistant |
| **Challenge** | PromptWars Virtual, Challenge 6 |
| **Deadline** | 29 Nov 2026, 11:59 PM IST |
| **Status** | Planning |

## 1. Problem

Every winter, cities like Delhi, Lahore and Beijing face severe smog. Families know "the air is
bad" but not **what to do today**: when it is safe to go outside, how to protect children and
elderly relatives, how to keep indoor air clean, or which of their own habits add to the problem.
Existing AQI apps show a number; they do not turn it into a personalised plan or explain the
impact of choices.

## 2. Challenge statement (verbatim intent)

> Create a GenAI-powered assistant that helps families and communities navigate severe winter smog
> and urban air pollution. The application should suggest low-emission daily routines, indoor air
> quality hacks, and sustainable alternatives tailored to their location and lifestyle, while
> clearly explaining the direct impact of their choices.

## 3. Goals

| # | Goal | Maps to challenge |
|---|---|---|
| G1 | Personalised daily routine based on live and forecast AQI | Low-emission daily routines |
| G2 | Practical indoor air quality tips for the user's home | Indoor air quality hacks |
| G3 | Lower-emission alternatives for commute, cooking, heating | Sustainable alternatives |
| G4 | Every recommendation shows its impact | Explain direct impact |
| G5 | Tailored to location + household + lifestyle | Tailored to location and lifestyle |
| G6 | GenAI-written plan + follow-up chat | GenAI-powered assistant |

## 4. Personas

1. **Priya, 34, parent in Delhi** — 6-year-old with mild asthma, drives to work. Needs to know when
   her child can play outside and how to keep the bedroom air clean.
2. **Mr & Mrs Khan, 68 & 65, retirees in Lahore** — enjoy morning walks, use a gas heater. Need
   safe walking windows and heater guidance.
3. **Arjun, 24, commuter in Gurugram** — rides a two-wheeler 40 min daily. Wants to cut exposure and
   emissions without big costs.
4. **Meera, RWA volunteer** — shares advice with her housing society. Needs clear, shareable
   explanations.

## 5. User stories

- As a parent, I want to know the **cleanest hours today** so my child can play outside safely.
- As a sensitive person, I want to be **warned when outdoor activity is unsafe** and offered an
  indoor alternative.
- As a commuter, I want **lower-exposure and lower-emission commute options** with their impact.
- As a homeowner, I want **indoor tips** (ventilation timing, purifier use) that fit my home.
- As any user, I want to **ask follow-up questions** in plain language.
- As any user, I want to understand **why** each recommendation was made.

## 6. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-1 | Search a city or use browser location to set coordinates | Must |
| FR-2 | Show current AQI, category, PM2.5, PM10 and a health message | Must |
| FR-3 | Collect a short profile: household sensitivity, commute mode and duration, cooking fuel, heating type, purifier ownership, outdoor activity habit | Must |
| FR-4 | Compute risk level from AQI + household sensitivity | Must |
| FR-5 | Find the best outdoor windows in the next 24 h from the forecast | Must |
| FR-6 | Select applicable recommendations in three groups: routine, indoor, alternative | Must |
| FR-7 | Show impact per recommendation (exposure reduction %, CO₂ saved/day) with basis label | Must |
| FR-8 | Generate a friendly summary and wording with Gemini | Must |
| FR-9 | Fall back to rule-based wording if Gemini fails | Must |
| FR-10 | Scoped chat for follow-up questions using the current plan as context | Should |
| FR-11 | Remember profile on the device (opt-in, localStorage) | Could |
| FR-12 | Hindi language option for AI text | Could |

## 7. Non-functional requirements

| Area | Requirement |
|---|---|
| Performance | First load < 100 KB transferred; plan generated in < 5 s (p95) |
| Accessibility | WCAG 2.2 AA; Lighthouse accessibility ≥ 95 |
| Security | No secrets in repo; validated inputs; rate limiting; CSP; no PII stored |
| Reliability | Works without AI (fallback); handles upstream API failure with clear message |
| Testing | Backend coverage ≥ 85 %; rules engine fully covered |
| Repo | Public, single branch `main`, < 10 MB |

## 8. Out of scope

User accounts, server database, push notifications, native mobile apps, medical diagnosis, paid
data sources.

## 9. Success criteria

- All six evaluation parameters addressed (see matrix below).
- A judge can run or open the app and get a personalised plan in under a minute.
- Every recommendation shows "what to do", "why" and "impact".

## 10. Evaluation alignment matrix

| Parameter | How AirWise addresses it | Doc |
|---|---|---|
| Problem Statement Alignment | All four asks (routines, indoor, alternatives, impact) + location/lifestyle tailoring | This doc, ai-design.md |
| Code Quality | Layered modules, type hints, docstrings, ruff, mypy | architecture.md, code-style.md |
| Security | Secrets in env, validation, rate limits, CSP, no PII, prompt-injection guards | security.md |
| Efficiency | Caching, one AI call per plan, no frontend framework | architecture.md |
| Testing | pytest + respx + node:test, CI | testing.md |
| Accessibility | WCAG 2.2 AA, keyboard, screen reader, not colour-only | accessibility.md |

## 11. Assumptions

- US EPA AQI scale from Open-Meteo is used as-is.
- Impact numbers are estimates with documented sources; see ai-design.md.
- Guidance is general wellbeing advice, not medical advice.
