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

def find_functions_improved(paths):
    """
    Improved function detection that captures more real OoT functions.
    """
    functions = set()
    
    # Multiple patterns to catch different function declaration styles
    func_patterns = [
        # Standard function definition: return_type func_name(args) {
        r'^[ \t]*(?:static[ \t]+)?(?:[A-Za-z_][A-Za-z0-9_\* ]+)[ \t]+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*\{',
        # Function declaration: return_type func_name(args);
        r'^[ \t]*(?:static[ \t]+)?(?:[A-Za-z_][A-Za-z0-9_\* ]+)[ \t]+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*;',
        # Function with complex return types
        r'^[ \t]*(?:static[ \t]+)?(?:[A-Za-z_][A-Za-z0-9_\* ]+)[ \t]+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)',
        # Simple pattern for basic functions
        r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*[{;]'
    ]
    
    for path in paths:
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('.h') or file.endswith('.c'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            # Process each pattern
                            for pattern in func_patterns:
                                for match in re.finditer(pattern, content, re.MULTILINE):
                                    name = match.group(1)
                                    
                                    # Filter out C keywords/types and common false positives
                                    if (name not in {
                                        'if', 'for', 'while', 'switch', 'return', 'void', 'int', 'float', 'double', 
                                        'char', 'static', 'const', 'struct', 'unsigned', 'signed', 'short', 'long', 
                                        'inline', 'extern', 'register', 'volatile', 'break', 'continue', 'goto', 
                                        'case', 'default', 'do', 'else', 'enum', 'typedef', 'sizeof', 'union', 
                                        'auto', 'restrict', 'bool', 'true', 'false', 'NULL', 'TRUE', 'FALSE',
                                        'malloc', 'free', 'calloc', 'realloc', 'memcpy', 'memmove', 'memset',
                                        'strcpy', 'strcat', 'strcmp', 'strlen', 'strchr', 'strstr', 'printf',
                                        'scanf', 'fopen', 'fclose', 'fread', 'fwrite', 'fseek', 'ftell',
                                        'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh',
                                        'exp', 'log', 'log10', 'pow', 'sqrt', 'fabs', 'floor', 'ceil',
                                        'abs', 'min', 'max', 'clamp', 'round', 'sign'
                                    } and 
                                    # Filter out very short names (likely not functions)
                                    len(name) > 2 and
                                    # Filter out names that are all uppercase (likely macros)
                                    not name.isupper() and
                                    # Filter out names starting with common prefixes that are likely not functions
                                    not name.startswith('g') and
                                    not name.startswith('s') and
                                    not name.startswith('D_') and
                                    not name.startswith('func_') and
                                    # Filter out names that look like variables
                                    not name.startswith('sp') and
                                    not name.startswith('temp') and
                                    not name.startswith('pad') and
                                    not name.startswith('arg') and
                                    not name.startswith('i') and
                                    not name.startswith('j') and
                                    not name.startswith('k')):
                                        functions.add(name)
                                        
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")
    
    return sorted(functions)

def find_functions(paths):
    """
    Legacy function for backward compatibility.
    """
    return find_functions_improved(paths)

def find_macros_and_enums(paths):
    """
    Improved constant detection that scans both .h and .c files with better patterns.
    """
    macro_pattern = re.compile(r'#define\s+([A-Za-z_][A-Za-z0-9_]*)')
    enum_pattern = re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\b')
    constants = set()
    
    for path in paths:
        for root, _, files in os.walk(path):
            for file in files:
                # Scan both .h and .c files for constants
                if file.endswith('.h') or file.endswith('.c'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            # Extract #define macros
                            for match in macro_pattern.finditer(content):
                                constants.add(match.group(1))
                            
                            # Extract enum values with improved patterns
                            # Pattern 1: typedef enum { ... } name;
                            typedef_enum_pattern = re.compile(r'typedef\s+enum\s*\{([^}]+)\}', re.DOTALL)
                            for match in typedef_enum_pattern.finditer(content):
                                enum_body = match.group(1)
                                for line in enum_body.split('\n'):
                                    line = line.strip()
                                    if line and not line.startswith('//') and not line.startswith('/*'):
                                        # Extract constant name (before = or ,)
                                        const_match = re.match(r'([A-Z][A-Z0-9_]*)\s*(?:,|$)', line)
                                        if const_match:
                                            constants.add(const_match.group(1))
                            
                            # Pattern 2: enum name { ... };
                            enum_def_pattern = re.compile(r'enum\s+[A-Za-z_][A-Za-z0-9_]*\s*\{([^}]+)\}', re.DOTALL)
                            for match in enum_def_pattern.finditer(content):
                                enum_body = match.group(1)
                                for line in enum_body.split('\n'):
                                    line = line.strip()
                                    if line and not line.startswith('//') and not line.startswith('/*'):
                                        const_match = re.match(r'([A-Z][A-Z0-9_]*)\s*(?:,|$)', line)
                                        if const_match:
                                            constants.add(const_match.group(1))
                            
                            # Pattern 3: enum { ... } name;
                            inline_enum_pattern = re.compile(r'enum\s*\{([^}]+)\}\s*[A-Za-z_][A-Za-z0-9_]*;', re.DOTALL)
                            for match in inline_enum_pattern.finditer(content):
                                enum_body = match.group(1)
                                for line in enum_body.split('\n'):
                                    line = line.strip()
                                    if line and not line.startswith('//') and not line.startswith('/*'):
                                        const_match = re.match(r'([A-Z][A-Z0-9_]*)\s*(?:,|$)', line)
                                        if const_match:
                                            constants.add(const_match.group(1))
                            
                            # Pattern 4: const declarations
                            const_decl_pattern = re.compile(r'const\s+[A-Za-z_][A-Za-z0-9_]*\s+([A-Z][A-Z0-9_]*)\s*=')
                            for match in const_decl_pattern.finditer(content):
                                constants.add(match.group(1))
                            
                            # Pattern 5: static const declarations
                            static_const_pattern = re.compile(r'static\s+const\s+[A-Za-z_][A-Za-z0-9_]*\s+([A-Z][A-Z0-9_]*)\s*=')
                            for match in static_const_pattern.finditer(content):
                                constants.add(match.group(1))
                                
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")
    
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

def verify_critical_functions(functions_set):
    """
    Verify that critical OoT functions are captured.
    """
    critical_functions = [
        'Actor_SetScale',
        'Actor_WorldDistXZToActor', 
        'Actor_WorldDistXYZToActor',
        'Actor_PlaySfx',
        'Actor_UpdateBgCheckInfo',
        'Actor_ProcessInitChain',
        'Actor_Kill',
        'Collider_InitCylinder',
        'Collider_SetCylinder',
        'Collider_UpdateCylinder',
        'Collider_DestroyCylinder',
        'CollisionCheck_SetAC',
        'CollisionCheck_SetOC',
        'Math_Vec3f_Copy',
        'Math_Vec3f_DistXYZ',
        'Math_Vec3f_DistXZ',
        'Math_ApproachF',
        'Flags_GetSwitch',
        'Flags_SetSwitch',
        'Matrix_Push',
        'Matrix_Pop',
        'Matrix_Scale',
        'Enemy_StartFinishingBlow',
        'DynaPolyActor_Init',
        'DynaPoly_DeleteBgActor'
    ]
    
    missing_functions = []
    for func in critical_functions:
        if func not in functions_set:
            missing_functions.append(func)
    
    if missing_functions:
        print(f"WARNING: Missing critical functions: {missing_functions}")
    else:
        print("✅ All critical functions captured successfully")
    
    return missing_functions

def verify_critical_constants(constants_set):
    """
    Verify that critical OoT constants are captured.
    """
    critical_constants = [
        'COLTYPE_NONE',
        'COLSHAPE_CYLINDER', 
        'COLSHAPE_SPHERE',
        'COLSHAPE_BOX',
        'ELEMTYPE_UNK0',
        'ELEMTYPE_UNK1',
        'ELEMTYPE_UNK2',
        'TOUCH_NONE',
        'TOUCH_ON',
        'BUMP_ON',
        'BUMP_NONE',
        'OC_ON',
        'OC_NONE',
        'OCELEM_ON',
        'OCELEM_NONE',
        'AT_NONE',
        'AT_ON',
        'AC_ON',
        'AC_NONE',
        'ACTORCAT_ENEMY',
        'ACTORCAT_NPC',
        'ACTORCAT_MISC',
        'ACTORCAT_ITEMACTION',
        'ACTOR_FLAG_0',
        'ACTOR_FLAG_1',
        'ACTOR_FLAG_2',
        'ACTOR_FLAG_3',
        'ACTOR_FLAG_4',
        'ACTOR_FLAG_5',
        'MASS_IMMOVABLE',
        'MASS_50',
        'MASS_40',
        'MASS_30',
        'OBJECT_GAMEPLAY_KEEP',
        'OBJECT_GAMEPLAY_DANGEON_KEEP',
        'UPDBGCHECKINFO_FLAG_0',
        'UPDBGCHECKINFO_FLAG_2',
        'UPDBGCHECKINFO_FLAG_4'
    ]
    
    missing_constants = []
    for const in critical_constants:
        if const not in constants_set:
            missing_constants.append(const)
    
    if missing_constants:
        print(f"WARNING: Missing critical constants: {missing_constants}")
    else:
        print("✅ All critical constants captured successfully")
    
    return missing_constants

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
    print('Scanning for simple function names with improved detection...')
    functions = find_functions_improved([oot_include, oot_src])
    
    # Verify critical functions are captured
    missing_critical = verify_critical_functions(set(functions))
    
    with open(out_funcs, 'w') as f:
        for fn in functions:
            f.write(fn + '\n')
    print(f'Wrote {len(functions)} simple function names to {out_funcs}')

    print('Scanning for constants...')
    constants = find_macros_and_enums([oot_include, oot_src])  # Scan both include and src directories
    
    # Verify critical constants are captured
    missing_critical_constants = verify_critical_constants(set(constants))
    
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