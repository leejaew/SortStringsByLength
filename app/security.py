"""Cross-cutting security: CSRF token management and HTTP response hardening.

Security concerns are isolated in their own module so:
  * Auditors and new contributors have one obvious place to look.
  * The helpers are unit-testable in isolation.
  * Adding a new security header or tweaking the CSP doesn't risk
    touching unrelated business logic.

We hand-roll the CSRF synchroniser pattern instead of pulling in
Flask-WTF because the form has exactly one POST endpoint, no AJAX, and
no file uploads. The standard library's ``secrets`` module is more than
enough and avoids an additional dependency (which previously caused
deployment failures during initial setup).
"""

from __future__ import annotations

import secrets
from typing import Final

from flask import Flask, Response, abort, session


# Single source of truth for the cookie/session/form key name. Centralising
# the literal removes "magic string drift" between the helper and the view.
CSRF_SESSION_KEY: Final[str] = "csrf_token"
CSRF_FORM_FIELD: Final[str] = "csrf_token"


def ensure_csrf_token() -> str:
    """Return the per-session CSRF token, creating one on first call.

    The token lives in the signed Flask session cookie (HttpOnly) so a
    JavaScript context on a third-party origin cannot read it — which is
    the entire point of the synchroniser pattern.
    """
    token = session.get(CSRF_SESSION_KEY)
    if not token:
        # 32 bytes ≈ 256 bits of entropy, base64-url encoded so the value
        # is safe to embed in HTML attributes and HTTP headers.
        token = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token
    return token


def verify_csrf_token(submitted: str | None) -> None:
    """Abort with HTTP 400 if ``submitted`` does not match the session token.

    Uses ``secrets.compare_digest`` to avoid leaking the token via timing
    differences in naive string comparison.
    """
    expected = session.get(CSRF_SESSION_KEY, "")
    if (
        not submitted
        or not expected
        or not secrets.compare_digest(submitted, expected)
    ):
        abort(400, description="Invalid CSRF token.")


def init_security_headers(app: Flask, *, is_production: bool) -> None:
    """Register the ``after_request`` hook that hardens every response.

    Header rationale (defence in depth):
      * ``Content-Security-Policy``: even if an injection slipped past
        Jinja's auto-escaping, browsers refuse to execute disallowed
        scripts. ``frame-ancestors 'none'`` doubles as clickjacking
        protection in modern browsers.
      * ``X-Content-Type-Options: nosniff``: stops browsers from
        re-interpreting responses as a different MIME type.
      * ``X-Frame-Options: DENY``: legacy clickjacking protection for
        browsers that pre-date CSP ``frame-ancestors``.
      * ``Referrer-Policy: no-referrer``: avoids leaking URLs (which can
        contain tokens) to third parties via the Referer header.
      * ``Permissions-Policy``: pre-emptively denies powerful browser
        APIs we never use.
      * ``Strict-Transport-Security``: emitted only in production where
        HTTPS is actually enforced. Sending HSTS from a plain-HTTP dev
        server would be dishonest and could break local testing.
    """

    @app.after_request
    def _set_security_headers(response: Response) -> Response:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; form-action 'self'; "
            "frame-ancestors 'none'; base-uri 'self'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        if is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response
