#!/usr/bin/env python3
"""
Test script for enhanced vector-based k-NN search in ROS Component Explorer.

This script demonstrates:
1. Loading ROS packages as dense vector embeddings
2. Converting user queries to vectors
3. Using k-NN similarity search to find relevant packages
4. Comparing vector search with traditional text search
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.vector_search_manager import VectorSearchManager
from NLP.nlp_search_engine import NLPSearchEngine
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_vector_search():
    """Test the enhanced vector search functionality."""
    
    print("🚀 Testing Enhanced Vector-Based k-NN Search for ROS Components")
    print("=" * 70)
    
    # Initialize data file
    project_root = Path(__file__).parent
    mobile_robot_file = project_root / "data" / "mobile_robot_components.ttl"
    legacy_data_file = project_root / "data" / "components_converted.ttl"
    
    # Find available data file
    ttl_file = None
    for candidate_file in [mobile_robot_file, legacy_data_file]:
        if candidate_file.exists():
            ttl_file = str(candidate_file)
            print(f"📁 Using data file: {ttl_file}")
            break
    
    if not ttl_file:
        print("❌ No data files found! Please ensure TTL files exist.")
        return
    
    try:
        print("\n🔧 Initializing Vector Search Manager...")
        vector_manager = VectorSearchManager(ttl_file)
        
        print("🔧 Initializing Enhanced NLP Search Engine...")
        nlp_engine = NLPSearchEngine(ttl_file)
        
        print("✅ All components initialized successfully!")
        
        # Get search statistics
        print("\n📊 Vector Search Statistics:")
        stats = vector_manager.get_search_stats()
        for key, value in stats.items():
            print(f"  • {key}: {value}")
        
        # Test queries
        test_queries = [
            "What is the best SLAM package for outdoor robots with 3D LiDAR?",
            "I need navigation components for indoor mobile robots",
            "Find localization packages that work with GPS and IMU",
            "Recommend perception components for object detection",
            "Path planning algorithms for dynamic environments"
        ]
        
        print("\n🔍 Testing Vector-Based k-NN Search:")
        print("-" * 50)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Query: \"{query}\"")
            print("   Vector k-NN Results:")
            
            # Perform vector search
            vector_results = vector_manager.vector_search(query, k=3)
            
            if vector_results:
                for j, result in enumerate(vector_results, 1):
                    name = result.get('name', 'Unknown')
                    score = result.get('score', 0.0)
                    desc = result.get('description', 'No description')[:80] + "..."
                    print(f"     {j}. {name} (score: {score:.3f})")
                    print(f"        {desc}")
            else:
                print("     No results found")
        
        print("\n🔍 Testing Hybrid Search (Vector + Text):")
        print("-" * 50)
        
        for i, query in enumerate(test_queries[:3], 1):  # Test first 3 queries
            print(f"\n{i}. Query: \"{query}\"")
            print("   Hybrid Search Results:")
            
            # Perform hybrid search
            hybrid_results = vector_manager.hybrid_search(query, k=3, semantic_weight=0.7)
            
            if hybrid_results:
                for j, result in enumerate(hybrid_results, 1):
                    name = result.get('name', 'Unknown')
                    score = result.get('score', 0.0)
                    desc = result.get('description', 'No description')[:80] + "..."
                    print(f"     {j}. {name} (score: {score:.3f})")
                    print(f"        {desc}")
            else:
                print("     No results found")
        
        print("\n🔍 Testing Enhanced NLP Search with Vector k-NN:")
        print("-" * 50)
        
        test_query = test_queries[0]  # Use first query
        print(f"\nQuery: \"{test_query}\"")
        
        # Process with enhanced NLP engine
        result = nlp_engine.process_natural_language_query(test_query, max_results=5)
        
        print("\nNLP Engine Response:")
        print(f"  {result.get('synthesized_response', 'No response generated')}")
        
        print(f"\nTop Components Found ({len(result.get('results', []))}):")
        for i, component in enumerate(result.get('results', [])[:3], 1):
            name = component.get('name', 'Unknown')
            search_type = component.get('search_type', 'unknown')
            score = component.get('relevance_score', 0.0)
            print(f"  {i}. {name} (type: {search_type}, score: {score:.3f})")
        
        print(f"\nSearch Metadata:")
        metadata = result.get('metadata', {})
        for key, value in metadata.items():
            print(f"  • {key}: {value}")
        
        # Test component similarity
        print("\n🔍 Testing Component Similarity Search:")
        print("-" * 50)
        
        # Get a sample component
        all_components = vector_manager.solr_manager.get_all_components()
        if all_components:
            sample_component = all_components[0]
            component_id = sample_component.get('uri', sample_component.get('id', ''))
            component_name = sample_component.get('name', 'Unknown')
            
            print(f"\nFinding components similar to: {component_name}")
            
            similar_components = vector_manager.find_similar_components(component_id, k=3)
            
            if similar_components:
                for i, comp in enumerate(similar_components, 1):
                    name = comp.get('name', 'Unknown')
                    score = comp.get('score', 0.0)
                    print(f"  {i}. {name} (similarity: {score:.3f})")
            else:
                print("  No similar components found")
        
        print("\n✅ Vector Search Testing Complete!")
        print("\n🎯 Key Features Demonstrated:")
        print("  • Dense vector embeddings for all ROS components")
        print("  • Query-to-vector conversion using Sentence-BERT")
        print("  • k-NN similarity search in vector space")
        print("  • Hybrid search combining text and semantic similarity")
        print("  • Component similarity recommendations")
        print("  • Integration with rule-based NLP processing")
        
    except Exception as e:
        print(f"❌ Error during vector search testing: {e}")
        import traceback
        traceback.print_exc()

def interactive_vector_search():
    """Interactive vector search demo."""
    
    print("\n🎮 Interactive Vector Search Demo")
    print("=" * 40)
    
    # Initialize
    project_root = Path(__file__).parent
    mobile_robot_file = project_root / "data" / "mobile_robot_components.ttl"
    legacy_data_file = project_root / "data" / "components_converted.ttl"
    
    ttl_file = None
    for candidate_file in [mobile_robot_file, legacy_data_file]:
        if candidate_file.exists():
            ttl_file = str(candidate_file)
            break
    
    if not ttl_file:
        print("❌ No data files found!")
        return
    
    try:
        vector_manager = VectorSearchManager(ttl_file)
        print("✅ Vector Search Manager ready!")
        
        while True:
            print("\n" + "-" * 40)
            query = input("🔍 Enter your search query (or 'quit' to exit): ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
                
            if not query:
                continue
            
            print(f"\n🎯 Searching for: \"{query}\"")
            
            # Vector search
            results = vector_manager.vector_search(query, k=5)
            
            if results:
                print(f"\n📋 Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    name = result.get('name', 'Unknown')
                    score = result.get('score', 0.0)
                    desc = result.get('description', 'No description')
                    print(f"\n{i}. {name} (similarity: {score:.3f})")
                    print(f"   Description: {desc}")
            else:
                print("❌ No results found")
        
        print("\n👋 Thanks for testing the vector search!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Run automatic tests
    test_vector_search()
    
    # Ask if user wants interactive demo
    print("\n" + "=" * 70)
    user_input = input("Would you like to try the interactive vector search demo? (y/n): ").strip().lower()
    
    if user_input in ['y', 'yes']:
        interactive_vector_search()
