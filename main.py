#!/usr/bin/env python3
"""
Main application entry point for the ROS Component Explorer.

This application provides a web-based interface for browsing and searching ROS components
from RDF/TTL knowledge bases. The system uses Apache Solr for indexing and text search,
with a NiceGUI-based web interface for user interaction.

Key functionality:
- Loads ROS component data from TTL/RDF files into Apache Solr
- Provides a web-based component browser with search capabilities
- Uses rule-based natural language query processing with pattern matching
- Displays component details including topics, packages, and descriptions

Note: This system uses structured pattern matching and rule-based processing
for natural language understanding, not external language model APIs.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.solr_manager import SolrManager
from frontend.modern_ui import ModernROSExplorerUI
import nicegui.ui as ui


def main():
    """Initialize and run the ROS Component Explorer application."""
    
    # Initialize the Solr manager with available component data
    components_clean_file = project_root / "data" / "components_clean.ttl"
    components_file = project_root / "data" / "components.ttl"
    hierarchical_file = project_root / "data" / "mobile_robot_packages_hierarchical.ttl"
    expanded_file = project_root / "data" / "expanded_components_ros.ttl"
    components_final_file = project_root / "data" / "components_final.ttl"
    
    # Prioritize components_clean.ttl as it has the correct Component types and proper Turtle format
    if components_clean_file.exists() and components_clean_file.stat().st_size > 0:
        data_file = components_clean_file
        print(f"Using clean components file: {components_clean_file}")
    elif components_file.exists() and components_file.stat().st_size > 0:
        data_file = components_file
        print(f"Using main components file: {components_file}")
    elif hierarchical_file.exists() and hierarchical_file.stat().st_size > 0:
        data_file = hierarchical_file
        print(f"Using hierarchical components file: {hierarchical_file}")
    elif expanded_file.exists() and expanded_file.stat().st_size > 0:
        data_file = expanded_file
        print(f"Using expanded components file: {expanded_file}")
    elif components_final_file.exists() and components_final_file.stat().st_size > 0:
        data_file = components_final_file
        print(f"Using cleaned components file: {components_final_file}")
    else:
        print(f"Error: No valid data files found!")
        print("All TTL files appear to be empty or missing.")
        return
        
    if not expanded_file.exists():
        print(f"Warning: Expanded components file not found at {expanded_file}")
        print("Only base components will be loaded.")
    
    try:
        # Try to initialize Solr, but fall back to old db_manager if it fails
        db_manager = None
        try:
            print("Attempting to initialize Solr backend...")
            db_manager = SolrManager(str(data_file))
            total_count = len(db_manager.get_all_components())
            print(f"Solr initialized successfully with {total_count} components")
            print("Note: Using Solr backend for hybrid semantic search")
        except Exception as solr_error:
            print(f"Solr not available: {solr_error}")
            print("Falling back to in-memory RDF backend...")
            from backend.db_manager import DatabaseManager
            db_manager = DatabaseManager(str(data_file))
            total_count = len(db_manager.get_all_components())
            print(f"RDF backend initialized with {total_count} components")
            print("Note: Using in-memory RDF backend (text search only)")
        
        # Build and run the modern user interface with Figma-based design
        modern_ui = ModernROSExplorerUI(db_manager, str(data_file))
        modern_ui.build_ui()
        
        # Start the NiceGUI application  
        ui.run(
            host="0.0.0.0",
            port=8083,
            title="ROS Component Explorer",
            show=True,
            reload=False
        )
        
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
