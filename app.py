import os
import json
from typing import List, Dict, Any


import re
import streamlit as st
from openai import OpenAI

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

# --- Config & setup ---

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

st.set_page_config(
    page_title="Agent Sous Chef",
    layout="centered",
)

st.title("Agent Sous Chef")
st.write("Your tiny AI sous chef, guiding you step by step as you cook.")
st.markdown(COMMANDS_LONG_MARKDOWN)

if not OPENAI_API_KEY:
    st.error(
        "OPENAI_API_KEY environment variable is not set.\n\n"
        "Set it locally (env var or .streamlit/secrets.toml) and in your hosting platform."
    )
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# --- Recipe library (with ingredients) ---

RECIPE_LIBRARY: Dict[str, Dict[str, Any]] = {
    "garlic_pasta": {
        "name": "Simple Garlic Pasta",
        "description": "Fast, simple, garlicky pasta for weeknights.",
        "ingredients": [
            "8 ounces dry spaghetti or other pasta",
            "Salt for the pasta water",
            "3 tablespoons olive oil",
            "3–4 cloves garlic, minced",
            "Freshly ground black pepper",
            "1/2 cup reserved pasta cooking water (as needed)",
            "Grated Parmesan or Pecorino cheese for serving",
        ],
        "steps": [
            "Bring a large pot of salted water to a boil.",
            "Add pasta and cook until just shy of al dente (about 1 minute less than package instructions).",
            "While pasta cooks, gently warm olive oil in a pan over low heat.",
            "Add minced garlic to the oil and cook gently until fragrant, not browned.",
            "Reserve a cup of pasta water, then drain the pasta.",
            "Toss pasta with the garlic oil, a splash of pasta water, salt, and pepper.",
            "Adjust with more pasta water if needed, then finish with cheese and serve.",
        ],
    },
    "scrambled_eggs": {
        "name": "Soft Scrambled Eggs",
        "description": "Gentle, creamy scrambled eggs on the stove.",
        "ingredients": [
            "3 large eggs",
            "Salt",
            "1–2 teaspoons butter",
            "Freshly ground black pepper",
            "Optional: 1–2 tablespoons milk or cream",
        ],
        "steps": [
            "Crack eggs into a bowl, add a pinch of salt, and whisk until fully combined.",
            "Heat a nonstick pan over low to medium-low heat and add a small knob of butter.",
            "Pour the eggs into the pan and let them sit for a few seconds until they just start to set at the edges.",
            "Use a spatula to gently push the eggs from the edges toward the center, forming soft curds.",
            "Continue slowly pushing and folding the eggs until they are mostly set but still slightly glossy and soft.",
            "Remove the pan from the heat; the eggs will finish cooking off the heat. Taste and adjust seasoning, then serve.",
        ],
    },
}


def get_recipe_keys_and_labels() -> List[tuple[str, str]]:
    items: List[tuple[str, str]] = []
    for key, data in RECIPE_LIBRARY.items():
        label = data["name"]
        items.append((key, label))
    return items


SYSTEM_INSTRUCTIONS = """
You are Agent Sous Chef — a friendly, concise AI cooking assistant.
You help users cook step by step with clarity and calm encouragement.

You must always respond as a strict JSON object with two keys:
- "reply": a short natural-language message to the user
- "advance_step": a boolean (true or false) indicating whether the app should move to the next step

Format example:
{
  "reply": "Some helpful message to the user.",
  "advance_step": false
}

Rules:
- Speak clearly and briefly.
- Focus on the current step unless it is clearly completed.
- If the user says things like "done", "finished", or clearly describes completing the current step, set "advance_step" to true.
- If the user asks "what is next" or similar, and the current step seems complete, set "advance_step" to true.
- If the user is asking for ingredient substitutions, suggest 1–3 simple alternatives and set "advance_step" to false.
- If you are at the final step, and it is complete, use "advance_step": false and wrap up the recipe politely.
- Do not add any extra keys to the JSON.
- Do not include backticks or explanations outside the JSON.
"""

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

        for ing in recipe_ingredients:
            sub_name = recipe_subs.get(ing)
            if sub_name:
                display = f"{sub_name} (instead of {ing})"
            else:
                display = ing

            # If this ingredient has been marked for strikethrough, render it with ~~...~~
            if ing in strikes_for_recipe:
                st.write(f"- ~~{display}~~")
            else:
                st.write(f"- {display}")

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


# --- Core LLM call helper ---

def call_agent_sous_chef(user_input: str) -> Dict[str, Any]:
    current_step_index = st.session_state.current_step
    steps = recipe_steps

    # Clamp index
    if current_step_index < 0:
        current_step_index = 0
    if current_step_index >= len(steps):
        current_step_index = len(steps) - 1

    current_step_text = steps[current_step_index]
    completed_steps = steps[:current_step_index]
    remaining_steps = steps[current_step_index + 1 :]

    steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))

    # Compose ingredient lines with substitutions
    if recipe_ingredients:
        ingredient_lines = []
        for ing in recipe_ingredients:
            sub_name = recipe_subs.get(ing)
            if sub_name:
                ingredient_lines.append(f"- {ing} (substitute: {sub_name})")
            else:
                ingredient_lines.append(f"- {ing}")
        ingredients_block = chr(10).join(ingredient_lines)
    else:
        ingredients_block = "None"

    user_context = f"""
User message: {user_input}

Active recipe: {recipe_name}
Recipe description: {recipe_description}

Ingredients:
{ingredients_block}

All steps:
{steps_text}

Current step index (1-based): {current_step_index + 1}
Current step text: {current_step_text}

Completed steps:
{chr(10).join(f"- {s}" for s in completed_steps) if completed_steps else "None"}

Remaining steps:
{chr(10).join(f"- {s}" for s in remaining_steps) if remaining_steps else "None"}
"""

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTIONS},
            {"role": "user", "content": user_context},
        ],
        max_tokens=300,
    )

    raw = completion.choices[0].message.content.strip()

    # Try to parse JSON response
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Response JSON is not an object")
        reply = str(data.get("reply", "")).strip()
        advance_step = bool(data.get("advance_step", False))
        if not reply:
            reply = "I had trouble generating a reply. Please tell me again what you did."
        return {"reply": reply, "advance_step": advance_step, "raw": raw}
    except Exception:
        # Fallback: treat entire response as text, simple naive advancing
        lower = user_input.lower()
        clean = "".join(ch for ch in lower if ch.isalnum() or ch.isspace())

        advance_triggers = [
            "done",
            "finished",
            "next",
            "next step",
            "whats next",
            "what is next",
            "ok",
            "okay",
            "k",
            "kk",
        ]

        naive_advance = any(
            trigger == clean or trigger in clean for trigger in advance_triggers
        )

        return {
            "reply": raw,
            "advance_step": naive_advance,
            "raw": raw,
        }


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

    # Handle full reset commands: "restart", "clear", "start over", etc.
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
            # Fully reset as if freshly selecting a recipe
            reset_conversation_for_recipe(current_recipe)
        st.rerun()

    # Handle explicit ingredient substitution commands like
    # "sub white pepper for black pepper" or "substitute white pepper for black pepper".
    # We also support multiple substitutions in one message, e.g.:
    # "sub oil for butter and sub white pepper for black pepper".
    sub_pattern = r"\bsub(?:stitute)?\s+(?P<sub>[^,;.]+?)\s+for\s+(?P<orig>[^,;.]+)"
    matches = list(re.finditer(sub_pattern, lower))

    if matches:
        subs_for_recipe = st.session_state.ingredient_subs.get(st.session_state.recipe_key, {})
        replacements: list[tuple[str, str]] = []

        for m in matches:
            sub_name = m.group("sub").strip()
            orig_name = m.group("orig").strip()

            # Try to match this original against the current recipe ingredients
            for ing in recipe_ingredients:
                ing_lower = ing.lower()
                if orig_name in ing_lower:
                    subs_for_recipe[ing] = sub_name
                    replacements.append((ing, sub_name))

        if replacements:
            st.session_state.ingredient_subs[st.session_state.recipe_key] = subs_for_recipe
            # Refresh local view for this run so downstream code sees updated subs
            recipe_subs = subs_for_recipe

            # Build a full "working ingredients" list for the reply,
            # including substitutions and any existing strikethroughs.
            strikes_for_recipe = st.session_state.ingredient_strikes.get(
                st.session_state.recipe_key, set()
            )

            lines = [
                "Got it. I will use those substitutions. Here is your updated ingredient list:",
                "",
            ]
            for ing in recipe_ingredients:
                sub_name = recipe_subs.get(ing)
                if sub_name:
                    display = f"{sub_name} (instead of {ing})"
                else:
                    display = ing

                if ing in strikes_for_recipe:
                    lines.append(f"- ~~{display}~~")
                else:
                    lines.append(f"- {display}")

            reply_text = "\n".join(lines)
        else:
            # Could not find the ingredient(s) to substitute
            lines = [
                "I couldn't find that ingredient in this recipe.",
                "Here are the ingredients I see:",
                "",
            ]
            lines.extend(f"- {ing}" for ing in recipe_ingredients)
            reply_text = "\n".join(lines)

        advance_step = False
        handled = True

    # Handle "x N" to mark steps 1..N as completed (and move current step to N)
    # Example: "x 3" will treat steps 1–3 as done and set the current step index to 3.
    if not handled:
        step_x_match = re.match(r"^x\s+(\d+)\s*$", lower)
        if step_x_match:
            n = int(step_x_match.group(1))
            # Clamp within valid range: 0..len(recipe_steps)
            if n < 0:
                n = 0
            if n > len(recipe_steps):
                n = len(recipe_steps)

            st.session_state.current_step = n

            # Build a full steps list reflecting the new progress.
            # Steps with index < current_step are considered completed and shown with strikethrough.
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
            for idx, step in enumerate(recipe_steps):
                if idx < current_idx:
                    lines.append(f"{idx + 1}. ~~{step}~~")
                else:
                    lines.append(f"{idx + 1}. {step}")

            reply_text = "\n".join(lines)

            advance_step = False
            handled = True

    # Handle "pick" to allow choosing a recipe via chat
    if not handled and lower == "pick":
        items = get_recipe_keys_and_labels()
        lines = ["Available recipes:", ""]
        for idx, (key, label) in enumerate(items, start=1):
            lines.append(f"{idx}. {label}")
        lines.append("")
        lines.append("Reply with a number (e.g., 1 or 2) to pick a recipe.")

        st.session_state.pending_recipe_pick = True
        reply_text = "\n".join(lines)
        advance_step = False
        handled = True

    # While in "pick" mode, treat non-numeric input as a filter over recipe titles.
    # Example:
    #   pick
    #   eggs
    # will show only recipes whose titles contain "eggs", keeping their original numbers.
    if not handled and st.session_state.get("pending_recipe_pick", False):
        # If the input is not a plain number, interpret it as a filter term.
        if not re.match(r"^\s*\d+\s*$", user_input):
            query = lower.strip()
            items = get_recipe_keys_and_labels()
            lines: list[str] = []

            # Filter recipes whose names contain the query (case-insensitive),
            # but KEEP their original index numbers so selection remains consistent.
            matching_indices: list[int] = []
            for idx, (key, label) in enumerate(items, start=1):
                if query in label.lower():
                    matching_indices.append(idx)

            if matching_indices:
                lines.append(f"Recipes matching '{query}':")
                lines.append("")
                for idx, (key, label) in enumerate(items, start=1):
                    if idx in matching_indices:
                        lines.append(f"{idx}. {label}")
                lines.append("")
                lines.append(
                    "Reply with a number to pick one of these recipes, "
                    "or type another keyword to filter again."
                )
            else:
                # No matches; fall back to showing all recipes again.
                lines.append(
                    f"I couldn't find any recipes matching '{query}'. "
                    "Here are all available recipes:"
                )
                lines.append("")
                for idx, (key, label) in enumerate(items, start=1):
                    lines.append(f"{idx}. {label}")
                lines.append("")
                lines.append(
                    "Reply with a number (e.g., 1 or 2) to pick a recipe, "
                    "or type another keyword to filter."
                )

            reply_text = "\n".join(lines)
            advance_step = False
            handled = True

    # Handle numeric-only input:
    # - If pending_recipe_pick is True: treat as "pick recipe #N"
    # - Otherwise: show that specific step number
    if not handled:
        # Match a string that is just a number (optionally surrounded by whitespace)
        num_match = re.match(r"^\s*(\d+)\s*$", user_input)
        if num_match:
            n = int(num_match.group(1))

            if st.session_state.get("pending_recipe_pick", False):
                items = get_recipe_keys_and_labels()
                if 1 <= n <= len(items):
                    new_key, new_label = items[n - 1]
                    reset_conversation_for_recipe(new_key)
                    # Full reset and rerun, just like choosing from the dropdown.
                    st.rerun()
                else:
                    reply_text = f"There are only {len(items)} recipes. Please pick a number between 1 and {len(items)}."
                    # Keep pending_recipe_pick = True so the user can try again.
                    advance_step = False
                    handled = True
            else:
                step_num = n
                step_index = step_num - 1  # convert to 0-based index

                if 0 <= step_index < len(recipe_steps):
                    step_text = recipe_steps[step_index]
                    reply_text = f"{step_num}. {step_text}"
                else:
                    reply_text = f"This recipe only has {len(recipe_steps)} steps."

                advance_step = False
                handled = True

    # Handle explicit strike / unstrike commands for ingredients, e.g.:
    # "strikethrough butter", "strike butter", "cross off butter",
    # "unstrike butter", "uncross butter", or "restore butter".
    if not handled:
        stripped = lower.strip()
        target_name: str | None = None
        mode: str | None = None  # "strike" or "unstrike"

        if stripped.startswith("strikethrough "):
            mode = "strike"
            target_name = stripped[len("strikethrough ") :].strip()
        elif stripped.startswith("strike "):
            mode = "strike"
            target_name = stripped[len("strike ") :].strip()
        elif stripped.startswith("cross off "):
            mode = "strike"
            target_name = stripped[len("cross off ") :].strip()
        elif stripped.startswith("x "):
            mode = "strike"
            target_name = stripped[len("x ") :].strip()
        elif stripped.startswith("cross "):
            mode = "strike"
            target_name = stripped[len("cross ") :].strip()
        elif stripped.startswith("86 "):
            mode = "strike"
            target_name = stripped[len("86 ") :].strip()
        elif stripped.startswith("unstrike "):
            mode = "unstrike"
            target_name = stripped[len("unstrike ") :].strip()
        elif stripped.startswith("uncross "):
            mode = "unstrike"
            target_name = stripped[len("uncross ") :].strip()
        elif stripped.startswith("restore "):
            mode = "unstrike"
            target_name = stripped[len("restore ") :].strip()

        if mode and target_name:
            strikes_for_recipe = st.session_state.ingredient_strikes.get(st.session_state.recipe_key, set())
            matches_found: list[str] = []

            # Match the target against the *working* ingredient text:
            # original ingredient plus any substitution name, case-insensitive.
            for ing in recipe_ingredients:
                ing_lower = ing.lower()
                sub_name = recipe_subs.get(ing)
                # Build a combined search string: original text + substitute (if any)
                search_text = ing_lower
                if sub_name:
                    search_text += " " + sub_name.lower()

                if target_name in search_text:
                    if mode == "strike":
                        strikes_for_recipe.add(ing)
                    else:  # unstrike
                        strikes_for_recipe.discard(ing)
                    matches_found.append(ing)

            # Persist updated strikes (even if the set is now empty)
            st.session_state.ingredient_strikes[st.session_state.recipe_key] = strikes_for_recipe

            if matches_found:
                # Build a full "working ingredients" list for the reply,
                # including substitutions and any current strikethroughs.
                lines = [
                    "Got it. I updated your ingredient list. Here is the current version:",
                    "",
                ]
                for ing in recipe_ingredients:
                    sub_name = recipe_subs.get(ing)
                    if sub_name:
                        display = f"{sub_name} (instead of {ing})"
                    else:
                        display = ing

                    if ing in strikes_for_recipe:
                        lines.append(f"- ~~{display}~~")
                    else:
                        lines.append(f"- {display}")

                reply_text = "\n".join(lines)
            else:
                lines = [
                    f"I couldn't find an ingredient matching '{target_name}' in this recipe.",
                    "Here are the ingredients I see:",
                    "",
                ]
                lines.extend(f"- {ing}" for ing in recipe_ingredients)
                reply_text = "\n".join(lines)

            advance_step = False
            handled = True

    # Handle explicit step listing commands like "show all steps" or "steps"
    if not handled:
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
                for idx, step in enumerate(recipe_steps):
                    # Steps with index < current_step are considered completed
                    if idx < current_idx:
                        # Strikethrough to indicate completion
                        reply_lines.append(f"{idx + 1}. ~~{step}~~")
                    else:
                        reply_lines.append(f"{idx + 1}. {step}")
                reply_text = "\n".join(reply_lines)
            else:
                reply_text = "This recipe does not have any steps defined yet."
            advance_step = False
            handled = True

    # Ingredient list direct handling (only if not already handled)
    if not handled:
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
                reply_lines = ["Here are the ingredients for this recipe (with substitutions applied):", ""]
                # Get any strike marks for this recipe so chat output matches the UI
                strikes_for_recipe = st.session_state.ingredient_strikes.get(st.session_state.recipe_key, set())

                for ing in recipe_ingredients:
                    sub_name = recipe_subs.get(ing)
                    if sub_name:
                        display = f"{sub_name} (instead of {ing})"
                    else:
                        display = ing

                    if ing in strikes_for_recipe:
                        reply_lines.append(f"- ~~{display}~~")
                    else:
                        reply_lines.append(f"- {display}")
                reply_text = "\n".join(reply_lines)
            else:
                reply_text = "This recipe does not have a stored ingredient list yet."
            advance_step = False
            handled = True

    # Handle "what" as a status command: show recipe name, working ingredients, and current step
    if not handled and lower == "what":
        lines: list[str] = []

        # Recipe name
        lines.append(f"You are cooking: {recipe_name}")
        lines.append("")

        # Ingredients section (working list with subs and strikes)
        if recipe_ingredients:
            lines.append("Ingredients (with substitutions applied):")
            lines.append("")
            strikes_for_recipe = st.session_state.ingredient_strikes.get(
                st.session_state.recipe_key, set()
            )

            for ing in recipe_ingredients:
                sub_name = recipe_subs.get(ing)
                if sub_name:
                    display = f"{sub_name} (instead of {ing})"
                else:
                    display = ing

                if ing in strikes_for_recipe:
                    lines.append(f"- ~~{display}~~")
                else:
                    lines.append(f"- {display}")

            lines.append("")

        # Current step section
        if 0 <= st.session_state.current_step < len(recipe_steps):
            step_num = st.session_state.current_step + 1
            step_text = recipe_steps[st.session_state.current_step]
            lines.append("Current step:")
            lines.append("")
            lines.append(f"{step_num}. {step_text}")
        else:
            lines.append("You’ve completed all the steps in this recipe.")

        # Append condensed command list at the end
        lines.append("")
        lines.append(COMMANDS_CONDENSED)

        reply_text = "\n".join(lines)
        advance_step = False
        handled = True

    # If still not handled, fall back to the LLM
    if not handled:
        try:
            result = call_agent_sous_chef(user_input)
            reply_text = result["reply"]
            advance_step = result["advance_step"]
        except Exception as e:
            reply_text = f"Error calling the AI model: {e}"
            advance_step = False

        # Override: simple confirmations always advance
        clean = "".join(ch for ch in lower if ch.isalnum() or ch.isspace())
        override_triggers = [
            "done",
            "finished",
            "next",
            "next step",
            "whats next",
            "what is next",
            "ok",
            "okay",
            "k",
            "kk",
        ]
        if any(trigger == clean or trigger in clean for trigger in override_triggers):
            advance_step = True

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