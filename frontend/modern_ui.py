"""
Modern ROS Package Explorer UI - Figma Design Implementation

This module implements a beautiful, modern interface matching the Figma design
from the React app. Features include:
- Clean card-based design with shadows and hover effects
- Tab navigation between Search, AI Agent, and Launch File Generator
- Modern typography and spacing
- Beautiful badges and icons
- Responsive layout
"""

import logging
from typing import List, Dict, Optional, Set
import nicegui.ui as ui
from nicegui import events

# Import the standalone agent
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModernROSExplorerUI:
    """
    Modern ROS Package Explorer UI matching the Figma design
    """
    
    def __init__(self, db_manager, ttl_file: str = None):
        self.db_manager = db_manager
        self.ttl_file = ttl_file or "data/components_clean.ttl"
        
        # State management
        self.search_term = ""
        self.selected_category = "All"
        self.selected_ros_version = "All"
        self.selected_tags = set()
        self.selected_packages = []
        self.all_packages = []
        
        # Initialize hybrid search backends
        self.solr_manager = None
        self.vector_search_manager = None
        self._init_hybrid_search()
        
        # Initialize the standalone ROS agent
        try:
            from backend.standalone_ros_agent import StandaloneROSAgent
            self.agent = StandaloneROSAgent(self.ttl_file, db_manager, None)
            self.agent_enabled = True
            logger.info("ROS Component Agent initialized successfully")
        except Exception as e:
            logger.warning(f"ROS Component Agent not available: {e}")
            self.agent = None
            self.agent_enabled = False
        
        # UI components
        self.package_container = None
        self.results_info = None
        self.agent_response_container = None
        
        # Search performance tracking
        self.last_search_latency = 0.0
        self.search_method_used = "text"
        
        # Load packages
        self._load_packages()
    
    def _load_packages(self):
        """Load packages from the database"""
        try:
            results = self.db_manager.search_components("*", 200)
            self.all_packages = results
            logger.info(f"Loaded {len(self.all_packages)} packages")
        except Exception as e:
            logger.error(f"Error loading packages: {e}")
            self.all_packages = []
    
    def _init_hybrid_search(self):
        """Initialize hybrid search backends (Solr + Vector)"""
        try:
            from backend.solr_manager import SolrManager
            logger.info("Initializing Solr backend for BM25 search...")
            self.solr_manager = SolrManager(self.ttl_file)
            logger.info("Solr backend initialized successfully")
        except Exception as e:
            logger.warning(f"Solr backend not available: {e}. Falling back to text search.")
            self.solr_manager = None
        
        try:
            from backend.vector_search_manager import VectorSearchManager
            logger.info("Initializing Vector Search backend (Sentence-BERT)...")
            self.vector_search_manager = VectorSearchManager(self.ttl_file)
            logger.info("Vector Search backend initialized successfully")
        except Exception as e:
            logger.warning(f"Vector Search backend not available: {e}. Will use text search only.")
            self.vector_search_manager = None
    
    def build_ui(self):
        """Build the modern UI interface"""
        try:
            # Add custom CSS for modern styling
            ui.add_head_html(self._get_custom_css())
            
            # Main container with modern layout
            with ui.column().classes('w-full min-h-screen bg-slate-50'):
                # Header
                self._build_header()
                
                # Main content area
                with ui.column().classes('flex-1 container mx-auto px-6 py-8 max-w-7xl'):
                    # Tab navigation - matching Figma design
                    with ui.tabs() as tabs:
                        search_tab = ui.tab('search').classes('tab-modern')
                        recommendations_tab = ui.tab('recommendations').classes('tab-modern')
                    
                    with ui.tab_panels(tabs, value=search_tab):
                        # Search Tab
                        with ui.tab_panel(search_tab):
                            self._build_search_tab()
                        
                        # Recommendations Tab
                        with ui.tab_panel(recommendations_tab).classes('w-full'):
                            self._build_recommendations_tab()
                
                # Footer
                self._build_footer()
            
            logger.info("Modern UI built successfully")
            
        except Exception as e:
            logger.error(f"Error building modern UI: {e}")
            raise
    
    def _get_custom_css(self):
        """Return custom CSS for modern styling"""
        return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            
            body {
                font-family: 'Inter', system-ui, -apple-system, sans-serif;
                background: #f8fafc;
            }
            
            .modern-header {
                background: white;
                border-bottom: 1px solid #e2e8f0;
                box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
            }
            
            .modern-card {
                background: white;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                padding: 24px;
                box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
                transition: all 0.2s ease;
            }
            
            .modern-card:hover {
                box-shadow: 0 10px 25px -5px rgb(0 0 0 / 0.1), 0 4px 6px -2px rgb(0 0 0 / 0.05);
                transform: translateY(-2px);
            }
            
            .package-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1rem;
                padding: 0;
                width: 100%;
            }
            
            .package-card {
                background: #ffffff;
                border-radius: 8px;
                border: 1px solid #e5e7eb;
                padding: 16px;
                box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
                transition: all 0.2s ease;
                cursor: pointer;
                width: 100%;
                box-sizing: border-box;
            }
            
            .package-card:hover {
                box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -1px rgb(0 0 0 / 0.06);
                transform: translateY(-1px);
                border-color: #d1d5db;
            }
            
            .package-card.selected {
                border-color: #3b82f6;
                background: #f8fafc;
                box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            }
            
            .badge {
                display: inline-flex;
                align-items: center;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
                border: none;
            }
            
            .badge-primary {
                background: #dbeafe;
                color: #1d4ed8;
            }
            
            .badge-secondary {
                background: #f3f4f6;
                color: #374151;
            }
            
            .badge-outline {
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                color: #6b7280;
            }
            
            .badge-version {
                background: #dbeafe;
                color: #1e40af;
                font-weight: 600;
            }
            
            /* Tag button animations */
            @keyframes pulse-glow {
                0%, 100% {
                    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4);
                }
                50% {
                    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
                }
            }
            
            @keyframes subtle-pulse {
                0%, 100% {
                    transform: scale(1);
                }
                50% {
                    transform: scale(1.03);
                }
            }
            
            .tag-selected {
                animation: pulse-glow 2s ease-in-out infinite;
                position: relative;
            }
            
            .tag-selected::before {
                content: '';
                position: absolute;
                top: -2px;
                left: -2px;
                right: -2px;
                bottom: -2px;
                background: linear-gradient(45deg, #3b82f6, #60a5fa, #3b82f6);
                border-radius: 9999px;
                opacity: 0.3;
                z-index: -1;
                animation: subtle-pulse 2s ease-in-out infinite;
            }
            
            .btn-modern {
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: 500;
                transition: all 0.2s ease;
                border: 1px solid transparent;
            }
            
            .btn-primary {
                background: #3b82f6;
                color: white;
            }
            
            .btn-primary:hover {
                background: #2563eb;
            }
            
            .btn-outline {
                background: transparent;
                border-color: #d1d5db;
                color: #6b7280;
            }
            
            .btn-outline:hover {
                background: #f9fafb;
                border-color: #9ca3af;
            }
            
            .tab-modern {
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 500;
                transition: all 0.2s ease;
            }
            
            .search-input {
                padding: 12px 16px;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                transition: all 0.2s ease;
            }
            
            .search-input:focus {
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgb(59 130 246 / 0.1);
            }
            
            .icon-package {
                width: 20px;
                height: 20px;
                color: #3b82f6;
            }
            
            .text-primary {
                color: #1e40af;
            }
            
            .text-secondary {
                color: #6b7280;
            }
            
            .text-muted {
                color: #9ca3af;
            }
        </style>
        """
    
    def _build_header(self):
        """Build the modern header"""
        with ui.row().classes('modern-header w-full py-6'):
            with ui.row().classes('container mx-auto px-6 items-center max-w-7xl'):
                # Logo and title
                with ui.row().classes('items-center gap-4'):
                    # Package icon
                    ui.html('<div class="p-3 bg-blue-50 rounded-lg"><svg class="icon-package" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16.5 9.4l-9-5.19M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27,6.96 12,12.01 20.73,6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg></div>')
                    
                    with ui.column().classes('gap-1'):
                        ui.html('<h1 class="text-2xl font-bold text-gray-900">ROS Package Explorer</h1>')
                        ui.html('<p class="text-secondary">Discover, explore, and generate launch files for ROS packages</p>')
    
    def _build_search_tab(self):
        """Build the search tab content - matching Figma design exactly"""
        with ui.column().classes('gap-6'):
            # Search input - prominent at top
            with ui.row().classes('w-full mb-6'):
                self.search_input = ui.input(
                    placeholder='Search packages by name or description...',
                    value=self.search_term
                ).classes('search-input flex-1 text-base')
                self.search_input.on('input', self._on_search_change)
                self.search_input.on('keydown.enter', self._perform_search)
            
            # Tag filters - matching Figma
            with ui.column().classes('mb-6'):
                ui.html('<span class="text-sm font-medium text-gray-600 mb-3">Filter by tags:</span>')
                # Container for tag buttons - will be refreshed when tags change
                self.tag_buttons_container = ui.row().classes('gap-2 flex-wrap')
                self._refresh_tag_buttons()
            
            # Results section 
            with ui.column().classes('gap-4'):
                # Results header with count
                self.results_info = ui.html('<p class="text-sm text-gray-600">Found 12 packages</p>')
                
                # Package grid - matching Figma layout
                self.package_container = ui.column().classes('gap-4')
                
            # Load initial results
            self._update_results()
    
    def _build_recommendations_tab(self):
        """Build the recommendations tab - matching Figma design"""
        with ui.column().classes('gap-6 w-full max-w-7xl mx-auto px-6'):
            # Header
            ui.html('<div class="mb-6"><h2 class="text-xl font-semibold text-gray-900 mb-2">🔍 Recommended Compatible Packages</h2><p class="text-gray-600">Based on your 2 selected packages, here are some compatible packages you might need</p></div>')
            
            # Selected packages section
            with ui.column().classes('gap-4 mb-6'):
                ui.html('<h3 class="text-lg font-semibold text-gray-900">📦 Selected Packages for Launch File</h3>')
                ui.html('<p class="text-sm text-gray-600 mb-4">Manage packages and configure parameters for your launch file</p>')
                
                # Show selected packages
                self.selected_packages_container = ui.column().classes('gap-3')
                
                # Initialize with current state
                with self.selected_packages_container:
                    if self.selected_packages:
                        self._update_selected_packages_display()
                    else:
                        ui.html('<p class="text-gray-500 text-sm">No packages selected yet. Go to Search tab to select packages.</p>')
            
            # Recommendations grid
            ui.html('<h3 class="text-lg font-semibold text-gray-900 mb-4">Recommended packages</h3>')
            self.recommendations_container = ui.column().classes('gap-4')
            
            # Initialize with some content
            with self.recommendations_container:
                if self.selected_packages:
                    self._update_recommendations()
                else:
                    ui.html('<p class="text-gray-500 text-sm">Select packages in the Search tab to see recommendations.</p>')
    
    def _build_launch_file_tab(self):
        """Build the launch file tab - matching Figma design"""  
        with ui.column().classes('gap-6 w-full max-w-7xl mx-auto px-6'):
            # Header section
            ui.html('<div class="mb-6"><h2 class="text-xl font-semibold text-gray-900 mb-2">Generate Launch File</h2><p class="text-gray-600">Configure and generate your ROS launch file</p></div>')
            
            # Selected packages section - matching the Figma design
            with ui.column().classes('gap-4 mb-6'):
                ui.html('<div class="flex items-center gap-2 mb-4"><div class="p-2 bg-orange-100 rounded-lg"><span class="text-lg">📦</span></div><h3 class="text-lg font-semibold text-gray-900">Selected Packages for Launch File</h3></div>')
                ui.html('<p class="text-sm text-gray-600 mb-4">Manage packages and configure parameters for your launch file</p>')
                
                # Container for selected packages display
                self.launch_selected_packages_container = ui.column().classes('gap-3')
                
                # Initialize with current state
                with self.launch_selected_packages_container:
                    if self.selected_packages:
                        self._update_launch_selected_packages()
                    else:
                        ui.html('<p class="text-gray-500 text-sm">No packages selected yet. Go to Search tab to select packages.</p>')
            
            # Launch file configuration
            with ui.column().classes('gap-4 mb-6'):
                ui.html('<h3 class="text-lg font-semibold text-gray-900 mb-4">Generate Launch File</h3>')
                ui.html('<p class="text-sm text-gray-600 mb-4">Configure and generate your ROS launch file</p>')
                
                with ui.row().classes('gap-6'):
                    with ui.column().classes('flex-1'):
                        ui.html('<label class="text-sm font-medium text-gray-700 mb-2">Launch File Name</label>')
                        self.launch_name_input = ui.input(value='robot_launch').classes('w-full')
                    
                    with ui.column().classes('min-w-32'):
                        ui.html('<label class="text-sm font-medium text-gray-700 mb-2">ROS Version</label>')
                        with ui.row().classes('gap-2'):
                            ui.button('ROS1', on_click=lambda: self._set_ros_version('ROS1')).classes('px-3 py-1 text-sm border rounded')
                            ui.button('ROS2', on_click=lambda: self._set_ros_version('ROS2')).classes('px-3 py-1 text-sm bg-blue-600 text-white rounded')
            
            # Generated launch file
            ui.html('<h3 class="text-lg font-semibold text-gray-900 mb-4">Generated Launch File</h3>')
            self.launch_file_container = ui.column().classes('bg-gray-50 rounded-lg p-4 w-full min-h-64')
            
            # Initialize launch file display - call method directly to populate
            self._generate_launch_file()
            
            # Action buttons
            with ui.row().classes('gap-3 mt-6'):
                ui.button('📋 Copy to Clipboard', on_click=self._copy_launch_file).classes('px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50')
                ui.button('⬇️ Download Launch File', on_click=self._download_launch_file).classes('px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800')

    def _build_agent_tab(self):
        """Build the AI agent tab content"""
        with ui.column().classes('gap-6'):
            if not self.agent_enabled:
                with ui.card().classes('modern-card text-center'):
                    ui.html('<h2 class="text-lg font-semibold mb-2 text-orange-600">⚠️ Agent Not Available</h2>')
                    ui.html('<p class="text-secondary">The AI agent is not available. Using basic functionality.</p>')
                return
            
            # Agent tools section
            with ui.card().classes('modern-card'):
                ui.html('<h2 class="text-lg font-semibold mb-4">🤖 AI Package Assistant</h2>')
                ui.html('<p class="text-secondary mb-6">Get intelligent recommendations, comparisons, and analysis for ROS packages.</p>')
                
                # Tool tabs
                with ui.tabs() as agent_tabs:
                    compare_tool = ui.tab('compare')
                    compat_tool = ui.tab('compatibility') 
                    chat_tool = ui.tab('chat')
                
                with ui.tab_panels(agent_tabs, value=compare_tool):
                    # Package Comparator
                    with ui.tab_panel(compare_tool):
                        self._build_comparator_tool()
                    
                    # Compatibility Checker
                    with ui.tab_panel(compat_tool):
                        self._build_compatibility_tool()
                    
                    # Natural Chat
                    with ui.tab_panel(chat_tool):
                        self._build_chat_tool()
            
            # Agent response area
            self.agent_response_container = ui.column().classes('gap-4')
    
    def _build_comparator_tool(self):
        """Build the component comparator tool"""
        with ui.column().classes('gap-4'):
            ui.html('<h3 class="font-semibold">Package Comparator</h3>')
            ui.html('<p class="text-secondary text-sm">Compare multiple packages side-by-side with detailed analysis.</p>')
            
            # Input and examples
            with ui.row().classes('w-full gap-4 items-end'):
                self.compare_input = ui.input(
                    label='Package names (comma-separated)',
                    placeholder='e.g., AMCL, GMapping, Cartographer'
                ).classes('flex-1')
                
                ui.button('Compare', on_click=self._run_comparison).classes('btn-modern btn-primary')
            
            # Example buttons
            with ui.row().classes('gap-2 mt-2'):
                ui.html('<span class="text-sm text-secondary">Examples:</span>')
                ui.button('AMCL,GMapping', on_click=lambda: self._set_compare_example('AMCL,GMapping')).classes('text-xs px-2 py-1 btn-outline')
                ui.button('Cartographer,andino_slam', on_click=lambda: self._set_compare_example('Cartographer,andino_slam')).classes('text-xs px-2 py-1 btn-outline')
    
    def _build_compatibility_tool(self):
        """Build the compatibility checker tool"""
        with ui.column().classes('gap-4'):
            ui.html('<h3 class="font-semibold">Compatibility Checker</h3>')
            ui.html('<p class="text-secondary text-sm">Analyze if packages work well together in your ROS system.</p>')
            
            with ui.row().classes('w-full gap-4 items-end'):
                self.compat_input = ui.input(
                    label='Package names (comma-separated)',
                    placeholder='e.g., Move Base, AMCL, Velodyne Driver'
                ).classes('flex-1')
                
                ui.button('Check Compatibility', on_click=self._check_compatibility).classes('btn-modern btn-primary')
    
    def _build_chat_tool(self):
        """Build the natural language chat tool"""
        with ui.column().classes('gap-4'):
            ui.html('<h3 class="font-semibold">Natural Language Assistant</h3>')
            ui.html('<p class="text-secondary text-sm">Ask questions about ROS packages in natural language.</p>')
            
            with ui.column().classes('w-full gap-4'):
                self.chat_input = ui.textarea(
                    label='Ask me anything about ROS packages',
                    placeholder='e.g., "What is the best localization package for outdoor robots?"'
                ).classes('min-h-20')
                
                ui.button('Ask Assistant', on_click=self._process_chat).classes('btn-modern btn-primary self-start')
    
    def _build_launch_tab(self):
        """Build the launch file generator tab"""
        with ui.column().classes('gap-6'):
            # Selected packages section
            with ui.card().classes('modern-card'):
                ui.html('<h2 class="text-lg font-semibold mb-4">Launch File Generator</h2>')
                ui.html('<p class="text-secondary mb-4">Generate ROS 2 launch files for your selected packages.</p>')
                
                if not self.selected_packages:
                    ui.html('<p class="text-muted text-center py-8">Select packages from the Search tab to generate launch files.</p>')
                else:
                    # Selected packages list
                    ui.html('<h3 class="font-medium mb-2">Selected Packages:</h3>')
                    for pkg in self.selected_packages:
                        with ui.row().classes('items-center gap-2 p-2 bg-gray-50 rounded'):
                            ui.html(f'<span class="font-medium">{pkg.get("name", "Unknown")}</span>')
                            ui.button('Remove', on_click=lambda p=pkg: self._remove_package(p)).classes('text-xs btn-outline')
                    
                    ui.button('Generate Launch File', on_click=self._generate_launch_files).classes('btn-modern btn-primary mt-4')
    
    def _build_footer(self):
        """Build the footer"""
        with ui.row().classes('w-full border-t bg-white py-6 mt-12'):
            with ui.row().classes('container mx-auto px-6 justify-center max-w-7xl'):
                ui.html('<p class="text-sm text-secondary">ROS Package Explorer - Simplifying ROS package management and launch file generation</p>')
    
    # Event handlers
    def _on_search_change(self, e):
        """Handle search input change"""
        try:
            self.search_term = e.value if e and hasattr(e, 'value') else ""
            logger.info(f"Search term changed to: '{self.search_term}'")
            # Trigger real-time search as user types
            self._update_results()
        except Exception as ex:
            logger.error(f"Error in search change: {ex}")
    
    def _on_category_change(self, e):
        """Handle category filter change"""
        try:
            self.selected_category = e.value if e and hasattr(e, 'value') else "All"
            logger.info(f"Category changed to: '{self.selected_category}'")
            self._update_results()
        except Exception as ex:
            logger.error(f"Error in category change: {ex}")
    
    def _on_ros_version_change(self, e):
        """Handle ROS version filter change"""
        try:
            self.selected_ros_version = e.value if e and hasattr(e, 'value') else "All"
            logger.info(f"ROS version changed to: '{self.selected_ros_version}'")
            self._update_results()
        except Exception as ex:
            logger.error(f"Error in ROS version change: {ex}")
    
    def _perform_search(self, e=None):
        """Perform package search"""
        try:
            # Update search term from the input field if event is provided
            if e and hasattr(e, 'sender') and hasattr(e.sender, 'value'):
                self.search_term = e.sender.value
            elif hasattr(self, 'search_input') and hasattr(self.search_input, 'value'):
                self.search_term = self.search_input.value
            
            logger.info(f"Performing search with term: '{self.search_term}'")
            self._update_results()
        except Exception as ex:
            logger.error(f"Error in perform search: {ex}")
    
    def _update_results(self):
        """Update the package results display"""
        try:
            logger.info(f"Updating results with search_term='{self.search_term}'")
            
            # Filter packages based on search criteria
            filtered_packages = self._filter_packages()
            
            # Update results info with better formatting
            count = len(filtered_packages)
            selected_count = len(self.selected_packages)
            
            logger.info(f"Filtered {count} packages from {len(self.all_packages)} total")
            
            # Build info HTML with search method and latency
            info_html = f'<div class="flex items-center justify-between mb-4">'
            info_html += f'<div class="flex items-center gap-4">'
            info_html += f'<p class="text-sm text-gray-600">Found {count} package{"s" if count != 1 else ""}</p>'
            info_html += f'<span class="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">'
            info_html += f'Method: <strong>{self.search_method_used}</strong> ({self.last_search_latency:.0f}ms)'
            info_html += f'</span>'
            info_html += f'</div>'
            if selected_count > 0:
                info_html += f'<span class="bg-black text-white px-3 py-1 rounded-full text-sm font-medium">{selected_count} package{"s" if selected_count != 1 else ""} selected</span>'
            info_html += '</div>'
            
            if hasattr(self, 'results_info') and self.results_info:
                self.results_info.content = info_html
            else:
                logger.warning("results_info not available for update")
            
            # Clear and rebuild package cards
            if hasattr(self, 'package_container') and self.package_container:
                self.package_container.clear()
            else:
                logger.error("package_container not available!")
            
            if not filtered_packages:
                with self.package_container:
                    ui.html('<div class="text-center py-12 text-muted">No packages found matching your search criteria.</div>')
                return
            
            # Create package grid
            with self.package_container:
                # Use CSS Grid for side-by-side layout
                with ui.element('div').classes('package-grid'):
                    for pkg in filtered_packages[:20]:  # Limit to 20 results
                        self._create_package_card(pkg)
        
        except Exception as e:
            logger.error(f"Error updating results: {e}")
            self.results_info.content = '<p class="text-red-500">Error loading packages</p>'
    
    def _filter_packages(self) -> List[Dict]:
        """Filter packages based on search term and tags - hybrid search for typed queries, text search for tags"""
        import time
        start_time = time.time()
        
        try:
            # Build search components
            has_search_term = self.search_term and self.search_term.strip()
            has_tags = bool(self.selected_tags)
            
            # No filters - return all packages
            if not has_search_term and not has_tags:
                filtered_packages = self.all_packages.copy()
                self.search_method_used = "no_filters"
                logger.info(f"No filters, showing all {len(filtered_packages)} packages")
                self.last_search_latency = (time.time() - start_time) * 1000
                logger.info(f"Search completed in {self.last_search_latency:.2f}ms")
                return filtered_packages
            
            # Use hybrid search ONLY when user types in search box
            if has_search_term:
                query = self.search_term.strip()
                logger.info(f"User typed search term: '{query}'")
                
                # Add tags to enhance the query if present
                if has_tags:
                    query = f"{query} {' '.join(self.selected_tags)}"
                    logger.info(f"Enhanced with tags: {self.selected_tags}")
                
                # Use vector semantic search for typed queries (best overall performance)
                try:
                    if self.solr_manager and hasattr(self.solr_manager, 'semantic_search'):
                        # Reuse existing vector_search_manager (already loaded at startup!)
                        if not hasattr(self, 'vector_search_manager') or self.vector_search_manager is None:
                            logger.warning("Vector search manager not available, falling back to text search")
                            raise Exception("No vector search manager")
                        
                        query_vector = self.vector_search_manager.vector_generator.model.encode(
                            [query], convert_to_numpy=True
                        )[0].tolist()
                        
                        # Use k=30 for reasonable performance
                        filtered_packages = self.solr_manager.semantic_search(
                            query_vector=query_vector,
                            k=30
                        )
                        self.search_method_used = "vector_semantic"
                        logger.info(f"Vector semantic search returned {len(filtered_packages)} packages")
                    else:
                        # Fallback to text search
                        solr_query = f"(content:*{query}* OR name:*{query}* OR type:*{query}*)"
                        filtered_packages = self.db_manager.search_components(solr_query, max_results=200)
                        self.search_method_used = "text_search"
                        logger.info(f"Text search returned {len(filtered_packages)} packages")
                except Exception as search_error:
                    logger.warning(f"Hybrid search failed, falling back to text: {search_error}")
                    solr_query = f"(content:*{query}* OR name:*{query}* OR type:*{query}*)"
                    filtered_packages = self.db_manager.search_components(solr_query, max_results=200)
                    self.search_method_used = "text_fallback"
                    logger.info(f"Text search (fallback) returned {len(filtered_packages)} packages")
            
            # Tag-only filtering: Use fast text-based Solr query (previous behavior)
            elif has_tags:
                logger.info(f"Tag-only filter: {self.selected_tags}")
                # Build OR query for tags (match ANY tag)
                tag_queries = [f"(content:*{tag}* OR name:*{tag}* OR type:*{tag}*)" for tag in self.selected_tags]
                solr_query = " OR ".join(tag_queries)
                
                filtered_packages = self.db_manager.search_components(solr_query, max_results=200)
                self.search_method_used = "tag_filter"
                logger.info(f"Tag filter returned {len(filtered_packages)} packages")
            
            self.last_search_latency = (time.time() - start_time) * 1000
            logger.info(f"Search completed in {self.last_search_latency:.2f}ms")
            
            return filtered_packages
            
        except Exception as e:
            logger.error(f"Error in _filter_packages: {e}")
            import traceback
            traceback.print_exc()
            return self.all_packages or []
    
    def _apply_category_and_version_filters_no_tags(self, packages: List[Dict]) -> List[Dict]:
        """Apply category and ROS version filters (WITHOUT tag filtering - tags are handled via hybrid search)"""
        try:
            # Apply category filter
            if self.selected_category != 'All':
                logger.info(f"Filtering by category: '{self.selected_category}'")
                category_mapping = {
                    'Navigation': ['NavigationComponent', 'PlanningComponent', 'PathPlannerComponent'],
                    'Perception': ['PerceptionComponent', 'VisionComponent'],
                    'Localization': ['LocalizationComponent', 'SLAMComponent'],
                    'Manipulation': ['ManipulationComponent'],
                    'Simulation': ['SimulationComponent'],
                    'SLAM': ['SLAMComponent', 'LocalizationComponent'],
                    'Core': ['CoreComponent']
                }
                
                if self.selected_category in category_mapping:
                    valid_types = category_mapping[self.selected_category]
                    filtered_packages = []
                    for pkg in packages:
                        pkg_type = pkg.get('type', [])
                        if isinstance(pkg_type, list):
                            if any(ptype in valid_types for ptype in pkg_type):
                                filtered_packages.append(pkg)
                        elif str(pkg_type) in valid_types:
                            filtered_packages.append(pkg)
                    packages = filtered_packages
                    logger.info(f"After category filter: {len(packages)} packages")
            
            # Apply ROS version filter
            if self.selected_ros_version != 'All':
                logger.info(f"Filtering by ROS version: '{self.selected_ros_version}'")
                filtered_packages = []
                for pkg in packages:
                    ros_version = pkg.get('ros_version', [])
                    if isinstance(ros_version, list):
                        version_str = ' '.join(str(v) for v in ros_version)
                    else:
                        version_str = str(ros_version)
                    
                    if self.selected_ros_version in version_str:
                        filtered_packages.append(pkg)
                packages = filtered_packages
                logger.info(f"After ROS version filter: {len(packages)} packages")
            
            return packages
        except Exception as e:
            logger.error(f"Error applying category/version filters: {e}")
            return packages
    
    def _apply_category_and_version_filters(self, packages: List[Dict]) -> List[Dict]:
        """Apply category, ROS version, and tag filters to package list"""
        try:
            # Apply category filter
            if self.selected_category != 'All':
                logger.info(f"Filtering by category: '{self.selected_category}'")
                category_mapping = {
                    'Navigation': ['NavigationComponent', 'PlanningComponent', 'PathPlannerComponent'],
                    'Perception': ['PerceptionComponent', 'VisionComponent'],
                    'Localization': ['LocalizationComponent', 'SLAMComponent'],
                    'Manipulation': ['ManipulationComponent'],
                    'Simulation': ['SimulationComponent'],
                    'SLAM': ['SLAMComponent', 'LocalizationComponent'],
                    'Core': ['CoreComponent']
                }
                
                if self.selected_category in category_mapping:
                    valid_types = category_mapping[self.selected_category]
                    filtered_packages = []
                    for pkg in packages:
                        pkg_type = pkg.get('type', [])
                        if isinstance(pkg_type, list):
                            if any(ptype in valid_types for ptype in pkg_type):
                                filtered_packages.append(pkg)
                        elif str(pkg_type) in valid_types:
                            filtered_packages.append(pkg)
                    packages = filtered_packages
                    logger.info(f"After category filter: {len(packages)} packages")
            
            # Apply ROS version filter
            if self.selected_ros_version != 'All':
                logger.info(f"Filtering by ROS version: '{self.selected_ros_version}'")
                filtered_packages = []
                for pkg in packages:
                    ros_version = pkg.get('ros_version', [])
                    if isinstance(ros_version, list):
                        version_str = ' '.join(str(v) for v in ros_version)
                    else:
                        version_str = str(ros_version)
                    
                    if self.selected_ros_version in version_str:
                        filtered_packages.append(pkg)
                packages = filtered_packages
                logger.info(f"After ROS version filter: {len(packages)} packages")
            
            # Apply tag filter (search selected tags in package names, descriptions, and types)
            if self.selected_tags:
                logger.info(f"Filtering by tags: {self.selected_tags}")
                import re
                filtered_packages = []
                for pkg in packages:
                    pkg_name = self._pkg_name(pkg).lower()
                    pkg_desc = str(pkg.get('description', '')).lower()
                    pkg_type_str = str(pkg.get('type', '')).lower()
                    combined_text = f"{pkg_name} {pkg_desc} {pkg_type_str}"
                    
                    # Check if any selected tag appears as a word in the package data
                    # Use word boundaries to avoid false matches (e.g., 'navigation' matching 'navigator')
                    matched = False
                    for tag in self.selected_tags:
                        tag_pattern = r'\b' + re.escape(tag.lower()) + r'\b'
                        if re.search(tag_pattern, combined_text):
                            filtered_packages.append(pkg)
                            matched = True
                            logger.debug(f"Package '{pkg_name}' matched tag '{tag}'")
                            break
                    
                    if not matched:
                        # Fallback to substring match for tags with hyphens or special patterns
                        for tag in self.selected_tags:
                            if tag.lower() in combined_text:
                                filtered_packages.append(pkg)
                                logger.debug(f"Package '{pkg_name}' matched tag '{tag}' (substring)")
                                break
                
                packages = filtered_packages
                logger.info(f"After tag filter: {len(packages)} packages")
            
            return packages
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            return packages
    
    def _create_package_card(self, pkg: Dict):
        """Create a package card matching Figma design exactly"""
        is_selected = any(p.get('id') == pkg.get('id') for p in self.selected_packages)
        
        with ui.card().classes('package-card'):
            # Header with package name and version
            with ui.row().classes('items-start justify-between mb-3'):
                # Package icon and name
                with ui.row().classes('items-center gap-3'):
                    ui.html('<div class="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center"><svg class="w-5 h-5 text-gray-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16.5 9.4l-9-5.19M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path></svg></div>')
                    
                    with ui.column().classes('gap-1'):
                        pkg_name = self._pkg_name(pkg)
                        # Get repository URL for hyperlink
                        repo_url = pkg.get('repository_url', '')
                        if isinstance(repo_url, list) and len(repo_url) > 0:
                            repo_url = repo_url[0]
                        
                        # Make package name a hyperlink if repo URL exists
                        if repo_url and repo_url != '' and repo_url != 'None':
                            ui.link(pkg_name, repo_url, new_tab=True).classes('font-semibold text-gray-900 text-base hover:text-blue-600')
                        else:
                            ui.html(f'<h3 class="font-semibold text-gray-900 text-base">{pkg_name}</h3>')
                        
                        # Version badge - use actual package version
                        version = pkg.get('package_version', 'Unknown')
                        if isinstance(version, list):
                            version = version[0] if version else 'Unknown'
                        if version and version != 'Unknown':
                            ui.html(f'<span class="badge badge-version">{version}</span>')
                
                # Add button
                button_text = '+ Add' if not is_selected else '✓ Add'  
                button_class = 'px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700' if not is_selected else 'px-3 py-1 text-sm bg-green-600 text-white rounded'
                ui.button(button_text, on_click=lambda p=pkg: self._toggle_package_selection(p)).classes(button_class)
            
            # Description - handle safely in case it's a list
            description = pkg.get('description', 'The navigation stack provides path planning, localization, and obstacle avoidance capabilities for mobile robots.')
            if isinstance(description, list):
                description = ' '.join(str(d) for d in description) if description else 'No description available.'
            else:
                description = str(description) if description else 'No description available.'
                
            if len(description) > 100:
                description = description[:97] + '...'
            ui.html(f'<p class="text-sm text-gray-600 mb-4">{description}</p>')
            
            # Package metadata in grid format - matching Figma exactly
            with ui.grid(columns=2).classes('gap-y-3 gap-x-6 text-sm'):
                # Category
                ui.html('<div><span class="text-gray-500">Category:</span></div>')
                category = pkg.get('type', 'Navigation')
                category = pkg.get('type', 'Navigation')
                if isinstance(category, list):
                    category = category[0] if category else 'Navigation'
                ui.html(f'<div class="font-medium text-gray-900">{category}</div>')
                
                # License (Solr returns as list)
                ui.html('<div><span class="text-gray-500">License:</span></div>')
                license_text = pkg.get('license', ['BSD'])
                if isinstance(license_text, list) and len(license_text) > 0:
                    license_text = license_text[0]
                elif not license_text:
                    license_text = 'Unknown'
                ui.html(f'<div class="font-medium text-gray-900">{license_text}</div>')
                
                # Maintainer (Solr returns as list)
                ui.html('<div><span class="text-gray-500">Maintainer:</span></div>')
                maintainer = pkg.get('author', ['Unknown'])
                if isinstance(maintainer, list) and len(maintainer) > 0:
                    maintainer = maintainer[0]
                elif not maintainer:
                    maintainer = 'Unknown'
                
                # Extract name and email if present
                maintainer_name = maintainer
                maintainer_email = None
                if '<' in maintainer and '>' in maintainer:
                    maintainer_name = maintainer.split('<')[0].strip()
                    maintainer_email = maintainer.split('<')[1].split('>')[0].strip()
                
                # Truncate long names
                if len(maintainer_name) > 30:
                    maintainer_name = maintainer_name[:30] + '...'
                
                # Create hyperlink with email if available
                with ui.element('div').classes('font-medium text-gray-900'):
                    if maintainer_email:
                        ui.link(maintainer_name, f'mailto:{maintainer_email}').classes('text-gray-900 hover:text-blue-600')
                    else:
                        ui.label(maintainer_name)
                
                # ROS Version
                ui.html('<div><span class="text-gray-500">ROS Version:</span></div>')
                ros_version = pkg.get('ros_version', ['ROS 2'])
                if isinstance(ros_version, list) and len(ros_version) > 0:
                    ros_version = ros_version[0]
                elif not ros_version:
                    ros_version = 'Unknown'
                ui.html(f'<div class="font-medium text-gray-900">{ros_version}</div>')
                
                # Distribution
                ui.html('<div><span class="text-gray-500">Distribution:</span></div>')
                distribution = pkg.get('distribution', ['Unknown'])
                # Debug log
                logger.debug(f"Distribution raw: {distribution}, type: {type(distribution)}")
                if isinstance(distribution, list) and len(distribution) > 0:
                    distribution = distribution[0]
                if not distribution or distribution == 'Unknown':
                    distribution = 'N/A'
                logger.debug(f"Distribution final: {distribution}")
                ui.html(f'<div class="font-medium text-gray-900">{distribution}</div>')
                
                # Last Updated
                ui.html('<div><span class="text-gray-500">Last Updated:</span></div>')
                last_updated = pkg.get('last_updated', ['Unknown'])
                logger.debug(f"Last updated raw: {last_updated}, type: {type(last_updated)}")
                if isinstance(last_updated, list) and len(last_updated) > 0:
                    last_updated = last_updated[0]
                # Format the date if it's a timestamp
                if last_updated and last_updated != 'Unknown' and 'T' in str(last_updated):
                    # Extract just the date part (YYYY-MM-DD)
                    last_updated = last_updated.split('T')[0]
                if not last_updated or last_updated == 'Unknown':
                    last_updated = 'N/A'
                logger.debug(f"Last updated final: {last_updated}")
                ui.html(f'<div class="font-medium text-gray-900">{last_updated}</div>')
            
            # Algorithms section
            algorithms = pkg.get('algorithms', [])
            if not isinstance(algorithms, list):
                algorithms = []
            if algorithms:
                ui.html('<div class="mt-3"><span class="text-sm text-gray-500">Algorithms:</span></div>')
                with ui.row().classes('gap-1 mt-1 mb-2 flex-wrap'):
                    for algo in algorithms[:4]:  # Show max 4 algorithms
                        ui.html(f'<span class="badge badge-info">{algo}</span>')
            
            # Hardware Requirements section
            required_hw = pkg.get('required_hardware', [])
            if not isinstance(required_hw, list):
                required_hw = []
            if required_hw:
                ui.html('<div class="mt-3"><span class="text-sm text-gray-500">Required Hardware:</span></div>')
                with ui.row().classes('gap-1 mt-1 mb-2 flex-wrap'):
                    for hw in required_hw[:4]:  # Show max 4 hardware items
                        ui.html(f'<span class="badge badge-warning">{hw}</span>')
            
            # Supported Hardware section
            supported_hw = pkg.get('supported_hardware', [])
            if not isinstance(supported_hw, list):
                supported_hw = []
            if supported_hw:
                ui.html('<div class="mt-3"><span class="text-sm text-gray-500">Supported Hardware:</span></div>')
                with ui.row().classes('gap-1 mt-1 mb-2 flex-wrap'):
                    for hw in supported_hw[:4]:  # Show max 4 hardware items
                        ui.html(f'<span class="badge badge-success">{hw}</span>')

            
            # Tags section
            tags = pkg.get('tags', [])
            if isinstance(tags, str):
                tags = [tags]
            elif not tags or tags is None:
                tags = []
            if not isinstance(tags, list):
                tags = []
            
            if tags:
                ui.html('<div class="mt-3"><span class="text-sm text-gray-500">Tags:</span></div>')
                with ui.row().classes('gap-1 mt-1 mb-3 flex-wrap'):
                    for tag in tags[:6]:  # Show max 6 tags
                        ui.html(f'<span class="badge badge-secondary">{tag}</span>')
            
            # Dependencies section (Solr returns as list [count])
            deps_count = pkg.get('dependencies_count', [0])
            if isinstance(deps_count, list) and len(deps_count) > 0:
                deps_count = deps_count[0]
            elif not deps_count:
                deps_count = 0
            
            # Get dependency list
            dependencies = pkg.get('dependencies', [])
            if not isinstance(dependencies, list):
                dependencies = []
            
            if deps_count > 0:
                ui.html(f'<div class="text-sm text-gray-700 font-medium mt-3">📦 {deps_count} Dependencies</div>')
                if dependencies:
                    # Show first few dependencies
                    deps_to_show = dependencies[:5]
                    deps_preview = ', '.join([dep.replace('package/', '') for dep in deps_to_show])
                    if len(dependencies) > 5:
                        deps_preview += f' ... +{len(dependencies) - 5} more'
                    ui.html(f'<div class="text-xs text-gray-500 mb-3">{deps_preview}</div>')
            
            # Action links
            with ui.row().classes('gap-4'):
                # Docs link (could be based on package name or ROS wiki)
                pkg_name = pkg.get('package', pkg.get('name', ''))
                # Handle Solr list format
                if isinstance(pkg_name, list) and len(pkg_name) > 0:
                    pkg_name = pkg_name[0]
                if pkg_name and pkg_name != 'Unknown package':
                    docs_url = f"https://wiki.ros.org/{pkg_name}"
                    ui.link('📖 Docs', docs_url, new_tab=True).classes('text-sm text-blue-600 hover:text-blue-800')
    
    def _toggle_package_selection(self, pkg: Dict):
        """Toggle package selection with improved state management"""
        pkg_id = pkg.get('id') or pkg.get('uri') or pkg.get('name')
        is_selected = any(p.get('id') == pkg_id or p.get('uri') == pkg_id or p.get('name') == pkg.get('name') 
                         for p in self.selected_packages)
        
        if is_selected:
            self.selected_packages = [p for p in self.selected_packages 
                                    if not (p.get('id') == pkg_id or p.get('uri') == pkg_id or p.get('name') == pkg.get('name'))]
            ui.notify(f"Removed {pkg.get('name', 'package')} from selection", type='warning')
        else:
            self.selected_packages.append(pkg)
            ui.notify(f"Added {pkg.get('name', 'package')} to selection", type='positive')
        
        # Update all components that depend on selection
        self._update_results()
        self._refresh_other_tabs()
    
    def _remove_package(self, pkg: Dict):
        """Remove package from selection"""
        pkg_id = pkg.get('id') or pkg.get('uri') or pkg.get('name')
        self.selected_packages = [p for p in self.selected_packages 
                                if not (p.get('id') == pkg_id or p.get('uri') == pkg_id or p.get('name') == pkg.get('name'))]
        
        ui.notify(f"Removed {pkg.get('name', 'package')} from launch file", type='warning')
        
        # Update all dependent components
        self._update_results()
        self._refresh_other_tabs()
    
    def _refresh_other_tabs(self):
        """Safely refresh other tabs when selection changes"""
        try:
            # Only update if the containers exist (tabs have been visited)
            if hasattr(self, 'selected_packages_container'):
                self._update_selected_packages_display()
            if hasattr(self, 'recommendations_container'):
                self._update_recommendations()
            if hasattr(self, 'launch_selected_packages_container'):
                self._update_launch_selected_packages()
            if hasattr(self, 'launch_file_container'):
                self._generate_launch_file()
        except Exception as e:
            logger.error(f"Error refreshing tabs: {e}")
    
    def _refresh_tag_buttons(self):
        """Refresh tag button display to show selected state"""
        try:
            if not hasattr(self, 'tag_buttons_container'):
                return
            
            self.tag_buttons_container.clear()
            with self.tag_buttons_container:
                tags = ['navigation', 'slam', 'mapping', 'localization', 'simulation', 'visualization', 
                       'manipulation', 'motion-planning', 'sensors', 'control', 'perception', '3d', 'camera', 'lidar']
                
                for tag in tags:
                    is_selected = tag in self.selected_tags
                    
                    # Green background with black border for selected tags
                    if is_selected:
                        button = ui.button(tag, on_click=lambda t=tag: self._toggle_tag_filter(t))
                        button.classes('px-3 py-1 text-sm rounded-full font-bold')
                        button.style('background-color: #10b981 !important; color: white !important; border: 2px solid black !important;')
                    else:
                        button = ui.button(tag, on_click=lambda t=tag: self._toggle_tag_filter(t))
                        button.classes('px-3 py-1 text-sm rounded-full bg-gray-100 hover:bg-gray-200 text-gray-700 transition-all duration-200')
        except Exception as e:
            logger.error(f"Error refreshing tag buttons: {e}")
    
    def _toggle_tag_filter(self, tag: str):
        """Toggle tag filter"""
        if tag in self.selected_tags:
            self.selected_tags.discard(tag)
            logger.info(f"Removed tag filter: {tag}")
        else:
            self.selected_tags.add(tag)
            logger.info(f"Added tag filter: {tag}")
        
        logger.info(f"Active tag filters: {self.selected_tags}")
        self._refresh_tag_buttons()
        self._update_results()
    
    def _update_selected_packages_display(self):
        """Update the display of selected packages in recommendations tab"""
        if not hasattr(self, 'selected_packages_container'):
            return  # Container not initialized yet
            
        self.selected_packages_container.clear()
        
        if not self.selected_packages:
            with self.selected_packages_container:
                ui.html('<p class="text-gray-500 text-sm">No packages selected yet. Go to Search tab to select packages.</p>')
            return
            
        with self.selected_packages_container:
            for pkg in self.selected_packages:
                with ui.row().classes('items-center justify-between p-3 bg-gray-50 rounded-lg mb-2'):
                    with ui.row().classes('items-center gap-3'):
                        # Package icon
                        ui.html('<div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center"><svg class="w-4 h-4 text-blue-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16.5 9.4l-9-5.19M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path></svg></div>')
                        with ui.column():
                            ui.html(f'<h4 class="font-semibold text-gray-900">{pkg.get("name", "Unknown")}</h4>')
                            version = pkg.get('version', '2.6.8')
                            ui.html(f'<span class="text-sm text-gray-500">{version}</span>')
                    
                    # Only remove button, no params button
                    ui.button('🗑️', on_click=lambda p=pkg: self._remove_package(p)).classes('px-2 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600')

    def _update_launch_selected_packages(self):
        """Update the display of selected packages in launch file tab"""
        if not hasattr(self, 'launch_selected_packages_container'):
            return  # Container not initialized yet
            
        self.launch_selected_packages_container.clear()
        
        if not self.selected_packages:
            with self.launch_selected_packages_container:
                ui.html('<p class="text-gray-500 text-sm">No packages selected yet. Go to Search tab to select packages.</p>')
            return
            
        with self.launch_selected_packages_container:
            for pkg in self.selected_packages:
                with ui.row().classes('items-center justify-between p-3 bg-gray-50 rounded-lg mb-2'):
                    with ui.row().classes('items-center gap-3'):
                        # Package icon
                        ui.html('<div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center"><svg class="w-4 h-4 text-blue-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16.5 9.4l-9-5.19M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path></svg></div>')
                        with ui.column():
                            ui.html(f'<h4 class="font-semibold text-gray-900">{pkg.get("name", "Unknown")}</h4>')
                            version = pkg.get('version', '2.6.8')
                            ui.html(f'<span class="text-sm text-gray-500">{version}</span>')
                    
                    # Only remove button, no params button
                    ui.button('🗑️', on_click=lambda p=pkg: self._remove_package(p)).classes('px-2 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600')
    
    def _update_recommendations(self):
        """Update recommendations based on selected packages using TTL data"""
        if not hasattr(self, 'recommendations_container'):
            return
            
        self.recommendations_container.clear()
        
        if not self.selected_packages:
            with self.recommendations_container:
                ui.html('<p class="text-gray-500 text-sm">Select packages to see recommendations.</p>')
            return
        
        # Generate TTL-based recommendations
        try:
            recommendations = self._generate_intelligent_recommendations()
            
            if not recommendations:
                with self.recommendations_container:
                    ui.html('<div class="p-4 bg-yellow-50 rounded-lg border border-yellow-200"><p class="text-yellow-700 text-sm">No compatible packages found in the knowledge base for your current selection.</p></div>')
                return
            
            with self.recommendations_container:
                ui.html(f'<p class="text-sm text-gray-600 mb-4">Found {len(recommendations)} compatible packages based on categories, topics, and dependencies:</p>')
                with ui.grid(columns=2).classes('gap-4'):
                    for pkg in recommendations[:4]:  # Show top 4 recommendations
                        self._create_recommendation_card(pkg)
                        
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            with self.recommendations_container:
                ui.html('<div class="p-4 bg-red-50 rounded-lg border border-red-200"><p class="text-red-700 text-sm">Error generating recommendations. Please try again.</p></div>')
    
    def _create_recommendation_card(self, pkg: Dict):
        """Create a recommendation card using TTL data"""
        with ui.card().classes('package-card'):
            with ui.row().classes('items-start justify-between mb-3'):
                with ui.row().classes('items-center gap-3'):
                    ui.html('<div class="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center"><svg class="w-4 h-4 text-gray-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16.5 9.4l-9-5.19M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path></svg></div>')
                    with ui.column():
                        ui.html(f'<h3 class="font-semibold text-gray-900">{pkg["name"]}</h3>')
                        ui.html(f'<span class="badge badge-version">{pkg.get("version", "1.0.0")}</span>')
                
                ui.button('+ Add', on_click=lambda p=pkg: self._add_recommendation(p)).classes('px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700')
            
            ui.html(f'<p class="text-sm text-gray-600 mb-3">{pkg["description"]}</p>')
            
            # Show category and compatibility score
            with ui.row().classes('gap-4 text-sm mb-2'):
                ui.html(f'<span><span class="text-gray-500">Category:</span> <span class="font-medium">{pkg["category"]}</span></span>')
                ui.html(f'<span><span class="text-gray-500">License:</span> <span class="font-medium">{pkg.get("license", "BSD")}</span></span>')
            
            # Show compatibility indicator
            if pkg.get('score', 0) > 10:
                ui.html('<div class="flex items-center gap-1 text-green-600 text-xs"><span class="w-2 h-2 bg-green-500 rounded-full"></span>Highly Compatible</div>')
            elif pkg.get('score', 0) > 5:
                ui.html('<div class="flex items-center gap-1 text-blue-600 text-xs"><span class="w-2 h-2 bg-blue-500 rounded-full"></span>Compatible</div>')
            else:
                ui.html('<div class="flex items-center gap-1 text-gray-600 text-xs"><span class="w-2 h-2 bg-gray-400 rounded-full"></span>Related</div>')
    
    def _generate_intelligent_recommendations(self):
        """Generate intelligent recommendations based on selected packages using TTL data"""
        try:
            if not self.selected_packages or not self.all_packages:
                logger.info("No selected packages or all_packages data available")
                return self._get_fallback_recommendations()
            
            recommendations = []
            selected_names = [self._pkg_name(pkg).lower() for pkg in self.selected_packages]
            
            # Get categories and topics from selected packages
            selected_categories = set()
            selected_topics = set()
            selected_packages_set = set()
            
            for pkg in self.selected_packages:
                selected_packages_set.add(self._pkg_name(pkg).lower())
                
                # Extract categories
                pkg_type = pkg.get('type', '')
                if isinstance(pkg_type, list):
                    selected_categories.update([t.lower() for t in pkg_type])
                elif pkg_type:
                    selected_categories.add(str(pkg_type).lower())
                
                # Extract topics
                pub_topics = pkg.get('published_topics', [])
                sub_topics = pkg.get('subscribed_topics', [])
                if isinstance(pub_topics, list):
                    selected_topics.update([t.lower() for t in pub_topics])
                if isinstance(sub_topics, list):
                    selected_topics.update([t.lower() for t in sub_topics])
            
            # Score packages based on similarity to selected packages
            scored_packages = []
            
            for pkg in self.all_packages:
                pkg_name = self._pkg_name(pkg).lower()
                
                # Skip if already selected
                if pkg_name in selected_packages_set:
                    continue
                
                score = 0
                
                # Score based on category similarity
                pkg_type = pkg.get('type', '')
                pkg_categories = set()
                if isinstance(pkg_type, list):
                    pkg_categories.update([str(t).lower() for t in pkg_type])
                elif pkg_type:
                    pkg_categories.add(str(pkg_type).lower())
                
                # High score for same category
                category_overlap = selected_categories.intersection(pkg_categories)
                score += len(category_overlap) * 10
                
                # Score based on topic compatibility (complementary topics)
                pkg_pub_topics = pkg.get('published_topics', [])
                pkg_sub_topics = pkg.get('subscribed_topics', [])
                
                pkg_topics = set()
                if isinstance(pkg_pub_topics, list):
                    pkg_topics.update([t.lower() for t in pkg_pub_topics])
                if isinstance(pkg_sub_topics, list):
                    pkg_topics.update([t.lower() for t in pkg_sub_topics])
                
                # Score for topic overlap (compatible packages often share topics)
                topic_overlap = selected_topics.intersection(pkg_topics)
                score += len(topic_overlap) * 5
                
                # Score based on package name similarity (common prefixes/suffixes)
                for selected_name in selected_names:
                    if any(keyword in pkg_name for keyword in ['nav', 'slam', 'mapping', 'localization', 'perception', 'vision', 'control', 'planning']):
                        if any(keyword in selected_name for keyword in ['nav', 'slam', 'mapping', 'localization', 'perception', 'vision', 'control', 'planning']):
                            score += 3
                
                # Boost score for commonly used packages
                if any(common in pkg_name for common in ['tf', 'robot_state', 'joint_state', 'sensor_msgs', 'geometry_msgs']):
                    score += 2
                
                if score > 0:
                    scored_packages.append((score, pkg))
            
            # Sort by score and take top recommendations
            scored_packages.sort(key=lambda x: x[0], reverse=True)
            
            # Convert to recommendation format
            for score, pkg in scored_packages[:8]:  # Top 8 recommendations
                # Handle description safely - it might be a list or string
                description = pkg.get('description', 'No description available.')
                if isinstance(description, list):
                    description = ' '.join(str(d) for d in description) if description else 'No description available.'
                else:
                    description = str(description) if description else 'No description available.'
                
                # Truncate description
                if len(description) > 100:
                    description = description[:97] + '...'
                
                # Handle Solr list format for license
                license_val = pkg.get('license', ['BSD'])
                if isinstance(license_val, list) and len(license_val) > 0:
                    license_val = license_val[0]
                elif not license_val:
                    license_val = 'Unknown'
                
                recommendations.append({
                    'name': pkg.get('name', 'Unknown'),
                    'version': pkg.get('version', '1.0.0'),
                    'description': description,
                    'category': str(pkg.get('type', 'Unknown')).replace('Component', '') if pkg.get('type') else 'Unknown',
                    'license': license_val,
                    'score': score
                })
        
            return recommendations
        
        except Exception as e:
            logger.error(f"Error generating intelligent recommendations: {e}")
            import traceback
            traceback.print_exc()
            return self._get_fallback_recommendations()
    
    def _get_fallback_recommendations(self):
        """Get fallback recommendations when TTL analysis fails"""
        return [
            {
                'name': 'tf2',
                'version': '0.25.5',
                'description': 'Transform library for tracking coordinate frames over time.',
                'category': 'Core',
                'license': 'BSD'
            },
            {
                'name': 'robot_localization',
                'version': '3.5.1',
                'description': 'Sensor fusion package for state estimation using EKF and UKF algorithms.',
                'category': 'Navigation',
                'license': 'BSD'
            },
            {
                'name': 'move_base',
                'version': '1.17.2',
                'description': 'Navigation stack for mobile robot path planning.',
                'category': 'Navigation',
                'license': 'BSD'
            },
            {
                'name': 'gmapping',
                'version': '1.4.2',
                'description': 'ROS wrapper for OpenSlam Gmapping SLAM algorithm.',
                'category': 'SLAM',
                'license': 'BSD'
            }
        ]

    def _pkg_name(self, pkg: Dict) -> str:
        """Normalize package name to a string. Handles list or string values."""
        name = pkg.get('name', '')
        if isinstance(name, list):
            # Prefer first non-empty element
            for n in name:
                if n:
                    return str(n)
            return ''
        return str(name)

    def _add_recommendation(self, pkg: Dict):
        """Add recommended package to selection"""
        # Check if already selected
        if any(p.get('name') == pkg.get('name') for p in self.selected_packages):
            ui.notify(f"{pkg.get('name')} is already selected", type='warning')
            return
            
        self.selected_packages.append(pkg)
        ui.notify(f"Added {pkg.get('name')} to selection", type='positive')
        
        # Update all dependent components
        self._update_selected_packages_display()
        self._update_recommendations()
        self._generate_launch_file()
        
    def _configure_params(self, pkg: Dict):
        """Configure package parameters"""
        pass  # Placeholder for parameter configuration
        
    def _set_ros_version(self, version: str):
        """Set ROS version for launch file"""
        self.launch_ros_version = version
        self._generate_launch_file()
        ui.notify(f"Switched to {version} launch file format", type='info')
    
    def _generate_launch_file(self):
        """Generate sophisticated launch file content based on selected packages"""
        try:
            if not hasattr(self, 'launch_file_container'):
                logger.warning("Launch file container not initialized")
                return
                
            self.launch_file_container.clear()
            
            if not self.selected_packages:
                with self.launch_file_container:
                    ui.html('<p class="text-gray-500 p-4">Select packages to generate launch file</p>')
                return
            
            logger.info(f"Generating launch file for {len(self.selected_packages)} packages")
            
            # Get launch file name
            launch_name = getattr(self, 'launch_name_input', None)
            file_name = launch_name.value if launch_name else 'robot_launch'
            
            # Generate ROS2 launch file content
            ros_version = getattr(self, 'launch_ros_version', 'ROS2')
            
            if ros_version == 'ROS2':
                launch_content = self._generate_ros2_launch_file(file_name)
            else:
                launch_content = self._generate_ros1_launch_file(file_name)
            
            # Store for copy/download
            self.current_launch_content = launch_content
        
            with self.launch_file_container:
                ui.html(f'<pre class="text-sm font-mono text-gray-800 whitespace-pre-wrap bg-white p-4 rounded-lg border overflow-x-auto max-h-96 overflow-y-auto">{launch_content}</pre>')
                
            logger.info("Launch file content generated and displayed successfully")
            
        except Exception as e:
            logger.error(f"Error generating launch file: {e}")
            with self.launch_file_container:
                ui.html(f'<p class="text-red-500 p-4">Error generating launch file: {str(e)}</p>')
    
    def _generate_ros2_launch_file(self, file_name: str):
        """Generate ROS2 launch file"""
        imports = []
        nodes = []
        
        # Add standard imports
        imports.extend([
            "from launch import LaunchDescription",
            "from launch_ros.actions import Node",
            "from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription",
            "from launch.launch_description_sources import PythonLaunchDescriptionSource",
            "from ament_index_python.packages import get_package_share_directory",
            "import os"
        ])
        
        # Generate nodes for each selected package
        for i, pkg in enumerate(self.selected_packages):
            pkg_name = pkg.get('name', f'package_{i}')
            description = pkg.get('description', f'{pkg_name} package')
            
            # Handle description safely
            if isinstance(description, list):
                description = ' '.join(str(d) for d in description) if description else f'{pkg_name} package'
            else:
                description = str(description) if description else f'{pkg_name} package'
            
            # Create node configuration based on package type
            node_config = self._generate_node_config(pkg, i)
            
            nodes.append(f"""        # {description[:80]}{'...' if len(description) > 80 else ''}
        Node(
            package='{pkg_name}',
            executable='{node_config["executable"]}',
            name='{node_config["name"]}',
            output='{node_config["output"]}',{node_config.get("parameters", "")}
        ),""")
        
        launch_content = f"""# Generated launch file: {file_name}.py
# Created by ROS Package Explorer
# Selected packages: {', '.join([self._pkg_name(p) for p in self.selected_packages])}

{chr(10).join(imports)}

def generate_launch_description():
    return LaunchDescription([
{chr(10).join(nodes)}
    ])"""
        
        return launch_content
    
    def _generate_node_config(self, pkg: Dict, index: int):
        """Generate node configuration based on package characteristics"""
        pkg_name = self._pkg_name(pkg) or f'package_{index}'
        
        # Default configuration
        config = {
            "executable": f"{pkg_name}_node",
            "name": f"{pkg_name}_{index}",
            "output": "screen"
        }
        
        # Package-specific configurations
        if 'navigation' in str(pkg_name).lower():
            config.update({
                "executable": "navigation_node",
                "parameters": "\n            parameters=[{'use_sim_time': True}],"
            })
        elif 'slam' in str(pkg_name).lower():
            config.update({
                "executable": "slam_toolbox_node", 
                "parameters": "\n            parameters=[{'use_sim_time': True, 'slam_toolbox': 'mapping'}],"
            })
        elif 'tf2' in str(pkg_name).lower():
            config.update({
                "executable": "tf2_ros_node",
                "parameters": "\n            parameters=[{'use_sim_time': True}],"
            })
        elif 'localization' in str(pkg_name).lower():
            config.update({
                "executable": "ekf_node",
                "parameters": "\n            parameters=[{'use_sim_time': True}],"
            })

        return config
    
    def _generate_ros1_launch_file(self, file_name: str):
        """Generate ROS1 launch file"""
        nodes = []
        
        # Generate nodes for each selected package
        for i, pkg in enumerate(self.selected_packages):
            pkg_name = pkg.get('name', f'package_{i}')
            description = pkg.get('description', f'{pkg_name} package')
            
            # Handle description safely
            if isinstance(description, list):
                description = ' '.join(str(d) for d in description) if description else f'{pkg_name} package'
            else:
                description = str(description) if description else f'{pkg_name} package'
            
            nodes.append(f"""  <!-- {description[:80]}{'...' if len(description) > 80 else ''} -->
  <node pkg="{pkg_name}" type="{pkg_name}_node" name="{pkg_name}_{i}" output="screen">
    <param name="use_sim_time" value="true"/>
  </node>""")
        
        launch_content = f"""<?xml version="1.0"?>
<!-- Generated launch file: {file_name}.launch -->
<!-- Created by ROS Package Explorer -->
<!-- Selected packages: {', '.join([self._pkg_name(p) for p in self.selected_packages])} -->

<launch>
{chr(10).join(nodes)}
</launch>"""
        
        return launch_content
    
    def _copy_launch_file(self):
        """Copy launch file to clipboard"""
        if hasattr(self, 'current_launch_content'):
            # Use JavaScript to copy to clipboard
            ui.run_javascript(f'''
                navigator.clipboard.writeText(`{self.current_launch_content.replace("`", "\\`")}`).then(() => {{
                    // Success handled by notification below
                }}).catch(err => {{
                    console.error('Failed to copy: ', err);
                }});
            ''')
            ui.notify("Launch file copied to clipboard!", type='positive')
        else:
            ui.notify("No launch file to copy", type='warning')
        
    def _download_launch_file(self):
        """Download launch file as Python file"""
        if hasattr(self, 'current_launch_content'):
            launch_name = getattr(self, 'launch_name_input', None)
            file_name = (launch_name.value if launch_name else 'robot_launch') + '.py'
            
            # Create download using JavaScript
            ui.run_javascript(f'''
                const content = `{self.current_launch_content.replace("`", "\\`")}`;
                const blob = new Blob([content], {{ type: 'text/plain' }});
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = '{file_name}';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            ''')
            ui.notify(f"Downloading {file_name}...", type='positive')
        else:
            ui.notify("No launch file to download", type='warning')
    
    # Agent tool methods
    def _set_compare_example(self, example: str):
        """Set example text in compare input"""
        if hasattr(self, 'compare_input'):
            self.compare_input.value = example
    
    def _run_comparison(self):
        """Run package comparison"""
        if not self.agent_enabled or not hasattr(self, 'compare_input'):
            return
        
        components = [name.strip() for name in self.compare_input.value.split(',') if name.strip()]
        if len(components) < 2:
            ui.notify("Please enter at least 2 package names", type='warning')
            return
        
        try:
            result = self.agent.compare_components(components)
            self._display_agent_response(result, "Package Comparison Results")
        except Exception as e:
            ui.notify(f"Error comparing packages: {str(e)}", type='negative')
    
    def _check_compatibility(self):
        """Check package compatibility"""
        if not self.agent_enabled or not hasattr(self, 'compat_input'):
            return
        
        components = [name.strip() for name in self.compat_input.value.split(',') if name.strip()]
        if len(components) < 2:
            ui.notify("Please enter at least 2 package names", type='warning')
            return
        
        try:
            result = self.agent.check_compatibility(components)
            self._display_agent_response(result, "Compatibility Analysis")
        except Exception as e:
            ui.notify(f"Error checking compatibility: {str(e)}", type='negative')
    
    def _process_chat(self):
        """Process natural language chat"""
        if not self.agent_enabled or not hasattr(self, 'chat_input'):
            return
        
        query = self.chat_input.value.strip()
        if not query:
            ui.notify("Please enter a question", type='warning')
            return
        
        try:
            result = self.agent.process_query(query)
            self._display_agent_response(result, "Assistant Response")
        except Exception as e:
            ui.notify(f"Error processing query: {str(e)}", type='negative')
    
    def _generate_launch_files(self):
        """Generate launch files for selected packages"""
        if not self.selected_packages:
            ui.notify("No packages selected", type='warning')
            return
        
        try:
            # For now, generate launch file for the first selected package
            first_package = self.selected_packages[0]
            package_name = first_package.get('name', 'Unknown')
            
            if self.agent_enabled:
                result = self.agent.generate_launch_file(package_name)
                self._display_agent_response(result, f"Launch File for {package_name}")
            else:
                ui.notify("Launch file generation requires the AI agent", type='warning')
                
        except Exception as e:
            ui.notify(f"Error generating launch file: {str(e)}", type='negative')
    
    def _display_agent_response(self, response: str, title: str):
        """Display agent response in a modern card"""
        self.agent_response_container.clear()
        
        with self.agent_response_container:
            with ui.card().classes('modern-card'):
                ui.html(f'<h3 class="font-semibold text-lg mb-4">{title}</h3>')
                
                # Check if response contains code
                if "#!/usr/bin/env python3" in response:
                    ui.markdown(f"```python\n{response}\n```")
                    ui.button('Copy Code', on_click=lambda: ui.run_javascript(f'navigator.clipboard.writeText(`{response.replace("`", "\\`")}`)')).classes('btn-modern btn-outline mt-4')
                else:
                    ui.markdown(response)
    
    def _matches_category(self, pkg: Dict, category: str) -> bool:
        """Check if a package matches the selected category"""
        category_mapping = {
            'Navigation': ['NavigationComponent', 'PlanningComponent', 'PathPlannerComponent'],
            'Perception': ['PerceptionComponent', 'VisionComponent'],
            'Localization': ['LocalizationComponent', 'SLAMComponent'],
            'Manipulation': ['ManipulationComponent'],
            'Simulation': ['SimulationComponent'],
            'SLAM': ['SLAMComponent', 'LocalizationComponent'],
            'Core': ['CoreComponent']
        }
        
        if category not in category_mapping:
            return True
        
        valid_types = category_mapping[category]
        pkg_type = pkg.get('type', [])
        
        if isinstance(pkg_type, list):
            return any(ptype in valid_types for ptype in pkg_type)
        else:
            return str(pkg_type) in valid_types
    
    def _matches_ros_version(self, pkg: Dict, ros_version: str) -> bool:
        """Check if a package matches the selected ROS version"""
        ros_ver = pkg.get('ros_version', [])
        
        if isinstance(ros_ver, list):
            version_str = ' '.join(str(v) for v in ros_ver)
        else:
            version_str = str(ros_ver)
        
        return ros_version in version_str


# Example usage
if __name__ == "__main__":
    pass