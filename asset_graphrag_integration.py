#!/usr/bin/env python3
"""
Zelda OoT Asset GraphRAG Integration
Advanced asset search and tagging system using GraphRAG technology
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from datetime import datetime

# Add GraphRAG backend to path
sys.path.append(str(Path("../graphrag/backend")))

try:
    from entity_extractor import EntityExtractor
    from knowledge_graph_builder import KnowledgeGraphBuilder
    from hybrid_retriever import HybridRetriever
    from query_processor import QueryProcessor
    GRAPHRAG_AVAILABLE = True
except ImportError:
    print("GraphRAG backend not available. Install from ../graphrag/backend")
    GRAPHRAG_AVAILABLE = False

class AssetGraphRAGSearch:
    def __init__(self, project_root: str = "oot"):
        self.project_root = Path(project_root)
        self.output_dir = Path("asset_documentation")
        self.graphrag_dir = Path("../graphrag")
        
        # Load existing asset inventory
        self.asset_inventory = self.load_asset_inventory()
        
        # GraphRAG components
        self.entity_extractor = None
        self.graph_builder = None
        self.hybrid_retriever = None
        self.query_processor = None
        
        # Asset-specific entity types
        self.asset_entity_types = {
            "ASSET": "Game asset files (textures, models, sounds)",
            "TEXTURE": "Image/texture assets",
            "UI_ELEMENT": "User interface components",
            "BACKGROUND": "Environmental background textures",
            "FONT": "Text rendering assets",
            "ICON": "Icon and symbol assets",
            "MAP": "Map and navigation assets",
            "LOCATION": "Game location assets",
            "ITEM": "Game item assets",
            "FORMAT": "Asset format specifications",
            "DIRECTORY": "Asset organization directories",
            "LANGUAGE": "Localization assets (JPN/ENG)",
            "QUALITY": "Asset quality levels",
            "SIZE": "Asset size categories"
        }
        
        # Asset-specific relationship types
        self.asset_relationship_types = {
            "CONTAINS": "Directory contains assets",
            "USES_FORMAT": "Asset uses specific format",
            "SIMILAR_TO": "Assets are similar",
            "REFERENCES": "Code references asset",
            "LOCALIZED_AS": "Asset has language variant",
            "PART_OF": "Asset is part of larger set",
            "REPLACES": "Asset replaces another",
            "DEPENDS_ON": "Asset depends on another",
            "GENERATED_FROM": "Asset generated from source",
            "OPTIMIZED_FOR": "Asset optimized for specific use"
        }
        
        if GRAPHRAG_AVAILABLE:
            self.initialize_graphrag()
    
    def load_asset_inventory(self) -> List[Dict[str, Any]]:
        """Load the existing asset inventory."""
        inventory_path = self.output_dir / "asset_inventory.json"
        if inventory_path.exists():
            with open(inventory_path, 'r') as f:
                return json.load(f)
        else:
            print("Asset inventory not found. Please run Phase 1 & 2 first.")
            return []
    
    def initialize_graphrag(self):
        """Initialize GraphRAG components."""
        try:
            # Initialize with asset-specific configurations
            self.entity_extractor = EntityExtractor(
                entity_types=self.asset_entity_types,
                relationship_types=self.asset_relationship_types
            )
            
            self.graph_builder = KnowledgeGraphBuilder()
            self.hybrid_retriever = HybridRetriever()
            self.query_processor = QueryProcessor()
            
            print("GraphRAG components initialized successfully")
        except Exception as e:
            print(f"Failed to initialize GraphRAG: {e}")
            GRAPHRAG_AVAILABLE = False
    
    def create_asset_documents(self) -> List[Dict[str, Any]]:
        """Convert asset inventory to documents for GraphRAG processing."""
        documents = []
        
        for asset in self.asset_inventory:
            # Create rich document content for each asset
            content = self.generate_asset_document_content(asset)
            
            document = {
                "id": f"asset_{asset['name']}",
                "content": content,
                "metadata": {
                    "asset_name": asset["name"],
                    "asset_path": asset["path"],
                    "directory": asset["directory"],
                    "file_type": asset.get("file_type", ""),
                    "size_bytes": asset.get("size_bytes", 0),
                    "detected_format": asset.get("detected_format", ""),
                    "is_image": asset.get("is_image", False),
                    "reference_count": asset.get("reference_count", 0),
                    "hash": asset.get("hash", "")
                }
            }
            documents.append(document)
        
        return documents
    
    def generate_asset_document_content(self, asset: Dict[str, Any]) -> str:
        """Generate rich document content for an asset."""
        content_parts = []
        
        # Basic asset information
        content_parts.append(f"Asset: {asset['name']}")
        content_parts.append(f"Path: {asset['path']}")
        content_parts.append(f"Directory: {asset['directory']}")
        
        # File characteristics
        if asset.get("is_image", False):
            content_parts.append("Type: Image texture")
            if "width" in asset and "height" in asset:
                content_parts.append(f"Dimensions: {asset['width']}x{asset['height']}")
        else:
            content_parts.append("Type: Code/data file")
        
        # Format information
        if asset.get("detected_format"):
            content_parts.append(f"Format: {asset['detected_format']}")
            content_parts.append(self.get_format_description(asset['detected_format']))
        
        # Size information
        size_mb = asset.get("size_bytes", 0) / 1024 / 1024
        content_parts.append(f"Size: {size_mb:.3f} MB")
        
        # Directory analysis
        content_parts.append(self.get_directory_description(asset["directory"]))
        
        # Reference information
        if asset.get("reference_count", 0) > 0:
            content_parts.append(f"Referenced in {asset['reference_count']} code locations")
        
        # Language indicators
        if "JPN" in asset["name"]:
            content_parts.append("Language: Japanese localization")
        elif "ENG" in asset["name"]:
            content_parts.append("Language: English localization")
        
        # Filename analysis
        content_parts.append(self.analyze_filename_patterns(asset["name"]))
        
        return "\n".join(content_parts)
    
    def get_format_description(self, format_name: str) -> str:
        """Get detailed description of asset format."""
        format_descriptions = {
            "i4": "4-bit intensity format, 16 colors, highly compressed, good for text and simple graphics",
            "ia8": "8-bit intensity with alpha, 256 colors, good for UI elements with transparency",
            "ci8": "8-bit color index, 256 colors, good for detailed textures with color palette",
            "rgba16": "16-bit RGBA, 65K colors, high quality for detailed images",
            "rgba32": "32-bit RGBA, 16M colors, highest quality, largest file size",
            "i8": "8-bit intensity, 256 grayscale levels, good for monochrome images"
        }
        return format_descriptions.get(format_name, f"Format: {format_name}")
    
    def get_directory_description(self, directory: str) -> str:
        """Get description of asset directory purpose."""
        directory_descriptions = {
            "kanji": "Japanese character rendering assets, contains thousands of kanji characters",
            "backgrounds": "Environmental background textures for game scenes",
            "skyboxes": "Sky textures for outdoor environments",
            "icon_item_static": "Static item icons for user interface",
            "icon_item_24_static": "24x24 pixel item icons for quest tracking",
            "map_i_static": "Map interface elements and minimap components",
            "title_static": "Title screen and menu interface elements",
            "nes_font_static": "NES-style font rendering for retro text display",
            "message_static": "Message and dialogue text rendering",
            "nintendo_rogo_static": "Nintendo branding and logo assets",
            "item_name_static": "Item name text rendering",
            "map_name_static": "Location name text rendering",
            "do_action_static": "Action button and prompt interface elements",
            "parameter_static": "Character stats and parameter display elements"
        }
        return directory_descriptions.get(directory, f"Directory: {directory}")
    
    def analyze_filename_patterns(self, filename: str) -> str:
        """Analyze filename patterns and provide insights."""
        patterns = []
        
        if filename.startswith("g"):
            patterns.append("Standard game asset prefix")
        
        if "Tex" in filename:
            patterns.append("Texture asset")
        
        if "Msg" in filename:
            patterns.append("Message-related asset")
        
        if "Kanji" in filename:
            patterns.append("Japanese character asset")
        
        if "Item" in filename:
            patterns.append("Item-related asset")
        
        if "Map" in filename:
            patterns.append("Map-related asset")
        
        if "Background" in filename or "Bg" in filename:
            patterns.append("Background texture")
        
        if "Icon" in filename:
            patterns.append("Icon asset")
        
        if "Button" in filename:
            patterns.append("Button interface element")
        
        if "Logo" in filename:
            patterns.append("Logo or branding asset")
        
        return f"Filename patterns: {', '.join(patterns)}" if patterns else "Standard asset naming"
    
    def build_asset_knowledge_graph(self):
        """Build knowledge graph from asset inventory."""
        if not GRAPHRAG_AVAILABLE:
            print("GraphRAG not available. Cannot build knowledge graph.")
            return
        
        print("Building asset knowledge graph...")
        
        # Convert assets to documents
        documents = self.create_asset_documents()
        print(f"Created {len(documents)} asset documents")
        
        # Process documents through GraphRAG pipeline
        try:
            # Extract entities and relationships
            entities_relationships = []
            for doc in documents:
                extracted = self.entity_extractor.extract_entities_and_relationships(doc["content"])
                entities_relationships.append({
                    "document_id": doc["id"],
                    "entities": extracted["entities"],
                    "relationships": extracted["relationships"],
                    "metadata": doc["metadata"]
                })
            
            # Build knowledge graph
            self.graph_builder.build_graph(entities_relationships)
            print("Asset knowledge graph built successfully")
            
        except Exception as e:
            print(f"Error building knowledge graph: {e}")
    
    def search_assets(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search assets using GraphRAG hybrid search."""
        if not GRAPHRAG_AVAILABLE:
            return self.fallback_search(query, max_results)
        
        try:
            # Use hybrid retriever for search
            results = self.hybrid_retriever.search(query, max_results=max_results)
            
            # Process and format results
            formatted_results = []
            for result in results:
                asset_info = self.get_asset_by_id(result["document_id"])
                if asset_info:
                    formatted_results.append({
                        "asset": asset_info,
                        "relevance_score": result.get("score", 0),
                        "matched_entities": result.get("entities", []),
                        "matched_relationships": result.get("relationships", [])
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"GraphRAG search failed: {e}")
            return self.fallback_search(query, max_results)
    
    def fallback_search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Fallback search using simple text matching."""
        query_lower = query.lower()
        results = []
        
        for asset in self.asset_inventory:
            score = 0
            
            # Check asset name
            if query_lower in asset["name"].lower():
                score += 10
            
            # Check directory
            if query_lower in asset["directory"].lower():
                score += 5
            
            # Check format
            if asset.get("detected_format") and query_lower in asset["detected_format"].lower():
                score += 3
            
            # Check file type
            if asset.get("file_type") and query_lower in asset["file_type"].lower():
                score += 2
            
            if score > 0:
                results.append({
                    "asset": asset,
                    "relevance_score": score,
                    "matched_entities": [],
                    "matched_relationships": []
                })
        
        # Sort by score and limit results
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:max_results]
    
    def get_asset_by_id(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get asset information by GraphRAG document ID."""
        asset_name = asset_id.replace("asset_", "")
        for asset in self.asset_inventory:
            if asset["name"] == asset_name:
                return asset
        return None
    
    def generate_search_report(self, query: str, results: List[Dict[str, Any]]):
        """Generate a detailed search report."""
        report_path = self.output_dir / f"search_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_path, 'w') as f:
            f.write(f"# Asset Search Report\n\n")
            f.write(f"**Query**: {query}\n")
            f.write(f"**Search Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Results Found**: {len(results)}\n\n")
            
            f.write("## Search Results\n\n")
            
            for i, result in enumerate(results, 1):
                asset = result["asset"]
                f.write(f"### {i}. {asset['name']}\n\n")
                f.write(f"- **Path**: `{asset['path']}`\n")
                f.write(f"- **Directory**: `{asset['directory']}`\n")
                f.write(f"- **Type**: {'Image' if asset.get('is_image') else 'Code/Data'}\n")
                
                if asset.get("detected_format"):
                    f.write(f"- **Format**: {asset['detected_format']}\n")
                
                size_mb = asset.get("size_bytes", 0) / 1024 / 1024
                f.write(f"- **Size**: {size_mb:.3f} MB\n")
                
                if asset.get("reference_count", 0) > 0:
                    f.write(f"- **References**: {asset['reference_count']} code references\n")
                
                f.write(f"- **Relevance Score**: {result['relevance_score']:.2f}\n")
                
                if result.get("matched_entities"):
                    f.write(f"- **Matched Entities**: {', '.join(result['matched_entities'])}\n")
                
                if result.get("matched_relationships"):
                    f.write(f"- **Matched Relationships**: {', '.join(result['matched_relationships'])}\n")
                
                f.write("\n")
            
            # Summary statistics
            f.write("## Summary Statistics\n\n")
            
            by_directory = {}
            by_format = {}
            by_type = {"images": 0, "code": 0}
            
            for result in results:
                asset = result["asset"]
                
                # Directory stats
                directory = asset["directory"]
                by_directory[directory] = by_directory.get(directory, 0) + 1
                
                # Format stats
                if asset.get("detected_format"):
                    format_name = asset["detected_format"]
                    by_format[format_name] = by_format.get(format_name, 0) + 1
                
                # Type stats
                if asset.get("is_image"):
                    by_type["images"] += 1
                else:
                    by_type["code"] += 1
            
            f.write("### By Directory\n")
            for directory, count in sorted(by_directory.items(), key=lambda x: x[1], reverse=True):
                f.write(f"- `{directory}`: {count} assets\n")
            f.write("\n")
            
            f.write("### By Format\n")
            for format_name, count in sorted(by_format.items(), key=lambda x: x[1], reverse=True):
                f.write(f"- `{format_name}`: {count} assets\n")
            f.write("\n")
            
            f.write("### By Type\n")
            f.write(f"- Images: {by_type['images']} assets\n")
            f.write(f"- Code/Data: {by_type['code']} assets\n")
            f.write("\n")
        
        print(f"Search report generated: {report_path}")
        return report_path
    
    def interactive_search(self):
        """Interactive search interface."""
        print("Zelda OoT Asset GraphRAG Search System")
        print("=" * 50)
        print("Enter search queries to find related assets.")
        print("Type 'quit' to exit.\n")
        
        while True:
            try:
                query = input("Search query: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not query:
                    continue
                
                print(f"\nSearching for: '{query}'")
                results = self.search_assets(query, max_results=15)
                
                if results:
                    print(f"\nFound {len(results)} results:\n")
                    for i, result in enumerate(results, 1):
                        asset = result["asset"]
                        score = result["relevance_score"]
                        print(f"{i}. {asset['name']} (score: {score:.2f})")
                        print(f"   Path: {asset['path']}")
                        print(f"   Directory: {asset['directory']}")
                        if asset.get("detected_format"):
                            print(f"   Format: {asset['detected_format']}")
                        print()
                else:
                    print("No results found.\n")
                
                # Generate report
                report_path = self.generate_search_report(query, results)
                print(f"Detailed report saved to: {report_path}\n")
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}\n")
    
    def run(self):
        """Run the asset GraphRAG search system."""
        print("Initializing Zelda OoT Asset GraphRAG Search System")
        print("=" * 60)
        
        if not self.asset_inventory:
            print("No asset inventory found. Please run Phase 1 & 2 first.")
            return
        
        if GRAPHRAG_AVAILABLE:
            print("GraphRAG integration available")
            # Build knowledge graph
            self.build_asset_knowledge_graph()
        else:
            print("GraphRAG not available, using fallback search")
        
        # Start interactive search
        self.interactive_search()

def main():
    """Main entry point."""
    searcher = AssetGraphRAGSearch()
    searcher.run()

if __name__ == "__main__":
    main() 