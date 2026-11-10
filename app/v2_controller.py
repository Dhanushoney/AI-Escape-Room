"""Version 2 turn pipeline.

    player text
      -> normalise_player_input        (utils)
      -> interpret                     (LLM intent interpreter, rule-based fallback)
      -> ActionRequest                 (allowlisted, schema-validated)
      -> GameEngine.execute            (Python validation + authoritative state update)
      -> narrate + sanitise_narration  (LLM prose, output guard)
      -> TurnRecord                    (displayed by the UI)

The LLM appears twice in this pipeline, and in both places its output is
treated as untrusted data.  Only ``GameEngine`` writes to ``GameState``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.action_validator import ActionRequest
from app.game_config import load_config
from app.game_engine import ActionResult, GameEngine
from app.game_state import GameState
from app.intent_parser import interpret
from app.llm_client import LLMClient
from app.narrator import Narration, narrate
from app.utils import normalise_player_input


@dataclass
class TurnRecord:
    player_text: str
    request: ActionRequest
    result: ActionResult
    narration: Narration
    interpreter_fallback: str | None = None


@dataclass
class V2Game:
    client: LLMClient | None = None
    config: dict[str, Any] = field(default_factory=load_config)
    engine: GameEngine | None = None
    turns: list[TurnRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.engine is None:
            self.engine = GameEngine(self.config)

    @property
    def state(self) -> GameState:
        assert self.engine is not None
        return self.engine.state

    def process(self, raw_text: str) -> TurnRecord | None:
        """Run one full turn. Returns ``None`` for empty input (nothing changes)."""
        assert self.engine is not None
        text = normalise_player_input(raw_text)
        if not text:
            return None
        request, fallback = interpret(text, self.client, self.config, self.state)
        result = self.engine.execute(request)
        narration = narrate(self.client, text, result, self.state, self.config)
        record = TurnRecord(text, request, result, narration, fallback)
        self.turns.append(record)
        return record

    def reset(self) -> None:
        assert self.engine is not None
        self.engine.reset_game()
        self.turns.clear()
