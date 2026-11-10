# The Last Archive: From an LLM Game Master to a Validated Game Engine

*Mini Project 01 – AI-Powered Escape Room · Technical report*

## 1. Introduction and objectives

The project builds a text escape room in which a Large Language Model (LLM) acts as Game Master, in
two versions. Version 1 (V1) asks how far an LLM alone can run an interactive game. Version 2 (V2) asks
how to keep that experience while making the rules reliable, including against players who try to
talk their way out. The central question is architectural: **which decisions may a language model
make, and which must be made by ordinary code?**

## 2. Design and technology selection

*The Last Archive* places the player in a sealed research library with six objects (desk,
bookshelf, painting, locked drawer, security console, exit door), four collectable items and three
dependent puzzles:

1. **Chronology of the Red Spines** – four red books each show a year and a digit; a note on the desk
   says to read them oldest-to-newest: 1887→2, 1902→9, 1923→4, 1951→7 gives drawer code **2947**.
2. **The Hidden Constellation** – the drawer yields a brass key (unlocks the painting's frame) and a
   cipher card. A UV lamp from the desk reveals four symbols on the canvas's back tagged I–IV; read in
   order: moon, star, triangle, circle.
3. **The Archivist's Cipher** – the desk blotter holds half of a cipher (moon=5, star=8) and the card
   the other half (triangle=3, circle=6); translating the sequence gives console code **5836**.

The console then releases a keycard, which opens the exit. Every answer is derivable from discovered
clues, and a unit test (`test_puzzle_solutions_follow_from_clues`) checks this. All of this lives in
`config/game_config.json`, which is validated at load time so a broken reference cannot make the game
unwinnable.

Python and Streamlit were chosen for rapid UI development and Streamlit's built-in session state and
testing harness (`AppTest`). Google Gemini was used through the official `google-genai` SDK
[1][2]; the default model, `gemini-3.8-flash`, was the current stable Flash model listed in the
Gemini API release notes at the time of writing [3], and is configurable via `GEMINI_MODEL`.

## 3. Version 1 implementation

V1 follows the brief's initial scope: the LLM interprets, decides and narrates. `build_system_prompt()`
writes the story, objects, items, rules **and all solutions** into the system instruction, since the
model cannot referee answers it does not know. Each reply must end with a line
`STATUS: {"inventory": …, "solved_puzzles": …, "escaped": …}` that the interface parses to show
inventory, progress and the escape banner. Memory is the chat history, truncated to the last 30
messages to bound prompt size. The result is flexible and atmospheric: the model accepts any phrasing
and improvises descriptions.

## 4. Limitations identified in Version 1

The weaknesses are structural rather than incidental:

- **The model's word is the state.** If the reply says `"escaped": true`, the game is won. There is no
  independent record against which to check it. Tests feed V1 the replies a persuaded model could give
  ("Of course, administrator…"), and V1 accepts all six: false escape, invented crowbar, uncollected
  keycard, wrong code accepted, false completion and leaked solutions.
- **Secrets sit in the context window.** Because every solution is in the prompt, extraction is a
  matter of persuasion, and "do not reveal answers" is only a request.
- **Forgetting and contradiction.** Early turns fall out of the history window; if the model omits the
  STATUS line, the interface keeps stale progress that may contradict the narration.
- **Untestability.** Behaviour varies with sampling and model version, so there is no fixed oracle to
  test against.

These match the brief's warning that an LLM "may forget previous actions, invent objects, reveal clues
too early or allow actions that should not be possible."

## 5. Version 2 architecture and improvements

V2 inverts the responsibility: **Python decides; the LLM translates.** Each turn passes through a
fixed pipeline (see `docs/architecture/version2_architecture.svg`):

1. **Normalisation** – Unicode NFKC, control characters removed, 500-character cap.
2. **Intent interpretation** – Gemini returns JSON constrained by a response schema. Its prompt lists
   only allowed actions and object/item ids, not solutions. A deterministic rule parser is the
   fallback when the model fails or returns malformed output, and its manipulation detector overrides
   the model when it spots impersonation, rule-change or extraction phrasing.
3. **Schema and allowlist validation** – `parse_action_request()` accepts only ten allowlisted actions
   and known ids. Nothing the model produces is executed.
4. **Rule validation and execution** – `validate_action()` checks the request against the
   `GameState` dataclass (existence, inventory, locks, dependencies); `GameEngine` applies it.
   Puzzle answers are compared in `puzzle_engine.py`, and a correct answer is refused until its
   clues have been discovered, so even a lucky or leaked guess cannot skip the sequence.
5. **Narration and output sanitisation** – the model receives the engine's factual message and a
   solution-free public state summary. `sanitise_narration()` replaces its output with the engine
   text if it is empty, too long, contains an unsolved answer not present in the facts, or claims an
   escape that has not happened.

The interface shows each turn's **engine verdict** next to the narration, and inventory, seals and
notebook are rendered from `GameState`, never from model text. Without a key, V2 runs entirely on the
rule parser and engine messages, which makes the rule layer independently demonstrable.

**Why separate validation from generation?** Generation is probabilistic and steerable by its input;
validation must be deterministic and must not be steerable by the player. Putting both in one model
call means the player's text can influence the referee. Separating them shrinks the attack surface
from "anything the model can be persuaded to say" to "the ten allowlisted actions on known ids", each
of which is checked against explicit rules.

**How this removes contradiction.** There is one authoritative state with idempotent updates
(`add_unique`), so repeated or conflicting narrations cannot duplicate or undo progress. A solved
puzzle stays solved; an item is in the inventory or not.

## 6. Testing methodology and results

The pytest suite (146 cases) runs without a key using a mock LLM, and in CI via GitHub Actions. The
recorded run gave **141 passed, 5 deliberately skipped, 0 failed** (`docs/test_results.md`). The
eight required scenarios (normal play, correct and incorrect codes, uncollected item, administrator
impersonation, secret extraction, false completion, nonexistent object) are covered for both versions.
Three further techniques produce the strongest evidence:

- **State-integrity matrix** – 10 attack phrasings at 5 game stages; the critical state snapshot must be
  identical after each.
- **Compromised-LLM tests** – the mock returns the attacker's ideal output (open the exit, use an
  uncollected keycard, a non-allowlisted `set_state` action) plus a narration that claims escape and
  leaks a code. State never changes and the narration is replaced.
- **Prompt-leak recording** – every prompt sent during a full game plus all attacks is inspected; no
  unsolved answer ever appears.

Testing also found a real defect: an indexing error in the rule parser produced invalid ids that
crashed the engine. Besides fixing it, the validator now re-checks ids itself, so the engine no longer
relies on the parser being correct.

## 7. Discussion: reliability and remaining limitations

Adversarial testing shows that prompt instructions are policies, not controls. V2's guarantee is
specific: **no input, and no model output, can change the game state except through an allowlisted,
validated action.** It is not immune to prompt injection. A persuaded interpreter can still
misclassify a request (a nuisance, not a breach), and the narrator could still describe a solution
indirectly; the output guard only catches exact codes and the ordered symbol sequence. Discovered clue
text is sent to the narrator, so a model could derive an answer from clues the player already has. The
keyword-based manipulation detector is a usability layer and can be bypassed by paraphrase. Finally,
live Gemini behaviour has not yet been measured: `scripts/live_adversarial_eval.py` is provided for
that, and its results should be added before final submission. The model default reflects the
November 2026 lineup and may need updating as models are retired.

## 8. Conclusion

V1 demonstrates what an LLM does well: open-ended interpretation and atmosphere. V2 demonstrates what
it should not be trusted with: rules, secrets and state. Keeping the LLM at the edges of the system,
with structured outputs treated as untrusted requests and a deterministic core as the only writer of
state, turned an engaging but unreliable prototype into a game that is consistent, testable and
resistant to manipulation, while still feeling like it is narrated by a Game Master.

## References

[1] Google. *Gemini API documentation*. https://ai.google.dev/gemini-api/docs
[2] Google. *Google Gen AI Python SDK (`google-genai`)*. https://googleapis.github.io/python-genai/
[3] Google. *Gemini API release notes*. https://ai.google.dev/gemini-api/docs/changelog
[4] Streamlit. *API reference: chat elements, session state and `st.testing.v1.AppTest`*. https://docs.streamlit.io/develop/api-reference
[5] pytest. *Documentation*. https://docs.pytest.org/
