# String Sorter

A small Flask web app: enter 5 strings, get them back sorted ascending by length with a casing rule applied (`≤ 3` chars → uppercase, longer → capitalized).

The codebase is intentionally small but is structured to be cleanly testable and easy to extend.

## Project structure

```
.
├── main.py                      # WSGI entry point (gunicorn-compatible)
├── requirements.txt
└── app/
    ├── __init__.py              # create_app() factory
    ├── config.py                # Config dataclass — all env reads
    ├── sorter.py                # Pure domain rule (no Flask import)
    ├── validation.py            # validate_strings → ValidationResult
    ├── security.py              # CSRF helpers + security headers hook
    ├── routes.py                # main_bp blueprint (thin HTTP layer)
    └── templates/
        └── index.html           # Jinja template (auto-escaped)
```

Each module has a single responsibility; see the docstring at the top of every file for the rationale behind the split.

## Running locally

```bash
pip install -r requirements.txt
python3 main.py
# open http://localhost:5000
```

The app binds to `0.0.0.0` on the port given by the `PORT` env var (default `5000`).

## Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Flask session signing key. **Required in production** so sessions and CSRF tokens survive restarts. | Random per-process (dev only) |
| `PORT` | Port the WSGI server binds to. | `5000` |
| `REPLIT_DEPLOYMENT` | Set to `"1"` to enable HTTPS-only behaviour (`Secure` cookies, HSTS header). Set automatically by Replit Deployments. | unset |

## Security

The form is hardened against common web vulnerabilities:

- **CSRF**: synchroniser token in the signed session cookie, validated with `secrets.compare_digest`.
- **XSS**: Jinja auto-escaping + strict `Content-Security-Policy`.
- **Clickjacking**: `X-Frame-Options: DENY` + CSP `frame-ancestors 'none'`.
- **MIME sniffing**: `X-Content-Type-Options: nosniff`.
- **Referer leak**: `Referrer-Policy: no-referrer`.
- **Browser feature abuse**: `Permissions-Policy` denies geolocation, mic, camera.
- **Session security**: `HttpOnly` + `SameSite=Lax`; `Secure` + HSTS automatically enabled in production via `ProxyFix`.
- **Request DoS**: `MAX_CONTENT_LENGTH = 16 KB` — oversized requests get HTTP 413 immediately.

## Validation

Server-side validation is the source of truth (HTML5 attributes are UX hints only):
- Required (rejects empty / whitespace-only input)
- Maximum 200 characters per field
- All errors collected and shown together so users can fix everything in one pass

## Deployment

The app runs on any WSGI server. For production:

```bash
gunicorn main:app --bind 0.0.0.0:$PORT
```

On Replit, click **Publish** — the included `.replit` config is set to a `vm` deployment target running `python3 main.py`.
