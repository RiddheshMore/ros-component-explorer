#!/usr/bin/env python3
"""
Test the full LLM search engine functionality.
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from LLM.llm_search_engine import LLMSearchEngine
    print("✅ Imported LLMSearchEngine")
    
    ttl_file = "data/components.ttl"
    print(f"🔧 Initializing with TTL file: {ttl_file}")
    
    engine = LLMSearchEngine(ttl_file)
    print("✅ LLM Search Engine initialized")
    
    query = "What is the best SLAM package for outdoor robots with 3D LiDAR?"
    print(f"🔍 Testing query: {query}")
    
    result = engine.process_natural_language_query(query, max_results=3)
    print("✅ Query processed successfully")
    
    print(f"\n🤖 AI Response:")
    print(result['synthesized_response'])
    
    print(f"\n📊 Metadata:")
    metadata = result.get('metadata', {})
    print(f"   Total found: {metadata.get('total_found', 0)}")
    print(f"   Returned: {metadata.get('returned', 0)}")
    print(f"   Search type: {metadata.get('search_type', 'unknown')}")
    
    print(f"\n📋 Top Results:")
    for i, component in enumerate(result.get('results', [])[:3], 1):
        print(f"   {i}. {component.get('name', 'Unknown')}")
        print(f"      Type: {component.get('class', 'Unknown')}")
        score = component.get('final_score', component.get('score', 0))
        print(f"      Score: {score:.3f}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
