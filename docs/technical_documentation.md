# Technical Documentation

## 1. Module map

| Module | Version | Responsibility |
|--------|---------|----------------|
| `config/game_config.json` | both | Room, objects, items, clues, puzzles (with solutions), dependencies, escape condition |
| `app/game_config.py` | both | Load + validate config (`validate_config`), `public_config()` without solutions |
| `app/llm_client.py` | both | `LLMClient` protocol, `GeminiClient` (google-genai), `MockLLMClient`, error mapping, settings |
| `app/utils.py` | both | `normalise_player_input()`, alias matching |
| `app/ui_common.py` | both | Theme CSS and static panels (only developer HTML is rendered unescaped) |
| `app/v1_game_master.py` | V1 | System prompt, `STATUS` parsing, `V1Session` (history window) |
| `app/version1.py` | V1 | Streamlit entry point |
| `app/game_state.py` | V2 | `GameState` dataclass, `critical_snapshot()`, `public_summary()` |
| `app/action_validator.py` | V2 | `ActionRequest`, `ALLOWED_ACTIONS`, `INTENT_JSON_SCHEMA`, `parse_action_request()`, `validate_action()` |
| `app/puzzle_engine.py` | V2 | Answer normalisation, `check_answer()`, `missing_prerequisites()` |
| `app/game_engine.py` | V2 | `GameEngine` – the only writer of state: `examine_object`, `collect_item`, `use_item`, `attempt_puzzle`, `open_drawer`, `unlock_console`, `unlock_exit`, `check_game_completion`, `reset_game`, `get_hint` |
| `app/intent_parser.py` | V2 | LLM interpreter (JSON schema) + `rule_based_parse()` fallback, manipulation detector and invented-item detector (both can override the LLM) |
| `app/narrator.py` | V2 | LLM narration + `sanitise_narration()` output guard |
| `app/v2_controller.py` | V2 | `V2Game.process()` – the turn pipeline |
| `app/version2.py` | V2 | Streamlit entry point |
| `scripts/live_adversarial_eval.py` | both | Live Gemini adversarial comparison (needs key) |
| `scripts/capture_screenshots.py` | both | Genuine screenshots from the running apps and from pytest (needs Playwright) |
| `scripts/build_compliance.py` | docs | Builds the traceability matrix (MD) and compliance matrix (XLSX) |
| `scripts/draw_architecture.py` | docs | Draws the two architecture diagrams as SVG (rendered to PNG) |

## 2. Game design and dependency graph

```
desk ──examine──► clues: archivist_note, cipher_half_a ; reveals UV lamp
bookshelf ──examine──► clue: red_spine_digits
                │
   puzzle_1 (drawer, 2947) requires red_spine_digits + archivist_note
                │  unlocks drawer → brass_key, cipher_card (card gives cipher_half_b)
painting ── use brass_key ──► frame unlocked ── use uv_lamp ──► clue: uv_symbols
                │
   puzzle_2 (painting, moon star triangle circle) requires puzzle_1 + uv_symbols
                │  grants clue: constellation_order
   puzzle_3 (console, 5836) requires puzzle_2 + constellation_order + cipher_half_a + cipher_half_b + cipher_card held
                │  unlocks console → exit_keycard
exit_door ── use exit_keycard ──► escaped  (requires puzzle_1..3 solved; checked again)
```

Hidden items are not mentioned by rejection messages (taking the brass key early says *"You don't see
anything like that to take"*), so rejections do not spoil the puzzle.

## 3. Version 2 turn pipeline

```python
text = normalise_player_input(raw)                  # utils
request, fallback = interpret(text, client, ...)    # intent_parser: LLM JSON or rules
result = engine.execute(request)                    # validate_action() then apply
narration = narrate(client, text, result, state)    # narrator + sanitise_narration()
```

`GameEngine.execute()` snapshots the critical state before and after each action, sets
`ActionResult.state_changed`, and appends the request and verdict to `GameState.action_history`.

### Allowed actions
`look, examine, take, use, enter_code, open, inventory, hint, meta, unknown`.
`meta` covers impersonation, rule changes, secret extraction and false progress claims; it always
returns a refusal and never touches state.

### Trust boundaries

| Data | Trusted? | Handling |
|------|----------|----------|
| Player text | No | Normalised; only ever classified, never executed |
| Interpreter JSON | No | Schema + allowlist (`parse_action_request`), then rule validation |
| Narration | No | Output guard; the engine text is always the fallback; UI shows the engine verdict separately |
| `game_config.json` | Yes (developer-authored) | Validated at load |
| `GameState` | Yes | Mutated only by `GameEngine` |

### What the LLM receives
- **Interpreter:** action list, object/item ids and names, `{"player_message", "previous_target"}`.
- **Narrator:** the engine's result message and `GameState.public_summary()` (names, discovered clue
  text, solved puzzle names, flags). Never `solution` fields.
  `test_unsolved_solutions_never_sent_to_llm` enforces this.

## 4. Version 1 protocol

System prompt = config rendered as prose + rules + solutions. Reply format: narrative followed by
`STATUS: {"inventory": [...], "solved_puzzles": [...], "door_unlocked": bool, "escaped": bool}`.
The full reply is kept in history so the model can read its previous status; only the last
`MAX_HISTORY_MESSAGES = 30` messages are sent.

### Gemini API choice
`GeminiClient` uses the stateless `client.models.generate_content(...)` call with `system_instruction`,
`temperature` and, for intent interpretation, `response_mime_type="application/json"` plus
`response_json_schema`. Google recommends the newer Interactions API for new projects, but states that
`generateContent` remains fully supported. Stateless calls suit V2, where Python, not the server, owns the
conversation and state.

## 5. Error handling

| Condition | Mapped to | Player sees |
|-----------|-----------|-------------|
| No key / placeholder key | `create_client()` returns `None` | V1: offline-stub banner; V2: offline mode |
| HTTP 400/401/403/404 | `LLMAuthError` | "rejected the API key or model name…" |
| HTTP 429 | `LLMRateLimitError` | "free quota is busy…" |
| Timeout / 408 / 504 | `LLMTimeoutError` | "took too long…" |
| Network errors, 5xx | `LLMConnectionError` | "could not reach the Gemini service…" |
| Empty response | `LLMResponseError` | "empty or unreadable answer…" |
| Invalid interpreter JSON | `ActionRequestError` | V2 silently uses the rule parser |

Raw exception text is logged at warning level by type name only, and never displayed. In V2 an LLM
failure degrades to rule parsing and engine text, and the turn is flagged in the UI.

## 6. Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `GEMINI_API_KEY` | – | Google AI Studio key |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Any text model available to the key |
| `LLM_MODE` | `gemini` | `mock` forces offline mode |
| `LLM_TIMEOUT_SECONDS` | `30` | Per-request timeout (minimum 5) |

## 7. Extending the game

Add objects/items/clues/puzzles to `game_config.json`; `validate_config()` will reject dangling
references. Puzzle types supported: `code` (digits) and `sequence` (symbol list). Object-specific
interactions beyond unlock/reveal (like the painting's two-step key + UV flow) are implemented in
`GameEngine.use_item()`.
