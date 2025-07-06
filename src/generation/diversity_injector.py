#!/usr/bin/env python3
"""
Diversity Injector for OoT Training Data Generation
"""

import random
from typing import List, Dict

from src.models.enums import ExampleType, ActorCategory
from src.core.logger import logger


class DiversityInjector:
    """Injects diversity into training data generation"""
    
    def __init__(self):
        self.scenario_templates = RealOoTScenarioTemplate()
        self.used_scenarios = set()
        self.actor_category_counts = {cat: 0 for cat in ActorCategory}
        
    def get_diverse_instruction(self, example_type: ExampleType, complexity: str) -> str:
        """Generate diverse instructions based on example type"""
        
        # Get base scenarios for the example type
        if example_type == ExampleType.ACTOR_CREATION:
            scenarios = self._get_actor_creation_scenarios()
        elif example_type == ExampleType.ANIMATION_SYSTEM:
            scenarios = self._get_animation_scenarios()
        elif example_type == ExampleType.COLLISION_SYSTEM:
            scenarios = self._get_collision_scenarios()
        elif example_type == ExampleType.INTERACTION_SYSTEM:
            scenarios = self._get_interaction_scenarios()
        elif example_type == ExampleType.EFFECT_SYSTEM:
            scenarios = self.scenario_templates.get_effect_scenarios()
        elif example_type == ExampleType.SOUND_SYSTEM:
            scenarios = self._get_sound_scenarios()
        elif example_type == ExampleType.AI_BEHAVIOR:
            scenarios = self.scenario_templates.get_player_scenarios()  # Use player scenarios for AI behavior
        elif example_type == ExampleType.ENVIRONMENTAL:
            scenarios = self.scenario_templates.get_background_scenarios()
        elif example_type == ExampleType.COMBAT_SYSTEM:
            scenarios = self.scenario_templates.get_player_scenarios()  # Use player scenarios for combat
        elif example_type == ExampleType.PUZZLE_SYSTEM:
            scenarios = self.scenario_templates.get_object_scenarios()  # Use object scenarios for puzzles
        elif example_type == ExampleType.CUSTOM_MECHANICS:
            scenarios = self.scenario_templates.get_misc_scenarios()  # Use misc scenarios for custom mechanics
        else:
            scenarios = self._get_generic_scenarios(example_type)
        
        # Filter out used scenarios to avoid repetition
        available_scenarios = [s for s in scenarios if s not in self.used_scenarios]
        if not available_scenarios:
            # Reset if all scenarios used
            self.used_scenarios.clear()
            available_scenarios = scenarios
        
        # Select scenario with diversity bias
        selected_scenario = self._select_with_diversity_bias(available_scenarios, example_type)
        self.used_scenarios.add(selected_scenario)
        
        # Add complexity modifiers
        complexity_modifiers = self._get_complexity_modifiers(complexity)
        if complexity_modifiers:
            selected_scenario += f" {random.choice(complexity_modifiers)}"
        
        return selected_scenario
    
    def _get_actor_creation_scenarios(self) -> List[str]:
        """Get diverse actor creation scenarios"""
        scenarios = []
        
        # Enemy scenarios
        scenarios.extend(self.scenario_templates.get_enemy_scenarios())
        
        # NPC scenarios  
        scenarios.extend(self.scenario_templates.get_npc_scenarios())
        
        # Item scenarios
        scenarios.extend(self.scenario_templates.get_item_scenarios())
        
        # Object scenarios (mechanical)
        scenarios.extend(self.scenario_templates.get_object_scenarios())
        
        # Background scenarios (environmental)
        scenarios.extend(self.scenario_templates.get_background_scenarios())
        
        return scenarios
    
    def _get_animation_scenarios(self) -> List[str]:
        return [
            "Create a skeletal animation system for character movement",
            "Implement a procedural animation system for natural movement",
            "Create a blend tree system for smooth animation transitions",
            "Make an animation event system that triggers effects during animations",
            "Create a facial animation system for NPC expressions",
            "Implement a physics-based animation system for cloth and hair",
            "Create an animation state machine for complex character behaviors",
            "Make a keyframe animation system for custom animations",
            "Create an animation compression system for memory optimization",
            "Implement an animation blending system for smooth transitions"
        ]
    
    def _get_collision_scenarios(self) -> List[str]:
        return [
            "Create a dynamic collision detection system for moving objects",
            "Implement a collision response system with realistic physics",
            "Create a collision filtering system for different object types",
            "Make a collision optimization system for performance",
            "Create a collision debugging system for development",
            "Implement a collision event system for trigger responses",
            "Create a collision prediction system for AI pathfinding",
            "Make a collision memory system for persistent interactions",
            "Create a collision visualization system for debugging",
            "Implement a collision caching system for repeated checks"
        ]
    
    def _get_interaction_scenarios(self) -> List[str]:
        return [
            "Create a dialogue system with branching conversations",
            "Implement an inventory system with item management",
            "Create a trading system for buying and selling items",
            "Make a crafting system for creating new items",
            "Create a quest system with objectives and rewards",
            "Implement a reputation system that affects NPC interactions",
            "Create a relationship system between NPCs and the player",
            "Make a skill system that improves with use",
            "Create a faction system with different groups and allegiances",
            "Implement a reputation system that affects available options"
        ]
    
    def _get_sound_scenarios(self) -> List[str]:
        return [
            "Create a dynamic music system that adapts to gameplay",
            "Implement a 3D audio system for spatial sound effects",
            "Create a voice acting system for NPC dialogue",
            "Make an ambient sound system for environmental audio",
            "Create a sound effect system for actions and events",
            "Implement a music transition system for smooth audio changes",
            "Create a sound filtering system for different environments",
            "Make a voice modulation system for different character types",
            "Create a sound memory system for persistent audio cues",
            "Implement a sound optimization system for performance"
        ]
    
    def _get_generic_scenarios(self, example_type: ExampleType) -> List[str]:
        """Generic scenarios for other example types"""
        return [
            f"Create a {example_type.value.replace('_', ' ')} system with proper OoT patterns",
            f"Implement {example_type.value.replace('_', ' ')} functionality using authentic code",
            f"Make a {example_type.value.replace('_', ' ')} that follows OoT decompilation standards",
            f"Create an advanced {example_type.value.replace('_', ' ')} with multiple features",
            f"Implement a complex {example_type.value.replace('_', ' ')} system for enhanced gameplay"
        ]
    
    def _select_with_diversity_bias(self, scenarios: List[str], example_type: ExampleType) -> str:
        """Select scenario with bias towards less used categories"""
        
        # Determine actor category from scenario content
        category_keywords = {
            ActorCategory.ENEMY: ["enemy", "boss", "attack", "patrol", "stealth", "flying"],
            ActorCategory.NPC: ["npc", "shopkeeper", "quest", "dialogue", "wandering"],
            ActorCategory.ITEM: ["item", "weapon", "armor", "tool", "consumable", "magic"],
            ActorCategory.OBJECT: ["object", "switch", "lift", "door", "chest", "torch"],
            ActorCategory.BACKGROUND: ["background", "temple", "water", "fire", "forest"],
            ActorCategory.EFFECT: ["effect", "song", "magic", "spell", "ocarina"],
            ActorCategory.PLAYER: ["player", "sword", "fishing", "ocarina", "bottle", "mask", "magic"],
            ActorCategory.MISC: ["fishing", "horse", "owl", "gossip", "treasure"]
        }
        
        # Score scenarios based on category diversity
        scenario_scores = []
        for scenario in scenarios:
            score = 1.0
            for category, keywords in category_keywords.items():
                if any(keyword.lower() in scenario.lower() for keyword in keywords):
                    # Boost score for less used categories
                    usage_ratio = self.actor_category_counts[category] / max(sum(self.actor_category_counts.values()), 1)
                    score += (1.0 - usage_ratio) * 2.0
                    break
            scenario_scores.append((scenario, score))
        
        # Weighted random selection
        total_score = sum(score for _, score in scenario_scores)
        if total_score > 0:
            weights = [score / total_score for _, score in scenario_scores]
            selected = random.choices(scenarios, weights=weights, k=1)[0]
        else:
            selected = random.choice(scenarios)
        
        # Update category counts
        for category, keywords in category_keywords.items():
            if any(keyword.lower() in selected.lower() for keyword in keywords):
                self.actor_category_counts[category] += 1
                break
        
        return selected
    
    def _get_complexity_modifiers(self, complexity: str) -> List[str]:
        """Get complexity modifiers for instructions"""
        if complexity == "advanced":
            return [
                "with multiple states and transitions",
                "using advanced optimization techniques", 
                "with complex interaction patterns",
                "implementing sophisticated AI behaviors",
                "with extensive error handling and edge cases",
                "using advanced memory management",
                "with complex mathematical calculations",
                "implementing multiple subsystems",
                "with extensive debugging capabilities",
                "using advanced rendering techniques"
            ]
        elif complexity == "intermediate":
            return [
                "with proper error handling",
                "using efficient algorithms",
                "with good code organization",
                "implementing standard patterns",
                "with appropriate documentation",
                "using memory-safe practices",
                "with reasonable performance",
                "implementing common features",
                "with basic debugging support",
                "using established conventions"
            ]
        else:  # basic
            return [
                "with basic functionality",
                "using simple patterns",
                "with minimal features",
                "implementing core requirements",
                "with straightforward logic",
                "using standard approaches",
                "with basic error checking",
                "implementing essential features",
                "with simple documentation",
                "using common practices"
            ]


class RealOoTScenarioTemplate:
    """Improved OoT scenario templates with natural, diverse instructions"""
    
    def __init__(self):
        # Import the new scenario generator and validator
        from helpers.improved_scenario_generator import ImprovedOoTScenarioGenerator
        from helpers.validate_and_enhance_scenarios import OoTPatternValidator
        self.scenario_generator = ImprovedOoTScenarioGenerator()
        self.validator = OoTPatternValidator()
        self.use_improved_generator = True
        logger.success("✅ Using improved scenario generator with validation")

    def get_enemy_scenarios(self) -> List[str]:
        if self.use_improved_generator:
            return self.scenario_generator.generate_enemy_scenarios(20)
        else:
            return self._get_fallback_enemy_scenarios()
    
    def _get_fallback_enemy_scenarios(self) -> List[str]:
        return [
            "Create a skeletal warrior that teleports behind the player for surprise attacks",
            "Design a fire-breathing dragon that creates defensive barriers when health is low",
            "Implement a crystal golem enemy with the ability to summon smaller minions to assist in battle",
            "Build a shadow assassin that changes attack patterns based on player actions when the player approaches",
            "Create a hostile ice elemental that uses environmental hazards as weapons as its main attack",
            "Design an enemy forest guardian that becomes more aggressive as the fight progresses",
            "How would you implement a stone gargoyle that can split into multiple smaller enemies when defeated?",
            "What's the best way to create a lightning spirit that absorbs elemental attacks to grow stronger?",
            "Explain how to build a poison spider with the ability to phase through walls to ambush the player",
            "Walk me through creating an armored knight that can mirror the player's equipped weapon and abilities",
            "Create a flying demon that has multiple phases with different abilities with state-based AI",
            "Design a water serpent that can only be damaged in specific ways using multiple attack patterns",
            "Implement a lava beast enemy with the ability to control the battlefield lighting and visibility",
            "Build a wind wraith that manipulates gravity in the surrounding area when the player approaches",
            "Create a hostile earth titan that creates illusions to confuse the player as its main attack",
            "Design an enemy void stalker that steals and uses the player's items temporarily",
            "How would you implement a crystal guardian that regenerates health by consuming nearby objects?",
            "What's the best way to create a shadow demon that coordinates attacks with other enemies?",
            "Explain how to build a flame spirit with the ability to adapt to the player's combat style",
            "Walk me through creating a stone beast that uses hit-and-run tactics to avoid damage"
        ]
    
    def get_npc_scenarios(self) -> List[str]:
        if self.use_improved_generator:
            return self.scenario_generator.generate_npc_scenarios(20)
        else:
            return self._get_fallback_npc_scenarios()
    
    def _get_fallback_npc_scenarios(self) -> List[str]:
        return [
            "Create a merchant NPC that provides hints about nearby secrets",
            "Design a blacksmith that can offer to upgrade the player's equipment",
            "I want to make a scholar that shares local legends and lore with the player",
            "How do I create a guard NPC that gives quests based on player progress?",
            "Build a farmer character that teaches new skills or abilities when approached",
            "Create a healer NPC that trades rare items for specific materials",
            "Design a sage that can provide temporary buffs or services",
            "I need a craftsman that can warns about upcoming dangers",
            "How would you implement a storyteller that offers transportation to other areas?",
            "Build a guide character that maintains a mini-game or challenge when approached",
            "Create a merchant NPC that provides item repair and enhancement services",
            "Design a innkeeper that can magical enchantments for equipment",
            "I want to make a collector that information about dungeon layouts with the player",
            "How do I create a trainer NPC that temporary companion assistance?",
            "Build a cook character that skill training and tutorials when approached",
            "Create a librarian NPC that rare item trading and exchange",
            "Design a musician that can quest coordination and tracking",
            "I need a sage that can fast travel between locations",
            "How would you implement a healer that inventory management and storage?",
            "Build a scholar character that character customization options when approached"
        ]
    
    def get_item_scenarios(self) -> List[str]:
        if self.use_improved_generator:
            return self.scenario_generator.generate_item_scenarios(15)
        else:
            return self._get_fallback_item_scenarios()
    
    def _get_fallback_item_scenarios(self) -> List[str]:
        return [
            "Build a magical sword item that reveals hidden passages and secrets when used",
            "Design a enchanted bow that can allows temporary flight or levitation",
            "I want to implement a crystal shield that creates protective barriers against attacks",
            "How do I create a power gauntlet with the ability to transforms the player's appearance or abilities?",
            "Build a stealth cloak item that provides enhanced vision in dark areas when used",
            "Create a healing potion that manipulates time flow in small areas",
            "Design a puzzle key that can controls elemental forces like fire or ice",
            "I need a transformation mask that grants telepathic communication with NPCs",
            "How would you implement an ancient relic that opens dimensional portals for fast travel?",
            "Build a utility tool item that amplifies the player's magical abilities when used",
            "Create a elemental stone that reveals hidden passages and secrets with simple effects",
            "Design a consumable scroll that can allows temporary flight or levitation using resource management",
            "I want to implement a magical sword that creates protective barriers against attacks for combat enhancement",
            "How do I create a enchanted bow with the ability to transforms the player's appearance or abilities?",
            "Build a crystal shield item that provides enhanced vision in dark areas when used with conditional effects"
        ]
    
    def get_object_scenarios(self) -> List[str]:
        if self.use_improved_generator:
            return self.scenario_generator.generate_object_scenarios(15)
        else:
            return self._get_fallback_object_scenarios()
    
    def _get_fallback_object_scenarios(self) -> List[str]:
        return [
            "Build a pressure switch object that activates when multiple conditions are met when activated",
            "Design a rotating platform mechanism that moves in complex patterns to create platforms",
            "I need a sliding door that can opens passages based on player inventory",
            "How would you implement a magical portal that responds to specific musical sequences?",
            "Build a crystal mechanism object that changes the room's layout dynamically when activated",
            "Create a ancient statue that creates temporary bridges across gaps",
            "Design a mechanical lift mechanism that manipulates light and shadow patterns",
            "I need a energy conduit that can generates force fields and barriers",
            "How would you implement a puzzle pedestal that controls water levels and flow?",
            "Build a temporal gate object that synchronizes with other mechanisms when activated",
            "Create a elemental altar that activates when multiple conditions are met with simple activation",
            "Design a gravity well mechanism that moves in complex patterns to create platforms using timing mechanisms",
            "I need a pressure switch that can opens passages based on player inventory",
            "How would you implement a rotating platform that responds to specific musical sequences?",
            "Build a sliding door object that changes the room's layout dynamically when activated with complex sequences"
        ]
    
    @staticmethod
    def get_background_scenarios() -> List[str]:
        return [
            "Create a Water Temple water level system",
            "Implement a Fire Temple lava flow mechanics",
            "Create a Forest Temple moving platforms",
            "Make a Shadow Temple darkness and light mechanics",
            "Create a Spirit Temple sand flow and time mechanics",
            "Implement a Deku Tree web and platform system",
            "Create a Jabu-Jabu's Belly water and bubble mechanics",
            "Make a Dodongo's Cavern rock and lava system",
            "Create a Inside the Deku Tree web and platform mechanics",
            "Implement a Ganon's Castle tower and barrier system"
        ]
    
    @staticmethod
    def get_effect_scenarios() -> List[str]:
        return [
            "Create a Sun Song effect that changes time of day",
            "Implement a Song of Storms effect that creates rain",
            "Create a Song of Time effect that advances time",
            "Make a Zelda's Lullaby effect that opens doors",
            "Create a Saria's Song effect that calls for help",
            "Implement a Epona's Song effect that calls the horse",
            "Create a Song of Healing effect that cures curses",
            "Make a Requiem of Spirit effect that warps to desert",
            "Create a Nocturne of Shadow effect that warps to shadow temple",
            "Implement a Prelude of Light effect that warps to temple of time"
        ]
    
    @staticmethod
    def get_player_scenarios() -> List[str]:
        return [
            "Create a Hookshot targeting and grappling system",
            "Implement a Boomerang throwing and returning mechanics",
            "Create a Bow and arrow aiming and shooting system",
            "Make a Bomb throwing and explosion mechanics",
            "Create a Magic spell casting and mana system",
            "Implement a Sword combat with different attack patterns",
            "Create a Shield blocking and deflection mechanics",
            "Make a Ocarina playing and song system",
            "Create a Transformation mask mechanics (Deku, Goron, Zora)",
            "Implement a Equipment and inventory management system"
        ]
    
    @staticmethod
    def get_misc_scenarios() -> List[str]:
        return [
            "Create a Fishing system with different fish types",
            "Implement a Horse riding and Epona mechanics",
            "Create a Owl Statue save point system",
            "Make a Gossip Stone hint system",
            "Create a Treasure Chest opening and item collection",
            "Implement a Rupee collection and wallet system",
            "Create a Heart Piece collection and health upgrade",
            "Make a Skulltula token collection system",
            "Create a Gold Skulltula reward system",
            "Implement a Trading sequence with various NPCs"
        ] 