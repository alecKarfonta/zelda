#!/usr/bin/env python3
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from pycparser import parse_file, c_ast, c_parser
from pycparser.c_ast import FuncDef, Decl, Constant, Typedef, Enum

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
    
    # Simple patterns that match actual OoT function declarations
    func_patterns = [
        # Standard function definition: void func_name(args) {
        r'void\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(',
        # Function with return type: return_type func_name(args) {
        r'[A-Za-z_][A-Za-z0-9_\* ]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*\{',
        # Function declaration: return_type func_name(args);
        r'[A-Za-z_][A-Za-z0-9_\* ]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*;',
        # Static function: static return_type func_name(args) {
        r'static\s+[A-Za-z_][A-Za-z0-9_\* ]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*\{',
        # Function with complex return types
        r'[A-Za-z_][A-Za-z0-9_\* ]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)',
        # Very permissive pattern for any function-like call
        r'([A-Za-z_][A-Za-z0-9_]*)\s*\(',
        # Pattern for function names with underscores (common in OoT)
        r'([A-Za-z_][A-Za-z0-9_]*_[A-Za-z0-9_]*)\s*\(',
        # Pattern for Actor functions specifically
        r'([A-Za-z_][A-Za-z0-9_]*_[A-Za-z0-9_]*)\s*\([^)]*\)\s*[{;]'
    ]
    
    # Keywords to exclude (much smaller list)
    exclude_keywords = {
        'if', 'for', 'while', 'switch', 'return', 'void', 'int', 'float', 'double', 
        'char', 'static', 'const', 'struct', 'unsigned', 'signed', 'short', 'long', 
        'inline', 'extern', 'register', 'volatile', 'break', 'continue', 'goto', 
        'case', 'default', 'do', 'else', 'enum', 'typedef', 'sizeof', 'union', 
        'auto', 'restrict', 'bool', 'true', 'false', 'NULL', 'TRUE', 'FALSE'
    }
    
    debug_count = 0
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
                                    debug_count += 1
                                    
                                    # Debug output for first few matches
                                    if debug_count <= 10:
                                        print(f"DEBUG: Found potential function '{name}' in {file_path}")
                                    
                                    # Much more permissive filtering
                                    if (name not in exclude_keywords and 
                                        len(name) > 2 and
                                        not name.isupper() and
                                        # Allow more prefixes that are common in OoT
                                        not name.startswith('g') and  # Global variables
                                        not name.startswith('s') and  # Static variables
                                        not name.startswith('D_') and # Debug symbols
                                        not name.startswith('func_') and # Function pointers
                                        # Allow common OoT prefixes
                                        not name.startswith('sp') and
                                        not name.startswith('temp') and
                                        not name.startswith('pad') and
                                        not name.startswith('arg') and
                                        # Allow single letter variables but not as function names
                                        not (len(name) == 1 and name in 'ijkxyz')):
                                        functions.add(name)
                                        
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")
    
    print(f"DEBUG: Total potential functions found: {debug_count}")
    print(f"DEBUG: Functions after filtering: {len(functions)}")
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
                            
                            # Pattern 6: More permissive enum extraction
                            # Look for any uppercase identifiers that might be constants
                            uppercase_pattern = re.compile(r'\b([A-Z][A-Z0-9_]*)\b')
                            for match in uppercase_pattern.finditer(content):
                                const_name = match.group(1)
                                # Filter out common non-constants
                                if (const_name not in {'NULL', 'TRUE', 'FALSE', 'EOF', 'SEEK_SET', 'SEEK_CUR', 'SEEK_END'} and
                                    len(const_name) > 2 and
                                    not const_name.startswith('0x') and
                                    not const_name.isdigit()):
                                    constants.add(const_name)
                                
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

def get_all_c_files(root):
    c_files = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.endswith('.c') or f.endswith('.h'):
                c_files.append(os.path.join(dirpath, f))
    return c_files

def extract_functions_regex(files) -> Set[str]:
    # Regex for plausible C function definitions and declarations
    func_patterns = [
        # return_type func_name(args) { or ;
        r'^[A-Za-z_][A-Za-z0-9_\* ]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*[;{]',
        # static return_type func_name(args) { or ;
        r'^static\s+[A-Za-z_][A-Za-z0-9_\* ]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*[;{]',
        # extern return_type func_name(args) { or ;
        r'^extern\s+[A-Za-z_][A-Za-z0-9_\* ]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*[;{]',
    ]
    exclude = {
        'if', 'for', 'while', 'switch', 'return', 'void', 'int', 'float', 'double', 'char', 'static', 'const', 'struct', 'unsigned', 'signed', 'short', 'long', 'inline', 'extern', 'register', 'volatile', 'break', 'continue', 'goto', 'case', 'default', 'do', 'else', 'enum', 'typedef', 'sizeof', 'union', 'auto', 'restrict', 'bool', 'true', 'false', 'NULL', 'TRUE', 'FALSE'
    }
    functions = set()
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8', errors='ignore') as src:
                for line in src:
                    for pat in func_patterns:
                        m = re.match(pat, line.strip())
                        if m:
                            name = m.group(1)
                            if name not in exclude and not name.startswith('__') and len(name) > 2:
                                functions.add(name)
        except Exception as e:
            print(f"Error reading {f}: {e}")
    return functions

def main():
    oot_root = '../oot'
    c_files = get_all_c_files(oot_root)
    all_functions = extract_functions_regex(c_files)
    with open('../oot_valid_functions.txt', 'w') as f:
        for fn in sorted(all_functions):
            f.write(fn + '\n')
    print(f'Wrote {len(all_functions)} functions to ../oot_valid_functions.txt')

if __name__ == '__main__':
    main() 