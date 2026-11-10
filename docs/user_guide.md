# User Guide

## Starting a game

```bash
streamlit run app/version1.py   # LLM Game Master (needs GEMINI_API_KEY)
streamlit run app/version2.py   # Validated engine (works with or without a key)
```

The game opens in your browser (usually http://localhost:8501). Run only one at a time, or pass
`--server.port 8502` to the second.

## The screen

- **Explore the room** – six object cards. Clicking one examines it. In Version 2, 🔒/🔓 show lock
  status and ✓ marks objects you have examined.
- **Journal** – the story so far. Type actions in the box at the bottom.
- **Inventory**, **Seals restored** and **Progress** – in V1 these are what the Game Master reports; in
  V2 they come from the game engine.
- **Notebook** (V2) – every clue you discover is written down for you.
- **Show engine details** (V2) – reveals the structured action, engine verdict and whether the output
  guard intervened. Useful for demonstrations.
- **Restart game** – starts over.

## Commands

Plain English works. In Version 2 the most reliable phrasings are:

| You want to… | Type |
|--------------|------|
| Look around | `look around` |
| Inspect something | `examine the bookshelf`, `read the cipher card` |
| Pick something up | `take the lamp` |
| Use an item | `use the brass key on the painting`, `shine the uv lamp on the painting` |
| Enter a code | `enter 1234 on the drawer`, `enter 1234 on the console` |
| Enter a symbol sequence | `enter moon star triangle circle on the painting` (example order only) |
| See your items | `inventory` |
| Get a nudge | `hint` |

## Tips (spoiler-free)

- Examine everything; the desk and the bookshelf hold the first pieces.
- Clues often only make sense together.
- Some ink can only be seen under special light.
- The exit needs something the console gives you.

## Troubleshooting

| Message | Fix |
|---------|-----|
| "No Gemini API key found" | Copy `.env.example` to `.env`, add your key, restart |
| "rejected the API key or model name" | Check the key, or set `GEMINI_MODEL` to a model your key can use |
| "free quota is busy" | Wait a minute (free-tier rate limit) |
| V2 shows "Gemini was unavailable for this turn" | Network/quota issue; the game continues in rule-based mode |
