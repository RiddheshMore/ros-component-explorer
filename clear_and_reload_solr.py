#!/usr/bin/env python3
"""
Clear Solr index and load fresh data from components.ttl
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.solr_manager import SolrManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_and_reload_solr():
    """Clear Solr index and reload from main components.ttl file."""
    
    # Path to the main components.ttl file
    main_components_file = project_root / "data" / "components_converted.ttl"
    
    if not main_components_file.exists():
        print(f"Error: Main components file not found at {main_components_file}")
        return False
    
    try:
        # Create a direct connection to Solr
        from pysolr import Solr
        SOLR_URL = "http://localhost:8984/solr/ros_explorer"
        solr = Solr(SOLR_URL, timeout=10)
        
        print("Clearing existing Solr index...")
        # Delete all documents
        solr.delete(q="*:*")
        solr.commit()
        print("Solr index cleared successfully")
        
        # Now load fresh data using SolrManager
        print(f"Loading components from {main_components_file}...")
        db_manager = SolrManager(str(main_components_file))
        
        # Get all loaded components
        all_components = db_manager.get_all_components()
        print(f"Successfully loaded {len(all_components)} components from {main_components_file}")
        
        # Display component types
        type_counts = {}
        for component in all_components:
            comp_type = component.get('class', 'Unknown')
            # Handle case where comp_type might be a list
            if isinstance(comp_type, list):
                comp_type = comp_type[0] if comp_type else 'Unknown'
            comp_type = str(comp_type)
            type_counts[comp_type] = type_counts.get(comp_type, 0) + 1
        
        print("\nComponent types loaded:")
        for comp_type, count in sorted(type_counts.items()):
            print(f"  {comp_type}: {count}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = clear_and_reload_solr()
    if success:
        print("\n✅ Successfully cleared and reloaded Solr with main components.ttl")
    else:
        print("\n❌ Failed to clear and reload Solr")
