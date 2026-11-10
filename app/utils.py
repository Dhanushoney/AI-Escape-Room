"""Small shared helpers: input normalisation and text matching."""

from __future__ import annotations

import re
import unicodedata

MAX_INPUT_LENGTH = 500

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
_WHITESPACE = re.compile(r"\s+")


def normalise_player_input(text: str | None, max_length: int = MAX_INPUT_LENGTH) -> str:
    """Return a cleaned single-line version of the player's message.

    * Unicode is NFKC-normalised (so look-alike full-width digits become ASCII).
    * Control characters are removed and whitespace is collapsed.
    * The result is truncated to ``max_length`` characters.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", str(text))
    text = _CONTROL_CHARS.sub(" ", text)
    text = _WHITESPACE.sub(" ", text).strip()
    return text[:max_length]


def contains_phrase(text: str, phrase: str) -> bool:
    """Whole-word, case-insensitive phrase match ("key" does not match "keycard")."""
    return re.search(rf"(?<![a-z0-9]){re.escape(phrase.lower())}(?![a-z0-9])", text.lower()) is not None


def find_aliases(text: str, alias_map: dict[str, list[str]]) -> list[tuple[int, str]]:
    """Find every id whose alias occurs in ``text``.

    Returns ``(position, id)`` pairs sorted by position.  Longer aliases win
    over shorter ones that overlap them ("exit keycard" beats "exit" and "key").
    """
    lowered = text.lower()
    candidates: list[tuple[int, int, str]] = []
    for ident, aliases in alias_map.items():
        for alias in aliases:
            for match in re.finditer(rf"(?<![a-z0-9]){re.escape(alias.lower())}(?![a-z0-9])", lowered):
                candidates.append((match.start(), match.end(), ident))
    # Keep the longest match first, then discard overlapping shorter matches.
    candidates.sort(key=lambda c: (-(c[1] - c[0]), c[0]))
    taken: list[tuple[int, int]] = []
    found: list[tuple[int, str]] = []
    for start, end, ident in candidates:
        if any(start < t_end and end > t_start for t_start, t_end in taken):
            continue
        taken.append((start, end))
        found.append((start, ident))
    found.sort()
    return found


def digits_only(text: str) -> str:
    return re.sub(r"\D", "", text)
