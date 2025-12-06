# api_server.py
"""
Clean FastAPI server using the core command engine.
No UI dependencies - just pure API logic.
"""

from typing import Dict, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import from wherever your files are
# Adjust these imports based on your structure
from recipes import RECIPE_LIBRARY
from llm_agent import call_agent_sous_chef

# Import the clean core
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "core"))
from commands import CookingState, handle_command


app = FastAPI(title="Agent Sous Chef API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Session Storage ----------

class Session:
    def __init__(self, recipe_key: str):
        self.cooking_state = CookingState(recipe_key=recipe_key)
        self.messages: list = []


SESSIONS: Dict[str, Session] = {}


# ---------- Request/Response Models ----------

class StartRequest(BaseModel):
    recipe_key: str


class StartResponse(BaseModel):
    session_id: str
    recipe_name: str
    reply: str


class MessageRequest(BaseModel):
    message: str


class MessageResponse(BaseModel):
    reply: str
    current_step: int
    total_steps: int
    ingredients: list[str]
    strikes: list[str]
    substitutions: dict[str, str]


# ---------- Helpers ----------

def get_session(session_id: str) -> Session:
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    return SESSIONS[session_id]


def get_recipe(recipe_key: str) -> dict:
    if recipe_key not in RECIPE_LIBRARY:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return RECIPE_LIBRARY[recipe_key]


# ---------- Endpoints ----------

@app.get("/")
def root():
    return {
        "name": "Agent Sous Chef API",
        "version": "2.0.0",
        "status": "healthy"
    }


@app.get("/recipes")
def list_recipes():
    """List all available recipes"""
    return [
        {
            "key": key,
            "name": recipe["name"],
            "description": recipe.get("description", "")
        }
        for key, recipe in RECIPE_LIBRARY.items()
    ]


@app.post("/session/start", response_model=StartResponse)
def start_session(req: StartRequest):
    """Start a new cooking session"""
    recipe = get_recipe(req.recipe_key)
    
    session_id = str(uuid4())
    session = Session(recipe_key=req.recipe_key)
    
    reply = f"Let's cook {recipe['name']}! Ask for 'ingredients', 'steps', or say 'next' to begin."
    
    session.messages.append({"role": "assistant", "content": reply})
    SESSIONS[session_id] = session
    
    return StartResponse(
        session_id=session_id,
        recipe_name=recipe["name"],
        reply=reply
    )


@app.post("/session/{session_id}/message", response_model=MessageResponse)
def send_message(session_id: str, req: MessageRequest):
    """Send a message in a cooking session"""
    session = get_session(session_id)
    recipe = get_recipe(session.cooking_state.recipe_key)
    
    user_msg = req.message.strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    session.messages.append({"role": "user", "content": user_msg})
    
    # Try command engine first
    result = handle_command(
        user_input=user_msg,
        state=session.cooking_state,
        recipe_name=recipe["name"],
        ingredients=recipe.get("ingredients", []),
        steps=recipe.get("steps", [])
    )
    
    if result.handled:
        # Command was handled
        if result.new_state:
            session.cooking_state = result.new_state
        reply = result.reply
    else:
        # Fall back to AI
        try:
            ai_result = call_agent_sous_chef(
                user_input=user_msg,
                recipe_name=recipe["name"],
                recipe_description=recipe.get("description", ""),
                recipe_steps=recipe.get("steps", []),
                recipe_ingredients=recipe.get("ingredients", []),
                recipe_subs=session.cooking_state.ingredient_subs,
                current_step_index=session.cooking_state.current_step,
            )
            reply = ai_result["reply"]
            
            # Apply step advancement if AI suggested it
            if ai_result.get("advance_step") and session.cooking_state.current_step < len(recipe["steps"]):
                session.cooking_state.current_step += 1
                
        except Exception as e:
            reply = f"Error: {str(e)}"
    
    session.messages.append({"role": "assistant", "content": reply})
    
    return MessageResponse(
        reply=reply,
        current_step=session.cooking_state.current_step,
        total_steps=len(recipe.get("steps", [])),
        ingredients=recipe.get("ingredients", []),
        strikes=list(session.cooking_state.ingredient_strikes),
        substitutions=session.cooking_state.ingredient_subs
    )


@app.get("/session/{session_id}")
def get_session_info(session_id: str):
    """Get current session state"""
    session = get_session(session_id)
    recipe = get_recipe(session.cooking_state.recipe_key)
    
    return {
        "session_id": session_id,
        "recipe_key": session.cooking_state.recipe_key,
        "recipe_name": recipe["name"],
        "current_step": session.cooking_state.current_step,
        "total_steps": len(recipe.get("steps", [])),
        "message_count": len(session.messages)
    }


@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    """End a cooking session"""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    del SESSIONS[session_id]
    return {"message": "Session deleted"}


@app.get("/sessions")
def list_sessions():
    """List all active sessions (debugging)"""
    result = []
    for sid, session in SESSIONS.items():
        recipe = RECIPE_LIBRARY.get(session.cooking_state.recipe_key, {})
        result.append({
            "session_id": sid,
            "recipe_name": recipe.get("name", "Unknown"),
            "current_step": session.cooking_state.current_step,
        })
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)