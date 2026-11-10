"""Version 2 behaviour: gameplay, puzzles, LLM integration paths and the UI."""

from __future__ import annotations

import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from app.llm_client import LLMRateLimitError, LLMTimeoutError, MockLLMClient
from app.narrator import sanitise_narration
from app.game_engine import ActionResult
from app.v2_controller import V2Game
from tests.conftest import WALKTHROUGH, game_at, play

APP_DIR = Path(__file__).resolve().parent.parent / "app"


# --------------------------------------------------------------------------- #
# Core test cases (numbering matches docs/testing_report.md)
# --------------------------------------------------------------------------- #
def test_tc01_normal_gameplay_examine_and_discover_clues(offline_game):
    """TC-01: examining objects reveals clues and items and records them in state."""
    desk = offline_game.process("examine the desk")
    shelf = offline_game.process("examine the bookshelf")
    state = offline_game.state
    assert desk.result.success and shelf.result.success
    assert {"archivist_note", "cipher_half_a", "red_spine_digits"} <= set(state.discovered_clues)
    assert "uv_lamp" in state.revealed_items
    assert {"desk", "bookshelf"} <= set(state.examined_objects)
    assert "1887" in shelf.narration.text  # clue content is shown to the player


def test_tc02_correct_solution_updates_state():
    """TC-02: the correct drawer combination solves puzzle 1 and unlocks the drawer."""
    game = game_at("after_exploring")
    turn = game.process("enter 2947 on the drawer")
    assert turn.result.success and turn.result.code == "puzzle_solved"
    assert "puzzle_1" in game.state.solved_puzzles
    assert game.state.is_unlocked("drawer")
    assert {"brass_key", "cipher_card"} <= set(game.state.revealed_items)


def test_tc03_incorrect_code_is_rejected_without_unlocking():
    """TC-03: a wrong combination changes nothing except the attempt log."""
    game = game_at("after_exploring")
    before = game.state.critical_snapshot()
    turn = game.process("enter 1234 on the drawer")
    assert not turn.result.success and turn.result.code == "incorrect_answer"
    assert game.state.critical_snapshot() == before
    assert not game.state.is_unlocked("drawer")
    assert game.state.puzzle_attempts["puzzle_1"] == ["1234"]


def test_full_walkthrough_reaches_escape(offline_game):
    play(offline_game, WALKTHROUGH)
    state = offline_game.state
    assert state.escaped and state.door_open
    assert state.solved_puzzles == ["puzzle_1", "puzzle_2", "puzzle_3"]
    assert offline_game.engine.check_game_completion()


# --------------------------------------------------------------------------- #
# Puzzle dependencies, repetition, persistence, restart
# --------------------------------------------------------------------------- #
def test_correct_answer_without_prerequisites_is_not_accepted(offline_game):
    """Even a correct guess fails until the clues have been discovered."""
    turn = offline_game.process("enter 2947 on the drawer")
    assert turn.result.code == "prerequisites_missing"
    assert offline_game.state.solved_puzzles == []
    assert "puzzle_1" not in offline_game.state.puzzle_attempts  # not even logged as an attempt


def test_puzzle_three_requires_puzzle_two():
    game = game_at("after_puzzle_1")
    play(game, ["use the brass key on the painting", "use the uv lamp on the painting"])
    turn = game.process("enter 5836 on the console")
    assert turn.result.code == "prerequisites_missing"
    assert "puzzle_3" not in game.state.solved_puzzles


def test_repeated_puzzle_attempts_are_idempotent():
    game = game_at("after_exploring")
    play(game, ["enter 1111 on the drawer", "enter 2222 on the drawer", "enter 2947 on the drawer"])
    snapshot = game.state.critical_snapshot()
    again = game.process("enter 2947 on the drawer")
    assert again.result.code == "already_solved"
    assert game.state.critical_snapshot() == snapshot
    assert game.state.solved_puzzles.count("puzzle_1") == 1
    assert game.state.puzzle_attempts["puzzle_1"] == ["1111", "2222", "2947"]


def test_state_persists_across_turns_within_session(offline_game):
    play(offline_game, WALKTHROUGH[:2])
    for filler in ["look around", "hint", "examine the bookshelf", "inventory", "examine the painting"]:
        offline_game.process(filler)
    assert offline_game.state.inventory == ["uv_lamp"]
    assert offline_game.state.turn_count == 7
    assert len(offline_game.state.action_history) == 7


def test_restart_resets_everything():
    game = game_at("after_puzzle_2")
    game.reset()
    fresh = V2Game(client=None)
    assert game.state.to_dict() == fresh.state.to_dict()
    assert game.turns == []


def test_empty_message_is_ignored(offline_game):
    before = offline_game.state.to_dict()
    assert offline_game.process("   \n\t ") is None
    assert offline_game.process("") is None
    assert offline_game.state.to_dict() == before


def test_hints_never_contain_solutions(config):
    game = V2Game(client=None)
    for step in range(len(WALKTHROUGH)):
        hint = game.engine.get_hint().message
        assert "2947" not in hint and "5836" not in hint
        assert "moon, star, triangle, circle" not in hint.lower()
        game.process(WALKTHROUGH[step])


# --------------------------------------------------------------------------- #
# LLM paths (mocked)
# --------------------------------------------------------------------------- #
def _router(intent: dict, narration: str):
    """Mock that answers the interpreter call with ``intent`` and the narrator call with ``narration``."""
    def respond(system, messages, schema):
        return json.dumps(intent) if schema is not None else narration
    return MockLLMClient(responses=respond)


def test_llm_interpreter_and_narrator_are_used_when_valid():
    game = game_at("start", client=_router(
        {"action": "examine", "target": "bookshelf", "item": "none", "answer": "none", "unknown_reference": "none"},
        "Dust drifts from the red spines: 1923 - 4, 1887 - 2, 1951 - 7, 1902 - 9.",
    ))
    turn = game.process("have a gander at those books")
    assert turn.request.source == "llm" and turn.interpreter_fallback is None
    assert turn.narration.source == "llm"
    assert "red_spine_digits" in game.state.discovered_clues


def test_invalid_llm_json_falls_back_to_rules_safely():
    game = game_at("start", client=MockLLMClient(responses=["{this is not json", "Narration."]))
    turn = game.process("examine the desk")
    assert turn.interpreter_fallback == "invalid_llm_output"
    assert turn.request.source == "rules" and turn.result.success


def test_api_errors_fall_back_to_engine_text():
    game = game_at("start", client=MockLLMClient(raise_error=LLMTimeoutError("t")))
    turn = game.process("examine the desk")
    assert turn.interpreter_fallback == "llm_unavailable"
    assert turn.narration.source == "engine_fallback"
    assert turn.narration.text == turn.result.message
    game.client = MockLLMClient(raise_error=LLMRateLimitError("429"))
    assert game.process("take the lamp").result.success


def test_narrator_solution_leak_is_blocked(config):
    game = game_at("after_exploring")
    result = ActionResult(False, "incorrect_answer", "The dials grind but the drawer stays locked.")
    narration = sanitise_narration("Wrong! Try 2-9-4-7 instead.", result, config, game.state)
    assert narration.source == "engine_fallback" and narration.guard_reason == "solution_leak:puzzle_1"
    assert "2" not in narration.text


def test_narrator_false_escape_claim_is_blocked(config):
    game = game_at("start")
    result = ActionResult(False, "locked", "The electromagnetic lock does not move.")
    narration = sanitise_narration("The exit door swings open and you are free!", result, config, game.state)
    assert narration.guard_reason == "false_escape_claim"
    assert narration.text == result.message


def test_narrator_may_repeat_clue_digits_from_facts(config):
    """Clue text that legitimately contains digits is not mistaken for a leak."""
    game = game_at("start")
    facts = config["objects"]["bookshelf"]["examine_text"]
    narration = sanitise_narration("You read: " + facts, ActionResult(True, "examined", facts), config, game.state)
    assert narration.source == "llm"


# --------------------------------------------------------------------------- #
# Integration: the Streamlit app
# --------------------------------------------------------------------------- #
def test_streamlit_v2_app_plays_and_restarts():
    at = AppTest.from_file(str(APP_DIR / "version2.py"), default_timeout=30).run()
    assert not at.exception
    at.chat_input[0].set_value("examine the desk").run()
    at.chat_input[0].set_value("take the uv lamp").run()
    game = at.session_state["v2_game"]
    assert game.state.inventory == ["uv_lamp"]
    assert any("Engine verdict" in c.value for c in at.caption)
    restart = next(b for b in at.button if b.key == "v2_restart")
    restart.click().run()
    assert at.session_state["v2_game"].state.inventory == []
    assert not at.exception
