#!/usr/bin/env python3
"""
Comprehensive test of the LLM search engine with various query types.
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_query(engine, query, query_type):
    """Test a single query and display results."""
    print(f"\n{'='*80}")
    print(f"🔍 {query_type.upper()} QUERY")
    print(f"{'='*80}")
    print(f"Query: {query}")
    print(f"{'-'*80}")
    
    try:
        result = engine.process_natural_language_query(query, max_results=3)
        
        print(f"🤖 AI Response:")
        print(result['synthesized_response'])
        
        metadata = result.get('metadata', {})
        print(f"\n📊 Found {metadata.get('total_found', 0)} components")
        
        print(f"\n📋 Top Results:")
        for i, component in enumerate(result.get('results', [])[:3], 1):
            name = component.get('name', 'Unknown')
            if isinstance(name, list):
                name = name[0] if name else "Unknown"
            
            comp_type = component.get('class', 'Unknown')
            if isinstance(comp_type, list):
                comp_type = comp_type[0] if comp_type else "Unknown"
            
            score = component.get('final_score', component.get('score', 0))
            print(f"   {i}. {name} ({comp_type}) - Score: {score:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run comprehensive LLM tests."""
    print("🚀 ROS Component Explorer - Comprehensive LLM Test")
    print("="*80)
    
    # Initialize the search engine
    try:
        from LLM.llm_search_engine import LLMSearchEngine
        ttl_file = "data/components.ttl"
        print(f"🔧 Initializing LLM Search Engine...")
        engine = LLMSearchEngine(ttl_file)
        print("✅ LLM Search Engine ready!")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Test queries with different types
    test_queries = [
        # Recommendation queries
        ("What is the best SLAM package for outdoor robots with 3D LiDAR?", "recommendation"),
        ("I need a navigation stack for indoor environments", "recommendation"),
        ("Recommend a localization package for robots with GPS", "recommendation"),
        
        # Search queries
        ("Find perception components for object detection", "search"),
        ("Show me planning algorithms for mobile robots", "search"),
        
        # Explanation queries
        ("What does AMCL do in robot localization?", "explanation"),
        ("Explain GMapping for SLAM", "explanation"),
        
        # Comparison queries
        ("Compare SLAM packages for indoor robots", "comparison"),
    ]
    
    successful_tests = 0
    total_tests = len(test_queries)
    
    for query, query_type in test_queries:
        if test_query(engine, query, query_type):
            successful_tests += 1
    
    print(f"\n{'='*80}")
    print(f"🏁 TEST SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Successful: {successful_tests}/{total_tests}")
    print(f"❌ Failed: {total_tests - successful_tests}/{total_tests}")
    
    if successful_tests == total_tests:
        print("🎉 All tests passed! LLM integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
