# Publishing to GitHub

The repository is complete and committed locally. **It has not been published.** In the build environment
`gh auth status` reported an invalid token, so no push was attempted. Follow these steps on your own
computer. You never need to paste a password or token anywhere: the GitHub CLI signs you in through your
browser.

## 1. One-time setup

1. Create a GitHub account with a professional username at https://github.com/ if you do not have one.
2. Install Git (https://git-scm.com/downloads) and the GitHub CLI (https://cli.github.com/).
3. Sign in through the browser:
   ```bash
   gh auth login --hostname github.com --git-protocol https --web
   gh auth status          # should show: Logged in to github.com account <you>
   ```
   This grants the CLI's default scopes for your own account (`repo`, `read:org`, `gist`). No personal
   access token is stored in the project.

## 2. Set your identity for future commits

The existing commits were made in the build session under a placeholder identity. Commits from now on
should be yours:

```bash
cd AI-Escape-Room
git config user.name  "Your Name"
git config user.email "your-github-email@example.com"   # or your GitHub noreply address
```

Before publishing, replace the placeholders `<your-github-username>`, `<Your Name>`, `<Student Name>` and
`<repository URL>` in `README.md`, `LICENSE` and the report (`docs/AI_Escape_Room_Technical_Report.docx`,
then re-export the PDF). Commit these edits:

```bash
git add -A
git commit -m "Personalise README, licence and report"
```

## 3. Create the repository and push

```bash
gh repo create AI-Escape-Room --public --source=. --remote=origin \
  --description "An interactive LLM-powered escape-room application featuring two development versions, structured game-state management, rule-based action validation and adversarial testing." \
  --push
```

Without the GitHub CLI: create an **empty** repository named `AI-Escape-Room` on github.com (no README,
no licence), then run:

```bash
git remote add origin https://github.com/<your-github-username>/AI-Escape-Room.git
git branch -M main
git push -u origin main      # Git Credential Manager opens a browser sign-in
```

## 4. Verify

```bash
gh repo view --web           # opens the repository
gh run list --limit 3        # the "tests" workflow should start and turn green
```

Check in a private browser window that the README renders with its diagrams and screenshots, and that
`.env` is **not** listed. Then copy the URL into your submission.

## 5. Before you submit

- [ ] Add your key to `.env` (never commit it) and play Version 1 once.
- [ ] `python scripts/live_adversarial_eval.py` → commit `docs/live_eval_results.md`.
- [ ] `python scripts/capture_screenshots.py v1` → commit `screenshots/version1/03–07`.
- [ ] Re-run `python scripts/build_compliance.py` after you update statuses in it (needs `openpyxl`).
- [ ] Repository is public (or shared with your instructor). Submit its URL.
- [ ] Pin the repository on your GitHub profile (profile → *Customize your pins*).

## Portfolio notes (from the course instructions)

- Keep each course project in its **own repository**, as this one is.
- Revisit it after submission: add the live screenshots, improve documentation, fix bugs, and record
  changes in `docs/development_log.md` with normal commits.
- Be ready to explain the architecture, the key design decisions and the limitations. See the
  "Explaining your project" section in `demo/DEMONSTRATION_GUIDE.md`.
