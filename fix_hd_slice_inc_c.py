import os
import re

# Directory containing the slice .inc.c files
SLICE_DIR = "oot/extracted/ntsc-1.2/assets/textures/nintendo_rogo_static/extracted/ntsc-1.2/assets/textures/nintendo_rogo_static/nintendo_rogo_static_Tex_000000.i8.png.hd_slices"

for fname in os.listdir(SLICE_DIR):
    if fname.startswith("slice_") and fname.endswith(".i8.inc.c"):
        path = os.path.join(SLICE_DIR, fname)
        # Extract X and Y from the filename
        m = re.match(r"slice_(\d+)_(\d+)\.i8\.inc\.c", fname)
        if not m:
            continue
        y, x = m.groups()
        varname = f"nintendo_rogo_static_slice_{y}_{x}"
        with open(path, "r") as f:
            data = f.read().strip().rstrip(',')
        with open(path, "w") as f:
            f.write(f"u8 {varname}[] = {{\n{data}\n}};\n")
print("Fixed HD slice .inc.c files") 