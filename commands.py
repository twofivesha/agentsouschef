from __future__ import annotations

import re
from typing import List, Dict, Any

import streamlit as st

from recipes import get_recipe_keys_and_labels, RECIPE_LIBRARY
from view_helpers import (
    format_working_ingredients_markdown,
    format_steps_with_progress_markdown,
)

# --- Command help text (central source of truth) ---

COMMANDS_LONG_MARKDOWN = """
**Commands**

- i — show working ingredients list  
- s — show all steps  
- x — cross off ingredient (x oil) or mark steps done (x 3 marks 1–3)  
- k — ok / advance to next step  
- what — shows working ingredients and current step  
- clear — clears all cross-offs, and returns to step 1  
- pick — choose a recipe via chat
"""

COMMANDS_CONDENSED = (
    "Commands: i=ingredients  |  s=steps  |  x=item/steps done  |  "
    "k=next step  |  what=status  |  clear=restart  |  pick=choose recipe"
)


def reset_conversation_for_recipe(new_recipe_key: str) -> None:
    """Fully reset ALL state when switching or restarting a recipe."""
    st.session_state.clear()

    st.session_state.recipe_key = new_recipe_key
    st.session_state.messages = []
    st.session_state.current_step = 0
    st.session_state.ingredient_subs = {new_recipe_key: {}}
    st.session_state.ingredient_strikes = {new_recipe_key: set()}
    st.session_state.pending_recipe_pick = False

    recipe = RECIPE_LIBRARY[new_recipe_key]

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": (
                f"Now cooking: {recipe['name']}.\n\n"
                f"{COMMANDS_CONDENSED}"
            ),
        }
    )


# --- Core command engine ---
def handle_user_command(
    user_input: str,
    recipe_name: str,
    recipe_description: str,
    recipe_steps: List[str],
    recipe_ingredients: List[str],
    recipe_subs: Dict[str, str],
) -> Dict[str, Any]:
    """Core command engine.

    Returns a dict with:
      - handled: bool
      - reply_text: str
      - advance_step: bool

    It is allowed to mutate st.session_state and call st.rerun().
    """
    lower = user_input.lower().strip()
    handled = False
    reply_text = ""
    advance_step = False

    # Allow cancelling recipe search (pick) mode
    if lower in {"cancel", "exit", "stop picking"} and st.session_state.get("pending_recipe_pick", False):
        st.session_state.pending_recipe_pick = False
        st.session_state.pick_candidates = None
        reply_text = "Okay, leaving recipe search mode."
        return {
            "handled": True,
            "reply_text": reply_text,
            "advance_step": False,
        }

    # --- 1. Full reset / clear commands ---
    start_over_triggers = [
        "start over",
        "restart",
        "start again",
        "reset recipe",
        "start this recipe over",
        "clear",
    ]
    if any(phrase == lower or phrase in lower for phrase in start_over_triggers):
        current_recipe = st.session_state.recipe_key if "recipe_key" in st.session_state else None
        st.session_state.clear()
        if current_recipe is not None:
            reset_conversation_for_recipe(current_recipe)
        st.rerun()

    # --- 2. Mark steps complete with "x N" ---
    step_x_match = re.match(r"^x\s+(\d+)\s*$", lower)
    if step_x_match:
        n = int(step_x_match.group(1))
        if n < 0:
            n = 0
        if n > len(recipe_steps):
            n = len(recipe_steps)

        st.session_state.current_step = n

        lines: list[str] = []
        if n == 0:
            lines.append("Okay, I’ve reset your step progress. You’re back at the beginning.")
        elif n >= len(recipe_steps):
            lines.append(
                f"Okay, I’ve marked all {len(recipe_steps)} steps as done. "
                "You’ve completed the recipe!"
            )
        else:
            lines.append(
                f"Got it. I’ve marked steps 1 through {n} as done. "
                f"You’re now on step {n + 1}."
            )

        lines.append("")
        lines.append("Here are all the steps with your updated progress:")
        lines.append("")

        current_idx = st.session_state.current_step
        lines.extend(
            format_steps_with_progress_markdown(
                recipe_steps,
                current_idx,
            )
        )

        reply_text = "\n".join(lines)
        return {
            "handled": True,
            "reply_text": reply_text,
            "advance_step": False,
        }

    # --- 3. Enter pick mode (interviewer style) ---
    if lower == "pick":
        # We don't list all recipes (there may be thousands).
        # Instead, we enter a search-based pick mode and ask for a keyword.
        st.session_state.pending_recipe_pick = True
        # We'll store the current filtered candidate keys here when the user searches.
        st.session_state.pick_candidates = None

        lines = [
            "Recipe search mode activated.",
            "What are you in the mood for?",
            "Try a keyword like 'eggs', 'pasta', 'soup', or 'chicken'.",
            "I'll show matching recipes and you can pick by number.",
        ]
        reply_text = "\n".join(lines)
        return {
            "handled": True,
            "reply_text": reply_text,
            "advance_step": False,
        }

    # --- 4. Pick-mode keyword filtering ---
    if st.session_state.get("pending_recipe_pick", False):
        # If the input is not a pure number, treat it as a filter query
        if not re.match(r"^\s*\d+\s*$", user_input):
            query = lower.strip()
            if not query:
                reply_text = (
                    "Please type a keyword for the kind of recipe you want.\n"
                    "For example: 'eggs', 'pasta', 'soup', or 'chicken'."
                )
                return {
                    "handled": True,
                    "reply_text": reply_text,
                    "advance_step": False,
                }

            items = get_recipe_keys_and_labels()
            lines: list[str] = []

            # Support multi-word queries: all tokens must appear in the label
            tokens = [t for t in query.split() if t]
            candidates: list[tuple[str, str]] = []
            for key, label in items:
                label_lower = label.lower()
                if all(t in label_lower for t in tokens):
                    candidates.append((key, label))

            if not candidates:
                reply_text = (
                    f"I couldn't find any recipes matching '{query}'.\n"
                    "Try a different keyword like 'eggs', 'pasta', 'soup', or 'chicken'."
                )
                # Keep pending_recipe_pick = True so they can try again
                return {
                    "handled": True,
                    "reply_text": reply_text,
                    "advance_step": False,
                }

            # Limit how many we show at once to keep the chat readable
            MAX_SHOW = 25
            shown = candidates[:MAX_SHOW]
            extra_count = max(0, len(candidates) - MAX_SHOW)

            # Store just the keys of the current candidate list in session state
            st.session_state.pick_candidates = [key for key, _ in shown]

            lines.append(f"Recipes matching '{query}':")
            lines.append("")
            for idx, (key, label) in enumerate(shown, start=1):
                lines.append(f"{idx}. {label}")

            if extra_count > 0:
                lines.append("")
                lines.append(
                    f"...and {extra_count} more results. "
                    "Try adding another word to narrow it down."
                )

            lines.append("")
            lines.append(
                "Reply with a number to pick one of these recipes, "
                "or type another keyword to search again."
            )

            reply_text = "\n".join(lines)
            return {
                "handled": True,
                "reply_text": reply_text,
                "advance_step": False,
            }

    # --- 5. Numeric-only input: pick or show step ---
    num_match = re.match(r"^\s*(\d+)\s*$", user_input)
    if num_match:
        n = int(num_match.group(1))

        # If we are in pending pick mode, interpret as recipe choice
        if st.session_state.get("pending_recipe_pick", False):
            candidates = st.session_state.get("pick_candidates")

            # If we don't have a current candidate list, ask them to search first
            if not candidates:
                reply_text = (
                    "Please type a keyword for the kind of recipe you want first.\n"
                    "For example: 'eggs', 'pasta', 'soup', or 'chicken'."
                )
                return {
                    "handled": True,
                    "reply_text": reply_text,
                    "advance_step": False,
                }

            if 1 <= n <= len(candidates):
                new_key = candidates[n - 1]
                reset_conversation_for_recipe(new_key)
                # Clear pick mode flags after a successful selection
                st.session_state.pending_recipe_pick = False
                st.session_state.pick_candidates = None
                st.rerun()
            else:
                reply_text = (
                    f"There are only {len(candidates)} recipes in the current list. "
                    f"Please pick a number between 1 and {len(candidates)}, "
                    "or type another keyword to search again."
                )
                return {
                    "handled": True,
                    "reply_text": reply_text,
                    "advance_step": False,
                }
        else:
            # Interpret as a request to show a specific step
            step_num = n
            step_index = step_num - 1
            if 0 <= step_index < len(recipe_steps):
                step_text = recipe_steps[step_index]
                reply_text = f"{step_num}. {step_text}"
            else:
                reply_text = f"This recipe only has {len(recipe_steps)} steps."

            return {
                "handled": True,
                "reply_text": reply_text,
                "advance_step": False,
            }

    # --- 6. Ingredient list command ("i" or similar) ---
    ingredient_triggers = [
        "ingredients",
        "ingredient list",
        "what are the ingredients",
        "show ingredients",
        "list the ingredients",
        "what do i need",
    ]

    if lower == "i" or any(phrase == lower or phrase in lower for phrase in ingredient_triggers):
        if recipe_ingredients:
            reply_lines = [
                "Here are the ingredients for this recipe (with substitutions applied):",
                "",
            ]
            strikes_for_recipe = st.session_state.ingredient_strikes.get(
                st.session_state.recipe_key, set()
            )

            reply_lines.extend(
                format_working_ingredients_markdown(
                    recipe_ingredients,
                    recipe_subs,
                    strikes_for_recipe,
                )
            )
            reply_text = "\n".join(reply_lines)
        else:
            reply_text = "This recipe does not have a stored ingredient list yet."

        return {
            "handled": True,
            "reply_text": reply_text,
            "advance_step": False,
        }

    # --- 7. Steps listing commands ("steps", "s") ---
    step_triggers = [
        "show all steps",
        "steps",
        "list steps",
        "show steps",
        "what are the steps",
        "s",
    ]
    if any(phrase == lower or phrase in lower for phrase in step_triggers):
        if recipe_steps:
            reply_lines = ["Here are all the steps for this recipe:", ""]
            current_idx = st.session_state.current_step
            reply_lines.extend(
                format_steps_with_progress_markdown(
                    recipe_steps,
                    current_idx,
                )
            )
            reply_text = "\n".join(reply_lines)
        else:
            reply_text = "This recipe does not have any steps defined yet."

        return {
            "handled": True,
            "reply_text": reply_text,
            "advance_step": False,
        }

    # --- 8. "what" status command: show name, ingredients, and current step ---
    if lower == "what":
        lines: list[str] = []

        # Recipe name
        lines.append(f"### You are cooking: {recipe_name}")
        lines.append("")

        # Ingredients section (working list with subs and strikes)
        if recipe_ingredients:
            lines.append("#### Ingredients (with substitutions applied)")
            lines.append("")
            strikes_for_recipe = st.session_state.ingredient_strikes.get(
                st.session_state.recipe_key, set()
            )

            lines.extend(
                format_working_ingredients_markdown(
                    recipe_ingredients,
                    recipe_subs,
                    strikes_for_recipe,
                )
            )

            lines.append("")

        # Current step section
        if 0 <= st.session_state.current_step < len(recipe_steps):
            step_num = st.session_state.current_step + 1
            step_text = recipe_steps[st.session_state.current_step]
            lines.append("#### Current step")
            lines.append("")
            lines.append(f"{step_num}. {step_text}")
        else:
            lines.append("You’ve completed all the steps in this recipe.")

        # Append a subtle separator and condensed command list at the end
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(COMMANDS_CONDENSED)

        reply_text = "\n".join(lines)
        return {
            "handled": True,
            "reply_text": reply_text,
            "advance_step": False,
        }

    # If nothing matched, let the caller fall back to the LLM
    return {
        "handled": False,
        "reply_text": "",
        "advance_step": False,
    }