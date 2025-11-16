"""
Enhanced Frontend UI for the ROS Component Explorer with LLM Agent Integration.

This provides a web-based interface with intelligent agent capabilities including:
- Component comparison tools
- Compatibility analysis
- Sample code generation
- Natural language query processing
"""

import logging
import asyncio
from typing import List, Dict, Optional
import nicegui.ui as ui
from nicegui import events

# Import the standalone agent
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedROSComponentUI:
    """
    Enhanced UI class for the ROS Component Explorer with LLM Agent integration.
    
    Provides an intelligent interface with specialized agent tools for component
    analysis, comparison, compatibility checking, and code generation.
    """
    
    def __init__(self, db_manager, ttl_file: str = None):
        self.db_manager = db_manager
        self.ttl_file = ttl_file or "data/components_clean.ttl"
        self.search_results = []
        
        # Initialize the standalone ROS agent
        try:
            from backend.standalone_ros_agent import StandaloneROSAgent
            self.agent = StandaloneROSAgent(self.ttl_file, db_manager, None)  # Vector manager can be None for basic functionality
            self.agent_enabled = True
            logger.info("ROS Component Agent initialized successfully")
        except Exception as e:
            logger.warning(f"ROS Component Agent not available: {e}")
            self.agent = None
            self.agent_enabled = False
        
        # Initialize fallback natural language search engine
        try:
            from NLP.nlp_search_engine import NLPSearchEngine
            self.nlp_engine = NLPSearchEngine(self.ttl_file)
            self.nlp_enabled = True
            logger.info("Fallback NLP search engine initialized")
        except Exception as e:
            logger.warning(f"Fallback NLP search engine not available: {e}")
            self.nlp_engine = None
            self.nlp_enabled = False
        
        # UI components
        self.agent_input = None
        self.results_container = None
        self.agent_response_container = None
        self.tool_selector = None
        
    def build_ui(self):
        """Build the complete enhanced user interface with agent capabilities."""
        try:
            # Main container
            with ui.column().classes('w-full max-w-7xl mx-auto p-4'):
                # Header
                self._build_header()
                
                # Agent interface section
                if self.agent_enabled:
                    self._build_agent_interface()
                else:
                    self._build_fallback_interface()
                
                # Results section
                self._build_results_section()
                
                # Component details modal
                self._build_details_modal()
                
            # Auto-load all components
            self._load_all_components()
                
            logger.info("Enhanced UI with agent capabilities built successfully")
            
        except Exception as e:
            logger.error(f"Error building enhanced UI: {e}")
            raise
    
    def _build_header(self):
        """Build the application header with agent information."""
        with ui.row().classes('w-full items-center mb-6'):
            ui.icon('smart_toy', size='lg').classes('text-blue-600 mr-3')
            with ui.column().classes('flex-grow'):
                ui.label('ROS Component Explorer - AI Agent').classes('text-3xl font-bold text-gray-800')
                status_text = 'Intelligent agent with component analysis tools' if self.agent_enabled else 'Basic search functionality (agent not available)'
                ui.label(status_text).classes('text-lg text-gray-600')
    
    def _build_agent_interface(self):
        """Build the intelligent agent interface."""
        with ui.card().classes('w-full mb-6 p-6'):
            ui.label('🤖 Intelligent ROS Component Agent').classes('text-xl font-semibold mb-4')
            ui.label('Ask me to compare components, check compatibility, or generate code!').classes('text-gray-600 mb-4')
            
            # Tool selector tabs
            with ui.tabs() as tabs:
                compare_tab = ui.tab('Compare')
                compatibility_tab = ui.tab('Compatibility')
                code_tab = ui.tab('Generate Code')
                chat_tab = ui.tab('Natural Chat')
                
            with ui.tab_panels(tabs, value=compare_tab):
                # Component Comparator Tool
                with ui.tab_panel(compare_tab):
                    self._build_comparator_tool()
                
                # Compatibility Checker Tool
                with ui.tab_panel(compatibility_tab):
                    self._build_compatibility_tool()
                
                # Sample Code Generator Tool
                with ui.tab_panel(code_tab):
                    self._build_code_generator_tool()
                
                # Natural language chat
                with ui.tab_panel(chat_tab):
                    self._build_natural_chat()
            
            # Agent response container
            self.agent_response_container = ui.column().classes('w-full mt-4')
    
    def _build_comparator_tool(self):
        """Build the component comparator tool interface."""
        with ui.column().classes('w-full'):
            ui.label('Component Comparator').classes('text-lg font-semibold mb-2')
            ui.label('Compare multiple ROS components side-by-side').classes('text-gray-600 mb-4')
            
            # Example comparisons
            with ui.expansion('Example Comparisons', icon='compare_arrows').classes('mb-4'):
                examples = [
                    "AMCL,GMapping,Cartographer",
                    "Move Base,Navigation2,TEB Local Planner",
                    "Velodyne Driver,Hokuyo Driver,RPLIDAR",
                ]
                
                for example in examples:
                    with ui.row().classes('w-full mb-2 items-center'):
                        ui.label(f'• {example}').classes('flex-grow text-sm text-gray-700')
                        ui.button('Compare', 
                                  on_click=lambda e, comps=example: self._run_comparison(comps)
                                ).classes('text-xs px-2 py-1')
            
            # Component input
            with ui.row().classes('w-full gap-4 items-end'):
                self.compare_input = ui.input(
                    label='Component names (comma-separated)',
                    placeholder='e.g., AMCL,GMapping,Cartographer'
                ).classes('flex-grow')
                
                ui.button('Compare Components', 
                         on_click=lambda: self._run_comparison(self.compare_input.value)
                        ).classes('px-6 py-2')
    
    def _build_compatibility_tool(self):
        """Build the compatibility checker tool interface."""
        with ui.column().classes('w-full'):
            ui.label('Compatibility Checker').classes('text-lg font-semibold mb-2')
            ui.label('Analyze if components work well together').classes('text-gray-600 mb-4')
            
            # Example compatibility checks
            with ui.expansion('Example Compatibility Checks', icon='verified').classes('mb-4'):
                examples = [
                    "AMCL,Move Base,Velodyne Driver",
                    "GMapping,TF2,Hokuyo Driver",
                    "Cartographer,Navigation2,RPLIDAR",
                ]
                
                for example in examples:
                    with ui.row().classes('w-full mb-2 items-center'):
                        ui.label(f'• {example}').classes('flex-grow text-sm text-gray-700')
                        ui.button('Check', 
                                  on_click=lambda e, comps=example: self._check_compatibility(comps)
                                ).classes('text-xs px-2 py-1')
            
            # Component input
            with ui.row().classes('w-full gap-4 items-end'):
                self.compatibility_input = ui.input(
                    label='Component names (comma-separated)',
                    placeholder='e.g., AMCL,Move Base,Velodyne Driver'
                ).classes('flex-grow')
                
                ui.button('Check Compatibility', 
                         on_click=lambda: self._check_compatibility(self.compatibility_input.value)
                        ).classes('px-6 py-2')
    
    def _build_code_generator_tool(self):
        """Build the sample code generator tool interface."""
        with ui.column().classes('w-full'):
            ui.label('Sample Code Generator').classes('text-lg font-semibold mb-2')
            ui.label('Generate ROS 2 launch files for components').classes('text-gray-600 mb-4')
            
            # Example code generations
            with ui.expansion('Example Code Generations', icon='code').classes('mb-4'):
                examples = [
                    "AMCL",
                    "Velodyne Driver", 
                    "Cartographer",
                    "Move Base",
                ]
                
                for example in examples:
                    with ui.row().classes('w-full mb-2 items-center'):
                        ui.label(f'• {example}').classes('flex-grow text-sm text-gray-700')
                        ui.button('Generate', 
                                  on_click=lambda e, comp=example: self._generate_code(comp)
                                ).classes('text-xs px-2 py-1')
            
            # Component input
            with ui.row().classes('w-full gap-4 items-end'):
                self.code_input = ui.input(
                    label='Component name',
                    placeholder='e.g., AMCL'
                ).classes('flex-grow')
                
                ui.button('Generate Launch File', 
                         on_click=lambda: self._generate_code(self.code_input.value)
                        ).classes('px-6 py-2')
    
    def _build_natural_chat(self):
        """Build the natural language chat interface."""
        with ui.column().classes('w-full'):
            ui.label('Natural Language Chat').classes('text-lg font-semibold mb-2')
            ui.label('Ask me anything about ROS components in natural language').classes('text-gray-600 mb-4')
            
            # Example natural language queries
            with ui.expansion('Example Questions', icon='chat').classes('mb-4'):
                examples = [
                    "Compare AMCL and GMapping for indoor navigation",
                    "Can Move Base work with AMCL and Velodyne Driver?",
                    "Generate a launch file for Cartographer",
                    "What's the difference between Navigation2 and Move Base?",
                ]
                
                for example in examples:
                    with ui.row().classes('w-full mb-2 items-center'):
                        ui.label(f'• {example}').classes('flex-grow text-sm text-gray-700')
                        ui.button('Ask', 
                                  on_click=lambda e, q=example: self._process_natural_query(q)
                                ).classes('text-xs px-2 py-1')
            
            # Natural language input
            with ui.row().classes('w-full gap-4 items-end'):
                self.chat_input = ui.textarea(
                    label='Ask me anything about ROS components',
                    placeholder='e.g., "Compare AMCL and GMapping for indoor robot navigation"'
                ).classes('flex-grow min-h-20')
                
                ui.button('Ask Agent', 
                         on_click=lambda: self._process_natural_query(self.chat_input.value)
                        ).classes('px-6 py-2')
            
            ui.label('Tip: The agent will automatically choose the right tool based on your question').classes('text-xs text-gray-500 mt-1')
    
    def _build_fallback_interface(self):
        """Build fallback interface when agent is not available."""
        with ui.card().classes('w-full mb-6 p-6'):
            ui.label('⚠️ Basic Search Interface').classes('text-xl font-semibold mb-4 text-orange-600')
            ui.label('Agent functionality not available - using basic search').classes('text-gray-600 mb-4')
            
            # Basic search input
            with ui.row().classes('w-full gap-4 items-end'):
                self.basic_input = ui.input(
                    label='Search components',
                    placeholder='e.g., SLAM, navigation, localization'
                ).classes('flex-grow')
                
                ui.button('Search', 
                         on_click=lambda: self._basic_search(self.basic_input.value)
                        ).classes('px-6 py-2')
    
    def _build_results_section(self):
        """Build the results display section."""
        with ui.column().classes('w-full'):
            # Results info
            self.results_info = ui.html('<p class="text-gray-600 mb-4">All components loaded</p>')
            
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
    
    # Agent tool methods
    def _run_comparison(self, component_names_str: str):
        """Run component comparison using the agent."""
        if not self.agent_enabled or not component_names_str.strip():
            ui.notify("Please enter component names to compare", type='warning')
            return
        
        try:
            # Show loading
            self._show_loading("Comparing components...")
            
            # Process comparison
            component_names = [name.strip() for name in component_names_str.split(',')]
            result = self.agent.compare_components(component_names)
            
            # Display result
            self._display_agent_response(result, "Component Comparison Results")
            
        except Exception as e:
            logger.error(f"Error in component comparison: {e}")
            ui.notify(f"Error comparing components: {str(e)}", type='negative')
    
    def _check_compatibility(self, component_names_str: str):
        """Check component compatibility using the agent."""
        if not self.agent_enabled or not component_names_str.strip():
            ui.notify("Please enter component names to check", type='warning')
            return
        
        try:
            # Show loading
            self._show_loading("Analyzing compatibility...")
            
            # Process compatibility check
            component_names = [name.strip() for name in component_names_str.split(',')]
            result = self.agent.check_compatibility(component_names)
            
            # Display result
            self._display_agent_response(result, "Compatibility Analysis Results")
            
        except Exception as e:
            logger.error(f"Error in compatibility check: {e}")
            ui.notify(f"Error checking compatibility: {str(e)}", type='negative')
    
    def _generate_code(self, component_name: str):
        """Generate sample code using the agent."""
        if not self.agent_enabled or not component_name.strip():
            ui.notify("Please enter a component name", type='warning')
            return
        
        try:
            # Show loading
            self._show_loading("Generating launch file...")
            
            # Generate code
            result = self.agent.generate_launch_file(component_name.strip())
            
            # Display result
            self._display_agent_response(result, f"Launch File for {component_name}")
            
        except Exception as e:
            logger.error(f"Error generating code: {e}")
            ui.notify(f"Error generating code: {str(e)}", type='negative')
    
    def _process_natural_query(self, query: str):
        """Process natural language query using the agent."""
        if not self.agent_enabled or not query.strip():
            ui.notify("Please enter a question", type='warning')
            return
        
        try:
            # Show loading
            self._show_loading("Processing your question...")
            
            # Process query
            result = self.agent.process_query(query.strip())
            
            # Display result
            self._display_agent_response(result, "Agent Response")
            
        except Exception as e:
            logger.error(f"Error processing natural query: {e}")
            ui.notify(f"Error processing query: {str(e)}", type='negative')
    
    def _basic_search(self, query: str):
        """Basic search functionality when agent is not available."""
        if not query.strip():
            self._load_all_components()
            return
        
        try:
            # Use database manager for basic search
            results = self.db_manager.search_components(query.strip(), 20)
            self._display_search_results(results)
            
        except Exception as e:
            logger.error(f"Error in basic search: {e}")
            ui.notify(f"Search error: {str(e)}", type='negative')
    
    def _show_loading(self, message: str):
        """Show loading indicator."""
        self.agent_response_container.clear()
        with self.agent_response_container:
            ui.spinner('dots', size='md').classes('mb-4')
            ui.label(message).classes('text-gray-600')
    
    def _display_agent_response(self, response: str, title: str):
        """Display agent response with proper formatting."""
        self.agent_response_container.clear()
        
        with self.agent_response_container:
            with ui.card().classes('w-full p-4'):
                ui.label(title).classes('text-lg font-semibold mb-4')
                
                # Check if response contains code (launch file)
                if "#!/usr/bin/env python3" in response:
                    ui.markdown(f"```python\n{response}\n```")
                else:
                    ui.markdown(response)
                
                # Copy button for code
                if "#!/usr/bin/env python3" in response:
                    ui.button('Copy Code', 
                             on_click=lambda: ui.run_javascript(f'navigator.clipboard.writeText(`{response.replace("`", "\\`")}`)')
                            ).classes('mt-2')
    
    def _load_all_components(self):
        """Load and display all available components."""
        try:
            results = self.db_manager.search_components("*", 100)
            self._display_search_results(results)
            self.results_info.content = f'<p class="text-gray-600 mb-4">Showing {len(results)} components</p>'
            
        except Exception as e:
            logger.error(f"Error loading components: {e}")
            self.results_info.content = '<p class="text-red-600 mb-4">Error loading components</p>'
    
    def _display_search_results(self, results: List[Dict]):
        """Display search results in the UI."""
        self.results_container.clear()
        self.search_results = results
        
        if not results:
            with self.results_container:
                ui.label('No components found').classes('text-gray-500 text-center py-8')
            return
        
        # Display results as cards
        with self.results_container:
            for i, component in enumerate(results):
                self._create_component_card(component, i)
    
    def _create_component_card(self, component: Dict, index: int):
        """Create a card for displaying a component."""
        with ui.card().classes('w-full p-4 hover:shadow-lg transition-shadow cursor-pointer'):
            with ui.row().classes('w-full items-start gap-4'):
                # Component icon
                ui.icon('precision_manufacturing', size='lg').classes('text-blue-500 mt-1')
                
                # Component info
                with ui.column().classes('flex-grow'):
                    with ui.row().classes('w-full items-center gap-2'):
                        ui.label(component.get('name', 'Unknown')).classes('text-lg font-semibold')
                        if component.get('type'):
                            ui.chip(component['type'], color='blue').classes('text-xs')
                    
                    if component.get('description'):
                        description = component['description'][:150] + '...' if len(component.get('description', '')) > 150 else component['description']
                        ui.label(description).classes('text-gray-600 text-sm mb-2')
                    
                    # Component details
                    with ui.row().classes('gap-4 text-xs text-gray-500'):
                        if component.get('package'):
                            ui.label(f"📦 {component['package']}")
                        if component.get('ros_version'):
                            ui.label(f"🔧 {component['ros_version']}")
                        if component.get('update_rate'):
                            ui.label(f"⚡ {component['update_rate']} Hz")
                
                # Actions
                with ui.column().classes('gap-2'):
                    ui.button('Details', on_click=lambda c=component: self._show_details(c)).classes('text-xs px-3 py-1')
    
    def _show_details(self, component: Dict):
        """Show detailed information about a component."""
        # Update modal content
        self.details_name.content = f'<p><strong>Name:</strong> {component.get("name", "N/A")}</p>'
        self.details_type.content = f'<p><strong>Type:</strong> {component.get("type", "N/A")}</p>'
        self.details_description.content = f'<p><strong>Description:</strong> {component.get("description", "N/A")}</p>'
        self.details_package.content = f'<p><strong>Package:</strong> {component.get("package", "N/A")}</p>'
        self.details_ros_version.content = f'<p><strong>ROS Version:</strong> {component.get("ros_version", "N/A")}</p>'
        self.details_update_rate.content = f'<p><strong>Update Rate:</strong> {component.get("update_rate", "N/A")} Hz</p>'
        
        # Format topics
        sub_topics = component.get('subscribed_topics', [])
        pub_topics = component.get('published_topics', [])
        self.details_subscribed.content = f'<p><strong>Subscribed Topics:</strong> {", ".join(sub_topics) if sub_topics else "None"}</p>'
        self.details_published.content = f'<p><strong>Published Topics:</strong> {", ".join(pub_topics) if pub_topics else "None"}</p>'
        
        # Show modal
        self.details_dialog.open()


# Example usage
if __name__ == "__main__":
    # This would be used by the main application
    pass
