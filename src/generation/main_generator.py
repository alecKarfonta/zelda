#!/usr/bin/env python3
"""
Main OoT Training Data Generator
"""

import os
import json
import time
import random
import re
from typing import Dict, List, Optional

import anthropic

from core.logger import logger
from models.enums import ExampleType, TrainingExample, ActorCategory
from analyzers.source_analyzer import DynamicSourceAnalyzer
from validation.authenticity_validator import StrictAuthenticityValidator
from generation.diversity_injector import DiversityInjector
from generation.temperature_manager import DynamicTemperatureManager
from parsers.response_parser import ResponseParser


class EnhancedOoTTrainingGenerator:
    """Enhanced generator with strict authenticity + real OoT decompilation data + diversity injection"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022", 
                 oot_path: str = "oot", use_dynamic_analysis: bool = True):
        # Try to get API key from environment first, then parameter
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY in .env file or pass as parameter")
            
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
        
        # Initialize dynamic source analyzer if enabled
        logger.info(f"🔍 Initializing dynamic source analysis from {oot_path}...")
        self.source_analyzer = DynamicSourceAnalyzer(oot_path)
        logger.success("✅ Dynamic source analysis initialized successfully")

        self.validator = StrictAuthenticityValidator(self.source_analyzer)
        
        # Initialize diversity injector
        self.diversity_injector = DiversityInjector()
        
        # Initialize dynamic temperature manager
        self.temperature_manager = DynamicTemperatureManager()
        
        # Initialize response parser
        self.response_parser = ResponseParser()
        
        # Initialize validation and context system
        from helpers.validate_and_enhance_scenarios import OoTPatternValidator
        from helpers.complete_context_generator import CompleteOoTContextGenerator
        self.pattern_validator = OoTPatternValidator(oot_path)
        self.context_generator = CompleteOoTContextGenerator(oot_path)
        self.use_validation = True
        logger.success("✅ Enhanced validation and context generation enabled")
        
        # Load authentic reference patterns from real decompilation
        self.authentic_examples = self._load_real_oot_examples()
        self.context_templates = self._load_enhanced_contexts()
        
        # Track generation statistics
        self.generation_stats = {
            "total_generated": 0,
            "total_accepted": 0,
            "total_rejected": 0,
            "category_distribution": {cat.value: 0 for cat in ActorCategory},
            "type_distribution": {t.value: 0 for t in ExampleType},
            "complexity_distribution": {"basic": 0, "intermediate": 0, "advanced": 0}
        }

    def _load_real_oot_examples(self) -> Dict[str, str]:
        """Load reference examples from authentic decompilation"""
        return {
            "basic_actor_authentic": """
// AUTHENTIC PATTERN from OoT decompilation (z_en_item00.c style)
typedef struct {
    /* 0x000 */ Actor actor;
    /* 0x14C */ s16 timer;
    /* 0x14E */ s16 actionState;
    /* 0x150 */ f32 scale;
    /* 0x154 */ ColliderCylinder collider;
} EnExample; // size = 0x1A0

void EnExample_Init(Actor* thisx, PlayState* play) {
    EnExample* this = (EnExample*)thisx;
    
    // Authentic collision initialization pattern
    Collider_InitCylinder(play, &this->collider);
    Collider_SetCylinder(play, &this->collider, &this->actor, &sCylinderInit);
    
    // Authentic actor setup
    Actor_SetScale(&this->actor, 0.01f);
    Actor_SetFocus(&this->actor, 50.0f);
    
    this->timer = 0;
    this->actionState = 0;
}

void EnExample_Update(Actor* thisx, PlayState* play) {
    EnExample* this = (EnExample*)thisx;
    
    // Authentic collision update pattern
    Actor_UpdateBgCheckInfo(play, &this->actor, 26.0f, 10.0f, 0.0f, BGCHECKFLAG_GROUND);
    Collider_UpdateCylinder(&this->actor, &this->collider);
    CollisionCheck_SetOC(play, &play->colChkCtx, &this->collider.base);
    
    // Authentic movement pattern
    Actor_MoveXZGravity(&this->actor);
}

// AUTHENTIC ActorProfile from decompilation
const ActorProfile En_Example_Profile = {
    /**/ ACTOR_EN_EXAMPLE,
    /**/ ACTORCAT_MISC,
    /**/ FLAGS,
    /**/ OBJECT_GAMEPLAY_KEEP,
    /**/ sizeof(EnExample),
    /**/ EnExample_Init,
    /**/ EnExample_Destroy,
    /**/ EnExample_Update,
    /**/ EnExample_Draw,
};
""",
            
            "collectible_authentic_item00": """
// AUTHENTIC COLLECTIBLE PATTERN - Use EnItem00 from z_en_item00.c
// Heart pieces use ITEM00_HEART_PIECE (0x06)
// Blue rupees use ITEM00_RUPEE_BLUE (0x01) 
// Small keys use ITEM00_SMALL_KEY (0x0B)

void SpawnHeartPiece(PlayState* play, Vec3f* pos) {
    // Authentic pattern from z_en_item00.c
    Actor_Spawn(&play->actorCtx, play, ACTOR_EN_ITEM00, 
                pos->x, pos->y, pos->z, 0, 0, 0, ITEM00_HEART_PIECE);
}

void SpawnBlueRupee(PlayState* play, Vec3f* pos) {
    Actor_Spawn(&play->actorCtx, play, ACTOR_EN_ITEM00,
                pos->x, pos->y, pos->z, 0, 0, 0, ITEM00_RUPEE_BLUE);
}
""",
            
            "real_collision_patterns": """
// AUTHENTIC COLLISION PATTERNS from z_collision_check.c

static ColliderCylinderInit sCylinderInit = {
    {
        COL_MATERIAL_NONE,
        AT_NONE,
        AC_ON | AC_TYPE_PLAYER,
        OC1_ON | OC1_TYPE_ALL,
        OC2_TYPE_1,
        COLSHAPE_CYLINDER,
    },
    {
        ELEM_MATERIAL_UNK0,
        { 0x00000000, HIT_SPECIAL_EFFECT_NONE, 0x00 },
        { 0x00000010, HIT_BACKLASH_NONE, 0x00 },
        ATELEM_NONE,
        ACELEM_ON,
        OCELEM_ON,
    },
    { 15, 25, 0, { 0, 0, 0 } },
};

// Authentic initialization sequence
Collider_InitCylinder(play, &this->collider);
Collider_SetCylinder(play, &this->collider, &this->actor, &sCylinderInit);

// Authentic update sequence  
Collider_UpdateCylinder(&this->actor, &this->collider);
CollisionCheck_SetOC(play, &play->colChkCtx, &this->collider.base);
""",
        }

    def _load_enhanced_contexts(self) -> Dict[str, str]:
        """Load contexts with strict requirements + real examples"""
        
        # Get dynamic function list if available
        function_list = list(self.source_analyzer.real_functions.keys())[:20]
        function_count = len(self.source_analyzer.real_functions)
        additional_info = f"""
REAL SOURCE DATA AVAILABLE:
   📁 Analyzed {len(self.source_analyzer.analyzed_files)} source files
   🔧 Found {len(self.source_analyzer.real_functions)} functions
   📊 Found {len(self.source_analyzer.real_structs)} structs
   📋 Found {len(self.source_analyzer.real_enums)} enums
   🔧 Found {len(self.source_analyzer.real_constants)} constants
"""
        return {
            "strict_requirements": f"""
CRITICAL AUTHENTICITY REQUIREMENTS (ENFORCED BY VALIDATION):
{additional_info}
1. FUNCTION SIGNATURES (MANDATORY):
   ✓ Actor lifecycle MUST use: FuncName(Actor* thisx, PlayState* play)
   ✗ NEVER use: FuncName(PlayState* play, Actor* thisx) 
   ✓ ALWAYS use PlayState*, NEVER GlobalContext*

2. ARCHITECTURAL ACCURACY (MANDATORY):
   ✓ Heart pieces: Use EnItem00 with ITEM00_HEART_PIECE parameter
   ✓ Rupees: Use EnItem00 with ITEM00_RUPEE_* parameters  
   ✓ Most collectibles: Use EnItem00, not custom actors
   ✓ Reference z_en_item00.c for collectible patterns

3. POSITION ACCESS (MANDATORY):
   ✓ Use actor.world.pos, NEVER actor.pos
   ✓ Use actor.world.rot, NEVER actor.rot

4. REAL FUNCTION USAGE (MANDATORY):
   Must use ONLY functions from actual OoT decompilation:
   {', '.join(function_list)}...
   (and {function_count} more real functions)

5. COLLISION PATTERNS (MANDATORY):
   ✓ Use Collider_InitCylinder(play, &collider)
   ✓ Use Collider_SetCylinder(play, &collider, &actor, &init)
   ✓ Follow patterns from z_collision_check.c

VALIDATION WILL REJECT ANY EXAMPLE VIOLATING THESE REQUIREMENTS.
""",
            
            "authentic_actor_context": f"""
AUTHENTIC ACTOR SYSTEM (FROM REAL OoT DECOMPILATION):

REAL ACTOR STRUCTURE PATTERN (from actor.h):
```c
typedef struct {{
    /* 0x0000 */ Actor actor;  // Base actor (size 0x14C)
    /* 0x014C */ // Custom fields start here with proper offsets
    /* 0x014C */ s16 timer;
    /* 0x014E */ s16 actionState;
    /* 0x0150 */ f32 customScale;
    /* 0x0154 */ ColliderCylinder collider;  // If collision needed
}} ActorName; // size = calculated correctly

// MANDATORY: Exact parameter order from decompilation
void ActorName_Init(Actor* thisx, PlayState* play) {{
    ActorName* this = (ActorName*)thisx;
    // Authentic patterns from z_actor.c and z_en_item00.c
}}

void ActorName_Update(Actor* thisx, PlayState* play) {{
    ActorName* this = (ActorName*)thisx;
    // Authentic patterns from z_actor.c
}}

// MANDATORY: Exact ActorProfile format from real decompilation
const ActorProfile ActorName_Profile = {{
    /**/ ACTOR_ACTORNAME,
    /**/ ACTORCAT_MISC,
    /**/ FLAGS,
    /**/ OBJECT_ACTORNAME,
    /**/ sizeof(ActorName),
    /**/ ActorName_Init,
    /**/ ActorName_Destroy,
    /**/ ActorName_Update,
    /**/ ActorName_Draw,
}};
```

AUTHENTIC REFERENCE EXAMPLE:
{self.authentic_examples['basic_actor_authentic']}
""",
        }

    def generate_training_example(self, example_type: ExampleType, complexity: str = "intermediate") -> TrainingExample:
        """Generate with strict authenticity validation + diversity injection + refinement"""
        
        # Update generation stats
        self.generation_stats["total_generated"] += 1
        self.generation_stats["type_distribution"][example_type.value] += 1
        self.generation_stats["complexity_distribution"][complexity] += 1
        
        # Phase 1: Generate with diversity injection
        example = self._generate_with_diverse_prompt(example_type, complexity)
        
        if not example:
            logger.debug(f"[DEBUG] Generation failed - no example returned")
            return TrainingExample(example_type=example_type, instruction="", output="")
        
        # Phase 2: Multi-pass validation and correction
        example = self._multi_pass_validation(example)
        
        # Fix instruction if it's a placeholder
        if example.instruction.strip().lower() in ["clear instruction", "", None]:
            logger.warning(f"[WARNING] Instruction is a placeholder, generating a new one")
            # Try to get a better scenario
            diverse_instruction = self.diversity_injector.get_diverse_instruction(example_type, complexity)
            example.instruction = diverse_instruction
        
        # Phase 3: Final authenticity scoring
        example.authenticity_score = self.validator.calculate_authenticity_score(example.output)
        
        # More lenient rejection criteria
        quality_threshold = 4.0  # Reduced from 6.0
        authenticity_threshold = 4.0  # Reduced from 6.0
        
        if example.authenticity_score < authenticity_threshold or example.quality_score < quality_threshold:
            logger.error(f"[REJECT] Quality: {example.quality_score:.1f}, Auth: {example.authenticity_score:.1f}")
            logger.debug(f"[DEBUG] Instruction: {example.instruction[:50]}...")
            logger.debug(f"[DEBUG] Output length: {len(example.output)}")
            logger.debug(f"[DEBUG] Validation notes: {example.validation_notes}")
            self.generation_stats["total_rejected"] += 1
            return TrainingExample(example_type=example_type, instruction="", output="")
        
        # Update acceptance stats
        self.generation_stats["total_accepted"] += 1
            
        return example

    def _generate_with_diverse_prompt(self, example_type: ExampleType, complexity: str) -> Optional[TrainingExample]:
        """Generate with diversity injection and enhanced prompts"""
        
        # Get diverse instruction from injector
        diverse_instruction = self.diversity_injector.get_diverse_instruction(example_type, complexity)
        
        # Get dynamic temperature based on diversity needs
        diversity_metrics = {
            "actor_categories": {cat.value: 0 for cat in ActorCategory},
            "example_types": {t.value: 0 for t in ExampleType},
            "complexities": {"basic": 0, "intermediate": 0, "advanced": 0},
            "unique_scenarios": set()
        }
        dynamic_temperature = self.temperature_manager.get_dynamic_temperature(example_type, complexity, diversity_metrics)
        
        # Create enhanced prompt
        enhanced_prompt = self._create_enhanced_prompt(diverse_instruction, example_type, complexity)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=dynamic_temperature,  # Use dynamic temperature
                messages=[{"role": "user", "content": enhanced_prompt}]
            )
            
            # Handle different types of content blocks
            content_block = response.content[0]
            if content_block.type == 'text':
                raw_response = content_block.text
            else:
                raw_response = str(content_block)
            return self.response_parser.parse_response(raw_response, example_type)
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return None

    def _create_enhanced_prompt(self, instruction: str, example_type: ExampleType, complexity: str) -> str:
        """Create enhanced prompt with all necessary context"""
        
        # Get context snippets
        header_block, macro_block, example_block = self._get_context_snippets(example_type)
        
        # Get relevant functions and constants
        category = self._map_example_type_to_category(example_type)
        relevant_functions = self._get_relevant_functions_and_constants(example_type, category)
        functions_and_constants = '\n'.join(f'- {f}' for f in relevant_functions)
        
        # Create the enhanced prompt
        prompt = f"""
{self.context_templates["strict_requirements"]}

{self.context_templates["authentic_actor_context"]}

AUTHENTIC OoT HEADER SNIPPETS:
{header_block}

AUTHENTIC OoT MACRO SNIPPETS:
{macro_block}

AUTHENTIC OoT EXAMPLE SNIPPETS:
{example_block}

RELEVANT AUTHENTIC FUNCTIONS AND CONSTANTS:
{functions_and_constants}

INSTRUCTION: {instruction}

COMPLEXITY: {complexity}

You are generating diverse OoT romhacking training data. You MUST follow authentic decompilation patterns exactly while creating varied and interesting content.

Return exactly this JSON:
{{
  "instruction": "{instruction}",
  "input": null,
  "output": "Authentic C code here"
}}
"""
        
        return prompt

    def _multi_pass_validation(self, example: TrainingExample) -> TrainingExample:
        """Multi-pass validation with progressive correction"""
        
        # Pass 1: Function signature validation against real functions
        signature_issues = self.validator.validate_function_signatures(example.output)
        if signature_issues:
            example.validation_notes += f"Signature issues: {len(signature_issues)}. "
            # Apply mandatory corrections
            example.output = self.validator.apply_mandatory_corrections(example.output)
        
        # Pass 2: Architectural validation against real patterns
        arch_issues = self.validator.validate_architectural_authenticity(example.output, example.instruction)
        if arch_issues:
            example.validation_notes += f"Architecture issues: {len(arch_issues)}. "
        
        # Pass 3: Additional source-based validation
        if self.source_analyzer:
            source_issues = self.source_analyzer.validate_against_real_source(example.output)
            if source_issues:
                example.validation_notes += f"Source validation issues: {len(source_issues)}. "
        
        # Pass 4: Final quality scoring
        example.quality_score = self._calculate_quality_score(example)
        
        return example

    def _calculate_quality_score(self, example: TrainingExample) -> float:
        """Enhanced quality scoring with authenticity focus"""
        score = 5.0
        
        # Basic content quality
        if len(example.instruction) > 20:
            score += 0.5
        if len(example.output) > 200:
            score += 1.0
        if "```c" in example.output:
            score += 1.0
            
        # Real function usage bonus
        func_pattern = r'(\w+)\s*\('
        total_functions = 0
        real_functions = 0
        
        for match in re.finditer(func_pattern, example.output):
            func_name = match.group(1)
            if (func_name not in ['if', 'for', 'while', 'switch', 'sizeof', 'typedef'] and
                not func_name.startswith('g') and not func_name.isupper() and len(func_name) > 3):
                total_functions += 1
                if func_name in self.validator.authentic_function_signatures:
                    real_functions += 1
                    
        if total_functions > 0:
            real_func_ratio = real_functions / total_functions
            score += real_func_ratio * 2.0  # Up to +2.0 for real functions
            
        # Authenticity pattern bonuses
        authentic_patterns = [
            "Actor* thisx, PlayState* play",
            "world.pos", 
            "ActorProfile",
            "Collider_InitCylinder",
            "ACTORCAT_",
            "EnItem00",  # For collectibles
        ]
        
        for pattern in authentic_patterns:
            if pattern in example.output:
                score += 0.3
                
        # Heavy penalties for non-authentic patterns
        if "GlobalContext" in example.output:
            score -= 3.0
        if "PlayState* play, Actor* thisx" in example.output:
            score -= 3.0
        if re.search(r"\.pos\.", example.output):  # Direct pos access
            score -= 1.0
            
        return max(0.0, min(10.0, score))

    def _map_example_type_to_category(self, example_type: ExampleType) -> str:
        """Map ExampleType to validation category"""
        mapping = {
            ExampleType.ACTOR_CREATION: "enemy",  # Actor creation can be enemy, npc, or object
            ExampleType.ANIMATION_SYSTEM: "object",  # Animation systems are typically objects/mechanics
            ExampleType.COLLISION_SYSTEM: "object",  # Collision systems are mechanics
            ExampleType.INTERACTION_SYSTEM: "npc",   # Interaction systems are typically NPC-related
            ExampleType.EFFECT_SYSTEM: "object",     # Effect systems are mechanics
            ExampleType.SOUND_SYSTEM: "object",      # Sound systems are mechanics
            ExampleType.AI_BEHAVIOR: "enemy",        # AI behavior is typically enemy-related
            ExampleType.ENVIRONMENTAL: "object",     # Environmental systems are objects/mechanics
            ExampleType.COMBAT_SYSTEM: "enemy",      # Combat systems are enemy-related
            ExampleType.PUZZLE_SYSTEM: "object",     # Puzzle systems are objects/mechanics
            ExampleType.UI_SYSTEM: "object",         # UI systems are objects/mechanics
            ExampleType.MEMORY_MANAGEMENT: "object", # Memory management is mechanics
            ExampleType.OPTIMIZATION: "object",      # Optimization is mechanics
            ExampleType.DEBUGGING_TOOLS: "object",   # Debugging tools are mechanics
            ExampleType.CUSTOM_MECHANICS: "object",  # Custom mechanics are objects
            ExampleType.CODE_EXPLANATION: "object",  # Code explanations are generic
            ExampleType.FEATURE_IMPLEMENTATION: "object", # Feature implementations are objects
            ExampleType.DEBUGGING_HELP: "object"     # Debugging help is generic
        }
        return mapping.get(example_type, "object")

    def _get_context_snippets(self, example_type: ExampleType):
        """Get header, macro, and example snippets"""
        # Placeholder - would integrate with helpers.oot_context_cache
        return "// Header snippets", "// Macro snippets", "// Example snippets"

    def _get_relevant_functions_and_constants(self, example_type: ExampleType, category: str) -> List[str]:
        """Get relevant functions and constants for the example type"""
        # Placeholder - would load from database files
        return [
            "Actor_Init", "Actor_Destroy", "Actor_Update", "Actor_Draw",
            "Collider_InitCylinder", "Collider_SetCylinder", "Collider_UpdateCylinder",
            "Actor_SetScale", "Actor_SetFocus", "Actor_UpdateBgCheckInfo"
        ]

    def generate_dataset(self, num_examples: int = 50, output_file: str = "authentic_oot_training.jsonl") -> None:
        """Generate dataset with strict quality control + diversity injection"""
        
        examples = []
        example_types = list(ExampleType)
        rejected_count = 0
        
        # Enhanced example type distribution for better diversity
        type_weights = {
            ExampleType.ACTOR_CREATION: 0.25,      # Core actor creation
            ExampleType.ANIMATION_SYSTEM: 0.08,     # Animation systems
            ExampleType.COLLISION_SYSTEM: 0.08,     # Collision systems  
            ExampleType.INTERACTION_SYSTEM: 0.08,   # Interaction systems
            ExampleType.EFFECT_SYSTEM: 0.08,        # Effect systems
            ExampleType.SOUND_SYSTEM: 0.06,         # Sound systems
            ExampleType.AI_BEHAVIOR: 0.08,          # AI behavior systems
            ExampleType.ENVIRONMENTAL: 0.06,        # Environmental systems
            ExampleType.COMBAT_SYSTEM: 0.06,        # Combat systems
            ExampleType.PUZZLE_SYSTEM: 0.06,        # Puzzle systems
            ExampleType.CUSTOM_MECHANICS: 0.05,     # Custom mechanics
            ExampleType.CODE_EXPLANATION: 0.03,     # Code explanations
            ExampleType.FEATURE_IMPLEMENTATION: 0.03, # Feature implementations
            ExampleType.DEBUGGING_HELP: 0.02,       # Debugging help
            ExampleType.UI_SYSTEM: 0.02,            # UI systems
            ExampleType.MEMORY_MANAGEMENT: 0.02,    # Memory management
            ExampleType.OPTIMIZATION: 0.02,         # Optimization
            ExampleType.DEBUGGING_TOOLS: 0.02,      # Debugging tools
        }
        
        # Complexity distribution for better variety
        complexity_weights = {
            "basic": 0.2,
            "intermediate": 0.5, 
            "advanced": 0.3
        }
        
        logger.generation(f"Generating {num_examples} diverse authentic examples...")
        logger.stats(f"Using {len(self.validator.authentic_function_signatures)} real OoT functions for validation")
        logger.stats(f"Target distribution: {len(type_weights)} example types with weighted selection")
        
        # Track diversity metrics
        diversity_metrics = {
            "actor_categories": {cat.value: 0 for cat in ActorCategory},
            "example_types": {t.value: 0 for t in ExampleType},
            "complexities": {"basic": 0, "intermediate": 0, "advanced": 0},
            "unique_scenarios": set()
        }
        
        for i in range(num_examples * 3):  # Generate more to account for rejections and diversity
            if len(examples) >= num_examples:
                break
                
            # Weighted selection for example type
            available_types = [t for t in example_types if t in type_weights]
            type_weights_list = [type_weights.get(t, 0.01) for t in available_types]
            example_type = random.choices(available_types, weights=type_weights_list, k=1)[0]
            
            # Weighted selection for complexity
            complexity = random.choices(list(complexity_weights.keys()), 
                                     weights=list(complexity_weights.values()), k=1)[0]
            
            logger.generation(f"Generating example {len(examples)+1}/{num_examples}: {example_type.value} ({complexity})")
            
            try:
                example = self.generate_training_example(example_type, complexity)
                
                # Enhanced acceptance criteria with diversity bonus
                base_quality = example.quality_score >= 7.0
                base_authenticity = example.authenticity_score >= 7.0
                base_length = len(example.output) > 100
                
                # Diversity bonus: boost score for underrepresented categories
                diversity_bonus = self._calculate_diversity_bonus(example, diversity_metrics)
                
                if base_quality and base_authenticity and base_length:
                    # Apply diversity bonus
                    final_score = example.quality_score + diversity_bonus
                    
                    if final_score >= 7.0:
                        examples.append(example)
                        
                        # Update diversity metrics
                        self._update_diversity_metrics(example, diversity_metrics)
                        
                        # Update temperature manager
                        self.temperature_manager.update_usage(example, diversity_metrics)
                        
                        logger.success(f"  ✓ ACCEPTED - Quality: {example.quality_score:.1f}, Auth: {example.authenticity_score:.1f}, Diversity: +{diversity_bonus:.1f}")
                    else:
                        rejected_count += 1
                        logger.warning(f"  ✗ REJECTED - Quality: {example.quality_score:.1f}, Auth: {example.authenticity_score:.1f}, Diversity: +{diversity_bonus:.1f}")
                else:
                    rejected_count += 1
                    logger.warning(f"  ✗ REJECTED - Quality: {example.quality_score:.1f}, Auth: {example.authenticity_score:.1f}")
                    
            except Exception as e:
                logger.error(f"  ✗ ERROR: {e}")
                rejected_count += 1
                
            time.sleep(0.5)  # Rate limiting
        
        # Save results with enhanced metadata
        self._save_dataset_with_diversity(examples, output_file, diversity_metrics)
        
        logger.info(f"\nFINAL RESULTS:")
        logger.success(f"✓ Accepted: {len(examples)} examples")
        logger.warning(f"✗ Rejected: {rejected_count} examples")
        logger.stats(f"📊 Acceptance rate: {len(examples)/(len(examples)+rejected_count)*100:.1f}%")
        logger.info(f" Diversity achieved:")
        logger.info(f"   - Actor categories: {len([c for c in diversity_metrics['actor_categories'].values() if c > 0])}/14")
        logger.info(f"   - Example types: {len([t for t in diversity_metrics['example_types'].values() if t > 0])}/{len(ExampleType)}")
        logger.info(f"   - Unique scenarios: {len(diversity_metrics['unique_scenarios'])}")
        logger.file_ops(f" Saved to: {output_file}")

    def _calculate_diversity_bonus(self, example: TrainingExample, diversity_metrics: Dict) -> float:
        """Calculate diversity bonus for underrepresented categories"""
        bonus = 0.0
        
        # Check actor category diversity
        for category, keywords in {
            ActorCategory.ENEMY: ["enemy", "dodongo", "karebaba", "wallmaster", "stalfos"],
            ActorCategory.NPC: ["npc", "zora", "goron", "kokiri", "hylian", "gerudo"],
            ActorCategory.ITEM: ["item", "heart", "rupee", "bomb", "arrow", "bottle"],
            ActorCategory.OBJECT: ["object", "switch", "lift", "door", "chest", "torch"],
            ActorCategory.BACKGROUND: ["background", "temple", "water", "fire", "forest"],
            ActorCategory.EFFECT: ["effect", "song", "magic", "spell", "ocarina"],
            ActorCategory.PLAYER: ["player", "sword", "fishing", "ocarina", "bottle", "mask", "magic"],
            ActorCategory.MISC: ["fishing", "horse", "owl", "gossip", "treasure"]
        }.items():
            if any(keyword.lower() in example.instruction.lower() for keyword in keywords):
                category_count = diversity_metrics['actor_categories'][category.value]
                if category_count < 2:  # Boost underrepresented categories
                    bonus += 1.0
                break
        
        # Check example type diversity
        type_count = diversity_metrics['example_types'][example.example_type.value]
        if type_count < 2:  # Boost underrepresented types
            bonus += 0.5
        
        # Check scenario uniqueness
        if example.instruction not in diversity_metrics['unique_scenarios']:
            bonus += 0.3
        
        return bonus

    def _update_diversity_metrics(self, example: TrainingExample, diversity_metrics: Dict) -> None:
        """Update diversity tracking metrics"""
        
        # Update actor category counts
        for category, keywords in {
            ActorCategory.ENEMY: ["enemy", "dodongo", "karebaba", "wallmaster", "stalfos"],
            ActorCategory.NPC: ["npc", "zora", "goron", "kokiri", "hylian", "gerudo"],
            ActorCategory.ITEM: ["item", "heart", "rupee", "bomb", "arrow", "bottle"],
            ActorCategory.OBJECT: ["object", "switch", "lift", "door", "chest", "torch"],
            ActorCategory.BACKGROUND: ["background", "temple", "water", "fire", "forest"],
            ActorCategory.EFFECT: ["effect", "song", "magic", "spell", "ocarina"],
            ActorCategory.PLAYER: ["player", "sword", "fishing", "ocarina", "bottle", "mask", "magic"],
            ActorCategory.MISC: ["fishing", "horse", "owl", "gossip", "treasure"]
        }.items():
            if any(keyword.lower() in example.instruction.lower() for keyword in keywords):
                diversity_metrics['actor_categories'][category.value] += 1
                break
        
        # Update example type counts
        diversity_metrics['example_types'][example.example_type.value] += 1
        
        # Update unique scenarios
        diversity_metrics['unique_scenarios'].add(example.instruction)

    def _save_dataset_with_diversity(self, examples: List[TrainingExample], output_file: str, diversity_metrics: Dict) -> None:
        """Save dataset with enhanced diversity metadata"""
        
        # Training data format
        with open(output_file, 'w') as f:
            for example in examples:
                record = {"instruction": example.instruction, "output": example.output}
                if example.input:
                    record["input"] = example.input
                f.write(json.dumps(record) + '\n')
        
        # Enhanced analysis with diversity metrics
        metadata = {
            "total_examples": len(examples),
            "average_quality": sum(e.quality_score for e in examples) / len(examples) if examples else 0.0,
            "average_authenticity": sum(e.authenticity_score for e in examples) / len(examples) if examples else 0.0,
            "type_distribution": {t.value: sum(1 for e in examples if e.example_type == t) for t in ExampleType},
            "real_functions_used": len(self.validator.authentic_function_signatures),
            "diversity_metrics": {
                "actor_categories": diversity_metrics['actor_categories'],
                "example_types": diversity_metrics['example_types'],
                "unique_scenarios": len(diversity_metrics['unique_scenarios']),
                "category_coverage": len([c for c in diversity_metrics['actor_categories'].values() if c > 0]),
                "type_coverage": len([t for t in diversity_metrics['example_types'].values() if t > 0])
            },
            "generation_stats": self.generation_stats,
            "validation_summary": [
                {
                    "instruction": e.instruction[:100] + "..." if len(e.instruction) > 100 else e.instruction,
                    "type": e.example_type.value,
                    "quality_score": e.quality_score,
                    "authenticity_score": e.authenticity_score,
                    "validation_notes": e.validation_notes
                } for e in examples
            ]
        }
        
        metadata_file = output_file.replace('.jsonl', '_diversity_analysis.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2) 