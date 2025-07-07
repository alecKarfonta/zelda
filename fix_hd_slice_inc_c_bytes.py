import os
import re

SLICE_DIR = "oot/extracted/ntsc-1.2/assets/textures/nintendo_rogo_static/extracted/ntsc-1.2/assets/textures/nintendo_rogo_static/nintendo_rogo_static_Tex_000000.i8.png.hd_slices"

for fname in os.listdir(SLICE_DIR):
    if fname.startswith("slice_") and fname.endswith(".i8.inc.c"):
        path = os.path.join(SLICE_DIR, fname)
        m = re.match(r"slice_(\d+)_(\d+)\.i8\.inc\.c", fname)
        if not m:
            continue
        y, x = m.groups()
        varname = f"nintendo_rogo_static_slice_{y}_{x}"
        with open(path, "r") as f:
            content = f.read()
        # Remove any existing declaration
        content = re.sub(r"u8 [^=]+\[\] = \{.*?\};", "", content, flags=re.DOTALL)
        # Find all hex values
        hexes = re.findall(r"0x[0-9a-fA-F]+", content)
        bytes_flat = []
        for h in hexes:
            v = int(h, 16)
            # Unpack into 8 bytes, big-endian
            for i in range(8):
                b = (v >> (8 * (7 - i))) & 0xFF
                bytes_flat.append(f"0x{b:02x}")
        # Write as a u8 array
        with open(path, "w") as f:
            f.write(f"u8 {varname}[] = {{\n    ")
            for i, b in enumerate(bytes_flat):
                if i > 0 and i % 16 == 0:
                    f.write("\n    ")
                f.write(b)
                if i != len(bytes_flat) - 1:
                    f.write(", ")
            f.write("\n};\n")
print("All HD slice .inc.c files have been byte-unpacked.") 