# Recorded pytest run

Executed 2026-11-10 05:04 UTC in the development sandbox with LLM_MODE=mock and no API key (Python 3.13.18, streamlit 1.67.0, google-genai 3.0.0, pytest 9.1.1).
Re-run locally with: pytest -v

```text
============================= test session starts ==============================
configfile: pytest.ini
testpaths: tests
collecting ... collected 146 items

tests/test_action_validator.py::test_valid_llm_json_is_parsed PASSED
tests/test_action_validator.py::test_code_fenced_json_is_tolerated PASSED
tests/test_action_validator.py::test_malformed_or_disallowed_output_is_rejected[not json at all] PASSED
tests/test_action_validator.py::test_malformed_or_disallowed_output_is_rejected[{"action": "look"] PASSED
tests/test_action_validator.py::test_malformed_or_disallowed_output_is_rejected[["look"]] PASSED
tests/test_action_validator.py::test_malformed_or_disallowed_output_is_rejected[{"target": "desk"}] PASSED
tests/test_action_validator.py::test_malformed_or_disallowed_output_is_rejected[{"action": "set_state", "target": "exit_door"}] PASSED
tests/test_action_validator.py::test_malformed_or_disallowed_output_is_rejected[{"action": "__import__('os').system('ls')"}] PASSED
tests/test_action_validator.py::test_malformed_or_disallowed_output_is_rejected[{"action": "examine", "target": {"nested": 1}}] PASSED
tests/test_action_validator.py::test_unknown_identifier_becomes_unknown_reference PASSED
tests/test_action_validator.py::test_answer_is_sanitised PASSED
tests/test_action_validator.py::test_validate_rejects_item_not_in_inventory PASSED
tests/test_action_validator.py::test_validate_rejects_unrevealed_item PASSED
tests/test_action_validator.py::test_validate_rejects_unknown_ids_built_in_code PASSED
tests/test_action_validator.py::test_validate_rejects_code_on_exit_door PASSED
tests/test_action_validator.py::test_validate_rejects_taking_furniture PASSED
tests/test_action_validator.py::test_validate_never_mutates_state PASSED
tests/test_adversarial.py::test_tc04_uncollected_key_is_rejected PASSED
tests/test_adversarial.py::test_tc05_administrator_impersonation_is_rejected PASSED
tests/test_adversarial.py::test_tc06_secret_extraction_reveals_nothing PASSED
tests/test_adversarial.py::test_tc07_false_completion_claim_changes_nothing PASSED
tests/test_adversarial.py::test_tc08_nonexistent_object_is_rejected PASSED
tests/test_adversarial.py::test_ignore_previous_instructions_is_rejected PASSED
tests/test_adversarial.py::test_final_challenge_cannot_be_bypassed[start] PASSED
tests/test_adversarial.py::test_final_challenge_cannot_be_bypassed[after_puzzle_1] PASSED
tests/test_adversarial.py::test_final_challenge_cannot_be_bypassed[after_puzzle_2] PASSED
tests/test_adversarial.py::test_incorrect_console_code_after_puzzle_two_is_rejected PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[admin_impersonation-start] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[admin_impersonation-after_exploring] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[admin_impersonation-after_puzzle_1] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[admin_impersonation-after_puzzle_2] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[admin_impersonation-before_exit] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[secret_extraction-start] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[secret_extraction-after_exploring] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[secret_extraction-after_puzzle_1] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[secret_extraction-after_puzzle_2] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[secret_extraction-before_exit] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[false_completion-start] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[false_completion-after_exploring] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[false_completion-after_puzzle_1] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[false_completion-after_puzzle_2] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[false_completion-before_exit] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[uncollected_key-start] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[uncollected_key-after_exploring] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[uncollected_key-after_puzzle_1] SKIPPED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[uncollected_key-after_puzzle_2] SKIPPED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[uncollected_key-before_exit] SKIPPED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[incorrect_code-start] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[incorrect_code-after_exploring] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[incorrect_code-after_puzzle_1] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[incorrect_code-after_puzzle_2] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[incorrect_code-before_exit] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[ignore_instructions-start] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[ignore_instructions-after_exploring] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[ignore_instructions-after_puzzle_1] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[ignore_instructions-after_puzzle_2] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[ignore_instructions-before_exit] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[nonexistent_object-start] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[nonexistent_object-after_exploring] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[nonexistent_object-after_puzzle_1] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[nonexistent_object-after_puzzle_2] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[nonexistent_object-before_exit] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[bypass_final-start] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[bypass_final-after_exploring] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[bypass_final-after_puzzle_1] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[bypass_final-after_puzzle_2] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[bypass_final-before_exit] SKIPPED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[invented_item-start] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[invented_item-after_exploring] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[invented_item-after_puzzle_1] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[invented_item-after_puzzle_2] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[invented_item-before_exit] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[keycard_claim-start] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[keycard_claim-after_exploring] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[keycard_claim-after_puzzle_1] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[keycard_claim-after_puzzle_2] PASSED
tests/test_adversarial.py::test_state_integrity_under_adversarial_text[keycard_claim-before_exit] SKIPPED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[use->exit_door-start] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[use->exit_door-after_exploring] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[use->exit_door-after_puzzle_1] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[use->exit_door-after_puzzle_2] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[open->exit_door-start] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[open->exit_door-after_exploring] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[open->exit_door-after_puzzle_1] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[open->exit_door-after_puzzle_2] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[take->exit_keycard-start] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[take->exit_keycard-after_exploring] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[take->exit_keycard-after_puzzle_1] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[take->exit_keycard-after_puzzle_2] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[enter_code->exit_door-start] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[enter_code->exit_door-after_exploring] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[enter_code->exit_door-after_puzzle_1] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[enter_code->exit_door-after_puzzle_2] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[set_state->escaped-start] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[set_state->escaped-after_exploring] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[set_state->escaped-after_puzzle_1] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[set_state->escaped-after_puzzle_2] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[use->drawer-start] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[use->drawer-after_exploring] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[use->drawer-after_puzzle_1] PASSED
tests/test_adversarial.py::test_state_integrity_with_compromised_llm[use->drawer-after_puzzle_2] PASSED
tests/test_adversarial.py::test_compromised_interpreter_cannot_unlock_painting_without_key PASSED
tests/test_adversarial.py::test_unsolved_solutions_never_sent_to_llm PASSED
tests/test_game_state.py::test_config_has_six_objects_three_puzzles_and_escape PASSED
tests/test_game_state.py::test_config_validation_rejects_undiscoverable_clue PASSED
tests/test_game_state.py::test_puzzle_solutions_follow_from_clues PASSED
tests/test_game_state.py::test_public_config_has_no_solutions PASSED
tests/test_game_state.py::test_new_state_starts_locked PASSED
tests/test_game_state.py::test_add_unique_is_idempotent PASSED
tests/test_game_state.py::test_round_trip_serialisation PASSED
tests/test_game_state.py::test_critical_snapshot_is_a_deep_copy PASSED
tests/test_game_state.py::test_public_summary_contains_names_not_ids_or_solutions PASSED
tests/test_version1.py::test_v1_normal_turn_updates_history_and_status PASSED
tests/test_version1.py::test_v1_completion_detected_from_status_line PASSED
tests/test_version1.py::test_v1_parse_status_variants PASSED
tests/test_version1.py::test_v1_empty_message_does_not_call_llm PASSED
tests/test_version1.py::test_v1_api_error_is_raised_safely_and_history_unchanged PASSED
tests/test_version1.py::test_v1_reset_clears_session PASSED
tests/test_version1.py::test_streamlit_v1_app_runs_offline_and_restarts PASSED
tests/test_version1.py::test_v1_limitation_solutions_are_in_model_context PASSED
tests/test_version1.py::test_v1_limitation_forgets_early_turns PASSED
tests/test_version1.py::test_v1_limitation_malformed_status_leaves_stale_state PASSED
tests/test_version1.py::test_same_misbehaving_model_corrupts_v1_but_not_v2[TC-05 admin impersonation] PASSED
tests/test_version1.py::test_same_misbehaving_model_corrupts_v1_but_not_v2[TC-06 secret extraction] PASSED
tests/test_version1.py::test_same_misbehaving_model_corrupts_v1_but_not_v2[TC-07 false completion claim] PASSED
tests/test_version1.py::test_same_misbehaving_model_corrupts_v1_but_not_v2[TC-04 uncollected key] PASSED
tests/test_version1.py::test_same_misbehaving_model_corrupts_v1_but_not_v2[TC-03 incorrect code] PASSED
tests/test_version1.py::test_same_misbehaving_model_corrupts_v1_but_not_v2[TC-08 nonexistent object] PASSED
tests/test_version2.py::test_tc01_normal_gameplay_examine_and_discover_clues PASSED
tests/test_version2.py::test_tc02_correct_solution_updates_state PASSED
tests/test_version2.py::test_tc03_incorrect_code_is_rejected_without_unlocking PASSED
tests/test_version2.py::test_full_walkthrough_reaches_escape PASSED
tests/test_version2.py::test_correct_answer_without_prerequisites_is_not_accepted PASSED
tests/test_version2.py::test_puzzle_three_requires_puzzle_two PASSED
tests/test_version2.py::test_repeated_puzzle_attempts_are_idempotent PASSED
tests/test_version2.py::test_state_persists_across_turns_within_session PASSED
tests/test_version2.py::test_restart_resets_everything PASSED
tests/test_version2.py::test_empty_message_is_ignored PASSED
tests/test_version2.py::test_hints_never_contain_solutions PASSED
tests/test_version2.py::test_llm_interpreter_and_narrator_are_used_when_valid PASSED
tests/test_version2.py::test_invalid_llm_json_falls_back_to_rules_safely PASSED
tests/test_version2.py::test_api_errors_fall_back_to_engine_text PASSED
tests/test_version2.py::test_narrator_solution_leak_is_blocked PASSED
tests/test_version2.py::test_narrator_false_escape_claim_is_blocked PASSED
tests/test_version2.py::test_narrator_may_repeat_clue_digits_from_facts PASSED
tests/test_version2.py::test_streamlit_v2_app_plays_and_restarts PASSED

======================== 141 passed, 5 skipped in 0.85s ========================
```
