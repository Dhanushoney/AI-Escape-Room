"""Shared Streamlit presentation helpers for both versions.

Only static, developer-authored HTML/CSS is rendered with
``unsafe_allow_html``.  Player and LLM text is always rendered through
ordinary Streamlit elements, so neither can inject markup into the page.
"""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Inter:wght@400;500;600&display=swap');

:root {
  --bg: #0e0d0b; --panel: #1a1814; --panel-2: #221f1a; --line: #3a342a;
  --ink: #ece4d4; --muted: #a89f8e; --gold: #d9a441; --gold-soft: rgba(217,164,65,.14);
  --ok: #6fbf73; --bad: #e07a5f;
}
html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif; }
.stApp {
  background: radial-gradient(ellipse at top, #1d1a14 0%, var(--bg) 60%);
}
.block-container { padding-top: 1.6rem; max-width: 1250px; }
h1, h2, h3, .er-title { font-family: 'Cinzel', Georgia, serif !important; letter-spacing: .04em; }

.er-hero {
  border: 1px solid var(--line); border-radius: 14px; padding: 1.1rem 1.4rem;
  background: linear-gradient(135deg, rgba(217,164,65,.10), rgba(0,0,0,0) 55%), var(--panel);
  margin-bottom: 1rem;
}
.er-title { font-size: 2rem; color: var(--gold); margin: 0; line-height: 1.15; }
.er-sub { color: var(--muted); margin: .2rem 0 0 0; font-size: .95rem; }
.er-badge {
  display: inline-block; font-size: .72rem; font-weight: 600; letter-spacing: .08em;
  text-transform: uppercase; padding: .2rem .6rem; border-radius: 999px;
  border: 1px solid var(--gold); color: var(--gold); margin-bottom: .45rem;
}
.er-panel-title {
  font-family: 'Cinzel', Georgia, serif; color: var(--gold); font-size: .95rem;
  letter-spacing: .08em; text-transform: uppercase; margin: .2rem 0 .5rem 0;
}
.er-chip {
  display: inline-block; padding: .25rem .6rem; margin: 0 .3rem .35rem 0;
  border-radius: 8px; background: var(--gold-soft); border: 1px solid #5a4824; font-size: .85rem;
}
.er-empty { color: var(--muted); font-size: .85rem; font-style: italic; }
.er-puzzle { display: flex; justify-content: space-between; gap: .5rem; padding: .35rem 0;
  border-bottom: 1px dashed var(--line); font-size: .88rem; }
.er-puzzle:last-child { border-bottom: none; }
.er-ok { color: var(--ok); font-weight: 600; }
.er-wait { color: var(--muted); }
.er-note { color: var(--muted); font-size: .78rem; margin-top: .3rem; }
.er-escaped {
  border: 1px solid var(--ok); background: rgba(111,191,115,.12); border-radius: 12px;
  padding: .9rem 1.1rem; margin: .5rem 0 1rem 0; font-weight: 600;
}
div[data-testid="stButton"] > button {
  border-radius: 10px; border: 1px solid var(--line); background: var(--panel-2);
  min-height: 3.1rem; font-weight: 500; transition: border-color .15s, transform .15s;
}
div[data-testid="stButton"] > button:hover { border-color: var(--gold); transform: translateY(-1px); }
div[data-testid="stButton"] > button:focus-visible { outline: 2px solid var(--gold); }
div[data-testid="stChatMessage"] { background: rgba(26,24,20,.7); border: 1px solid var(--line); border-radius: 12px; }
</style>
"""


def setup_page(page_title: str) -> None:
    st.set_page_config(page_title=page_title, page_icon="🗝️", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)


def render_hero(config: dict[str, Any], version_label: str, version_blurb: str) -> None:
    st.markdown(
        f"""<div class="er-hero">
<span class="er-badge">{html.escape(version_label)}</span>
<p class="er-title">{html.escape(config['title'])}</p>
<p class="er-sub">{html.escape(config['subtitle'])} &middot; {html.escape(version_blurb)}</p>
</div>""",
        unsafe_allow_html=True,
    )


def panel_title(text: str) -> None:
    st.markdown(f'<p class="er-panel-title">{html.escape(text)}</p>', unsafe_allow_html=True)


def render_chips(labels: list[str], empty_text: str) -> None:
    if not labels:
        st.markdown(f'<p class="er-empty">{html.escape(empty_text)}</p>', unsafe_allow_html=True)
        return
    chips = "".join(f'<span class="er-chip">{html.escape(label)}</span>' for label in labels)
    st.markdown(chips, unsafe_allow_html=True)


def render_puzzle_rows(rows: list[tuple[str, bool]]) -> None:
    body = "".join(
        f'<div class="er-puzzle"><span>{html.escape(name)}</span>'
        f'<span class="{"er-ok" if done else "er-wait"}">{"✔ Solved" if done else "○ Unsolved"}</span></div>'
        for name, done in rows
    )
    st.markdown(body, unsafe_allow_html=True)


def render_note(text: str) -> None:
    st.markdown(f'<p class="er-note">{html.escape(text)}</p>', unsafe_allow_html=True)


def render_escaped_banner(text: str) -> None:
    st.markdown(f'<div class="er-escaped">🏆 {html.escape(text)}</div>', unsafe_allow_html=True)


def render_story_and_instructions(config: dict[str, Any], extra_tips: list[str]) -> None:
    with st.expander("📜 Story & how to play", expanded=False):
        st.write(config["intro"])
        st.markdown(
            "**How to play** — type what you want to do in plain English, or click an object card "
            "to examine it. Examples:\n"
            "- `examine the bookshelf`\n"
            "- `take the UV lamp`\n"
            "- `enter 1234 on the drawer`\n"
            "- `use the brass key on the painting`\n"
            "- `I need a hint`\n"
            + "".join(f"- {tip}\n" for tip in extra_tips)
        )
