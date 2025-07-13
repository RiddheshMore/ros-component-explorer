"""
User interface for the ROS Component Explorer.
Built with NiceGUI for a modern web-based interface.
"""

import nicegui.ui as ui
from typing import List, Dict, Optional
from backend.db_manager import DatabaseManager
import logging
import functools

logger = logging.getLogger(__name__)


def build_ui(db_manager: DatabaseManager):
    """
    Build the main user interface for the ROS Component Explorer.
    
    Args:
        db_manager: The database manager instance
    """
    
    # Global state for the UI
    current_components = []
    search_input = None
    results_container = None
    status_label = None
    
    def update_component_list(components: List[Dict]):
        """Update the component list display."""
        nonlocal current_components
        current_components = components
        
        # Clear existing results
        if results_container:
            results_container.clear()
        
        if not components:
            with results_container:
                ui.label("No components found").classes("text-gray-500 text-center p-4")
            return
        
        # Display components in cards
        for component in components:
            with results_container:
                with ui.card().classes("w-full mb-2 cursor-pointer hover:bg-blue-50"):
                    with ui.row().classes("items-center justify-between"):
                        with ui.column():
                            ui.label(component['name']).classes("text-lg font-semibold")
                            ui.label(f"Class: {component['class']}").classes("text-sm text-gray-600")
                            if component['description']:
                                ui.label(component['description']).classes("text-sm text-gray-700 mt-1")
                        
                        with ui.column().classes("items-end"):
                            ui.button("Details", on_click=functools.partial(show_component_details, component)).classes("bg-blue-500 text-white")
    
    def perform_search():
        """Perform search based on current input."""
        search_term = search_input.value if search_input else ""
        components = db_manager.search_components(search_term)
        update_component_list(components)
        
        # Update status
        if status_label:
            status_label.text = f"Found {len(components)} component(s)"
    
    def show_component_details(component: Dict):
        """Show detailed information for a component in a dialog."""
        details = db_manager.get_component_details(component['uri'])
        
        if not details:
            ui.notify("Error: Could not load component details", type="error")
            return
        
        with ui.dialog() as dialog, ui.card():
            ui.card_section().classes("p-6")
            
            # Header
            with ui.row().classes("items-center justify-between mb-4"):
                ui.label(f"Component Details: {details.get('name', 'Unknown')}").classes("text-xl font-bold")
                ui.button("Close", on_click=dialog.close).classes("bg-gray-500 text-white")
            
            # Details content
            with ui.column().classes("space-y-3"):
                # Display class if available
                if 'class' in details:
                    ui.label(f"**Class:** {details['class']}").classes("text-sm")
                
                # Display description if available
                if 'description' in details.get('properties', {}):
                    ui.label(f"**Description:** {details['properties']['description']}").classes("text-sm")
                
                # Display inputs
                inputs = [v for k, v in details.get('properties', {}).items() if k == 'hasInput']
                if inputs:
                    ui.label(f"**Inputs:** {', '.join(inputs)}").classes("text-sm")
                
                # Display outputs
                outputs = [v for k, v in details.get('properties', {}).items() if k == 'hasOutput']
                if outputs:
                    ui.label(f"**Outputs:** {', '.join(outputs)}").classes("text-sm")
                
                # Display other properties
                for prop_name, prop_value in details.get('properties', {}).items():
                    if prop_name not in ['description', 'hasInput', 'hasOutput']:  # Skip already displayed properties
                        # Format property name for display
                        display_name = prop_name.replace('_', ' ').title()
                        ui.label(f"**{display_name}:** {prop_value}").classes("text-sm")
                
                # Show URI for reference
                ui.label(f"**URI:** {details['uri']}").classes("text-xs text-gray-500 mt-4")
        dialog.open()
    
    def load_all_components():
        """Load and display all components."""
        components = db_manager.get_all_components()
        update_component_list(components)
        
        if status_label:
            status_label.text = f"Showing all {len(components)} components"
    
    # Main UI Layout
    with ui.column().classes("w-full max-w-4xl mx-auto p-4"):
        # Header
        with ui.row().classes("items-center justify-between mb-6"):
            ui.label("ROS Component Explorer").classes("text-3xl font-bold text-blue-600")
            ui.label("Proof-of-Concept").classes("text-sm text-gray-500")
        
        # Search Section
        with ui.card().classes("w-full mb-6"):
            ui.card_section().classes("p-4")
            
            with ui.row().classes("items-center space-x-4"):
                search_input = ui.input(
                    label="Search for components...",
                    placeholder="Enter component name, class, or description"
                ).classes("flex-grow")
                
                ui.button("Search", on_click=perform_search).classes("bg-blue-500 text-white")
                ui.button("Show All", on_click=load_all_components).classes("bg-gray-500 text-white")
        
        # Status
        status_label = ui.label("").classes("text-sm text-gray-600 mb-4")
        
        # Results Section
        with ui.card().classes("w-full"):
            ui.card_section().classes("p-4")
            ui.label("Components").classes("text-lg font-semibold mb-4")
            
            results_container = ui.column().classes("w-full")
        
        # Load initial data
        load_all_components()
    
    logger.info("UI built successfully")


def create_about_dialog():
    """Create an about dialog with project information."""
    with ui.dialog() as dialog, ui.card():
        ui.card_section().classes("p-6")
        
        with ui.column().classes("space-y-4"):
            ui.label("About ROS Component Explorer").classes("text-xl font-bold")
            
            ui.label("""
            This is a proof-of-concept application for exploring ROS components using semantic search.
            
            **Features:**
            • Search components by name, class, or description
            • View detailed component information
            • RDF-based data storage using Turtle format
            
            **Technology Stack:**
            • Backend: Python with rdflib for RDF processing
            • Frontend: NiceGUI for modern web interface
            • Data: RDF/Turtle format for semantic descriptions
            """).classes("text-sm")
            
            ui.button("Close", on_click=dialog.close).classes("bg-blue-500 text-white") 