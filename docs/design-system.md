# Design System — AirWise

Calm, trustworthy, readable. The UI should feel like a helpful health guide, not a dashboard.
All tokens live in `static/css/tokens.css` as CSS custom properties.

## 1. Principles

1. **Clarity first** — one primary action per screen; plain language.
2. **Never colour alone** — every AQI state has colour + icon + text label.
3. **Mobile first** — designed at 360 px wide, scales up.
4. **Light and fast** — system fonts, inline SVG icons, no images or animations that matter.

## 2. Colour tokens

Theme: **Nature** (`data-theme="nature"` on `<html>`): warm cream page, deep green accents,
serif headings and a dark green hero over a skyline illustration. All colours are CSS custom
properties in `static/css/tokens.css`; components never use raw hex values, so another theme
is one more `[data-theme="..."]` block.

| Token | Light | Use |
|---|---|---|
| `--color-bg` | `#F6F4EE` | Page background |
| `--color-surface` | `#FFFFFF` | Cards, inputs |
| `--color-text` / `--color-text-muted` | `#1E2B26` / `#4F5D57` | Body / secondary text (≥ 7:1) |
| `--color-primary` | `#1F5E3B` | Buttons, links, icons (≥ 7:1 with white) |
| `--color-ink` | `#13312C` | Hero background and overlay |
| `--color-do` / `--color-avoid` | `#1F7A45` / `#B42318` | Tip icons (always paired with text) |
| `--tint-children` / `--tint-adults` / `--tint-sensitive` / `--tint-pregnancy` | peach / cream / pale blue / pale pink | Audience cards |
| `--chart-*` | green → yellow → orange → red → purple | Chart line follows the AQI scale |

Dark mode (`prefers-color-scheme: dark`) swaps to a deep green-black page with light text.

### Illustrations

All in `static/img/` as WebP (≈ 200 KB total). Decorative only (`alt=""`).

| File | Used for |
|---|---|
| `sky-clear.webp` / `sky-haze.webp` / `sky-smog.webp` | Hero background: Good–Moderate / USG–Very Unhealthy / Hazardous |
| `person-child.webp` / `person-child-boy.webp` | "For children" card |
| `person-adult-female.webp` / `person-adult.webp` | "For adults" card |
| `person-elder-female.webp` / `person-elder.webp` | "For sensitive people" card |
| `person-pregnant.webp` | "During pregnancy" card |

Where a woman and a man (or girl and boy) are both available, the picture alternates by calendar
day (`static/js/utils/art.js`): stable all day, both represented over time, and the adult and
older-adult cards always show different genders on the same day.
| `branch.webp` | Hero corner decoration |

### AQI scale (US EPA colours)

| Category | AQI | Background | Text colour | Icon |
|---|---|---|---|---|
| Good | 0–50 | `#00E400` | `#1A2330` | smile |
| Moderate | 51–100 | `#FFFF00` | `#1A2330` | neutral |
| Unhealthy for Sensitive Groups | 101–150 | `#FF7E00` | `#1A2330` | alert |
| Unhealthy | 151–200 | `#FF0000` | `#000000` | mask |
| Very Unhealthy | 201–300 | `#8F3F97` | `#FFFFFF` | warning |
| Hazardous | 301+ | `#7E0023` | `#FFFFFF` | stop |

Text colours are chosen so every badge meets ≥ 4.5:1 contrast.

## 3. Typography

- Headings and the AQI number: `--font-display` (Fraunces if installed, otherwise Iowan Old
  Style, Palatino or Georgia).
- Body: `--font-sans` (Inter if installed, otherwise the system UI font).
- No web fonts are downloaded, which keeps the first load small.

## 4. Spacing, radius, elevation

- Spacing scale (4 px base): `--space-1` 4px · `--space-2` 8px · `--space-3` 12px ·
  `--space-4` 16px · `--space-6` 24px · `--space-8` 32px · `--space-12` 48px
- Radius: `--radius-sm` 6px · `--radius-md` 12px · `--radius-pill` 999px
- Shadow: `--shadow-card: 0 1px 3px rgb(0 0 0 / 0.08)`
- Breakpoints: 640 px (tablet), 1024 px (desktop)

## 5. Components

| Component | Description | Key a11y notes |
|---|---|---|
| **Top bar** | Logo, greeting ("Good evening, Raja Ram"), search with results dropdown, location button, date, "My family" chip | Greeting is the page `h1`; icon buttons have `aria-label`; chip has `aria-expanded` |
| **My family panel** | Optional name, household, commute, home, habits | Name stays on the device; `<fieldset>`/`<legend>` |
| **Hero** | Skyline matched to the AQI, big AQI number + badge, verdict, PM2.5 / PM10 / NO₂ / O₃ tiles, 24-hour line chart | Chart is an SVG with a `<title>` summary; badge always has text |
| **Audience cards** | For children / adults / sensitive people / during pregnancy (only groups at home), three do/avoid tips each, illustration | Tip type is announced ("Do:", "Avoid:"), never icon-only |
| **Indoor air row** | Indoor recommendations as icon tiles with impact | Real list |
| **Insights card** | vs yesterday, PM2.5 vs WHO guideline, main pollutant | Plain text |
| **Outlook card** | Next-24-hour trend (improving / steady / worsening) | Bars are decorative; sentence carries the meaning |
| **Action cards** | Daily routine and greener swaps, each with an impact line | `h4` titles |
| **Chat** | Suggested questions, log, pill input | `role="log"`, labelled input |

## 6. Layout

Top bar → hero (info left, chart right at ≥ 1000 px) → "Your plan for today" → audience cards →
indoor / insights / outlook row → routine and swap cards → chat → footer. Everything stacks into a
single column on phones.

## 7. Motion

Only subtle fades (≤ 150 ms). Disabled under `@media (prefers-reduced-motion: reduce)`.

## 8. Voice and tone

- Short sentences, second person: "Go for your walk between 2 and 4 pm."
- Lead with the action, then the reason, then the impact.
- No fear language; be calm and specific.
- Avoid jargon; explain PM2.5 once as "tiny particles that reach deep into the lungs".
