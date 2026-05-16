"""Application factory for the String Sorter Flask app.

Why a factory (instead of a module-level ``app = Flask(__name__)``)?
  * Tests can construct an app with a custom ``Config`` instance instead of
    monkey-patching environment variables.
  * Importing the package has no side effects: no socket binding, no env
    reads, no global mutation. That keeps tooling (linters, IDEs, the
    code-review subagent) fast and predictable.
  * The factory is the single composition root: every cross-cutting concern
    (security headers, proxy fix, blueprints) is wired here so the file
    reads as a table of contents for the whole app.
"""

from __future__ import annotations

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config
from .routes import main_bp
from .security import init_security_headers


def create_app(config: Config | None = None) -> Flask:
    """Build and return a fully-configured Flask application.

    Pass a custom ``config`` to override defaults (used by tests). When
    ``None``, a default ``Config`` is constructed which reads from the
    environment.
    """
    cfg = config or Config()

    app = Flask(__name__)

    # ProxyFix teaches Flask to honour the X-Forwarded-* headers from the
    # ONE trusted reverse proxy in front of us (Replit's edge / Cloud Run).
    # Without it, ``request.is_secure`` and ``request.url`` lie when TLS
    # is terminated upstream, which would break HTTPS-only logic and
    # any future absolute-URL generation.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # Flask conventionally reads UPPERCASE keys off ``app.config``. We copy
    # values from our typed ``Config`` dataclass into that dict so both the
    # framework and our own view code can consume them uniformly.
    app.config.update(
        SECRET_KEY=cfg.secret_key,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        # ``Secure`` is only meaningful over HTTPS. Sending it from the
        # plain-HTTP dev server would silently drop the session cookie and
        # break CSRF on local testing — hence the IS_PRODUCTION gate.
        SESSION_COOKIE_SECURE=cfg.is_production,
        MAX_CONTENT_LENGTH=cfg.max_content_length,
        # Custom keys consumed by our own view layer. We own the entire
        # config namespace so prefix-free names are fine.
        NUM_INPUTS=cfg.num_inputs,
        MAX_STRING_LENGTH=cfg.max_string_length,
        SHORT_STRING_THRESHOLD=cfg.short_string_threshold,
    )

    # Register cross-cutting concerns and routes. Order matters only when
    # one hook depends on another; here they are independent.
    init_security_headers(app, is_production=cfg.is_production)
    app.register_blueprint(main_bp)

    return app
