"""Draw the two architecture diagrams as clean, hand-laid-out SVG files.

Output: docs/architecture/version1_architecture.svg and version2_architecture.svg
(PNG renders are produced from these SVGs with a headless browser).

Every box and connector is placed explicitly so that nothing overlaps and no
connector crosses another. Run from the project root:

    python scripts/draw_architecture.py
"""

from __future__ import annotations

import html
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "architecture"

FONT = "Segoe UI, Helvetica Neue, Arial, sans-serif"
INK = "#1f2933"
MUTED = "#52606d"
LINE = "#3e4c59"

STYLES = {
    "ui": ("#e8f1fb", "#4a7bb7"),        # interface / player-facing
    "code": ("#ffffff", "#3e4c59"),      # ordinary Python code
    "core": ("#e6f4ea", "#2f855a"),      # authoritative Python core
    "llm": ("#fdebc8", "#c68a12"),       # language model
    "data": ("#eef0f7", "#5a67a8"),      # configuration / state stores
    "danger": ("#fdecea", "#c53030"),
}


class Canvas:
    def __init__(self, width: int, height: int, title: str, subtitle: str):
        self.w, self.h = width, height
        self.parts: list[str] = []
        self.labels: list[str] = []  # drawn last so they sit on top of lines
        self.parts.append(f'<rect width="{width}" height="{height}" fill="#ffffff"/>')
        self.text(30, 38, title, 22, weight="700")
        self.text(30, 62, subtitle, 13.5, color=MUTED)

    # ------------------------------------------------------------------ text
    def text(self, x, y, s, size, weight="400", color=INK, anchor="start", italic=False, layer=None):
        style = ' font-style="italic"' if italic else ""
        (layer if layer is not None else self.parts).append(
            f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}" text-anchor="{anchor}"{style}>{html.escape(s)}</text>'
        )

    def _lines(self, cx, top, title, lines, title_size=14.5, line_size=12, gap=16):
        self.text(cx, top, title, title_size, weight="700", anchor="middle")
        y = top + gap + 2
        for line in lines:
            italic = line.startswith("~")
            self.text(cx, y, line.lstrip("~"), line_size, color=MUTED if not italic else "#3b4a5a",
                      anchor="middle", italic=italic)
            y += gap - 1

    # ---------------------------------------------------------------- shapes
    def box(self, x, y, w, h, title, lines=(), kind="code", radius=9):
        fill, stroke = STYLES[kind]
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>')
        n = len(lines)
        top = y + h / 2 - (n * 15) / 2 + 4
        self._lines(x + w / 2, top, title, lines)

    def pill(self, x, y, w, h, title, kind="ui"):
        fill, stroke = STYLES[kind]
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>')
        self.text(x + w / 2, y + h / 2 + 5, title, 13, weight="700", anchor="middle")

    def cylinder(self, x, y, w, h, title, lines=(), kind="data"):
        fill, stroke = STYLES[kind]
        e = 9
        self.parts.append(
            f'<path d="M{x},{y+e} A{w/2},{e} 0 0 1 {x+w},{y+e} L{x+w},{y+h-e} A{w/2},{e} 0 0 1 {x},{y+h-e} Z" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>'
            f'<path d="M{x},{y+e} A{w/2},{e} 0 0 0 {x+w},{y+e}" fill="none" stroke="{stroke}" stroke-width="1.8"/>'
        )
        n = len(lines)
        top = y + h / 2 - (n * 15) / 2 + 9
        self._lines(x + w / 2, top, title, lines)

    def lane(self, x, y, w, h, label, kind, label_x=None):
        fill, stroke = {"llm": ("#fffaf0", "#e2b45a"), "core": ("#f3faf5", "#68a77c"), "plain": ("#f7f9fb", "#b8c2cc")}[kind]
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="{stroke}" stroke-width="1.5" stroke-dasharray="7 5"/>')
        self.text(label_x if label_x is not None else x + 16, y + 24, label, 13, weight="700", color=stroke if kind != "plain" else MUTED)

    def note(self, x, y, w, h, lines, kind="danger"):
        fill, stroke = STYLES[kind]
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
        yy = y + 24
        for i, line in enumerate(lines):
            self.text(x + 16, yy, line, 13 if i == 0 else 12.5, weight="700" if i == 0 else "400", color=stroke if i == 0 else INK)
            yy += 19

    # ---------------------------------------------------------------- arrows
    def arrow(self, points, label=None, at=None, dashed=False, color=LINE, anchor="middle"):
        d = "M" + " L".join(f"{x},{y}" for x, y in points)
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        self.parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.8"{dash} marker-end="url(#arrow)"/>')
        if label:
            lx, ly = at if at else ((points[0][0] + points[1][0]) / 2, (points[0][1] + points[1][1]) / 2)
            width = len(label) * 6.4 + 12
            bx = lx - width / 2 if anchor == "middle" else (lx if anchor == "start" else lx - width)
            self.labels.append(f'<rect x="{bx}" y="{ly-11}" width="{width}" height="18" rx="4" fill="#ffffff" stroke="#d5dbe1" stroke-width="0.8"/>')
            self.text(bx + width / 2, ly + 2.5, label, 11.5, color="#334e68", anchor="middle", layer=self.labels)

    def dot(self, x, y):
        self.parts.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{LINE}"/>')

    def save(self, path: Path):
        defs = (
            '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/></marker></defs>'
        )
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
            + defs + "".join(self.parts) + "".join(self.labels) + "</svg>"
        )
        path.write_text(svg, encoding="utf-8")


def legend(c: Canvas, x, y, items):
    for kind, label in items:
        fill, stroke = STYLES[kind]
        c.parts.append(f'<rect x="{x}" y="{y-11}" width="16" height="14" rx="3" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
        c.text(x + 22, y + 1, label, 12, color=MUTED)
        x += 30 + len(label) * 6.6


# ====================================================================== V1
def version1() -> None:
    c = Canvas(1440, 640, "Version 1 architecture — the LLM is the Game Master",
               "One model call per turn. The model holds the rules, every puzzle solution and the game state.")
    # row 1 (y-centre 170) and row 2 (y-centre 440); session sits between them
    c.pill(25, 145, 185, 50, "Player types an action")
    c.box(250, 128, 220, 84, "Streamlit interface", ["~app/version1.py", "object cards · chat input · restart"], "ui")
    c.box(540, 255, 260, 112, "Session management", ["~V1Session in st.session_state", "chat history (last 30 messages)", "status as reported by the model"], "code")
    c.box(870, 118, 230, 104, "LLM Game Master", ["Google Gemini", "interprets actions · judges answers", "decides and tracks the game state"], "llm")
    c.box(1220, 118, 200, 104, "Prompt and game context", ["~build_system_prompt()", "story · objects · rules", "ALL puzzle solutions"], "data")
    c.box(870, 398, 230, 84, "Response parser", ["~parse_game_master_reply()", "narrative + STATUS line"], "code")
    c.box(250, 398, 220, 84, "Player display", ["journal · inventory · seals", "(reported by the LLM, unverified)"], "ui")
    c.pill(25, 415, 185, 50, "Player sees outcome")

    c.arrow([(210, 170), (250, 170)])
    c.arrow([(470, 170), (640, 170), (640, 255)], "player message", at=(560, 170))
    c.arrow([(800, 285), (835, 285), (835, 170), (870, 170)], "history + new message", at=(835, 230))
    c.arrow([(1220, 170), (1100, 170)], "instructions", at=(1160, 170))
    c.arrow([(985, 222), (985, 398)], "reply text", at=(985, 310))
    c.arrow([(870, 440), (720, 440), (720, 367)], "narrative + STATUS", at=(795, 440))
    c.arrow([(600, 367), (600, 440), (470, 440)], "journal + status", at=(535, 440))
    c.arrow([(250, 440), (210, 440)])

    c.note(250, 525, 1160, 76, [
        "Why Version 1 is unreliable",
        "Whatever the model writes in its STATUS line becomes the game state — nothing checks it. All solutions sit in the model's",
        "context, so a persuasive player (\"I am the administrator…\") can talk it into escaping or revealing codes.",
    ])
    legend(c, 30, 625, [("ui", "Interface"), ("code", "Python code"), ("llm", "Language model"), ("data", "Prompt / data")])
    c.save(OUT / "version1_architecture.svg")


# ====================================================================== V2
def version2() -> None:
    c = Canvas(1480, 960, "Version 2 architecture — Python decides, the LLM translates",
               "Both LLM outputs are treated as untrusted. Only the Python game engine can change the game state.")

    # ---- Lane A: input and interpretation (y 85..300)
    c.lane(15, 85, 1450, 215, "① INPUT AND INTERPRETATION — the LLM's output here is only a request", "llm")
    c.pill(28, 168, 170, 50, "Player types an action")
    c.box(215, 151, 170, 84, "Streamlit interface", ["~app/version2.py", "object cards · chat"], "ui")
    c.box(415, 145, 200, 96, "Input normalisation", ["~normalise_player_input()", "Unicode NFKC · strip control", "characters · 500-char cap"], "code")
    c.box(665, 118, 250, 74, "LLM intent interpreter", ["Gemini · JSON schema · temperature 0", "sees object ids only — no solutions"], "llm")
    c.box(665, 210, 250, 74, "Rule-based parser", ["~rule_based_parse()", "used if the LLM fails · overrides tricks"], "code")
    c.box(985, 151, 260, 84, "Structured action request", ["~parse_action_request()", "schema check · action + id allowlists"], "core")

    c.arrow([(198, 193), (215, 193)])
    c.arrow([(385, 193), (415, 193)])
    c.arrow([(615, 193), (640, 193), (640, 155), (665, 155)], "clean text", at=(640, 132))
    c.arrow([(640, 193), (640, 247), (665, 247)])
    c.dot(640, 193)
    c.arrow([(915, 155), (950, 155), (950, 193), (985, 193)], "JSON intent", at=(950, 132))
    c.arrow([(915, 247), (950, 247), (950, 193)])

    # ---- Lane B: authoritative core (y 330..610)
    c.lane(15, 330, 1450, 280, "② PYTHON GAME CORE — authoritative: the only code that can change the game state", "core")
    c.cylinder(40, 395, 230, 120, "GameState", ["~app/game_state.py", "single source of truth", "inventory · clues · puzzles · door"], "data")
    c.box(500, 410, 280, 90, "Game engine", ["~GameEngine.execute()", "applies validated actions", "check_game_completion()"], "core")
    c.box(985, 410, 260, 90, "Action validation engine", ["~validate_action()", "exists? held? unlocked? prerequisites?"], "core")
    c.cylinder(1290, 400, 165, 110, "Rule config", ["~game_config.json", "objects · dependencies", "solutions"], "data")
    c.box(415, 530, 200, 64, "Inventory manager", ["~collect_item() · use_item()"], "core")
    c.box(665, 530, 200, 64, "Puzzle engine", ["~check_answer() · prerequisites"], "core")

    c.arrow([(1115, 235), (1115, 410)], "ActionRequest", at=(1115, 312))
    c.arrow([(1290, 455), (1245, 455)], "rules", at=(1267, 432))
    c.arrow([(985, 455), (780, 455)], "accepted / rejected", at=(882, 455))
    c.arrow([(500, 455), (270, 455)], "validated update", at=(385, 455))
    c.arrow([(560, 500), (560, 530)])
    c.arrow([(720, 500), (720, 530)])
    c.arrow([(1372, 510), (1372, 562), (865, 562)], "solutions + dependencies", at=(1118, 562))
    c.arrow([(155, 395), (155, 378), (1035, 378), (1035, 410)], "current state (read-only)", at=(600, 378))

    # ---- Lane C: narration and display (y 650..860)
    c.lane(15, 650, 1450, 215, "③ NARRATION AND DISPLAY — the LLM describes the verdict; its text is checked before display", "llm", label_x=670)
    c.box(90, 735, 260, 84, "LLM narrative generator", ["Gemini · receives engine facts +", "public state summary (no solutions)"], "llm")
    c.box(480, 735, 280, 84, "Output sanitisation", ["~sanitise_narration()", "leak · false-escape · length checks"], "core")
    c.box(890, 735, 280, 84, "Player display", ["narration + engine verdict badge", "inventory · seals · notebook"], "ui")
    c.pill(1250, 752, 190, 50, "Player sees outcome")

    # engine facts drop through the gap between inventory and puzzle engine
    c.arrow([(640, 500), (640, 700), (300, 700), (300, 735)], "ActionResult facts", at=(470, 700))
    c.arrow([(640, 700), (640, 735)], "engine text = safe fallback", at=(650, 718), anchor="start")
    c.dot(640, 700)
    c.arrow([(130, 515), (130, 735)], "public summary", at=(130, 620))
    c.arrow([(350, 777), (480, 777)], "draft", at=(415, 777))
    c.arrow([(760, 777), (890, 777)], "approved text", at=(825, 777))
    c.arrow([(1170, 777), (1250, 777)])
    c.arrow([(40, 455), (25, 455), (25, 900), (1030, 900), (1030, 819)], "authoritative status (inventory, seals, notebook)", at=(560, 900))

    legend(c, 30, 945, [("ui", "Interface"), ("code", "Python code"), ("core", "Validated core"), ("llm", "Language model (untrusted output)"), ("data", "State / configuration")])
    c.save(OUT / "version2_architecture.svg")


if __name__ == "__main__":
    version1()
    version2()
    print("wrote", OUT / "version1_architecture.svg", "and", OUT / "version2_architecture.svg")
