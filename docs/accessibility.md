# Accessibility — AirWise

**Target:** WCAG 2.2 Level AA. Air pollution hits elderly people, children and people with health
conditions hardest — the people most likely to rely on assistive technology. Accessibility is a
core feature, not polish.

## 1. Commitments

### Perceivable
- Text contrast ≥ 4.5:1 (body) and ≥ 3:1 (large text, UI components, focus ring).
- **AQI is never conveyed by colour alone**: colour + icon + category text.
- All icons are decorative (`aria-hidden="true"`) or have an accessible name.
- Content reflows at 320 px wide and 200 % zoom with no horizontal scroll.
- `lang="en"` on `<html>`; `lang="hi"` on Hindi content when that option is used.

### Operable
- Everything works with keyboard only; logical tab order follows visual order.
- Visible focus indicator on every interactive element (3 px `--color-focus` outline).
- "Skip to main content" link as first focusable element.
- Touch targets ≥ 44×44 px (WCAG 2.2 minimum is 24×24).
- No time limits; no auto-playing content; respects `prefers-reduced-motion`.

### Understandable
- Every input has a visible `<label>`; groups use `<fieldset>` + `<legend>`.
- Errors explained in text next to the field, linked with `aria-describedby`, and summarised at
  the top of the form on submit.
- Plain language (aim for reading age ~12); terms like PM2.5 explained once.
- Consistent navigation and naming across the page.

### Robust
- Semantic HTML first (`<header>`, `<main>`, `<nav>`, `<section>`, `<button>`, `<time>`);
  ARIA only when no native element fits.
- Dynamic updates announced:
  - Plan loaded → `role="status"` region: "Your plan for Delhi is ready."
  - Chat replies → log with `aria-live="polite"`.
  - Errors → `role="alert"`.
- Loading states have text ("Getting live air data…"), not just spinners; `aria-busy` on regions.

## 2. Component patterns

| Component | Pattern |
|---|---|
| Location search | Search form; results are a list of buttons (simpler and fully keyboard/screen-reader friendly) |
| Forecast chart | `role="img"` with a generated text summary (range and cleanest window); title states the window in words |
| Household panel | Toggled by the profile chip (`aria-expanded`, `aria-controls`); focus moves to the panel heading |
| Chat | `role="log"`, labelled input, send button with text |
| AQI number | `aria-label="Air quality index 287, Very Unhealthy"` |

## 3. Checklist (run for every UI change)

- [ ] Keyboard-only walkthrough: search → household panel → plan → chat
- [ ] Focus always visible and never trapped
- [ ] Screen reader (NVDA on Windows / VoiceOver) announces plan, errors and chat replies
- [ ] Contrast checked for new colours (both themes)
- [ ] 200 % zoom and 320 px width — no loss of content
- [ ] Reduced motion respected
- [ ] Lighthouse accessibility score ≥ 95
- [ ] axe DevTools: zero serious/critical issues

## 4. Testing tools

- Lighthouse (Chrome DevTools)
- axe DevTools browser extension
- NVDA (free, Windows) / VoiceOver (macOS, iOS)
- Keyboard only

## 5. Known limitations

- AI-generated text is reviewed by guardrails for length and tone, but reading level may vary.
- Hindi option covers AI text only; static UI labels are English in v1.
