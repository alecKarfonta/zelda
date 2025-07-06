#!/usr/bin/env python3
"""
Zelda OoT Asset GraphRAG Connector
Converts asset inventory into enriched documents for GraphRAG processing
"""

import json
import requests
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import subprocess
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AssetGraphRAGConnector:
    def __init__(self, graphrag_url: str = "http://localhost:8000"):
        self.graphrag_url = graphrag_url
        self.output_dir = Path("asset_documentation")
        self.asset_inventory_file = "asset_inventory.json"
        self.repo_docs_dir = "repo_documentation"
        
        # Load existing asset inventory
        self.asset_inventory = self.load_asset_inventory()
        
        # Asset-specific entity types for GraphRAG
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
            "SIZE": "Asset size categories",
            "GAME_SYSTEM": "Game system components",
            "RENDERING": "Graphics rendering assets",
            "AUDIO": "Sound and music assets",
            "ANIMATION": "Animation and motion assets"
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
            "OPTIMIZED_FOR": "Asset optimized for specific use",
            "RENDERS_IN": "Asset renders in specific context",
            "STORED_IN": "Asset stored in specific location",
            "ACCESSED_BY": "Asset accessed by specific system",
            "MODIFIED_BY": "Asset modified by specific process"
        }
        
        # Repository documentation sources
        self.repo_sources = [
            {
                "name": "z64-romhack-tutorials",
                "url": "https://github.com/Dragorn421/z64-romhack-tutorials",
                "description": "Romhacking-related tutorials for Zelda64 games",
                "category": "tutorials"
            },
            {
                "name": "Better-OoT", 
                "url": "https://github.com/fig02/Better-OoT",
                "description": "OoT ROM hack with quality-of-life changes optimized for speedruns",
                "category": "rom_hacks"
            },
            {
                "name": "triforce-percent",
                "url": "https://github.com/triforce-percent/triforce-percent", 
                "description": "Triforce percent tracking and documentation",
                "category": "tools"
            },
            {
                "name": "HackerOoT",
                "url": "https://github.com/HackerN64/HackerOoT",
                "description": "HackerN64 OoT hacking tools and documentation",
                "category": "tools"
            }
        ]
    
    def load_asset_inventory(self) -> List[Dict[str, Any]]:
        """Load the existing asset inventory."""
        inventory_path = self.output_dir / "asset_inventory.json"
        if inventory_path.exists():
            with open(inventory_path, 'r') as f:
                return json.load(f)
        else:
            logger.error("Asset inventory not found. Please run Phase 1 & 2 first.")
            return []
    
    def check_graphrag_status(self) -> bool:
        """Check if GraphRAG API is available."""
        try:
            response = requests.get(f"{self.graphrag_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"GraphRAG API not available: {e}")
            return False
    
    def create_enriched_asset_documents(self, sample_size: Optional[int] = None) -> List[Dict[str, Any]]:
        """Convert asset inventory into enriched documents for GraphRAG."""
        documents = []
        
        # Use sample if specified
        assets_to_process = self.asset_inventory
        if sample_size and sample_size < len(self.asset_inventory):
            # Take a representative sample
            import random
            random.seed(42)  # For reproducible results
            assets_to_process = random.sample(self.asset_inventory, sample_size)
            logger.info(f"Using sample of {sample_size} assets for testing")
        
        for asset in assets_to_process:
            # Create rich document content
            content = self.generate_enriched_asset_content(asset)
            
            # Create document metadata
            metadata = {
                "asset_name": asset["name"],
                "asset_path": asset["path"],
                "directory": asset["directory"],
                "file_type": asset.get("file_type", ""),
                "size_bytes": asset.get("size_bytes", 0),
                "detected_format": asset.get("detected_format", ""),
                "is_image": asset.get("is_image", False),
                "reference_count": asset.get("reference_count", 0),
                "hash": asset.get("hash", ""),
                "domain": "zelda_oot_assets",
                "asset_category": self.categorize_asset(asset),
                "technical_details": self.get_technical_details(asset)
            }
            
            # Add image dimensions if available
            if asset.get("is_image") and "width" in asset and "height" in asset:
                metadata["dimensions"] = f"{asset['width']}x{asset['height']}"
            
            document = {
                "content": content,
                "metadata": metadata,
                "filename": f"{asset['name']}.md"  # GraphRAG expects files
            }
            
            documents.append(document)
        
        return documents
    
    def generate_enriched_asset_content(self, asset: Dict[str, Any]) -> str:
        """Generate rich, contextual content for an asset."""
        content_parts = []
        
        # Asset identification
        content_parts.append(f"# Asset: {asset['name']}")
        content_parts.append(f"**Path**: `{asset['path']}`")
        content_parts.append(f"**Directory**: `{asset['directory']}`")
        content_parts.append("")
        
        # Asset type and characteristics
        if asset.get("is_image", False):
            content_parts.append("## Asset Type: Image Texture")
            if "width" in asset and "height" in asset:
                content_parts.append(f"**Dimensions**: {asset['width']} × {asset['height']} pixels")
        else:
            content_parts.append("## Asset Type: Code/Data File")
        
        # Format information
        if asset.get("detected_format"):
            content_parts.append(f"**Format**: {asset['detected_format']}")
            content_parts.append(self.get_format_description(asset['detected_format']))
        
        # Size information
        size_mb = asset.get("size_bytes", 0) / 1024 / 1024
        content_parts.append(f"**Size**: {size_mb:.3f} MB")
        
        # Directory analysis
        content_parts.append("")
        content_parts.append("## Directory Context")
        content_parts.append(self.get_directory_description(asset["directory"]))
        
        # Usage information
        if asset.get("reference_count", 0) > 0:
            content_parts.append("")
            content_parts.append("## Code References")
            content_parts.append(f"This asset is referenced in {asset['reference_count']} code locations.")
        
        # Language indicators
        if "JPN" in asset["name"]:
            content_parts.append("**Language**: Japanese localization")
        elif "ENG" in asset["name"]:
            content_parts.append("**Language**: English localization")
        
        # Filename analysis
        content_parts.append("")
        content_parts.append("## Filename Analysis")
        content_parts.append(self.analyze_filename_patterns(asset["name"]))
        
        # Technical context
        content_parts.append("")
        content_parts.append("## Technical Context")
        content_parts.append(self.get_technical_context(asset))
        
        # Game context
        content_parts.append("")
        content_parts.append("## Game Context")
        content_parts.append(self.get_game_context(asset))
        
        return "\n".join(content_parts)
    
    def categorize_asset(self, asset: Dict[str, Any]) -> str:
        """Categorize asset based on its characteristics."""
        name = asset["name"].lower()
        directory = asset["directory"].lower()
        
        if "kanji" in directory or "kanji" in name:
            return "text_rendering"
        elif "background" in directory or "bg" in name:
            return "environment"
        elif "icon" in directory or "icon" in name:
            return "ui_elements"
        elif "map" in directory or "map" in name:
            return "navigation"
        elif "title" in directory or "title" in name:
            return "ui_elements"
        elif "font" in directory or "font" in name:
            return "text_rendering"
        elif "message" in directory or "msg" in name:
            return "text_rendering"
        elif "item" in directory or "item" in name:
            return "game_items"
        elif "button" in name or "action" in name:
            return "ui_elements"
        elif "logo" in name:
            return "branding"
        else:
            return "general"
    
    def get_technical_details(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Get technical details for the asset."""
        details = {
            "file_extension": Path(asset["name"]).suffix,
            "is_image": asset.get("is_image", False),
            "has_references": asset.get("reference_count", 0) > 0,
            "size_category": self.get_size_category(asset.get("size_bytes", 0))
        }
        
        if asset.get("is_image"):
            details["image_format"] = asset.get("detected_format", "unknown")
            if "width" in asset and "height" in asset:
                details["dimensions"] = f"{asset['width']}x{asset['height']}"
        
        return details
    
    def get_size_category(self, size_bytes: int) -> str:
        """Categorize asset by size."""
        if size_bytes < 1024:
            return "tiny"
        elif size_bytes < 1024 * 1024:
            return "small"
        elif size_bytes < 5 * 1024 * 1024:
            return "medium"
        else:
            return "large"
    
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
            "kanji": "Japanese character rendering assets, contains thousands of kanji characters for text display",
            "backgrounds": "Environmental background textures for game scenes and locations",
            "skyboxes": "Sky textures for outdoor environments and atmospheric effects",
            "icon_item_static": "Static item icons for user interface and inventory system",
            "icon_item_24_static": "24x24 pixel item icons for quest tracking and HUD elements",
            "map_i_static": "Map interface elements and minimap components for navigation",
            "title_static": "Title screen and menu interface elements for game startup",
            "nes_font_static": "NES-style font rendering for retro text display and UI",
            "message_static": "Message and dialogue text rendering for game communication",
            "nintendo_rogo_static": "Nintendo branding and logo assets for company identification",
            "item_name_static": "Item name text rendering for inventory and description systems",
            "map_name_static": "Location name text rendering for map and navigation systems",
            "do_action_static": "Action button and prompt interface elements for user interaction",
            "parameter_static": "Character stats and parameter display elements for status screens"
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
        
        if "Font" in filename:
            patterns.append("Font rendering asset")
        
        if "Title" in filename:
            patterns.append("Title screen asset")
        
        return f"Filename patterns: {', '.join(patterns)}" if patterns else "Standard asset naming"
    
    def get_technical_context(self, asset: Dict[str, Any]) -> str:
        """Get technical context for the asset."""
        context_parts = []
        
        # File system context
        context_parts.append(f"**File System**: Stored in `{asset['directory']}` directory")
        context_parts.append(f"**File Type**: {asset.get('file_type', 'Unknown')}")
        
        # Memory and performance context
        size_mb = asset.get("size_bytes", 0) / 1024 / 1024
        if size_mb > 1:
            context_parts.append(f"**Memory Impact**: Large asset ({size_mb:.1f} MB), may affect loading times")
        else:
            context_parts.append(f"**Memory Impact**: Small asset ({size_mb:.3f} MB), efficient loading")
        
        # Format optimization
        if asset.get("detected_format"):
            format_name = asset["detected_format"]
            if format_name in ["i4", "i8"]:
                context_parts.append("**Optimization**: Compressed format for memory efficiency")
            elif format_name in ["rgba16", "rgba32"]:
                context_parts.append("**Optimization**: High-quality format for visual fidelity")
        
        # Code integration
        if asset.get("reference_count", 0) > 0:
            context_parts.append(f"**Code Integration**: Referenced in {asset['reference_count']} code locations")
        else:
            context_parts.append("**Code Integration**: No direct code references found")
        
        return "\n".join(context_parts)
    
    def get_game_context(self, asset: Dict[str, Any]) -> str:
        """Get game context for the asset."""
        context_parts = []
        
        # Game system context
        directory = asset["directory"]
        if "kanji" in directory:
            context_parts.append("**Game System**: Japanese text rendering system")
            context_parts.append("**Usage**: Character dialogue, item names, location names")
        elif "background" in directory:
            context_parts.append("**Game System**: Environmental rendering system")
            context_parts.append("**Usage**: Scene backgrounds, atmospheric effects")
        elif "icon" in directory:
            context_parts.append("**Game System**: User interface system")
            context_parts.append("**Usage**: Inventory icons, quest markers, HUD elements")
        elif "map" in directory:
            context_parts.append("**Game System**: Navigation and mapping system")
            context_parts.append("**Usage**: Minimap, location markers, navigation aids")
        elif "title" in directory:
            context_parts.append("**Game System**: Menu and interface system")
            context_parts.append("**Usage**: Title screen, menu elements, branding")
        elif "font" in directory:
            context_parts.append("**Game System**: Text rendering system")
            context_parts.append("**Usage**: All text display in the game")
        else:
            context_parts.append("**Game System**: General asset system")
            context_parts.append("**Usage**: Various game functionality")
        
        # Localization context
        if "JPN" in asset["name"]:
            context_parts.append("**Localization**: Japanese version specific")
        elif "ENG" in asset["name"]:
            context_parts.append("**Localization**: English version specific")
        else:
            context_parts.append("**Localization**: Language-neutral asset")
        
        return "\n".join(context_parts)
    
    def create_temp_document_files(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Create temporary files for GraphRAG ingestion."""
        temp_files = []
        
        for doc in documents:
            # Create temporary file with .md extension (now supported by GraphRAG)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
                f.write(doc["content"])
                temp_files.append(f.name)
        
        return temp_files
    
    def ingest_assets_to_graphrag(self, domain: str = "zelda_oot_assets", batch_size: int = 50, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """Ingest asset documents into GraphRAG system in batches."""
        if not self.check_graphrag_status():
            raise Exception("GraphRAG API is not available")
        
        # Create enriched documents
        documents = self.create_enriched_asset_documents(sample_size=sample_size)
        logger.info(f"Created {len(documents)} enriched asset documents")
        
        # Process in batches
        total_documents = len(documents)
        total_batches = (total_documents + batch_size - 1) // batch_size
        all_results = {}
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, total_documents)
            batch_documents = documents[start_idx:end_idx]
            
            logger.info(f"Processing batch {batch_idx + 1}/{total_batches} ({len(batch_documents)} documents)")
            
            # Create temporary files for this batch
            temp_files = self.create_temp_document_files(batch_documents)
            
            try:
                # Prepare files for upload
                files = []
                for temp_file in temp_files:
                    with open(temp_file, 'rb') as f:
                        files.append(('files', (os.path.basename(temp_file), f.read(), 'text/markdown')))
                
                # Send to GraphRAG API with custom domain
                response = requests.post(
                    f"{self.graphrag_url}/ingest-documents",
                    files=files,
                    data={
                        'domain': domain,
                        'build_knowledge_graph': 'true'
                    },
                    timeout=300  # 5 minutes timeout for large documentation
                )
                
                if response.status_code == 200:
                    result = response.json()
                    all_results[f"batch_{batch_idx + 1}"] = result
                    logger.info(f"Successfully ingested batch {batch_idx + 1} ({len(batch_documents)} assets)")
                else:
                    raise Exception(f"GraphRAG ingestion failed for batch {batch_idx + 1}: {response.status_code} - {response.text}")
            
            except Exception as e:
                logger.error(f"Error ingesting batch {batch_idx + 1}: {e}")
                # Continue with next batch instead of failing completely
                continue
            
            finally:
                # Clean up temporary files
                for temp_file in temp_files:
                    try:
                        os.unlink(temp_file)
                    except:
                        pass
        
        logger.info(f"Successfully ingested {len(all_results)} batches into GraphRAG")
        return {
            "total_documents": total_documents,
            "total_batches": total_batches,
            "successful_batches": len(all_results),
            "batch_results": all_results
        }
    
    def search_assets_via_graphrag(self, query: str, top_k: int = 10, search_type: str = "hybrid") -> Dict[str, Any]:
        """Search assets using GraphRAG's advanced search capabilities."""
        if not self.check_graphrag_status():
            raise Exception("GraphRAG API is not available")
        
        # Use advanced search endpoint with custom domain
        search_request = {
            "query": query,
            "search_type": search_type,  # "hybrid", "vector", "graph", "keyword"
            "top_k": top_k,
            "domain": "zelda_oot_assets",
            "filters": {
                "asset_category": None,  # No filtering by default
                "is_image": None,
                "size_category": None
            }
        }
        
        response = requests.post(
            f"{self.graphrag_url}/search-advanced",
            json=search_request,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"GraphRAG search failed: {response.status_code} - {response.text}")
    
    def enhanced_query_assets(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Use GraphRAG's enhanced query processing for complex asset queries."""
        if not self.check_graphrag_status():
            raise Exception("GraphRAG API is not available")
        
        # Use enhanced query endpoint
        query_request = {
            "query": query,
            "context": context or {}
        }
        
        response = requests.post(
            f"{self.graphrag_url}/api/enhanced-query",
            json=query_request,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Enhanced query failed: {response.status_code} - {response.text}")
    
    def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """Analyze query intent for better asset search."""
        if not self.check_graphrag_status():
            raise Exception("GraphRAG API is not available")
        
        response = requests.post(
            f"{self.graphrag_url}/api/analyze-query-intent",
            json={"query": query},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Query intent analysis failed: {response.status_code} - {response.text}")
    
    def get_graphrag_stats(self) -> Dict[str, Any]:
        """Get GraphRAG system statistics."""
        if not self.check_graphrag_status():
            raise Exception("GraphRAG API is not available")
        
        response = requests.get(f"{self.graphrag_url}/knowledge-graph/stats", timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get GraphRAG stats: {response.status_code}")
    
    def export_knowledge_graph(self) -> Dict[str, Any]:
        """Export the knowledge graph data."""
        if not self.check_graphrag_status():
            raise Exception("GraphRAG API is not available")
        
        response = requests.get(f"{self.graphrag_url}/knowledge-graph/export?format=json", timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to export knowledge graph: {response.status_code}")
    
    def run_interactive_search(self):
        """Run interactive search interface with advanced GraphRAG capabilities."""
        print("Zelda OoT Asset GraphRAG Search System")
        print("=" * 50)
        
        if not self.check_graphrag_status():
            print("❌ GraphRAG API is not available. Please start the GraphRAG service first.")
            return
        
        print("✅ GraphRAG API is available")
        
        # Check if assets are already ingested
        try:
            stats = self.get_graphrag_stats()
            print(f"📊 Current GraphRAG stats: {stats}")
        except Exception as e:
            print(f"⚠️  Could not get GraphRAG stats: {e}")
        
        print("\nAdvanced search with GraphRAG capabilities:")
        print("- Hybrid search (semantic + graph)")
        print("- Query intent analysis")
        print("- Enhanced query processing")
        print("Type 'quit' to exit.\n")
        
        while True:
            try:
                query = input("Search query: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not query:
                    continue
                
                print(f"\n🔍 Analyzing query: '{query}'")
                
                # Analyze query intent
                try:
                    intent_analysis = self.analyze_query_intent(query)
                    print(f"📊 Query intent: {intent_analysis.get('intent', 'Unknown')}")
                    print(f"📊 Complexity: {intent_analysis.get('complexity', 'Unknown')}")
                except Exception as e:
                    print(f"⚠️  Intent analysis failed: {e}")
                
                # Perform hybrid search
                print(f"\n🔍 Searching assets...")
                results = self.search_assets_via_graphrag(query, top_k=15, search_type="hybrid")
                
                if results and "results" in results:
                    print(f"\n📋 Found {len(results['results'])} results:\n")
                    for i, result in enumerate(results["results"], 1):
                        print(f"{i}. {result.get('document_name', 'Unknown')}")
                        print(f"   Score: {result.get('score', 0):.3f}")
                        if "metadata" in result:
                            metadata = result["metadata"]
                            if "asset_name" in metadata:
                                print(f"   Asset: {metadata['asset_name']}")
                            if "directory" in metadata:
                                print(f"   Directory: {metadata['directory']}")
                            if "asset_category" in metadata:
                                print(f"   Category: {metadata['asset_category']}")
                        print()
                    
                    # Offer enhanced query processing
                    if len(results["results"]) > 0:
                        enhance = input("Use enhanced query processing for detailed analysis? (y/n): ").strip().lower()
                        if enhance == 'y':
                            try:
                                enhanced_result = self.enhanced_query_assets(query)
                                print(f"\n🧠 Enhanced analysis: {enhanced_result}")
                            except Exception as e:
                                print(f"⚠️  Enhanced query failed: {e}")
                else:
                    print("No results found.\n")
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}\n")
    
    def demo_advanced_search(self):
        """Demonstrate advanced search capabilities with example queries."""
        print("Zelda OoT Asset GraphRAG Advanced Search Demo")
        print("=" * 50)
        
        if not self.check_graphrag_status():
            print("❌ GraphRAG API is not available.")
            return
        
        # Example queries that demonstrate different search capabilities
        demo_queries = [
            "Find all texture assets used in the user interface",
            "Show me assets related to Japanese text rendering",
            "What background textures are used in the game?",
            "Find large image files that might be high-resolution textures",
            "Show me assets that are referenced in the code",
            "Find all icon assets for the inventory system",
            "What assets are used for map and navigation?",
            "Find assets with specific formats like rgba16 or ci8"
        ]
        
        print("Demo queries that showcase GraphRAG capabilities:")
        for i, query in enumerate(demo_queries, 1):
            print(f"{i}. {query}")
        
        print("\nThese queries demonstrate:")
        print("- Semantic understanding of asset purposes")
        print("- Relationship discovery between assets")
        print("- Format and technical attribute filtering")
        print("- Cross-domain knowledge integration")
        
        choice = input("\nEnter query number to test (1-8), or 'all' to run all: ").strip()
        
        try:
            if choice.lower() == 'all':
                for i, query in enumerate(demo_queries, 1):
                    print(f"\n{'='*60}")
                    print(f"Demo Query {i}: {query}")
                    print(f"{'='*60}")
                    self._run_demo_query(query)
            elif choice.isdigit() and 1 <= int(choice) <= len(demo_queries):
                query = demo_queries[int(choice) - 1]
                print(f"\n{'='*60}")
                print(f"Demo Query: {query}")
                print(f"{'='*60}")
                self._run_demo_query(query)
            else:
                print("Invalid choice")
                
        except Exception as e:
            print(f"Demo failed: {e}")
    
    def _run_demo_query(self, query: str):
        """Run a single demo query with full analysis."""
        try:
            # Analyze query intent
            print(f"🔍 Analyzing query intent...")
            intent_analysis = self.analyze_query_intent(query)
            print(f"📊 Intent: {intent_analysis.get('intent', 'Unknown')}")
            print(f"📊 Complexity: {intent_analysis.get('complexity', 'Unknown')}")
            
            # Perform hybrid search
            print(f"\n🔍 Performing hybrid search...")
            results = self.search_assets_via_graphrag(query, top_k=10, search_type="hybrid")
            
            if results and "results" in results:
                print(f"\n📋 Found {len(results['results'])} results:")
                for i, result in enumerate(results["results"], 1):
                    metadata = result.get("metadata", {})
                    print(f"\n{i}. Asset: {metadata.get('asset_name', 'Unknown')}")
                    print(f"   Directory: {metadata.get('directory', 'Unknown')}")
                    print(f"   Category: {metadata.get('asset_category', 'Unknown')}")
                    print(f"   Score: {result.get('score', 0):.3f}")
                    if metadata.get('is_image'):
                        print(f"   Type: Image texture")
                        if 'dimensions' in metadata:
                            print(f"   Dimensions: {metadata['dimensions']}")
                    if metadata.get('detected_format'):
                        print(f"   Format: {metadata['detected_format']}")
                
                # Enhanced query processing
                print(f"\n🧠 Enhanced query analysis...")
                enhanced_result = self.enhanced_query_assets(query)
                print(f"Enhanced insights: {enhanced_result}")
                
            else:
                print("No results found.")
                
        except Exception as e:
            print(f"Query failed: {e}")
    
    def run(self):
        """Main execution method."""
        print("Zelda OoT Asset GraphRAG Connector")
        print("=" * 40)
        
        if not self.asset_inventory:
            print("❌ No asset inventory found. Please run Phase 1 & 2 first.")
            return
        
        print(f"✅ Loaded {len(self.asset_inventory)} assets from inventory")
        
        # Check GraphRAG availability
        if not self.check_graphrag_status():
            print("❌ GraphRAG API is not available.")
            print("Please start the GraphRAG service with: docker compose up -d")
            return
        
        print("✅ GraphRAG API is available")
        
        # Ask user what to do
        print("\nOptions:")
        print("1. Ingest all assets into GraphRAG (full dataset)")
        print("2. Ingest sample assets into GraphRAG (for testing)")
        print("3. Search assets via GraphRAG")
        print("4. Get GraphRAG statistics")
        print("5. Export knowledge graph")
        print("6. Interactive search")
        print("7. Demo advanced search")
        print("8. Ingest repository documentation")
        print("9. Search repository documentation")
        print("10. Get repository statistics")
        
        choice = input("\nEnter choice (1-10): ").strip()
        
        try:
            if choice == "1":
                print("\n🔄 Ingesting all assets into GraphRAG...")
                result = self.ingest_assets_to_graphrag()
                print(f"✅ Ingestion complete: {result}")
                
            elif choice == "2":
                sample_size = input("Enter sample size (default 50): ").strip()
                sample_size = int(sample_size) if sample_size.isdigit() else 50
                print(f"\n🔄 Ingesting {sample_size} sample assets into GraphRAG...")
                result = self.ingest_assets_to_graphrag(sample_size=sample_size, batch_size=25)
                print(f"✅ Sample ingestion complete: {result}")
                
            elif choice == "3":
                query = input("Enter search query: ").strip()
                if query:
                    print(f"\n🔍 Searching for: '{query}'")
                    results = self.search_assets_via_graphrag(query)
                    print(f"✅ Search results: {results}")
                
            elif choice == "4":
                stats = self.get_graphrag_stats()
                print(f"✅ GraphRAG stats: {stats}")
                
            elif choice == "5":
                graph_data = self.export_knowledge_graph()
                print(f"✅ Knowledge graph exported: {len(graph_data)} entities")
                
            elif choice == "6":
                self.run_interactive_search()
                
            elif choice == "7":
                self.demo_advanced_search()
                
            elif choice == "8":
                print("\n🔄 Ingesting repository documentation into GraphRAG...")
                result = self.ingest_repository_documentation()
                print(f"✅ Repository documentation ingestion complete: {result}")
                
            elif choice == "9":
                query = input("Enter search query for repository documentation: ").strip()
                if query:
                    print(f"\n🔍 Searching repository documentation for: '{query}'")
                    results = self.search_repository_documentation(query)
                    print(f"✅ Repository search results: {results}")
                
            elif choice == "10":
                stats = self.get_repository_stats()
                print(f"✅ Repository stats: {stats}")
                
            else:
                print("Invalid choice")
                
        except Exception as e:
            print(f"❌ Error: {e}")

    def pull_repository_documentation(self, repo_info: Dict[str, str]) -> List[Dict[str, Any]]:
        """Pull documentation files from a GitHub repository."""
        repo_name = repo_info["name"]
        repo_url = repo_info["url"]
        repo_description = repo_info["description"]
        repo_category = repo_info["category"]
        
        logger.info(f"Pulling documentation from {repo_name}...")
        
        # Create directory for this repo
        repo_dir = Path(self.repo_docs_dir) / repo_name
        repo_dir.mkdir(parents=True, exist_ok=True)
        
        # Clone the repository
        try:
            if repo_dir.exists() and (repo_dir / ".git").exists():
                # Update existing repo
                subprocess.run(["git", "pull"], cwd=repo_dir, check=True, capture_output=True)
                logger.info(f"Updated existing repository: {repo_name}")
            else:
                # Clone new repo
                subprocess.run(["git", "clone", repo_url, str(repo_dir)], check=True, capture_output=True)
                logger.info(f"Cloned repository: {repo_name}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone/update {repo_name}: {e}")
            return []
        
        # Find documentation files
        doc_files = []
        for ext in ['.md', '.txt', '.rst']:
            doc_files.extend(repo_dir.rglob(f"*{ext}"))
        
        # Filter out common non-documentation files
        excluded_patterns = [
            'LICENSE', 'README', 'CHANGELOG', 'CONTRIBUTING', 'CODE_OF_CONDUCT',
            'node_modules', '.git', '.github', 'dist', 'build', '__pycache__'
        ]
        
        filtered_files = []
        for file_path in doc_files:
            file_name = file_path.name.lower()
            if not any(pattern.lower() in file_name for pattern in excluded_patterns):
                # Check if it's not in excluded directories
                if not any(excluded in str(file_path) for excluded in ['node_modules', '.git', '.github', 'dist', 'build', '__pycache__']):
                    filtered_files.append(file_path)
        
        logger.info(f"Found {len(filtered_files)} documentation files in {repo_name}")
        
        # Process each documentation file
        documents = []
        for file_path in filtered_files:
            try:
                # Try UTF-8 first, fallback to other encodings if needed
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    # Try with error handling
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                
                # Skip empty files
                if not content.strip():
                    continue
                
                # Create enriched document with metadata
                doc_metadata = {
                    "source_repo": repo_name,
                    "source_url": repo_url,
                    "source_description": repo_description,
                    "source_category": repo_category,
                    "file_path": str(file_path.relative_to(repo_dir)),
                    "file_name": file_path.name,
                    "file_extension": file_path.suffix,
                    "file_size": file_path.stat().st_size,
                    "ingestion_date": datetime.now().isoformat(),
                    "content_type": "repository_documentation"
                }
                
                # Create enriched content
                enriched_content = self.create_enriched_repo_document_content(
                    content, file_path, doc_metadata
                )
                
                documents.append({
                    "content": enriched_content,
                    "metadata": doc_metadata,
                    "source": str(file_path)
                })
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue
        
        logger.info(f"Successfully processed {len(documents)} documents from {repo_name}")
        return documents

    def create_enriched_repo_document_content(self, content: str, file_path: Path, metadata: Dict[str, Any]) -> str:
        """Create enriched content for repository documentation."""
        lines = []
        
        # Header with source information
        lines.append(f"# Repository Documentation: {metadata['file_name']}")
        lines.append("")
        lines.append(f"**Source Repository**: {metadata['source_repo']}")
        lines.append(f"**Repository URL**: {metadata['source_url']}")
        lines.append(f"**Repository Description**: {metadata['source_description']}")
        lines.append(f"**Category**: {metadata['source_category']}")
        lines.append(f"**File Path**: {metadata['file_path']}")
        lines.append(f"**Ingestion Date**: {metadata['ingestion_date']}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Add the original content
        lines.append(content)
        
        return "\n".join(lines)

    def ingest_repository_documentation(self, domain: str = "zelda_oot_documentation", batch_size: int = 10) -> Dict[str, Any]:
        """Ingest documentation from all configured repositories into GraphRAG."""
        if not self.check_graphrag_status():
            raise Exception("GraphRAG API is not available")
        
        all_documents = []
        
        # Pull documentation from each repository
        for i, repo_info in enumerate(self.repo_sources, 1):
            print(f"Processing repository {i}/{len(self.repo_sources)}: {repo_info['name']}")
            try:
                documents = self.pull_repository_documentation(repo_info)
                all_documents.extend(documents)
                logger.info(f"Pulled {len(documents)} documents from {repo_info['name']}")
                print(f"✅ Successfully processed {len(documents)} documents from {repo_info['name']}")
            except Exception as e:
                logger.error(f"Failed to pull documentation from {repo_info['name']}: {e}")
                print(f"❌ Failed to process {repo_info['name']}: {e}")
                continue
        
        if not all_documents:
            raise Exception("No documentation files found in any repository")
        
        logger.info(f"Total documents to ingest: {len(all_documents)}")
        
        # Process in batches
        total_documents = len(all_documents)
        total_batches = (total_documents + batch_size - 1) // batch_size
        all_results = {}
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, total_documents)
            batch_documents = all_documents[start_idx:end_idx]
            
            logger.info(f"Processing batch {batch_idx + 1}/{total_batches} ({len(batch_documents)} documents)")
            
            # Create temporary files for this batch
            temp_files = self.create_temp_document_files(batch_documents)
            
            try:
                # Prepare files for upload
                files = []
                for temp_file in temp_files:
                    with open(temp_file, 'rb') as f:
                        files.append(('files', (os.path.basename(temp_file), f.read(), 'text/markdown')))
                
                # Send to GraphRAG API
                response = requests.post(
                    f"{self.graphrag_url}/ingest-documents",
                    files=files,
                    data={
                        'domain': domain,
                        'build_knowledge_graph': 'true'
                    },
                    timeout=120
                )
                
                if response.status_code == 200:
                    result = response.json()
                    all_results[f"batch_{batch_idx + 1}"] = result
                    logger.info(f"Successfully ingested batch {batch_idx + 1} ({len(batch_documents)} documents)")
                else:
                    raise Exception(f"GraphRAG ingestion failed for batch {batch_idx + 1}: {response.status_code} - {response.text}")
            
            except Exception as e:
                logger.error(f"Error ingesting batch {batch_idx + 1}: {e}")
                continue
            
            finally:
                # Clean up temporary files
                for temp_file in temp_files:
                    try:
                        os.unlink(temp_file)
                    except:
                        pass
        
        logger.info(f"Successfully ingested {len(all_results)} batches into GraphRAG")
        return {
            "total_documents": total_documents,
            "total_batches": total_batches,
            "successful_batches": len(all_results),
            "batch_results": all_results,
            "repositories_processed": len(self.repo_sources)
        }

    def search_repository_documentation(self, query: str, top_k: int = 10, search_type: str = "hybrid") -> Dict[str, Any]:
        """Search repository documentation using GraphRAG."""
        if not self.check_graphrag_status():
            raise Exception("GraphRAG API is not available")
        
        # Use advanced search endpoint with documentation domain
        search_request = {
            "query": query,
            "search_type": search_type,
            "top_k": top_k,
            "domain": "zelda_oot_documentation",
            "filters": {
                "content_type": "repository_documentation"
            }
        }
        
        response = requests.post(
            f"{self.graphrag_url}/search-advanced",
            json=search_request,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"GraphRAG search failed: {response.status_code} - {response.text}")

    def get_repository_stats(self) -> Dict[str, Any]:
        """Get statistics about repository documentation."""
        stats = {
            "configured_repositories": len(self.repo_sources),
            "repository_list": [repo["name"] for repo in self.repo_sources],
            "repo_docs_directory": self.repo_docs_dir
        }
        
        # Check if repo docs directory exists
        repo_docs_path = Path(self.repo_docs_dir)
        if repo_docs_path.exists():
            stats["local_repositories"] = [d.name for d in repo_docs_path.iterdir() if d.is_dir()]
        else:
            stats["local_repositories"] = []
        
        return stats

def main():
    """Main entry point."""
    connector = AssetGraphRAGConnector()
    connector.run()

if __name__ == "__main__":
    main() 