# Development Log

This log records how the project was built. The Git history in this repository is genuine: each
commit was made when the work it describes was completed, with real timestamps. All commits were
made on **10 November 2026 in a single development session** (with an AI coding assistant, as the
course permits). No dates were back-filled.

> **Before submitting:** set your own Git identity (`git config user.name/user.email`) for future
> commits, and keep committing as you extend the project (live evaluation results, your own Version 1
> screenshots, documentation changes). The history should keep growing with your own work.

## Milestones

| # | Commit message | What changed and why |
|---|----------------|----------------------|
| 1 | Initial project structure, licence, env template and requirement matrix | Folder layout, `.gitignore` (excludes `.env`), `.env.example`, requirement-to-deliverable matrix from the brief |
| 2 | Define The Last Archive game configuration and Gemini LLM client | Game designed in JSON with dependency validation; Gemini wrapper verified against the current `google-genai` SDK (`Client`, `models.generate_content`, `GenerateContentConfig`) and the Sept 2026 model lineup |
| 3 | Add Version 1: LLM Game Master with Streamlit interface and session history | System prompt built from config, STATUS-line protocol, 30-message history window, dark-theme UI, offline stub when no key |
| 4 | Version 2: structured authoritative GameState dataclass | Single source of truth with idempotent updates and integrity snapshots |
| 5 | Version 2: allowlisted action requests and Python rule validation | JSON schema for the interpreter, action/id allowlists, `validate_action()` |
| 6 | Version 2: game engine with inventory checks and puzzle dependencies | `GameEngine` as the only state writer; prerequisites enforced even for correct guesses |
| 7 | Version 2: LLM intent interpreter with rule fallback, guarded narrator and turn pipeline | Interpreter/narrator separation, manipulation detector, output sanitiser |
| 8 | Version 2: Streamlit interface with engine verdicts, notebook and lock indicators | UI renders state from Python, not from model text |
| 9 | UI: fix hero spacing and title size | Found while reviewing the first screenshot |
| 10 | Add pytest suite: unit, integration, adversarial and state-integrity tests | 146 cases including compromised-LLM and prompt-leak tests |
| 11 | Add GitHub Actions workflow and live Gemini adversarial evaluation script | CI without a key; script for live evidence |
| 12 | Version 2 UI: flag turns where Gemini was unavailable | Found while testing the real Gemini client with a dummy key: V2 degraded silently |
| 13 | Add genuine application screenshots | Captured with headless Chrome from the running apps |
| 14 | Add architecture diagrams | Mermaid sources rendered to SVG/PNG with mermaid-cli |
| 15 | Documentation | README, reports, guides |

## Problems encountered and decisions

1. **Which Gemini model?** Older tutorials still use the deprecated `google-generativeai` package and
   1.5/2.0 models. The current SDK is `google-genai`; the release notes (checked 10 Nov 2026) list
   `gemini-3.8-flash` as GA since 2 Sept 2026. The model is configurable because the lineup changes.
2. **V1 needs the solutions in its prompt.** Without them, the model cannot referee. This is the root
   cause of V1's secret-exposure weakness and the strongest argument for V2.
3. **V1 state display.** Asking the model for a machine-readable STATUS line lets the UI show
   progress, but it also shows precisely that the state is whatever the model says.
4. **Rule-parser crash (real defect).** During the first V2 walkthrough, an off-by-one in prefix
   slicing produced ids like `"esk"` and crashed the engine. Fixed, and the validator now re-checks
   ids so a bad parser cannot crash or bypass the engine.
5. **Correct guesses before clues.** Decided that a correct answer is refused until prerequisites are
   met, and the refusal message does not reveal whether the guess was right. Otherwise a leaked or
   guessed code would skip the puzzle chain.
6. **Spoiler-free rejections.** "You don't see a brass key here" would reveal a hidden item; replaced
   with a generic message.
7. **Silent degradation.** With a bad key, V2 kept working on rules but the player could not tell.
   Added a per-turn notice.
8. **Diagram layout.** The player→…→player cycle made Mermaid place the player mid-diagram; split
   into input and output nodes.

## Not completed in this session

- Live Gemini gameplay and the live adversarial evaluation (no API key in the sandbox).
- Version 1 screenshots of real LLM gameplay (require a key; see `demo/DEMONSTRATION_GUIDE.md`).
