"""Unit tests for schema/allowlist parsing and rule validation."""

from __future__ import annotations

import pytest

from app.action_validator import (
    ActionRequest,
    ActionRequestError,
    parse_action_request,
    validate_action,
)
from app.game_state import GameState


def test_valid_llm_json_is_parsed(config):
    req = parse_action_request(
        '{"action": "use", "target": "painting", "item": "brass_key", "answer": "none", "unknown_reference": "none"}',
        config,
    )
    assert (req.action, req.target, req.item, req.answer) == ("use", "painting", "brass_key", None)
    assert req.source == "llm"


def test_code_fenced_json_is_tolerated(config):
    req = parse_action_request('```json\n{"action": "look"}\n```', config)
    assert req.action == "look"


@pytest.mark.parametrize(
    "raw",
    [
        "not json at all",
        '{"action": "look"',                       # truncated
        '["look"]',                                 # wrong top-level type
        '{"target": "desk"}',                       # missing action
        '{"action": "set_state", "target": "exit_door"}',   # not allowlisted
        '{"action": "__import__(\'os\').system(\'ls\')"}',  # code injection attempt
        '{"action": "examine", "target": {"nested": 1}}',   # wrong field type
    ],
)
def test_tc10_malformed_or_disallowed_output_is_rejected(config, raw):
    with pytest.raises(ActionRequestError):
        parse_action_request(raw, config)


def test_unknown_identifier_becomes_unknown_reference(config):
    req = parse_action_request('{"action": "use", "item": "golden_key", "target": "exit_door"}', config)
    assert req.item is None and req.target == "exit_door"
    assert req.unknown_reference == "golden_key"


def test_answer_is_sanitised(config):
    req = parse_action_request('{"action": "enter_code", "target": "drawer", "answer": "29<script>47; DROP"}', config)
    assert "<" not in req.answer and ";" not in req.answer


def test_validate_rejects_item_not_in_inventory(config):
    state = GameState.new(config)
    result = validate_action(ActionRequest("use", target="painting", item="brass_key"), state, config)
    assert not result.ok and result.code == "item_not_in_inventory"


def test_validate_rejects_unrevealed_item(config):
    state = GameState.new(config)
    result = validate_action(ActionRequest("take", target="brass_key"), state, config)
    assert not result.ok and result.code == "not_visible"
    assert "brass" not in result.message.lower()  # does not spoil hidden items


def test_validate_rejects_unknown_ids_built_in_code(config):
    state = GameState.new(config)
    result = validate_action(ActionRequest("examine", target="secret_vault"), state, config)
    assert not result.ok and result.code == "nonexistent_object"


def test_validate_rejects_code_on_exit_door(config):
    state = GameState.new(config)
    result = validate_action(ActionRequest("enter_code", target="exit_door", answer="0000"), state, config)
    assert not result.ok and result.code == "wrong_mechanism"


def test_validate_rejects_taking_furniture(config):
    state = GameState.new(config)
    result = validate_action(ActionRequest("take", target="desk"), state, config)
    assert not result.ok and result.code == "not_collectable"


def test_validate_never_mutates_state(config):
    state = GameState.new(config)
    before = state.to_dict()
    for req in [
        ActionRequest("use", target="exit_door", item="exit_keycard"),
        ActionRequest("enter_code", target="console", answer="5836"),
        ActionRequest("take", target="exit_keycard"),
    ]:
        validate_action(req, state, config)
    assert state.to_dict() == before
