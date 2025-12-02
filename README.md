# 🧑‍🍳 Agent Sous Chef
*A conversational, AI-assisted cooking companion.*

Agent Sous Chef is an interactive recipe assistant that lets a user cook step-by-step through natural language. 
It supports substitutions, ingredient tracking, step progression, recipe picking, and fuzzy conversational input — all backed by OpenAI’s models and a modular command engine.

This project started as a Streamlit MVP and is organized for future expansion (FastAPI backend, Next.js UI, voice mode, semantic recipe search, etc.).

---

## ✨ Features

### 🔹 Natural Language Cooking
Talk to the assistant like you would to a real sous chef:

- “What’s the next step?”
- “Done.”
- “Sub olive oil for butter.”
- “x 3” → mark steps 1–3 done
- “What do I do now?”

### 🔹 Smart Ingredient List
- Tracks substitutions
- Tracks crossed-off items
- Strikethrough support
- Automatically stays up-to-date as you cook

### 🔹 Step Guidance
- Tracks current step
- Moves forward when you say “ok”, “done”, etc.
- Lets you preview any step by number
- Displays a full list with progress indicators

### 🔹 Recipe Picker
Pick a recipe by:

- Typing `pick`
- Filtering via keywords (e.g., “eggs”)
- Selecting by number

### 🔹 Command Engine (Modular)
All logic lives in `commands.py` — Streamlit is just the UI layer.
This means the same engine could power:

- A mobile app
- A web backend
- A voice assistant
- SMS bot
- Discord bot
- Anything you want later

### 🔹 LLM Engine (Modular)
All LLM calls live in `llm_agent.py`, separate from UI code.

---

## 🗂 Project Structure

```
agentsouschef/
│
├─ app.py                    # Streamlit UI
│
├─ commands.py               # Command parser + engine (ingredient ops, steps, pick logic)
├─ llm_agent.py              # OpenAI calls + system prompt
├─ recipes.py                # Recipe library + lookup helpers
├─ view_helpers.py           # Formatting helpers for UI
│
├─ README.md                 # This file
└─ .streamlit/               # Streamlit configs (optional)
```

This layout intentionally keeps cooking logic separate from UI/LLM layers.

---

## 🚀 Running Locally

### 1. Clone the repo
```
git clone https://github.com/yourusername/agentsouschef.git
cd agentsouschef
```

### 2. Install dependencies (with uv)
```
uv sync
```

### 3. Add your OpenAI API key  
Create `.streamlit/secrets.toml`:

```
OPENAI_API_KEY="sk-..."
```

Or export it:

```
export OPENAI_API_KEY="sk-..."
```

### 4. Start the Streamlit app
```
streamlit run app.py
```

Then open http://localhost:8501.

---

## 🧠 Commands (Chat)

```
i      — show working ingredients  
s      — show all steps  
x      — cross off ingredient (x oil) or mark steps done (x 3 → marks steps 1–3)  
k      — ok / advance to next step  
what   — show current recipe status  
clear  — restart recipe  
pick   — choose a recipe by chat
```

Commands are intentionally simple so the LLM can handle everything else.

---

## 🔮 Roadmap / Ideas

These are all easy next steps based on the architecture:

- 🔊 Voice input → STT → command engine → TTS output  
- 📱 FastAPI backend + React/Next.js frontend  
- 🧭 Semantic recipe search (“something with eggs”, “vegetarian pasta”)  
- 🍳 Premium recipe packs for monetization

---

## 🤝 Contributing

Feel free to submit issues or PRs 

---

## 📜 License

MIT License. 
