#!/usr/bin/env python3
"""
Main application entry point for the ROS Component Explorer.
This proof-of-concept demonstrates semantic search and visualization of ROS components.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.db_manager import DatabaseManager
from frontend.ui import build_ui
import nicegui.ui as ui


def main():
    """Initialize and run the ROS Component Explorer application."""
    
    # Initialize the database manager with the RDF data file
    data_file = project_root / "data" / "components.ttl"
    
    if not data_file.exists():
        print(f"Error: Data file not found at {data_file}")
        print("Please ensure the data/components.ttl file exists.")
        return
    
    try:
        db_manager = DatabaseManager(str(data_file))
        db_manager.load_data()
        print(f"Loaded {len(db_manager.get_all_components())} components from database")
        
        # Build and run the user interface
        build_ui(db_manager)
        
        # Start the NiceGUI application
        ui.run(
            title="ROS Component Explorer",
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
