"""Pure domain logic: sort strings by length and apply casing rules.

This module has zero knowledge of Flask, HTTP, sessions, or the
environment. That isolation is the highest-value separation in the whole
refactor because:

  * It can be unit-tested in microseconds without fixtures.
  * The same rule could be reused tomorrow from a CLI, a JSON API, or a
    background job without dragging in the web layer.
  * It documents the *business rule* in one obvious place — a future
    reader (human or AI) can answer "what does this app actually do?" by
    reading exactly one short file.

We resist introducing a Strategy pattern (abstract ``Formatter`` base
class with concrete subclasses). There is exactly one rule today and it
fits in three lines; an inheritance hierarchy would be ceremony without
benefit (YAGNI). If a *second* formatting rule ever appears, that is the
right moment to introduce the abstraction.
"""

from __future__ import annotations

from typing import Iterable


def format_sorted(strings: Iterable[str], short_threshold: int = 3) -> list[str]:
    """Return ``strings`` sorted ascending by length, then case-formatted.

    Rules (product-defined):
      * Strings whose length is ``<= short_threshold`` are upper-cased.
      * Longer strings are capitalised (first letter upper, rest lower).

    The function is pure: identical inputs always produce identical
    outputs and the input collection is never mutated (``sorted`` returns
    a new list).
    """
    by_length = sorted(strings, key=len)
    return [
        s.upper() if len(s) <= short_threshold else s.capitalize()
        for s in by_length
    ]
