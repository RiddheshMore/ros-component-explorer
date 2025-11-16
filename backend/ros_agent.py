"""
LLM-Powered Agentic System for ROS Component Explorer

This module implements an intelligent agent that uses LangChain and open-source LLMs
to perform complex analysis tasks on ROS components. The agent is equipped with
specialized tools for component comparison, compatibility checking, and code generation.
"""

import logging
import os
import json
import hashlib
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# LangChain imports
from langchain.agents import AgentType, initialize_agent, Tool
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.callbacks.base import BaseCallbackHandler
from langchain_community.llms import HuggingFaceHub
from langchain_core.prompts import PromptTemplate

# ROS Component Explorer imports
from backend.solr_manager import SolrManager
from backend.vector_search_manager import VectorSearchManager

# RDF imports
import rdflib
from rdflib import Graph, Namespace, RDF, RDFS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROS = Namespace("http://www.ros.org/ontology#")
DCTERMS = Namespace("http://purl.org/dc/terms/")

class CompatibilityLevel(Enum):
    """Compatibility assessment levels"""
    HIGH = "High"
    PARTIAL_WITH_WARNINGS = "Partial with warnings"
    LOW = "Low"
    INCOMPATIBLE = "Incompatible"

@dataclass
class ComponentInfo:
    """Structured component information"""
    name: str
    uri: str
    component_type: str
    package: str
    ros_version: str
    description: str
    published_topics: List[str]
    subscribed_topics: List[str]
    services_provided: List[str]
    services_used: List[str]
    hardware_requirements: List[str]
    update_rate: Optional[float]
    repository_url: Optional[str]
    maintainer: Optional[str]
    license_type: Optional[str]
    maturity_level: Optional[str]
    accuracy: Optional[float]

@dataclass
class CompatibilityIssue:
    """Represents a compatibility issue between components"""
    severity: str  # "critical", "warning", "info"
    component1: str
    component2: str
    issue_type: str  # "ros_version_mismatch", "topic_mismatch", etc.
    description: str

@dataclass
class TopicConnection:
    """Represents a successful topic connection between components"""
    publisher: str
    subscriber: str
    topic_name: str
    message_type: str

class ROSAgentTools:
    """
    Collection of specialized tools for the ROS Component Agent
    """
    
    def __init__(self, ttl_file_path: str, solr_manager: SolrManager, vector_manager: VectorSearchManager):
        self.ttl_file_path = ttl_file_path
        self.solr_manager = solr_manager
        self.vector_manager = vector_manager
        
        # Load RDF graph for direct queries
        self.graph = Graph()
        self.graph.parse(ttl_file_path, format="turtle")
        
        logger.info("ROS Agent Tools initialized with knowledge base")
    
    def get_component_info(self, component_name: str) -> Optional[ComponentInfo]:
        """
        Retrieve comprehensive information about a ROS component
        """
        try:
            # First, search for the component by name
            search_results = self.solr_manager.search_components(component_name, max_results=5)
            
            if not search_results:
                logger.warning(f"Component '{component_name}' not found")
                return None
            
            # Find the best match (exact name match or highest score)
            best_match = None
            for result in search_results:
                if result.get('name', '').lower() == component_name.lower():
                    best_match = result
                    break
            
            if not best_match:
                best_match = search_results[0]  # Take first result if no exact match
            
            # Extract component URI for RDF queries
            component_uri = rdflib.URIRef(best_match.get('id', ''))
            
            # Get additional information from RDF graph
            rdf_info = self._extract_rdf_info(component_uri)
            
            # Merge information from Solr and RDF
            component_info = ComponentInfo(
                name=best_match.get('name', component_name),
                uri=str(component_uri),
                component_type=best_match.get('type', 'Unknown'),
                package=best_match.get('package', rdf_info.get('package', 'Unknown')),
                ros_version=best_match.get('ros_version', rdf_info.get('ros_version', 'Unknown')),
                description=best_match.get('description', rdf_info.get('description', '')),
                published_topics=best_match.get('published_topics', rdf_info.get('published_topics', [])),
                subscribed_topics=best_match.get('subscribed_topics', rdf_info.get('subscribed_topics', [])),
                services_provided=rdf_info.get('services_provided', []),
                services_used=rdf_info.get('services_used', []),
                hardware_requirements=rdf_info.get('hardware_requirements', []),
                update_rate=self._safe_float(best_match.get('update_rate', rdf_info.get('update_rate'))),
                repository_url=best_match.get('repository_url', rdf_info.get('repository_url')),
                maintainer=rdf_info.get('maintainer'),
                license_type=rdf_info.get('license_type'),
                maturity_level=rdf_info.get('maturity_level'),
                accuracy=self._safe_float(rdf_info.get('accuracy'))
            )
            
            return component_info
            
        except Exception as e:
            logger.error(f"Error retrieving component info for '{component_name}': {e}")
            return None
    
    def _extract_rdf_info(self, component_uri: rdflib.URIRef) -> Dict[str, Any]:
        """Extract additional information from RDF graph"""
        info = {}
        
        try:
            # Basic properties
            info['package'] = str(self.graph.value(component_uri, ROS.isInPackage) or
                                self.graph.value(component_uri, ROS.packageName) or "")
            info['ros_version'] = str(self.graph.value(component_uri, ROS.rosVersion) or "")
            info['description'] = str(self.graph.value(component_uri, DCTERMS.description) or "")
            info['update_rate'] = str(self.graph.value(component_uri, ROS.hasUpdateRate) or "")
            info['repository_url'] = str(self.graph.value(component_uri, ROS.repositoryURL) or "")
            info['maintainer'] = str(self.graph.value(component_uri, ROS.maintainer) or "")
            info['license_type'] = str(self.graph.value(component_uri, ROS.licenseType) or "")
            info['maturity_level'] = str(self.graph.value(component_uri, ROS.maturityLevel) or "")
            info['accuracy'] = str(self.graph.value(component_uri, ROS.hasAccuracy) or "")
            
            # Topics
            info['published_topics'] = [str(obj) for obj in self.graph.objects(component_uri, ROS.publishesTopic)]
            info['subscribed_topics'] = [str(obj) for obj in self.graph.objects(component_uri, ROS.subscribesToTopic)]
            info['services_provided'] = [str(obj) for obj in self.graph.objects(component_uri, ROS.providesService)]
            info['services_used'] = [str(obj) for obj in self.graph.objects(component_uri, ROS.usesService)]
            
            # Hardware requirements
            info['hardware_requirements'] = [str(obj) for obj in self.graph.objects(component_uri, ROS.requiresHardware)]
            
        except Exception as e:
            logger.error(f"Error extracting RDF info: {e}")
        
        return info
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        if not value:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def component_comparator_tool(self, component_names: str) -> str:
        """
        Tool 1: Component Comparator
        Performs detailed side-by-side comparison of ROS components
        
        Args:
            component_names: Comma-separated list of component names (e.g., "AMCL,GMapping,Cartographer")
        
        Returns:
            Markdown-formatted comparison report
        """
        try:
            # Parse component names
            names = [name.strip() for name in component_names.split(',')]
            
            if len(names) < 2:
                return "Error: Please provide at least 2 component names for comparison."
            
            # Retrieve component information
            components = []
            for name in names:
                component_info = self.get_component_info(name)
                if component_info:
                    components.append(component_info)
                else:
                    logger.warning(f"Could not find component: {name}")
            
            if len(components) < 2:
                return f"Error: Could only find information for {len(components)} out of {len(names)} components."
            
            # Generate comparison
            return self._generate_comparison_markdown(components)
            
        except Exception as e:
            logger.error(f"Error in component comparator: {e}")
            return f"Error performing component comparison: {str(e)}"
    
    def compatibility_checker_tool(self, component_names: str) -> str:
        """
        Tool 2: Compatibility Checker
        Analyzes compatibility between ROS components
        
        Args:
            component_names: Comma-separated list of component names
        
        Returns:
            Human-readable compatibility report
        """
        try:
            # Parse component names
            names = [name.strip() for name in component_names.split(',')]
            
            if len(names) < 2:
                return "Error: Please provide at least 2 component names for compatibility checking."
            
            # Retrieve component information
            components = []
            for name in names:
                component_info = self.get_component_info(name)
                if component_info:
                    components.append(component_info)
            
            if len(components) < 2:
                return f"Error: Could only find information for {len(components)} out of {len(names)} components."
            
            # Perform compatibility analysis
            compatibility_level, issues, connections = self._analyze_compatibility(components)
            
            # Generate report
            return self._generate_compatibility_report(compatibility_level, issues, connections, components)
            
        except Exception as e:
            logger.error(f"Error in compatibility checker: {e}")
            return f"Error performing compatibility analysis: {str(e)}"
    
    def sample_code_generator_tool(self, component_name: str) -> str:
        """
        Tool 3: Sample Code Generator
        Generates ROS 2 launch file for a component
        
        Args:
            component_name: Name of the ROS component
        
        Returns:
            Python code for ROS 2 launch file
        """
        try:
            # Get component information
            component_info = self.get_component_info(component_name.strip())
            
            if not component_info:
                return f"Error: Could not find component '{component_name}'"
            
            # Generate launch file code
            return self._generate_launch_file(component_info)
            
        except Exception as e:
            logger.error(f"Error in sample code generator: {e}")
            return f"Error generating launch file: {str(e)}"
    
    def _generate_comparison_markdown(self, components: List[ComponentInfo]) -> str:
        """Generate markdown comparison table and summary"""
        
        # Start with comparison table
        markdown = "# ROS Component Comparison\n\n"
        markdown += "## Comparison Table\n\n"
        
        # Table headers
        headers = ["Property"] + [comp.name for comp in components]
        markdown += "| " + " | ".join(headers) + " |\n"
        markdown += "|" + "|".join(["---"] * len(headers)) + "|\n"
        
        # Table rows
        properties = [
            ("Type", lambda c: c.component_type),
            ("Package", lambda c: c.package),
            ("ROS Version", lambda c: c.ros_version),
            ("Update Rate (Hz)", lambda c: str(c.update_rate) if c.update_rate else "N/A"),
            ("Maturity Level", lambda c: c.maturity_level or "N/A"),
            ("Accuracy", lambda c: str(c.accuracy) if c.accuracy else "N/A"),
            ("Repository", lambda c: c.repository_url or "N/A"),
            ("Published Topics", lambda c: ", ".join(c.published_topics[:3]) + ("..." if len(c.published_topics) > 3 else "")),
            ("Subscribed Topics", lambda c: ", ".join(c.subscribed_topics[:3]) + ("..." if len(c.subscribed_topics) > 3 else "")),
            ("Hardware Requirements", lambda c: ", ".join(c.hardware_requirements[:2]) + ("..." if len(c.hardware_requirements) > 2 else ""))
        ]
        
        for prop_name, prop_func in properties:
            row = [prop_name] + [prop_func(comp) for comp in components]
            markdown += "| " + " | ".join(row) + " |\n"
        
        # Add detailed descriptions
        markdown += "\n## Detailed Descriptions\n\n"
        for comp in components:
            markdown += f"### {comp.name}\n"
            markdown += f"{comp.description}\n\n"
        
        # Add summary analysis
        markdown += "## Analysis Summary\n\n"
        markdown += self._generate_comparison_summary(components)
        
        return markdown
    
    def _generate_comparison_summary(self, components: List[ComponentInfo]) -> str:
        """Generate intelligent summary of component comparison"""
        
        summary = ""
        
        # Analyze ROS versions
        ros_versions = set(comp.ros_version for comp in components)
        if len(ros_versions) > 1:
            summary += "**ROS Version Compatibility**: These components use different ROS versions which may require bridging or separate deployment.\n\n"
        
        # Analyze component types
        types = [comp.component_type for comp in components]
        if all("Localization" in t for t in types):
            summary += "**Use Case**: All components are localization-related. Consider factors like accuracy requirements, computational resources, and sensor compatibility when choosing.\n\n"
        elif all("Navigation" in t for t in types):
            summary += "**Use Case**: All components are navigation-related. Evaluate path planning algorithms, obstacle avoidance capabilities, and real-time performance requirements.\n\n"
        
        # Analyze update rates
        rates = [comp.update_rate for comp in components if comp.update_rate]
        if rates:
            max_rate = max(rates)
            min_rate = min(rates)
            if max_rate / min_rate > 5:
                summary += f"**Performance**: Significant difference in update rates ({min_rate:.1f} - {max_rate:.1f} Hz). Higher rates may provide better performance but require more computational resources.\n\n"
        
        # Topic analysis
        all_pub_topics = set()
        all_sub_topics = set()
        for comp in components:
            all_pub_topics.update(comp.published_topics)
            all_sub_topics.update(comp.subscribed_topics)
        
        common_topics = all_pub_topics.intersection(all_sub_topics)
        if common_topics:
            summary += f"**Integration**: Common topics found: {', '.join(list(common_topics)[:3])}. These components may work well together in a system.\n\n"
        
        return summary
    
    def _analyze_compatibility(self, components: List[ComponentInfo]) -> Tuple[CompatibilityLevel, List[CompatibilityIssue], List[TopicConnection]]:
        """Analyze compatibility between components"""
        
        issues = []
        connections = []
        
        # Check ROS version compatibility
        ros_versions = set(comp.ros_version for comp in components)
        if len(ros_versions) > 1:
            for comp in components:
                if comp.ros_version != list(ros_versions)[0]:
                    issues.append(CompatibilityIssue(
                        severity="critical",
                        component1=components[0].name,
                        component2=comp.name,
                        issue_type="ros_version_mismatch",
                        description=f"{components[0].name} is {components[0].ros_version} but {comp.name} is {comp.ros_version}"
                    ))
        
        # Check topic connections
        for i, comp1 in enumerate(components):
            for j, comp2 in enumerate(components):
                if i != j:
                    # Check if comp1 publishes topics that comp2 subscribes to
                    for pub_topic in comp1.published_topics:
                        if pub_topic in comp2.subscribed_topics:
                            connections.append(TopicConnection(
                                publisher=comp1.name,
                                subscriber=comp2.name,
                                topic_name=pub_topic,
                                message_type="Unknown"  # Could be enhanced with message type info
                            ))
        
        # Check for unmet subscriptions
        all_published = set()
        for comp in components:
            all_published.update(comp.published_topics)
        
        for comp in components:
            for sub_topic in comp.subscribed_topics:
                if sub_topic not in all_published:
                    issues.append(CompatibilityIssue(
                        severity="warning",
                        component1=comp.name,
                        component2="",
                        issue_type="unmet_subscription",
                        description=f"{comp.name} subscribes to {sub_topic} but no component in the list publishes it"
                    ))
        
        # Determine overall compatibility level
        critical_issues = [issue for issue in issues if issue.severity == "critical"]
        warning_issues = [issue for issue in issues if issue.severity == "warning"]
        
        if critical_issues:
            compatibility_level = CompatibilityLevel.INCOMPATIBLE if len(critical_issues) > 2 else CompatibilityLevel.LOW
        elif warning_issues:
            compatibility_level = CompatibilityLevel.PARTIAL_WITH_WARNINGS
        else:
            compatibility_level = CompatibilityLevel.HIGH
        
        return compatibility_level, issues, connections
    
    def _generate_compatibility_report(self, compatibility_level: CompatibilityLevel, 
                                     issues: List[CompatibilityIssue], 
                                     connections: List[TopicConnection],
                                     components: List[ComponentInfo]) -> str:
        """Generate human-readable compatibility report"""
        
        report = "# ROS Component Compatibility Analysis\n\n"
        
        # Overall assessment
        report += f"## Overall Compatibility: {compatibility_level.value}\n\n"
        
        # Component list
        report += "## Analyzed Components\n"
        for comp in components:
            report += f"- **{comp.name}** ({comp.component_type}) - {comp.ros_version}\n"
        report += "\n"
        
        # Issues section
        if issues:
            report += "## Compatibility Issues\n\n"
            
            critical_issues = [issue for issue in issues if issue.severity == "critical"]
            warning_issues = [issue for issue in issues if issue.severity == "warning"]
            
            if critical_issues:
                report += "### Critical Issues ❌\n"
                for issue in critical_issues:
                    report += f"- **{issue.issue_type}**: {issue.description}\n"
                report += "\n"
            
            if warning_issues:
                report += "### Warnings ⚠️\n"
                for issue in warning_issues:
                    report += f"- **{issue.issue_type}**: {issue.description}\n"
                report += "\n"
        else:
            report += "## ✅ No Compatibility Issues Found\n\n"
        
        # Connections section
        if connections:
            report += "## Successful Topic Connections\n\n"
            for conn in connections:
                report += f"- **{conn.publisher}** → **{conn.subscriber}** via `{conn.topic_name}`\n"
            report += "\n"
        
        # Recommendations
        report += "## Recommendations\n\n"
        if compatibility_level == CompatibilityLevel.HIGH:
            report += "These components should work well together. Consider testing in a simulation environment before deployment.\n"
        elif compatibility_level == CompatibilityLevel.PARTIAL_WITH_WARNINGS:
            report += "These components can work together but may require additional configuration or bridge nodes for full compatibility.\n"
        elif compatibility_level == CompatibilityLevel.LOW:
            report += "Significant compatibility issues detected. Consider alternative components or implement bridge solutions.\n"
        else:
            report += "These components are not compatible in their current configuration. Major modifications or alternatives are needed.\n"
        
        return report
    
    def _generate_launch_file(self, component_info: ComponentInfo) -> str:
        """Generate ROS 2 Python launch file for a component"""
        
        # Determine launch file parameters based on component type
        params = self._get_component_parameters(component_info)
        
        launch_code = f'''#!/usr/bin/env python3
"""
ROS 2 Launch file for {component_info.name}

This launch file starts the {component_info.name} node with common parameters.
Generated automatically by ROS Component Explorer.

Component Information:
- Name: {component_info.name}
- Type: {component_info.component_type}
- Package: {component_info.package}
- ROS Version: {component_info.ros_version}
- Description: {component_info.description[:100]}...
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration, TextSubstitution
from launch_ros.actions import Node
from launch.conditions import IfCondition, UnlessCondition


def generate_launch_description():
    """Generate launch description for {component_info.name}"""
    
    # Declare launch arguments
    declared_arguments = []
    
    # Common arguments
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="Use simulation time if true"
        )
    )
    
    declared_arguments.append(
        DeclareLaunchArgument(
            "log_level", 
            default_value="info",
            description="Log level for the node"
        )
    )
'''
        
        # Add component-specific parameters
        for param_name, default_value, description in params:
            launch_code += f'''
    declared_arguments.append(
        DeclareLaunchArgument(
            "{param_name}",
            default_value="{default_value}",
            description="{description}"
        )
    )
'''
        
        # Node configuration
        launch_code += f'''
    
    # Node configuration
    {component_info.name.lower().replace(' ', '_')}_node = Node(
        package="{component_info.package}",
        executable="{component_info.name.lower().replace(' ', '_')}_node",  # Adjust executable name as needed
        name="{component_info.name.lower().replace(' ', '_')}",
        output="screen",
        parameters=[
            {{"use_sim_time": LaunchConfiguration("use_sim_time")}},'''
        
        # Add component-specific parameters to node
        for param_name, _, _ in params:
            launch_code += f'''
            {{"{param_name}": LaunchConfiguration("{param_name}")}},'''
        
        launch_code += '''
        ],
        arguments=['--ros-args', '--log-level', LaunchConfiguration('log_level')],
        remappings=[
            # Add any necessary topic remappings here
            # Example: ('/input_topic', '/remapped_input_topic'),
        ]
    )
    
    return LaunchDescription(
        declared_arguments + [
            LogInfo(
                msg=TextSubstitution(text="Starting ''' + component_info.name + ''' node...")
            ),
            ''' + component_info.name.lower().replace(' ', '_') + '''_node,
        ]
    )


if __name__ == "__main__":
    generate_launch_description()
'''
        
        return launch_code
    
    def _get_component_parameters(self, component_info: ComponentInfo) -> List[Tuple[str, str, str]]:
        """Get component-specific launch parameters based on type"""
        
        params = []
        
        # Common parameters based on component type
        if "Localization" in component_info.component_type:
            params.extend([
                ("odom_frame_id", "odom", "Odometry frame ID"),
                ("base_frame_id", "base_link", "Base link frame ID"),
                ("global_frame_id", "map", "Global frame ID"),
                ("transform_tolerance", "0.1", "Transform tolerance in seconds"),
            ])
            
            if "AMCL" in component_info.name:
                params.extend([
                    ("min_particles", "500", "Minimum number of particles"),
                    ("max_particles", "5000", "Maximum number of particles"),
                    ("update_min_d", "0.2", "Minimum translation before update"),
                    ("update_min_a", "0.5", "Minimum rotation before update"),
                ])
        
        elif "Navigation" in component_info.component_type:
            params.extend([
                ("controller_frequency", "20.0", "Controller frequency in Hz"),
                ("planner_patience", "5.0", "Planner patience in seconds"),
                ("controller_patience", "15.0", "Controller patience in seconds"),
                ("recovery_behavior_enabled", "true", "Enable recovery behaviors"),
            ])
        
        elif "Sensor" in component_info.component_type or "Driver" in component_info.component_type:
            params.extend([
                ("frame_id", "laser", "Frame ID for sensor data"),
                ("device_ip", "192.168.1.10", "IP address of sensor device"),
                ("port", "2112", "Communication port"),
            ])
            
            if component_info.update_rate:
                params.append(("scan_frequency", str(component_info.update_rate), "Scan frequency in Hz"))
        
        elif "Perception" in component_info.component_type:
            params.extend([
                ("image_topic", "/camera/image_raw", "Input image topic"),
                ("camera_info_topic", "/camera/camera_info", "Camera info topic"),
                ("output_topic", "/detection_result", "Output detection topic"),
            ])
        
        return params


class ROSComponentAgent:
    """
    Main LLM-powered agent for ROS Component analysis
    """
    
    def __init__(self, ttl_file_path: str, solr_manager: SolrManager, 
                 vector_manager: VectorSearchManager, hf_api_token: Optional[str] = None):
        
        self.ttl_file_path = ttl_file_path
        self.solr_manager = solr_manager
        self.vector_manager = vector_manager
        self.hf_api_token = hf_api_token
        
        # Initialize tools
        self.tools_instance = ROSAgentTools(ttl_file_path, solr_manager, vector_manager)
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Define tools for the agent
        self.tools = [
            Tool(
                name="Component Comparator",
                func=self.tools_instance.component_comparator_tool,
                description="Compare multiple ROS components side-by-side. Input: comma-separated component names (e.g., 'AMCL,GMapping,Cartographer')"
            ),
            Tool(
                name="Compatibility Checker", 
                func=self.tools_instance.compatibility_checker_tool,
                description="Check compatibility between ROS components. Input: comma-separated component names"
            ),
            Tool(
                name="Sample Code Generator",
                func=self.tools_instance.sample_code_generator_tool,
                description="Generate ROS 2 launch file for a component. Input: single component name"
            )
        ]
        
        # Initialize the agent
        self.agent = initialize_agent(
            self.tools,
            self.llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True
        )
        
        logger.info("ROS Component Agent initialized successfully")
    
    def _initialize_llm(self) -> Any:
        """Initialize the LLM with fallback options"""
        
        try:
            if self.hf_api_token:
                # Try multiple models in order of preference
                models = [
                    "microsoft/DialoGPT-large",
                    "google/flan-t5-large", 
                    "facebook/blenderbot-1B-distill",
                    "microsoft/DialoGPT-medium"
                ]
                
                for model in models:
                    try:
                        llm = HuggingFaceHub(
                            repo_id=model,
                            model_kwargs={
                                "temperature": 0.7,
                                "max_new_tokens": 500,
                                "return_full_text": False
                            },
                            huggingfacehub_api_token=self.hf_api_token
                        )
                        logger.info(f"Successfully initialized LLM with model: {model}")
                        return llm
                    except Exception as e:
                        logger.warning(f"Failed to initialize {model}: {e}")
                        continue
            
            # Fallback to a simple text-based response system
            logger.warning("Using fallback text-based LLM")
            return FallbackLLM()
            
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            return FallbackLLM()
    
    def query(self, user_input: str) -> str:
        """
        Process user query using the agent
        
        Args:
            user_input: User's natural language query
            
        Returns:
            Agent's response
        """
        try:
            # Process the query through the agent
            response = self.agent.run(input=user_input)
            return response
            
        except Exception as e:
            logger.error(f"Error processing agent query: {e}")
            return f"I encountered an error while processing your request: {str(e)}. Please try rephrasing your question or use one of the specific tools directly."
    
    def get_available_tools(self) -> List[Dict[str, str]]:
        """Get information about available tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "example": self._get_tool_example(tool.name)
            }
            for tool in self.tools
        ]
    
    def _get_tool_example(self, tool_name: str) -> str:
        """Get example usage for each tool"""
        examples = {
            "Component Comparator": "Compare AMCL and GMapping localization algorithms",
            "Compatibility Checker": "Check if Move Base, AMCL, and Velodyne Driver work together", 
            "Sample Code Generator": "Generate launch file for Cartographer"
        }
        return examples.get(tool_name, "")


class FallbackLLM:
    """
    Fallback LLM implementation for when HuggingFace models are not available
    """
    
    def __call__(self, prompt: str) -> str:
        """Generate a response using template-based logic"""
        
        prompt_lower = prompt.lower()
        
        if "compare" in prompt_lower or "comparison" in prompt_lower:
            return "I can help you compare ROS components. Please use the Component Comparator tool with component names separated by commas."
        
        elif "compatible" in prompt_lower or "compatibility" in prompt_lower:
            return "I can check compatibility between ROS components. Please use the Compatibility Checker tool with the component names you want to analyze."
        
        elif "launch" in prompt_lower or "code" in prompt_lower or "generate" in prompt_lower:
            return "I can generate ROS 2 launch files. Please use the Sample Code Generator tool with a single component name."
        
        else:
            return "I can help you with ROS component analysis using these tools: Component Comparator (for comparing components), Compatibility Checker (for analyzing compatibility), and Sample Code Generator (for creating launch files). What would you like to do?"
    
    def predict(self, text: str) -> str:
        """LangChain compatibility method"""
        return self.__call__(text)


# Example usage and testing
if __name__ == "__main__":
    import os
    
    # Initialize managers (assuming they're available)
    ttl_file = "data/components_clean.ttl"
    solr_manager = SolrManager(ttl_file)
    vector_manager = VectorSearchManager(ttl_file)
    
    # Initialize agent
    hf_token = os.getenv("HUGGINGFACE_API_TOKEN")
    agent = ROSComponentAgent(ttl_file, solr_manager, vector_manager, hf_token)
    
    # Test queries
    test_queries = [
        "Compare AMCL and GMapping components",
        "Check compatibility between Move Base and AMCL", 
        "Generate launch file for Velodyne Driver"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("Response:", agent.query(query))
        print("-" * 50)