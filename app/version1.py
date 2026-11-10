"""Version 1 - Interactive AI Escape Room (the LLM is the Game Master).

Run with:  streamlit run app/version1.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow ``streamlit run app/version1.py`` from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json  # noqa: E402

import streamlit as st  # noqa: E402

from app import ui_common as ui  # noqa: E402
from app.game_config import load_config  # noqa: E402
from app.llm_client import (  # noqa: E402
    ChatMessage,
    LLMError,
    MockLLMClient,
    create_client,
    load_settings,
)
from app.v1_game_master import V1Session  # noqa: E402

STUB_NOTICE = (
    "*(Offline stub — no Gemini API key is configured, so the Version 1 LLM Game Master is not running. "
    "Add GEMINI_API_KEY to `.env` and restart to play Version 1. Version 2 is fully playable offline.)*"
)


def _stub_reply(session_holder: dict) -> MockLLMClient:
    """A clearly labelled placeholder used only when no API key is available."""

    def respond(_system: str, _messages: list[ChatMessage], _schema: dict | None) -> str:
        status = session_holder.get("status", {})
        return f"{STUB_NOTICE}\nSTATUS: {json.dumps(status)}"

    return MockLLMClient(responses=respond, name="Offline stub (no LLM)")


def get_session() -> V1Session:
    if "v1_session" not in st.session_state:
        settings = load_settings()
        holder: dict = {}
        client = None
        try:
            client = create_client(settings)
        except LLMError as exc:
            st.session_state["v1_setup_error"] = exc.user_message
        if client is None:
            client = _stub_reply(holder)
            st.session_state["v1_offline"] = True
        session = V1Session(client=client, config=load_config())
        holder["status"] = session.status
        st.session_state["v1_holder"] = holder
        st.session_state["v1_session"] = session
        st.session_state["v1_log"] = []  # what the player sees: (role, text)
    return st.session_state["v1_session"]


def queue_action(text: str) -> None:
    st.session_state["v1_pending"] = text


def restart() -> None:
    session: V1Session = st.session_state["v1_session"]
    session.reset()
    st.session_state["v1_holder"]["status"] = session.status
    st.session_state["v1_log"] = []
    st.session_state.pop("v1_error", None)


def handle(text: str) -> None:
    session: V1Session = st.session_state["v1_session"]
    st.session_state.pop("v1_error", None)
    try:
        reply = session.send(text)
    except LLMError as exc:
        st.session_state["v1_error"] = exc.user_message
        return
    st.session_state["v1_holder"]["status"] = session.status
    st.session_state["v1_log"].append(("user", text))
    st.session_state["v1_log"].append(("assistant", reply))


def main() -> None:
    ui.setup_page("The Last Archive · Version 1")
    config = load_config()
    session = get_session()

    ui.render_hero(config, "Version 1 · LLM Game Master", "the language model runs the whole game")

    if st.session_state.get("v1_offline"):
        st.warning(
            "No Gemini API key found — Version 1 is running an **offline stub**, not an LLM. "
            "Create a free key at Google AI Studio, put it in `.env` as `GEMINI_API_KEY`, and restart.",
            icon="🔑",
        )
    if st.session_state.get("v1_setup_error"):
        st.error(st.session_state["v1_setup_error"])

    main_col, side_col = st.columns([2.3, 1], gap="large")

    with side_col:
        ui.render_story_and_instructions(config, ["In Version 1 the Game Master (an LLM) decides everything."])
        ui.panel_title("🎒 Inventory")
        ui.render_chips(session.status.get("inventory", []), "Empty-handed.")
        ui.panel_title("🧩 Seals restored")
        solved = set(session.status.get("solved_puzzles", []))
        rows = [(p["name"], pid in solved) for pid, p in config["puzzles"].items()]
        ui.render_puzzle_rows(rows)
        progress = min(len(solved & set(config["puzzles"])), 3) / 3
        st.progress(progress, text=f"Progress {int(progress * 100)}%")
        ui.render_note(
            "Inventory and progress above are reported by the LLM itself (STATUS line) and are not verified."
        )
        st.button("↻ Restart game", on_click=restart, use_container_width=True, key="v1_restart")
        st.caption(f"Model: {session.client.name}")

    with main_col:
        if session.escaped:
            ui.render_escaped_banner("The Game Master reports that you have escaped the Last Archive!")
        ui.panel_title("🔎 Explore the room")
        objects = list(config["objects"].items())
        for row_start in range(0, len(objects), 3):
            cols = st.columns(3)
            for col, (obj_id, obj) in zip(cols, objects[row_start: row_start + 3]):
                col.button(
                    f"{obj['icon']}  {obj['name']}",
                    key=f"v1_obj_{obj_id}",
                    on_click=queue_action,
                    args=(f"I examine the {obj['name'].lower()}.",),
                    use_container_width=True,
                )

        ui.panel_title("📖 Journal")
        with st.container(height=460, border=False):
            with st.chat_message("assistant", avatar="🕯️"):
                st.markdown(f"**{config['room']['name']}**")
                st.write(config["intro"])
                st.write(config["room"]["description"])
            for role, text in st.session_state["v1_log"]:
                with st.chat_message(role, avatar="🧑" if role == "user" else "🕯️"):
                    st.markdown(text)
        if st.session_state.get("v1_error"):
            st.error(st.session_state["v1_error"], icon="⚠️")

    typed = st.chat_input("What do you do? (e.g. examine the bookshelf)")
    action = typed or st.session_state.pop("v1_pending", None)
    if action:
        with st.spinner("The Game Master considers your move..."):
            handle(action)
        st.rerun()


main()
