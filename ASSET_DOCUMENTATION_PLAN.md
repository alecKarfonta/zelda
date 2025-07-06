# Zelda OoT Asset Documentation Plan

## Overview
This document outlines a robust, phased plan for building an automated documentation system for assets in `extracted/ntsc-1.2/assets/textures`. The goal is to provide comprehensive, searchable, and human/AI-augmented documentation for all assets, including metadata, usage, and visual descriptions.

---

## Phase 1: Asset Inventory and Metadata Extraction

**Checklist:**
- [ ] Recursively walk the `extracted/ntsc-1.2/assets/textures` directory.
- [ ] For each file, collect:
  - File path and name
  - File type (PNG, C, header, etc.)
  - Dimensions (for images)
  - Size
  - Format (e.g., ia8, rgba16, etc.)
- [ ] Output a structured inventory (JSON/CSV/Markdown).

---

## Phase 2: Reference and Usage Analysis

**Checklist:**
- [ ] For each asset, search the codebase for references (includes, loads, etc.).
- [ ] Record:
  - Which C files or overlays reference the asset
  - How it is used (texture, display list, etc.)
  - Any associated variables or symbols
- [ ] Link references in the documentation.

---

## Phase 3: Automated Image Description (VLM Integration)

**Checklist:**
- [ ] For each image asset, generate a visual description using a Vision-Language Model (VLM).
  - [ ] Set up a local VLM (e.g., LLaVA, MiniGPT-4, etc.)
  - [ ] Pass each PNG to the VLM and record the output.
- [ ] Store the description alongside the asset metadata.

---

## Phase 4: Human-in-the-Loop and LLM Integration

**Checklist:**
- [ ] For non-image assets (C arrays, display lists), use an LLM to:
  - [ ] Summarize the code or data structure.
  - [ ] Suggest likely in-game usage.
- [ ] Allow for human review and annotation of auto-generated docs.

---

## Phase 5: Documentation Generation and Browsing

**Checklist:**
- [ ] Generate browsable documentation (Markdown, HTML, or web app).
- [ ] For each asset, show:
  - Metadata
  - Usage/references
  - Visual description (with image preview)
  - Human/LLM notes
- [ ] Add search and filtering.

---

## Phase 6: Continuous Integration and Updates

**Checklist:**
- [ ] Set up a script or CI job to re-run the documentation generator when assets change.
- [ ] Optionally, add a web interface for browsing and editing docs.

---

## Script Skeleton (Phase 1 & 2 Example, Python)

```python
import os
import json
from PIL import Image

def get_image_metadata(path):
    try:
        with Image.open(path) as img:
            return {"width": img.width, "height": img.height, "mode": img.mode}
    except Exception:
        return {}

def find_references(asset_name, search_dirs):
    # Use ripgrep or similar to find references in codebase
    # Placeholder: return []
    return []

def walk_assets(root):
    assets = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            meta = {
                "path": fpath,
                "name": fname,
                "size": os.path.getsize(fpath),
                "type": os.path.splitext(fname)[1].lower(),
            }
            if fname.endswith('.png'):
                meta.update(get_image_metadata(fpath))
            meta["references"] = find_references(fname, ["../src", "../assets"])
            assets.append(meta)
    return assets

if __name__ == "__main__":
    assets = walk_assets("extracted/ntsc-1.2/assets/textures")
    with open("asset_inventory.json", "w") as f:
        json.dump(assets, f, indent=2)
```

---

## Next Steps

1. **Start with Phase 1:** Build and test the inventory script.
2. **Iterate through the phases,** adding reference analysis, VLM/LLM integration, and documentation generation.
3. **Set up local VLM/LLM** for image and code description (can advise on this setup). 