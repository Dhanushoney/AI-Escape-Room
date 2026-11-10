"""Version 2 authoritative game state.

``GameState`` is the single source of truth for a Version 2 game.  Only the
Python engine (``app/game_engine.py``) mutates it; the LLM only ever receives
a read-only, solution-free summary produced by :meth:`GameState.public_summary`.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from typing import Any

# Fields whose values define game progress.  State-integrity tests compare
# these before and after rejected actions.
CRITICAL_FIELDS = (
    "inventory",
    "discovered_clues",
    "revealed_items",
    "solved_puzzles",
    "unlocked_objects",
    "door_open",
    "escaped",
)


@dataclass
class GameState:
    current_room: str = "reading_room"
    available_objects: list[str] = field(default_factory=list)
    examined_objects: list[str] = field(default_factory=list)
    inventory: list[str] = field(default_factory=list)          # item ids actually collected
    discovered_clues: list[str] = field(default_factory=list)
    revealed_items: list[str] = field(default_factory=list)     # items the player has seen but not taken
    solved_puzzles: list[str] = field(default_factory=list)
    puzzle_attempts: dict[str, list[str]] = field(default_factory=dict)  # puzzle id -> normalised attempts
    unlocked_objects: list[str] = field(default_factory=list)
    door_open: bool = False
    escaped: bool = False
    turn_count: int = 0
    action_history: list[dict[str, Any]] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    @classmethod
    def new(cls, config: dict[str, Any]) -> "GameState":
        """Create the starting state for the configured room."""
        return cls(
            current_room=config["room"]["id"],
            available_objects=list(config["objects"].keys()),
            unlocked_objects=[oid for oid, obj in config["objects"].items() if not obj.get("locked")],
        )

    # Mutation helpers (idempotent, so repeating an action never duplicates state)
    def add_unique(self, field_name: str, value: str) -> bool:
        values: list[str] = getattr(self, field_name)
        if value in values:
            return False
        values.append(value)
        return True

    def record_action(self, entry: dict[str, Any]) -> None:
        self.turn_count += 1
        self.action_history.append({"turn": self.turn_count, **entry})

    # Read helpers
    def has_item(self, item_id: str) -> bool:
        return item_id in self.inventory

    def is_unlocked(self, object_id: str) -> bool:
        return object_id in self.unlocked_objects

    def is_solved(self, puzzle_id: str) -> bool:
        return puzzle_id in self.solved_puzzles

    def critical_snapshot(self) -> dict[str, Any]:
        """Deep copy of the progress-defining fields (for integrity checks)."""
        return {name: copy.deepcopy(getattr(self, name)) for name in CRITICAL_FIELDS}

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        return cls(**copy.deepcopy(data))

    def public_summary(self, config: dict[str, Any]) -> dict[str, Any]:
        """Facts the narrator may use. Contains names and discovered clue text only - never solutions."""
        return {
            "room": config["room"]["name"],
            "inventory": [config["items"][i]["name"] for i in self.inventory],
            "discovered_clues": [config["clues"][c] for c in self.discovered_clues],
            "solved_puzzles": [config["puzzles"][p]["name"] for p in self.solved_puzzles],
            "unlocked": [config["objects"][o]["name"] for o in self.unlocked_objects],
            "door_open": self.door_open,
            "escaped": self.escaped,
        }
