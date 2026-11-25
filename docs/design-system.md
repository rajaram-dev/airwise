# Design System — AirWise

Calm, trustworthy, readable. The UI should feel like a helpful health guide, not a dashboard.
All tokens live in `static/css/tokens.css` as CSS custom properties.

## 1. Principles

1. **Clarity first** — one primary action per screen; plain language.
2. **Never colour alone** — every AQI state has colour + icon + text label.
3. **Mobile first** — designed at 360 px wide, scales up.
4. **Light and fast** — system fonts, inline SVG icons, no images or animations that matter.

## 2. Colour tokens

### Base (light theme)

| Token | Value | Use |
|---|---|---|
| `--color-bg` | `#F7F9FB` | Page background |
| `--color-surface` | `#FFFFFF` | Cards |
| `--color-text` | `#1A2330` | Body text (contrast 15:1 on bg) |
| `--color-text-muted` | `#4A5868` | Secondary text (≥ 7:1) |
| `--color-border` | `#D5DDE5` | Dividers, inputs |
| `--color-primary` | `#0B6E99` | Buttons, links (≥ 5:1 on white) |
| `--color-primary-hover` | `#085678` | Hover/active |
| `--color-focus` | `#FFB000` | Focus ring (3 px outline + 2 px offset) |
| `--color-success` | `#1E7B34` | Positive impact text |
| `--color-danger` | `#B3261E` | Errors |

### Dark theme

Applied with `@media (prefers-color-scheme: dark)`.

| Token | Value |
|---|---|
| `--color-bg` | `#0F1720` |
| `--color-surface` | `#18222D` |
| `--color-text` | `#E8EEF4` |
| `--color-text-muted` | `#A9B6C3` |
| `--color-border` | `#2C3A48` |
| `--color-primary` | `#5CC4F0` |

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

System font stack — no web font download:

```css
--font-sans: system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", sans-serif;
```

| Token | Size (rem) | Use |
|---|---|---|
| `--text-xs` | 0.8125 | Labels, captions |
| `--text-sm` | 0.875 | Secondary text |
| `--text-base` | 1 | Body (16 px min) |
| `--text-lg` | 1.25 | Card titles |
| `--text-xl` | 1.75 | Section headings |
| `--text-hero` | 3 | AQI number |

Line height 1.5 for body, 1.2 for headings. Max line length ~70 characters.

## 4. Spacing, radius, elevation

- Spacing scale (4 px base): `--space-1` 4px · `--space-2` 8px · `--space-3` 12px ·
  `--space-4` 16px · `--space-6` 24px · `--space-8` 32px · `--space-12` 48px
- Radius: `--radius-sm` 6px · `--radius-md` 12px · `--radius-pill` 999px
- Shadow: `--shadow-card: 0 1px 3px rgb(0 0 0 / 0.08)`
- Breakpoints: 640 px (tablet), 1024 px (desktop)

## 5. Components

| Component | Description | Key a11y notes |
|---|---|---|
| **LocationSearch** | Text input + "Use my location" button + suggestions list | Combobox pattern, `aria-expanded`, arrow-key navigation |
| **ProfileForm** | Short form in fieldsets: household, commute, home | `<fieldset>`/`<legend>`, labels on every input, inline errors via `aria-describedby` |
| **AqiCard** | Big AQI number, category badge, PM2.5/PM10, health message, updated time | Category spoken as text; number has `aria-label` with category |
| **RiskBanner** | Risk level with reasons | `role="status"` |
| **TimeWindowList** | Best outdoor windows as a list of time ranges | Real `<time>` elements |
| **RecommendationCard** | Title, action, why, impact chips (e.g. "−40 % exposure", "1.8 kg CO₂/day"), basis label | Impact chips have text, not icons only |
| **Tabs** | Routine · Indoor · Greener swaps | WAI-ARIA tabs pattern, arrow keys |
| **ChatPanel** | Message log + input + send | Log `aria-live="polite"`, input labelled, Enter to send |
| **Button** | Primary, secondary, ghost | Min target 44×44 px, visible focus |
| **Alert** | Info, warning, error | `role="alert"` for errors only |
| **Disclaimer** | "General guidance, not medical advice" | Always visible near plan |

## 6. Layout

```
┌─────────────────────────────┐
│ Header: AirWise · skip link │
├─────────────────────────────┤
│ LocationSearch              │
│ AqiCard        RiskBanner   │   ← stacked on mobile, 2 columns ≥ 1024 px
│ ProfileForm  [Get my plan]  │
│ Summary (AI)                │
│ Tabs: Routine|Indoor|Swaps  │
│   RecommendationCard × n    │
│ TimeWindowList              │
│ ChatPanel                   │
│ Footer: data sources, disclaimer
└─────────────────────────────┘
```

## 7. Motion

Only subtle fades (≤ 150 ms). Disabled under `@media (prefers-reduced-motion: reduce)`.

## 8. Voice and tone

- Short sentences, second person: "Go for your walk between 2 and 4 pm."
- Lead with the action, then the reason, then the impact.
- No fear language; be calm and specific.
- Avoid jargon; explain PM2.5 once as "tiny particles that reach deep into the lungs".
