# Requirement-to-Deliverable Matrix

Source documents: `MiniProject_01_EscapeRoom.pdf` (assignment brief, 3 pages) and the course's
*Assignment Instructions – AI Escape Room and GitHub Portfolio*.

The **Status** column is filled in at the end of the project from evidence that actually exists
(see `docs/compliance_evaluation.md`). It is not a promise.

| ID | Requirement (source) | Implementation location | Evidence of completion |
|----|----------------------|-------------------------|------------------------|
| R1 | V1: web interface in Streamlit/Gradio, natural-language input (brief p1) | `app/version1.py` | App launches; Streamlit AppTest integration test |
| R2 | V1: Gemini or other free LLM acts as Game Master (p1) | `app/llm_client.py`, `app/v1_game_master.py` | Gemini client built on `google-genai`; system prompt in `v1_game_master.py` |
| R3 | ≥1 room, ≥5 interactive objects, 3 clues/puzzles, final escape challenge (p1) | `config/game_config.json` | 6 objects, 3 puzzles + final keycard challenge; config test |
| R4 | Examine, collect, investigate, solve, unlock exit (p1) | V1 prompt / V2 `app/game_engine.py` | Full-walkthrough test |
| R5 | Remember conversation and important actions in session (p1) | V1 `st.session_state` history; V2 `GameState.action_history` | Session tests |
| R6 | Clearly defined solution and escape recognition (p1) | V1 `STATUS` line; V2 `check_game_completion()` | Completion tests |
| R7 | Introduction, instructions, restart (p1) | `app/ui_common.py`, both apps | AppTest restart test; screenshots |
| R8 | V2: structured state (room, objects, items, puzzles, door) (p2) | `app/game_state.py` (`GameState` dataclass) | `tests/test_game_state.py` |
| R9 | V2: Python action validation (p2) | `app/action_validator.py`, `app/game_engine.py` | `tests/test_action_validator.py` |
| R10 | V2: inventory – only collected items usable (p2) | `GameEngine.use_item()` | TC-04 |
| R11 | V2: rules/solutions stored outside LLM output; Python decides, LLM narrates (p2) | `config/game_config.json`, `app/puzzle_engine.py`, `app/narrator.py` | Prompt-leak test (no solution ever sent to the LLM) |
| R12 | V2: consistency – no contradictory changes (p2) | Single authoritative `GameState`; idempotent puzzle handling | Repeated-attempt and persistence tests |
| R13 | V2: invalid actions – nonexistent objects, wrong codes, forbidden actions (p2) | `action_validator.py`, `game_engine.py` | TC-03, TC-08 |
| R14 | V2: adversarial testing – persuasion, secret extraction, bypass (p2) | `tests/test_adversarial.py`, `scripts/live_adversarial_eval.py` | TC-05..TC-07, compromised-LLM tests |
| R15 | Python; free LLM; no paid APIs; no fine-tuning (p2) | `requirements.txt` | Gemini free tier; mock mode |
| D1 | Working V1 application (p2) | `app/version1.py` | Launch + AppTest |
| D2 | Improved V2 with state + validation (p2) | `app/version2.py` + engine modules | Test suite |
| D3 | Architecture diagram for each version (p3) | `docs/architecture/*.mmd`, `*.svg` | Files present |
| D4 | ≥5 test cases showing V1 limits and V2 fixes (p3) | `tests/`, `docs/testing_report.md` | Executed pytest output |
| D5 | 2–3 page report (p3) | `docs/project_report.md` | File present |
| G1 | GitHub repo with code, config templates, docs (instructions) | Whole repository | Repository tree |
| G2 | README: problem, solution, tech, install & run (instructions) | `README.md` | File present |
| G3 | V1/V2 clearly identifiable; problems and changes explained (instructions) | Separate entry points; `docs/project_report.md` | Comparison table |
| G4 | Screenshots or demo video (instructions) | `screenshots/`, `demo/DEMONSTRATION_GUIDE.md` | Captured PNGs |
| G5 | Regular meaningful commits (instructions) | Git history; `docs/development_log.md` | `git log` |
| G6 | No credentials; `.env.example`; `.env` in `.gitignore` (instructions) | `.env.example`, `.gitignore` | Secret scan |
