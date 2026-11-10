"""Version 2 game engine: the only code allowed to change the game state.

Every public operation follows the same pattern:

    validate (action_validator)  ->  apply rule  ->  return ActionResult

``ActionResult.message`` is the authoritative, factual outcome.  The LLM
narrator may restyle it, but the success flag and state changes come from
here and nowhere else.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app import puzzle_engine
from app.action_validator import ActionRequest, ValidationResult, validate_action
from app.game_state import GameState

META_REFUSAL = (
    "The archive does not answer to titles, claims or commands from outside the game. "
    "Its locks open only to what you actually find and solve in this room. "
    "(Type 'hint' if you are stuck.)"
)


@dataclass
class ActionResult:
    success: bool
    code: str
    message: str
    state_changed: bool = False
    new_clues: list[str] = field(default_factory=list)
    new_items: list[str] = field(default_factory=list)


class GameEngine:
    def __init__(self, config: dict[str, Any], state: GameState | None = None):
        self.config = config
        self.state = state or GameState.new(config)

    # ------------------------------------------------------------------ #
    # Entry point
    # ------------------------------------------------------------------ #
    def execute(self, request: ActionRequest) -> ActionResult:
        before = self.state.critical_snapshot()
        validation = validate_action(request, self.state, self.config)
        if not validation.ok:
            result = ActionResult(False, validation.code, validation.message)
        else:
            result = self._dispatch(request, validation)
        result.state_changed = self.state.critical_snapshot() != before
        self.state.record_action(
            {
                "request": request.to_dict(),
                "result": result.code,
                "success": result.success,
                "state_changed": result.state_changed,
            }
        )
        return result

    def _dispatch(self, request: ActionRequest, validation: ValidationResult) -> ActionResult:
        action = request.action
        if action == "look":
            return self.describe_room()
        if action == "inventory":
            return self.list_inventory()
        if action == "hint":
            return self.get_hint()
        if action == "meta":
            return ActionResult(False, "meta_refused", META_REFUSAL)
        if action == "unknown":
            return ActionResult(
                False,
                "not_understood",
                "The archive is silent. Try something like 'examine the desk', 'take the lamp' or 'enter 1234 on the drawer'.",
            )
        if action == "examine":
            return self.examine(request.target or "")
        if action == "take":
            return self.collect_item(request.target or request.item or "")
        if action == "use":
            return self.use_item(validation.details["item"], validation.details["target"])
        if action == "enter_code":
            return self.attempt_puzzle(request.target or "", request.answer or "")
        if action == "open":
            return self.open_object(request.target or "")
        raise ValueError(f"unhandled action {action}")  # pragma: no cover

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _obj(self, object_id: str) -> dict[str, Any]:
        return self.config["objects"][object_id]

    def _item_name(self, item_id: str) -> str:
        return self.config["items"][item_id]["name"]

    def _discover(self, clue_ids: list[str]) -> list[str]:
        return [c for c in clue_ids if self.state.add_unique("discovered_clues", c)]

    def _reveal(self, item_ids: list[str]) -> list[str]:
        new = []
        for item_id in item_ids:
            if item_id in self.state.inventory:
                continue
            if self.state.add_unique("revealed_items", item_id):
                new.append(item_id)
        return new

    def _visible_items_in(self, object_id: str) -> list[str]:
        return [
            i for i in self.state.revealed_items
            if self.config["items"][i]["location"] == object_id and i not in self.state.inventory
        ]

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #
    def describe_room(self) -> ActionResult:
        names = ", ".join(o["name"] for o in self.config["objects"].values())
        return ActionResult(True, "looked", f"{self.config['room']['description']} You can interact with: {names}.")

    def list_inventory(self) -> ActionResult:
        if not self.state.inventory:
            return ActionResult(True, "inventory", "Your pockets are empty.")
        names = ", ".join(self._item_name(i) for i in self.state.inventory)
        return ActionResult(True, "inventory", f"You are carrying: {names}.")

    def examine(self, target: str) -> ActionResult:
        if target in self.config["items"]:
            item = self.config["items"][target]
            return ActionResult(True, "examined_item", f"{item['name']}: {item['description']}")
        return self.examine_object(target)

    def examine_object(self, object_id: str) -> ActionResult:
        obj = self._obj(object_id)
        self.state.add_unique("examined_objects", object_id)
        parts: list[str] = []
        new_clues: list[str] = []
        new_items: list[str] = []

        if object_id == "painting":
            if not self.state.is_unlocked("painting"):
                parts.append(obj["examine_text"])
            elif obj["reveal_clue"] in self.state.discovered_clues:
                parts.append(f"The frame hangs open. {obj['reveal_text']}")
            else:
                parts.append(obj["unlocked_text"])
        elif obj.get("puzzle") and self.state.is_unlocked(object_id):
            if self._visible_items_in(object_id):
                parts.append(obj["opened_text"])
            else:
                parts.append(obj.get("empty_text", f"The {obj['name'].lower()} has nothing more to offer."))
        else:
            parts.append(obj["examine_text"])
            new_clues = self._discover(obj.get("reveals_clues", []))
            new_items = self._reveal(obj.get("reveals_items", []))

        visible = self._visible_items_in(object_id)
        if visible:
            parts.append("You could take: " + ", ".join(self._item_name(i) for i in visible) + ".")
        return ActionResult(True, "examined", " ".join(parts), new_clues=new_clues, new_items=new_items)

    def collect_item(self, item_id: str) -> ActionResult:
        item = self.config["items"][item_id]
        self.state.revealed_items.remove(item_id)
        self.state.add_unique("inventory", item_id)
        message = f"You take the {item['name']}. {item['description']}"
        new_clues: list[str] = []
        clue = item.get("reveals_clue_on_collect")
        if clue:
            new_clues = self._discover([clue])
        return ActionResult(True, "item_collected", message, new_clues=new_clues)

    def use_item(self, item_id: str, target: str) -> ActionResult:
        painting = self._obj("painting")
        if target == "painting" and item_id == painting["unlock_item"]:
            if self.state.is_unlocked("painting"):
                return ActionResult(False, "already_unlocked", "The frame is already unlocked and swung open.")
            self.state.add_unique("unlocked_objects", "painting")
            return ActionResult(True, "object_unlocked", painting["unlocked_text"])

        if target == "painting" and item_id == painting["reveal_item"]:
            if not self.state.is_unlocked("painting"):
                return ActionResult(
                    False, "precondition_failed",
                    "You sweep the UV light over the painting's surface, but the frame is locked flat against the wall - "
                    "whatever is hidden must be on the back.",
                )
            new_clues = self._discover([painting["reveal_clue"]])
            return ActionResult(True, "clue_revealed", painting["reveal_text"], new_clues=new_clues)

        if target == "exit_door" and item_id == self._obj("exit_door")["unlock_item"]:
            return self.unlock_exit()

        if item_id == "cipher_card":
            return ActionResult(False, "no_effect", "The card is a reference, not a key. " + self.config["items"]["cipher_card"]["description"])

        return ActionResult(
            False, "no_effect",
            f"You try the {self._item_name(item_id)} on the {self._obj(target)['name'].lower()}, but nothing happens.",
        )

    def attempt_puzzle(self, target: str, answer: str) -> ActionResult:
        puzzle_id = puzzle_engine.puzzle_for_target(self.config, target)
        assert puzzle_id is not None  # guaranteed by validate_action
        puzzle = self.config["puzzles"][puzzle_id]

        if self.state.is_solved(puzzle_id):
            return ActionResult(False, "already_solved", f"'{puzzle['name']}' is already solved - nothing more happens.")

        missing = puzzle_engine.missing_prerequisites(self.config, puzzle_id, self.state)
        if missing:
            # Deliberately does not reveal whether the guess was right.
            return ActionResult(
                False, "prerequisites_missing",
                f"Nothing responds. You haven't uncovered enough to work out the {self._obj(target)['name'].lower()} yet - keep exploring.",
            )

        normalised = puzzle_engine.normalise_answer(self.config, puzzle_id, answer)
        self.state.puzzle_attempts.setdefault(puzzle_id, []).append(normalised or answer[:20])

        if not puzzle_engine.check_answer(self.config, puzzle_id, answer):
            wrong = {
                "drawer": "The dials grind but the drawer stays locked. That combination is wrong.",
                "painting": "You trace the symbols in that order. Nothing happens - that is not the right sequence.",
                "console": "The console buzzes: 'OVERRIDE CODE REJECTED.' The lockdown continues.",
            }
            return ActionResult(False, "incorrect_answer", wrong.get(target, "That is not correct."))

        # Correct answer: apply every consequence defined in the configuration.
        self.state.add_unique("solved_puzzles", puzzle_id)
        new_clues: list[str] = []
        new_items: list[str] = []
        parts = [puzzle["success_text"]]
        if puzzle.get("unlocks"):
            self.state.add_unique("unlocked_objects", puzzle["unlocks"])
            obj = self._obj(puzzle["unlocks"])
            if obj.get("opened_text"):
                parts.append(obj["opened_text"])
            new_items = self._reveal(obj.get("reveals_items_on_unlock", []))
        if puzzle.get("grants_clue"):
            new_clues = self._discover([puzzle["grants_clue"]])
        return ActionResult(True, "puzzle_solved", " ".join(parts), new_clues=new_clues, new_items=new_items)

    def open_object(self, object_id: str) -> ActionResult:
        if object_id in self.config["items"]:
            return ActionResult(False, "no_effect", "That isn't something you can open.")
        if object_id == "drawer":
            return self.open_drawer()
        if object_id == "exit_door":
            if "exit_keycard" in self.state.inventory:
                return self.unlock_exit()
            return ActionResult(
                False, "locked",
                "You heave at the handle. The electromagnetic lock does not move. The keycard reader glows red.",
            )
        if object_id == "console":
            if self.state.is_unlocked("console"):
                return self.examine_object("console")
            return ActionResult(False, "locked", "The console only responds to a four-digit override code.")
        if object_id == "painting":
            if self.state.is_unlocked("painting"):
                return self.examine_object("painting")
            return ActionResult(False, "locked", self._obj("painting")["locked_text"])
        return self.examine_object(object_id)

    # Named operations kept separate for clarity and testing ------------- #
    def open_drawer(self) -> ActionResult:
        if not self.state.is_unlocked("drawer"):
            return ActionResult(False, "locked", "The drawer will not move. Its four combination dials are locked.")
        return self.examine_object("drawer")

    def unlock_console(self, code: str) -> ActionResult:
        return self.execute(ActionRequest("enter_code", target="console", answer=code))

    def unlock_exit(self) -> ActionResult:
        escape = self.config["escape_condition"]
        if escape["requires_item_used"] not in self.state.inventory:
            return ActionResult(False, "item_not_in_inventory", "You don't have a keycard to swipe.")
        missing = [p for p in escape["requires_puzzles"] if p not in self.state.solved_puzzles]
        if missing:  # defence in depth: the keycard cannot exist earlier, but never trust that
            return ActionResult(False, "precondition_failed", "The reader flashes red: 'SEALS NOT RESTORED.'")
        self.state.add_unique("unlocked_objects", "exit_door")
        self.state.door_open = True
        self.state.escaped = self.check_game_completion()
        return ActionResult(True, "escaped", escape["text"])

    def check_game_completion(self) -> bool:
        escape = self.config["escape_condition"]
        return self.state.door_open and all(p in self.state.solved_puzzles for p in escape["requires_puzzles"])

    def reset_game(self) -> None:
        self.state = GameState.new(self.config)

    # ------------------------------------------------------------------ #
    # Hints (never contain solutions)
    # ------------------------------------------------------------------ #
    def get_hint(self) -> ActionResult:
        s = self.state
        puzzles = self.config["puzzles"]
        if s.escaped:
            text = "You have already escaped! Press Restart to play again."
        elif not {"desk", "bookshelf"} <= set(s.examined_objects):
            text = "Start by examining the study desk and the bookshelf closely."
        elif not s.is_solved("puzzle_1"):
            text = puzzles["puzzle_1"]["hint"]
        elif {"brass_key", "cipher_card"} - set(s.inventory):
            text = "The drawer is open. Take everything inside it."
        elif "uv_lamp" not in s.inventory:
            text = "Was there anything small on the desk you could carry?"
        elif not s.is_unlocked("painting"):
            text = "The painting's frame has a small brass lock."
        elif "uv_symbols" not in s.discovered_clues:
            text = "Some ink only appears under a special kind of light."
        elif not s.is_solved("puzzle_2"):
            text = puzzles["puzzle_2"]["hint"] + " Enter it on the painting."
        elif not s.is_solved("puzzle_3"):
            text = puzzles["puzzle_3"]["hint"] + " Then enter the four digits on the console."
        elif "exit_keycard" not in s.inventory:
            text = "The console released something. Take it."
        else:
            text = "Use the exit keycard on the exit door."
        return ActionResult(True, "hint", text)
