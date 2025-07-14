#!/usr/bin/env python3
"""
Convert raw hex data in .inc.c files to proper C array declarations.
This script reads the raw hex data and wraps it in proper u8[] array declarations.
"""

import os
import re
import glob

def convert_inc_c_file(filepath):
    """Convert a single .inc.c file to proper C array format."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Extract the hex values
    hex_values = re.findall(r'0x[0-9a-fA-F]+', content)
    
    if not hex_values:
        print(f"Warning: No hex values found in {filepath}")
        return
    
    # Convert 64-bit hex values to individual bytes
    byte_values = []
    for hex_val in hex_values:
        # Convert hex string to integer, then to bytes
        val = int(hex_val, 16)
        # Convert to 8 bytes (64-bit value)
        bytes_val = val.to_bytes(8, byteorder='big')
        byte_values.extend(bytes_val)
    
    # Create the array name from the filename
    basename = os.path.basename(filepath)
    array_name = basename.replace('.inc.c', '').replace('.i8', '')
    
    # Generate the C array
    c_array = f"u8 {array_name}[] = {{\n"
    
    # Add bytes in groups of 16 for readability
    for i in range(0, len(byte_values), 16):
        group = byte_values[i:i+16]
        hex_strings = [f"0x{b:02x}" for b in group]
        c_array += "    " + ", ".join(hex_strings) + ",\n"
    
    c_array += "};\n"
    
    # Write the converted file
    with open(filepath, 'w') as f:
        f.write(c_array)
    
    print(f"Converted {filepath}")

def main():
    """Convert all .inc.c files in the current directory."""
    inc_c_files = glob.glob("*.inc.c")
    
    if not inc_c_files:
        print("No .inc.c files found in current directory")
        return
    
    print(f"Found {len(inc_c_files)} .inc.c files to convert")
    
    for filepath in inc_c_files:
        convert_inc_c_file(filepath)
    
    print("Conversion completed!")

if __name__ == "__main__":
    main() 