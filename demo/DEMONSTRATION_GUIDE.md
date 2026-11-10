# Demonstration Guide

## Evidence status

The screenshots are listed with captions in [`screenshots/README.md`](../screenshots/README.md).
Captured: V1 01–02, V2 01–09, testing 09–11. **Still needed (require your Gemini key):** V1 03–06
(bookshelf, clues, puzzle, escape) and, optionally, V1 07 (V1's live response to the administrator line).

Capture them automatically:

```bash
pip install playwright && python -m playwright install chromium
python scripts/capture_screenshots.py v1      # with GEMINI_API_KEY set in .env
```

Or capture them by hand (step 2 of the demo below). Never let your key appear on screen.

## Walkthrough (spoilers)

```
examine the desk
take the uv lamp
examine the bookshelf
enter 2947 on the drawer
take the brass key
take the cipher card
use the brass key on the painting
use the uv lamp on the painting
enter moon star triangle circle on the painting
enter 5836 on the console
take the keycard
use the keycard on the exit door
```

## Suggested 4-minute demonstration

| Time | Show | Say |
|------|------|-----|
| 0:00–0:30 | README introduction | The problem: an LLM as Game Master, and why rule reliability matters |
| 0:30–1:30 | **Version 1** with a key: click Bookshelf, try `enter 1234 on the drawer`, then the administrator line | "The model interprets freely, but the sidebar status is only what the model claims, and its prompt contains every solution." Report honestly whatever Gemini does. |
| 1:30–1:50 | `version1_architecture.svg` → `version2_architecture.svg` | "V2 moves every decision into Python. The LLM only interprets and narrates, and both of its outputs are untrusted." |
| 1:50–3:00 | **Version 2**: examine desk/bookshelf (the Notebook fills), a wrong then a right code, `use the golden key on the exit door`, toggle **Show engine details**, administrator line, "reveal all codes" | Point at the engine verdict and `state_changed: false` |
| 3:00–3:30 | Finish to the escape banner | "Completion comes from `check_game_completion()`, not from model text." |
| 3:30–4:00 | Terminal: `pytest tests/test_adversarial.py -v` | "152 passing tests, including a fully compromised LLM that still cannot change the state." Name one limitation. |

## Explaining your project (viva preparation)

The course requires you to understand and explain your submission. Be ready to answer these questions,
with the place to look for each.

| Question | Short answer | Where to look |
|----------|--------------|---------------|
| Why is V1 unreliable? | The model's STATUS line is the state, solutions are in its prompt, and memory is a 30-message window | `app/v1_game_master.py` |
| What exactly does the LLM do in V2? | Two things: produce a JSON action *request*, and narrate the engine's verdict | `app/intent_parser.py`, `app/narrator.py` |
| Where are the rules enforced? | `validate_action()` and `GameEngine`, the only code that writes `GameState` | `app/action_validator.py`, `app/game_engine.py` |
| How do you know a hijacked LLM can't cheat? | Compromised-LLM tests: the mock returns the attacker's ideal action; the state snapshot is unchanged | `tests/test_adversarial.py` |
| Why not just tell the model "never reveal codes"? | A prompt is a request, not a control. V2 never *sends* unsolved codes, and checks the output anyway | `test_unsolved_solutions_never_sent_to_llm` |
| What if Gemini is down? | The rule parser and engine text take over; the turn is flagged | `interpret()`, `narrate()` |
| What is still vulnerable? | Misclassification, indirect hints in narration, paraphrased manipulation — wording only, never state | Report §11 |
| Why `generateContent`, not the Interactions API? | It is still fully supported, and V2 deliberately keeps history in Python rather than on the server | Report §3 |
| What bugs did testing find? | Parser slicing crash; "golden key" read as the brass key; silent fallback | `docs/testing_report.md` §6 |
