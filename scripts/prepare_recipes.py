from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, Any


# Paths
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
INPUT_CSV = DATA_DIR / "13k-recipes.csv"
OUTPUT_JSON = DATA_DIR / "recipes_internal.json"


def slugify(title: str) -> str:
    """Simple key generator from a recipe title."""
    base = "".join(ch.lower() if ch.isalnum() else "_" for ch in title)
    while "__" in base:
        base = base.replace("__", "_")
    return base.strip("_")[:80]  # cap length just in case


def main() -> None:
    """
    Read a CSV of recipes and normalize it into a JSON file that
    Agent Sous Chef can consume as RECIPE_LIBRARY.

    Expected CSV columns (adjust as needed for your dataset):
      - Title
      - Ingredients
      - Instructions
    """
    if not INPUT_CSV.exists():
        raise FileNotFoundError(
            f"Input CSV not found at {INPUT_CSV}. "
            "Put your recipe CSV there (e.g. 13k-recipes.csv)."
        )

    recipes: Dict[str, Dict[str, Any]] = {}

    with INPUT_CSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = (row.get("Title") or "").strip()
            ingredients_text = (row.get("Ingredients") or "").strip()
            instructions_text = (row.get("Instructions") or "").strip()

            if not title or not ingredients_text or not instructions_text:
                continue

            key = slugify(title)

            # Avoid overwriting if we hit a duplicate slug
            if key in recipes:
                continue

            # --- Parse ingredients ---
            ing = ingredients_text.strip()
            # Some datasets store ingredients like "['1 cup flour', '2 eggs', ...]"
            if ing.startswith("[") and ing.endswith("]"):
                ing = ing[1:-1]

            ingredients = []
            for part in ing.split("',"):
                cleaned = part.strip().strip("[]'\" ")
                if cleaned:
                    ingredients.append(cleaned)

            # --- Parse instructions into steps ---
            raw_instr = instructions_text.replace("\r\n", "\n").replace("\r", "\n")
            if "\n" in raw_instr:
                steps = [s.strip() for s in raw_instr.split("\n") if s.strip()]
            else:
                steps = [s.strip() for s in raw_instr.split(".") if s.strip()]

            # Skip very short or malformed recipes
            if len(ingredients) < 2 or len(steps) < 2:
                continue

            recipes[key] = {
                "key": key,
                "name": title,
                "description": "",
                "ingredients": ingredients,
                "steps": steps,
            }

    print(f"Loaded {len(recipes)} cleaned recipes.")
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(recipes, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
