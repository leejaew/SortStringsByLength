"""Centralised application configuration.

All environment-variable reads are concentrated *here*, evaluated when a
``Config`` instance is constructed (typically once at app startup).
Every other module receives configuration via the ``Config`` instance
(or via Flask's ``app.config``) and never touches ``os.environ``
directly. Benefits:

  * Tests can build a ``Config(secret_key="x", is_production=False)``
    without patching the environment.
  * One file to audit when asking "what does this app depend on?".
  * Defaults and fallbacks are co-located with the values they apply to.

We intentionally keep this as a plain frozen dataclass instead of pulling
in a settings library (pydantic-settings, dynaconf, ...). The surface is
small — six values — so a third-party dependency would be over-engineering.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field


def _default_secret_key() -> str:
    """Generate a random per-process key when ``SECRET_KEY`` is not set.

    Acceptable for local development (sessions just don't survive a
    restart). Production deployments MUST set ``SECRET_KEY`` so sessions
    and CSRF tokens remain valid across process restarts and across
    multiple instances behind a load balancer.
    """
    return secrets.token_hex(32)


@dataclass(frozen=True)
class Config:
    """Immutable application configuration.

    ``frozen=True`` prevents accidental mutation after construction —
    config drift inside a long-running process is a classic source of
    "works on my machine" bugs.
    """

    # Flask's signing key for the session cookie (which carries the CSRF
    # token). Must be stable across restarts in production.
    secret_key: str = field(
        default_factory=lambda: os.environ.get("SECRET_KEY") or _default_secret_key()
    )

    # ``REPLIT_DEPLOYMENT`` is set to "1" only in Replit's production
    # deploy runtime. We use it as the single source of truth for "are we
    # serving over HTTPS behind a trusted proxy?" — which drives both the
    # ``Secure`` cookie flag and the HSTS header.
    is_production: bool = field(
        default_factory=lambda: os.environ.get("REPLIT_DEPLOYMENT") == "1"
    )

    # Hard cap on request body size; deflects trivial DoS attempts. The
    # form only ever submits ~1 KB so 16 KB is a generous ceiling.
    max_content_length: int = 16 * 1024

    # Number of input strings the form collects. Centralised so the route,
    # the validator, and the template all agree without duplication.
    num_inputs: int = 5

    # Per-field maximum length. Enforced both client-side (HTML5
    # ``maxlength``) and server-side; the server is the source of truth.
    max_string_length: int = 200

    # Threshold for the "short string" formatting rule (uppercase vs
    # capitalize). Pulling this out of the sorter lets the rule be tuned
    # without touching domain code.
    short_string_threshold: int = 3

    # Port the WSGI server binds to. ``PORT`` is set by most PaaS runtimes
    # (Cloud Run, Replit Deployments). Defaults to 5000 for local dev.
    port: int = field(default_factory=lambda: int(os.environ.get("PORT", "5000")))
