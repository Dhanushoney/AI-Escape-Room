"""Loading and sanity-checking of the game configuration.

The JSON file in ``config/game_config.json`` is the single place where the
room, its objects, items, clues and puzzle solutions are defined.  Version 1
turns it into a system prompt for the LLM; Version 2 uses it as the rule book
for the Python game engine.
"""

from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "game_config.json"


class ConfigError(ValueError):
    """Raised when the game configuration is internally inconsistent."""


@lru_cache(maxsize=4)
def _load_raw(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def load_config(path: Path | str = CONFIG_PATH) -> dict[str, Any]:
    """Return a fresh, validated copy of the game configuration."""
    config = copy.deepcopy(_load_raw(str(path)))
    validate_config(config)
    return config


def validate_config(config: dict[str, Any]) -> None:
    """Check that every reference in the configuration points at something real.

    Catching a typo here (for example a puzzle that requires a clue nobody can
    discover) prevents an unwinnable game.
    """
    objects = config["objects"]
    items = config["items"]
    clues = config["clues"]
    puzzles = config["puzzles"]

    discoverable_clues: set[str] = set()
    for obj in objects.values():
        discoverable_clues.update(obj.get("reveals_clues", []))
        if obj.get("reveal_clue"):
            discoverable_clues.add(obj["reveal_clue"])
    for item in items.values():
        if item.get("reveals_clue_on_collect"):
            discoverable_clues.add(item["reveals_clue_on_collect"])
    for puzzle in puzzles.values():
        if puzzle.get("grants_clue"):
            discoverable_clues.add(puzzle["grants_clue"])

    for clue_id in discoverable_clues:
        if clue_id not in clues:
            raise ConfigError(f"Clue '{clue_id}' is referenced but not defined")

    for item_id, item in items.items():
        if item["location"] not in objects:
            raise ConfigError(f"Item '{item_id}' is located in unknown object")

    for puzzle_id, puzzle in puzzles.items():
        if puzzle["target"] not in objects:
            raise ConfigError(f"Puzzle '{puzzle_id}' targets an unknown object")
        for clue_id in puzzle["requires_clues"]:
            if clue_id not in discoverable_clues:
                raise ConfigError(f"Puzzle '{puzzle_id}' needs undiscoverable clue '{clue_id}'")
        for dep in puzzle["requires_puzzles"]:
            if dep not in puzzles:
                raise ConfigError(f"Puzzle '{puzzle_id}' depends on unknown puzzle '{dep}'")
        for item_id in puzzle["requires_items"]:
            if item_id not in items:
                raise ConfigError(f"Puzzle '{puzzle_id}' needs unknown item '{item_id}'")

    escape = config["escape_condition"]
    if escape["requires_item_used"] not in items or escape["on"] not in objects:
        raise ConfigError("Escape condition references unknown item or object")


def public_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of the configuration with every puzzle solution removed.

    Version 2 never needs to show solutions to the LLM, so anything derived
    from the configuration for prompting should start from this view.
    """
    view = copy.deepcopy(config)
    for puzzle in view["puzzles"].values():
        puzzle.pop("solution", None)
        puzzle.pop("success_text", None)
    return view


def solution_strings(config: dict[str, Any]) -> dict[str, str]:
    """Map each puzzle id to its canonical solution text (for leak detection)."""
    out: dict[str, str] = {}
    for puzzle_id, puzzle in config["puzzles"].items():
        solution = puzzle["solution"]
        out[puzzle_id] = " ".join(solution) if isinstance(solution, list) else str(solution)
    return out
