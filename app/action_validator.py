"""Version 2 action requests and their validation.

Two separate checks happen before anything touches the game state:

1. **Schema / allowlist validation** - :func:`parse_action_request` turns the
   (untrusted) output of the LLM intent interpreter into an
   :class:`ActionRequest`.  Only allowlisted action names and known object/item
   identifiers survive; everything else is rejected or reduced to ``None``.
   Nothing produced by the LLM is ever executed as code.

2. **Rule validation** - :func:`validate_action` checks the request against the
   current :class:`GameState` (does the object exist, is the item really in the
   inventory, is the object unlocked, ...).  The engine only mutates state when
   this returns ``ok``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.game_state import GameState
from app.puzzle_engine import puzzle_for_target

ALLOWED_ACTIONS: tuple[str, ...] = (
    "look",        # describe the room
    "examine",     # inspect an object or a held item
    "take",        # collect a revealed item
    "use",         # use a held item on an object
    "enter_code",  # submit a puzzle answer to an object
    "open",        # open / try an object (drawer, door, ...)
    "inventory",   # list held items
    "hint",        # ask for a nudge
    "meta",        # out-of-game request: claims of authority, rule changes, secret extraction
    "unknown",     # could not interpret
)

MAX_ANSWER_LENGTH = 60
MAX_REFERENCE_LENGTH = 40
_SAFE_ANSWER = re.compile(r"[^A-Za-z0-9 ,\-]")
_NONE_VALUES = {"", "none", "null", "nil", "n/a"}

# JSON schema given to Gemini (response_json_schema) for intent interpretation.
INTENT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": list(ALLOWED_ACTIONS)},
        "target": {"type": "string", "description": "object or item id, or 'none'"},
        "item": {"type": "string", "description": "item id used in a 'use' action, or 'none'"},
        "answer": {"type": "string", "description": "code or symbol sequence for enter_code, or 'none'"},
        "unknown_reference": {
            "type": "string",
            "description": "name of a thing the player mentions that is not in the id lists, or 'none'",
        },
    },
    "required": ["action", "target", "item", "answer", "unknown_reference"],
}


class ActionRequestError(ValueError):
    """The interpreter output was malformed or outside the allowlist."""


@dataclass
class ActionRequest:
    action: str
    target: str | None = None
    item: str | None = None
    answer: str | None = None
    unknown_reference: str | None = None
    source: str = "rules"  # "llm" or "rules"

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "target": self.target,
            "item": self.item,
            "answer": self.answer,
            "unknown_reference": self.unknown_reference,
            "source": self.source,
        }


@dataclass
class ValidationResult:
    ok: bool
    code: str
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


def _clean_optional(value: Any, max_length: int) -> str | None:
    if value is None:
        return None
    if not isinstance(value, (str, int)):
        raise ActionRequestError("field must be a string")
    text = str(value).strip()
    if text.lower() in _NONE_VALUES:
        return None
    return text[:max_length]


def parse_action_request(raw: str | dict[str, Any], config: dict[str, Any], source: str = "llm") -> ActionRequest:
    """Validate interpreter output against the schema and the allowlists.

    Raises :class:`ActionRequestError` for malformed JSON, non-object payloads,
    or actions outside :data:`ALLOWED_ACTIONS`.  Unknown object/item ids are
    not errors: they are moved into ``unknown_reference`` so the engine can
    tell the player that the thing does not exist.
    """
    if isinstance(raw, str):
        text = raw.strip()
        # tolerate ```json fences some models add
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ActionRequestError("interpreter output is not valid JSON") from exc
    else:
        data = raw
    if not isinstance(data, dict):
        raise ActionRequestError("interpreter output must be a JSON object")

    action = data.get("action")
    if not isinstance(action, str) or action.strip().lower() not in ALLOWED_ACTIONS:
        raise ActionRequestError(f"action {action!r} is not allowlisted")
    action = action.strip().lower()

    known_targets = set(config["objects"]) | set(config["items"])
    known_items = set(config["items"])

    unknown_reference = _clean_optional(data.get("unknown_reference"), MAX_REFERENCE_LENGTH)

    target = _clean_optional(data.get("target"), MAX_REFERENCE_LENGTH)
    if target is not None:
        target = target.lower()
        if target not in known_targets:
            unknown_reference = unknown_reference or target
            target = None

    item = _clean_optional(data.get("item"), MAX_REFERENCE_LENGTH)
    if item is not None:
        item = item.lower()
        if item not in known_items:
            unknown_reference = unknown_reference or item
            item = None

    answer = _clean_optional(data.get("answer"), MAX_ANSWER_LENGTH)
    if answer is not None:
        answer = _SAFE_ANSWER.sub("", answer).strip() or None

    return ActionRequest(action, target, item, answer, unknown_reference, source)


# --------------------------------------------------------------------------- #
# Rule validation against the current state
# --------------------------------------------------------------------------- #
def _name(config: dict[str, Any], ident: str) -> str:
    if ident in config["objects"]:
        return config["objects"][ident]["name"]
    if ident in config["items"]:
        return config["items"][ident]["name"]
    return ident


def validate_action(request: ActionRequest, state: GameState, config: dict[str, Any]) -> ValidationResult:
    """Check whether ``request`` is permitted in ``state``. Never mutates state."""
    action = request.action
    objects = config["objects"]
    items = config["items"]

    if state.escaped and action not in {"look", "inventory", "examine", "hint"}:
        return ValidationResult(False, "game_over", "You have already escaped. Press Restart to play again.")

    if action not in ALLOWED_ACTIONS:
        return ValidationResult(False, "unsupported", "That action is not possible here.")

    if action in {"look", "inventory", "hint", "meta", "unknown"}:
        return ValidationResult(True, "ok")

    # Defence in depth: requests may be built in code, not only via
    # parse_action_request, so identifiers are checked again here.
    for ident in (request.target, request.item):
        if ident is not None and ident not in objects and ident not in items:
            return ValidationResult(False, "nonexistent_object", f"There is no \"{ident}\" in this room.")
    if request.item is not None and request.item not in items:
        return ValidationResult(False, "nonexistent_item", "That is not an item.")

    # A reference to something not in the room always fails, whatever the verb.
    if request.unknown_reference and request.target is None and request.item is None:
        return ValidationResult(
            False,
            "nonexistent_object",
            f"There is no \"{request.unknown_reference}\" in this room.",
        )

    if action == "examine":
        if request.target is None:
            return ValidationResult(False, "missing_target", "What would you like to examine?")
        if request.target in items and request.target not in state.inventory:
            if request.target in state.revealed_items:
                return ValidationResult(True, "ok")
            return ValidationResult(False, "not_visible", "You don't see anything like that here.")
        return ValidationResult(True, "ok")

    if action == "take":
        target = request.target or request.item
        if target is None:
            return ValidationResult(False, "missing_target", "What would you like to take?")
        if target in objects:
            return ValidationResult(False, "not_collectable", f"The {_name(config, target).lower()} is far too heavy to carry.")
        if target in state.inventory:
            return ValidationResult(False, "already_held", f"You already have the {_name(config, target)}.")
        if target not in state.revealed_items:
            return ValidationResult(False, "not_visible", "You don't see anything like that to take.")
        return ValidationResult(True, "ok")

    if action == "use":
        item = request.item
        target = request.target
        # "use the drawer" with no item is really an open/examine request
        if item is None and target in items:
            item, target = target, None
        if item is None:
            return ValidationResult(False, "missing_item", "What do you want to use?")
        if item not in state.inventory:
            return ValidationResult(
                False,
                "item_not_in_inventory",
                f"You are not carrying a {_name(config, item).lower()}. You can only use items you have collected.",
            )
        if target is None:
            if item == "exit_keycard":
                return ValidationResult(True, "ok", details={"item": item, "target": "exit_door"})
            return ValidationResult(False, "missing_target", f"Use the {_name(config, item)} on what?")
        if target in items:
            return ValidationResult(False, "invalid_combination", "Nothing useful happens.")
        return ValidationResult(True, "ok", details={"item": item, "target": target})

    if action == "enter_code":
        if not request.answer:
            return ValidationResult(False, "missing_answer", "What code or sequence do you want to enter?")
        target = request.target
        if target is None:
            return ValidationResult(
                False, "missing_target", "Where do you want to enter that - the drawer, the painting or the console?"
            )
        if target == "exit_door":
            return ValidationResult(
                False, "wrong_mechanism", "The exit door has no keypad - only a keycard reader."
            )
        if puzzle_for_target(config, target) is None:
            return ValidationResult(False, "no_mechanism", f"The {_name(config, target).lower()} has nothing to enter a code into.")
        return ValidationResult(True, "ok")

    if action == "open":
        if request.target is None:
            return ValidationResult(False, "missing_target", "What would you like to open?")
        return ValidationResult(True, "ok")

    return ValidationResult(False, "unsupported", "That action is not possible here.")  # pragma: no cover
