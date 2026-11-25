# Security — AirWise

## 1. Assets to protect

| Asset | Why |
|---|---|
| Gemini API key | Abuse costs quota/money; leaking it is the biggest realistic risk |
| Users' household and health flags | Sensitive personal context |
| Service availability | Public demo during judging |
| Users' browsers | XSS via AI or user text |

## 2. Threat model and controls

| Threat | Control |
|---|---|
| **Secret leakage** | Key only in server env (`.env` git-ignored, host secrets in prod). Never sent to the browser. `.env.example` has empty values. Pre-commit check: `git grep -n "AIza"` must return nothing. |
| **Injection via inputs** | Every request validated by Pydantic: types, enums, ranges, string lengths. Unknown fields rejected (`extra="forbid"`). |
| **XSS** | Frontend never uses `innerHTML` with dynamic data; only `textContent` and `createElement`. Strict CSP blocks inline scripts. |
| **Prompt injection** | User chat text delimited and marked untrusted; system instruction takes priority; output limited to provided ids; number guard; 500-char limit. See [ai-design.md](ai-design.md#5-guardrails-summary). |
| **API abuse / quota drain** | Per-IP rate limits (`slowapi`): plan 10/min, chat 20/min, others 60/min. Max request body 16 KB. Token caps on Gemini calls. |
| **SSRF** | Outbound calls only to fixed hostnames (Open-Meteo, OpenStreetMap Nominatim, Gemini). User input never becomes a URL host; query params URL-encoded by httpx. |
| **Information disclosure** | Generic error messages; stack traces only in server logs; `/docs` can be disabled in prod via env. |
| **Clickjacking** | `frame-ancestors 'none'` + `X-Frame-Options: DENY`. |
| **Vulnerable dependencies** | Pinned versions in `requirements.txt`; `pip-audit` in CI; Dependabot alerts on GitHub. |
| **Privacy** | No database, no cookies, no analytics. Logs exclude profile fields and chat text. Coordinates rounded before caching. |
| **Unsafe AI advice** | No diagnosis/medication advice; fixed disclaimer; recommendations come only from a reviewed catalogue. |

## 3. HTTP security headers

Set by middleware on every response:

```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self';
  img-src 'self' data:; connect-src 'self'; font-src 'self'; object-src 'none';
  base-uri 'self'; form-action 'self'; frame-ancestors 'none'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(self), camera=(), microphone=()
Strict-Transport-Security: max-age=31536000; includeSubDomains   (production, HTTPS only)
```

## 4. CORS

Only origins in `ALLOWED_ORIGINS`. Methods: `GET`, `POST`. No credentials.

## 5. Rate limiting behind a proxy

Hosts like Render sit behind a proxy. Run uvicorn with `--proxy-headers` and trust only the host's
proxy so the real client IP is used for rate limiting.

## 6. Logging

- Structured logs: timestamp, level, route, status, latency, `source` (ai/rules).
- Never log: API keys, request bodies, chat text, coordinates with more than 1 decimal.

## 7. Secure development checklist

- [ ] No secrets in code, docs, tests or commit history
- [ ] New endpoints have Pydantic models with limits and a rate limit
- [ ] No `innerHTML`, `eval`, `new Function` or inline event handlers in frontend
- [ ] `pip-audit` clean
- [ ] Security tests pass (headers, validation, rate limit, injection cases)

## 8. If a key leaks

1. Revoke the key in Google AI Studio immediately.
2. Create a new key and update host secrets.
3. Remove it from git history (`git filter-repo`) and force-push `main`.
