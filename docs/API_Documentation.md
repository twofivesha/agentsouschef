# Agent Sous Chef API Documentation

A headless REST API for the Agent Sous Chef cooking assistant.

## Getting Started

### Running the API Server

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="sk-..."

# Run the server
python api_server.py

# Or with uvicorn directly
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Interactive Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Health Check

**GET /** - Check API status

```bash
curl http://localhost:8000/
```

Response:
```json
{
  "name": "Agent Sous Chef API",
  "version": "1.0.0",
  "status": "healthy"
}
```

---

### Recipe Management

#### List All Recipes

**GET /recipes** - Get all available recipes

```bash
curl http://localhost:8000/recipes
```

Response:
```json
[
  {
    "key": "garlic_pasta",
    "name": "Simple Garlic Pasta",
    "description": "Fast, simple, garlicky pasta for weeknights."
  }
]
```

#### Get Recipe Details

**GET /recipes/{recipe_key}** - Get full recipe information

```bash
curl http://localhost:8000/recipes/garlic_pasta
```

Response:
```json
{
  "key": "garlic_pasta",
  "name": "Simple Garlic Pasta",
  "description": "Fast, simple, garlicky pasta for weeknights.",
  "ingredients": [
    "8 ounces dry spaghetti or other pasta",
    "Salt for the pasta water",
    "3 tablespoons olive oil"
  ],
  "steps": [
    "Bring a large pot of salted water to a boil.",
    "Add pasta and cook until just shy of al dente"
  ]
}
```

---

### Session Management

#### Start a Session

**POST /session/start** - Begin a new cooking session

```bash
curl -X POST http://localhost:8000/session/start \
  -H "Content-Type: application/json" \
  -d '{"recipe_key": "garlic_pasta"}'
```

Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "recipe": {
    "key": "garlic_pasta",
    "name": "Simple Garlic Pasta",
    "description": "Fast, simple, garlicky pasta for weeknights.",
    "ingredients": [...],
    "steps": [...]
  },
  "reply": "Now cooking: Simple Garlic Pasta.\n\nTell me what you've done..."
}
```

#### Get Session Info

**GET /session/{session_id}** - Get current session state

```bash
curl http://localhost:8000/session/{session_id}
```

Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "recipe_key": "garlic_pasta",
  "recipe_name": "Simple Garlic Pasta",
  "current_step": 2,
  "message_count": 6
}
```

#### Delete Session

**DELETE /session/{session_id}** - End a cooking session

```bash
curl -X DELETE http://localhost:8000/session/{session_id}
```

Response:
```json
{
  "message": "Session deleted successfully"
}
```

#### List All Sessions

**GET /sessions** - List all active sessions (debugging)

```bash
curl http://localhost:8000/sessions
```

---

### Conversation

#### Send Command

**POST /session/{session_id}/command** - Send a message or command

```bash
curl -X POST http://localhost:8000/session/{session_id}/command \
  -H "Content-Type: application/json" \
  -d '{"user_input": "what is the next step?"}'
```

Response:
```json
{
  "reply": "Next step:\n\n2. Add pasta and cook until just shy of al dente",
  "ingredient_state": {
    "ingredients": ["8 ounces dry spaghetti", "Salt for pasta water"],
    "subs": {},
    "strikes": []
  },
  "steps_state": {
    "steps": ["Bring a large pot of salted water to a boil.", ...],
    "current_step": 2
  },
  "recipe": {
    "key": "garlic_pasta",
    "name": "Simple Garlic Pasta",
    "description": "..."
  }
}
```

**Available Commands:**
- `i` - Show ingredients
- `s` - Show all steps
- `k`, `ok`, `next` - Advance to next step
- `what` - Show current status
- `x 3` - Mark steps 1-3 as complete
- `x oil` - Strike out an ingredient
- Or just chat naturally with the AI!

---

### Ingredient Management

#### Strike/Unstrike Ingredient

**POST /session/{session_id}/ingredient/strike** - Mark ingredient as used

```bash
curl -X POST http://localhost:8000/session/{session_id}/ingredient/strike \
  -H "Content-Type: application/json" \
  -d '{"ingredient": "olive oil", "action": "strike"}'
```

Request body:
```json
{
  "ingredient": "olive oil",
  "action": "strike"  // or "unstrike"
}
```

Response:
```json
{
  "message": "Ingredient 'olive oil' struck successfully",
  "ingredient_state": {
    "ingredients": [...],
    "subs": {},
    "strikes": ["3 tablespoons olive oil"]
  }
}
```

#### Add Substitution

**POST /session/{session_id}/ingredient/substitute** - Add ingredient substitution

```bash
curl -X POST http://localhost:8000/session/{session_id}/ingredient/substitute \
  -H "Content-Type: application/json" \
  -d '{
    "original": "olive oil",
    "substitute": "butter"
  }'
```

Response:
```json
{
  "message": "Substituted '3 tablespoons olive oil' with 'butter'",
  "ingredient_state": {
    "ingredients": [...],
    "subs": {
      "3 tablespoons olive oil": "butter"
    },
    "strikes": []
  }
}
```

#### Remove Substitution

**DELETE /session/{session_id}/ingredient/substitute/{ingredient}** - Remove a substitution

```bash
curl -X DELETE "http://localhost:8000/session/{session_id}/ingredient/substitute/3%20tablespoons%20olive%20oil"
```

---

## Example Workflow

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. List recipes
recipes = requests.get(f"{BASE_URL}/recipes").json()
print(f"Available recipes: {[r['name'] for r in recipes]}")

# 2. Start a session
session = requests.post(
    f"{BASE_URL}/session/start",
    json={"recipe_key": "garlic_pasta"}
).json()

session_id = session["session_id"]
print(f"Started session: {session_id}")
print(f"Reply: {session['reply']}")

# 3. Ask for ingredients
result = requests.post(
    f"{BASE_URL}/session/{session_id}/command",
    json={"user_input": "i"}
).json()
print(f"Ingredients: {result['ingredient_state']['ingredients']}")

# 4. Get next step
result = requests.post(
    f"{BASE_URL}/session/{session_id}/command",
    json={"user_input": "k"}
).json()
print(f"Next step: {result['reply']}")
print(f"Current step index: {result['steps_state']['current_step']}")

# 5. Mark ingredient as used
requests.post(
    f"{BASE_URL}/session/{session_id}/ingredient/strike",
    json={"ingredient": "salt", "action": "strike"}
)

# 6. Chat naturally
result = requests.post(
    f"{BASE_URL}/session/{session_id}/command",
    json={"user_input": "I added the pasta, what's next?"}
).json()
print(f"AI reply: {result['reply']}")

# 7. Clean up
requests.delete(f"{BASE_URL}/session/{session_id}")
```

---

## Response Models

### CommandResponse

```typescript
{
  reply: string;              // AI or command response
  ingredient_state: {
    ingredients: string[];    // Original ingredient list
    subs: {[key: string]: string};  // Substitutions applied
    strikes: string[];        // Struck-out ingredients
  };
  steps_state: {
    steps: string[];          // All recipe steps
    current_step: number;     // Current step index (0-based)
  };
  recipe: {
    key: string;
    name: string;
    description?: string;
  };
}
```

---

## Error Handling

All endpoints return standard HTTP status codes:

- `200` - Success
- `400` - Bad Request (invalid input)
- `404` - Not Found (session or recipe doesn't exist)
- `500` - Internal Server Error

Error response format:
```json
{
  "detail": "Error message here"
}
```

---

## CORS Configuration

By default, CORS is enabled for all origins. In production, update `api_server.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Next Steps

Now that your API is working, you can:

1. **Build the UI** - Create a React/Next.js frontend
2. **Add persistence** - Replace in-memory sessions with Redis/database
3. **Add authentication** - Protect sessions with JWT tokens
4. **Voice mode** - Add speech-to-text and text-to-speech endpoints
5. **Recipe search** - Implement semantic search with embeddings
6. **Multi-user support** - Add user accounts and recipe collections