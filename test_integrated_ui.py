#!/usr/bin/env python3
"""
Test the LLM-integrated web interface without actually starting the web server.
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("🔧 Testing LLM-Integrated Web Interface...")
    
    # Test backend components
    from backend.solr_manager import SolrManager
    print("✅ SolrManager imported")
    
    from LLM.llm_search_engine import LLMSearchEngine
    print("✅ LLMSearchEngine imported")
    
    # Test initialization
    ttl_file = "data/components_clean.ttl"
    print(f"🗂️ Using TTL file: {ttl_file}")
    
    db_manager = SolrManager(ttl_file)
    print("✅ SolrManager initialized")
    
    llm_engine = LLMSearchEngine(ttl_file)
    print("✅ LLMSearchEngine initialized")
    
    # Test a simple query
    print("\n🧠 Testing LLM Query Processing...")
    test_query = "What is the best SLAM package for outdoor robots?"
    
    result = llm_engine.process_natural_language_query(test_query, max_results=3)
    print("✅ LLM query processed successfully")
    
    print(f"\n📊 Results:")
    print(f"   Query: {result['query']}")
    print(f"   Components found: {result['metadata']['total_found']}")
    print(f"   Search type: {result['metadata']['search_type']}")
    
    print(f"\n🤖 AI Response Preview:")
    response = result['synthesized_response']
    if len(response) > 200:
        response = response[:200] + "..."
    print(f"   {response}")
    
    print("\n🎉 LLM Integration Test Successful!")
    print("\nYou can now run the web interface with:")
    print("   python main.py")
    print("\nThe web interface will include both:")
    print("   • Traditional search (text, semantic, hybrid)")
    print("   • Natural language queries with AI responses")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
