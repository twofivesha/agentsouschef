# test_api.py
"""
Simple test client for the clean API.
"""

import requests

BASE = "http://localhost:8000"


def test_api():
    print("🧪 Testing Agent Sous Chef API\n")
    
    # 1. List recipes
    print("📚 Listing recipes...")
    recipes = requests.get(f"{BASE}/recipes").json()
    print(f"Found {len(recipes)} recipes")
    for r in recipes:
        print(f"  - {r['name']}")
    print()
    
    # 2. Start session
    recipe_key = recipes[0]["key"]
    print(f"🚀 Starting session with '{recipe_key}'...")
    start = requests.post(
        f"{BASE}/session/start",
        json={"recipe_key": recipe_key}
    ).json()
    
    session_id = start["session_id"]
    print(f"Session: {session_id}")
    print(f"Reply: {start['reply']}\n")
    
    # 3. Ask for ingredients - DEBUG VERSION
    print("💬 Asking for ingredients...")
    resp = requests.post(
        f"{BASE}/session/{session_id}/message",
        json={"message": "i"}
    )
    print(f"Status code: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"Error response: {resp.text}")
        return
    
    msg = resp.json()
    print(f"Response keys: {list(msg.keys())}")
    print(f"Full response: {msg}\n")
    
    if 'reply' in msg:
        print(f"Reply:\n{msg['reply']}\n")
    else:
        print(f"⚠️  No 'reply' key in response!\n")
    
    # 4. Get next step
    print("💬 Asking for next step...")
    msg = requests.post(
        f"{BASE}/session/{session_id}/message",
        json={"message": "k"}
    ).json()
    
    if 'reply' in msg:
        print(f"Reply:\n{msg['reply']}")
        print(f"Current step: {msg['current_step']}/{msg['total_steps']}\n")
    
    # 5. Chat with AI
    print("💬 Chatting: 'What should I do now?'")
    msg = requests.post(
        f"{BASE}/session/{session_id}/message",
        json={"message": "What should I do now?"}
    ).json()
    
    if 'reply' in msg:
        print(f"AI Reply: {msg['reply']}\n")
    
    # 6. Check status
    print("ℹ️  Getting session info...")
    info = requests.get(f"{BASE}/session/{session_id}").json()
    print(f"Recipe: {info['recipe_name']}")
    print(f"Progress: {info['current_step']}/{info['total_steps']}\n")
    
    # 7. Clean up
    print("🧹 Deleting session...")
    requests.delete(f"{BASE}/session/{session_id}")
    print("✅ Done!\n")


if __name__ == "__main__":
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("❌ Can't connect to API. Is it running?")
        print("   Run: uv run python api_server.py")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()