from typing import List, Dict, Set


def format_working_ingredients_markdown(
    recipe_ingredients: List[str],
    recipe_subs: Dict[str, str],
    strikes: Set[str],
) -> List[str]:
    """Return markdown lines (bullets) for current ingredient state."""
    lines: List[str] = []
    for ing in recipe_ingredients:
        sub_name = recipe_subs.get(ing)
        if sub_name:
            display = f"{sub_name} (instead of {ing})"
        else:
            display = ing

        if ing in strikes:
            lines.append(f"- ~~{display}~~")
        else:
            lines.append(f"- {display}")
    return lines


def format_steps_with_progress_markdown(
    steps: List[str],
    current_step: int,
) -> List[str]:
    """Return markdown lines for all steps, with completed ones struck through."""
    lines: List[str] = []
    for idx, step in enumerate(steps):
        if idx < current_step:
            lines.append(f"{idx + 1}. ~~{step}~~")
        else:
            lines.append(f"{idx + 1}. {step}")
    return lines