"""
Standalone ROS Component Agent - No External Dependencies

This module implements an intelligent agent for ROS component analysis
without requiring external LLM APIs. It provides three specialized tools:
1. Component Comparator - Side-by-side component analysis
2. Compatibility Checker - Component compatibility analysis  
3. Sample Code Generator - ROS 2 launch file generation
"""

import logging
import os
import json
import hashlib
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

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

class StandaloneROSAgent:
    """
    Standalone LLM-powered agent for ROS Component analysis
    Provides intelligent component analysis without external API dependencies
    """
    
    def __init__(self, ttl_file_path: str, solr_manager: SolrManager, vector_manager: VectorSearchManager):
        
        self.ttl_file_path = ttl_file_path
        self.solr_manager = solr_manager
        self.vector_manager = vector_manager
        
        # Load RDF graph for direct queries
        self.graph = Graph()
        self.graph.parse(ttl_file_path, format="turtle")
        
        logger.info("Standalone ROS Agent initialized with knowledge base")
    
    def get_component_info(self, component_name: str) -> Optional[ComponentInfo]:
        """
        Retrieve comprehensive information about a ROS component
        """
        try:
            # First, search for the component by name
            search_results = self.solr_manager.search_components(component_name, 5)
            
            if not search_results:
                logger.warning(f"Component '{component_name}' not found")
                return None
            
            # Find the best match (exact name match or highest score)
            best_match = None
            for result in search_results:
                # Handle case where name might be a list or string
                result_name = result.get('name', '')
                if isinstance(result_name, list):
                    result_name = result_name[0] if result_name else ''
                
                if str(result_name).lower() == component_name.lower():
                    best_match = result
                    break
            
            if not best_match:
                best_match = search_results[0]  # Take first result if no exact match
            
            # Extract component URI for RDF queries
            component_uri = rdflib.URIRef(best_match.get('id', ''))
            
            # Get additional information from RDF graph
            rdf_info = self._extract_rdf_info(component_uri)
            
            # Helper function to extract string from potentially list values
            def extract_string(value, default=''):
                if isinstance(value, list):
                    return value[0] if value else default
                return str(value) if value else default
            
            # Merge information from Solr and RDF
            component_info = ComponentInfo(
                name=extract_string(best_match.get('name'), component_name),
                uri=str(component_uri),
                component_type=extract_string(best_match.get('type'), 'Unknown'),
                package=extract_string(best_match.get('package'), rdf_info.get('package', 'Unknown')),
                ros_version=extract_string(best_match.get('ros_version'), rdf_info.get('ros_version', 'Unknown')),
                description=extract_string(best_match.get('description'), rdf_info.get('description', '')),
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
    
    def compare_components(self, component_names: List[str]) -> str:
        """
        Tool 1: Component Comparator
        Performs detailed side-by-side comparison of ROS components
        
        Args:
            component_names: List of component names to compare
        
        Returns:
            Markdown-formatted comparison report
        """
        try:
            if len(component_names) < 2:
                return "Error: Please provide at least 2 component names for comparison."
            
            # Retrieve component information
            components = []
            for name in component_names:
                component_info = self.get_component_info(name.strip())
                if component_info:
                    components.append(component_info)
                else:
                    logger.warning(f"Could not find component: {name}")
            
            if len(components) < 2:
                return f"Error: Could only find information for {len(components)} out of {len(component_names)} components."
            
            # Generate comparison
            return self._generate_comparison_markdown(components)
            
        except Exception as e:
            logger.error(f"Error in component comparator: {e}")
            return f"Error performing component comparison: {str(e)}"
    
    def check_compatibility(self, component_names: List[str]) -> str:
        """
        Tool 2: Compatibility Checker
        Analyzes compatibility between ROS components
        
        Args:
            component_names: List of component names to check
        
        Returns:
            Human-readable compatibility report
        """
        try:
            if len(component_names) < 2:
                return "Error: Please provide at least 2 component names for compatibility checking."
            
            # Retrieve component information
            components = []
            for name in component_names:
                component_info = self.get_component_info(name.strip())
                if component_info:
                    components.append(component_info)
            
            if len(components) < 2:
                return f"Error: Could only find information for {len(components)} out of {len(component_names)} components."
            
            # Perform compatibility analysis
            compatibility_level, issues, connections = self._analyze_compatibility(components)
            
            # Generate report
            return self._generate_compatibility_report(compatibility_level, issues, connections, components)
            
        except Exception as e:
            logger.error(f"Error in compatibility checker: {e}")
            return f"Error performing compatibility analysis: {str(e)}"
    
    def generate_launch_file(self, component_name: str) -> str:
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
    
    def process_query(self, query: str) -> str:
        """
        Process natural language queries and route to appropriate tools
        
        Args:
            query: User's natural language query
            
        Returns:
            Formatted response
        """
        query_lower = query.lower()
        
        # Parse component names from query
        components = self._extract_component_names_from_query(query)
        
        if not components:
            return self._provide_usage_help()
        
        # Route to appropriate tool based on query intent
        if any(word in query_lower for word in ["compare", "comparison", "difference", "vs", "versus"]):
            return self.compare_components(components)
        
        elif any(word in query_lower for word in ["compatible", "compatibility", "work together", "integrate"]):
            return self.check_compatibility(components)
        
        elif any(word in query_lower for word in ["launch", "code", "generate", "create file", "example"]):
            if len(components) == 1:
                return self.generate_launch_file(components[0])
            else:
                return "Sample code generation works with one component at a time. Please specify a single component."
        
        else:
            # Default to comparison if multiple components, launch file if single component
            if len(components) > 1:
                return self.compare_components(components)
            else:
                return self.generate_launch_file(components[0])
    
    def _extract_component_names_from_query(self, query: str) -> List[str]:
        """Extract component names from natural language query"""
        
        # Get list of all known components
        all_components = self._get_known_components()
        
        # Find mentioned components in the query
        mentioned_components = []
        query_lower = query.lower()
        
        for component in all_components:
            if component.lower() in query_lower:
                mentioned_components.append(component)
        
        return mentioned_components
    
    def _get_known_components(self) -> List[str]:
        """Get list of known component names from the knowledge base"""
        try:
            # Query Solr for all components
            results = self.solr_manager.search_components("*", 200)
            return [result.get('name', '') for result in results if result.get('name')]
        except Exception as e:
            logger.error(f"Error getting known components: {e}")
            return []
    
    def _provide_usage_help(self) -> str:
        """Provide usage help when no components are detected"""
        return """
# ROS Component Agent Help

I can help you analyze ROS components using three tools:

## 1. Component Comparator
Compare multiple components side-by-side:
- **Usage**: "Compare AMCL and GMapping"
- **Features**: Technical specifications, performance metrics, compatibility info

## 2. Compatibility Checker  
Analyze if components work together:
- **Usage**: "Check compatibility between Move Base, AMCL, and Velodyne Driver"
- **Features**: ROS version compatibility, topic connections, integration issues

## 3. Sample Code Generator
Generate ROS 2 launch files:
- **Usage**: "Generate launch file for Cartographer" 
- **Features**: Proper parameter configuration, documentation, best practices

## Available Components
Some components you can ask about: AMCL, GMapping, Cartographer, Move Base, Velodyne Driver, Hokuyo Driver, CV Bridge, RViz, Gazebo, TF2

## Example Queries
- "Compare AMCL and GMapping localization algorithms"
- "Can Move Base work with AMCL for navigation?"
- "Create a launch file for Velodyne Driver"
- "What's the difference between Cartographer and GMapping?"
"""
    
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


# Example usage and testing
if __name__ == "__main__":
    import sys
    import os
    
    # Add the current directory to path for imports
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Initialize managers (assuming they're available)
    ttl_file = "data/components_clean.ttl"
    
    try:
        from solr_manager import SolrManager
        from vector_search_manager import VectorSearchManager
        
        solr_manager = SolrManager(ttl_file)
        vector_manager = VectorSearchManager(ttl_file)
        
        # Initialize agent
        agent = StandaloneROSAgent(ttl_file, solr_manager, vector_manager)
        
        # Test queries
        test_queries = [
            "Compare AMCL and GMapping components",
            "Check compatibility between Move Base and AMCL", 
            "Generate launch file for Velodyne Driver",
            "What's the difference between Cartographer and GMapping?",
            "Can AMCL work with Move Base for navigation?"
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            print("Response:", agent.process_query(query))
            print("-" * 80)
            
    except ImportError as e:
        print(f"Import error: {e}")
        print("This example requires the SolrManager and VectorSearchManager to be available.")