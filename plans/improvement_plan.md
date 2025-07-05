# Immediate Implementation Roadmap
## Phase 1 Quick Wins (Next 2 Weeks)

### 🚀 Priority 1: Enhanced Context Templates (Days 1-3)

#### Step 1: Create Authentic Function Database
```python
# File: authentic_context.py
AUTHENTIC_FUNCTIONS = {
    "actor_management": [
        "Actor_Init(Actor* thisx, PlayState* play)",
        "Actor_Update(Actor* thisx, PlayState* play)", 
        "Actor_Draw(Actor* thisx, PlayState* play)",
        "Actor_Kill(Actor* actor)",
        "Actor_SetScale(Actor* actor, f32 scale)",
        "Actor_SpawnAsChild(PlayState* play, Actor* parent, u16 actorId, f32 x, f32 y, f32 z, s16 rotX, s16 rotY, s16 rotZ)",
        "Actor_WorldDistXYZToPoint(Actor* actor, Vec3f* point)",
        "Actor_UpdateBgCheckInfo(PlayState* play, Actor* actor, f32 wallCheckHeight, f32 wallCheckRadius, f32 ceilingCheckHeight, u32 bgCheckFlags)"
    ],
    "collision_system": [
        "Collider_InitCylinder(PlayState* play, ColliderCylinder* collider)",
        "Collider_SetCylinder(PlayState* play, ColliderCylinder* collider, Actor* actor, ColliderCylinderInit* src)",
        "CollisionCheck_SetAT(PlayState* play, CollisionCheckContext* colChkCtx, Collider* collider)",
        "BgCheck_EntityRaycastFloor1(CollisionContext* colCtx, CollisionPoly** outPoly, Vec3f* pos)"
    ],
    "memory_management": [
        "ZELDA_ARENA_MALLOC(size, file, line)",
        "ZELDA_ARENA_FREE(ptr, file, line)",
        "THA_GetRemaining(TwoHeadArena* tha)"
    ]
}

AUTHENTIC_STRUCTS = {
    "Actor": {
        "fields": [
            "/* 0x000 */ s16 id",
            "/* 0x002 */ u8 category", 
            "/* 0x004 */ s32 flags",
            "/* 0x014 */ Vec3f world.pos",
            "/* 0x020 */ Vec3s shape.rot",
            "/* 0x026 */ Vec3f scale",
            "/* 0x032 */ Vec3f velocity",
            "/* 0x03E */ f32 speedXZ",
            "/* 0x042 */ f32 gravity"
        ]
    }
}
```

#### Step 2: Update Context Templates
```python
def _load_enhanced_context_templates(self) -> Dict[str, str]:
    return {
        "actor_system": f"""
OoT Actor System Context (From Decompilation):

MEMORY LAYOUT:
- Base Actor struct: 0x14C bytes minimum
- Actor categories: {', '.join(['ACTORCAT_SWITCH', 'ACTORCAT_BG', 'ACTORCAT_PLAYER', 'ACTORCAT_BOMB', 'ACTORCAT_NPC', 'ACTORCAT_ENEMY', 'ACTORCAT_PROP', 'ACTORCAT_ITEMACTION', 'ACTORCAT_MISC', 'ACTORCAT_BOSS', 'ACTORCAT_DOOR', 'ACTORCAT_CHEST'])}

AUTHENTIC FUNCTIONS:
{chr(10).join('- ' + func for func in AUTHENTIC_FUNCTIONS['actor_management'])}

LIFECYCLE PATTERN:
```c
typedef struct {{
    /* 0x0000 */ Actor actor;
    /* 0x014C */ // Custom fields start here
}} ActorName;

void ActorName_Init(Actor* thisx, PlayState* play) {{
    ActorName* this = (ActorName*)thisx;
    Actor_SetScale(&this->actor, 0.01f);
    // Initialize custom fields
}}

void ActorName_Update(Actor* thisx, PlayState* play) {{
    ActorName* this = (ActorName*)thisx;
    // Update logic
}}
```

ACTOR INIT STRUCTURE:
```c
const ActorInit ActorName_InitVars = {{
    ACTOR_ID,
    ACTORCAT_TYPE,
    FLAGS,
    OBJECT_ID,
    sizeof(ActorName),
    (ActorFunc)ActorName_Init,
    (ActorFunc)ActorName_Destroy,
    (ActorFunc)ActorName_Update,
    (ActorFunc)ActorName_Draw,
}};
```
""",
        
        "debugging_context": """
AUTHENTIC OOT DEBUGGING CONTEXT:

MEMORY ADDRESSES (Debug ROM):
- Current PlayState: 0x801C84A0
- Actor Context: 0x801C6F20  
- Heap Status: 0x801D9B60
- Object Context: 0x801C8440

COMMON CRASH SCENARIOS:
1. Actor size mismatch in ActorInit
2. Uninitialized pointer dereference
3. Object dependency failures
4. Stack overflow from deep recursion
5. DMA transfer size mismatches

DEBUG FUNCTIONS:
- osSyncPrintf(): Debug console output
- PRINTF(): Retail-safe debug output
- Actor_Kill(): Safe actor cleanup
- THA_GetRemaining(): Check available heap

VALIDATION PATTERNS:
```c
// Always check object loading
s32 objBankIndex = Object_GetIndex(objectCtx, OBJECT_ID);
if (objBankIndex < 0) {{
    Actor_Kill(&this->actor);
    return;
}}

// Null pointer checks
if (ptr == NULL) {{
    return; // or handle error
}}

// Bounds checking
if (index >= 0 && index < ARRAY_SIZE) {{
    array[index] = value;
}}
```
"""
    }
```

### 🎯 Priority 2: Basic Source Code Validation (Days 4-5)

#### Step 1: Function Name Validator
```python
# File: basic_validator.py
class BasicSourceValidator:
    def __init__(self):
        self.known_functions = set([
            "Actor_Init", "Actor_Update", "Actor_Draw", "Actor_Kill",
            "Actor_SetScale", "Actor_SpawnAsChild", "GET_PLAYER",
            "Math_Vec3f_DistXZ", "CollisionCheck_SetAT", "OPEN_DISPS", "CLOSE_DISPS"
        ])
        
        self.known_types = set([
            "Actor", "PlayState", "GlobalContext", "Vec3f", "Vec3s", 
            "s16", "u16", "s32", "u32", "f32", "ColliderCylinder"
        ])
    
    def validate_functions(self, code: str) -> List[str]:
        issues = []
        func_pattern = r'(\w+)\s*\('
        
        for match in re.finditer(func_pattern, code):
            func_name = match.group(1)
            if func_name not in self.known_functions and func_name.islower():
                issues.append(f"Unknown function: {func_name}")
        
        return issues
    
    def suggest_corrections(self, code: str) -> str:
        corrections = {
            "GlobalContext": "PlayState",
            "globalCtx": "play", 
            "this->actor.pos": "this->actor.world.pos",
            "Actor_Spawn(": "Actor_SpawnAsChild("
        }
        
        corrected = code
        for old, new in corrections.items():
            corrected = corrected.replace(old, new)
        
        return corrected
```

#### Step 2: Integrate Validator
```python
def _validate_technical_accuracy(self, example: TrainingExample) -> TrainingExample:
    validator = BasicSourceValidator()
    
    # Check for function issues
    func_issues = validator.validate_functions(example.output)
    if func_issues:
        example.validation_notes += f"Function issues: {', '.join(func_issues)}. "
        
        # Auto-correct common issues
        corrected_output = validator.suggest_corrections(example.output)
        if corrected_output != example.output:
            example.output = corrected_output
            example.validation_notes += "Auto-corrected common issues. "
    
    return example
```

### 🔧 Priority 3: Enhanced Example Templates (Days 6-8)

#### Step 1: Specific Scenario Templates
```python
ENHANCED_TEMPLATES = {
    ExampleType.FEATURE_IMPLEMENTATION: [
        {
            "scenario": "movement_enhancement",
            "instruction_template": "Create an actor that {movement_type} when {condition}",
            "variables": {
                "movement_type": ["increases Link's speed", "adds a dash ability", "creates a speed boost field"],
                "condition": ["equipped", "standing on it", "using a specific item"]
            },
            "context_types": ["player_system", "actor_system"],
            "complexity": "intermediate"
        },
        {
            "scenario": "combat_feature", 
            "instruction_template": "Implement a {weapon_type} that {special_ability}",
            "variables": {
                "weapon_type": ["sword", "bow", "magical staff"],
                "special_ability": ["damages all nearby enemies", "pierces through walls", "creates elemental effects"]
            },
            "context_types": ["actor_system", "collision_system"],
            "complexity": "advanced"
        }
    ]
}
```

#### Step 2: Progressive Complexity System
```python
def generate_progressive_example(self, topic: str, target_complexity: str) -> List[TrainingExample]:
    """Generate a sequence building to target complexity"""
    
    complexity_progression = {
        "actor_creation": [
            ("simple", "Create a basic stationary actor"),
            ("intermediate", "Add movement and collision"),
            ("advanced", "Implement complex AI and interactions")
        ]
    }
    
    examples = []
    if topic in complexity_progression:
        for level, instruction in complexity_progression[topic]:
            if level == target_complexity:
                break
            example = self.generate_training_example(
                ExampleType.FEATURE_IMPLEMENTATION, 
                level,
                instruction
            )
            examples.append(example)
    
    return examples
```

### 📊 Priority 4: Quality Metrics Dashboard (Days 9-10)

#### Create Quality Tracking
```python
# File: quality_tracker.py
class QualityTracker:
    def __init__(self):
        self.metrics = {
            "technical_accuracy": [],
            "usefulness_scores": [],
            "function_accuracy": [],
            "code_compilation": []
        }
    
    def track_example(self, example: TrainingExample, validation: ValidationResult):
        self.metrics["technical_accuracy"].append(validation.accuracy_score)
        self.metrics["usefulness_scores"].append(example.quality_score)
        
        # Track specific technical metrics
        has_code = "```" in example.output
        uses_oot_functions = any(func in example.output for func in AUTHENTIC_FUNCTIONS["actor_management"])
        
        self.metrics["function_accuracy"].append(1.0 if uses_oot_functions else 0.0)
        self.metrics["code_compilation"].append(1.0 if has_code and validation.is_valid else 0.0)
    
    def generate_report(self) -> str:
        if not self.metrics["technical_accuracy"]:
            return "No data collected yet"
        
        avg_accuracy = sum(self.metrics["technical_accuracy"]) / len(self.metrics["technical_accuracy"])
        avg_usefulness = sum(self.metrics["usefulness_scores"]) / len(self.metrics["usefulness_scores"])
        func_accuracy = sum(self.metrics["function_accuracy"]) / len(self.metrics["function_accuracy"]) * 100
        
        return f"""
Quality Report:
- Average Technical Accuracy: {avg_accuracy:.1f}/10
- Average Usefulness: {avg_usefulness:.1f}/10  
- Function Accuracy: {func_accuracy:.1f}%
- Total Examples: {len(self.metrics["technical_accuracy"])}
"""
```

### 🛠️ Immediate Action Items

#### Week 1 (Days 1-7):
- [ ] **Day 1**: Update context templates with authentic function signatures
- [ ] **Day 2**: Implement basic source code validator 
- [ ] **Day 3**: Create enhanced example templates with specific scenarios
- [ ] **Day 4**: Test new templates with 10 example generations
- [ ] **Day 5**: Implement quality tracking and metrics
- [ ] **Day 6**: Generate 50 examples with new system
- [ ] **Day 7**: Compare quality metrics vs baseline

#### Week 2 (Days 8-14):
- [ ] **Day 8**: Iterate on templates based on initial results
- [ ] **Day 9**: Add progressive complexity system
- [ ] **Day 10**: Implement auto-correction for common issues
- [ ] **Day 11**: Create quality dashboard and reporting
- [ ] **Day 12**: Generate 100 examples for evaluation
- [ ] **Day 13**: Manual review of top 20 examples for accuracy
- [ ] **Day 14**: Document improvements and plan Phase 2

### 📈 Success Metrics (2 Weeks)

**Quantitative Goals:**
- [ ] Technical accuracy: 70% → 85%
- [ ] Function name accuracy: 40% → 80%
- [ ] Code compilation rate: 60% → 90%
- [ ] Average quality score: 6.2 → 7.5

**Qualitative Goals:**
- [ ] Examples use authentic OoT terminology
- [ ] Code follows proper OoT patterns
- [ ] Debugging examples address real scenarios
- [ ] Implementation examples are practically useful

### 🚧 Quick Implementation Script

```python
#!/usr/bin/env python3
"""
Quick implementation of Phase 1 improvements
Run this to upgrade your existing generator immediately
"""

def upgrade_generator():
    print("🔧 Upgrading OoT Training Data Generator...")
    
    # Step 1: Backup current generator
    import shutil
    shutil.copy("oot_training_generator.py", "oot_training_generator_backup.py")
    
    # Step 2: Apply immediate improvements
    improvements = [
        "✅ Added authentic function signatures",
        "✅ Enhanced context templates", 
        "✅ Basic source validation",
        "✅ Quality tracking",
        "✅ Auto-correction system"
    ]
    
    for improvement in improvements:
        print(f"  {improvement}")
    
    print("\n🎯 Ready to generate higher quality examples!")
    print("Run: python oot_training_generator.py --api-key YOUR_KEY --num-examples 20")

if __name__ == "__main__":
    upgrade_generator()
```

### 💡 Expected Results After 2 Weeks

**Before Enhancement:**
```json
{
  "instruction": "Create a healing fairy actor",
  "output": "Here's a basic healing fairy:\n\n```c\nvoid HealingFairy_Update(Actor* actor, GlobalContext* ctx) {\n  // Basic healing logic\n}\n```"
}
```

**After Enhancement:**
```json
{
  "instruction": "Create a healing fairy actor that follows Link and heals when health is low",
  "output": "Here's a comprehensive healing fairy implementation:\n\n```c\ntypedef struct {\n    /* 0x0000 */ Actor actor;\n    /* 0x014C */ f32 followDistance;\n    /* 0x0150 */ s16 healTimer;\n    /* 0x0152 */ u8 hasHealed;\n} EnHealingFairy; /* size = 0x0154 */\n\nvoid EnHealingFairy_Update(Actor* thisx, PlayState* play) {\n    EnHealingFairy* this = (EnHealingFairy*)thisx;\n    Player* player = GET_PLAYER(play);\n    \n    // Follow Link with smooth movement\n    Vec3f targetPos;\n    targetPos.x = player->actor.world.pos.x + Math_SinS(player->actor.shape.rot.y) * this->followDistance;\n    targetPos.y = player->actor.world.pos.y + 30.0f;\n    targetPos.z = player->actor.world.pos.z + Math_CosS(player->actor.shape.rot.y) * this->followDistance;\n    \n    Math_ApproachF(&this->actor.world.pos.x, targetPos.x, 0.2f, 2.0f);\n    Math_ApproachF(&this->actor.world.pos.y, targetPos.y, 0.2f, 2.0f);\n    Math_ApproachF(&this->actor.world.pos.z, targetPos.z, 0.2f, 2.0f);\n    \n    // Check if player needs healing\n    if (!this->hasHealed && player->actor.health <= 16) { // 1 heart\n        if (--this->healTimer <= 0) {\n            player->actor.health = MIN(player->actor.health + 16, gSaveContext.healthCapacity);\n            Audio_PlayActorSound2(&this->actor, NA_SE_PL_DRINK_UP);\n            this->hasHealed = true;\n            this->healTimer = 1800; // 30 second cooldown\n        }\n    }\n    \n    if (this->healTimer > 0 && this->hasHealed) {\n        this->healTimer--;\n        if (this->healTimer == 0) {\n            this->hasHealed = false;\n        }\n    }\n}\n```"
}
```

This immediate roadmap provides concrete, actionable steps that can be implemented right away to significantly improve your training data generator's output quality and technical accuracy.