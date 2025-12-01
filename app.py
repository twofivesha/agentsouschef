import os
import json
from typing import List, Dict, Any

import streamlit as st
from openai import OpenAI

# --- Config & setup ---

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

st.set_page_config(
    page_title="Agent Sous Chef",
    layout="centered",
)

st.title("Agent Sous Chef")
st.write("Your tiny AI sous chef, guiding you step by step as you cook.")

if not OPENAI_API_KEY:
    st.error(
        "OPENAI_API_KEY environment variable is not set.\n\n"
        "Set it locally (env var or .streamlit/secrets.toml) and in your hosting platform."
    )
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# --- Recipe library (easy to extend later) ---

RECIPE_LIBRARY: Dict[str, Dict[str, Any]] = {
    "garlic_pasta": {
        "name": "Simple Garlic Pasta",
        "description": "Fast, simple, garlicky pasta for weeknights.",
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


def get_recipe_keys_and_labels():
    items = []
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
- If you are at the final step, and it is complete, use "advance_step": false and wrap up the recipe politely.
- Do not add any extra keys to the JSON.
- Do not include backticks or explanations outside the JSON.
"""


# --- Session state setup ---

if "messages" not in st.session_state:
    st.session_state.messages: List[Dict[str, str]] = []

if "current_step" not in st.session_state:
    st.session_state.current_step: int = 0

if "recipe_key" not in st.session_state:
    # Default to the first recipe in the library
    first_key = next(iter(RECIPE_LIBRARY.keys()))
    st.session_state.recipe_key: str = first_key


def reset_conversation_for_recipe(new_recipe_key: str):
    st.session_state.recipe_key = new_recipe_key
    st.session_state.current_step = 0
    st.session_state.messages = []
    recipe = RECIPE_LIBRARY[new_recipe_key]
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": (
                f"Now cooking: {recipe['name']}.\n\n"
                f"{recipe['description']}\n\n"
                "When you are ready, tell me what you have done so far or ask to start from the first step."
            ),
        }
    )


# Ensure we have an initial system-style message if messages are empty
if not st.session_state.messages:
    reset_conversation_for_recipe(st.session_state.recipe_key)


# --- Sidebar: recipe choice and visualizer ---

st.sidebar.header("Agent Sous Chef")

recipe_items = get_recipe_keys_and_labels()
recipe_labels = [label for _, label in recipe_items]

# Find current recipe index for the selectbox
current_recipe_key = st.session_state.recipe_key
current_index = next(
    (i for i, (key, _) in enumerate(recipe_items) if key == current_recipe_key),
    0,
)

selected_label = st.sidebar.selectbox(
    "Choose a recipe",
    recipe_labels,
    index=current_index,
)

# Map label back to key
selected_key = next(
    key for key, label in recipe_items if label == selected_label
)

if selected_key != st.session_state.recipe_key:
    reset_conversation_for_recipe(selected_key)

active_recipe = RECIPE_LIBRARY[st.session_state.recipe_key]
recipe_name = active_recipe["name"]
recipe_description = active_recipe["description"]
recipe_steps: List[str] = active_recipe["steps"]

st.sidebar.subheader(f"Recipe: {recipe_name}")
st.sidebar.caption(recipe_description)

st.sidebar.markdown("Steps:")
for i, step in enumerate(recipe_steps):
    if i < st.session_state.current_step:
        prefix = "[x]"
    elif i == st.session_state.current_step:
        prefix = "->"
    else:
        prefix = "[ ]"
    st.sidebar.write(f"{prefix} {i+1}. {step}")

if st.sidebar.button("Restart this recipe"):
    reset_conversation_for_recipe(st.session_state.recipe_key)

st.sidebar.caption("MVP: multiple recipes, step tracking, and LLM-guided progress.")


# --- Display chat history ---

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# --- Core LLM call helper ---

def call_agent_sous_chef(user_input: str) -> Dict[str, Any]:
    current_step_index = st.session_state.current_step
    steps = recipe_steps

    # Clamp current_step_index to valid range
    if current_step_index < 0:
        current_step_index = 0
    if current_step_index >= len(steps):
        current_step_index = len(steps) - 1

    current_step_text = steps[current_step_index]
    completed_steps = steps[:current_step_index]
    remaining_steps = steps[current_step_index + 1 :]

    steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))

    user_context = f"""
User message: {user_input}

Active recipe: {recipe_name}
Recipe description: {recipe_description}

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

    # Try to parse the JSON the model should return
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
        # Normalize by stripping punctuation so "ok!", "ok.", etc. still match.
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

    # Call LLM
    try:
        result = call_agent_sous_chef(user_input)
        reply_text = result["reply"]
        advance_step = result["advance_step"]
    except Exception as e:
        reply_text = f"Error calling the AI model: {e}"
        advance_step = False

    # Advance step if LLM says so and we are not past the last step
    if advance_step and st.session_state.current_step < len(recipe_steps) - 1:
        st.session_state.current_step += 1

    # Append and display assistant message
    st.session_state.messages.append({"role": "assistant", "content": reply_text})
    with st.chat_message("assistant"):
        st.markdown(reply_text)