"""Shared fixtures. No test needs a real API key: LLMs are mocked."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.game_config import load_config  # noqa: E402
from app.game_engine import GameEngine  # noqa: E402
from app.v2_controller import V2Game  # noqa: E402

# The shortest correct walkthrough, split into named stages.
WALKTHROUGH: list[str] = [
    "examine the desk",                       # 0  clues: archivist_note, cipher_half_a; reveals UV lamp
    "take the uv lamp",                       # 1
    "examine the bookshelf",                  # 2  clue: red_spine_digits
    "enter 2947 on the drawer",               # 3  puzzle_1
    "take the brass key",                     # 4
    "take the cipher card",                   # 5  clue: cipher_half_b
    "use the brass key on the painting",      # 6  painting unlocked
    "use the uv lamp on the painting",        # 7  clue: uv_symbols
    "enter moon star triangle circle on the painting",  # 8  puzzle_2
    "enter 5836 on the console",              # 9  puzzle_3, keycard revealed
    "take the keycard",                       # 10
    "use the keycard on the exit door",       # 11 escaped
]

STAGES = {
    "start": 0,
    "after_exploring": 3,        # desk + bookshelf examined, lamp held
    "after_puzzle_1": 6,         # drawer open, key + card held
    "after_puzzle_2": 9,
    "before_exit": 11,           # keycard in hand
}


@pytest.fixture(autouse=True)
def _no_real_llm(monkeypatch):
    """Guarantee tests never call the real Gemini API."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("LLM_MODE", "mock")


@pytest.fixture
def config():
    return load_config()


@pytest.fixture
def engine(config):
    return GameEngine(config)


def play(game: V2Game, commands: list[str]) -> None:
    for command in commands:
        game.process(command)


def game_at(stage: str, client=None) -> V2Game:
    """An offline game advanced to a named stage, then given ``client``."""
    game = V2Game(client=None)
    play(game, WALKTHROUGH[: STAGES[stage]])
    game.client = client
    return game


@pytest.fixture
def offline_game():
    return V2Game(client=None)
