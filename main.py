"""WSGI entry point.

Replit's deployment runs ``python3 main.py``. Keeping this file tiny
ensures the app's structure lives in the ``app`` package where it
belongs, and a production WSGI server (gunicorn) can also import
``main:app`` directly without executing the dev-server block below.
"""

from app import create_app
from app.config import Config

# Build the app once at import time. ``Config()`` reads the environment.
config = Config()
app = create_app(config)


if __name__ == "__main__":
    # ``host="0.0.0.0"`` is required so the Replit proxy can reach the
    # process from outside the container. ``port`` comes from the
    # centralised config (PORT env var in production, 5000 in dev).
    app.run(host="0.0.0.0", port=config.port)
