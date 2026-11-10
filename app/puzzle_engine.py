"""Version 2 puzzle rules: answer normalisation, checking and dependencies.

Solutions live only in ``config/game_config.json`` and are compared here, in
Python.  Nothing in this module is ever sent to the LLM.
"""

from __future__ import annotations

import hmac
import re
from typing import Any

from app.game_state import GameState
from app.utils import digits_only


def puzzle_for_target(config: dict[str, Any], target: str | None) -> str | None:
    """Return the id of the puzzle attached to an object, if any."""
    if target is None:
        return None
    for puzzle_id, puzzle in config["puzzles"].items():
        if puzzle["target"] == target:
            return puzzle_id
    return None


def extract_symbols(config: dict[str, Any], text: str) -> list[str]:
    """Return symbol names mentioned in ``text`` in the order they appear."""
    aliases = sorted(config["symbol_aliases"].items(), key=lambda kv: -len(kv[0]))
    found: list[tuple[int, str]] = []
    taken: list[tuple[int, int]] = []
    lowered = text.lower()
    for alias, symbol in aliases:
        for match in re.finditer(rf"(?<![a-z]){re.escape(alias)}s?(?![a-z])", lowered):
            span = (match.start(), match.end())
            if any(span[0] < e and span[1] > s for s, e in taken):
                continue
            taken.append(span)
            found.append((match.start(), symbol))
    found.sort()
    return [symbol for _, symbol in found]


def normalise_answer(config: dict[str, Any], puzzle_id: str, raw: str | None) -> str:
    """Convert a free-text attempt into the canonical comparison form."""
    raw = raw or ""
    puzzle = config["puzzles"][puzzle_id]
    if puzzle["type"] == "code":
        return digits_only(raw)
    return " ".join(extract_symbols(config, raw))


def check_answer(config: dict[str, Any], puzzle_id: str, raw: str | None) -> bool:
    """True when the normalised attempt equals the stored solution."""
    puzzle = config["puzzles"][puzzle_id]
    solution = puzzle["solution"]
    expected = " ".join(solution) if isinstance(solution, list) else str(solution)
    attempt = normalise_answer(config, puzzle_id, raw)
    # constant-time comparison: good habit for anything secret-like
    return bool(attempt) and hmac.compare_digest(attempt.encode(), expected.encode())


def missing_prerequisites(config: dict[str, Any], puzzle_id: str, state: GameState) -> list[str]:
    """List the unmet requirements (puzzles, clues, items) for a puzzle."""
    puzzle = config["puzzles"][puzzle_id]
    missing: list[str] = []
    missing += [f"puzzle:{p}" for p in puzzle["requires_puzzles"] if p not in state.solved_puzzles]
    missing += [f"clue:{c}" for c in puzzle["requires_clues"] if c not in state.discovered_clues]
    missing += [f"item:{i}" for i in puzzle["requires_items"] if i not in state.inventory]
    return missing


def is_attemptable(config: dict[str, Any], puzzle_id: str, state: GameState) -> bool:
    return not missing_prerequisites(config, puzzle_id, state)
