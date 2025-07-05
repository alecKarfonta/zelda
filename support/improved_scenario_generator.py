#!/usr/bin/env python3
"""
Improved OoT Scenario Generator

Creates natural, diverse training instructions based on real OoT behaviors
and patterns, avoiding repetitive literal translations.
"""

import random
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class ScenarioTemplate:
    """Template for generating diverse scenarios"""
    base_pattern: str
    variations: List[str]
    complexity_modifiers: Dict[str, List[str]]
    context_variations: List[str]

class ImprovedOoTScenarioGenerator:
    """Generates natural, diverse OoT training scenarios"""
    
    def __init__(self):
        self.enemy_templates = self._create_enemy_templates()
        self.npc_templates = self._create_npc_templates()
        self.item_templates = self._create_item_templates()
        self.object_templates = self._create_object_templates()
        self.background_templates = self._create_background_templates()
        self.effect_templates = self._create_effect_templates()
        self.player_templates = self._create_player_templates()
        self.misc_templates = self._create_misc_templates()
        
    def _create_enemy_templates(self) -> List[ScenarioTemplate]:
        """Create natural enemy scenario templates"""
        return [
            ScenarioTemplate(
                base_pattern="Create a {enemy_type} enemy that {behavior}",
                variations=[
                    "Design a {enemy_type} that can {behavior}",
                    "Implement a {enemy_type} enemy with the ability to {behavior}",
                    "Build a {enemy_type} that {behavior} when the player approaches",
                    "Create a hostile {enemy_type} that {behavior} as its main attack",
                    "Design an enemy {enemy_type} that {behavior} to defend its territory"
                ],
                complexity_modifiers={
                    "basic": ["with simple AI", "using basic collision detection", "with straightforward behavior"],
                    "intermediate": ["with state-based AI", "using multiple attack patterns", "with conditional behaviors"],
                    "advanced": ["with complex AI decision trees", "using advanced pathfinding", "with dynamic behavior adaptation"]
                },
                context_variations=[
                    "for dungeon encounters",
                    "for overworld exploration",
                    "for boss battles",
                    "for stealth sections",
                    "for puzzle rooms"
                ]
            ),
            ScenarioTemplate(
                base_pattern="How would you implement a {enemy_type} that {unique_mechanic}?",
                variations=[
                    "What's the best way to create a {enemy_type} that {unique_mechanic}?",
                    "Explain how to build a {enemy_type} with the ability to {unique_mechanic}",
                    "Walk me through creating a {enemy_type} that can {unique_mechanic}",
                    "I need help implementing a {enemy_type} that {unique_mechanic}"
                ],
                complexity_modifiers={
                    "basic": ["using simple mechanics", "with basic interactions"],
                    "intermediate": ["with multiple interaction types", "using conditional logic"],
                    "advanced": ["with complex state management", "using advanced AI techniques"]
                },
                context_variations=[
                    "in a forest temple setting",
                    "for underwater combat",
                    "in a fire temple environment",
                    "for aerial combat sequences",
                    "in tight corridor spaces"
                ]
            )
        ]
    
    def _create_npc_templates(self) -> List[ScenarioTemplate]:
        """Create natural NPC scenario templates"""
        return [
            ScenarioTemplate(
                base_pattern="Create an NPC {character_type} that {interaction_type}",
                variations=[
                    "Design a {character_type} NPC that can {interaction_type}",
                    "I want to make a {character_type} that {interaction_type} with the player",
                    "How do I create a {character_type} NPC that {interaction_type}?",
                    "Build a {character_type} character that {interaction_type} when approached"
                ],
                complexity_modifiers={
                    "basic": ["with simple dialogue", "using basic interaction patterns"],
                    "intermediate": ["with branching conversations", "using quest mechanics"],
                    "advanced": ["with dynamic dialogue trees", "using complex relationship systems"]
                },
                context_variations=[
                    "in a village setting",
                    "for a trading post",
                    "in a dungeon entrance",
                    "for a mini-game area",
                    "in a story cutscene"
                ]
            ),
            ScenarioTemplate(
                base_pattern="Design a {character_type} that {service_type}",
                variations=[
                    "Create a {character_type} NPC that provides {service_type}",
                    "I need a {character_type} that can {service_type} for the player",
                    "How would you implement a {character_type} that {service_type}?"
                ],
                complexity_modifiers={
                    "basic": ["with simple mechanics", "using basic UI"],
                    "intermediate": ["with inventory management", "using currency systems"],
                    "advanced": ["with dynamic pricing", "using reputation systems"]
                },
                context_variations=[
                    "in a market area",
                    "for a specialized shop",
                    "in a remote location",
                    "for a temporary event"
                ]
            )
        ]
    
    def _create_item_templates(self) -> List[ScenarioTemplate]:
        """Create natural item scenario templates"""
        return [
            ScenarioTemplate(
                base_pattern="Create a {item_type} item that {functionality}",
                variations=[
                    "Design a {item_type} that can {functionality}",
                    "I want to implement a {item_type} that {functionality}",
                    "How do I create a {item_type} with the ability to {functionality}?",
                    "Build a {item_type} item that {functionality} when used"
                ],
                complexity_modifiers={
                    "basic": ["with simple effects", "using basic mechanics"],
                    "intermediate": ["with conditional effects", "using resource management"],
                    "advanced": ["with complex interactions", "using advanced state tracking"]
                },
                context_variations=[
                    "for puzzle solving",
                    "for combat enhancement",
                    "for exploration mechanics",
                    "for story progression",
                    "for optional content"
                ]
            )
        ]
    
    def _create_object_templates(self) -> List[ScenarioTemplate]:
        """Create natural object scenario templates"""
        return [
            ScenarioTemplate(
                base_pattern="Create a {object_type} that {mechanism}",
                variations=[
                    "Design a {object_type} mechanism that {mechanism}",
                    "I need a {object_type} that can {mechanism}",
                    "How would you implement a {object_type} that {mechanism}?",
                    "Build a {object_type} object that {mechanism} when activated"
                ],
                complexity_modifiers={
                    "basic": ["with simple activation", "using basic collision"],
                    "intermediate": ["with multiple states", "using timing mechanisms"],
                    "advanced": ["with complex sequences", "using interconnected systems"]
                },
                context_variations=[
                    "for puzzle rooms",
                    "for dungeon progression",
                    "for secret areas",
                    "for platforming challenges",
                    "for environmental storytelling"
                ]
            )
        ]
    
    def _create_background_templates(self) -> List[ScenarioTemplate]:
        """Create natural background/environmental scenario templates"""
        return [
            ScenarioTemplate(
                base_pattern="Create an environmental system that {effect}",
                variations=[
                    "Design a {environment_type} area that {effect}",
                    "I want to implement an environmental hazard that {effect}",
                    "How do I create a {environment_type} that {effect}?",
                    "Build an environmental system that {effect} over time"
                ],
                complexity_modifiers={
                    "basic": ["with simple effects", "using basic triggers"],
                    "intermediate": ["with dynamic changes", "using multiple triggers"],
                    "advanced": ["with complex interactions", "using weather systems"]
                },
                context_variations=[
                    "in temple environments",
                    "for overworld areas",
                    "in underground sections",
                    "for water-based areas",
                    "in volcanic regions"
                ]
            )
        ]
    
    def _create_effect_templates(self) -> List[ScenarioTemplate]:
        """Create natural effect scenario templates"""
        return [
            ScenarioTemplate(
                base_pattern="Create a {effect_type} effect that {visual_behavior}",
                variations=[
                    "Design a {effect_type} that {visual_behavior}",
                    "I need a {effect_type} effect that can {visual_behavior}",
                    "How would you implement a {effect_type} that {visual_behavior}?",
                    "Build a {effect_type} effect that {visual_behavior} when triggered"
                ],
                complexity_modifiers={
                    "basic": ["with simple animations", "using basic particles"],
                    "intermediate": ["with dynamic behavior", "using particle systems"],
                    "advanced": ["with complex interactions", "using advanced rendering"]
                },
                context_variations=[
                    "for magic spells",
                    "for environmental atmosphere",
                    "for combat feedback",
                    "for story moments",
                    "for interactive elements"
                ]
            )
        ]
    
    def _create_player_templates(self) -> List[ScenarioTemplate]:
        """Create natural player system scenario templates"""
        return [
            ScenarioTemplate(
                base_pattern="Implement a {system_type} system that {functionality}",
                variations=[
                    "Create a {system_type} mechanic that {functionality}",
                    "Design a {system_type} system that can {functionality}",
                    "I want to build a {system_type} that {functionality}",
                    "How do I implement a {system_type} that {functionality}?"
                ],
                complexity_modifiers={
                    "basic": ["with simple controls", "using basic feedback"],
                    "intermediate": ["with multiple modes", "using state management"],
                    "advanced": ["with complex interactions", "using advanced physics"]
                },
                context_variations=[
                    "for combat scenarios",
                    "for exploration mechanics",
                    "for puzzle interactions",
                    "for story sequences",
                    "for mini-games"
                ]
            )
        ]
    
    def _create_misc_templates(self) -> List[ScenarioTemplate]:
        """Create natural miscellaneous scenario templates"""
        return [
            ScenarioTemplate(
                base_pattern="Create a {system_type} that {behavior}",
                variations=[
                    "Design a {system_type} mechanism that {behavior}",
                    "I need to implement a {system_type} that {behavior}",
                    "How would you create a {system_type} that {behavior}?",
                    "Build a {system_type} system that {behavior} dynamically"
                ],
                complexity_modifiers={
                    "basic": ["with simple logic", "using basic interactions"],
                    "intermediate": ["with conditional behavior", "using multiple systems"],
                    "advanced": ["with complex algorithms", "using AI-driven behavior"]
                },
                context_variations=[
                    "for gameplay enhancement",
                    "for technical optimization",
                    "for debugging purposes",
                    "for accessibility features",
                    "for mod support"
                ]
            )
        ]
    
    def generate_enemy_scenarios(self, count: int = 20) -> List[str]:
        """Generate natural enemy scenarios"""
        scenarios = []
        enemy_types = [
            "skeletal warrior", "fire-breathing dragon", "crystal golem", "shadow assassin",
            "ice elemental", "forest guardian", "stone gargoyle", "lightning spirit",
            "poison spider", "armored knight", "flying demon", "water serpent",
            "lava beast", "wind wraith", "earth titan", "void stalker"
        ]
        
        behaviors = [
            "teleports behind the player for surprise attacks",
            "creates defensive barriers when health is low",
            "summons smaller minions to assist in battle",
            "changes attack patterns based on player actions",
            "uses environmental hazards as weapons",
            "becomes more aggressive as the fight progresses",
            "has multiple phases with different abilities",
            "can only be damaged in specific ways",
            "adapts to the player's combat style",
            "uses hit-and-run tactics to avoid damage"
        ]
        
        unique_mechanics = [
            "split into multiple smaller enemies when defeated",
            "absorb elemental attacks to grow stronger",
            "phase through walls to ambush the player",
            "mirror the player's equipped weapon and abilities",
            "control the battlefield lighting and visibility",
            "manipulate gravity in the surrounding area",
            "create illusions to confuse the player",
            "steal and use the player's items temporarily",
            "regenerate health by consuming nearby objects",
            "coordinate attacks with other enemies"
        ]
        
        for i in range(count):
            template = random.choice(self.enemy_templates)
            variation = random.choice(template.variations)
            complexity = random.choice(["basic", "intermediate", "advanced"])
            
            if "{unique_mechanic}" in variation:
                scenario = variation.format(
                    enemy_type=random.choice(enemy_types),
                    unique_mechanic=random.choice(unique_mechanics)
                )
            else:
                scenario = variation.format(
                    enemy_type=random.choice(enemy_types),
                    behavior=random.choice(behaviors)
                )
            
            # Add complexity modifier
            if random.random() < 0.7:  # 70% chance to add complexity
                modifier = random.choice(template.complexity_modifiers[complexity])
                scenario += f" {modifier}"
            
            # Add context variation
            if random.random() < 0.5:  # 50% chance to add context
                context = random.choice(template.context_variations)
                scenario += f" {context}"
            
            scenarios.append(scenario)
        
        return scenarios
    
    def generate_npc_scenarios(self, count: int = 20) -> List[str]:
        """Generate natural NPC scenarios"""
        scenarios = []
        character_types = [
            "merchant", "blacksmith", "scholar", "guard", "farmer", "innkeeper",
            "healer", "sage", "craftsman", "storyteller", "guide", "collector",
            "trainer", "cook", "librarian", "musician"
        ]
        
        interaction_types = [
            "provides hints about nearby secrets",
            "offers to upgrade the player's equipment",
            "shares local legends and lore",
            "gives quests based on player progress",
            "teaches new skills or abilities",
            "trades rare items for specific materials",
            "provides temporary buffs or services",
            "warns about upcoming dangers",
            "offers transportation to other areas",
            "maintains a mini-game or challenge"
        ]
        
        service_types = [
            "item repair and enhancement services",
            "magical enchantments for equipment",
            "information about dungeon layouts",
            "temporary companion assistance",
            "skill training and tutorials",
            "rare item trading and exchange",
            "quest coordination and tracking",
            "fast travel between locations",
            "inventory management and storage",
            "character customization options"
        ]
        
        for i in range(count):
            template = random.choice(self.npc_templates)
            variation = random.choice(template.variations)
            complexity = random.choice(["basic", "intermediate", "advanced"])
            
            if "{service_type}" in variation:
                scenario = variation.format(
                    character_type=random.choice(character_types),
                    service_type=random.choice(service_types)
                )
            else:
                scenario = variation.format(
                    character_type=random.choice(character_types),
                    interaction_type=random.choice(interaction_types)
                )
            
            # Add complexity modifier
            if random.random() < 0.6:
                modifier = random.choice(template.complexity_modifiers[complexity])
                scenario += f" {modifier}"
            
            # Add context variation
            if random.random() < 0.4:
                context = random.choice(template.context_variations)
                scenario += f" {context}"
            
            scenarios.append(scenario)
        
        return scenarios
    
    def generate_item_scenarios(self, count: int = 15) -> List[str]:
        """Generate natural item scenarios"""
        scenarios = []
        item_types = [
            "magical sword", "enchanted bow", "crystal shield", "power gauntlet",
            "stealth cloak", "healing potion", "puzzle key", "transformation mask",
            "elemental stone", "ancient relic", "utility tool", "consumable scroll"
        ]
        
        functionalities = [
            "reveals hidden passages and secrets",
            "allows temporary flight or levitation",
            "creates protective barriers against attacks",
            "transforms the player's appearance or abilities",
            "provides enhanced vision in dark areas",
            "manipulates time flow in small areas",
            "controls elemental forces like fire or ice",
            "grants telepathic communication with NPCs",
            "opens dimensional portals for fast travel",
            "amplifies the player's magical abilities"
        ]
        
        for i in range(count):
            template = random.choice(self.item_templates)
            variation = random.choice(template.variations)
            complexity = random.choice(["basic", "intermediate", "advanced"])
            
            scenario = variation.format(
                item_type=random.choice(item_types),
                functionality=random.choice(functionalities)
            )
            
            # Add complexity modifier
            if random.random() < 0.6:
                modifier = random.choice(template.complexity_modifiers[complexity])
                scenario += f" {modifier}"
            
            # Add context variation
            if random.random() < 0.5:
                context = random.choice(template.context_variations)
                scenario += f" {context}"
            
            scenarios.append(scenario)
        
        return scenarios
    
    def generate_object_scenarios(self, count: int = 15) -> List[str]:
        """Generate natural object scenarios"""
        scenarios = []
        object_types = [
            "pressure switch", "rotating platform", "sliding door", "magical portal",
            "crystal mechanism", "ancient statue", "mechanical lift", "energy conduit",
            "puzzle pedestal", "temporal gate", "elemental altar", "gravity well"
        ]
        
        mechanisms = [
            "activates when multiple conditions are met",
            "moves in complex patterns to create platforms",
            "opens passages based on player inventory",
            "responds to specific musical sequences",
            "changes the room's layout dynamically",
            "creates temporary bridges across gaps",
            "manipulates light and shadow patterns",
            "generates force fields and barriers",
            "controls water levels and flow",
            "synchronizes with other mechanisms"
        ]
        
        for i in range(count):
            template = random.choice(self.object_templates)
            variation = random.choice(template.variations)
            complexity = random.choice(["basic", "intermediate", "advanced"])
            
            scenario = variation.format(
                object_type=random.choice(object_types),
                mechanism=random.choice(mechanisms)
            )
            
            # Add complexity modifier
            if random.random() < 0.7:
                modifier = random.choice(template.complexity_modifiers[complexity])
                scenario += f" {modifier}"
            
            # Add context variation
            if random.random() < 0.6:
                context = random.choice(template.context_variations)
                scenario += f" {context}"
            
            scenarios.append(scenario)
        
        return scenarios
    
    def generate_all_scenarios(self) -> Dict[str, List[str]]:
        """Generate all scenario types"""
        return {
            "enemy": self.generate_enemy_scenarios(20),
            "npc": self.generate_npc_scenarios(20),
            "item": self.generate_item_scenarios(15),
            "object": self.generate_object_scenarios(15),
            "background": self.generate_background_scenarios(10),
            "effect": self.generate_effect_scenarios(10),
            "player": self.generate_player_scenarios(10),
            "misc": self.generate_misc_scenarios(10)
        }
    
    def generate_background_scenarios(self, count: int = 10) -> List[str]:
        """Generate natural background/environmental scenarios"""
        scenarios = []
        effects = [
            "changes lighting based on time of day",
            "creates dynamic weather patterns",
            "responds to player actions with environmental changes",
            "generates ambient sounds and atmosphere",
            "controls temperature and environmental hazards"
        ]
        
        for i in range(count):
            template = random.choice(self.background_templates)
            variation = random.choice(template.variations)
            scenario = variation.format(
                effect=random.choice(effects),
                environment_type=random.choice(["temple", "forest", "cave", "mountain", "lake"])
            )
            scenarios.append(scenario)
        
        return scenarios
    
    def generate_effect_scenarios(self, count: int = 10) -> List[str]:
        """Generate natural effect scenarios"""
        scenarios = []
        effect_types = ["particle", "lighting", "magical", "elemental", "atmospheric"]
        visual_behaviors = [
            "creates swirling energy patterns",
            "generates cascading light effects",
            "produces dynamic color transitions",
            "creates realistic fire and smoke",
            "generates magical aura effects"
        ]
        
        for i in range(count):
            template = random.choice(self.effect_templates)
            variation = random.choice(template.variations)
            scenario = variation.format(
                effect_type=random.choice(effect_types),
                visual_behavior=random.choice(visual_behaviors)
            )
            scenarios.append(scenario)
        
        return scenarios
    
    def generate_player_scenarios(self, count: int = 10) -> List[str]:
        """Generate natural player system scenarios"""
        scenarios = []
        system_types = ["combat", "movement", "interaction", "inventory", "progression"]
        functionalities = [
            "adapts to different weapon types",
            "provides responsive movement controls",
            "handles complex object interactions",
            "manages item collection and usage",
            "tracks player progress and achievements"
        ]
        
        for i in range(count):
            template = random.choice(self.player_templates)
            variation = random.choice(template.variations)
            scenario = variation.format(
                system_type=random.choice(system_types),
                functionality=random.choice(functionalities)
            )
            scenarios.append(scenario)
        
        return scenarios
    
    def generate_misc_scenarios(self, count: int = 10) -> List[str]:
        """Generate natural miscellaneous scenarios"""
        scenarios = []
        system_types = ["save", "audio", "camera", "UI", "networking"]
        behaviors = [
            "automatically saves progress at checkpoints",
            "dynamically adjusts audio based on environment",
            "smoothly follows player movement",
            "provides intuitive menu navigation",
            "handles multiplayer synchronization"
        ]
        
        for i in range(count):
            template = random.choice(self.misc_templates)
            variation = random.choice(template.variations)
            scenario = variation.format(
                system_type=random.choice(system_types),
                behavior=random.choice(behaviors)
            )
            scenarios.append(scenario)
        
        return scenarios

def main():
    """Generate improved scenarios"""
    generator = ImprovedOoTScenarioGenerator()
    all_scenarios = generator.generate_all_scenarios()
    
    print("🎯 Improved OoT Training Scenarios")
    print("=" * 50)
    
    for category, scenarios in all_scenarios.items():
        print(f"\n{category.upper()} SCENARIOS ({len(scenarios)}):")
        print("-" * 30)
        for i, scenario in enumerate(scenarios[:5], 1):  # Show first 5
            print(f"{i}. {scenario}")
        if len(scenarios) > 5:
            print(f"   ... and {len(scenarios) - 5} more")
    
    # Save to file
    import json
    with open("improved_scenarios.json", "w") as f:
        json.dump(all_scenarios, f, indent=2)
    
    print(f"\n💾 Saved {sum(len(s) for s in all_scenarios.values())} scenarios to improved_scenarios.json")

if __name__ == "__main__":
    main() 