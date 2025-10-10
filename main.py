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
from frontend.ui import build_ui
import nicegui.ui as ui


def main():
    """Initialize and run the ROS Component Explorer application."""
    
    # Initialize the Solr manager with mobile robot components
    # Use the new mobile robot components as primary data
    mobile_robot_file = project_root / "data" / "mobile_robot_components.ttl"
    legacy_data_file = project_root / "data" / "components_converted.ttl"
    expanded_file = project_root / "data" / "expanded_components_ros.ttl"
    
    # Prioritize mobile robot components
    if mobile_robot_file.exists():
        data_file = mobile_robot_file
        print(f"Using mobile robot components from {mobile_robot_file}")
    elif legacy_data_file.exists():
        data_file = legacy_data_file
        print(f"Using legacy components from {legacy_data_file}")
    else:
        print(f"Error: No data files found!")
        print("Please ensure mobile_robot_components.ttl or components_converted.ttl exists.")
        return
        
    if not expanded_file.exists():
        print(f"Warning: Expanded components file not found at {expanded_file}")
        print("Only base components will be loaded.")
    
    try:
        # Initialize Solr with mobile robot components
        db_manager = SolrManager(str(data_file))
        base_count = len(db_manager.get_all_components())
        
        # Only use mobile robot components to maintain GitHub URLs
        total_count = len(db_manager.get_all_components())
        print(f"Total components loaded: {total_count}")
        print("Note: Using only mobile robot components to preserve GitHub repository URLs")
        
        # Build and run the user interface with rule-based natural language processing
        build_ui(db_manager, str(data_file))
        
        # Start the NiceGUI application
        ui.run(
            title="ROS Component Explorer - Natural Language Search",
            port=8080,
            show=True,
            reload=False
        )
        
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
