#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.solr_manager import SolrManager

def main():
    sm = SolrManager("/home/ritz/ros-component-explorer/data/components_converted.ttl")
    
    # Test the exact query that's being generated
    query = "name:(raspberry OR detection OR cameras OR perception OR camera OR vision) OR type:(raspberry OR detection OR cameras OR perception OR camera OR vision) OR description:(raspberry OR detection OR cameras OR perception OR camera OR vision) OR content:(raspberry OR detection OR cameras OR perception OR camera OR vision)"
    
    print("Query:", query)
    print("=" * 80)
    
    results = sm.search_components(query)
    
    print(f"Found {len(results)} results:")
    print("-" * 40)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.get('name', 'Unknown')}")
        print(f"   Type: {result.get('class', 'Unknown')}")
        print(f"   Score: {result.get('relevance_score', 0):.3f}")
        print(f"   URI: {result.get('uri', 'Unknown')}")
        print(f"   Description: {result.get('description', 'No description')[:100]}...")
        print()

if __name__ == "__main__":
    main()
