# Enhanced OoT Training Generator - Diversity Improvements



Ensure that in these scenarios the request to the llm to generate the example contains enough context from the source code to meanignfully implement the requested feature

Lets also create a mapping so things like 


## Problem Analysis

The original training data generator was producing repetitive content with limited variety:

### Original Issues
- **Only 4 example types**: CODE_EXPLANATION, FEATURE_IMPLEMENTATION, DEBUGGING_HELP, ACTOR_CREATION
- **Repetitive patterns**: Mostly heart piece spawners and basic collision actors
- **Limited actor categories**: Focused on collectibles and simple interactions
- **Low temperature (0.3)**: Conservative responses leading to repetition
- **No diversity injection**: No mechanism to force variety
- **No category tracking**: No way to ensure balanced coverage

### Repetitive Examples from Original Data
```json
{"instruction": "Create an actor that spawns a heart piece when hit by the player's sword..."}
{"instruction": "Create an actor that spawns a heart piece when hit and plays a chime sound..."}
{"instruction": "Create an actor that spawns a heart piece when hit by the player's sword..."}
```

## Solution: Comprehensive Diversity Enhancement

### 1. Expanded Example Types (4 → 18)

**New Example Types Added:**
- `ANIMATION_SYSTEM` - Skeletal animation, blend trees, procedural animation
- `COLLISION_SYSTEM` - Dynamic collision, collision response, optimization
- `INTERACTION_SYSTEM` - Dialogue systems, inventory, trading, crafting
- `EFFECT_SYSTEM` - Particle effects, screen effects, environmental effects
- `SOUND_SYSTEM` - Dynamic music, 3D audio, voice acting, ambient sound
- `AI_BEHAVIOR` - Pathfinding, state machines, flocking, decision trees
- `ENVIRONMENTAL` - Weather systems, day/night cycles, lighting, water
- `COMBAT_SYSTEM` - Combo systems, blocking, dodging, magic systems
- `PUZZLE_SYSTEM` - Pressure plates, sliding blocks, logic puzzles
- `UI_SYSTEM` - User interface systems and components
- `MEMORY_MANAGEMENT` - Memory allocation, optimization, cleanup
- `OPTIMIZATION` - Performance optimization techniques
- `DEBUGGING_TOOLS` - Development and debugging utilities
- `CUSTOM_MECHANICS` - Time manipulation, possession, cloning, etc.

### 2. Actor Category System (4 → 14 Categories)

**New Actor Categories:**
- `ENEMY` - Bosses, patrols, stealth enemies, flying enemies
- `NPC` - Shopkeepers, quest givers, wandering NPCs, companions
- `ITEM` - Weapons, armor, tools, consumables, magic items
- `MECHANICAL` - Platforms, doors, bridges, elevators, traps
- `ENVIRONMENTAL` - Weather, lighting, water, fire, wind systems
- `EFFECT` - Particle effects, explosions, smoke, sparkles
- `PUZZLE` - Pressure plates, sliding blocks, color matching
- `COMBAT` - Combat systems, combos, blocking, magic
- `TRANSPORT` - Moving platforms, vehicles, teleporters
- `UTILITY` - Utility actors and helper systems
- `DEBUG` - Debugging and development tools
- `CUSTOM` - Custom mechanics and unique systems

### 3. Scenario Template System (100+ Templates)

**Comprehensive Scenario Templates:**

#### Enemy Scenarios (10 templates)
- Patrolling enemies with path following
- Flying enemies with projectile attacks
- Stealth enemies with ambush mechanics
- Boss enemies with multiple phases
- Ranged enemies with distance attacks
- Group coordination systems
- Transformative enemies
- Environment-using enemies
- Minion-spawning enemies
- Time-based behavior enemies

#### NPC Scenarios (10 templates)
- Shopkeepers with dialogue systems
- Quest-giving NPCs with branching
- Wandering NPCs with schedules
- Reactive NPCs with state changes
- Teaching NPCs with ability grants
- Hint-giving NPCs with progress tracking
- Routine-based NPCs with schedules
- Companion NPCs with recruitment
- Reputation-based NPCs
- Mini-game providing NPCs

#### Item Scenarios (10 templates)
- Magic items with temporary abilities
- Key items with unlock mechanics
- Consumable items with restoration
- Weapons with special properties
- Armor with protection bonuses
- Tools with environment interaction
- Collectible items with completion tracking
- Cursed items with trade-offs
- Rare items with spawn conditions
- Upgradeable items with progression

#### Environmental Scenarios (10 templates)
- Weather systems affecting gameplay
- Day/night cycles changing behavior
- Seasonal systems altering activities
- Dynamic lighting responding to time
- Water systems with currents and swimming
- Fire systems with spreading mechanics
- Wind systems affecting movement
- Gravity systems for unique areas
- Temperature systems affecting health
- Pollution systems affecting visibility

#### Puzzle Scenarios (10 templates)
- Pressure plate puzzles
- Sliding block puzzles
- Color-matching puzzles
- Timing-based puzzles
- Logic puzzles with item combinations
- Sequence puzzles requiring order
- Weight-based puzzles
- Light-based puzzles with mirrors
- Sound-based puzzles with audio cues
- Multi-step puzzles spanning rooms

### 4. Diversity Injection System

**Key Features:**
- **Scenario Selection**: Weighted random selection with diversity bias
- **Category Tracking**: Monitors usage of different actor categories
- **Complexity Modifiers**: Adds variety to instruction complexity
- **Diversity Bonus**: Boosts scores for underrepresented categories
- **Usage Tracking**: Prevents repetition of used scenarios

**Diversity Bias Algorithm:**
```python
def _select_with_diversity_bias(self, scenarios, example_type):
    # Score scenarios based on category diversity
    for scenario in scenarios:
        score = 1.0
        for category, keywords in category_keywords.items():
            if any(keyword in scenario.lower() for keyword in keywords):
                # Boost score for less used categories
                usage_ratio = category_count / total_count
                score += (1.0 - usage_ratio) * 2.0
                break
    return weighted_random_selection(scenarios, scores)
```

### 5. Enhanced Generation Process

**Improved Prompts:**
- Higher temperature (0.3 → 0.7) for more variety
- Diversity-focused instructions
- Authentic pattern integration
- Complexity modifiers
- Variety requirements

**Enhanced Acceptance Criteria:**
- Base quality and authenticity requirements
- Diversity bonus scoring
- Category balance tracking
- Unique scenario tracking
- Comprehensive analytics

### 6. Weighted Distribution System

**Example Type Distribution:**
- ACTOR_CREATION: 25% (core functionality)
- Animation/Effect/Interaction/AI: 8% each (system focus)
- Sound/Environmental/Combat/Puzzle: 6% each (gameplay)
- Custom Mechanics: 5% (unique features)
- Code/Feature/Debug: 2-3% each (support)

**Complexity Distribution:**
- Basic: 20% (simple implementations)
- Intermediate: 50% (standard features)
- Advanced: 30% (complex systems)

## Results and Improvements

### Quantitative Improvements
- **4.5x more example types** (4 → 18)
- **3.5x more actor categories** (4 → 14)
- **25x more scenario templates** (4 → 100+)
- **Higher temperature** (0.3 → 0.7) for variety
- **Diversity injection** with bias towards underrepresented categories

### Qualitative Improvements
- **Reduced repetition** through diversity injection
- **Balanced coverage** across actor categories
- **Authentic patterns** with real OoT function usage
- **Complex scenarios** with multiple interaction types
- **Varied complexity** from basic to advanced implementations

### Expected Training Data Quality
- **More diverse actor types**: Enemies, NPCs, items, mechanical, environmental
- **Varied interaction patterns**: Collision, dialogue, proximity, timing
- **Different visual effects**: Particles, explosions, lighting, animations
- **Complex AI behaviors**: State machines, pathfinding, flocking
- **Environmental systems**: Weather, day/night, lighting, water
- **Puzzle mechanics**: Logic, timing, sequence, weight-based
- **Combat systems**: Combos, blocking, dodging, magic
- **Custom mechanics**: Time manipulation, possession, cloning

## Usage

### Basic Usage
```bash
python3 enhanced_authentic_generator.py --num-examples 50 --output diverse_oot_training.jsonl
```

### Advanced Usage
```bash
python3 enhanced_authentic_generator.py \
  --num-examples 100 \
  --output diverse_oot_training_100.jsonl \
  --oot-path ./oot \
  --no-dynamic  # Disable dynamic source analysis if needed
```

### Output Files
- `diverse_oot_training.jsonl` - Training data
- `diverse_oot_training_diversity_analysis.json` - Detailed analytics

## Analytics and Monitoring

The enhanced generator provides comprehensive analytics:

### Diversity Metrics
- Actor category distribution
- Example type coverage
- Unique scenario count
- Complexity distribution
- Generation statistics

### Quality Metrics
- Authenticity scores
- Quality scores
- Validation notes
- Acceptance rates
- Error tracking

### Example Analytics Output
```json
{
  "diversity_metrics": {
    "actor_categories": {
      "enemy": 15,
      "npc": 12,
      "item": 8,
      "mechanical": 10,
      "environmental": 5
    },
    "example_types": {
      "actor_creation": 25,
      "animation_system": 8,
      "collision_system": 8
    },
    "unique_scenarios": 95,
    "category_coverage": 14,
    "type_coverage": 18
  }
}
```

## Conclusion

The enhanced OoT training generator addresses the repetitive content issue through:

1. **Comprehensive diversity injection** with 100+ scenario templates
2. **Expanded example types** covering 18 different systems
3. **Actor category system** with 14 diverse categories
4. **Weighted distribution** ensuring balanced coverage
5. **Diversity bias algorithms** preventing repetition
6. **Enhanced prompts** with higher temperature and variety requirements
7. **Comprehensive analytics** for monitoring and improvement

This results in much more robust, diverse, and useful training data for OoT romhacking development. 