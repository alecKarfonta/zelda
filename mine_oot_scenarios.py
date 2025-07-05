#!/usr/bin/env python3
"""
OoT Actor Scenario Template Miner

Automatically extracts scenario templates from OoT actor source files
to create authentic, diverse training data scenarios.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class OoTScenarioMiner:
    """Mines scenario templates from OoT actor source files"""
    
    def __init__(self, oot_path: str = "oot"):
        self.oot_path = Path(oot_path)
        self.actors_path = self.oot_path / "src" / "overlays" / "actors"
        self.mined_scenarios = {
            "enemy": [],
            "npc": [],
            "item": [],
            "object": [],
            "background": [],
            "effect": [],
            "player": [],
            "misc": []
        }
        
    def extract_actor_info(self, file_path: Path) -> Optional[Dict]:
        """Extract actor information from a source file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract actor name from filename
            actor_name = file_path.stem.replace('z_', '')
            
            # Extract description from comment block
            desc_match = re.search(r'/\*\s*\*\s*File:\s*[^\n]*\n\s*\*\s*Overlay:\s*[^\n]*\n\s*\*\s*Description:\s*([^*]+?)\s*\*/', content, re.DOTALL)
            description = desc_match.group(1).strip() if desc_match else ""
            
            # Extract actor category from ActorProfile
            category_match = re.search(r'ACTORCAT_(\w+)', content)
            category = category_match.group(1).lower() if category_match else "misc"
            
            # Map OoT categories to our categories
            category_mapping = {
                "enemy": "enemy",
                "npc": "npc", 
                "itemaction": "item",
                "prop": "object",
                "bg": "background",
                "item": "item",
                "misc": "misc"
            }
            
            mapped_category = category_mapping.get(category, "misc")
            
            return {
                "name": actor_name,
                "description": description,
                "category": mapped_category,
                "file_path": str(file_path)
            }
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return None
    
    def generate_scenario_template(self, actor_info: Dict) -> str:
        """Generate a scenario template from actor information"""
        name = actor_info["name"]
        description = actor_info["description"]
        
        # Clean up the name for better readability
        clean_name = name.replace('_', ' ').title()
        
        # Generate scenario based on description
        if description:
            # Remove common prefixes and clean up
            desc = description.strip()
            if desc.startswith("Spawns"):
                return f"Create an actor that {desc.lower()}"
            elif desc.startswith("Manages"):
                return f"Implement an actor that {desc.lower()}"
            elif desc.startswith("Environmental"):
                return f"Create an actor for {desc.lower()}"
            elif "bombable" in desc.lower():
                return f"Implement a bombable {desc.lower()}"
            elif "boulder" in desc.lower():
                return f"Create a {desc.lower()} that can be broken with a hammer"
            else:
                return f"Create a {clean_name} actor that {desc.lower()}"
        else:
            # Fallback based on name patterns
            if "En_" in name:
                return f"Create a {clean_name} enemy with authentic OoT behavior patterns"
            elif "Obj_" in name:
                return f"Implement a {clean_name} object with proper collision and interaction"
            elif "Bg_" in name:
                return f"Create a {clean_name} background element for environmental effects"
            elif "Item_" in name:
                return f"Create a {clean_name} item with proper collection mechanics"
            else:
                return f"Implement a {clean_name} actor following OoT decompilation patterns"
    
    def mine_all_actors(self) -> Dict[str, List[str]]:
        """Mine scenario templates from all actor source files"""
        print("🔍 Mining OoT actor scenario templates...")
        
        # Find all actor .c files
        actor_files = list(self.actors_path.rglob("z_*.c"))
        print(f"Found {len(actor_files)} actor files")
        
        for file_path in actor_files:
            actor_info = self.extract_actor_info(file_path)
            if actor_info:
                scenario = self.generate_scenario_template(actor_info)
                category = actor_info["category"]
                
                # Add to appropriate category
                if category in self.mined_scenarios:
                    self.mined_scenarios[category].append(scenario)
                else:
                    self.mined_scenarios["misc"].append(scenario)
                
                print(f"  ✓ {actor_info['name']}: {scenario[:60]}...")
        
        # Remove duplicates and sort
        for category in self.mined_scenarios:
            self.mined_scenarios[category] = sorted(list(set(self.mined_scenarios[category])))
        
        return self.mined_scenarios
    
    def generate_python_code(self) -> str:
        """Generate Python code for the scenario templates"""
        code = """class RealOoTScenarioTemplate:
    \"\"\"Real OoT scenario templates mined from actual source code\"\"\"
    
    @staticmethod
    def get_enemy_scenarios() -> List[str]:
        return [
"""
        
        for scenario in self.mined_scenarios["enemy"]:
            code += f'            "{scenario}",\n'
        
        code += """        ]
    
    @staticmethod
    def get_npc_scenarios() -> List[str]:
        return [
"""
        
        for scenario in self.mined_scenarios["npc"]:
            code += f'            "{scenario}",\n'
        
        code += """        ]
    
    @staticmethod
    def get_item_scenarios() -> List[str]:
        return [
"""
        
        for scenario in self.mined_scenarios["item"]:
            code += f'            "{scenario}",\n'
        
        code += """        ]
    
    @staticmethod
    def get_object_scenarios() -> List[str]:
        return [
"""
        
        for scenario in self.mined_scenarios["object"]:
            code += f'            "{scenario}",\n'
        
        code += """        ]
    
    @staticmethod
    def get_background_scenarios() -> List[str]:
        return [
"""
        
        for scenario in self.mined_scenarios["background"]:
            code += f'            "{scenario}",\n'
        
        code += """        ]
    
    @staticmethod
    def get_effect_scenarios() -> List[str]:
        return [
"""
        
        for scenario in self.mined_scenarios["effect"]:
            code += f'            "{scenario}",\n'
        
        code += """        ]
    
    @staticmethod
    def get_player_scenarios() -> List[str]:
        return [
"""
        
        for scenario in self.mined_scenarios["player"]:
            code += f'            "{scenario}",\n'
        
        code += """        ]
    
    @staticmethod
    def get_misc_scenarios() -> List[str]:
        return [
"""
        
        for scenario in self.mined_scenarios["misc"]:
            code += f'            "{scenario}",\n'
        
        code += """        ]
"""
        
        return code
    
    def save_results(self, output_file: str = "mined_scenarios.json"):
        """Save mined scenarios to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(self.mined_scenarios, f, indent=2)
        print(f"💾 Saved mined scenarios to {output_file}")
    
    def print_summary(self):
        """Print a summary of mined scenarios"""
        print("\n📊 Mined Scenario Summary:")
        print("=" * 50)
        
        total_scenarios = 0
        for category, scenarios in self.mined_scenarios.items():
            count = len(scenarios)
            total_scenarios += count
            print(f"{category.upper():12}: {count:3d} scenarios")
        
        print(f"{'TOTAL':12}: {total_scenarios:3d} scenarios")
        print("=" * 50)

def main():
    """Main function to mine OoT scenarios"""
    miner = OoTScenarioMiner()
    
    # Mine all scenarios
    scenarios = miner.mine_all_actors()
    
    # Print summary
    miner.print_summary()
    
    # Save results
    miner.save_results()
    
    # Generate Python code
    python_code = miner.generate_python_code()
    
    # Save Python code
    with open("mined_scenario_templates.py", 'w') as f:
        f.write(python_code)
    
    print("💾 Saved Python code to mined_scenario_templates.py")
    
    # Show sample scenarios
    print("\n🎯 Sample Scenarios by Category:")
    print("=" * 50)
    
    for category, scenarios in scenarios.items():
        if scenarios:
            print(f"\n{category.upper()}:")
            for i, scenario in enumerate(scenarios[:3]):  # Show first 3
                print(f"  {i+1}. {scenario}")
            if len(scenarios) > 3:
                print(f"  ... and {len(scenarios) - 3} more")

if __name__ == "__main__":
    main() 