# commands_headless.py
"""
Headless version of commands.py that doesn't depend on Streamlit session state.
This can be used by the API server.
"""

from __future__ import annotations
import re
from typing import List, Dict, Any, Set, Optional

from view_helpers import (
    format_working_ingredients_markdown,
    format_steps_with_progress_markdown,
)

# --- Command help text ---

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


class SessionUpdate:
    """Encapsulates changes that should be applied to a session"""
    def __init__(self):
        self.new_current_step: Optional[int] = None
        self.strikes_to_add: Set[str] = set()
        self.strikes_to_remove: Set[str] = set()
        self.subs_to_add: Dict[str, str] = {}
        self.subs_to_remove: Set[str] = set()


def handle_user_command_headless(
    user_input: str,
    recipe_name: str,
    recipe_description: str,
    recipe_steps: List[str],
    recipe_ingredients: List[str],
    recipe_subs: Dict[str, str],
    ingredient_strikes: Set[str],
    current_step: int,
) -> Dict[str, Any]:
    """
    Headless command engine that doesn't depend on Streamlit.
    
    Returns:
        {
            "handled": bool,
            "reply_text": str,
            "advance_step": bool,
            "session_update": Optional[SessionUpdate]  # Changes to apply
        }
    """
    lower = user_input.lower().strip()
    reply_text = ""
    advance_step = False
    session_update = SessionUpdate()

    # --- 1. Full reset / clear commands ---
    start_over_triggers = [
        "start over", "restart", "start again", "reset recipe",
        "start this recipe over", "clear",
    ]
    if any(phrase == lower or phrase in lower for phrase in start_over_triggers):
        session_update.new_current_step = 0
        session_update.strikes_to_remove = ingredient_strikes.copy()
        reply_text = (
            f"Okay, I've reset your progress. "
            f"You're back at the beginning of {recipe_name}."
        )
        return {
            "handled": True,
            "reply_text": reply_text,
            "advance_step": False,
            "session_update": session_update,
        }

    # --- 2. Mark steps complete with "x N" ---
    step_x_match = re.match(r"^x\s+(\d+)\s*$", lower)
    if step_x_match:
        n = int(step_x_match.group(1))
        n = max(0, min(n, len(recipe_steps)))

        session_update.new_current_step = n

        lines: list[str] = []
        if n == 0:
            lines.append("Okay, I've reset your step progress. You're back at the beginning.")
        elif n >= len(recipe_steps):
            lines.append(
                f"Okay, I've marked all {len(recipe_steps)} steps as done. "
                "You've completed the recipe!"
            )
        else:
            lines.append(
                f"Got it. I've marked steps 1 through {n} as done. "
                f"You're now on step {n + 1}."
            )

        lines.append("")
        lines.append("Here are all the steps with your updated progress:")
        lines.append("")
        lines.extend(format_steps_with_progress_markdown(recipe_steps, n))

        reply_text = "\n".join(lines)
        return {
            "handled": True,
            "reply_text": reply_text,
            "advance_step": False,
            "session_update": session_update,
        }

    # --- 3. Simple next-step commands ("k", "ok", etc.) ---
    next_step_triggers = {
        "k", "ok", "okay", "next", "next step", "done", "finished",
    }
    if lower in next_step_triggers:
        if current_step < len(recipe_steps):
            next_idx = current_step
            step_num = next_idx + 1
            step_text = recipe_steps[next_idx]

            session_update.new_current_step = min(current_step + 1, len(recipe_steps))
            reply_text = f"Next step:\n\n{step_num}. {step_text}"
        else:
            reply_text = "You've already completed all the steps in this recipe."

        return {
            "handled": True,
            "reply_text": reply_text,
            "advance_step": False,
            "session_update": session_update,
        }

    # --- 4. Ingredient strike / unstrike commands ---
    stripped = lower.strip()

    strike_prefixes = [
        "strikethrough ", "strike ", "cross off ", "x ", "cross ", "86 ",
    ]
    unstrike_prefixes = [
        "unstrike ", "uncross ", "restore ",
    ]

    command_type = None
    target_name = ""

    for prefix in strike_prefixes:
        if stripped.startswith(prefix):
            command_type = "strike"
            target_name = stripped[len(prefix):].strip()
            break

    if command_type is None:
        for prefix in unstrike_prefixes:
            if stripped.startswith(prefix):
                command_type = "unstrike"
                target_name = stripped[len(prefix):].strip()
                break

    if command_type is not None:
        if not target_name:
            reply_text = "Tell me which ingredient to change, for example: `x oil` or `86 butter`."
            return {
                "handled": True,
                "reply_text": reply_text,
                "advance_step": False,
                "session_update": None,
            }

        # Find matching ingredients
        target_lower = target_name.lower()
        matching_keys = []
        for base_ing in recipe_ingredients:
            search_text = base_ing.lower()
            sub_name = recipe_subs.get(base_ing)
            if sub_name:
                search_text += " " + str(sub_name).lower()

            if target_lower in search_text:
                matching_keys.append(base_ing)

        if not matching_keys:
            lines: list[str] = []
            lines.append(
                f"I couldn't find an ingredient matching '{target_name}' in this recipe."
            )
            lines.append("Here are the ingredients I see:")
            lines.append("")
            lines.extend(
                format_working_ingredients_markdown(
                    recipe_ingredients,
                    recipe_subs,
                    ingredient_strikes,
                )
            )

            reply_text = "\n".join(lines)
            return {
                "handled": True,
                "reply_text": reply_text,
                "advance_step": False,
                "session_update": None,
            }

        # Apply strike or unstrike
        updated_strikes = ingredient_strikes.copy()
        if command_type == "strike":
            for key in matching_keys:
                updated_strikes.add(key)
                session_update.strikes_to_add.add(key)
        elif command_type == "unstrike":
            for key in matching_keys:
                updated_strikes.discard(key)
                session_update.strikes_to_remove.add(key)

        # Build response
        lines = []
        if command_type == "strike":
            lines.append("Got it. I updated your ingredient list. Here is the current version:")
        else:
            lines.append("Got it. I restored those ingredients. Here is the current list:")

        lines.append("")
        lines.extend(
            format_working_ingredients_markdown(
                recipe_ingredients,
                recipe_subs,
                updated_strikes,
            )
        )

        reply_text = "\n".join(lines)
        return {
            "handled": True,
            "reply_text": reply_text,
            "advance_step": False,
            "session_update": session_update,
        }

    # --- 5. Ingredient list command ---
    ingredient_triggers = [
        "ingredients", "ingredient list", "what are the ingredients",
        "show ingredients", "list the ingredients", "what do i need",
    ]

    if lower == "i" or any(phrase == lower or phrase in lower for phrase in ingredient_triggers):
        if recipe_ingredients:
            reply_lines = [
                "Here are the ingredients for this recipe (with substitutions applied):",
                "",
            ]
            reply_lines.extend(
                format_working_ingredients_markdown(
                    recipe_ingredients,
                    recipe_subs,
                    ingredient_strikes,
                )
            )
            reply_text = "\n".join(reply_lines)
        else:
            reply_text = "This recipe does not have a stored ingredient list yet."

        return {
            "handled": True,
            "reply_text": reply_text,
            "advance_step": False,
            "session_update": None,
        }

    # --- 6. Steps listing commands ---
    step_triggers = [
        "show all steps", "steps", "list steps", "show steps",
        "what are the steps", "s",
    ]
    if any(phrase == lower or phrase in lower for phrase in step_triggers):
        if recipe_steps:
            reply_lines = ["Here are all the steps for this recipe:", ""]
            reply_lines.extend(
                format_steps_with_progress_markdown(recipe_steps, current_step)
            )
            reply_text = "\n".join(reply_lines)
        else:
            reply_text = "This recipe does not have any steps defined yet."

        return {
            "handled": True,
            "reply_text": reply_text,
            "advance_step": False,
            "session_update": None,
        }

    # --- 7. "what" status command ---
    if lower == "what":
        lines: list[str] = []

        lines.append(f"### You are cooking: {recipe_name}")
        lines.append("")

        if recipe_ingredients:
            lines.append("#### Ingredients (with substitutions applied)")
            lines.append("")
            lines.extend(
                format_working_ingredients_markdown(
                    recipe_ingredients,
                    recipe_subs,
                    ingredient_strikes,
                )
            )
            lines.append("")

        if 0 <= current_step < len(recipe_steps):
            step_num = current_step + 1
            step_text = recipe_steps[current_step]
            lines.append("#### Current step")
            lines.append("")
            lines.append(f"{step_num}. {step_text}")
        else:
            lines.append("You've completed all the steps in this recipe.")

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(COMMANDS_CONDENSED)

        reply_text = "\n".join(lines)
        return {
            "handled": True,
            "reply_text": reply_text,
            "advance_step": False,
            "session_update": None,
        }

    # --- 8. Numeric-only input: show step ---
    num_match = re.match(r"^\s*(\d+)\s*$", user_input)
    if num_match:
        step_num = int(num_match.group(1))
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
            "session_update": None,
        }

    # Not handled
    return {
        "handled": False,
        "reply_text": "",
        "advance_step": False,
        "session_update": None,
    }