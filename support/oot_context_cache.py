#!/usr/bin/env python3
"""oot_context_cache.py

Light-weight helper that lazily loads small excerpts from real OoT
headers / source so we can embed them in LLM prompts without
re-reading files each time.
"""
from pathlib import Path
from functools import lru_cache
from typing import Dict

ROOT = Path(__file__).parent / "oot"
INCLUDE = ROOT / "include"
SRC = ROOT / "src"

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _read_first_lines(path: Path, n: int = 120) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[:n]
        return "".join(lines)
    except FileNotFoundError:
        return f"/* Could not load {path} */\n"

@lru_cache(maxsize=None)
def _load_snippets() -> Dict[str, str]:
    """Gather category → snippet mappings (first ~120 lines each)."""
    snippets = {}
    snippets["actor"] = _read_first_lines(INCLUDE / "z_actor.h")
    snippets["collision"] = _read_first_lines(INCLUDE / "z_collision_check.h")
    snippets["animation"] = _read_first_lines(INCLUDE / "z64animation.h")  # fallback
    snippets["macros_collider"] = _read_first_lines(INCLUDE / "z_collision_check.h", 200)
    snippets["macros_animation"] = _read_first_lines(INCLUDE / "z64animation.h", 180)
    # small canonical example (first 350 lines)
    ex_path = SRC / "overlays" / "actors" / "ovl_En_Item00" / "z_en_item00.c"
    snippets["example_actor"] = _read_first_lines(ex_path, 350)
    return snippets

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

def get_snippet(key: str) -> str:
    return _load_snippets().get(key, "/* snippet not found */\n")


def get_macro_pack(kind: str) -> str:
    key = f"macros_{kind}"
    return _load_snippets().get(key, "/* macros not found */\n")


def get_example(category: str) -> str:
    if category == "actor":
        return get_snippet("example_actor")
    return "/* example not available */\n"

if __name__ == "__main__":
    print(get_snippet("actor")[:400]) 