# api_server.py
from typing import Dict, List, Set
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from recipes import RECIPE_LIBRARY
from commands import handle_user_command
from llm_agent import call_agent_sous_chef

app = FastAPI(title="Agent Sous Chef API")

# ---------- In-memory session store (phase 1) ----------

class SessionState:
    def __init__(self, recipe_key: str):
        self.recipe_key = recipe_key
        self.current_step: int = 0
        self.ingredient_subs: Dict[str, str] = {}
        self.ingredient_strikes: Set[str] = set()
        self.messages: List[Dict[str, str]] = []  # [{"role": "user"/"assistant", "content": str}]


SESSIONS: Dict[str, SessionState] = {}  # session_id -> SessionState


# ---------- Pydantic models ----------

class RecipeSummary(BaseModel):
    key: str
    name: str
    description: str | None = None


class StartSessionRequest(BaseModel):
    recipe_key: str


class StartSessionResponse(BaseModel):
    session_id: str
    recipe: RecipeSummary
    reply: str


class CommandRequest(BaseModel):
    user_input: str


class IngredientState(BaseModel):
    ingredients: List[str]
    subs: Dict[str, str]
    strikes: List[str]


class StepsState(BaseModel):
    steps: List[str]
    current_step: int


class CommandResponse(BaseModel):
    reply: str
    ingredient_state: IngredientState
    steps_state: StepsState
    recipe: RecipeSummary


# ---------- Helper functions ----------

def get_recipe_or_404(recipe_key: str) -> Dict:
    if recipe_key not in RECIPE_LIBRARY:
        raise HTTPException(status_code=404, detail="Unknown recipe_key")
    return RECIPE_LIBRARY[recipe_key]


def build_ingredient_state(session: SessionState, recipe: Dict) -> IngredientState:
    return IngredientState(
        ingredients=recipe["ingredients"],
        subs=session.ingredient_subs,
        strikes=list(session.ingredient_strikes),
    )


def build_steps_state(session: SessionState, recipe: Dict) -> StepsState:
    return StepsState(
        steps=recipe["steps"],
        current_step=session.current_step,
    )


def build_recipe_summary(recipe_key: str, recipe: Dict) -> RecipeSummary:
    return RecipeSummary(
        key=recipe_key,
        name=recipe["name"],
        description=recipe.get("description"),
    )


# ---------- Endpoints ----------

@app.get("/recipes", response_model=List[RecipeSummary])
def list_recipes() -> List[RecipeSummary]:
    """List recipes available in the library."""
    results: List[RecipeSummary] = []
    for key, recipe in RECIPE_LIBRARY.items():
        results.append(build_recipe_summary(key, recipe))
    return results


@app.post("/session/start", response_model=StartSessionResponse)
def start_session(payload: StartSessionRequest) -> StartSessionResponse:
    recipe = get_recipe_or_404(payload.recipe_key)

    session_id = str(uuid4())
    session = SessionState(recipe_key=payload.recipe_key)

    # Optionally add a greeting / initial assistant message
    initial_reply = f"Now cooking: {recipe['name']}.\n\nTell me what you've done or ask for 'ingredients', 'steps', or 'what'."

    session.messages.append({"role": "assistant", "content": initial_reply})
    SESSIONS[session_id] = session

    return StartSessionResponse(
        session_id=session_id,
        recipe=build_recipe_summary(payload.recipe_key, recipe),
        reply=initial_reply,
    )


@app.post("/session/{session_id}/command", response_model=CommandResponse)
def send_command(session_id: str, payload: CommandRequest) -> CommandResponse:
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Unknown session_id")

    session = SESSIONS[session_id]
    recipe = get_recipe_or_404(session.recipe_key)

    user_input = payload.user_input.strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="user_input cannot be empty")

    # Mirror chat-style history (optional, but nice to keep)
    session.messages.append({"role": "user", "content": user_input})

    # Prepare data for command engine
    recipe_name = recipe["name"]
    recipe_description = recipe.get("description", "")
    recipe_steps = recipe["steps"]
    recipe_ingredients = recipe["ingredients"]
    recipe_subs = session.ingredient_subs  # currently global per session

    # First let the command engine try to handle it
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

    # If not handled, fall back to LLM
    if not handled:
        result = call_agent_sous_chef(
            user_input=user_input,
            recipe_name=recipe_name,
            recipe_description=recipe_description,
            recipe_steps=recipe_steps,
            recipe_ingredients=recipe_ingredients,
            recipe_subs=recipe_subs,
            current_step_index=session.current_step,
        )
        reply_text = result["reply"]
        advance_step = result["advance_step"]

    # Apply step advancement if requested
    if advance_step and session.current_step < len(recipe_steps):
        session.current_step += 1

    # Save assistant message
    session.messages.append({"role": "assistant", "content": reply_text})

    return CommandResponse(
        reply=reply_text,
        ingredient_state=build_ingredient_state(session, recipe),
        steps_state=build_steps_state(session, recipe),
        recipe=build_recipe_summary(session.recipe_key, recipe),
    )