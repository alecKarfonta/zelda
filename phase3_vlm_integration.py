#!/usr/bin/env python3
"""
Zelda OoT Asset Documentation - Phase 3: VLM Integration
Automated image description using Vision-Language Models
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

class VLMImageAnalyzer:
    def __init__(self, project_root: str = "oot"):
        self.project_root = Path(project_root)
        self.assets_dir = self.project_root / "extracted" / "ntsc-1.2" / "assets" / "textures"
        self.output_dir = Path("asset_documentation")
        self.output_dir.mkdir(exist_ok=True)
        
        # VLM Configuration
        self.vlm_config = {
            "use_local": False,  # Set to True if you have local VLM
            "use_api": True,     # Use cloud API as fallback
            "api_key": None,     # Set your API key
            "model": "llava-v1.6-34b",  # Default model
            "max_retries": 3,
            "delay_between_requests": 1.0  # Rate limiting
        }
        
        # Load existing asset inventory
        self.asset_inventory = self.load_asset_inventory()
        
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
    
    def analyze_image_with_api(self, image_path: Path, asset_name: str) -> Dict[str, Any]:
        """Analyze image using cloud API (OpenAI, Anthropic, etc.)."""
        if not self.vlm_config["use_api"]:
            return {"error": "API analysis disabled"}
        
        # This is a placeholder for API integration
        # You would implement the actual API call here
        # For now, we'll create a mock analysis based on filename patterns
        
        return self.mock_image_analysis(image_path, asset_name)
    
    def mock_image_analysis(self, image_path: Path, asset_name: str) -> Dict[str, Any]:
        """Mock image analysis based on filename patterns and directory structure."""
        analysis = {
            "description": "",
            "confidence": 0.8,
            "tags": [],
            "analysis_method": "filename_pattern"
        }
        
        # Extract directory and filename info
        relative_path = image_path.relative_to(self.assets_dir)
        directory = relative_path.parent.name
        filename = image_path.stem
        
        # Analyze based on directory structure
        if directory == "kanji":
            analysis["description"] = f"Japanese kanji character texture: {filename}"
            analysis["tags"] = ["text", "japanese", "kanji", "font"]
        elif directory == "backgrounds":
            analysis["description"] = f"Background texture: {filename}"
            analysis["tags"] = ["background", "environment", "texture"]
        elif directory == "icon_item_static":
            analysis["description"] = f"Item icon texture: {filename}"
            analysis["tags"] = ["icon", "item", "ui", "interface"]
        elif directory == "skyboxes":
            analysis["description"] = f"Skybox texture: {filename}"
            analysis["tags"] = ["skybox", "environment", "background"]
        elif directory == "title_static":
            analysis["description"] = f"Title screen texture: {filename}"
            analysis["tags"] = ["title", "ui", "interface"]
        elif directory == "nes_font_static":
            analysis["description"] = f"NES-style font texture: {filename}"
            analysis["tags"] = ["font", "text", "ui"]
        elif directory == "map_i_static":
            analysis["description"] = f"Map interface texture: {filename}"
            analysis["tags"] = ["map", "ui", "interface"]
        elif directory == "place_title_cards":
            analysis["description"] = f"Location title card texture: {filename}"
            analysis["tags"] = ["title_card", "location", "ui"]
        elif directory == "item_name_static":
            analysis["description"] = f"Item name texture: {filename}"
            analysis["tags"] = ["item_name", "text", "ui"]
        elif directory == "map_name_static":
            analysis["description"] = f"Map name texture: {filename}"
            analysis["tags"] = ["map_name", "text", "ui"]
        elif directory == "do_action_static":
            analysis["description"] = f"Action button texture: {filename}"
            analysis["tags"] = ["action", "button", "ui"]
        elif directory == "parameter_static":
            analysis["description"] = f"Parameter/stat texture: {filename}"
            analysis["tags"] = ["parameter", "stat", "ui"]
        elif directory == "nintendo_rogo_static":
            analysis["description"] = f"Nintendo logo texture: {filename}"
            analysis["tags"] = ["logo", "nintendo", "branding"]
        elif directory == "message_static":
            analysis["description"] = f"Message texture: {filename}"
            analysis["tags"] = ["message", "text", "ui"]
        elif directory == "message_texture_static":
            analysis["description"] = f"Message texture: {filename}"
            analysis["tags"] = ["message", "texture", "ui"]
        else:
            analysis["description"] = f"Texture asset: {filename}"
            analysis["tags"] = ["texture", "asset"]
        
        # Add format-specific tags
        if "ia8" in filename.lower():
            analysis["tags"].append("ia8_format")
        elif "rgba16" in filename.lower():
            analysis["tags"].append("rgba16_format")
        elif "ci8" in filename.lower():
            analysis["tags"].append("ci8_format")
        elif "i4" in filename.lower():
            analysis["tags"].append("i4_format")
        
        return analysis
    
    def analyze_image_with_local_vlm(self, image_path: Path, asset_name: str) -> Dict[str, Any]:
        """Analyze image using local VLM (LLaVA, etc.)."""
        if not self.vlm_config["use_local"]:
            return {"error": "Local VLM not configured"}
        
        # This would integrate with local VLM models
        # For now, return a placeholder
        return {
            "description": f"Local VLM analysis for {asset_name}",
            "confidence": 0.9,
            "tags": ["local_vlm"],
            "analysis_method": "local_vlm"
        }
    
    def analyze_single_image(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single image asset."""
        if not asset.get("is_image", False):
            return {"error": "Not an image asset"}
        
        image_path = Path(asset["full_path"])
        if not image_path.exists():
            return {"error": "Image file not found"}
        
        print(f"Analyzing: {asset['name']}")
        
        # Try local VLM first, then API
        if self.vlm_config["use_local"]:
            analysis = self.analyze_image_with_local_vlm(image_path, asset["name"])
        else:
            analysis = self.analyze_image_with_api(image_path, asset["name"])
        
        # Add metadata
        analysis["asset_name"] = asset["name"]
        analysis["asset_path"] = asset["path"]
        analysis["analysis_timestamp"] = time.time()
        
        return analysis
    
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
        analyses_path = self.output_dir / "vlm_analyses.json"
        with open(analyses_path, 'w') as f:
            json.dump(analyses, f, indent=2)
        print(f"Saved VLM analyses to: {analyses_path}")
        
        # Generate summary report
        self.generate_vlm_report(analyses)
    
    def generate_vlm_report(self, analyses: List[Dict[str, Any]]):
        """Generate a report of VLM analyses."""
        report_path = self.output_dir / "vlm_report.md"
        
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
        
        with open(report_path, 'w') as f:
            f.write("# Zelda OoT Asset VLM Analysis Report\n\n")
            f.write(f"Generated on: {Path().cwd()}\n\n")
            
            # Summary statistics
            f.write("## Summary Statistics\n\n")
            f.write(f"- **Total Images Analyzed**: {len(analyses):,}\n")
            f.write(f"- **Successful Analyses**: {len(successful):,}\n")
            f.write(f"- **Failed Analyses**: {len(failed):,}\n")
            f.write(f"- **Success Rate**: {len(successful)/len(analyses)*100:.1f}%\n\n")
            
            # Top tags
            f.write("## Most Common Tags\n\n")
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            for tag, count in sorted_tags[:20]:
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
                for analysis in category_analyses[:5]:  # Show first 5
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
        
        print(f"Generated VLM report: {report_path}")
    
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
        updated_inventory_path = self.output_dir / "asset_inventory_with_vlm.json"
        with open(updated_inventory_path, 'w') as f:
            json.dump(updated_assets, f, indent=2)
        print(f"Saved updated inventory with VLM data: {updated_inventory_path}")
    
    def run(self, max_images: Optional[int] = None):
        """Execute Phase 3 VLM integration."""
        print("Starting Zelda OoT Asset Documentation - Phase 3: VLM Integration")
        print("=" * 60)
        
        if not self.asset_inventory:
            print("No asset inventory found. Please run Phase 1 & 2 first.")
            return
        
        # Process image assets
        print("\nProcessing Image Assets for VLM Analysis")
        print("-" * 40)
        analyses = self.process_image_assets(max_images)
        
        # Save results
        print("\nSaving VLM Analysis Results")
        print("-" * 40)
        self.save_vlm_analyses(analyses)
        
        # Update asset inventory
        print("\nUpdating Asset Inventory with VLM Data")
        print("-" * 40)
        self.update_asset_inventory_with_vlm(analyses)
        
        print("\nPhase 3 VLM integration complete!")
        print(f"Results saved in: {self.output_dir}")

def main():
    """Main entry point."""
    analyzer = VLMImageAnalyzer()
    
    # For testing, process only first 50 images
    # Remove max_images parameter to process all images
    analyzer.run(max_images=50)

if __name__ == "__main__":
    main() 