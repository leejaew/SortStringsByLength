"""HTTP layer: a single Flask blueprint that wires the form to the domain.

The view is deliberately thin. Its only jobs are:
  1. Enforce the CSRF check.
  2. Delegate validation to ``validate_strings``.
  3. Delegate the business rule to ``format_sorted``.
  4. Render the template with the result.

If the view starts growing (multiple endpoints, JSON API, file uploads,
authentication, ...) the right next step is to split it into multiple
blueprints under a ``routes/`` package. Until then, one file is the
correct size — splitting prematurely would be over-engineering.
"""

from __future__ import annotations

from flask import Blueprint, current_app, render_template, request

from .security import CSRF_FORM_FIELD, ensure_csrf_token, verify_csrf_token
from .sorter import format_sorted
from .validation import validate_strings


# A blueprint (rather than ``@app.route`` directly) keeps routes
# decoupled from app construction, which is what makes the factory
# pattern useful for testing.
main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET", "POST"])
def index():
    """Render the form on GET; validate, sort and render results on POST."""
    # Pull configuration from Flask's app config rather than reaching into
    # ``os.environ`` or module globals. This keeps the view testable with
    # any Config instance the factory was built with.
    cfg = current_app.config
    num_inputs: int = cfg["NUM_INPUTS"]
    max_length: int = cfg["MAX_STRING_LENGTH"]
    short_threshold: int = cfg["SHORT_STRING_THRESHOLD"]

    csrf_token = ensure_csrf_token()
    values: list[str] = [""] * num_inputs
    errors: list[str] = []
    results: list[str] = []

    if request.method == "POST":
        # CSRF check first — never trust the body of an unverified
        # request, not even to validate it (cheap and avoids leaking
        # validation behaviour to attackers).
        verify_csrf_token(request.form.get(CSRF_FORM_FIELD))

        outcome = validate_strings(
            request.form, num_inputs=num_inputs, max_length=max_length
        )
        values, errors = outcome.values, outcome.errors

        if outcome.ok:
            results = format_sorted(values, short_threshold=short_threshold)

    # ``render_template`` (not ``render_template_string``) loads from disk
    # so the HTML lives in a real ``.html`` file with proper editor
    # support. Auto-escaping is on by default for ``.html`` templates,
    # which is the XSS defence for ``values`` and ``results``.
    return render_template(
        "index.html",
        results=results,
        values=values,
        errors=errors,
        csrf_token=csrf_token,
        num_inputs=num_inputs,
        max_length=max_length,
        short_threshold=short_threshold,
    )
