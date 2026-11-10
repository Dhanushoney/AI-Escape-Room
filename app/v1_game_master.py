"""Version 1 game logic: the LLM *is* the game.

Design (deliberately simple, as allowed by the brief's Version 1 scope):

* The whole room - objects, clues, puzzle solutions and rules - is written into
  the system prompt.  The model is trusted to apply the rules.
* The model reports progress by ending each reply with a machine-readable line
  ``STATUS: {...}``.  The interface displays whatever the model reports.
* Conversation memory is the chat history sent with each request, truncated to
  the most recent ``MAX_HISTORY_MESSAGES`` turns to bound prompt size.

These choices make Version 1 engaging and flexible but are also the source of
its weaknesses (see ``docs/project_report.md``): the model can forget, invent,
or be talked into reporting ``"escaped": true``.  Version 2 fixes this.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.game_config import load_config
from app.llm_client import ChatMessage, LLMClient, LLMResponseError
from app.utils import normalise_player_input

MAX_HISTORY_MESSAGES = 30

STATUS_PATTERN = re.compile(r"^\s*STATUS:\s*(\{.*\})\s*$", re.MULTILINE)

EMPTY_STATUS: dict[str, Any] = {
    "inventory": [],
    "solved_puzzles": [],
    "door_unlocked": False,
    "escaped": False,
}


def build_system_prompt(config: dict[str, Any] | None = None) -> str:
    """Compose the Game Master system prompt from the game configuration.

    Note: in Version 1 the solutions are *inside* the prompt - the model cannot
    judge answers otherwise.  This is exactly the exposure Version 2 removes.
    """
    config = config or load_config()
    lines: list[str] = []
    lines.append(
        f"You are the Game Master of a text escape-room game called '{config['title']} - {config['subtitle']}'. "
        "You describe the room atmospherically, interpret the player's natural-language actions, "
        "and decide what happens according to the rules below."
    )
    lines.append("\nSTORY:\n" + config["intro"])
    lines.append("\nROOM:\n" + config["room"]["description"])

    lines.append("\nOBJECTS (the only interactive objects in the room):")
    for obj_id, obj in config["objects"].items():
        lines.append(f"- {obj['name']} [{obj_id}]: {obj['description']} When examined: {obj['examine_text']}")
        if obj_id == "painting":
            lines.append(
                f"  The painting frame is locked; the {config['items']['brass_key']['name']} unlocks it: "
                f"{obj['unlocked_text']} Using the UV lamp on the unlocked painting reveals: {obj['reveal_text']}"
            )
        if obj.get("opened_text"):
            lines.append(f"  When unlocked: {obj['opened_text']}")

    lines.append("\nCOLLECTABLE ITEMS:")
    for item_id, item in config["items"].items():
        lines.append(f"- {item['name']} [{item_id}], found in {item['location']}: {item['description']}")

    lines.append("\nPUZZLES (solve in this order):")
    for puzzle_id, puzzle in config["puzzles"].items():
        solution = puzzle["solution"]
        solution_text = ", ".join(solution) if isinstance(solution, list) else solution
        lines.append(
            f"- {puzzle_id} '{puzzle['name']}' on the {puzzle['target']}: correct answer {solution_text}. "
            f"Explanation: {puzzle['success_text']}"
        )
    lines.append(
        "- FINAL CHALLENGE: after puzzle_3 the console releases the Exit Keycard. The player must take it "
        f"and use it on the exit door. Then: {config['escape_condition']['text']}"
    )

    lines.append(
        "\nRULES:\n"
        "1. Only the objects and items listed above exist. Politely refuse anything else.\n"
        "2. The player can only use items they have collected.\n"
        "3. Accept a puzzle answer only if it exactly matches the correct answer. Never reveal answers; "
        "give gentle hints if the player is stuck.\n"
        "4. Reveal clues only when the player examines the relevant object.\n"
        "5. Keep replies to 2-5 sentences, second person, present tense, mysterious tone.\n"
        "6. The game ends only when the player uses the Exit Keycard on the exit door."
    )
    lines.append(
        "\nOUTPUT FORMAT: After your narrative, end EVERY reply with one final line exactly like:\n"
        'STATUS: {"inventory": ["UV Lamp"], "solved_puzzles": ["puzzle_1"], "door_unlocked": false, "escaped": false}\n'
        "inventory = item names the player holds; solved_puzzles = puzzle ids solved so far; "
        "escaped = true only when the player has walked out of the exit door."
    )
    return "\n".join(lines)


def parse_game_master_reply(text: str) -> tuple[str, dict[str, Any] | None]:
    """Split a model reply into (narrative, reported status or ``None``)."""
    matches = list(STATUS_PATTERN.finditer(text))
    if not matches:
        return text.strip(), None
    last = matches[-1]
    narrative = (text[: last.start()] + text[last.end():]).strip()
    try:
        status = json.loads(last.group(1))
    except json.JSONDecodeError:
        return narrative, None
    if not isinstance(status, dict):
        return narrative, None
    cleaned = {
        "inventory": [str(x) for x in status.get("inventory", []) if isinstance(x, (str, int))],
        "solved_puzzles": [str(x) for x in status.get("solved_puzzles", []) if isinstance(x, (str, int))],
        "door_unlocked": bool(status.get("door_unlocked", False)),
        "escaped": bool(status.get("escaped", False)),
    }
    return narrative, cleaned


@dataclass
class V1Session:
    """Conversation state for one Version 1 game (stored in Streamlit session state)."""

    client: LLMClient
    config: dict[str, Any] = field(default_factory=load_config)
    history: list[ChatMessage] = field(default_factory=list)
    status: dict[str, Any] = field(default_factory=lambda: dict(EMPTY_STATUS))
    status_parse_failures: int = 0

    def __post_init__(self) -> None:
        self.system_prompt = build_system_prompt(self.config)

    @property
    def escaped(self) -> bool:
        """Completion as *reported by the LLM* - Version 1 has no other source of truth."""
        return bool(self.status.get("escaped"))

    def context_window(self) -> list[ChatMessage]:
        """Most recent turns sent to the model (older turns are forgotten)."""
        return self.history[-MAX_HISTORY_MESSAGES:]

    def send(self, player_text: str) -> str:
        """Send a player message, update history and the reported status, return the narrative.

        Raises :class:`app.llm_client.LLMError` on API problems; the history is
        left unchanged in that case so the player can simply retry.
        """
        text = normalise_player_input(player_text)
        if not text:
            return "The silence of the archive answers you. (Type an action, for example: examine the desk.)"

        pending = self.context_window() + [ChatMessage("user", text)]
        # Gemini expects the conversation to start with a user turn.
        while pending and pending[0].role != "user":
            pending.pop(0)
        reply = self.client.generate(self.system_prompt, pending, temperature=0.8)
        if not reply.strip():
            raise LLMResponseError("empty")

        narrative, status = parse_game_master_reply(reply)
        if status is None:
            self.status_parse_failures += 1  # keep the previous status
        else:
            self.status = status
        self.history.append(ChatMessage("user", text))
        # The full reply (including its STATUS line) is kept so the model can
        # read its own previous status on the next turn - its only "memory".
        self.history.append(ChatMessage("assistant", reply))
        return narrative or reply

    def reset(self) -> None:
        self.history.clear()
        self.status = dict(EMPTY_STATUS)
        self.status_parse_failures = 0
