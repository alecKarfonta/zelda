#!/usr/bin/env python3
"""
Zelda OoT Asset Documentation Generator
Implements Phase 1 and 2 of the asset documentation plan.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from PIL import Image
import hashlib

class AssetDocumentationGenerator:
    def __init__(self, project_root: str = "oot"):
        self.project_root = Path(project_root)
        self.assets_dir = self.project_root / "extracted" / "ntsc-1.2" / "assets" / "textures"
        self.src_dir = self.project_root / "src"
        self.output_dir = Path("asset_documentation")
        self.output_dir.mkdir(exist_ok=True)
        
    def get_image_metadata(self, path: Path) -> Dict[str, Any]:
        """Extract metadata from image files."""
        try:
            with Image.open(path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "mode": img.mode,
                    "format": img.format,
                    "size_bytes": os.path.getsize(path)
                }
        except Exception as e:
            return {"error": str(e), "size_bytes": os.path.getsize(path)}
    
    def get_file_metadata(self, path: Path) -> Dict[str, Any]:
        """Extract basic file metadata."""
        stat = path.stat()
        return {
            "size_bytes": stat.st_size,
            "modified_time": stat.st_mtime,
            "file_type": path.suffix.lower(),
            "is_image": path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
        }
    
    def detect_format_from_filename(self, filename: str) -> Optional[str]:
        """Detect texture format from filename patterns."""
        # Common OoT texture format patterns
        format_patterns = {
            'ia8': r'ia8',
            'rgba16': r'rgba16',
            'rgba32': r'rgba32',
            'ci4': r'ci4',
            'ci8': r'ci8',
            'i4': r'i4',
            'i8': r'i8',
        }
        
        for format_name, pattern in format_patterns.items():
            if re.search(pattern, filename.lower()):
                return format_name
        return None
    
    def find_references_python(self, asset_name: str, search_dirs: List[Path]) -> List[Dict[str, Any]]:
        """Find references to an asset in the codebase using Python file searching."""
        references = []
        
        # Search patterns for different types of references
        search_patterns = [
            f'"{asset_name}"',  # String literals
            f"'{asset_name}'",  # String literals
            asset_name,  # Direct references
        ]
        
        # File extensions to search in
        search_extensions = {'.c', '.h', '.cpp', '.hpp', '.asm', '.s'}
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
                
            print(f"Searching in {search_dir}...")
            
            # Walk through all files in the search directory
            for file_path in search_dir.rglob('*'):
                if not file_path.is_file():
                    continue
                    
                # Only search in relevant file types
                if file_path.suffix.lower() not in search_extensions:
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    for pattern in search_patterns:
                        # Use regex to find matches
                        matches = re.finditer(re.escape(pattern), content)
                        for match in matches:
                            # Get line number
                            line_num = content[:match.start()].count('\n') + 1
                            
                            # Get the line content
                            lines = content.split('\n')
                            if 0 <= line_num - 1 < len(lines):
                                line_content = lines[line_num - 1].strip()
                            else:
                                line_content = ""
                            
                            references.append({
                                "file": str(file_path.relative_to(self.project_root)),
                                "line": line_num,
                                "line_text": line_content,
                                "pattern": pattern
                            })
                            
                except Exception as e:
                    # Skip files that can't be read
                    continue
        
        return references
    
    def walk_assets(self) -> List[Dict[str, Any]]:
        """Recursively walk through all assets and collect metadata."""
        assets = []
        
        if not self.assets_dir.exists():
            print(f"Assets directory not found: {self.assets_dir}")
            return assets
        
        print(f"Scanning assets in: {self.assets_dir}")
        
        for file_path in self.assets_dir.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(self.assets_dir)
                
                # Get basic metadata
                metadata = {
                    "path": str(relative_path),
                    "name": file_path.name,
                    "full_path": str(file_path),
                    "directory": str(relative_path.parent),
                }
                
                # Add file metadata
                metadata.update(self.get_file_metadata(file_path))
                
                # Detect format from filename
                detected_format = self.detect_format_from_filename(file_path.name)
                if detected_format:
                    metadata["detected_format"] = detected_format
                
                # Add image-specific metadata
                if metadata["is_image"]:
                    image_meta = self.get_image_metadata(file_path)
                    metadata.update(image_meta)
                
                # Calculate file hash for change detection
                try:
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                    metadata["hash"] = file_hash
                except Exception as e:
                    metadata["hash_error"] = str(e)
                
                assets.append(metadata)
                
                if len(assets) % 100 == 0:
                    print(f"Processed {len(assets)} assets...")
        
        print(f"Total assets found: {len(assets)}")
        return assets
    
    def analyze_references(self, assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze references for each asset."""
        print("Analyzing references...")
        
        search_dirs = [
            self.src_dir,
            self.project_root / "extracted" / "ntsc-1.2" / "assets",
            self.project_root / "include"
        ]
        
        # Only analyze a subset of assets for performance (first 100)
        assets_to_analyze = assets[:100]
        print(f"Analyzing references for first {len(assets_to_analyze)} assets...")
        
        for i, asset in enumerate(assets_to_analyze):
            if i % 10 == 0:
                print(f"Analyzing references for asset {i+1}/{len(assets_to_analyze)}...")
            
            # Find references
            references = self.find_references_python(asset["name"], search_dirs)
            asset["references"] = references
            asset["reference_count"] = len(references)
        
        # For remaining assets, just set empty references
        for asset in assets[len(assets_to_analyze):]:
            asset["references"] = []
            asset["reference_count"] = 0
        
        return assets
    
    def generate_summary_stats(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics about the assets."""
        stats = {
            "total_assets": len(assets),
            "total_size_bytes": sum(asset.get("size_bytes", 0) for asset in assets),
            "file_types": {},
            "formats": {},
            "directories": {},
            "images": 0,
            "non_images": 0,
            "assets_with_references": 0,
            "total_references": 0
        }
        
        for asset in assets:
            # File type stats
            file_type = asset.get("file_type", "unknown")
            stats["file_types"][file_type] = stats["file_types"].get(file_type, 0) + 1
            
            # Format stats
            if "detected_format" in asset:
                format_name = asset["detected_format"]
                stats["formats"][format_name] = stats["formats"].get(format_name, 0) + 1
            
            # Directory stats
            directory = asset.get("directory", "root")
            stats["directories"][directory] = stats["directories"].get(directory, 0) + 1
            
            # Image vs non-image
            if asset.get("is_image", False):
                stats["images"] += 1
            else:
                stats["non_images"] += 1
            
            # Reference stats
            ref_count = asset.get("reference_count", 0)
            if ref_count > 0:
                stats["assets_with_references"] += 1
                stats["total_references"] += ref_count
        
        return stats
    
    def save_documentation(self, assets: List[Dict[str, Any]], stats: Dict[str, Any]):
        """Save the documentation to files."""
        # Save full asset inventory
        inventory_path = self.output_dir / "asset_inventory.json"
        with open(inventory_path, 'w') as f:
            json.dump(assets, f, indent=2)
        print(f"Saved asset inventory to: {inventory_path}")
        
        # Save summary statistics
        stats_path = self.output_dir / "asset_stats.json"
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"Saved asset statistics to: {stats_path}")
        
        # Generate markdown report
        self.generate_markdown_report(assets, stats)
    
    def generate_markdown_report(self, assets: List[Dict[str, Any]], stats: Dict[str, Any]):
        """Generate a human-readable markdown report."""
        report_path = self.output_dir / "asset_report.md"
        
        with open(report_path, 'w') as f:
            f.write("# Zelda OoT Asset Documentation Report\n\n")
            f.write(f"Generated on: {Path().cwd()}\n\n")
            
            # Summary statistics
            f.write("## Summary Statistics\n\n")
            f.write(f"- **Total Assets**: {stats['total_assets']:,}\n")
            f.write(f"- **Total Size**: {stats['total_size_bytes']:,} bytes ({stats['total_size_bytes'] / 1024 / 1024:.2f} MB)\n")
            f.write(f"- **Images**: {stats['images']:,}\n")
            f.write(f"- **Non-Images**: {stats['non_images']:,}\n")
            f.write(f"- **Assets with References**: {stats['assets_with_references']:,}\n")
            f.write(f"- **Total References**: {stats['total_references']:,}\n\n")
            
            # File type breakdown
            f.write("## File Type Breakdown\n\n")
            for file_type, count in sorted(stats["file_types"].items(), key=lambda x: x[1], reverse=True):
                f.write(f"- **{file_type}**: {count:,}\n")
            f.write("\n")
            
            # Format breakdown
            if stats["formats"]:
                f.write("## Detected Format Breakdown\n\n")
                for format_name, count in sorted(stats["formats"].items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- **{format_name}**: {count:,}\n")
                f.write("\n")
            
            # Directory breakdown
            f.write("## Directory Breakdown\n\n")
            for directory, count in sorted(stats["directories"].items(), key=lambda x: x[1], reverse=True):
                f.write(f"- **{directory}**: {count:,}\n")
            f.write("\n")
            
            # Assets with most references
            assets_with_refs = [a for a in assets if a.get("reference_count", 0) > 0]
            if assets_with_refs:
                f.write("## Assets with Most References\n\n")
                sorted_assets = sorted(assets_with_refs, key=lambda x: x.get("reference_count", 0), reverse=True)
                for asset in sorted_assets[:20]:  # Top 20
                    f.write(f"- **{asset['name']}** ({asset['path']}): {asset['reference_count']} references\n")
                f.write("\n")
            
            # Large assets
            large_assets = sorted(assets, key=lambda x: x.get("size_bytes", 0), reverse=True)
            f.write("## Largest Assets\n\n")
            for asset in large_assets[:20]:  # Top 20
                size_mb = asset.get("size_bytes", 0) / 1024 / 1024
                f.write(f"- **{asset['name']}** ({asset['path']}): {size_mb:.2f} MB\n")
            f.write("\n")
        
        print(f"Generated markdown report: {report_path}")
    
    def run(self):
        """Execute the complete asset documentation generation process."""
        print("Starting Zelda OoT Asset Documentation Generation")
        print("=" * 50)
        
        # Phase 1: Asset Inventory and Metadata Extraction
        print("\nPhase 1: Asset Inventory and Metadata Extraction")
        print("-" * 40)
        assets = self.walk_assets()
        
        if not assets:
            print("No assets found. Exiting.")
            return
        
        # Phase 2: Reference Analysis
        print("\nPhase 2: Reference Analysis")
        print("-" * 40)
        assets = self.analyze_references(assets)
        
        # Generate summary statistics
        print("\nGenerating Summary Statistics")
        print("-" * 40)
        stats = self.generate_summary_stats(assets)
        
        # Save documentation
        print("\nSaving Documentation")
        print("-" * 40)
        self.save_documentation(assets, stats)
        
        print("\nAsset documentation generation complete!")
        print(f"Output files saved in: {self.output_dir}")

def main():
    """Main entry point."""
    generator = AssetDocumentationGenerator()
    generator.run()

if __name__ == "__main__":
    main() 