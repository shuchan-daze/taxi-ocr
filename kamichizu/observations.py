"""Observation helpers for physical cells.

Layer 1 records what is visible on paper.  These helpers decide whether that
observation is usable as a value without assigning business meaning.
"""

from __future__ import annotations

from typing import Any, Iterable


DASH_VALUES = frozenset(("-", "ー", "―", "—", "−", "–", "－"))
VOID_MARKS = frozenset(("strikethrough", "crossed_out", "voided", "deleted", "correction_line"))
VOID_STATES = frozenset(("voided", "deleted", "corrected"))


def has_effective_value(value: Any) -> bool:
    if value in (None, ""):
        return False
    text = str(value).strip()
    return bool(text) and text not in DASH_VALUES


def is_voided_observation(state: str = "", marks: Iterable[str] = ()) -> bool:
    normalized_state = str(state or "").strip().lower()
    if normalized_state in VOID_STATES:
        return True
    normalized_marks = {str(mark).strip().lower() for mark in marks if str(mark).strip()}
    return bool(normalized_marks & VOID_MARKS)


def has_effective_observation(value: Any, raw: Any, state: str = "", marks: Iterable[str] = ()) -> bool:
    if is_voided_observation(state, marks):
        return False
    return has_effective_value(value) or has_effective_value(raw)
