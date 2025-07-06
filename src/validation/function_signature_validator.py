#!/usr/bin/env python3
"""
Function Signature Validator for OoT Training Data Generation

Parses oot_functions_detailed.txt and validates function calls against authentic signatures.
"""

import re
import os
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass

from src.core.logger import logger


@dataclass
class FunctionSignature:
    """Represents a function signature with return type and parameters"""
    name: str
    return_type: str
    parameters: List[Tuple[str, str]]  # (type, name) pairs
    file_location: str
    line_number: int


class FunctionSignatureValidator:
    """Validates function calls against authentic OoT function signatures"""
    
    def __init__(self, detailed_functions_file: str = "oot_functions_detailed.txt"):
        self.detailed_functions_file = detailed_functions_file
        self.function_signatures: Dict[str, FunctionSignature] = {}
        self.load_function_signatures()
    
    def load_function_signatures(self) -> None:
        """Load and parse function signatures from the detailed functions file"""
        if not os.path.exists(self.detailed_functions_file):
            logger.warning(f"Detailed functions file not found: {self.detailed_functions_file}")
            return
        
        logger.info(f"Loading function signatures from {self.detailed_functions_file}")
        
        with open(self.detailed_functions_file, 'r') as f:
            lines = f.readlines()
        
        current_function = None
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip comments and empty lines
            if line.startswith('#') or not line:
                continue
            
            # Check if this is a function signature line
            if '(' in line and ')' in line and not line.startswith('#'):
                # Parse function signature
                signature = self._parse_function_signature(line, line_num)
                if signature:
                    self.function_signatures[signature.name] = signature
                    current_function = signature.name
            
            # Check if this is a file location line
            elif line.startswith('#') and ':' in line and current_function:
                # Extract file location
                file_info = line[1:].strip()  # Remove #
                if ':' in file_info:
                    file_path, line_num_str = file_info.rsplit(':', 1)
                    if current_function in self.function_signatures:
                        self.function_signatures[current_function].file_location = file_path
                        try:
                            self.function_signatures[current_function].line_number = int(line_num_str)
                        except ValueError:
                            pass
        
        logger.success(f"Loaded {len(self.function_signatures)} function signatures")
        
        # Log some examples
        sample_functions = list(self.function_signatures.keys())[:5]
        logger.debug(f"Sample functions: {sample_functions}")
    
    def _parse_function_signature(self, signature_line: str, line_num: int) -> Optional[FunctionSignature]:
        """Parse a function signature line into a FunctionSignature object"""
        try:
            # Match pattern: return_type function_name(param1_type param1_name, param2_type param2_name, ...)
            # or: return_type function_name(param1_type, param2_type, ...)
            
            # First, extract the return type and function name
            match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*)\)$', signature_line)
            if not match:
                return None
            
            return_type = match.group(1)
            function_name = match.group(2)
            params_str = match.group(3)
            
            # Parse parameters
            parameters = []
            if params_str.strip():
                # Split by comma, but be careful about nested parentheses
                param_parts = self._split_parameters(params_str)
                
                for param in param_parts:
                    param = param.strip()
                    if param:
                        # Handle both "type name" and "type" formats
                        param_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s+([a-zA-Z_][a-zA-Z0-9_]*)$', param)
                        if param_match:
                            # "type name" format
                            param_type = param_match.group(1)
                            param_name = param_match.group(2)
                        else:
                            # "type" format (no parameter name)
                            param_type = param
                            param_name = f"arg{len(parameters)}"
                        
                        parameters.append((param_type, param_name))
            
            return FunctionSignature(
                name=function_name,
                return_type=return_type,
                parameters=parameters,
                file_location="",
                line_number=line_num
            )
            
        except Exception as e:
            logger.debug(f"Failed to parse function signature at line {line_num}: {signature_line} - {e}")
            return None
    
    def _split_parameters(self, params_str: str) -> List[str]:
        """Split parameter string by commas, respecting parentheses"""
        params = []
        current_param = ""
        paren_count = 0
        
        for char in params_str:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == ',' and paren_count == 0:
                params.append(current_param.strip())
                current_param = ""
                continue
            
            current_param += char
        
        if current_param.strip():
            params.append(current_param.strip())
        
        return params
    
    def validate_function_call(self, function_name: str, arguments: List[str], 
                             return_usage: Optional[str] = None) -> List[str]:
        """Validate a function call against the authentic signature"""
        issues = []
        
        if function_name not in self.function_signatures:
            issues.append(f"❌ Unknown function: {function_name} - not found in OoT function database")
            return issues
        
        signature = self.function_signatures[function_name]
        
        # Validate argument count
        expected_count = len(signature.parameters)
        actual_count = len(arguments)
        
        if actual_count != expected_count:
            issues.append(f"❌ Function {function_name}: expected {expected_count} arguments, got {actual_count}")
            return issues
        
        # Validate argument types (basic validation)
        for i, (expected_type, expected_name) in enumerate(signature.parameters):
            if i < len(arguments):
                arg = arguments[i].strip()
                type_issue = self._validate_argument_type(arg, expected_type, function_name, i)
                if type_issue:
                    issues.append(type_issue)
        
        # Validate return type usage
        if signature.return_type == "void" and return_usage:
            issues.append(f"❌ Function {function_name}: void function should not return a value")
        elif signature.return_type != "void" and not return_usage:
            issues.append(f"❌ Function {function_name}: non-void function should return {signature.return_type}")
        
        return issues
    
    def _validate_argument_type(self, argument: str, expected_type: str, 
                               function_name: str, arg_index: int) -> Optional[str]:
        """Validate that an argument matches the expected type"""
        # Basic type checking - this could be enhanced with more sophisticated parsing
        
        # Common OoT types and their patterns
        type_patterns = {
            "Actor*": r"this|actor|\w+\->actor|\w+\.actor|&\w+",
            "PlayState*": r"play",
            "f32": r"-?\d+\.\d+f?|-?\d+\.\d+|\w+",  # Allow variable names for f32
            "s32": r"-?\d+|\w+",  # Allow variable names for s32
            "s16": r"-?\d+|\w+",  # Allow variable names for s16
            "u32": r"\d+|\w+",  # Allow variable names for u32
            "u16": r"\d+|\w+",  # Allow variable names for u16
            "u8": r"\d+|\w+",  # Allow variable names for u8
            "Vec3f*": r"&\w+\.pos|\w+\.pos|\w+",
            "Vec3s*": r"&\w+\.rot|\w+\.rot|\w+",
            "ColliderCylinder*": r"&\w+\.collider|\w+\.collider|\w+",
            "char*": r'"[^"]*"',
            "void*": r"NULL|\w+",
        }
        
        # For strict type checking, we need to be more specific
        if expected_type == "f32":
            # Check for float literals or variable names
            if not re.match(r'^-?\d+\.\d+f?$|^-?\d+\.\d+$|^\w+$', argument):
                return f"❌ Function {function_name} arg {arg_index + 1}: expected {expected_type}, got '{argument}'"
        elif expected_type == "Actor*":
            # Check for actor pointers
            if not re.match(r'^this$|^actor$|^\w+\->actor$|^\w+\.actor$|^&\w+$', argument):
                return f"❌ Function {function_name} arg {arg_index + 1}: expected {expected_type}, got '{argument}'"
        elif expected_type == "PlayState*":
            # Check for play state pointer
            if not re.match(r'^play$', argument):
                return f"❌ Function {function_name} arg {arg_index + 1}: expected {expected_type}, got '{argument}'"
        elif expected_type == "s32":
            # Check for integer literals or variable names
            if not re.match(r'^-?\d+$|^\w+$', argument):
                return f"❌ Function {function_name} arg {arg_index + 1}: expected {expected_type}, got '{argument}'"
        elif expected_type == "s16":
            # Check for integer literals or variable names
            if not re.match(r'^-?\d+$|^\w+$', argument):
                return f"❌ Function {function_name} arg {arg_index + 1}: expected {expected_type}, got '{argument}'"
        elif expected_type == "u32":
            # Check for unsigned integer literals or variable names
            if not re.match(r'^\d+$|^\w+$', argument):
                return f"❌ Function {function_name} arg {arg_index + 1}: expected {expected_type}, got '{argument}'"
        elif expected_type == "u16":
            # Check for unsigned integer literals or variable names
            if not re.match(r'^\d+$|^\w+$', argument):
                return f"❌ Function {function_name} arg {arg_index + 1}: expected {expected_type}, got '{argument}'"
        elif expected_type == "u8":
            # Check for unsigned integer literals or variable names
            if not re.match(r'^\d+$|^\w+$', argument):
                return f"❌ Function {function_name} arg {arg_index + 1}: expected {expected_type}, got '{argument}'"
        elif expected_type == "Vec3f*":
            # Check for vector pointers
            if not re.match(r'^&\w+\.pos$|^\w+\.pos$|^\w+$', argument):
                return f"❌ Function {function_name} arg {arg_index + 1}: expected {expected_type}, got '{argument}'"
        elif expected_type == "Vec3s*":
            # Check for vector pointers
            if not re.match(r'^&\w+\.rot$|^\w+\.rot$|^\w+$', argument):
                return f"❌ Function {function_name} arg {arg_index + 1}: expected {expected_type}, got '{argument}'"
        elif expected_type == "ColliderCylinder*":
            # Check for collider pointers
            if not re.match(r'^&\w+\.collider$|^\w+\.collider$|^\w+$', argument):
                return f"❌ Function {function_name} arg {arg_index + 1}: expected {expected_type}, got '{argument}'"
        elif expected_type == "char*":
            # Check for string literals
            if not re.match(r'^"[^"]*"$', argument):
                return f"❌ Function {function_name} arg {arg_index + 1}: expected {expected_type}, got '{argument}'"
        elif expected_type == "void*":
            # Check for void pointers
            if not re.match(r'^NULL$|^\w+$', argument):
                return f"❌ Function {function_name} arg {arg_index + 1}: expected {expected_type}, got '{argument}'"
        
        return None
    
    def _check_return_usage(self, code: str, call_start: int, function_name: str) -> Optional[str]:
        """Check if the function call's return value is used"""
        # Look for assignment patterns before the function call
        lines = code[:call_start].split('\n')
        if lines:
            last_line = lines[-1].strip()
            
            # Check for assignment patterns
            assignment_patterns = [
                r'(\w+)\s*=\s*$',  # variable = 
                r'(\w+)\s*\+=\s*$',  # variable +=
                r'(\w+)\s*-=\s*$',   # variable -=
                r'(\w+)\s*\*=\s*$',  # variable *=
                r'(\w+)\s*/=\s*$',   # variable /=
            ]
            
            for pattern in assignment_patterns:
                match = re.search(pattern, last_line)
                if match:
                    return match.group(1)
        
        # Also check for direct usage in expressions
        # Look ahead in the code to see if the function call is part of an expression
        code_after = code[call_start:]
        if code_after:
            # Check if the function call is followed by operators or used in expressions
            next_char = code_after[0] if code_after else ''
            if next_char in ['+', '-', '*', '/', ';', ',', ')']:
                # Function call is used in an expression
                return "expression"
        
        return None
    
    def extract_function_calls(self, code: str) -> List[Tuple[str, List[str], Optional[str]]]:
        """Extract function calls from C code with their arguments and return usage"""
        function_calls = []
        
        # Pattern to match function calls: function_name(arg1, arg2, ...)
        # Also capture if the result is assigned to something
        call_pattern = r'(\w+)\s*\(([^)]*)\)'
        
        for match in re.finditer(call_pattern, code):
            function_name = match.group(1)
            args_str = match.group(2)
            
            # Skip common C keywords and builtins
            if function_name in ['if', 'for', 'while', 'switch', 'sizeof', 'typedef', 'return']:
                continue
            
            # Parse arguments
            arguments = self._parse_function_arguments(args_str)
            
            # Check if return value is used
            return_usage = self._check_return_usage(code, match.start(), function_name)
            
            function_calls.append((function_name, arguments, return_usage))
        
        return function_calls
    
    def _parse_function_arguments(self, args_str: str) -> List[str]:
        """Parse function arguments from a string"""
        if not args_str.strip():
            return []
        
        args = []
        current_arg = ""
        paren_count = 0
        
        for char in args_str:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == ',' and paren_count == 0:
                args.append(current_arg.strip())
                current_arg = ""
                continue
            
            current_arg += char
        
        if current_arg.strip():
            args.append(current_arg.strip())
        
        return args
    
    def validate_code_function_calls(self, code: str) -> List[str]:
        """Validate all function calls in a piece of code"""
        issues = []
        
        function_calls = self.extract_function_calls(code)
        
        for function_name, arguments, return_usage in function_calls:
            call_issues = self.validate_function_call(function_name, arguments, return_usage)
            issues.extend(call_issues)
        
        return issues


# Test the function signature validator
if __name__ == "__main__":
    validator = FunctionSignatureValidator()
    
    # Test with some sample code
    test_code = """
    void EnTest_Init(Actor* thisx, PlayState* play) {
        EnTest* this = (EnTest*)thisx;
        
        f32 scale = Math_SinF(0.5f);
        s32 result = Math_Atan2S(1.0f, 2.0f);
        Vec3f pos = {1.0f, 2.0f, 3.0f};
        
        Actor_SetScale(&this->actor, scale);
        Collider_InitCylinder(play, &this->collider);
    }
    """
    
    print("Testing function signature validation:")
    print("=" * 50)
    
    issues = validator.validate_code_function_calls(test_code)
    
    print(f"Found {len(issues)} validation issues:")
    for issue in issues:
        print(f"  - {issue}")
    
    # Show some loaded signatures
    print(f"\nLoaded {len(validator.function_signatures)} function signatures")
    sample_funcs = list(validator.function_signatures.keys())[:5]
    print(f"Sample functions: {sample_funcs}")
    
    if sample_funcs:
        sample_func = sample_funcs[0]
        sig = validator.function_signatures[sample_func]
        print(f"\nSample signature for {sample_func}:")
        print(f"  Return type: {sig.return_type}")
        print(f"  Parameters: {sig.parameters}")
        print(f"  Location: {sig.file_location}:{sig.line_number}") 