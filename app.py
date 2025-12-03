import os
import json
from typing import List, Dict, Any


import re
import streamlit as st

from recipes import RECIPE_LIBRARY, get_recipe_keys_and_labels
from view_helpers import (
    format_working_ingredients_markdown,
    format_steps_with_progress_markdown,
)
from llm_agent import call_agent_sous_chef
from commands import COMMANDS_LONG_MARKDOWN, COMMANDS_CONDENSED, handle_user_command


# --- Config & setup ---

st.set_page_config(
    page_title="Agent Sous Chef",
    layout="centered",
)

st.title("Agent Sous Chef")
st.write("Your tiny AI sous chef, guiding you step by step as you cook.")
st.markdown(COMMANDS_LONG_MARKDOWN)

# --- Session state setup ---

if "messages" not in st.session_state:
    st.session_state.messages: List[Dict[str, str]] = []

if "current_step" not in st.session_state:
    st.session_state.current_step = 0

if "recipe_key" not in st.session_state:
    # Default to the first recipe in the library
    first_key = next(iter(RECIPE_LIBRARY.keys()))
    st.session_state.recipe_key = first_key

if "ingredient_subs" not in st.session_state:
    # Per-recipe mapping: { recipe_key: { original_ingredient: substitute_name } }
    st.session_state.ingredient_subs: Dict[str, Dict[str, str]] = {}

if "ingredient_strikes" not in st.session_state:
    # Per-recipe mapping: { recipe_key: set_of_original_ingredients_to_strike }
    st.session_state.ingredient_strikes: Dict[str, set[str]] = {}

if "pending_recipe_pick" not in st.session_state:
    # When True, numeric input like "2" is treated as "pick recipe #2"
    st.session_state.pending_recipe_pick = False

if "pick_candidates" not in st.session_state:
    # Holds the current list of candidate recipe keys during pick/search mode
    st.session_state.pick_candidates = None


def reset_conversation_for_recipe(new_recipe_key: str) -> None:
    """Fully reset ALL state when switching or restarting a recipe."""
    # Clear all session state first
    st.session_state.clear()

    # Restore the selected recipe key
    st.session_state.recipe_key = new_recipe_key

    # Fresh containers
    st.session_state.messages = []
    st.session_state.current_step = 0
    st.session_state.ingredient_subs = {new_recipe_key: {}}
    st.session_state.ingredient_strikes = {new_recipe_key: set()}
    st.session_state.pending_recipe_pick = False

    recipe = RECIPE_LIBRARY[new_recipe_key]

    # First assistant message
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": (
                f"Now cooking: {recipe['name']}.\n\n"
                f"{COMMANDS_CONDENSED}"
            ),
        }
    )


# Ensure we have an initial message if messages are empty
if not st.session_state.messages:
    reset_conversation_for_recipe(st.session_state.recipe_key)

# --- Main layout: recipe choice, ingredients, and steps (no sidebar) ---

recipe_items = get_recipe_keys_and_labels()
recipe_labels = [label for _, label in recipe_items]

current_recipe_key = st.session_state.recipe_key
current_index = next(
    (i for i, (key, _) in enumerate(recipe_items) if key == current_recipe_key),
    0,
)

st.markdown("## Recipe selection")
selected_label = st.selectbox(
    "Choose a recipe",
    recipe_labels,
    index=current_index,
)

selected_key = next(
    key for key, label in recipe_items if label == selected_label
)

if selected_key != st.session_state.recipe_key:
    reset_conversation_for_recipe(selected_key)

active_recipe = RECIPE_LIBRARY[st.session_state.recipe_key]
recipe_name = active_recipe["name"]
recipe_description = active_recipe["description"]
recipe_steps: List[str] = active_recipe["steps"]
recipe_ingredients: List[str] = active_recipe.get("ingredients", [])
recipe_subs: Dict[str, str] = st.session_state.ingredient_subs.get(st.session_state.recipe_key, {})

st.markdown(f"### {recipe_name}")
st.caption(recipe_description)

# Layout: left = ingredients, right = steps / restart
col_left, col_right = st.columns([2, 1])

with col_left:
    if recipe_ingredients:
        st.markdown("#### Ingredients")

        # Get any strike marks for this recipe (ingredients user wants visually struck out)
        strikes_for_recipe = st.session_state.ingredient_strikes.get(st.session_state.recipe_key, set())

        lines = format_working_ingredients_markdown(
            recipe_ingredients,
            recipe_subs,
            strikes_for_recipe,
        )
        for line in lines:
            st.write(line)

with col_right:
    # Restart button: hard reset all state, keep the current recipe, and rerun
    if st.button("Restart this recipe"):
        current_recipe = st.session_state.recipe_key if "recipe_key" in st.session_state else None
        st.session_state.clear()
        if current_recipe is not None:
            st.session_state.recipe_key = current_recipe
        st.rerun()

    st.markdown("#### Steps")

    # Use simple text markers instead of checkboxes:
    # [x] = completed, -> = current, no prefix = not started yet
    for idx, step in enumerate(recipe_steps):
        if idx < st.session_state.current_step:
            prefix = "[x]"
        elif idx == st.session_state.current_step:
            prefix = "->"
        else:
            prefix = ""  # no prefix for not-yet-done steps
        if prefix:
            st.write(f"{prefix} {idx + 1}. {step}")
        else:
            st.write(f"{idx + 1}. {step}")

    st.caption("MVP: multiple recipes, ingredients, step tracking, and AI guidance.")

# --- Display chat history ---

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Chat input ---
user_input = st.chat_input("Talk to Agent Sous Chef...")

if user_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    lower = user_input.lower().strip()
    handled = False
    reply_text = ""
    advance_step = False

    # First, let the central command engine try to handle this input.
    command_result = handle_user_command(
        user_input=user_input,
        recipe_name=recipe_name,
        recipe_description=recipe_description,
        recipe_steps=recipe_steps,
        recipe_ingredients=recipe_ingredients,
        recipe_subs=recipe_subs,
    )
    handled = command_result.get("handled", False)
    reply_text = command_result.get("reply_text", "") or ""
    advance_step = command_result.get("advance_step", False)

    # If the command engine did not handle this, fall back to the LLM
    if not handled:
        try:
            result = call_agent_sous_chef(
                user_input=user_input,
                recipe_name=recipe_name,
                recipe_description=recipe_description,
                recipe_steps=recipe_steps,
                recipe_ingredients=recipe_ingredients,
                recipe_subs=recipe_subs,
                current_step_index=st.session_state.current_step,
            )
            reply_text = result["reply"]
            advance_step = result["advance_step"]
        except Exception as e:
            reply_text = f"Error calling the AI model: {e}"
            advance_step = False

    # Advance step if allowed and not beyond the final "all done" position.
    # We treat current_step as "index of the next step to work on", so it can go
    # from 0 up to len(recipe_steps). When it reaches len(recipe_steps), all steps
    # are considered completed and all boxes are checked.
    if advance_step and st.session_state.current_step < len(recipe_steps):
        st.session_state.current_step += 1

    # Append and display assistant message
    st.session_state.messages.append({"role": "assistant", "content": reply_text})
    with st.chat_message("assistant"):
        st.markdown(reply_text)