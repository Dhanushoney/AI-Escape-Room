# Final Evaluation and Zero-Omission Audit

**Basis of evaluation.** No official marking rubric was supplied. This evaluation is against the assignment
brief (`MiniProject_01_EscapeRoom.pdf`, all three pages), the course's *GitHub Setup and Submission*
instructions, and the two project prompts (Ultimate Master Prompt and Zero-Omission instruction). It is
not a grade prediction.

## 1. Coverage summary

Each requirement has a unique ID and full traceability in
[`REQUIREMENT_TRACEABILITY_MATRIX.md`](REQUIREMENT_TRACEABILITY_MATRIX.md) and
[`FINAL_REQUIREMENT_COMPLIANCE_MATRIX.xlsx`](../FINAL_REQUIREMENT_COMPLIANCE_MATRIX.xlsx). Both are generated
by `scripts/build_compliance.py`, which refuses to mark a row COMPLETE unless its evidence file exists.

| Status | Count |
|--------|-------|
| COMPLETE | 236 |
| PARTIALLY COMPLETE | 4 |
| NOT COMPLETE | 0 |
| REQUIRES USER ACTION | 15 |
| NOT APPLICABLE | 1 (no rubric supplied) |
| **Total** | **256** |

**The project is therefore not 100% complete.** The project is published at https://github.com/Dhanushoney/AI-Escape-Room (11 Nov 2026). What remains
needs a Gemini API key (live Version 1 evidence) or a personal action (submitting the link, pinning the
repository, preparing to explain the code).

## 2. Three independent reviews

### Review 1 – Source compliance
Each sentence of the brief was given an ID: V1-01–V1-25 (Version 1, p.1), V2-01–V2-30 (Version 2, p.2),
T-01–T-06 (technical, p.2) and RP-01–RP-05, A-01–A-03, TS-01 (deliverables, p.3). Every GitHub instruction
became G-01–G-28, and every prompt section its own group (UI, TS, CMP, RP, S, RM, SEC, GH, Z, DOC, F, ZO).
Findings:

- All five brief deliverables exist: V1 app, V2 app, two diagrams, 14 documented test cases (≥5), and a 3-page report.
- All five "Example Challenges" on p.2 are explicit tests (TC-04, TC-03, TC-08, TC-06, TC-07) and pass.
- **Gap:** Version 1's *live* LLM behaviour (V1-03, V1-04, V1-10–V1-14, V1-22, V1-23, V1-25) is implemented
  but unverified, because no API key was available. These rows are marked PARTIALLY COMPLETE or REQUIRES USER
  ACTION, not COMPLETE.
- Design deviation, disclosed: the brief's example door uses a 4-digit code. Here the 4-digit code is on the
  security console, which releases a keycard for the door. The brief explicitly allows your own design.

### Review 2 – Technical verification
- `pytest -v -rs` → **157 collected, 152 passed, 5 skipped (documented), 0 failed** ([output](test_results.md)).
- Both apps launched headless (`/_stcore/health` → `ok`) and were driven by Streamlit AppTest and by a real
  browser (`scripts/capture_screenshots.py`).
- Full V2 game played to the escape banner in the browser; phone width (390 px) had 0 px horizontal overflow.
- The Gemini client reached the real endpoint and handled the dummy-key HTTP 400 gracefully.
- The XLSX recalculated in LibreOffice: 133 formulas, 0 errors.
- Secret scan of the working tree and the full Git history: 0 hits; no `.env` present.
- GitHub Actions run #1 on the published repository: **success** (Python 3.11 and 3.12).
- Three application defects were found and fixed during verification (testing report §6).

### Review 3 – Submission verification
- Report: DOCX and PDF; 3-page body (title to references) of about 1,320 words with tables; all 14 required
  sections; 8 references to official documentation, each URL resolved during development; figures in an appendix.
- README: all required sections, with the real username and repository URL filled in; commands
  re-run from a fresh copy (see §4).
- Diagrams: Mermaid source, SVG and PNG for each version; checked visually for overlaps.
- Screenshots: 14 genuine captures with captions (`screenshots/README.md`). 4 Version 1 gameplay captures are
  missing and clearly marked.
- GitHub: **published and verified** at https://github.com/Dhanushoney/AI-Escape-Room. The `gh` device sign-in was blocked by the build
  environment's proxy, so the push went through the Claude GitHub App, which the owner installed for this one
  repository only. Remote `main` was checked to equal the local HEAD, and the README renders on GitHub.
- ZIP: see §4.

## 3. Critical evaluation

**1. What was implemented successfully.** A working V2 with structured state, Python validation,
inventory and dependency control, completion validation, structured LLM I/O, output sanitisation, graceful
API failure handling and adversarial resistance. A working V1 interface with a genuine Gemini integration
path. A test suite, diagrams, report, README and supporting guides.

**2. Supporting evidence.** The recorded pytest run; state-integrity (50 cases) and compromised-LLM
(24 cases) matrices; the same-bad-model comparison (7 cases); prompt-recording proof that unsolved answers
never reach the model; 14 genuine screenshots; the fresh-copy install test.

**3. Remaining limitations.** No live Gemini evidence; the V1 comparison uses simulated replies. The
narration guard does not catch indirect hints. The manipulation detector is keyword-based. The commit
history is genuine but covers two days of sessions; the earlier commits carry a placeholder author name.

**4. What you must do before submission.**
1. Add your key to `.env`, play Version 1, and run `python scripts/capture_screenshots.py v1` and
   `python scripts/live_adversarial_eval.py`. Commit the screenshots and `docs/live_eval_results.md`. Update
   the V1 rows in `scripts/build_compliance.py` to match what you observed, then re-run it.
2. Fill in the report's title block (`<Student Name>`, `<Student ID>`, `<Course>`, `<repository URL>` → https://github.com/Dhanushoney/AI-Escape-Room),
   then re-export the PDF.
3. Submit the repository URL and pin the repository on your profile.
4. Study the "Explaining your project" table in `demo/DEMONSTRATION_GUIDE.md`.

**5. Has every brief requirement been addressed?** Every requirement has been *addressed*: implemented,
documented and traced. Not every requirement is *fully evidenced*. The Version 1 live-LLM requirements and
a few personal steps need your key or your own action. They are marked accordingly, not as
complete.

## 4. ZIP package verification

`AI_Escape_Room_COMPLETE_SUBMISSION.zip` (about 24 MB) contains `START_HERE.md`, `assignment/` (the brief and
the GitHub instructions) and `AI-Escape-Room/`, a clean clone of this repository with its full commit
history.

Verification run (10 Nov 2026). The ZIP was extracted into a separate temporary directory, then:

| Check | Result |
|-------|--------|
| 57 essential files (sources, config, tests, report DOCX/PDF, diagrams, docs, matrices, scripts, CI) present | ✅ 0 missing |
| Screenshots present | ✅ 14 PNG |
| `__pycache__`, `*.pyc`, `.pytest_cache`, `venv`, `.env` | ✅ none |
| Google API key and GitHub token patterns (regex scan) | ✅ none |
| Git history in the package | ✅ commits present, clean working tree |
| Fresh venv + `pip install -r requirements.txt` | ✅ streamlit 1.67.0, google-genai 3.0.0 |
| `pytest -q` in the extracted copy | ✅ 152 passed, 5 skipped |
| `streamlit run app/version1.py` / `app/version2.py` | ✅ both `/_stcore/health` → ok |

This file and the matrices were then regenerated with these results, and the ZIP was rebuilt and
re-checked (file list, secret scan, pytest).
