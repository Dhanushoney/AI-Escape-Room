"""Version 2 - Reliable AI Escape Room (Python rules, LLM language).

Run with:  streamlit run app/version2.py

Works with a Gemini key (LLM intent interpretation + narration) or without
one (rule-based interpreter + engine narration).  The game rules are identical
in both modes because they live in Python, not in the model.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st  # noqa: E402

from app import ui_common as ui  # noqa: E402
from app.game_config import load_config  # noqa: E402
from app.llm_client import LLMError, create_client, load_settings  # noqa: E402
from app.v2_controller import V2Game  # noqa: E402


def get_game() -> V2Game:
    if "v2_game" not in st.session_state:
        client = None
        try:
            client = create_client(load_settings())
        except LLMError as exc:
            st.session_state["v2_setup_error"] = exc.user_message
        st.session_state["v2_game"] = V2Game(client=client, config=load_config())
    return st.session_state["v2_game"]


def queue_action(text: str) -> None:
    st.session_state["v2_pending"] = text


def restart() -> None:
    st.session_state["v2_game"].reset()


def object_label(game: V2Game, obj_id: str) -> str:
    obj = game.config["objects"][obj_id]
    state = game.state
    if obj.get("locked") and not state.is_unlocked(obj_id):
        status = "🔒"
    elif obj.get("locked"):
        status = "🔓"
    else:
        status = ""
    seen = " ✓" if obj_id in state.examined_objects else ""
    return f"{obj['icon']}  {obj['name']} {status}{seen}".strip()


def render_sidebar_panels(game: V2Game) -> None:
    config, state = game.config, game.state
    ui.render_story_and_instructions(
        config,
        ["Version 2 checks every action in Python - claims, titles and tricks do not change the rules."],
    )
    ui.panel_title("🎒 Inventory")
    ui.render_chips(
        [f"{config['items'][i]['icon']} {config['items'][i]['name']}" for i in state.inventory],
        "Empty-handed.",
    )
    ui.panel_title("🧩 Seals restored")
    ui.render_puzzle_rows([(p["name"], pid in state.solved_puzzles) for pid, p in config["puzzles"].items()])
    steps_total = len(config["puzzles"]) + 1
    steps_done = len(state.solved_puzzles) + (1 if state.escaped else 0)
    st.progress(steps_done / steps_total, text=f"Progress {steps_done}/{steps_total} (3 seals + exit)")

    ui.panel_title("🗒️ Notebook")
    if state.discovered_clues:
        for clue_id in state.discovered_clues:
            st.markdown(f"- {config['clues'][clue_id]}")
    else:
        ui.render_note("Clues you discover are recorded here automatically.")

    st.button("↻ Restart game", on_click=restart, use_container_width=True, key="v2_restart")
    mode = game.client.name if game.client else "Offline mode: rule-based interpreter + engine narration"
    st.caption(f"Language layer: {mode}")
    ui.render_note("All inventory, puzzle and door status above comes from the Python game state.")


def render_turns(game: V2Game, show_engine: bool) -> None:
    config = game.config
    with st.chat_message("assistant", avatar="🕯️"):
        st.markdown(f"**{config['room']['name']}**")
        st.write(config["intro"])
        st.write(config["room"]["description"])
    for turn in game.turns:
        with st.chat_message("user", avatar="🧑"):
            st.write(turn.player_text)
        with st.chat_message("assistant", avatar="🕯️"):
            st.markdown(turn.narration.text)
            verdict = "✅ accepted" if turn.result.success else "⛔ rejected"
            st.caption(f"⚙️ Engine verdict: {verdict} · `{turn.result.code}`")
            if "llm_unavailable" in (turn.interpreter_fallback, turn.narration.guard_reason):
                st.caption("⚠️ Gemini was unavailable for this turn (key, quota or network) - rule-based fallback used.")
            if show_engine:
                st.json(
                    {
                        "action_request": turn.request.to_dict(),
                        "interpreter_fallback": turn.interpreter_fallback,
                        "engine_result": turn.result.code,
                        "state_changed": turn.result.state_changed,
                        "narration_source": turn.narration.source,
                        "output_guard": turn.narration.guard_reason,
                    },
                    expanded=False,
                )


def main() -> None:
    ui.setup_page("The Last Archive · Version 2")
    game = get_game()
    config, state = game.config, game.state

    ui.render_hero(config, "Version 2 · Validated Engine", "Python enforces the rules, the LLM tells the story")
    if st.session_state.get("v2_setup_error"):
        st.error(st.session_state["v2_setup_error"] + " Continuing in offline mode.")

    main_col, side_col = st.columns([2.3, 1], gap="large")
    with side_col:
        render_sidebar_panels(game)

    with main_col:
        if state.escaped:
            ui.render_escaped_banner(
                f"Escaped in {state.turn_count} turns - all three seals restored and the exit door is open."
            )
        ui.panel_title("🔎 Explore the room")
        objects = list(config["objects"])
        for row_start in range(0, len(objects), 3):
            cols = st.columns(3)
            for col, obj_id in zip(cols, objects[row_start: row_start + 3]):
                col.button(
                    object_label(game, obj_id),
                    key=f"v2_obj_{obj_id}",
                    on_click=queue_action,
                    args=(f"examine the {config['objects'][obj_id]['name'].lower()}",),
                    use_container_width=True,
                )
        head_left, head_right = st.columns([3, 1.4])
        with head_left:
            ui.panel_title("📖 Journal")
        with head_right:
            show_engine = st.toggle("Show engine details", key="v2_show_engine")
        with st.container(height=460, border=False):
            render_turns(game, show_engine)

    typed = st.chat_input("What do you do? (e.g. examine the desk, take the lamp, hint)")
    action = typed or st.session_state.pop("v2_pending", None)
    if action:
        with st.spinner("The archive stirs..."):
            game.process(action)
        st.rerun()


main()
