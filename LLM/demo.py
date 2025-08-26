#!/usr/bin/env python3
"""
Command-line demo of the LLM-enhanced ROS Component Explorer.

This script demonstrates the natural language querying capabilities
without requiring web frameworks or UI dependencies.
"""

import sys
import os
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LLM.llm_search_engine import LLMSearchEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_separator(char="=", length=80):
    """Print a separator line."""
    print(char * length)

def print_results(result: dict):
    """Print search results in a formatted way."""
    print_separator()
    print(f"QUERY: {result['query']}")
    print_separator("-")
    
    # Print AI response
    print("🤖 AI RESPONSE:")
    print(result['synthesized_response'])
    print()
    
    # Print metadata
    metadata = result.get('metadata', {})
    print(f"📊 SEARCH METADATA:")
    print(f"   • Total found: {metadata.get('total_found', 0)}")
    print(f"   • Returned: {metadata.get('returned', 0)}")
    print(f"   • Search type: {metadata.get('search_type', 'unknown')}")
    print()
    
    # Print detailed results
    results = result.get('results', [])
    if results:
        print("📋 COMPONENT DETAILS:")
        print_separator("-", 60)
        
        for i, component in enumerate(results[:5], 1):  # Show top 5
            print(f"{i}. {component.get('name', 'Unknown')}")
            print(f"   Type: {component.get('class', 'Unknown')}")
            print(f"   Score: {component.get('final_score', component.get('score', 0)):.3f}")
            
            description = component.get('description', 'No description')
            if len(description) > 100:
                description = description[:100] + "..."
            print(f"   Description: {description}")
            
            if component.get('uri'):
                print(f"   URI: {component['uri']}")
            print()
        
        if len(results) > 5:
            print(f"   ... and {len(results) - 5} more results")
    
    print_separator()

def interactive_demo():
    """Run an interactive demo of the LLM search engine."""
    print("🚀 ROS Component Explorer - LLM Demo")
    print("=====================================")
    print()
    
    # Initialize the search engine
    ttl_file = "/home/ritz/Desktop/RnD/data/components.ttl"
    
    try:
        print("🔧 Initializing LLM Search Engine...")
        engine = LLMSearchEngine(ttl_file)
        print("✅ LLM Search Engine ready!")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize LLM Search Engine: {e}")
        return
    
    # Example queries
    example_queries = [
        "What is the best SLAM package for a robot with a 3D LiDAR and an IMU in a large, outdoor environment?",
        "I need a navigation stack for indoor environments with stereo cameras",
        "Recommend a localization package for outdoor robots with GPS and wheel odometry",
        "Find perception components for object detection using depth cameras",
        "What planning algorithms work well with 2D LiDAR in real-time?",
        "Compare different SLAM approaches for indoor robots",
        "Explain what move_base does in ROS navigation"
    ]
    
    print("💡 Example queries you can try:")
    for i, query in enumerate(example_queries, 1):
        print(f"{i}. {query}")
    print()
    
    while True:
        print("Options:")
        print("1. Enter your own natural language query")
        print("2. Try an example query")
        print("3. Exit")
        
        choice = input("\nSelect an option (1-3): ").strip()
        
        if choice == "1":
            query = input("\n🗣️ Enter your natural language query: ").strip()
            if query:
                print("\n🔍 Processing your query...")
                try:
                    result = engine.process_natural_language_query(query)
                    print_results(result)
                except Exception as e:
                    print(f"❌ Error processing query: {e}")
            else:
                print("❌ Please enter a valid query.")
        
        elif choice == "2":
            print("\n📝 Example queries:")
            for i, query in enumerate(example_queries, 1):
                print(f"{i}. {query}")
            
            try:
                example_choice = int(input(f"\nSelect an example (1-{len(example_queries)}): "))
                if 1 <= example_choice <= len(example_queries):
                    query = example_queries[example_choice - 1]
                    print(f"\n🔍 Processing: {query}")
                    
                    result = engine.process_natural_language_query(query)
                    print_results(result)
                else:
                    print("❌ Invalid selection.")
            except ValueError:
                print("❌ Please enter a valid number.")
            except Exception as e:
                print(f"❌ Error processing query: {e}")
        
        elif choice == "3":
            print("\n👋 Thanks for trying the ROS Component Explorer LLM demo!")
            break
        
        else:
            print("❌ Invalid option. Please select 1, 2, or 3.")
        
        print("\n" + "="*80 + "\n")

def batch_demo():
    """Run a batch demonstration with predefined queries."""
    print("🚀 ROS Component Explorer - Batch LLM Demo")
    print("==========================================")
    print()
    
    # Initialize the search engine
    ttl_file = "/home/ritz/Desktop/RnD/data/components.ttl"
    
    try:
        print("🔧 Initializing LLM Search Engine...")
        engine = LLMSearchEngine(ttl_file)
        print("✅ LLM Search Engine ready!")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize LLM Search Engine: {e}")
        return
    
    # Test queries
    test_queries = [
        "What is the best SLAM package for a robot with a 3D LiDAR and an IMU in a large, outdoor environment?",
        "I need a navigation stack for indoor environments",
        "Recommend localization packages for outdoor robots with GPS",
        "Find components for object detection",
        "What planning algorithms work with 2D LiDAR?"
    ]
    
    print(f"🧪 Running {len(test_queries)} test queries...")
    print()
    
    for i, query in enumerate(test_queries, 1):
        print(f"[{i}/{len(test_queries)}] Processing query...")
        try:
            result = engine.process_natural_language_query(query)
            print_results(result)
            print()
        except Exception as e:
            print(f"❌ Error processing query '{query}': {e}")
            print()

def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--batch":
        batch_demo()
    else:
        interactive_demo()

if __name__ == "__main__":
    main()
