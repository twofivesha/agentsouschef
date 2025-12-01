import os
from typing import List, Dict

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
        "Set it locally (export/openenv) and later in DigitalOcean App Platform."
    )
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# --- One simple recipe for the MVP ---

RECIPE_NAME = "Simple Garlic Pasta"
RECIPE_STEPS: List[str] = [
    "Bring a large pot of salted water to a boil.",
    "Add pasta and cook until just shy of al dente (about 1 minute less than package instructions).",
    "While pasta cooks, gently warm olive oil in a pan over low heat.",
    "Add minced garlic to the oil and cook gently until fragrant, not browned.",
    "Reserve a cup of pasta water, then drain the pasta.",
    "Toss pasta with the garlic oil, a splash of pasta water, salt, and pepper.",
    "Adjust with more pasta water if needed, then finish with cheese and serve.",
]

SYSTEM_INSTRUCTIONS = f"""
You are Agent Sous Chef — a friendly, concise AI cooking assistant.
You help users cook step-by-step with clarity and calm encouragement.

The user is cooking the recipe: {RECIPE_NAME}.

Here are the steps:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(RECIPE_STEPS))}

Guidelines:
- Speak clearly and briefly.
- Focus on the current step unless the user indicates it is done.
- If they say something like "done", "finished", or "what's next", move to the next step.
- Provide helpful cooking cues (texture, smell, color) when relevant.
- If we are at the final step, wrap up the recipe nicely.
"""


# --- Session state ---

if "messages" not in st.session_state:
    st.session_state.messages: List[Dict[str, str]] = []

if "current_step" not in st.session_state:
    st.session_state.current_step: int = 0


# --- Sidebar: recipe visualizer ---

st.sidebar.header("Agent Sous Chef")
st.sidebar.subheader(f"Recipe: {RECIPE_NAME}")

st.sidebar.markdown("Steps:")
for i, step in enumerate(RECIPE_STEPS):
    if i < st.session_state.current_step:
        prefix = "[x]"
    elif i == st.session_state.current_step:
        prefix = "->"
    else:
        prefix = "[ ]"
    st.sidebar.write(f"{prefix} {i+1}. {step}")

if st.sidebar.button("Restart Recipe"):
    st.session_state.current_step = 0
    st.session_state.messages.append(
        {"role": "assistant", "content": "Resetting the recipe from the beginning."}
    )

st.sidebar.caption("Agent Sous Chef (MVP): one recipe, simple step tracking, AI guidance.")


# --- Display chat history ---

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# --- Chat input ---

user_input = st.chat_input("Talk to Agent Sous Chef…")

if user_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Determine if user wants to advance
    lower = user_input.lower()
    advance_words = ["done", "finished", "completed", "next", "what's next", "what is next", "ok", "okay"]
    should_advance = any(word in lower for word in advance_words)

    if should_advance and st.session_state.current_step < len(RECIPE_STEPS) - 1:
        st.session_state.current_step += 1

    # Build context for model
    current_index = st.session_state.current_step
    current_step_text = RECIPE_STEPS[current_index]

    completed_steps = RECIPE_STEPS[:current_index]
    remaining_steps = RECIPE_STEPS[current_index + 1 :]

    user_context = f"""
User message: {user_input}

Current step number: {current_index + 1}
Current step text: {current_step_text}

Completed steps:
{chr(10).join(f"- {s}" for s in completed_steps) if completed_steps else "None"}

Remaining steps:
{chr(10).join(f"- {s}" for s in remaining_steps) if remaining_steps else "None"}
"""

    # Call LLM
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                {"role": "user", "content": user_context},
            ],
            max_tokens=250,
        )
        reply = completion.choices[0].message.content.strip()

    except Exception as e:
        reply = f"Error calling the AI model: {e}"

    st.session_state.messages.append({"role": "assistant", "content": reply})

    with st.chat_message("assistant"):
        st.markdown(reply)