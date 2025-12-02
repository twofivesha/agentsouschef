from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple


# Path to the normalized recipe JSON produced by scripts/prepare_recipes.py
DATA_DIR = Path(__file__).resolve().parent / "data"
RECIPES_JSON = DATA_DIR / "recipes_internal.json"


# --- Default built-in recipes (fallback for development) ---

_BUILTIN_RECIPES: Dict[str, Dict[str, Any]] = {
    "garlic_pasta": {
        "key": "garlic_pasta",
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
        "key": "scrambled_eggs",
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


def _load_recipe_library() -> Dict[str, Dict[str, Any]]:
    """
    Load recipes from data/recipes_internal.json if present;
    otherwise fall back to a small built-in library.
    """
    if RECIPES_JSON.exists():
        try:
            data = json.loads(RECIPES_JSON.read_text(encoding="utf-8"))
            # Expecting a dict of {key: {name, description, ingredients, steps, ...}}
            if isinstance(data, dict) and data:
                return data
        except Exception:
            # If anything goes wrong, just fall back to built-ins
            pass

    # Fallback: built-in examples
    return _BUILTIN_RECIPES


# This is what the rest of the app imports
RECIPE_LIBRARY: Dict[str, Dict[str, Any]] = _load_recipe_library()


def get_recipe_keys_and_labels() -> List[Tuple[str, str]]:
    """
    Return a list of (key, label) pairs for recipe selection.

    Label is currently just the recipe name, but could be extended
    to include a short description in the future.
    """
    items: List[Tuple[str, str]] = []
    for key, data in RECIPE_LIBRARY.items():
        label = data.get("name", key)
        items.append((key, label))
    # Sort alphabetically by label for nicer UI
    items.sort(key=lambda x: x[1].lower())
    return items