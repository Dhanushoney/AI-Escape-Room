"""Unit tests for the configuration and the structured GameState."""

from __future__ import annotations

import copy
import json

import pytest

from app.game_config import ConfigError, public_config, solution_strings, validate_config
from app.game_state import CRITICAL_FIELDS, GameState


def test_config_has_six_objects_three_puzzles_and_escape(config):
    assert set(config["objects"]) == {"desk", "bookshelf", "painting", "drawer", "console", "exit_door"}
    assert len(config["puzzles"]) == 3
    assert config["escape_condition"]["requires_puzzles"] == ["puzzle_1", "puzzle_2", "puzzle_3"]


def test_config_validation_rejects_undiscoverable_clue(config):
    broken = copy.deepcopy(config)
    broken["puzzles"]["puzzle_1"]["requires_clues"].append("clue_nobody_can_find")
    with pytest.raises(ConfigError):
        validate_config(broken)


def test_puzzle_solutions_follow_from_clues(config):
    """The answers must be derivable from the clue text, not arbitrary."""
    spines = {1923: "4", 1887: "2", 1951: "7", 1902: "9"}
    assert "".join(spines[y] for y in sorted(spines)) == config["puzzles"]["puzzle_1"]["solution"]
    cipher = {"moon": "5", "star": "8", "triangle": "3", "circle": "6"}
    order = config["puzzles"]["puzzle_2"]["solution"]
    assert "".join(cipher[s] for s in order) == config["puzzles"]["puzzle_3"]["solution"]


def test_public_config_has_no_solutions(config):
    text = json.dumps(public_config(config))
    for solution in solution_strings(config).values():
        assert solution not in text


def test_new_state_starts_locked(config):
    state = GameState.new(config)
    assert state.inventory == [] and state.solved_puzzles == []
    assert not state.door_open and not state.escaped
    assert set(state.unlocked_objects) == {"desk", "bookshelf"}
    assert state.available_objects == list(config["objects"])


def test_add_unique_is_idempotent(config):
    state = GameState.new(config)
    assert state.add_unique("inventory", "uv_lamp") is True
    assert state.add_unique("inventory", "uv_lamp") is False
    assert state.inventory == ["uv_lamp"]


def test_round_trip_serialisation(config):
    state = GameState.new(config)
    state.add_unique("inventory", "uv_lamp")
    state.record_action({"request": {"action": "take"}, "result": "item_collected"})
    restored = GameState.from_dict(json.loads(json.dumps(state.to_dict())))
    assert restored == state


def test_critical_snapshot_is_a_deep_copy(config):
    state = GameState.new(config)
    snap = state.critical_snapshot()
    state.inventory.append("uv_lamp")
    assert snap["inventory"] == []
    assert set(snap) == set(CRITICAL_FIELDS)


def test_public_summary_contains_names_not_ids_or_solutions(config):
    state = GameState.new(config)
    state.add_unique("inventory", "uv_lamp")
    summary = state.public_summary(config)
    assert summary["inventory"] == ["UV Lamp"]
    text = json.dumps(summary)
    for solution in solution_strings(config).values():
        assert solution not in text
