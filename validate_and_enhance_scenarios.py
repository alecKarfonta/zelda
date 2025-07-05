#!/usr/bin/env python3
"""
OoT Scenario Validator & Context Generator

Restored full-featured version.  
• Extracts authentic patterns per category (enemy, npc, item, object).  
• Provides ValidationResult detailing issues/suggestions.  
• Supplies rich context snippets to feed the LLM.  
• Exposes create_enhanced_prompt() for prompt assembly.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict
import re

# ------------------------------------------------------------
# Data classes
# ------------------------------------------------------------

@dataclass
class ValidationResult:
    """Result of scenario validation"""
    is_valid: bool
    issues: List[str]
    suggestions: List[str]
    authentic_patterns: List[str]
    required_context: List[str]

# ------------------------------------------------------------
# Validator class
# ------------------------------------------------------------

class OoTPatternValidator:
    """Validate scenario text against known OoT patterns (lightweight restore)."""

    def __init__(self, oot_path: str = "oot") -> None:
        self.oot_path = oot_path  # kept for future expansion
        self.context_templates = self._build_context_templates()

    # ------------------------ public API ---------------------

    def validate_scenario(self, scenario: str, category: str) -> ValidationResult:
        category = category.lower().strip()
        if category == "enemy":
            issues, sugg, pats = self._validate_enemy_scenario(scenario)
            ctx = [self.context_templates["enemy"]]
        elif category == "npc":
            issues, sugg, pats = self._validate_npc_scenario(scenario)
            ctx = [self.context_templates["npc"]]
        elif category == "item":
            issues, sugg, pats = self._validate_item_scenario(scenario)
            ctx = [self.context_templates["item"]]
        else:
            # treat anything else as object/mechanism
            issues, sugg, pats = self._validate_object_scenario(scenario)
            ctx = [self.context_templates["object"]]

        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            suggestions=sugg,
            authentic_patterns=pats,
            required_context=ctx,
        )

    def create_enhanced_prompt(self, scenario: str, category: str, val: ValidationResult) -> str:
        """Return a rich prompt containing requirements & authentic snippets."""
        patterns = "\n".join(f"- {p}" for p in val.authentic_patterns[:6])
        issues_block = "\n".join(f"⚠️  {i}" for i in val.issues) or "None"
        suggestions_block = "\n".join(f"💡 {s}" for s in val.suggestions) or "None"
        ctx = "\n\n".join(val.required_context)
        return f"""
You are generating **authentic OoT rom-hacking code**.  Follow REAL decompilation patterns.

SCENARIO (category={category}): {scenario}

STRICT REQUIREMENTS:
1. Function signatures **must** be `(Actor* thisx, PlayState* play)`
2. Use real struct layouts and collision setup (`Collider_InitCylinder`, etc.)
3. Access positions via `actor.world.pos`, not deprecated fields.
4. Prefer re-using `EnItem00` for collectibles.

AUTHENTIC PATTERNS TO EMULATE:
{patterns}

KNOWN ISSUES:
{issues_block}

SUGGESTIONS TO IMPROVE:
{suggestions_block}

{ctx}

Return exactly this JSON:
{{
  "instruction": "clear instruction",
  "input": null,
  "output": "C code here"
}}
"""

    # ------------------------ private helpers ---------------

    def _validate_enemy_scenario(self, s: str) -> Tuple[List[str], List[str], List[str]]:
        issues, sugg, pats = [], [], []
        
        # More flexible validation for actor creation scenarios
        actor_keywords = ["actor", "enemy", "boss", "attack", "damage", "state", "create", "implement", "build"]
        has_actor_content = any(keyword in s.lower() for keyword in actor_keywords)
        
        if not has_actor_content:
            issues.append("Scenario does not mention concrete actor/enemy behaviour")
            sugg.append("Describe the actor's behavior, states, or goals (e.g., 'charges player when low health', 'creates a switch that activates when player stands on it')")
        
        pats.extend([
            "Use Actor_WorldDistXZToActor for distance checks",
            "State machine via `actionState` field",
            "Damage via Actor_ApplyDamage + Enemy_StartFinishingBlow",
        ])
        return issues, sugg, pats

    def _validate_npc_scenario(self, s: str) -> Tuple[List[str], List[str], List[str]]:
        issues, sugg, pats = [], [], []
        if "dialog" not in s.lower() and "shop" not in s.lower():
            sugg.append("Mention dialogue, shop or quest behaviour to clarify NPC role")
        pats.extend([
            "Dialogue via Npc_UpdateTalking and TEXT_STATE_CLOSING",
            "Tracking with NpcInteractInfo",
        ])
        return issues, sugg, pats

    def _validate_item_scenario(self, s: str) -> Tuple[List[str], List[str], List[str]]:
        issues, sugg, pats = [], [], []
        if not re.search(r"item|rupee|heart|key|mask", s, re.I):
            issues.append("Missing explicit item type")
        pats.append("Spawn with EnItem00 and ITEM00_* params")
        return issues, sugg, pats

    def _validate_object_scenario(self, s: str) -> Tuple[List[str], List[str], List[str]]:
        issues, sugg, pats = [], [], []
        if not re.search(r"switch|platform|door|mechanism|puzzle", s, re.I):
            sugg.append("Specify mechanism type (switch, platform, door, etc.)")
        pats.append("Use DynaPolyActor for moving/mechanic objects")
        return issues, sugg, pats

    # ------------------------ context templates -------------

    def _build_context_templates(self) -> Dict[str, str]:
        tpl = {}
        tpl["enemy"] = (
            "AUTHENTIC ENEMY PATTERNS:\n"
            "- Collider_InitCylinder for body\n"
            "- actionState enum controlling AI\n"
            "- Damage handled with Actor_ApplyDamage\n"
            "- Distance checks via Actor_WorldDistXZToActor"
        )
        tpl["npc"] = (
            "AUTHENTIC NPC PATTERNS:\n"
            "- Dialogue via Npc_UpdateTalking\n"
            "- Text IDs handled in GetTextId function\n"
            "- Tracking player with NpcInteractInfo"
        )
        tpl["item"] = (
            "AUTHENTIC ITEM PATTERNS:\n"
            "- Use EnItem00 for collectibles\n"
            "- ITEM00_* constants for types\n"
            "- Bobbing animation via Math_SinS"
        )
        tpl["object"] = (
            "AUTHENTIC OBJECT PATTERNS:\n"
            "- Mechanics via DynaPolyActor\n"
            "- Switch state toggled with Flags_Get/SetSwitch\n"
            "- Movement with Math_ApproachF"
        )
        return tpl

# ------------------------------------------------------------
# Simple CLI test
# ------------------------------------------------------------

if __name__ == "__main__":
    val = OoTPatternValidator()
    scenario = "Design a rotating platform switch that activates when the player stands on it"
    res = val.validate_scenario(scenario, "object")
    print(res)
    print("\n--- Enhanced Prompt Preview (first 300 chars) ---")
    print(val.create_enhanced_prompt(scenario, "object", res)[:300] + "...\n") 