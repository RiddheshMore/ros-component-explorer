#!/usr/bin/env python3
"""
Quick demonstration of the LLM-enhanced web interface features.
This shows what users will experience in the web interface.
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demo_search_modes():
    """Demonstrate the different search modes available in the web interface."""
    
    print("🌐 ROS Component Explorer - LLM Enhanced Web Interface")
    print("=" * 60)
    print()
    
    # Initialize the components
    from backend.solr_manager import SolrManager
    from LLM.llm_search_engine import LLMSearchEngine
    
    db_manager = SolrManager("data/components_clean.ttl")
    llm_engine = LLMSearchEngine("data/components_clean.ttl")
    
    print("✅ Backend systems initialized")
    print(f"   Database: {len(db_manager.get_all_components())} components loaded")
    print(f"   LLM Engine: Ready for natural language queries")
    print()
    
    # Demo 1: Traditional Text Search
    print("🔍 MODE 1: Traditional Text Search")
    print("-" * 40)
    query = "slam"
    results = db_manager.search_components(query)
    print(f"Query: '{query}'")
    print(f"Results: {len(results)} components found")
    for i, comp in enumerate(results[:3], 1):
        name = comp['name'][0] if isinstance(comp['name'], list) else comp['name']
        print(f"   {i}. {name}")
    print()
    
    # Demo 2: Natural Language Search
    print("🧠 MODE 2: Natural Language Search")
    print("-" * 40)
    nl_query = "What is the best SLAM package for outdoor robots with 3D LiDAR?"
    print(f"Query: '{nl_query}'")
    
    result = llm_engine.process_natural_language_query(nl_query, max_results=3)
    print(f"AI Understanding:")
    print(f"   • Categories: {[c.value for c in result.get('requirements', {}).get('categories', [])]}")
    print(f"   • Sensors: {[s.value for s in result.get('requirements', {}).get('sensors', [])]}")
    print(f"   • Environment: {result.get('requirements', {}).get('environment', {}).value if result.get('requirements', {}).get('environment') else 'Unknown'}")
    print()
    print(f"AI Response:")
    response = result['synthesized_response']
    # Show first few lines
    lines = response.split('\n')[:4]
    for line in lines:
        if line.strip():
            print(f"   {line}")
    print("   ...")
    print()
    
    print("🌐 Web Interface Features:")
    print("-" * 40)
    print("✅ Dual Search Modes:")
    print("   • Traditional: Keyword search with text/semantic/hybrid options")
    print("   • Natural Language: Ask questions in plain English")
    print()
    print("✅ Smart UI Elements:")
    print("   • Search mode toggle (Traditional ↔ Natural Language)")
    print("   • Example queries to help users get started")
    print("   • AI response cards with explanations")
    print("   • Component cards with detailed information")
    print()
    print("✅ Query Types Supported:")
    print("   • Recommendations: 'What is the best...'")
    print("   • Searches: 'Find components for...'")
    print("   • Explanations: 'What does X do...'")
    print("   • Comparisons: 'Compare X and Y...'")
    print()
    
    print("🚀 How to Start the Web Interface:")
    print("-" * 40)
    print("1. Run: python main.py")
    print("2. Open: http://localhost:8080")
    print("3. Choose your search mode:")
    print("   • Traditional: Use the search box and filters")
    print("   • Natural Language: Click the toggle and ask questions")
    print()
    
    print("💡 Example Web Interface Workflow:")
    print("-" * 40)
    print("1. User visits http://localhost:8080")
    print("2. Sees both Traditional and Natural Language options")
    print("3. Clicks 'Natural Language' toggle")
    print("4. Types: 'I need navigation for indoor robots'")
    print("5. Gets AI response with recommendations + component details")
    print("6. Can switch to Traditional mode for keyword searches")
    print()
    
    print("🎉 The web interface now combines the best of both worlds:")
    print("   • Precise traditional search for experts")
    print("   • Intuitive natural language for everyone")

if __name__ == "__main__":
    try:
        demo_search_modes()
    except Exception as e:
        print(f"❌ Error running demo: {e}")
        print("\nMake sure Solr is running and all dependencies are installed.")
        print("Run: python start.py --check")
