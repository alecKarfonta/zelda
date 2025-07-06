#!/usr/bin/env python3
"""
Demonstrate GraphRAG capabilities with Zelda assets
"""

import requests
import json

def demonstrate_capabilities():
    """Demonstrate what GraphRAG is actually doing with our Zelda assets."""
    base_url = "http://localhost:8000"
    
    print("Zelda OoT Asset GraphRAG Capabilities Demonstration")
    print("=" * 60)
    
    # Test queries that showcase different capabilities
    test_cases = [
        {
            "query": "Find Japanese kanji character assets",
            "description": "Demonstrates entity extraction and semantic understanding"
        },
        {
            "query": "What assets are used for text rendering?",
            "description": "Demonstrates concept understanding and relationship discovery"
        },
        {
            "query": "Find assets with compressed formats",
            "description": "Demonstrates technical attribute understanding"
        },
        {
            "query": "What are the different asset directories?",
            "description": "Demonstrates organizational structure understanding"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        description = test_case["description"]
        
        print(f"\n{'='*80}")
        print(f"Test {i}: {query}")
        print(f"Purpose: {description}")
        print(f"{'='*80}")
        
        try:
            # Test advanced search
            search_request = {
                "query": query,
                "search_type": "hybrid",
                "top_k": 5,
                "domain": "zelda_oot_assets"
            }
            
            response = requests.post(
                f"{base_url}/search-advanced",
                json=search_request,
                timeout=30
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"✅ Search successful")
                print(f"📋 Found {len(results.get('results', []))} results")
                
                # Show the AI-generated answer
                if "answer" in results:
                    print(f"\n🤖 AI Answer:")
                    print(f"{results['answer']}")
                
                # Show query analysis
                if "query_analysis" in results:
                    analysis = results["query_analysis"]
                    print(f"\n📊 Query Analysis:")
                    print(f"   Intent: {analysis.get('intent', {}).get('primary_intent', 'Unknown')}")
                    print(f"   Confidence: {analysis.get('intent', {}).get('confidence', 'Unknown')}")
                    
                    if "entities" in analysis:
                        entities = analysis["entities"]
                        print(f"   Entities found: {len(entities)}")
                        for entity in entities:
                            print(f"     - {entity.get('name', 'Unknown')} ({entity.get('entity_type', 'Unknown')})")
                
                # Show results breakdown
                print(f"\n📋 Results Breakdown:")
                graph_results = 0
                document_results = 0
                
                for j, result in enumerate(results.get('results', []), 1):
                    source = result.get('source', 'Unknown')
                    score = result.get('score', 0)
                    content = result.get('content', '')[:100] + "..." if len(result.get('content', '')) > 100 else result.get('content', '')
                    
                    if source == "graph":
                        graph_results += 1
                        print(f"   {j}. [GRAPH] Score: {score:.3f} - {content}")
                    else:
                        document_results += 1
                        print(f"   {j}. [DOC] Score: {score:.3f} - {content}")
                
                print(f"\n📊 Summary:")
                print(f"   Graph entities: {graph_results}")
                print(f"   Document chunks: {document_results}")
                print(f"   Total results: {len(results.get('results', []))}")
                
            else:
                print(f"❌ Search failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Query failed: {e}")
    
    # Test different search types and compare
    print(f"\n{'='*80}")
    print("Comparing Search Types")
    print(f"{'='*80}")
    
    test_query = "Find Japanese kanji character assets"
    search_types = ["hybrid", "vector", "graph", "keyword"]
    
    for search_type in search_types:
        print(f"\n--- {search_type.upper()} Search ---")
        
        try:
            search_request = {
                "query": test_query,
                "search_type": search_type,
                "top_k": 3,
                "domain": "zelda_oot_assets"
            }
            
            response = requests.post(
                f"{base_url}/search-advanced",
                json=search_request,
                timeout=30
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"✅ {search_type} search successful")
                print(f"📋 Found {len(results.get('results', []))} results")
                
                # Count result types
                graph_count = sum(1 for r in results.get('results', []) if r.get('source') == 'graph')
                doc_count = len(results.get('results', [])) - graph_count
                
                print(f"   Graph entities: {graph_count}")
                print(f"   Document chunks: {doc_count}")
                
                # Show top result
                if results.get('results'):
                    top_result = results['results'][0]
                    print(f"   Top result: {top_result.get('content', '')[:50]}...")
            else:
                print(f"❌ {search_type} search failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {search_type} search failed: {e}")
    
    # Show knowledge graph statistics
    print(f"\n{'='*80}")
    print("Knowledge Graph Statistics")
    print(f"{'='*80}")
    
    try:
        stats_response = requests.get(f"{base_url}/knowledge-graph/stats", timeout=10)
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"✅ Graph statistics retrieved")
            print(f"📊 Nodes: {stats.get('nodes', 0)}")
            print(f"📊 Edges: {stats.get('edges', 0)}")
            print(f"📊 Density: {stats.get('density', 0):.4f}")
            print(f"📊 Connected components: {stats.get('connected_components', 0)}")
            print(f"📊 Average clustering: {stats.get('average_clustering', 0):.4f}")
        else:
            print(f"❌ Statistics failed: {stats_response.status_code}")
            
    except Exception as e:
        print(f"❌ Statistics failed: {e}")

if __name__ == "__main__":
    demonstrate_capabilities() 