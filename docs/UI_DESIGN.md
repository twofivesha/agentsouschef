# Agent Sous Chef - UI Design Specification

## Overview
A cooking assistant app designed for use with greasy fingers and distracted minds. Emphasis on large touch targets, minimal cognitive load, and quick view switching.

## Core Design Principles

1. **Large Touch Targets** - Minimum 60px height buttons
2. **Minimal Cognitive Load** - Only 3-5 main actions visible at once
3. **Grease-Proof Interaction** - Tap anywhere on items to toggle
4. **Glanceable Information** - Large text, high contrast
5. **Quick View Switching** - One tap between main views

## Layout Structure

```
┌─────────────────────────────────────┐
│  🍳 Recipe Name            [⚙️]     │  ← Clean header (no progress bar)
├─────────────────────────────────────┤
│                                     │
│  ┏━━━━━━━━┓ ┌──────────┐ ┌────────┐│
│  ┃ STEPS  ┃ │  INGRED  │ │ STATUS ││  ← Three main tabs (always visible)
│  ┗━━━━━━━━┛ └──────────┘ └────────┘│
├─────────────────────────────────────┤
│                                     │
│  [Active View Content Here]        │
│                                     │
│         ┌─────────────────┐        │
│         │   ✓ DONE / NEXT │        │  ← Primary action button
│         └─────────────────┘        │
│                                     │
│         ┌─────────────────┐        │
│         │   🎤 VOICE      │        │  ← Voice input button
│         └─────────────────┘        │
└─────────────────────────────────────┘
```

## Three Main Views

### 📋 STEPS Tab

**Purpose:** Show all recipe steps with progress tracking

**Visual States:**
- ✅ **Completed steps:**
  - Grey text color (#888888)
  - Strikethrough styling (~~text~~)
  - Tap to undo if needed
  
- ➤ **Current step:**
  - Bold text weight
  - Highlighted background (light yellow or light blue)
  - Arrow indicator (➤) at start
  - Darker text color for emphasis
  
- ⚪ **Future steps:**
  - Normal text color
  - Regular font weight
  - No special styling

**Interactions:**
- Tap anywhere on a step line to toggle complete/incomplete
- "DONE" button advances to next step
- Entire list is scrollable if needed

**Example:**
```
┌───────────────────────────────┐
│ 1. ~~Boil water~~             │  ← Completed (grey + strikethrough)
│ 2. ~~Add pasta~~              │  ← Completed (grey + strikethrough)
│ ➤ 3. Add minced garlic to     │  ← Current (bold + highlighted)
│      oil and cook gently      │
│ 4. Reserve pasta water        │  ← Future (normal)
│ 5. Drain pasta                │  ← Future (normal)
│ 6. Toss with garlic oil       │
│ 7. Add cheese and serve       │
└───────────────────────────────┘
```

### 🥘 INGREDIENTS Tab

**Purpose:** Show all ingredients with ability to mark as used

**Visual States:**
- ☑ **Used ingredients:**
  - Checkbox checked
  - Strikethrough styling
  - Grey text color
  
- □ **Unused ingredients:**
  - Empty checkbox
  - Normal text color
  - Full opacity

**Interactions:**
- Tap anywhere on ingredient line to toggle used/unused
- Shows substitutions if any applied (e.g., "butter (instead of olive oil)")

**Example:**
```
┌───────────────────────────────┐
│ □ 8 oz dry spaghetti          │
│ ☑ Salt for pasta water        │  ← Marked as used
│ □ 3 tbsp olive oil            │
│ □ 3-4 cloves garlic, minced   │
│ □ Black pepper                │
│ □ Parmesan cheese             │
└───────────────────────────────┘
```

### ❓ STATUS Tab

**Purpose:** Quick overview of current cooking state

**Content:**
- Progress indicator: "Step X of Y" with progress bar
- Current step text (large, prominent)
- Ingredients summary (what's used, what's left)
- Quick reference for "where am I?"

**Example:**
```
┌───────────────────────────────┐
│                               │
│ CURRENT STEP:                 │
│                               │
│ Add minced garlic to the oil  │
│ and cook gently until         │
│ fragrant, not browned.        │
│                               │
│ INGREDIENTS:                  │
│ ✓ 2 used  ○ 4 remaining       │
└───────────────────────────────┘
```

## Buttons

### Primary Actions (Large)

**✓ DONE / NEXT Button:**
- Height: 60px minimum
- Full-width or centered large button
- Advances to next step
- Changes text based on context:
  - "NEXT STEP" when viewing steps
  - "DONE" when on current step
  - "COMPLETE!" on final step

**🎤 VOICE Button:**
- Height: 60px minimum
- Activates voice input mode
- Visual feedback when listening
- Always accessible

### Secondary Actions (Medium)

**Tab Buttons:**
- Height: 50px minimum
- Equal width distribution
- Active tab clearly highlighted
- High contrast between active/inactive

## Voice Commands

All voice commands work from any view:

**Navigation:**
- "Show steps" → Switch to STEPS tab
- "Show ingredients" → Switch to INGREDIENTS tab
- "What's the status?" / "Where am I?" → Switch to STATUS tab

**Actions:**
- "Next" / "Done" / "OK" → Advance to next step
- "Cross off [ingredient]" → Mark ingredient as used
- "Step [number]" → Jump to specific step
- "What step am I on?" → Show current step

**Queries:**
- "Show me step 5" → Display step 5
- "What ingredients do I need?" → Show ingredients list
- "Repeat that" → Repeat current step

## Responsive Behavior

### Mobile (Portrait)
- Single column layout
- One tab view at a time
- Full-width buttons
- Vertical scrolling

### Tablet (Landscape)
- Consider side-by-side layout:
  - Steps on left
  - Ingredients on right
  - Status as overlay or bottom panel
- Larger text and buttons

### Desktop
- Centered layout, max-width ~800px
- Larger text for reading from distance
- Keyboard shortcuts optional

## Color Palette (Suggestions)

**Primary:**
- Active Tab: #4CAF50 (Green)
- Current Step Highlight: #FFF9C4 (Light Yellow)
- Buttons: #4CAF50 (Green)

**Status:**
- Completed: #9E9E9E (Grey)
- Normal Text: #212121 (Dark Grey)
- Background: #FFFFFF (White)

**High Contrast Mode:**
- Ensure 4.5:1 contrast ratio minimum
- Option for dark mode in settings

## Touch Targets

- Minimum tap target: 44x44px (iOS guideline)
- Preferred: 60x60px for primary actions
- Spacing between targets: 8px minimum
- Entire row tappable, not just checkbox/text

## Typography

**Sizes:**
- Recipe name (header): 24px, bold
- Tab labels: 18px, semibold
- Current step text: 20px, bold
- Regular step text: 16px
- Completed step text: 16px, lighter weight
- Button text: 18px, bold

**Fonts:**
- System default for maximum performance
- High legibility priority
- No decorative fonts

## Accessibility

- High contrast text
- Large touch targets
- Voice as primary input method
- Screen reader support for all elements
- Clear focus indicators for keyboard navigation

## Future Enhancements (Not MVP)

- Timer integration per step
- Photo upload for recipes
- Recipe scaling (2x, 3x portions)
- Shopping list generation
- Multi-device sync
- Offline mode
- Recipe search
- Personal recipe collection

## Technical Implementation Notes

**Platform:** Progressive Web App (PWA)
- React + Tailwind CSS
- Web Speech API for voice
- Connects to existing FastAPI backend
- Installable to home screen
- Works offline (with service worker)

**API Integration:**
- GET /recipes - List recipes
- POST /session/start - Start cooking session
- POST /session/{id}/message - Send commands
- All state managed by backend

**State Management:**
- Session ID from backend
- Local state for UI (active tab, etc.)
- Real-time sync with API

---

## Version History

- v1.0 - 2024-12-06 - Initial design specification