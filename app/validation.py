"""Server-side validation for the string-sorter form.

Why a separate module?
  * The view stays focused on HTTP concerns (parse request, call domain,
    render template) instead of growing into a god-function.
  * Validation can be exercised in tests without a Flask test client.
  * If a JSON API endpoint is ever added that consumes the same fields,
    it can reuse ``validate_strings`` verbatim.

We return a small dataclass instead of a ``(values, errors)`` tuple
because tuples of two same-typed lists are easy to swap by accident at
the call site — a class of bug a named result eliminates entirely.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of validating a single form submission."""

    # Cleaned (whitespace-trimmed) values, one per field, in field order.
    # Always populated even when validation fails so the template can
    # re-display what the user typed instead of clearing the form.
    values: list[str]

    # Human-readable error messages. Empty list means "no errors".
    errors: list[str]

    @property
    def ok(self) -> bool:
        """``True`` when the form passed validation and is safe to process."""
        return not self.errors


def validate_strings(
    form: Mapping[str, str],
    *,
    num_inputs: int,
    max_length: int,
    field_prefix: str = "s",
) -> ValidationResult:
    """Validate ``num_inputs`` text fields named ``s1`` … ``sN``.

    Design choices:
      * We collect *all* errors instead of failing fast. Users prefer
        fixing every problem in one pass rather than playing whack-a-mole.
      * Inputs are trimmed before length checks so a field of pure
        whitespace is correctly rejected as empty.
      * The function accepts any ``Mapping[str, str]`` (not specifically
        a Flask ``ImmutableMultiDict``) so it can be tested with a plain
        dict.
    """
    values: list[str] = []
    errors: list[str] = []

    for i in range(1, num_inputs + 1):
        raw = form.get(f"{field_prefix}{i}", "")

        # Defensive type-check. ``request.form`` always yields strings,
        # but this module accepts arbitrary mappings, so a caller passing
        # a non-string value should produce a clean error rather than an
        # AttributeError on ``.strip()``.
        if not isinstance(raw, str):
            errors.append(f"String {i} is invalid.")
            values.append("")
            continue

        cleaned = raw.strip()

        if len(cleaned) == 0:
            errors.append(f"String {i} is required.")
        elif len(cleaned) > max_length:
            errors.append(f"String {i} must be at most {max_length} characters.")

        values.append(cleaned)

    return ValidationResult(values=values, errors=errors)
