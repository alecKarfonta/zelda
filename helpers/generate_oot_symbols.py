#!/usr/bin/env python3
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional

def parse_function_signature(line: str) -> Optional[Dict]:
    """
    Parse a C function signature to extract return type, name, and arguments.
    Returns None if the line doesn't contain a valid function signature.
    """
    # Skip comments and preprocessor directives
    line = line.strip()
    if line.startswith('//') or line.startswith('/*') or line.startswith('#'):
        return None
    
    # More comprehensive function pattern that captures return type, name, and arguments
    # This pattern handles various C function declaration formats
    func_patterns = [
        # Standard function declaration: return_type func_name(arg1, arg2)
        r'^([A-Za-z_][A-Za-z0-9_]*\s+(?:const\s+)?(?:volatile\s+)?(?:unsigned\s+)?(?:signed\s+)?(?:short\s+)?(?:long\s+)?(?:int|char|float|double|void|struct\s+[A-Za-z_][A-Za-z0-9_]*|union\s+[A-Za-z_][A-Za-z0-9_]*|enum\s+[A-Za-z_][A-Za-z0-9_]*|[A-Za-z_][A-Za-z0-9_]*))\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*[{;]?$',
        # Function pointer or complex return types
        r'^([A-Za-z_][A-Za-z0-9_]*\s*(?:\*+\s*)*)\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*[{;]?$',
        # Simple pattern for basic functions
        r'^([A-Za-z_][A-Za-z0-9_]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*[{;]?$'
    ]
    
    for pattern in func_patterns:
        match = re.match(pattern, line)
        if match:
            return_type = match.group(1).strip()
            func_name = match.group(2).strip()
            args_str = match.group(3).strip()
            
            # Filter out C keywords that might be mistaken for function names
            if func_name in {'if', 'for', 'while', 'switch', 'return', 'void', 'int', 'float', 'double', 'char', 'static', 'const', 'struct', 'unsigned', 'signed', 'short', 'long', 'inline', 'extern', 'register', 'volatile', 'break', 'continue', 'goto', 'case', 'default', 'do', 'else', 'enum', 'typedef', 'sizeof', 'union', 'auto', 'restrict', 'bool', 'true', 'false'}:
                return None
            
            # Parse arguments
            args = []
            if args_str and args_str != 'void':
                # Split by comma, but be careful about nested parentheses
                arg_parts = []
                paren_count = 0
                current_arg = ""
                
                for char in args_str:
                    if char == '(':
                        paren_count += 1
                    elif char == ')':
                        paren_count -= 1
                    elif char == ',' and paren_count == 0:
                        if current_arg.strip():
                            arg_parts.append(current_arg.strip())
                        current_arg = ""
                        continue
                    current_arg += char
                
                if current_arg.strip():
                    arg_parts.append(current_arg.strip())
                
                for arg in arg_parts:
                    if arg.strip():
                        args.append(arg.strip())
            
            return {
                'return_type': return_type,
                'name': func_name,
                'arguments': args,
                'full_signature': line
            }
    
    return None

def find_functions_with_metadata(paths: List[str]) -> List[Dict]:
    """
    Find functions with detailed metadata including return type, name, and arguments.
    """
    functions = []
    
    for path in paths:
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('.h') or file.endswith('.c'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_num, line in enumerate(f, 1):
                                # Skip lines that are clearly not function declarations
                                if line.strip().startswith('//') or line.strip().startswith('/*'):
                                    continue
                                
                                # Try to parse the line as a function signature
                                func_info = parse_function_signature(line)
                                if func_info:
                                    func_info['file'] = file_path
                                    func_info['line'] = line_num
                                    functions.append(func_info)
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")
    
    return functions

def find_functions(paths):
    func_pattern = re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*[{;]')
    functions = set()
    for path in paths:
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('.h') or file.endswith('.c'):
                    with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            # Only match function definitions/declarations, not calls
                            m = func_pattern.match(line.strip())
                            if m:
                                name = m.group(1)
                                # Filter out C keywords/types
                                if name not in {'if', 'for', 'while', 'switch', 'return', 'void', 'int', 'float', 'double', 'char', 'static', 'const', 'struct', 'unsigned', 'signed', 'short', 'long', 'inline', 'extern', 'register', 'volatile', 'break', 'continue', 'goto', 'case', 'default', 'do', 'else', 'enum', 'typedef', 'sizeof', 'union', 'auto', 'restrict', 'bool', 'true', 'false'}:
                                    functions.add(name)
    return sorted(functions)

def find_macros_and_enums(paths):
    macro_pattern = re.compile(r'#define\s+([A-Za-z_][A-Za-z0-9_]*)')
    enum_pattern = re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\b')
    constants = set()
    for path in paths:
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('.h'):
                    with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        # Macros
                        for line in lines:
                            m = macro_pattern.match(line.strip())
                            if m:
                                constants.add(m.group(1))
                        # Enums
                        inside_enum = False
                        for line in lines:
                            if 'typedef enum' in line:
                                inside_enum = True
                                continue
                            if inside_enum:
                                if '}' in line:
                                    inside_enum = False
                                    continue
                                # Find all enum values (before = or ,)
                                parts = line.strip().split(',')
                                for part in parts:
                                    part = part.strip()
                                    if not part or part.startswith('//'):
                                        continue
                                    # Remove assignment
                                    if '=' in part:
                                        part = part.split('=')[0].strip()
                                    if part:
                                        m = enum_pattern.match(part)
                                        if m:
                                            constants.add(m.group(1))
    return sorted(constants)

def find_sound_effects(sfx_dir):
    sfx_pattern = re.compile(r'DEFINE_SFX\([^,]+,\s*([A-Za-z_][A-Za-z0-9_]*)')
    sfx = set()
    for file in Path(sfx_dir).glob('*.h'):
        with open(file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                m = sfx_pattern.search(line)
                if m:
                    sfx.add(m.group(1))
    return sorted(sfx)

def main():
    oot_include = 'oot/include'
    oot_src = 'oot/src'
    sfx_dir = 'oot/include/tables/sfx'
    out_funcs = 'oot_valid_functions.txt'
    out_funcs_detailed = 'oot_functions_detailed.txt'
    out_consts = 'oot_valid_constants.txt'
    out_sfx = 'oot_valid_sound_effects.txt'

    print('Scanning for functions with metadata...')
    functions_with_metadata = find_functions_with_metadata([oot_include, oot_src])
    
    # Write detailed function information
    with open(out_funcs_detailed, 'w') as f:
        f.write("# Function signatures with metadata\n")
        f.write("# Format: return_type function_name(arg1_type, arg2_type, ...)\n")
        f.write("# File: line_number\n\n")
        
        for func in functions_with_metadata:
            # Format arguments for display
            args_str = ", ".join(func['arguments']) if func['arguments'] else "void"
            f.write(f"{func['return_type']} {func['name']}({args_str})\n")
            f.write(f"# {func['file']}: {func['line']}\n\n")
    
    print(f'Wrote {len(functions_with_metadata)} detailed function signatures to {out_funcs_detailed}')

    # Also write simple function names for backward compatibility
    print('Scanning for simple function names...')
    functions = find_functions([oot_include, oot_src])
    with open(out_funcs, 'w') as f:
        for fn in functions:
            f.write(fn + '\n')
    print(f'Wrote {len(functions)} simple function names to {out_funcs}')

    print('Scanning for constants...')
    constants = find_macros_and_enums([oot_include])
    with open(out_consts, 'w') as f:
        for c in constants:
            f.write(c + '\n')
    print(f'Wrote {len(constants)} constants to {out_consts}')

    print('Scanning for sound effects...')
    sfx = find_sound_effects(sfx_dir)
    with open(out_sfx, 'w') as f:
        for s in sfx:
            f.write(s + '\n')
    print(f'Wrote {len(sfx)} sound effects to {out_sfx}')

if __name__ == '__main__':
    main() 