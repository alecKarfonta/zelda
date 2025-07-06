#!/usr/bin/env python3
"""
Robust Response Parser for OoT Training Data Generation
"""

import json
import re
from typing import Optional, List

from src.models.enums import ExampleType, TrainingExample
from src.core.logger import logger


class ResponseParser:
    """Robust parser for handling different LLM response formats"""
    
    def parse_response(self, raw_response: str, example_type: ExampleType) -> Optional[TrainingExample]:
        """Parse Claude's response into a TrainingExample object using multiple robust parsing strategies"""
        
        # Strategy 1: Check if the entire response is just C code
        if self._is_pure_c_code(raw_response):
            logger.info("[DEBUG] Detected pure C code response")
            instruction = self._extract_instruction_from_context(example_type)
            return TrainingExample(
                example_type=example_type,
                instruction=instruction,
                input=None,
                output=raw_response,
                metadata={"generation_method": "pure_c_code"},
                quality_score=0.0
            )
        
        # Strategy 2: Try standard JSON parsing first
        try:
            # Look for JSON block
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                return TrainingExample(
                    example_type=example_type,
                    instruction=data.get("instruction", ""),
                    input=data.get("input") if data.get("input") != "null" else None,
                    output=data.get("output", ""),
                    metadata={"generation_method": "json_block_parsing"},
                    quality_score=0.0
                )
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Strategy 3: Try parsing as raw JSON (no code block)
        try:
            # Check if the response is just raw JSON
            stripped = raw_response.strip()
            if stripped.startswith('{') and stripped.endswith('}'):
                data = json.loads(stripped)
                logger.debug(f"[DEBUG] Raw JSON parsing successful - Output length: {len(data.get('output', ''))}")
                return TrainingExample(
                    example_type=example_type,
                    instruction=data.get("instruction", ""),
                    input=data.get("input") if data.get("input") != "null" else None,
                    output=data.get("output", ""),
                    metadata={"generation_method": "raw_json_parsing"},
                    quality_score=0.0
                )
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Strategy 4: Extract C code blocks and instruction separately
        c_code_blocks = self._extract_c_code_blocks(raw_response)
        if c_code_blocks:
            logger.info(f"[DEBUG] Found {len(c_code_blocks)} C code blocks")
            instruction = self._extract_instruction_from_response(raw_response, example_type)
            output = c_code_blocks[0]  # Use the first code block
            
            return TrainingExample(
                example_type=example_type,
                instruction=instruction,
                input=None,
                output=output,
                metadata={"generation_method": "c_code_block_extraction"},
                quality_score=0.0
            )
        
        # Strategy 5: Try to extract fields using regex patterns that handle unescaped content
        logger.info("[DEBUG] Attempting robust field extraction...")
        
        # More flexible regex patterns that can handle unescaped content
        instruction_patterns = [
            r'"instruction":\s*"((?:[^"\\]|\\.)*)"',  # Handle escaped quotes properly
            r'"instruction":\s*"([^"]+)"',  # Standard quoted string (fallback)
        ]
        
        output_patterns = [
            # Handle code blocks properly - match everything until the closing quote
            r'"output":\s*"((?:[^"\\]|\\.)*)"\s*[,}]',  # Comprehensive pattern for quoted content with escapes
            r'"output":\s*"([^"]*(?:\\.[^"]*)*)"',  # Handle escaped quotes
            r'"output":\s*```([^`]+)```',  # Unescaped code block (fallback)
            r'"output":\s*```c\s*([^`]+)```',  # Specific C code block (fallback)
        ]
        
        input_patterns = [
            r'"input":\s*(null|"[^"]*")',  # null or quoted string
        ]
        
        # Try different extraction strategies
        instruction = None
        output = None
        input_text = None
        
        # Extract instruction
        for pattern in instruction_patterns:
            match = re.search(pattern, raw_response, re.DOTALL)
            if match:
                instruction = match.group(1).strip()
                break
        
        # Extract output - try multiple strategies
        for pattern in output_patterns:
            match = re.search(pattern, raw_response, re.DOTALL)
            if match:
                output = match.group(1).strip()
                # Decode escaped characters (like \n -> newlines)
                try:
                    output = output.encode().decode('unicode_escape')
                except:
                    pass  # If decoding fails, use as-is
                
                # If this was a code block, add proper formatting
                if not output.startswith('```') and ('void ' in output or '#include' in output or 'typedef' in output):
                    output = f"```c\n{output}\n```"
                break
        
        # Extract input
        for pattern in input_patterns:
            match = re.search(pattern, raw_response, re.DOTALL)
            if match:
                input_content = match.group(1).strip()
                if input_content != "null":
                    input_text = input_content.strip('"')
                break
        
        # Strategy 6: If structured extraction worked, create example
        if instruction and output:
            logger.info(f"[DEBUG] Successfully extracted - Instruction: {len(instruction)} chars, Output: {len(output)} chars")
            logger.info(f"[DEBUG] Output preview: {output[:100]}...")
            return TrainingExample(
                example_type=example_type,
                instruction=instruction,
                input=input_text,
                output=output,
                metadata={"extraction_method": "robust_regex"},
                quality_score=0.0
            )
        
        # Strategy 7: Manual parsing fallback for completely malformed responses
        logger.info("[DEBUG] Attempting manual parsing fallback...")
        
        # Try to find JSON-like structure manually
        lines = raw_response.split('\n')
        current_field = None
        current_content = []
        parsed_data = {}
        
        for line in lines:
            line = line.strip()
            
            # Check for field start
            if line.startswith('"instruction":'):
                current_field = "instruction"
                content = line.split(':', 1)[1].strip().strip('"').strip(',')
                if content:
                    parsed_data[current_field] = content
                current_content = []
            elif line.startswith('"input":'):
                current_field = "input"
                content = line.split(':', 1)[1].strip().strip('"').strip(',')
                if content and content != "null":
                    parsed_data[current_field] = content
                current_content = []
            elif line.startswith('"output":'):
                current_field = "output"
                content = line.split(':', 1)[1].strip()
                if content.startswith('```'):
                    # This is a code block, start collecting
                    current_content = [content]
                else:
                    # Regular quoted content
                    content = content.strip('"').strip(',')
                    if content:
                        parsed_data[current_field] = content
                    current_content = []
            elif current_field and line:
                # Continue collecting multi-line content
                current_content.append(line)
            elif current_field and current_content:
                # End of field, finalize content
                if current_field == "output" and current_content:
                    parsed_data[current_field] = '\n'.join(current_content)
                current_field = None
                current_content = []
        
        # Finalize any remaining content
        if current_field and current_content:
            parsed_data[current_field] = '\n'.join(current_content)
        
        # Create example from manual parsing
        if parsed_data.get("instruction") and parsed_data.get("output"):
            logger.info(f"[DEBUG] Manual parsing successful - {len(parsed_data)} fields extracted")
            return TrainingExample(
                example_type=example_type,
                instruction=parsed_data["instruction"],
                input=parsed_data.get("input"),
                output=parsed_data["output"],
                metadata={"extraction_method": "manual_parsing", "raw_response": raw_response[:500]},
                quality_score=0.0
            )
        
        # Strategy 8: Last resort - try to find any usable content
        logger.info("[DEBUG] Last resort parsing...")
        
        # Look for any instruction-like content
        instruction_fallback = None
        output_fallback = None
        
        # Search for common patterns
        create_match = re.search(r'(Create|Implement|Explain|Debug).*?(?=\n|$)', raw_response, re.IGNORECASE)
        if create_match:
            instruction_fallback = create_match.group(0).strip()
        
        # Look for code blocks
        code_match = re.search(r'```c?\s*\n(.*?)\n```', raw_response, re.DOTALL)
        if code_match:
            output_fallback = f"```c\n{code_match.group(1).strip()}\n```"
        elif re.search(r'```', raw_response):
            # There's a code block but it's malformed
            start = raw_response.find('```')
            if start != -1:
                remaining = raw_response[start+3:]
                end = remaining.find('```')
                if end != -1:
                    code_content = remaining[:end].strip()
                    output_fallback = f"```c\n{code_content}\n```"
        
        if instruction_fallback and output_fallback:
            logger.info(f"[DEBUG] Fallback extraction successful")
            return TrainingExample(
                example_type=example_type,
                instruction=instruction_fallback,
                input=None,
                output=output_fallback,
                metadata={"extraction_method": "fallback", "warning": "Extracted from malformed response"},
                quality_score=0.0
            )
        
        # Complete failure
        logger.error(f"[DEBUG] Complete parsing failure. Raw response preview:\n{raw_response[:200]}...")
        return None

    def _is_pure_c_code(self, response: str) -> bool:
        """Check if the response is just C code without any JSON structure"""
        # Remove leading/trailing whitespace
        stripped = response.strip()
        
        # Check if it starts with C code patterns
        c_code_patterns = [
            r'^#include\s+["<][^>"]*[">]',  # #include statements
            r'^typedef\s+struct',  # struct definitions
            r'^void\s+\w+\s*\(',  # function declarations
            r'^static\s+',  # static declarations
            r'^const\s+',  # const declarations
            r'^enum\s+',  # enum declarations
            r'^#define\s+',  # #define macros
        ]
        
        for pattern in c_code_patterns:
            if re.search(pattern, stripped, re.MULTILINE):
                return True
        
        # Check if it contains C code but no JSON structure
        has_c_code = any(pattern in stripped for pattern in ['void ', 'typedef', '#include', 'struct', 'enum'])
        has_json = any(pattern in stripped for pattern in ['"instruction"', '"output"', '{', '}'])
        
        return has_c_code and not has_json

    def _extract_c_code_blocks(self, response: str) -> List[str]:
        """Extract all C code blocks from the response"""
        code_blocks = []
        
        # Pattern to match ```c ... ``` blocks
        c_block_pattern = r'```c\s*\n(.*?)\n```'
        matches = re.finditer(c_block_pattern, response, re.DOTALL)
        
        for match in matches:
            code_content = match.group(1).strip()
            if code_content:
                code_blocks.append(f"```c\n{code_content}\n```")
        
        # Also look for ``` ... ``` blocks that contain C code
        generic_block_pattern = r'```\s*\n(.*?)\n```'
        matches = re.finditer(generic_block_pattern, response, re.DOTALL)
        
        for match in matches:
            code_content = match.group(1).strip()
            # Check if this looks like C code
            if any(c_pattern in code_content for c_pattern in ['void ', 'typedef', '#include', 'struct', 'enum', 'Actor', 'PlayState']):
                code_blocks.append(f"```c\n{code_content}\n```")
        
        return code_blocks

    def _extract_instruction_from_response(self, response: str, example_type: ExampleType) -> str:
        """Extract instruction from response text"""
        # Look for instruction-like text before code blocks
        lines = response.split('\n')
        instruction_candidates = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('```') and not line.startswith('{') and not line.startswith('"'):
                # Look for instruction-like patterns
                if any(pattern in line.lower() for pattern in ['create', 'implement', 'build', 'design', 'make']):
                    instruction_candidates.append(line)
        
        if instruction_candidates:
            return instruction_candidates[0]
        
        # Fallback to example type description
        return f"Create a {example_type.value.replace('_', ' ')} system"

    def _extract_instruction_from_context(self, example_type: ExampleType) -> str:
        """Generate instruction from example type context"""
        return f"Create a {example_type.value.replace('_', ' ')} system" 