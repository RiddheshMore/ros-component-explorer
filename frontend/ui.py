"""
Frontend UI for the ROS Component Explorer with LLM Integration.
Provides a web-based interface focused on a single natural language search bar.
"""

import logging
import asyncio
from typing import List, Dict, Optional
import nicegui.ui as ui
from nicegui import events

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ROSComponentUI:
    """Main UI class for the ROS Component Explorer with LLM integration."""
    
    def __init__(self, db_manager, ttl_file: str = None):
        self.db_manager = db_manager
        self.ttl_file = ttl_file or "data/components_clean.ttl"
        self.search_results = []
        
        # Initialize LLM search engine
        try:
            # Import here to avoid dependency issues if LLM modules aren't available
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            from LLM.llm_search_engine import LLMSearchEngine
            self.llm_engine = LLMSearchEngine(self.ttl_file)
            self.nlp_enabled = True
            logger.info("LLM search engine initialized")
        except Exception as e:
            logger.warning(f"LLM search engine not available: {e}")
            self.llm_engine = None
            self.nlp_enabled = False
        
        # UI components (will be set during build)
        self.nlp_input = None
        self.results_container = None
        self.nlp_response_container = None
        
    def build_ui(self):
        """Build the complete user interface with LLM integration."""
        try:
            # Main container
            with ui.column().classes('w-full max-w-7xl mx-auto p-4'):
                # Header
                self._build_header()
                
                # Natural language search section (single search bar)
                self._build_nlp_search()
                
                # Results section
                self._build_results_section()
                
                # Component details modal
                self._build_details_modal()
                
            # Auto-load all components in ascending order when the app is launched
            self._load_all_components()
                
            logger.info("Enhanced UI built successfully")
            
        except Exception as e:
            logger.error(f"Error building UI: {e}")
            raise
    
    def _build_header(self):
        """Build the application header."""
        with ui.row().classes('w-full items-center mb-6'):
            ui.icon('robot', size='lg').classes('text-blue-600 mr-3')
            with ui.column().classes('flex-grow'):
                ui.label('ROS Component Explorer').classes('text-3xl font-bold text-gray-800')
                ui.label('Ask questions in natural language to discover ROS components').classes('text-lg text-gray-600')
    
    # Removed search mode toggle and traditional search; keeping only NLP search
    
    def _build_nlp_search(self):
        """Build the natural language search interface."""
        with ui.card().classes('w-full mb-6 p-6'):
            ui.label('Natural Language Search').classes('text-xl font-semibold mb-4')
            ui.label('Ask me anything about ROS components!').classes('text-gray-600 mb-4')
            
            # Example queries
            with ui.expansion('Example Queries', icon='help_outline').classes('mb-4'):
                examples = [
                    "What is the best SLAM package for a robot with a 3D LiDAR and an IMU in a large, outdoor environment?",
                    "I need a navigation stack for indoor environments with stereo cameras",
                    "Recommend a localization package for outdoor robots with GPS and wheel odometry",
                    "Find perception components for object detection using depth cameras",
                    "What planning algorithms work well with 2D LiDAR in real-time?"
                ]
                
                for example in examples:
                    with ui.row().classes('w-full mb-2 items-center'):
                        ui.label(f'• {example}').classes('flex-grow text-sm text-gray-700')
                        ui.button('Try', 
                                  on_click=lambda e, q=example: self._use_example_query(q)
                                ).classes('text-xs px-2 py-1')
            
            # NLP search input
            with ui.row().classes('w-full gap-4 items-end'):
                self.nlp_input = ui.textarea(
                    label='Ask me anything about ROS components',
                    placeholder='e.g., "What is the best SLAM package for outdoor robots with 3D LiDAR?"'
                ).classes('flex-grow min-h-20')
                self.nlp_input.on('keydown.ctrl+enter', self._perform_nlp_search)
                
                ui.button('Ask', on_click=self._perform_nlp_search).classes('px-6 py-2')
            
            ui.label('Tip: Press Ctrl+Enter to search').classes('text-xs text-gray-500 mt-1')
            
            # NLP response container
            self.nlp_response_container = ui.column().classes('w-full mt-4 hidden')
    
    def _build_results_section(self):
        """Build the results display section."""
        with ui.column().classes('w-full'):
            # Results info
            self.results_info = ui.html('<p class="text-gray-600 mb-4">Loading components in ascending order...</p>')
            
            # Results container
            self.results_container = ui.column().classes('w-full gap-4')
    
    def _build_details_modal(self):
        """Build the component details modal."""
        with ui.dialog() as self.details_dialog, ui.card():
            ui.html('<h3 class="text-lg font-semibold mb-4">Component Details</h3>')
            
            with ui.column().classes('w-full'):
                self.details_name = ui.html('<p><strong>Name:</strong> <span id="comp-name"></span></p>')
                self.details_type = ui.html('<p><strong>Type:</strong> <span id="comp-type"></span></p>')
                self.details_description = ui.html('<p><strong>Description:</strong> <span id="comp-desc"></span></p>')
                self.details_package = ui.html('<p><strong>Package:</strong> <span id="comp-pkg"></span></p>')
                self.details_ros_version = ui.html('<p><strong>ROS Version:</strong> <span id="comp-ros"></span></p>')
                self.details_update_rate = ui.html('<p><strong>Update Rate:</strong> <span id="comp-rate"></span></p>')
                
                with ui.row().classes('w-full mt-4'):
                    self.details_subscribed = ui.html('<p><strong>Subscribed Topics:</strong> <span id="comp-sub"></span></p>')
                    self.details_published = ui.html('<p><strong>Published Topics:</strong> <span id="comp-pub"></span></p>')
            
            with ui.row().classes('w-full justify-end mt-4'):
                ui.button('Close', on_click=self.details_dialog.close).classes('px-4 py-2')
    
    def _on_search_change(self, e: events.ValueChangeEventArguments):
        """Handle search input change."""
        # Could add real-time search suggestions here
        pass
    
    # Removed auto-load and mode switching; results appear after NLP queries
    def _use_example_query(self, query: str):
        """Use an example query in the NLP search."""
        if hasattr(self, 'nlp_input'):
            self.nlp_input.value = query
    
    # Removed search type change handler; no longer applicable
    def _perform_nlp_search(self, e=None):
        """Perform natural language search."""
        if not self.nlp_enabled:
            ui.notify("Natural language search is not available", type='warning')
            return
        
        query = self.nlp_input.value.strip() if hasattr(self, 'nlp_input') and self.nlp_input.value else ""
        if not query:
            # If no query is provided, reset to showing all components in ascending order
            self._load_all_components()
            return
        
        try:
            # Show loading indicator
            if hasattr(self, 'nlp_response_container'):
                self.nlp_response_container.clear()
                with self.nlp_response_container:
                    ui.spinner('dots', size='md').classes('mb-4')
                    ui.label('Processing your query...').classes('text-gray-600')
                self.nlp_response_container.classes(remove='hidden')
            
            # Process query with LLM asynchronously
            async def process_query():
                try:
                    result = self.llm_engine.process_natural_language_query(query, max_results=10)
                    
                    # Update NLP response
                    if hasattr(self, 'nlp_response_container'):
                        self.nlp_response_container.clear()
                        with self.nlp_response_container:
                            # Show synthesized response
                            with ui.card().classes('w-full p-4 bg-blue-50 border-l-4 border-blue-500'):
                                ui.label('AI Response').classes('font-semibold text-blue-800 mb-2')
                                ui.markdown(result['synthesized_response']).classes('text-gray-800')
                            
                            # Show metadata
                            if result.get('metadata'):
                                with ui.row().classes('w-full gap-4 mt-2 text-sm text-gray-600'):
                                    ui.label(f"Found: {result['metadata']['total_found']} components")
                                    ui.label(f"Search type: {result['metadata']['search_type']}")
                    
                    # Update results
                    self.search_results = result['results']
                    self._update_results()
                    
                except Exception as e:
                    logger.error(f"NLP search error: {e}")
                    if hasattr(self, 'nlp_response_container'):
                        self.nlp_response_container.clear()
                        with self.nlp_response_container:
                            ui.label(f"Error: {str(e)}").classes('text-red-600')
            
            # Run async processing
            asyncio.create_task(process_query())
            
        except Exception as e:
            logger.error(f"NLP search error: {e}")
            ui.notify(f"Search error: {str(e)}", type='negative')
    
    # Removed traditional search handler; only NLP search remains
    
    def _load_all_components(self):
        """Load all components in ascending order by name when the app is launched."""
        try:
            # Get all components from the database
            all_components = self.db_manager.get_all_components()
            
            # Remove duplicates by name, preferring components with "Component" in the class name
            unique_components = {}
            for component in all_components:
                name = component.get('name', '')
                class_name = component.get('class', '')
                
                # Handle cases where name or class might be lists
                if isinstance(name, list):
                    name = name[0] if name else ''
                if isinstance(class_name, list):
                    class_name = class_name[0] if class_name else ''
                
                # Ensure we have string values
                name = str(name)
                class_name = str(class_name)
                
                if name in unique_components:
                    # Prefer components with "Component" suffix (newer format)
                    existing_class = unique_components[name].get('class', '')
                    if isinstance(existing_class, list):
                        existing_class = existing_class[0] if existing_class else ''
                    existing_class = str(existing_class)
                    
                    if 'Component' in class_name and 'Component' not in existing_class:
                        # Update the component's name and class to ensure they're strings
                        component['name'] = name
                        component['class'] = class_name
                        unique_components[name] = component
                    elif 'Component' not in class_name and 'Component' in existing_class:
                        # Keep the existing one (already has Component suffix)
                        pass
                    else:
                        # Both have same format, keep the first one
                        pass
                else:
                    # Update the component's name and class to ensure they're strings
                    component['name'] = name
                    component['class'] = class_name
                    unique_components[name] = component
            
            # Convert back to list and sort by name in ascending order
            def safe_sort_key(component):
                name = component.get('name', '')
                return name.lower() if isinstance(name, str) else str(name).lower()
                
            sorted_components = sorted(unique_components.values(), key=safe_sort_key)
            
            # Set the search results
            self.search_results = sorted_components
            
            # Update the results display
            self.results_info.content = f'<p class="text-gray-600 mb-4">All {len(sorted_components)} unique components loaded in ascending order.</p>'
            self._update_results()
            
        except Exception as e:
            logger.error(f"Error loading all components: {e}")
            ui.notify(f"Error loading components: {str(e)}", type='negative')
            self.results_info.content = '<p class="text-red-600 mb-4">Failed to load components.</p>'

    def _update_results(self):
        """Update the results display with component cards."""
        results = self.search_results
        
        # Clear existing results  
        self.results_container.clear()
        
        if not results:
            with self.results_container:
                ui.label('No components found.').classes('text-gray-600 text-center py-8')
            return
        
        # Display results as cards
        if results:
            with self.results_container:
                ui.html('<h3 class="text-xl font-bold mb-4">Components</h3>')
                with ui.row().classes('w-full mb-4'):
                    ui.label(f'Found {len(results)} components').classes('text-lg font-semibold text-blue-600')
        
        # Add component cards
        for i, result in enumerate(results):
            with self.results_container:
                with ui.card().classes('w-full p-4 border'):
                    with ui.row().classes('w-full items-center justify-between'):
                        with ui.column().classes('flex-1'):
                            # Component name
                            ui.html(f'<h4 class="text-lg font-semibold text-blue-700">{result.get("name", "Unknown")}</h4>')
                            
                            # Component class
                            class_name = result.get('class', 'Unknown')
                            ui.html(f'<p class="text-sm text-gray-600 mb-2">Class: {class_name}</p>')
                            
                            # Component description
                            description = result.get('description', 'No description')
                            if len(description) > 150:
                                description = description[:150] + '...'
                            ui.html(f'<p class="text-gray-700">{description}</p>')
                        
                        # Details button
                        ui.button(
                            'DETAILS',
                            on_click=lambda r=result: self._show_component_details(r),
                            color='primary'
                        ).classes('px-4 py-2 ml-4')
    
    def _show_component_details(self, component: Dict):
        """Show detailed information about a component."""
        try:
            # Get full component details
            details = self.db_manager.get_component_details(component['uri'])
            
            if details:
                # Update modal content
                self.details_name.content = f'<p><strong>Name:</strong> {details.get("name", "Unknown")}</p>'
                self.details_type.content = f'<p><strong>Type:</strong> {details.get("class", "Unknown")}</p>'
                self.details_description.content = f'<p><strong>Description:</strong> {details.get("description", "No description")}</p>'
                
                properties = details.get('properties', {})
                self.details_package.content = f'<p><strong>Package:</strong> {properties.get("package", "Unknown")}</p>'
                self.details_ros_version.content = f'<p><strong>ROS Version:</strong> {properties.get("ros_version", "Unknown")}</p>'
                self.details_update_rate.content = f'<p><strong>Update Rate:</strong> {properties.get("update_rate", "Unknown")}</p>'
                
                subscribed = properties.get('subscribed_topics', [])
                subscribed_text = ', '.join(subscribed) if subscribed else 'None'
                self.details_subscribed.content = f'<p><strong>Subscribed Topics:</strong> {subscribed_text}</p>'
                
                published = properties.get('published_topics', [])
                published_text = ', '.join(published) if published else 'None'
                self.details_published.content = f'<p><strong>Published Topics:</strong> {published_text}</p>'
                
                # Show modal
                self.details_dialog.open()
            else:
                ui.notify('Component details not found.', type='warning')
                
        except Exception as e:
            logger.error(f"Error showing component details: {e}")
            ui.notify(f'Error loading component details: {str(e)}', type='negative')


def build_ui(db_manager, ttl_file: str = None):
    """Build and return the complete UI with LLM integration."""
    ui_instance = ROSComponentUI(db_manager, ttl_file)
    ui_instance.build_ui()
    return ui_instance 