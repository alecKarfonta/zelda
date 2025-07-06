#!/usr/bin/env python3
"""
Enhanced Asset Analysis for Zelda OoT
Adds additional useful features for understanding and navigating assets
"""

import json
import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter

class EnhancedAssetAnalyzer:
    def __init__(self, project_root: str = "oot"):
        self.project_root = Path(project_root)
        self.output_dir = Path("asset_documentation")
        
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
    
    def analyze_filename_patterns(self) -> Dict[str, Any]:
        """Analyze filename patterns to help users understand naming conventions."""
        patterns = {
            "prefixes": Counter(),
            "suffixes": Counter(),
            "common_words": Counter(),
            "format_indicators": Counter(),
            "size_indicators": Counter(),
            "language_indicators": Counter()
        }
        
        for asset in self.asset_inventory:
            filename = asset["name"]
            
            # Analyze prefixes (common starting patterns)
            if filename.startswith("g"):
                patterns["prefixes"]["g_"] += 1
            elif filename.startswith("nintendo"):
                patterns["prefixes"]["nintendo_"] += 1
            elif filename.startswith("icon"):
                patterns["prefixes"]["icon_"] += 1
            elif filename.startswith("map"):
                patterns["prefixes"]["map_"] += 1
            elif filename.startswith("message"):
                patterns["prefixes"]["message_"] += 1
            
            # Analyze suffixes and format indicators
            if ".ia8" in filename:
                patterns["format_indicators"]["ia8"] += 1
            if ".rgba16" in filename:
                patterns["format_indicators"]["rgba16"] += 1
            if ".ci8" in filename:
                patterns["format_indicators"]["ci8"] += 1
            if ".i4" in filename:
                patterns["format_indicators"]["i4"] += 1
            if ".rgba32" in filename:
                patterns["format_indicators"]["rgba32"] += 1
            
            # Language indicators
            if "JPN" in filename:
                patterns["language_indicators"]["JPN"] += 1
            if "ENG" in filename:
                patterns["language_indicators"]["ENG"] += 1
            
            # Common words
            words = re.findall(r'[A-Z][a-z]+', filename)
            for word in words:
                if len(word) > 2:  # Skip short words
                    patterns["common_words"][word] += 1
        
        return patterns
    
    def analyze_asset_relationships(self) -> Dict[str, Any]:
        """Analyze relationships between assets (similar names, related files, etc.)."""
        relationships = {
            "similar_names": [],
            "related_groups": defaultdict(list),
            "paired_files": [],  # .c and .h pairs
            "size_clusters": defaultdict(list)
        }
        
        # Group by directory and analyze relationships
        by_directory = defaultdict(list)
        for asset in self.asset_inventory:
            by_directory[asset["directory"]].append(asset)
        
        # Find similar names within directories
        for directory, assets in by_directory.items():
            for i, asset1 in enumerate(assets):
                for j, asset2 in enumerate(assets[i+1:], i+1):
                    name1 = asset1["name"].lower()
                    name2 = asset2["name"].lower()
                    
                    # Check for similar names (shared prefix/suffix)
                    if name1 != name2:
                        common_prefix = os.path.commonprefix([name1, name2])
                        if len(common_prefix) > 5:  # Significant common prefix
                            relationships["similar_names"].append({
                                "asset1": asset1["name"],
                                "asset2": asset2["name"],
                                "directory": directory,
                                "common_prefix": common_prefix
                            })
        
        # Find paired files (.c and .h)
        for asset in self.asset_inventory:
            if asset["name"].endswith(".c"):
                base_name = asset["name"][:-2]
                header_name = base_name + ".h"
                
                # Look for corresponding header
                for other_asset in self.asset_inventory:
                    if other_asset["name"] == header_name and other_asset["directory"] == asset["directory"]:
                        relationships["paired_files"].append({
                            "c_file": asset["name"],
                            "h_file": header_name,
                            "directory": asset["directory"]
                        })
        
        # Size clusters (group assets by size ranges)
        for asset in self.asset_inventory:
            size_mb = asset.get("size_bytes", 0) / 1024 / 1024
            if size_mb < 0.01:
                size_range = "tiny (< 10KB)"
            elif size_mb < 0.1:
                size_range = "small (10KB-100KB)"
            elif size_mb < 1:
                size_range = "medium (100KB-1MB)"
            else:
                size_range = "large (> 1MB)"
            
            relationships["size_clusters"][size_range].append(asset["name"])
        
        return relationships
    
    def generate_search_guide(self) -> Dict[str, Any]:
        """Generate a search guide to help users find specific types of assets."""
        search_guide = {
            "by_purpose": {
                "UI Elements": ["icon_item_static", "icon_item_24_static", "do_action_static"],
                "Text/Fonts": ["kanji", "nes_font_static", "message_static"],
                "Maps": ["map_i_static", "map_name_static", "map_48x85_static", "map_grand_static"],
                "Backgrounds": ["backgrounds", "skyboxes"],
                "Titles": ["title_static", "place_title_cards", "nintendo_rogo_static"],
                "Items": ["item_name_static", "parameter_static"],
                "Messages": ["message_static", "message_texture_static"]
            },
            "by_format": {
                "i4": "4-bit intensity (most common, good for fonts/text)",
                "ia8": "8-bit intensity + alpha (good for UI elements)",
                "ci8": "8-bit color index (good for detailed textures)",
                "rgba16": "16-bit RGBA (good for detailed images)",
                "rgba32": "32-bit RGBA (highest quality, largest files)",
                "i8": "8-bit intensity (good for grayscale)"
            },
            "by_language": {
                "Japanese": ["kanji", "icon_item_jpn_static"],
                "English": ["icon_item_nes_static"],
                "Universal": ["icon_item_static", "backgrounds", "skyboxes"]
            },
            "quick_filters": {
                "Largest Files": "Sort by size_bytes descending",
                "Most Referenced": "Filter by reference_count > 0",
                "Recent Changes": "Sort by modified_time descending",
                "Specific Format": "Filter by detected_format",
                "UI Elements": "Search directories with 'icon' or 'static'",
                "Backgrounds": "Search 'backgrounds' or 'skyboxes' directories"
            }
        }
        
        return search_guide
    
    def analyze_asset_complexity(self) -> Dict[str, Any]:
        """Analyze asset complexity based on various factors."""
        complexity_analysis = {
            "simple_assets": [],
            "complex_assets": [],
            "unique_assets": [],
            "mass_produced": []
        }
        
        # Analyze by directory patterns
        directory_counts = Counter(asset["directory"] for asset in self.asset_inventory)
        
        for asset in self.asset_inventory:
            directory = asset["directory"]
            count = directory_counts[directory]
            
            # Assets in directories with many files are likely "mass produced"
            if count > 100:
                complexity_analysis["mass_produced"].append({
                    "name": asset["name"],
                    "directory": directory,
                    "count_in_directory": count
                })
            # Assets in directories with few files might be unique
            elif count < 10:
                complexity_analysis["unique_assets"].append({
                    "name": asset["name"],
                    "directory": directory,
                    "count_in_directory": count
                })
            
            # Complex assets based on size and format
            size_mb = asset.get("size_bytes", 0) / 1024 / 1024
            format = asset.get("detected_format", "")
            
            if size_mb > 0.01 or format in ["rgba32", "rgba16", "ci8"]:
                complexity_analysis["complex_assets"].append({
                    "name": asset["name"],
                    "size_mb": size_mb,
                    "format": format,
                    "reason": "Large size or high-quality format"
                })
            else:
                complexity_analysis["simple_assets"].append({
                    "name": asset["name"],
                    "size_mb": size_mb,
                    "format": format
                })
        
        return complexity_analysis
    
    def generate_enhanced_report(self):
        """Generate an enhanced asset analysis report with all new features."""
        report_path = self.output_dir / "enhanced_asset_analysis.md"
        
        # Run all analyses
        filename_patterns = self.analyze_filename_patterns()
        relationships = self.analyze_asset_relationships()
        search_guide = self.generate_search_guide()
        complexity = self.analyze_asset_complexity()
        
        with open(report_path, 'w') as f:
            f.write("# Enhanced Zelda OoT Asset Analysis Report\n\n")
            f.write(f"Generated on: {Path().cwd()}\n\n")
            
            # Search Guide (most useful for users)
            f.write("## 🔍 Quick Search Guide\n\n")
            f.write("### By Purpose\n\n")
            for purpose, directories in search_guide["by_purpose"].items():
                f.write(f"**{purpose}**:\n")
                for directory in directories:
                    count = len([a for a in self.asset_inventory if a["directory"] == directory])
                    f.write(f"- `{directory}` ({count} assets)\n")
                f.write("\n")
            
            f.write("### By Format\n\n")
            for format_name, description in search_guide["by_format"].items():
                count = len([a for a in self.asset_inventory if a.get("detected_format") == format_name])
                f.write(f"**{format_name}** ({count} assets): {description}\n\n")
            
            f.write("### Quick Filters\n\n")
            for filter_name, description in search_guide["quick_filters"].items():
                f.write(f"- **{filter_name}**: {description}\n")
            f.write("\n")
            
            # Filename Patterns
            f.write("## 📝 Filename Pattern Analysis\n\n")
            f.write("### Common Prefixes\n\n")
            for prefix, count in filename_patterns["prefixes"].most_common(10):
                f.write(f"- `{prefix}`: {count} assets\n")
            f.write("\n")
            
            f.write("### Common Words in Filenames\n\n")
            for word, count in filename_patterns["common_words"].most_common(15):
                f.write(f"- `{word}`: {count} assets\n")
            f.write("\n")
            
            f.write("### Language Indicators\n\n")
            for lang, count in filename_patterns["language_indicators"].most_common():
                f.write(f"- `{lang}`: {count} assets\n")
            f.write("\n")
            
            # Asset Relationships
            f.write("## 🔗 Asset Relationships\n\n")
            f.write("### Paired Files (.c and .h)\n\n")
            for pair in relationships["paired_files"][:10]:  # Show first 10
                f.write(f"- `{pair['c_file']}` ↔ `{pair['h_file']}` (in {pair['directory']})\n")
            f.write("\n")
            
            f.write("### Similar Names (Common Prefixes)\n\n")
            for similar in relationships["similar_names"][:10]:  # Show first 10
                f.write(f"- `{similar['asset1']}` ↔ `{similar['asset2']}` (prefix: `{similar['common_prefix']}`)\n")
            f.write("\n")
            
            # Size Clusters
            f.write("## 📊 Size Distribution\n\n")
            for size_range, assets in relationships["size_clusters"].items():
                f.write(f"**{size_range}**: {len(assets)} assets\n")
            f.write("\n")
            
            # Complexity Analysis
            f.write("## 🎯 Asset Complexity Analysis\n\n")
            f.write(f"**Simple Assets**: {len(complexity['simple_assets'])} (small, basic formats)\n")
            f.write(f"**Complex Assets**: {len(complexity['complex_assets'])} (large or high-quality formats)\n")
            f.write(f"**Unique Assets**: {len(complexity['unique_assets'])} (in small directories)\n")
            f.write(f"**Mass Produced**: {len(complexity['mass_produced'])} (in large directories)\n\n")
            
            f.write("### Most Complex Assets (Top 10)\n\n")
            complex_sorted = sorted(complexity["complex_assets"], 
                                  key=lambda x: x["size_mb"], reverse=True)
            for asset in complex_sorted[:10]:
                f.write(f"- `{asset['name']}`: {asset['size_mb']:.3f} MB ({asset['format']})\n")
            f.write("\n")
            
            f.write("### Unique Assets (Top 10)\n\n")
            for asset in complexity["unique_assets"][:10]:
                f.write(f"- `{asset['name']}` (in {asset['directory']}, {asset['count_in_directory']} total)\n")
            f.write("\n")
            
            # Usage Tips
            f.write("## 💡 Usage Tips\n\n")
            f.write("1. **Start with directories**: Use the search guide to find relevant directories\n")
            f.write("2. **Filter by format**: Choose format based on your needs (i4 for text, rgba32 for quality)\n")
            f.write("3. **Check relationships**: Look for paired .c/.h files or similar named assets\n")
            f.write("4. **Consider complexity**: Simple assets are easier to work with\n")
            f.write("5. **Use references**: Assets with code references are actively used\n")
            f.write("6. **Language matters**: JPN/ENG indicators show localization differences\n\n")
            
            # Technical Details
            f.write("## 🔧 Technical Details\n\n")
            f.write("### Format Specifications\n\n")
            f.write("- **i4**: 4-bit intensity, 16 colors, 1:2 compression\n")
            f.write("- **ia8**: 8-bit intensity + alpha, 256 colors, good for UI\n")
            f.write("- **ci8**: 8-bit color index, 256 colors, detailed textures\n")
            f.write("- **rgba16**: 16-bit RGBA, 65K colors, high quality\n")
            f.write("- **rgba32**: 32-bit RGBA, 16M colors, highest quality\n")
            f.write("- **i8**: 8-bit intensity, 256 grayscale levels\n\n")
            
            f.write("### Directory Structure\n\n")
            f.write("Assets are organized by function:\n")
            f.write("- `*_static`: UI elements and interface components\n")
            f.write("- `*_jpn`: Japanese localization assets\n")
            f.write("- `*_nes`: English/NES-style assets\n")
            f.write("- `backgrounds`: Environmental textures\n")
            f.write("- `skyboxes`: Sky textures for outdoor scenes\n")
            f.write("- `kanji`: Japanese text rendering\n")
        
        print(f"Generated enhanced asset analysis: {report_path}")
    
    def run(self):
        """Run the enhanced asset analysis."""
        print("Starting Enhanced Asset Analysis")
        print("=" * 40)
        
        if not self.asset_inventory:
            print("No asset inventory found. Please run Phase 1 & 2 first.")
            return
        
        self.generate_enhanced_report()
        print("Enhanced asset analysis complete!")

def main():
    """Main entry point."""
    analyzer = EnhancedAssetAnalyzer()
    analyzer.run()

if __name__ == "__main__":
    main() 