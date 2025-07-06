#!/usr/bin/env python3
"""
Strict Authenticity Validator for OoT Training Data
"""

import re
from typing import List, Optional

from core.logger import logger
from analyzers.source_analyzer import DynamicSourceAnalyzer


class StrictAuthenticityValidator:
    """Enhanced validator with strict authenticity enforcement + real OoT function data"""
    
    def __init__(self, source_analyzer: Optional[DynamicSourceAnalyzer] = None):
        # Use dynamic source analyzer if provided, otherwise use OoTAuthenticPatterns data
        self.source_analyzer = source_analyzer
        
        if source_analyzer:
            # Real function signatures from actual OoT decompilation
            self.authentic_function_signatures = set(source_analyzer.real_functions.keys())
            
            # Real OoT types from decompilation
            self.authentic_types = set(source_analyzer.real_structs.keys())
        else:
            # Use OoTAuthenticPatterns data instead of hardcoded lists
            from helpers.validate_and_enhance_scenarios import OoTAuthenticPatterns
            patterns = OoTAuthenticPatterns()
            self.authentic_function_signatures = patterns.AUTHENTIC_FUNCTIONS
            self.authentic_types = patterns.AUTHENTIC_CONSTANTS  # Use constants as types too
        
        # Mandatory corrections for authenticity
        self.mandatory_corrections = {
            # Function signature corrections
            "GlobalContext": "PlayState",
            "globalCtx": "play",
            "void ActorName_Init(PlayState* play, Actor* thisx)": "void ActorName_Init(Actor* thisx, PlayState* play)",
            "void ActorName_Update(PlayState* play, Actor* thisx)": "void ActorName_Update(Actor* thisx, PlayState* play)",
            "void ActorName_Destroy(PlayState* play, Actor* thisx)": "void ActorName_Destroy(Actor* thisx, PlayState* play)",
            "void ActorName_Draw(PlayState* play, Actor* thisx)": "void ActorName_Draw(Actor* thisx, PlayState* play)",
            
            # Position access corrections (from real decompilation)
            "this->actor.pos": "this->actor.world.pos",
            "this->actor.rot": "this->actor.world.rot", 
            "player->actor.pos": "player->actor.world.pos",
            
            # Structure corrections
            "ActorInit": "ActorProfile",
            "const ActorInit": "const ActorProfile",
        }
        
        # Forbidden patterns that indicate non-authenticity (STRICT)
        self.forbidden_patterns = [
            r"GlobalContext\*\s+\w+",  # Any GlobalContext usage
            r"void\s+\w+_Init\(PlayState\*.*?Actor\*",  # Wrong parameter order
            r"void\s+\w+_Update\(PlayState\*.*?Actor\*",  # Wrong parameter order
            r"ACTOR_HEART_PIECE",  # Custom heart piece actors (should use EN_ITEM00)
            r"HeartPieceActor",  # Custom heart piece structs
            r"\.pos\.",  # Direct pos access instead of world.pos
            r"gPlayState",  # Global state variables
            r"gGlobalCtx",  # Global context variables
        ]
        
        # Required authentic patterns for quality code
        self.required_patterns = [
            r"PlayState\*\s+play",  # Modern PlayState usage
            r"Actor\*\s+thisx",  # Authentic actor parameter
            r"world\.pos",  # Proper position access
            r"ACTORCAT_\w+",  # Actor categories
            r"Collider_\w+",  # Collision functions
        ]
        
        # Real architectural patterns from OoT decompilation
        self.architectural_guidance = {
            "heart_piece": "Use EnItem00 with ITEM00_HEART_PIECE parameter (from z_en_item00.c)",
            "rupees": "Use EnItem00 with ITEM00_RUPEE_* parameters (from z_en_item00.c)", 
            "keys": "Use EnItem00 with ITEM00_SMALL_KEY parameter (from z_en_item00.c)",
            "collectibles": "Most collectibles use EnItem00 with different parameters (see z_en_item00.c)",
            "switches": "Use existing switch actors with parameters, rarely create new ones",
        }

    def validate_function_signatures(self, code: str) -> List[str]:
        """Strict validation against real OoT function signatures"""
        issues = []
        
        # Check for wrong parameter order in actor lifecycle functions
        wrong_order_patterns = [
            r"void\s+\w+_Init\(PlayState\*[^,]*,\s*Actor\*",
            r"void\s+\w+_Update\(PlayState\*[^,]*,\s*Actor\*", 
            r"void\s+\w+_Destroy\(PlayState\*[^,]*,\s*Actor\*",
            r"void\s+\w+_Draw\(PlayState\*[^,]*,\s*Actor\*",
        ]
        
        for pattern in wrong_order_patterns:
            if re.search(pattern, code):
                issues.append("CRITICAL: Wrong parameter order - should be (Actor* thisx, PlayState* play)")
        
        # Check for GlobalContext usage
        if re.search(r"GlobalContext", code):
            issues.append("CRITICAL: Uses outdated GlobalContext instead of PlayState")
            
        # Check for forbidden architectural patterns
        for pattern in self.forbidden_patterns:
            if re.search(pattern, code):
                issues.append(f"FORBIDDEN: Found non-authentic pattern: {pattern}")
        
        # Use dynamic source analyzer if available
        if self.source_analyzer:
            dynamic_issues = self.source_analyzer.validate_against_real_source(code)
            issues.extend(dynamic_issues)
        else:
            # Fallback to hardcoded validation
            func_pattern = r'(\w+)\s*\('
            unknown_functions = []
            for match in re.finditer(func_pattern, code):
                func_name = match.group(1)
                if (func_name not in self.authentic_function_signatures and 
                    func_name not in ['if', 'for', 'while', 'switch', 'sizeof', 'typedef'] and
                    not func_name.startswith('g') and  # Skip display lists
                    not func_name.isupper() and  # Skip macros
                    len(func_name) > 3):  # Skip short names
                    unknown_functions.append(func_name)
                    
            if unknown_functions:
                issues.append(f"NON-AUTHENTIC: Unknown functions: {', '.join(unknown_functions[:5])}")
        
        return issues

    def validate_architectural_authenticity(self, code: str, instruction: str) -> List[str]:
        """Validate against authentic OoT architectural patterns"""
        issues = []
        
        # Check for custom heart piece actors (should use EnItem00)
        if "heart piece" in instruction.lower() and "ACTOR_HEART_PIECE" in code:
            issues.append("ARCHITECTURAL: Heart pieces should use EnItem00 with ITEM00_HEART_PIECE parameter")
            
        # Check for custom collectible actors
        collectible_keywords = ["rupee", "key", "magic jar", "arrow bundle"]
        if any(keyword in instruction.lower() for keyword in collectible_keywords):
            if "EnItem00" not in code and "ACTOR_EN_ITEM00" not in code:
                issues.append("ARCHITECTURAL: Collectibles should typically use EnItem00 (see z_en_item00.c)")
        
        # Check for proper ActorProfile usage
        if "ActorInit" in code:
            issues.append("NAMING: Should use ActorProfile, not ActorInit")
            
        return issues

    def apply_mandatory_corrections(self, code: str) -> str:
        """Apply mandatory corrections for authenticity"""
        corrected = code
        
        for old_pattern, new_pattern in self.mandatory_corrections.items():
            corrected = corrected.replace(old_pattern, new_pattern)
        
        # Fix parameter order with regex
        parameter_fixes = [
            (r"void\s+(\w+)_Init\(PlayState\*\s+(\w+),\s*Actor\*\s+(\w+)\)",
             r"void \1_Init(Actor* \3, PlayState* \2)"),
            (r"void\s+(\w+)_Update\(PlayState\*\s+(\w+),\s*Actor\*\s+(\w+)\)",
             r"void \1_Update(Actor* \3, PlayState* \2)"),
            (r"void\s+(\w+)_Destroy\(PlayState\*\s+(\w+),\s*Actor\*\s+(\w+)\)",
             r"void \1_Destroy(Actor* \3, PlayState* \2)"),
            (r"void\s+(\w+)_Draw\(PlayState\*\s+(\w+),\s*Actor\*\s+(\w+)\)",
             r"void \1_Draw(Actor* \3, PlayState* \2)"),
        ]
        
        for old_regex, new_format in parameter_fixes:
            corrected = re.sub(old_regex, new_format, corrected)
            
        return corrected

    def calculate_authenticity_score(self, code: str) -> float:
        """Calculate authenticity score based on real OoT patterns"""
        score = 10.0  # Start with perfect score
        
        # Major penalties for forbidden patterns
        for pattern in self.forbidden_patterns:
            if re.search(pattern, code):
                score -= 2.0
                
        # Check function authenticity
        func_pattern = r'(\w+)\s*\('
        total_functions = 0
        authentic_functions = 0
        
        for match in re.finditer(func_pattern, code):
            func_name = match.group(1)
            if (func_name not in ['if', 'for', 'while', 'switch', 'sizeof', 'typedef'] and
                not func_name.startswith('g') and not func_name.isupper() and len(func_name) > 3):
                total_functions += 1
                if func_name in self.authentic_function_signatures:
                    authentic_functions += 1
                    
        if total_functions > 0:
            func_authenticity = authentic_functions / total_functions
            score = score * func_authenticity + (score * 0.1)  # Blend score based on function authenticity
        
        # Bonus for required patterns
        required_found = sum(1 for pattern in self.required_patterns if re.search(pattern, code))
        if required_found >= len(self.required_patterns) * 0.8:
            score += 1.0
            
        return max(0.0, min(10.0, score)) 