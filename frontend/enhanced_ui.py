"""
Enhanced Frontend UI for the ROS Component Explorer with LLM Integration.
Provides both traditional search and natural language querying capabilities.
"""

import logging
import asyncio
import json
from typing import List, Dict, Optional, Any
import nicegui.ui as ui
from nicegui import events
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LLM.llm_search_engine import LLMSearchEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedROSComponentUI:
    """Enhanced UI class with LLM-powered natural language search."""
    
    def __init__(self, db_manager, ttl_file: str):
        self.db_manager = db_manager
        self.ttl_file = ttl_file
        self.search_results = []
        self.current_search_type = "text"  # text, semantic, hybrid, nlp
        self.semantic_weight = 0.7
        
        # Initialize LLM search engine
        try:
            self.llm_engine = LLMSearchEngine(ttl_file)
            self.nlp_enabled = True
            logger.info("LLM search engine initialized")
        except Exception as e:
            logger.warning(f"LLM search engine not available: {e}")
            self.llm_engine = None
            self.nlp_enabled = False
        
        # UI components (will be set during build)
        self.search_input = None
        self.nlp_input = None
        self.results_container = None
        self.search_type_toggle = None
        self.nlp_response_container = None
        
    def build_ui(self):
        """Build the complete user interface with LLM integration."""
        try:
            # Main container
            with ui.column().classes('w-full max-w-7xl mx-auto p-4'):
                # Header
                self._build_header()
                
                # Search mode toggle
                self._build_search_mode_toggle()
                
                # Search sections
                self._build_search_sections()
                
                # Results section
                self._build_results_section()
                
                # Component details modal
                self._build_details_modal()
                
            # Load all components by default
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
                ui.label('Intelligent search for ROS packages and components').classes('text-lg text-gray-600')
    
    def _build_search_mode_toggle(self):
        """Build the search mode toggle."""
        with ui.card().classes('w-full mb-4 p-4'):
            ui.label('Search Mode').classes('text-lg font-semibold mb-2')
            
            with ui.row().classes('w-full gap-4'):
                # Traditional search toggle
                with ui.button_group():
                    ui.button('Traditional Search', 
                              on_click=lambda: self._switch_search_mode('traditional')).classes('px-4 py-2')
                    
                    if self.nlp_enabled:
                        ui.button('Natural Language', 
                                  on_click=lambda: self._switch_search_mode('nlp')).classes('px-4 py-2')
                    else:
                        ui.button('Natural Language (Unavailable)', 
                                  on_click=None).classes('px-4 py-2 opacity-50 cursor-not-allowed')
                
                # Search type indicator
                self.search_mode_indicator = ui.label('Traditional Search Mode').classes('text-sm text-gray-600 ml-4')
    
    def _build_search_sections(self):
        """Build both traditional and NLP search sections."""
        # Traditional search section
        self.traditional_search_container = ui.column().classes('w-full')
        with self.traditional_search_container:
            self._build_traditional_search()
        
        # NLP search section (initially hidden)
        self.nlp_search_container = ui.column().classes('w-full hidden')
        with self.nlp_search_container:
            if self.nlp_enabled:
                self._build_nlp_search()
    
    def _build_traditional_search(self):
        """Build the traditional search interface."""
        with ui.card().classes('w-full mb-6 p-6'):
            ui.label('Traditional Search').classes('text-xl font-semibold mb-4')
            
            with ui.row().classes('w-full gap-4 items-end'):
                # Search input
                self.search_input = ui.input(
                    label='Search components',
                    placeholder='Enter keywords, component names, or descriptions...'
                ).classes('flex-grow')
                self.search_input.on('keydown.enter', self._perform_traditional_search)
                
                # Search button
                ui.button('Search', on_click=self._perform_traditional_search).classes('px-6 py-2')
                
            # Search type options
            with ui.row().classes('w-full gap-4 mt-4'):
                ui.label('Search Type:').classes('text-sm font-medium')
                
                self.search_type_toggle = ui.toggle(
                    ['Text', 'Semantic', 'Hybrid'],
                    value='Text',
                    on_change=self._on_search_type_change
                ).classes('ml-2')
                
                # Semantic weight slider (shown for hybrid search)
                self.semantic_weight_container = ui.row().classes('ml-4 items-center hidden')
                with self.semantic_weight_container:
                    ui.label('Semantic Weight:').classes('text-sm')
                    self.semantic_weight_slider = ui.slider(
                        min=0.1, max=0.9, step=0.1, value=0.7,
                        on_change=lambda e: setattr(self, 'semantic_weight', e.value)
                    ).classes('w-32 ml-2')
    
    def _build_nlp_search(self):
        """Build the natural language search interface."""
        with ui.card().classes('w-full mb-6 p-6'):
            ui.label('Natural Language Search').classes('text-xl font-semibold mb-4')
            
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
            # Results header
            self.results_header = ui.row().classes('w-full items-center justify-between mb-4 hidden')
            with self.results_header:
                self.results_count = ui.label('').classes('text-lg font-semibold')
                
                # Sort options
                with ui.row().classes('items-center gap-2'):
                    ui.label('Sort by:').classes('text-sm')
                    self.sort_toggle = ui.toggle(
                        ['Relevance', 'Name', 'Type'],
                        value='Relevance',
                        on_change=self._sort_results
                    ).classes('text-sm')
            
            # Results container
            self.results_container = ui.column().classes('w-full gap-4')
    
    def _build_details_modal(self):
        """Build the component details modal."""
        with ui.dialog() as self.details_dialog:
            with ui.card().classes('w-full max-w-2xl'):
                self.details_content = ui.column().classes('w-full')
    
    def _switch_search_mode(self, mode: str):
        """Switch between traditional and NLP search modes."""
        if mode == 'traditional':
            self.traditional_search_container.classes(remove='hidden')
            self.nlp_search_container.classes(add='hidden')
            self.search_mode_indicator.text = 'Traditional Search Mode'
            self.current_search_type = 'text'
        elif mode == 'nlp' and self.nlp_enabled:
            self.traditional_search_container.classes(add='hidden')
            self.nlp_search_container.classes(remove='hidden')
            self.search_mode_indicator.text = 'Natural Language Mode'
            self.current_search_type = 'nlp'
    
    def _use_example_query(self, query: str):
        """Use an example query in the NLP search."""
        self.nlp_input.value = query
    
    def _on_search_type_change(self, e: events.ValueChangeEventArguments):
        """Handle search type change."""
        search_type = e.value.lower()
        self.current_search_type = search_type
        
        # Show/hide semantic weight slider for hybrid search
        if search_type == 'hybrid':
            self.semantic_weight_container.classes(remove='hidden')
        else:
            self.semantic_weight_container.classes(add='hidden')
    
    def _perform_traditional_search(self, e=None):
        """Perform traditional search."""
        query = self.search_input.value.strip() if self.search_input.value else ""
        
        if not query:
            self._load_all_components()
            return
        
        try:
            # Clear NLP response
            self.nlp_response_container.classes(add='hidden')
            
            if self.current_search_type == "text":
                results = self.db_manager.search_components(query)
            elif self.current_search_type == "semantic":
                results = self.db_manager.semantic_search(query)
            elif self.current_search_type == "hybrid":
                results = self.db_manager.hybrid_search(query, semantic_weight=self.semantic_weight)
            else:
                results = self.db_manager.search_components(query)
            
            self.search_results = results
            self._update_results()
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            ui.notify(f"Search error: {str(e)}", type='negative')
    
    def _perform_nlp_search(self, e=None):
        """Perform natural language search."""
        if not self.nlp_enabled:
            ui.notify("Natural language search is not available", type='warning')
            return
        
        query = self.nlp_input.value.strip() if self.nlp_input.value else ""
        if not query:
            return
        
        try:
            # Show loading indicator
            with self.nlp_response_container:
                self.nlp_response_container.clear()
                ui.spinner('dots', size='md').classes('mb-4')
                ui.label('Processing your query...').classes('text-gray-600')
            self.nlp_response_container.classes(remove='hidden')
            
            # Process query with LLM
            async def process_query():
                try:
                    result = self.llm_engine.process_natural_language_query(query, max_results=10)
                    
                    # Update NLP response
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
                    self.nlp_response_container.clear()
                    with self.nlp_response_container:
                        ui.label(f"Error: {str(e)}").classes('text-red-600')
            
            # Run async processing
            asyncio.create_task(process_query())
            
        except Exception as e:
            logger.error(f"NLP search error: {e}")
            ui.notify(f"Search error: {str(e)}", type='negative')
    
    def _load_all_components(self):
        """Load all components."""
        try:
            self.search_results = self.db_manager.get_all_components()
            self._update_results()
        except Exception as e:
            logger.error(f"Error loading components: {e}")
    
    def _update_results(self):
        """Update the results display."""
        # Clear results container
        self.results_container.clear()
        
        if not self.search_results:
            with self.results_container:
                ui.label('No components found.').classes('text-gray-600 text-center py-8')
            self.results_header.classes(add='hidden')
            return
        
        # Update results header
        self.results_count.text = f'Found {len(self.search_results)} components'
        self.results_header.classes(remove='hidden')
        
        # Display results as cards
        with self.results_container:
            for component in self.search_results:
                self._create_component_card(component)
    
    def _create_component_card(self, component: Dict):
        """Create a card for a component."""
        with ui.card().classes('w-full p-4 hover:shadow-lg transition-shadow cursor-pointer'):
            with ui.row().classes('w-full items-start justify-between'):
                with ui.column().classes('flex-grow'):
                    # Component name and type
                    with ui.row().classes('items-center gap-2 mb-2'):
                        ui.label(component.get('name', 'Unknown')).classes('text-lg font-semibold text-gray-800')
                        
                        # Component type badge
                        comp_type = component.get('class', component.get('type', 'Unknown'))
                        ui.badge(comp_type).classes('bg-blue-100 text-blue-800')
                        
                        # Score badge (if available)
                        if 'score' in component or 'final_score' in component:
                            score = component.get('final_score', component.get('score', 0))
                            ui.badge(f'Score: {score:.2f}').classes('bg-green-100 text-green-800')
                    
                    # Description
                    description = component.get('description', 'No description available')
                    if len(description) > 200:
                        description = description[:200] + '...'
                    ui.label(description).classes('text-gray-600 mb-2')
                    
                    # URI (if available)
                    if component.get('uri'):
                        ui.label(f"URI: {component['uri']}").classes('text-xs text-gray-500')
                
                # View details button
                ui.button('Details', 
                          on_click=lambda c=component: self._show_component_details(c)
                         ).classes('px-4 py-2')
    
    def _show_component_details(self, component: Dict):
        """Show detailed information about a component."""
        self.details_content.clear()
        
        with self.details_content:
            # Header
            with ui.row().classes('w-full items-center justify-between mb-4'):
                ui.label(component.get('name', 'Unknown Component')).classes('text-2xl font-bold')
                ui.button('Close', on_click=self.details_dialog.close).classes('px-4 py-2')
            
            # Component information
            with ui.column().classes('w-full gap-4'):
                # Basic info
                with ui.card().classes('w-full p-4'):
                    ui.label('Basic Information').classes('text-lg font-semibold mb-2')
                    
                    info_items = [
                        ('Name', component.get('name', 'N/A')),
                        ('Type', component.get('class', component.get('type', 'N/A'))),
                        ('URI', component.get('uri', 'N/A')),
                    ]
                    
                    for label, value in info_items:
                        with ui.row().classes('w-full'):
                            ui.label(f'{label}:').classes('font-medium w-20')
                            ui.label(str(value)).classes('flex-grow')
                
                # Description
                with ui.card().classes('w-full p-4'):
                    ui.label('Description').classes('text-lg font-semibold mb-2')
                    description = component.get('description', 'No description available')
                    ui.markdown(description)
                
                # Additional properties
                additional_props = {k: v for k, v in component.items() 
                                   if k not in ['name', 'class', 'type', 'uri', 'description', 'score', 'final_score']}
                
                if additional_props:
                    with ui.card().classes('w-full p-4'):
                        ui.label('Additional Properties').classes('text-lg font-semibold mb-2')
                        
                        for key, value in additional_props.items():
                            with ui.row().classes('w-full'):
                                ui.label(f'{key}:').classes('font-medium w-32')
                                ui.label(str(value)).classes('flex-grow break-all')
        
        self.details_dialog.open()
    
    def _sort_results(self, e: events.ValueChangeEventArguments):
        """Sort results based on selected criteria."""
        sort_by = e.value.lower()
        
        if sort_by == 'name':
            self.search_results.sort(key=lambda x: x.get('name', '').lower())
        elif sort_by == 'type':
            self.search_results.sort(key=lambda x: x.get('class', x.get('type', '')).lower())
        elif sort_by == 'relevance':
            # Sort by score (descending)
            self.search_results.sort(key=lambda x: x.get('final_score', x.get('score', 0)), reverse=True)
        
        self._update_results()

# Example usage function
def create_enhanced_ui(db_manager, ttl_file: str):
    """Create and return the enhanced UI instance."""
    return EnhancedROSComponentUI(db_manager, ttl_file)
