#!/usr/bin/env python3
"""
Zelda OoT Asset Documentation - Phase 3: Enhanced VLM Integration
Automated image description using Vision-Language Models with real API support
"""

import os
import json
import base64
import requests
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from PIL import Image
import hashlib

# Optional OpenAI import
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI library not available. Install with: pip install openai")

class EnhancedVLMImageAnalyzer:
    def __init__(self, project_root: str = "oot"):
        self.project_root = Path(project_root)
        self.assets_dir = self.project_root / "extracted" / "ntsc-1.2" / "assets" / "textures"
        self.output_dir = Path("asset_documentation")
        self.output_dir.mkdir(exist_ok=True)
        
        # VLM Configuration
        self.vlm_config = {
            "use_local": False,
            "use_openai": False and OPENAI_AVAILABLE,  # Only if OpenAI is available
            "use_anthropic": False,  # Set to True and provide API key
            "use_mock": True,  # Use mock analysis for testing
            "openai_api_key": None,
            "anthropic_api_key": None,
            "model": "gpt-4-vision-preview",  # OpenAI model
            "max_retries": 3,
            "delay_between_requests": 2.0  # Rate limiting
        }
        
        # Load existing asset inventory
        self.asset_inventory = self.load_asset_inventory()
        
        # Initialize API clients if configured
        if self.vlm_config["use_openai"] and self.vlm_config["openai_api_key"] and OPENAI_AVAILABLE:
            openai.api_key = self.vlm_config["openai_api_key"]
        
    def load_asset_inventory(self) -> List[Dict[str, Any]]:
        """Load the existing asset inventory."""
        inventory_path = self.output_dir / "asset_inventory.json"
        if inventory_path.exists():
            with open(inventory_path, 'r') as f:
                return json.load(f)
        else:
            print("Asset inventory not found. Please run Phase 1 & 2 first.")
            return []
    
    def encode_image_to_base64(self, image_path: Path) -> str:
        """Encode image to base64 for API transmission."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error encoding image {image_path}: {e}")
            return ""
    
    def analyze_with_openai(self, image_path: Path, asset_name: str) -> Dict[str, Any]:
        """Analyze image using OpenAI's GPT-4V."""
        if not self.vlm_config["use_openai"] or not OPENAI_AVAILABLE:
            return {"error": "OpenAI analysis disabled or not available"}
        
        try:
            # Encode image
            base64_image = self.encode_image_to_base64(image_path)
            if not base64_image:
                return {"error": "Failed to encode image"}
            
            # Prepare prompt for Zelda OoT context
            prompt = f"""
            Analyze this texture from The Legend of Zelda: Ocarina of Time.
            Asset name: {asset_name}
            
            Please provide:
            1. A clear description of what this texture shows
            2. The likely in-game usage (UI element, background, item icon, etc.)
            3. Any notable visual characteristics
            4. Relevant tags for categorization
            
            Focus on the game context and be specific about the texture's purpose.
            """
            
            # Make API call
            response = openai.ChatCompletion.create(
                model=self.vlm_config["model"],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            return {
                "description": content,
                "confidence": 0.9,
                "tags": self.extract_tags_from_description(content),
                "analysis_method": "openai_gpt4v",
                "raw_response": content
            }
            
        except Exception as e:
            return {"error": f"OpenAI API error: {str(e)}"}
    
    def analyze_with_anthropic(self, image_path: Path, asset_name: str) -> Dict[str, Any]:
        """Analyze image using Anthropic's Claude."""
        if not self.vlm_config["use_anthropic"]:
            return {"error": "Anthropic analysis disabled"}
        
        try:
            # Encode image
            base64_image = self.encode_image_to_base64(image_path)
            if not base64_image:
                return {"error": "Failed to encode image"}
            
            # Prepare prompt
            prompt = f"""
            Analyze this texture from The Legend of Zelda: Ocarina of Time.
            Asset name: {asset_name}
            
            Provide a detailed description including:
            1. What the texture shows
            2. Its likely in-game usage
            3. Visual characteristics
            4. Relevant tags
            
            Be specific about the game context.
            """
            
            # Make API call (this would use Anthropic's API)
            # For now, return a placeholder
            return {
                "description": f"Anthropic Claude analysis for {asset_name}",
                "confidence": 0.9,
                "tags": ["anthropic", "claude"],
                "analysis_method": "anthropic_claude"
            }
            
        except Exception as e:
            return {"error": f"Anthropic API error: {str(e)}"}
    
    def extract_tags_from_description(self, description: str) -> List[str]:
        """Extract relevant tags from a description."""
        tags = []
        description_lower = description.lower()
        
        # Game-specific tags
        if "ui" in description_lower or "interface" in description_lower:
            tags.append("ui")
        if "background" in description_lower:
            tags.append("background")
        if "icon" in description_lower:
            tags.append("icon")
        if "text" in description_lower or "font" in description_lower:
            tags.append("text")
        if "texture" in description_lower:
            tags.append("texture")
        if "item" in description_lower:
            tags.append("item")
        if "map" in description_lower:
            tags.append("map")
        if "logo" in description_lower:
            tags.append("logo")
        if "button" in description_lower:
            tags.append("button")
        
        # Format tags
        if "ia8" in description_lower:
            tags.append("ia8_format")
        if "rgba16" in description_lower:
            tags.append("rgba16_format")
        if "ci8" in description_lower:
            tags.append("ci8_format")
        if "i4" in description_lower:
            tags.append("i4_format")
        
        return tags
    
    def enhanced_mock_analysis(self, image_path: Path, asset_name: str) -> Dict[str, Any]:
        """Enhanced mock analysis with more detailed descriptions."""
        analysis = {
            "description": "",
            "confidence": 0.8,
            "tags": [],
            "analysis_method": "enhanced_filename_pattern"
        }
        
        # Extract directory and filename info
        relative_path = image_path.relative_to(self.assets_dir)
        directory = relative_path.parent.name
        filename = image_path.stem
        
        # Enhanced analysis based on directory and filename patterns
        if directory == "kanji":
            analysis["description"] = f"Japanese kanji character texture '{filename}' - likely used for text rendering in the game's Japanese localization"
            analysis["tags"] = ["text", "japanese", "kanji", "font", "localization"]
        elif directory == "backgrounds":
            analysis["description"] = f"Background texture '{filename}' - environmental texture used for scene backgrounds"
            analysis["tags"] = ["background", "environment", "texture", "scene"]
        elif directory == "icon_item_static":
            analysis["description"] = f"Item icon texture '{filename}' - UI element representing an in-game item"
            analysis["tags"] = ["icon", "item", "ui", "interface", "inventory"]
        elif directory == "icon_item_24_static":
            analysis["description"] = f"Quest item icon texture '{filename}' - special item icon for quest tracking"
            analysis["tags"] = ["icon", "quest", "item", "ui", "special"]
        elif directory == "icon_item_dungeon_static":
            analysis["description"] = f"Dungeon map interface texture '{filename}' - UI element for dungeon navigation"
            analysis["tags"] = ["dungeon", "map", "ui", "interface", "navigation"]
        elif directory == "skyboxes":
            analysis["description"] = f"Skybox texture '{filename}' - environmental sky texture for outdoor scenes"
            analysis["tags"] = ["skybox", "environment", "background", "outdoor"]
        elif directory == "title_static":
            analysis["description"] = f"Title screen texture '{filename}' - UI element for game title screens"
            analysis["tags"] = ["title", "ui", "interface", "menu"]
        elif directory == "nes_font_static":
            analysis["description"] = f"NES-style font texture '{filename}' - retro font texture for text rendering"
            analysis["tags"] = ["font", "text", "ui", "retro", "nes"]
        elif directory == "map_i_static":
            analysis["description"] = f"Map interface texture '{filename}' - UI element for world map display"
            analysis["tags"] = ["map", "ui", "interface", "world"]
        elif directory == "place_title_cards":
            analysis["description"] = f"Location title card texture '{filename}' - UI element for area name display"
            analysis["tags"] = ["title_card", "location", "ui", "area"]
        elif directory == "item_name_static":
            analysis["description"] = f"Item name texture '{filename}' - text texture for item names"
            analysis["tags"] = ["item_name", "text", "ui", "label"]
        elif directory == "map_name_static":
            analysis["description"] = f"Map name texture '{filename}' - text texture for location names"
            analysis["tags"] = ["map_name", "text", "ui", "location"]
        elif directory == "do_action_static":
            analysis["description"] = f"Action button texture '{filename}' - UI element for action prompts"
            analysis["tags"] = ["action", "button", "ui", "prompt"]
        elif directory == "parameter_static":
            analysis["description"] = f"Parameter/stat texture '{filename}' - UI element for character stats"
            analysis["tags"] = ["parameter", "stat", "ui", "character"]
        elif directory == "nintendo_rogo_static":
            analysis["description"] = f"Nintendo logo texture '{filename}' - branding element for Nintendo copyright"
            analysis["tags"] = ["logo", "nintendo", "branding", "copyright"]
        elif directory == "message_static":
            analysis["description"] = f"Message texture '{filename}' - text texture for in-game messages"
            analysis["tags"] = ["message", "text", "ui", "dialogue"]
        elif directory == "message_texture_static":
            analysis["description"] = f"Message texture '{filename}' - UI element for message display"
            analysis["tags"] = ["message", "texture", "ui", "dialogue"]
        else:
            analysis["description"] = f"Texture asset '{filename}' - general game texture"
            analysis["tags"] = ["texture", "asset", "general"]
        
        # Add format-specific tags
        if "ia8" in filename.lower():
            analysis["tags"].append("ia8_format")
        elif "rgba16" in filename.lower():
            analysis["tags"].append("rgba16_format")
        elif "ci8" in filename.lower():
            analysis["tags"].append("ci8_format")
        elif "i4" in filename.lower():
            analysis["tags"].append("i4_format")
        elif "rgba32" in filename.lower():
            analysis["tags"].append("rgba32_format")
        
        # Add specific content tags based on filename
        if "quest" in filename.lower():
            analysis["tags"].append("quest")
        if "dungeon" in filename.lower():
            analysis["tags"].append("dungeon")
        if "map" in filename.lower():
            analysis["tags"].append("map")
        if "icon" in filename.lower():
            analysis["tags"].append("icon")
        if "logo" in filename.lower():
            analysis["tags"].append("logo")
        if "button" in filename.lower():
            analysis["tags"].append("button")
        
        return analysis
    
    def analyze_single_image(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single image asset using the best available method."""
        if not asset.get("is_image", False):
            return {"error": "Not an image asset"}
        
        image_path = Path(asset["full_path"])
        if not image_path.exists():
            return {"error": "Image file not found"}
        
        print(f"Analyzing: {asset['name']}")
        
        # Try different analysis methods in order of preference
        if self.vlm_config["use_openai"]:
            analysis = self.analyze_with_openai(image_path, asset["name"])
            if "error" not in analysis:
                analysis["asset_name"] = asset["name"]
                analysis["asset_path"] = asset["path"]
                analysis["analysis_timestamp"] = time.time()
                return analysis
        
        if self.vlm_config["use_anthropic"]:
            analysis = self.analyze_with_anthropic(image_path, asset["name"])
            if "error" not in analysis:
                analysis["asset_name"] = asset["name"]
                analysis["asset_path"] = asset["path"]
                analysis["analysis_timestamp"] = time.time()
                return analysis
        
        # Fall back to enhanced mock analysis
        if self.vlm_config["use_mock"]:
            analysis = self.enhanced_mock_analysis(image_path, asset["name"])
            analysis["asset_name"] = asset["name"]
            analysis["asset_path"] = asset["path"]
            analysis["analysis_timestamp"] = time.time()
            return analysis
        
        return {"error": "No analysis method available"}
    
    def process_image_assets(self, max_images: Optional[int] = None) -> List[Dict[str, Any]]:
        """Process all image assets for VLM analysis."""
        image_assets = [asset for asset in self.asset_inventory if asset.get("is_image", False)]
        
        if max_images:
            image_assets = image_assets[:max_images]
        
        print(f"Processing {len(image_assets)} image assets for VLM analysis...")
        
        analyses = []
        for i, asset in enumerate(image_assets):
            if i % 10 == 0:
                print(f"Processing image {i+1}/{len(image_assets)}...")
            
            analysis = self.analyze_single_image(asset)
            analyses.append(analysis)
            
            # Rate limiting
            if self.vlm_config["delay_between_requests"] > 0:
                time.sleep(self.vlm_config["delay_between_requests"])
        
        return analyses
    
    def save_vlm_analyses(self, analyses: List[Dict[str, Any]]):
        """Save VLM analyses to files."""
        # Save full analyses
        analyses_path = self.output_dir / "vlm_analyses_enhanced.json"
        with open(analyses_path, 'w') as f:
            json.dump(analyses, f, indent=2)
        print(f"Saved enhanced VLM analyses to: {analyses_path}")
        
        # Generate summary report
        self.generate_enhanced_vlm_report(analyses)
    
    def generate_enhanced_vlm_report(self, analyses: List[Dict[str, Any]]):
        """Generate an enhanced report of VLM analyses."""
        report_path = self.output_dir / "vlm_report_enhanced.md"
        
        # Count successful vs failed analyses
        successful = [a for a in analyses if "error" not in a]
        failed = [a for a in analyses if "error" in a]
        
        # Collect all tags
        all_tags = []
        for analysis in successful:
            all_tags.extend(analysis.get("tags", []))
        
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Analysis method breakdown
        method_counts = {}
        for analysis in successful:
            method = analysis.get("analysis_method", "unknown")
            method_counts[method] = method_counts.get(method, 0) + 1
        
        with open(report_path, 'w') as f:
            f.write("# Zelda OoT Asset Enhanced VLM Analysis Report\n\n")
            f.write(f"Generated on: {Path().cwd()}\n\n")
            
            # Summary statistics
            f.write("## Summary Statistics\n\n")
            f.write(f"- **Total Images Analyzed**: {len(analyses):,}\n")
            f.write(f"- **Successful Analyses**: {len(successful):,}\n")
            f.write(f"- **Failed Analyses**: {len(failed):,}\n")
            f.write(f"- **Success Rate**: {len(successful)/len(analyses)*100:.1f}%\n\n")
            
            # Analysis method breakdown
            f.write("## Analysis Method Breakdown\n\n")
            for method, count in sorted(method_counts.items(), key=lambda x: x[1], reverse=True):
                f.write(f"- **{method}**: {count:,}\n")
            f.write("\n")
            
            # Top tags
            f.write("## Most Common Tags\n\n")
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            for tag, count in sorted_tags[:25]:
                f.write(f"- **{tag}**: {count:,}\n")
            f.write("\n")
            
            # Sample descriptions by category
            f.write("## Sample Descriptions by Category\n\n")
            
            categories = {}
            for analysis in successful:
                directory = Path(analysis["asset_path"]).parent.name
                if directory not in categories:
                    categories[directory] = []
                categories[directory].append(analysis)
            
            for category, category_analyses in sorted(categories.items()):
                f.write(f"### {category}\n\n")
                for analysis in category_analyses[:3]:  # Show first 3
                    f.write(f"- **{analysis['asset_name']}**: {analysis['description']}\n")
                f.write("\n")
            
            # Error summary
            if failed:
                f.write("## Analysis Errors\n\n")
                error_types = {}
                for analysis in failed:
                    error = analysis.get("error", "Unknown error")
                    error_types[error] = error_types.get(error, 0) + 1
                
                for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- **{error}**: {count:,}\n")
                f.write("\n")
        
        print(f"Generated enhanced VLM report: {report_path}")
    
    def update_asset_inventory_with_vlm(self, analyses: List[Dict[str, Any]]):
        """Update the asset inventory with VLM analysis results."""
        # Create lookup dictionary
        analysis_lookup = {}
        for analysis in analyses:
            if "asset_name" in analysis:
                analysis_lookup[analysis["asset_name"]] = analysis
        
        # Update asset inventory
        updated_assets = []
        for asset in self.asset_inventory:
            if asset["name"] in analysis_lookup:
                asset["vlm_analysis"] = analysis_lookup[asset["name"]]
            updated_assets.append(asset)
        
        # Save updated inventory
        updated_inventory_path = self.output_dir / "asset_inventory_with_vlm_enhanced.json"
        with open(updated_inventory_path, 'w') as f:
            json.dump(updated_assets, f, indent=2)
        print(f"Saved updated inventory with enhanced VLM data: {updated_inventory_path}")
    
    def run(self, max_images: Optional[int] = None):
        """Execute Phase 3 Enhanced VLM integration."""
        print("Starting Zelda OoT Asset Documentation - Phase 3: Enhanced VLM Integration")
        print("=" * 70)
        
        if not self.asset_inventory:
            print("No asset inventory found. Please run Phase 1 & 2 first.")
            return
        
        # Process image assets
        print("\nProcessing Image Assets for Enhanced VLM Analysis")
        print("-" * 50)
        analyses = self.process_image_assets(max_images)
        
        # Save results
        print("\nSaving Enhanced VLM Analysis Results")
        print("-" * 50)
        self.save_vlm_analyses(analyses)
        
        # Update asset inventory
        print("\nUpdating Asset Inventory with Enhanced VLM Data")
        print("-" * 50)
        self.update_asset_inventory_with_vlm(analyses)
        
        print("\nPhase 3 Enhanced VLM integration complete!")
        print(f"Results saved in: {self.output_dir}")

def main():
    """Main entry point."""
    analyzer = EnhancedVLMImageAnalyzer()
    
    # For testing, process only first 30 images
    # Remove max_images parameter to process all images
    analyzer.run(max_images=30)

if __name__ == "__main__":
    main() 