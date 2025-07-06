#!/usr/bin/env python3
"""
Dynamic Temperature Manager for OoT Training Data Generation
"""

from typing import Dict

from models.enums import ExampleType, ActorCategory
from models.enums import TrainingExample


class DynamicTemperatureManager:
    """Manages dynamic temperature based on diversity needs"""
    
    def __init__(self):
        self.base_temperature = 0.3  # Reduced for more conservative generation
        self.min_temperature = 0.3
        self.max_temperature = 0.9
        self.category_usage = {cat.value: 0 for cat in ActorCategory}
        self.recent_examples = []
        self.max_recent = 10
        
    def get_dynamic_temperature(self, example_type: ExampleType, complexity: str, 
                              diversity_metrics: Dict) -> float:
        """Calculate dynamic temperature based on diversity needs"""
        
        # Start with base temperature
        temp = self.base_temperature
        
        # Adjust based on category diversity
        category_coverage = len([c for c in diversity_metrics['actor_categories'].values() if c > 0])
        total_categories = len(ActorCategory)
        coverage_ratio = category_coverage / total_categories
        
        if coverage_ratio < 0.5:  # Low diversity - increase temperature
            temp += 0.2
        elif coverage_ratio > 0.8:  # High diversity - decrease temperature for consistency
            temp -= 0.1
        
        # Adjust based on recent repetition
        if len(self.recent_examples) >= 3:
            recent_types = [ex['type'] for ex in self.recent_examples[-3:]]
            if len(set(recent_types)) == 1:  # All same type - increase temperature
                temp += 0.15
        
        # Adjust based on complexity
        if complexity == "advanced":
            temp += 0.1  # More variety for complex examples
        elif complexity == "basic":
            temp -= 0.05  # Less variety for basic examples
        
        # Adjust based on example type
        if example_type in [ExampleType.ACTOR_CREATION, ExampleType.CUSTOM_MECHANICS]:
            temp += 0.1  # More variety for creative examples
        elif example_type in [ExampleType.CODE_EXPLANATION, ExampleType.DEBUGGING_HELP]:
            temp -= 0.05  # Less variety for explanatory examples
        
        # Clamp to valid range
        temp = max(self.min_temperature, min(self.max_temperature, temp))
        
        return temp
    
    def update_usage(self, example: TrainingExample, diversity_metrics: Dict):
        """Update usage tracking for dynamic temperature calculation"""
        
        # Update recent examples
        self.recent_examples.append({
            'type': example.example_type.value,
            'instruction': example.instruction[:50]
        })
        
        # Keep only recent examples
        if len(self.recent_examples) > self.max_recent:
            self.recent_examples.pop(0)
        
        # Update category usage
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
                self.category_usage[category.value] += 1
                break 