# core/commands.py
"""
Pure command engine with zero UI dependencies.
All state is passed in and returned - no global state.
"""

import re
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field


@dataclass
class CookingState:
    """Complete state for a cooking session"""
    recipe_key: str
    current_step: int = 0
    ingredient_subs: Dict[str, str] = field(default_factory=dict)
    ingredient_strikes: Set[str] = field(default_factory=set)


@dataclass
class CommandResult:
    """Result of processing a command"""
    handled: bool
    reply: str
    new_state: Optional[CookingState] = None  # If None, state unchanged
    advance_step: bool = False


def format_ingredient_list(
    ingredients: List[str],
    subs: Dict[str, str],
    strikes: Set[str]
) -> str:
    """Format ingredients as markdown"""
    lines = []
    for ing in ingredients:
        # Check if substituted
        display = ing
        if ing in subs:
            display = f"{subs[ing]} (instead of {ing})"
        
        # Check if struck
        if ing in strikes:
            lines.append(f"- ~~{display}~~")
        else:
            lines.append(f"- {display}")
    
    return "\n".join(lines)


def format_steps_list(steps: List[str], current_step: int) -> str:
    """Format steps with progress markers"""
    lines = []
    for idx, step in enumerate(steps):
        if idx < current_step:
            lines.append(f"{idx + 1}. ~~{step}~~")
        else:
            lines.append(f"{idx + 1}. {step}")
    return "\n".join(lines)


def handle_command(
    user_input: str,
    state: CookingState,
    recipe_name: str,
    ingredients: List[str],
    steps: List[str],
) -> CommandResult:
    """
    Process a user command.
    Pure function - no side effects, no global state.
    """
    lower = user_input.lower().strip()
    
    # Command: Show ingredients
    if lower in ["i", "ingredients"]:
        reply = "**Ingredients:**\n\n" + format_ingredient_list(
            ingredients,
            state.ingredient_subs,
            state.ingredient_strikes
        )
        return CommandResult(handled=True, reply=reply)
    
    # Command: Show steps
    if lower in ["s", "steps"]:
        reply = "**Steps:**\n\n" + format_steps_list(steps, state.current_step)
        return CommandResult(handled=True, reply=reply)
    
    # Command: Next step
    if lower in ["k", "ok", "next", "done"]:
        if state.current_step >= len(steps):
            return CommandResult(
                handled=True,
                reply="You've completed all steps! 🎉"
            )
        
        step_num = state.current_step + 1
        step_text = steps[state.current_step]
        
        new_state = CookingState(
            recipe_key=state.recipe_key,
            current_step=state.current_step + 1,
            ingredient_subs=state.ingredient_subs.copy(),
            ingredient_strikes=state.ingredient_strikes.copy()
        )
        
        return CommandResult(
            handled=True,
            reply=f"**Step {step_num}:**\n\n{step_text}",
            new_state=new_state
        )
    
    # Command: Jump to step N (e.g., "x 3" marks steps 1-3 done)
    step_match = re.match(r"^x\s+(\d+)$", lower)
    if step_match:
        n = int(step_match.group(1))
        n = max(0, min(n, len(steps)))
        
        new_state = CookingState(
            recipe_key=state.recipe_key,
            current_step=n,
            ingredient_subs=state.ingredient_subs.copy(),
            ingredient_strikes=state.ingredient_strikes.copy()
        )
        
        reply_lines = [f"Marked steps 1-{n} as complete." if n > 0 else "Reset to beginning."]
        reply_lines.append("\n**All Steps:**\n")
        reply_lines.append(format_steps_list(steps, n))
        
        return CommandResult(
            handled=True,
            reply="\n".join(reply_lines),
            new_state=new_state
        )
    
    # Command: Strike ingredient (e.g., "x oil")
    strike_match = re.match(r"^x\s+(.+)$", lower)
    if strike_match:
        target = strike_match.group(1).strip()
        
        # Find matching ingredients
        matches = [ing for ing in ingredients if target in ing.lower()]
        
        if not matches:
            return CommandResult(
                handled=True,
                reply=f"Couldn't find ingredient matching '{target}'"
            )
        
        new_strikes = state.ingredient_strikes.copy()
        new_strikes.update(matches)
        
        new_state = CookingState(
            recipe_key=state.recipe_key,
            current_step=state.current_step,
            ingredient_subs=state.ingredient_subs.copy(),
            ingredient_strikes=new_strikes
        )
        
        reply = "Marked as used:\n\n" + format_ingredient_list(
            ingredients,
            state.ingredient_subs,
            new_strikes
        )
        
        return CommandResult(
            handled=True,
            reply=reply,
            new_state=new_state
        )
    
    # Command: What (show current status)
    if lower == "what":
        lines = [f"**Cooking: {recipe_name}**\n"]
        
        if ingredients:
            lines.append("**Ingredients:**")
            lines.append(format_ingredient_list(
                ingredients,
                state.ingredient_subs,
                state.ingredient_strikes
            ))
            lines.append("")
        
        if state.current_step < len(steps):
            step_num = state.current_step + 1
            lines.append(f"**Current Step ({step_num}/{len(steps)}):**")
            lines.append(steps[state.current_step])
        else:
            lines.append("✅ All steps complete!")
        
        return CommandResult(handled=True, reply="\n".join(lines))
    
    # Command: Show specific step number
    num_match = re.match(r"^(\d+)$", user_input.strip())
    if num_match:
        step_num = int(num_match.group(1))
        if 1 <= step_num <= len(steps):
            return CommandResult(
                handled=True,
                reply=f"**Step {step_num}:**\n\n{steps[step_num - 1]}"
            )
    
    # Not a recognized command
    return CommandResult(handled=False, reply="")