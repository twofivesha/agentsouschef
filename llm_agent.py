import json
from typing import List, Dict, Any
from openai import OpenAI


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
- If the user is asking for ingredient substitutions, suggest 1–3 simple alternatives and set "advance_step": false.
- If you are at the final step, and it is complete, use "advance_step": false and wrap up the recipe politely.
- Do not add any extra keys to the JSON.
- Do not include backticks or explanations outside the JSON.
"""


def call_agent_sous_chef(
    client: OpenAI,
    user_input: str,
    recipe_name: str,
    recipe_description: str,
    recipe_steps: List[str],
    recipe_ingredients: List[str],
    recipe_subs: Dict[str, str],
    current_step_index: int,
) -> Dict[str, Any]:
    """
    Core LLM call helper. Pure function: no Streamlit inside,
    and receives all required context via arguments.
    """

    steps = recipe_steps

    # Clamp step index
    if current_step_index < 0:
        current_step_index = 0

    if steps:
        if current_step_index >= len(steps):
            current_step_index = len(steps) - 1

        current_step_text = steps[current_step_index]
        completed_steps = steps[:current_step_index]
        remaining_steps = steps[current_step_index + 1:]
        steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))

    else:
        current_step_text = "No steps defined."
        completed_steps = []
        remaining_steps = []
        steps_text = "None"

    # Compose ingredients block
    if recipe_ingredients:
        ingredient_lines = []
        for ing in recipe_ingredients:
            sub_name = recipe_subs.get(ing)
            if sub_name:
                ingredient_lines.append(f"- {ing} (substitute: {sub_name})")
            else:
                ingredient_lines.append(f"- {ing}")
        ingredients_block = "\n".join(ingredient_lines)
    else:
        ingredients_block = "None"

    # Format context for the LLM
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

    # Call the OpenAI client
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTIONS},
            {"role": "user", "content": user_context},
        ],
        max_tokens=300,
    )

    raw = completion.choices[0].message.content.strip()

    # Try to parse the JSON
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Response JSON is not an object")

        reply = str(data.get("reply", "")).strip()
        advance_step = bool(data.get("advance_step", False))

        if not reply:
            reply = "I had trouble generating a reply. Please tell me again what you did."

        return {
            "reply": reply,
            "advance_step": advance_step,
            "raw": raw,
        }

    except Exception:
        # Fallback naive advancing
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