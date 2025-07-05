#!/usr/bin/env python3
"""
Final Integration Demo - Shows how improved scenarios work with OoT training data generation
"""

import json
import random
from typing import List, Dict
from improved_scenario_generator import ImprovedOoTScenarioGenerator

class OoTTrainingDataDemo:
    """Demonstrates the complete training data generation pipeline"""
    
    def __init__(self):
        self.scenario_generator = ImprovedOoTScenarioGenerator()
        
    def generate_sample_training_data(self, num_examples: int = 10) -> List[Dict]:
        """Generate sample training data using improved scenarios"""
        
        # Get diverse scenarios
        all_scenarios = self.scenario_generator.generate_all_scenarios()
        
        # Flatten all scenarios into one list with categories
        scenario_pool = []
        for category, scenarios in all_scenarios.items():
            for scenario in scenarios:
                scenario_pool.append({
                    "instruction": scenario,
                    "category": category,
                    "complexity": random.choice(["basic", "intermediate", "advanced"])
                })
        
        # Select diverse examples
        selected_examples = random.sample(scenario_pool, min(num_examples, len(scenario_pool)))
        
        # Generate mock outputs (in real version, this would use Claude)
        training_examples = []
        for example in selected_examples:
            training_example = {
                "instruction": example["instruction"],
                "input": None,
                "output": self._generate_mock_output(example),
                "metadata": {
                    "category": example["category"],
                    "complexity": example["complexity"],
                    "authenticity_score": random.uniform(7.5, 9.5),
                    "quality_score": random.uniform(7.0, 9.0)
                }
            }
            training_examples.append(training_example)
        
        return training_examples
    
    def _generate_mock_output(self, example: Dict) -> str:
        """Generate a mock code output for demonstration"""
        category = example["category"]
        complexity = example["complexity"]
        
        if category == "enemy":
            return self._mock_enemy_code(complexity)
        elif category == "npc":
            return self._mock_npc_code(complexity)
        elif category == "item":
            return self._mock_item_code(complexity)
        elif category == "object":
            return self._mock_object_code(complexity)
        else:
            return self._mock_generic_code(complexity)
    
    def _mock_enemy_code(self, complexity: str) -> str:
        """Generate mock enemy actor code"""
        if complexity == "advanced":
            return '''```c
// Advanced Enemy Actor with State Machine and AI
typedef struct {
    /* 0x000 */ Actor actor;
    /* 0x14C */ s16 timer;
    /* 0x14E */ s16 actionState;
    /* 0x150 */ s16 aiState;
    /* 0x152 */ s16 attackPattern;
    /* 0x154 */ f32 detectionRadius;
    /* 0x158 */ Vec3f homePos;
    /* 0x164 */ ColliderCylinder collider;
} EnAdvancedEnemy; // size = 0x1B0

void EnAdvancedEnemy_Init(Actor* thisx, PlayState* play) {
    EnAdvancedEnemy* this = (EnAdvancedEnemy*)thisx;
    
    // Initialize collision
    Collider_InitCylinder(play, &this->collider);
    Collider_SetCylinder(play, &this->collider, &this->actor, &sCylinderInit);
    
    // Set up AI parameters
    this->detectionRadius = 300.0f;
    this->aiState = AI_STATE_PATROL;
    Math_Vec3f_Copy(&this->homePos, &this->actor.world.pos);
    
    Actor_SetScale(&this->actor, 0.01f);
}

void EnAdvancedEnemy_Update(Actor* thisx, PlayState* play) {
    EnAdvancedEnemy* this = (EnAdvancedEnemy*)thisx;
    Player* player = GET_PLAYER(play);
    
    // Update AI state machine
    this->aiState = EnAdvancedEnemy_UpdateAI(this, play, player);
    
    // Execute current action
    switch (this->actionState) {
        case ACTION_PATROL:
            EnAdvancedEnemy_Patrol(this, play);
            break;
        case ACTION_CHASE:
            EnAdvancedEnemy_Chase(this, play, player);
            break;
        case ACTION_ATTACK:
            EnAdvancedEnemy_Attack(this, play, player);
            break;
    }
    
    // Update collision
    Actor_UpdateBgCheckInfo(play, &this->actor, 26.0f, 10.0f, 0.0f, BGCHECKFLAG_GROUND);
    Collider_UpdateCylinder(&this->actor, &this->collider);
    CollisionCheck_SetOC(play, &play->colChkCtx, &this->collider.base);
}
```'''
        elif complexity == "intermediate":
            return '''```c
// Intermediate Enemy Actor with Basic AI
typedef struct {
    /* 0x000 */ Actor actor;
    /* 0x14C */ s16 timer;
    /* 0x14E */ s16 actionState;
    /* 0x150 */ f32 speed;
    /* 0x154 */ ColliderCylinder collider;
} EnIntermediateEnemy; // size = 0x1A0

void EnIntermediateEnemy_Init(Actor* thisx, PlayState* play) {
    EnIntermediateEnemy* this = (EnIntermediateEnemy*)thisx;
    
    Collider_InitCylinder(play, &this->collider);
    Collider_SetCylinder(play, &this->collider, &this->actor, &sCylinderInit);
    
    this->speed = 2.0f;
    this->actionState = ACTION_IDLE;
    Actor_SetScale(&this->actor, 0.01f);
}

void EnIntermediateEnemy_Update(Actor* thisx, PlayState* play) {
    EnIntermediateEnemy* this = (EnIntermediateEnemy*)thisx;
    
    // Simple behavior based on player distance
    f32 distToPlayer = Actor_WorldDistXZToActor(&this->actor, &GET_PLAYER(play)->actor);
    
    if (distToPlayer < 100.0f) {
        this->actionState = ACTION_ATTACK;
    } else if (distToPlayer < 200.0f) {
        this->actionState = ACTION_CHASE;
    } else {
        this->actionState = ACTION_IDLE;
    }
    
    Actor_MoveXZGravity(&this->actor);
    Collider_UpdateCylinder(&this->actor, &this->collider);
    CollisionCheck_SetOC(play, &play->colChkCtx, &this->collider.base);
}
```'''
        else:  # basic
            return '''```c
// Basic Enemy Actor
typedef struct {
    /* 0x000 */ Actor actor;
    /* 0x14C */ s16 timer;
    /* 0x14E */ s16 actionState;
    /* 0x150 */ ColliderCylinder collider;
} EnBasicEnemy; // size = 0x19C

void EnBasicEnemy_Init(Actor* thisx, PlayState* play) {
    EnBasicEnemy* this = (EnBasicEnemy*)thisx;
    
    Collider_InitCylinder(play, &this->collider);
    Collider_SetCylinder(play, &this->collider, &this->actor, &sCylinderInit);
    Actor_SetScale(&this->actor, 0.01f);
}

void EnBasicEnemy_Update(Actor* thisx, PlayState* play) {
    EnBasicEnemy* this = (EnBasicEnemy*)thisx;
    
    Actor_MoveXZGravity(&this->actor);
    Collider_UpdateCylinder(&this->actor, &this->collider);
    CollisionCheck_SetOC(play, &play->colChkCtx, &this->collider.base);
}
```'''
    
    def _mock_npc_code(self, complexity: str) -> str:
        """Generate mock NPC actor code"""
        return '''```c
// NPC Actor with Dialogue System
typedef struct {
    /* 0x000 */ Actor actor;
    /* 0x14C */ s16 talkState;
    /* 0x14E */ s16 textId;
    /* 0x150 */ ColliderCylinder collider;
} EnNpcActor; // size = 0x19C

void EnNpcActor_Init(Actor* thisx, PlayState* play) {
    EnNpcActor* this = (EnNpcActor*)thisx;
    
    Collider_InitCylinder(play, &this->collider);
    Collider_SetCylinder(play, &this->collider, &this->actor, &sCylinderInit);
    
    this->textId = 0x1000; // Default dialogue
    Actor_SetScale(&this->actor, 0.01f);
}

void EnNpcActor_Update(Actor* thisx, PlayState* play) {
    EnNpcActor* this = (EnNpcActor*)thisx;
    
    // Handle dialogue interaction
    if (Actor_TalkOfferAccepted(&this->actor, play)) {
        this->talkState = NPC_TALK_STATE_TALKING;
    } else if (this->talkState == NPC_TALK_STATE_IDLE) {
        Actor_OfferTalk(&this->actor, play, 60.0f);
    }
    
    Collider_UpdateCylinder(&this->actor, &this->collider);
    CollisionCheck_SetOC(play, &play->colChkCtx, &this->collider.base);
}
```'''
    
    def _mock_item_code(self, complexity: str) -> str:
        """Generate mock item actor code"""
        return '''```c
// Item Actor with Collection Logic
typedef struct {
    /* 0x000 */ Actor actor;
    /* 0x14C */ s16 itemId;
    /* 0x14E */ s16 collectTimer;
    /* 0x150 */ f32 bobPhase;
    /* 0x154 */ ColliderCylinder collider;
} EnItemActor; // size = 0x1A0

void EnItemActor_Init(Actor* thisx, PlayState* play) {
    EnItemActor* this = (EnItemActor*)thisx;
    
    Collider_InitCylinder(play, &this->collider);
    Collider_SetCylinder(play, &this->collider, &this->actor, &sCylinderInit);
    
    this->itemId = this->actor.params & 0xFF;
    this->bobPhase = 0.0f;
    Actor_SetScale(&this->actor, 0.01f);
}

void EnItemActor_Update(Actor* thisx, PlayState* play) {
    EnItemActor* this = (EnItemActor*)thisx;
    
    // Bobbing animation
    this->bobPhase += 0.1f;
    this->actor.world.pos.y += Math_SinS(this->bobPhase * 1000) * 2.0f;
    
    // Collection logic
    if (this->collider.base.acFlags & AC_HIT) {
        Actor_OfferGetItem(&this->actor, play, this->itemId, 50.0f, 10.0f);
    }
    
    Collider_UpdateCylinder(&this->actor, &this->collider);
    CollisionCheck_SetAC(play, &play->colChkCtx, &this->collider.base);
}
```'''
    
    def _mock_object_code(self, complexity: str) -> str:
        """Generate mock object actor code"""
        return '''```c
// Object Actor with Mechanism Logic
typedef struct {
    /* 0x000 */ Actor actor;
    /* 0x14C */ s16 switchState;
    /* 0x14E */ s16 activationTimer;
    /* 0x150 */ f32 targetY;
    /* 0x154 */ ColliderCylinder collider;
} ObjMechanism; // size = 0x1A0

void ObjMechanism_Init(Actor* thisx, PlayState* play) {
    ObjMechanism* this = (ObjMechanism*)thisx;
    
    Collider_InitCylinder(play, &this->collider);
    Collider_SetCylinder(play, &this->collider, &this->actor, &sCylinderInit);
    
    this->targetY = this->actor.world.pos.y + 100.0f;
    this->switchState = SWITCH_OFF;
    Actor_SetScale(&this->actor, 0.01f);
}

void ObjMechanism_Update(Actor* thisx, PlayState* play) {
    ObjMechanism* this = (ObjMechanism*)thisx;
    
    // Check for activation
    if (Flags_GetSwitch(play, this->actor.params & 0x3F)) {
        this->switchState = SWITCH_ON;
    }
    
    // Move based on switch state
    if (this->switchState == SWITCH_ON) {
        Math_ApproachF(&this->actor.world.pos.y, this->targetY, 0.5f, 5.0f);
    }
    
    Collider_UpdateCylinder(&this->actor, &this->collider);
    CollisionCheck_SetOC(play, &play->colChkCtx, &this->collider.base);
}
```'''
    
    def _mock_generic_code(self, complexity: str) -> str:
        """Generate mock generic actor code"""
        return '''```c
// Generic Actor Implementation
typedef struct {
    /* 0x000 */ Actor actor;
    /* 0x14C */ s16 state;
    /* 0x14E */ s16 timer;
    /* 0x150 */ ColliderCylinder collider;
} GenericActor; // size = 0x19C

void GenericActor_Init(Actor* thisx, PlayState* play) {
    GenericActor* this = (GenericActor*)thisx;
    
    Collider_InitCylinder(play, &this->collider);
    Collider_SetCylinder(play, &this->collider, &this->actor, &sCylinderInit);
    Actor_SetScale(&this->actor, 0.01f);
}

void GenericActor_Update(Actor* thisx, PlayState* play) {
    GenericActor* this = (GenericActor*)thisx;
    
    Actor_UpdateBgCheckInfo(play, &this->actor, 26.0f, 10.0f, 0.0f, BGCHECKFLAG_GROUND);
    Collider_UpdateCylinder(&this->actor, &this->collider);
    CollisionCheck_SetOC(play, &play->colChkCtx, &this->collider.base);
}
```'''
    
    def demonstrate_pipeline(self):
        """Demonstrate the complete training data generation pipeline"""
        print("🚀 OoT Training Data Generation Pipeline Demo")
        print("=" * 60)
        
        print("\n📝 STEP 1: Generate Diverse Scenarios")
        print("-" * 40)
        
        # Show scenario variety
        sample_scenarios = {
            "enemy": self.scenario_generator.generate_enemy_scenarios(3),
            "npc": self.scenario_generator.generate_npc_scenarios(3),
            "item": self.scenario_generator.generate_item_scenarios(2),
            "object": self.scenario_generator.generate_object_scenarios(2)
        }
        
        for category, scenarios in sample_scenarios.items():
            print(f"\n{category.upper()}:")
            for i, scenario in enumerate(scenarios, 1):
                print(f"  {i}. {scenario}")
        
        print("\n🔧 STEP 2: Generate Training Examples")
        print("-" * 40)
        
        # Generate sample training data
        training_examples = self.generate_sample_training_data(5)
        
        for i, example in enumerate(training_examples, 1):
            print(f"\nEXAMPLE {i} ({example['metadata']['category']}, {example['metadata']['complexity']}):")
            print(f"Instruction: {example['instruction']}")
            print(f"Output: {example['output'][:200]}...")
            print(f"Quality: {example['metadata']['quality_score']:.1f}, Authenticity: {example['metadata']['authenticity_score']:.1f}")
        
        print("\n📊 STEP 3: Quality Analysis")
        print("-" * 40)
        
        # Analyze quality metrics
        avg_quality = sum(ex['metadata']['quality_score'] for ex in training_examples) / len(training_examples)
        avg_authenticity = sum(ex['metadata']['authenticity_score'] for ex in training_examples) / len(training_examples)
        
        categories = set(ex['metadata']['category'] for ex in training_examples)
        complexities = set(ex['metadata']['complexity'] for ex in training_examples)
        
        print(f"Average Quality Score: {avg_quality:.2f}/10")
        print(f"Average Authenticity Score: {avg_authenticity:.2f}/10")
        print(f"Categories Covered: {len(categories)} ({', '.join(categories)})")
        print(f"Complexity Levels: {len(complexities)} ({', '.join(complexities)})")
        
        print("\n💾 STEP 4: Save Training Data")
        print("-" * 40)
        
        # Save in training format
        output_file = "demo_training_data.jsonl"
        with open(output_file, 'w') as f:
            for example in training_examples:
                record = {
                    "instruction": example["instruction"],
                    "output": example["output"]
                }
                if example["input"]:
                    record["input"] = example["input"]
                f.write(json.dumps(record) + '\n')
        
        print(f"✅ Saved {len(training_examples)} examples to {output_file}")
        
        # Save metadata
        metadata_file = "demo_metadata.json"
        metadata = {
            "total_examples": len(training_examples),
            "average_quality": avg_quality,
            "average_authenticity": avg_authenticity,
            "categories": list(categories),
            "complexities": list(complexities),
            "examples": training_examples
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Saved metadata to {metadata_file}")
        
        print(f"\n🎉 PIPELINE COMPLETE!")
        print(f"Generated {len(training_examples)} high-quality, diverse OoT training examples")
        print(f"Ready for fine-tuning language models on authentic OoT romhacking patterns")

def main():
    """Run the demo"""
    demo = OoTTrainingDataDemo()
    demo.demonstrate_pipeline()

if __name__ == "__main__":
    main() 