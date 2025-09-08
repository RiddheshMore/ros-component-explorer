"""
LLM-powered Natural Language Query Processor for ROS Component Explorer.

This module enables natural language querying of the ROS component database by:
1. Parsing natural language queries to extract component requirements
2. Translating requirements into structured search parameters
3. Executing searches against the knowledge graph
4. Synthesizing results into human-readable answers
"""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComponentCategory(Enum):
    """Categories of ROS components for classification."""
    SLAM = "slam"
    LOCALIZATION = "localization"
    NAVIGATION = "navigation"
    PERCEPTION = "perception"
    SENSORS = "sensors"
    PLANNING = "planning"
    CONTROL = "control"
    SIMULATION = "simulation"
    VISUALIZATION = "visualization"
    COMMUNICATION = "communication"

class EnvironmentType(Enum):
    """Types of operating environments."""
    INDOOR = "indoor"
    OUTDOOR = "outdoor"
    MIXED = "mixed"
    UNKNOWN = "unknown"

class SensorType(Enum):
    """Types of sensors mentioned in queries."""
    LIDAR_2D = "2d_lidar"
    LIDAR_3D = "3d_lidar"
    CAMERA = "camera"
    STEREO_CAMERA = "stereo_camera"
    DEPTH_CAMERA = "depth_camera"
    IMU = "imu"
    GPS = "gps"
    ODOMETRY = "odometry"
    SONAR = "sonar"

@dataclass
class QueryRequirements:
    """Structured representation of extracted query requirements."""
    primary_function: Optional[str] = None
    categories: List[ComponentCategory] = None
    sensors: List[SensorType] = None
    environment: Optional[EnvironmentType] = None
    performance_requirements: List[str] = None
    constraints: List[str] = None
    keywords: List[str] = None
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = []
        if self.sensors is None:
            self.sensors = []
        if self.performance_requirements is None:
            self.performance_requirements = []
        if self.constraints is None:
            self.constraints = []
        if self.keywords is None:
            self.keywords = []

class NLQueryProcessor:
    """Natural Language Query Processor for ROS components."""
    
    def __init__(self):
        self.category_keywords = {
            ComponentCategory.SLAM: ["slam", "mapping", "localization and mapping", "simultaneous localization"],
            ComponentCategory.LOCALIZATION: ["localization", "localize", "position", "pose estimation"],
            ComponentCategory.NAVIGATION: ["navigation", "navigate", "path planning", "motion planning"],
            ComponentCategory.PERCEPTION: ["perception", "object detection", "recognition", "computer vision"],
            ComponentCategory.SENSORS: ["sensor", "sensing", "data acquisition"],
            ComponentCategory.PLANNING: ["planning", "path planning", "motion planning", "trajectory"],
            ComponentCategory.CONTROL: ["control", "controller", "pid", "motor control"],
            ComponentCategory.SIMULATION: ["simulation", "simulator", "gazebo", "stage"],
            ComponentCategory.VISUALIZATION: ["visualization", "visualize", "rviz", "display"],
            ComponentCategory.COMMUNICATION: ["communication", "messaging", "publisher", "subscriber"]
        }
        
        self.sensor_keywords = {
            SensorType.LIDAR_2D: ["2d lidar", "laser scanner", "2d laser", "planar lidar"],
            SensorType.LIDAR_3D: ["3d lidar", "velodyne", "3d laser", "point cloud"],
            SensorType.CAMERA: ["camera", "vision", "image"],
            SensorType.STEREO_CAMERA: ["stereo camera", "stereo vision", "binocular"],
            SensorType.DEPTH_CAMERA: ["depth camera", "rgbd", "kinect", "realsense"],
            SensorType.IMU: ["imu", "inertial", "accelerometer", "gyroscope"],
            SensorType.GPS: ["gps", "gnss", "global positioning"],
            SensorType.ODOMETRY: ["odometry", "wheel encoder", "visual odometry"],
            SensorType.SONAR: ["sonar", "ultrasonic", "range finder"]
        }
        
        self.environment_keywords = {
            EnvironmentType.INDOOR: ["indoor", "inside", "building", "room", "house"],
            EnvironmentType.OUTDOOR: ["outdoor", "outside", "field", "forest", "street", "large"],
            EnvironmentType.MIXED: ["mixed", "indoor and outdoor", "both"]
        }
        
        self.performance_keywords = [
            "best", "optimal", "fast", "efficient", "accurate", "robust", 
            "reliable", "real-time", "low latency", "high performance"
        ]
    
    def parse_query(self, query: str) -> QueryRequirements:
        """
        Parse a natural language query into structured requirements.
        
        Args:
            query: Natural language query string
            
        Returns:
            QueryRequirements object with extracted information
        """
        query_lower = query.lower()
        logger.info(f"Parsing query: {query}")
        
        requirements = QueryRequirements()
        
        # Extract primary function/purpose
        requirements.primary_function = self._extract_primary_function(query_lower)
        
        # Extract component categories
        requirements.categories = self._extract_categories(query_lower)
        
        # Extract sensor types
        requirements.sensors = self._extract_sensors(query_lower)
        
        # Extract environment type
        requirements.environment = self._extract_environment(query_lower)
        
        # Extract performance requirements
        requirements.performance_requirements = self._extract_performance_requirements(query_lower)
        
        # Extract constraints
        requirements.constraints = self._extract_constraints(query_lower)
        
        # Extract general keywords
        requirements.keywords = self._extract_keywords(query_lower)
        
        logger.info(f"Extracted requirements: {requirements}")
        return requirements
    
    def _extract_primary_function(self, query: str) -> Optional[str]:
        """Extract the primary function being requested."""
        # Look for question patterns
        if "what is the best" in query:
            # Extract what comes after "best"
            match = re.search(r"what is the best (.+?) (?:for|package|library|component)", query)
            if match:
                return match.group(1).strip()
        
        if "recommend" in query or "suggest" in query:
            return "recommendation"
        
        if "find" in query or "search" in query:
            return "search"
        
        return None
    
    def _extract_categories(self, query: str) -> List[ComponentCategory]:
        """Extract component categories from the query."""
        categories = []
        
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    categories.append(category)
                    break
        
        return list(set(categories))  # Remove duplicates
    
    def _extract_sensors(self, query: str) -> List[SensorType]:
        """Extract sensor types mentioned in the query."""
        sensors = []
        
        for sensor, keywords in self.sensor_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    sensors.append(sensor)
                    break
        
        return list(set(sensors))  # Remove duplicates
    
    def _extract_environment(self, query: str) -> Optional[EnvironmentType]:
        """Extract environment type from the query."""
        for env_type, keywords in self.environment_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    return env_type
        
        return EnvironmentType.UNKNOWN
    
    def _extract_performance_requirements(self, query: str) -> List[str]:
        """Extract performance-related requirements."""
        requirements = []
        
        for keyword in self.performance_keywords:
            if keyword in query:
                requirements.append(keyword)
        
        return requirements
    
    def _extract_constraints(self, query: str) -> List[str]:
        """Extract constraints and limitations."""
        constraints = []
        
        # Look for resource constraints
        if "low memory" in query or "limited memory" in query:
            constraints.append("low_memory")
        
        if "real-time" in query or "real time" in query:
            constraints.append("real_time")
        
        if "embedded" in query:
            constraints.append("embedded")
        
        if "ros1" in query or "ros 1" in query:
            constraints.append("ros1")
        
        if "ros2" in query or "ros 2" in query:
            constraints.append("ros2")
        
        return constraints
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract general keywords from the query."""
        # Remove common stop words and extract meaningful terms
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", 
            "of", "with", "by", "is", "are", "was", "were", "what", "which", 
            "who", "where", "when", "why", "how", "best", "good", "better",
            "show", "me", "all", "that", "can", "be", "used", "work", "works",
            "find", "search", "get", "give", "list", "display", "tell", "help",
            "want", "need", "looking", "please", "have", "has", "would", "could",
            "should", "will", "shall", "may", "might", "must", "do", "does", "did"
        }
        
        # Simple word extraction (could be enhanced with NLP libraries)
        words = re.findall(r'\b\w+\b', query)
        
        # Filter keywords to only include meaningful technical terms
        meaningful_keywords = []
        technical_terms = {
            "camera", "lidar", "sensor", "robot", "ros", "detection", "tracking",
            "navigation", "localization", "slam", "perception", "planning", "control",
            "raspberry", "pi", "nvidia", "jetson", "arduino", "motors", "wheels",
            "ultrasonic", "infrared", "thermal", "stereo", "depth", "rgb", "imu",
            "gps", "odometry", "mapping", "path", "trajectory", "obstacle", "avoidance"
        }
        
        for word in words:
            if (word not in stop_words and 
                len(word) > 2 and 
                (word in technical_terms or any(term in word for term in technical_terms))):
                meaningful_keywords.append(word)
        
        return meaningful_keywords[:5]  # Limit to top 5 meaningful keywords

class QueryToSearchTranslator:
    """Translates parsed requirements into search parameters."""
    
    def __init__(self):
        self.category_to_type_mapping = {
            ComponentCategory.SLAM: ["slam", "mapping", "localization"],
            ComponentCategory.LOCALIZATION: ["localization", "pose"],
            ComponentCategory.NAVIGATION: ["navigation", "planner", "move_base"],
            ComponentCategory.PERCEPTION: ["perception", "vision", "detection"],
            ComponentCategory.SENSORS: ["sensor", "driver"],
            ComponentCategory.PLANNING: ["planner", "planning"],
            ComponentCategory.CONTROL: ["control", "controller"],
            ComponentCategory.SIMULATION: ["simulation", "gazebo"],
            ComponentCategory.VISUALIZATION: ["visualization", "rviz"],
            ComponentCategory.COMMUNICATION: ["communication", "message"]
        }
    
    def translate_to_search_params(self, requirements: QueryRequirements) -> Dict[str, Any]:
        """
        Translate query requirements into search parameters.
        
        Args:
            requirements: Parsed query requirements
            
        Returns:
            Dictionary of search parameters for the search engine
        """
        search_params = {
            "text_query": "",
            "filters": {},
            "boost_fields": [],
            "must_include": [],
            "should_include": []
        }
        
        # Build text query from categories and keywords
        query_terms = []
        
        # Prioritize category-based terms (highest priority)
        for category in requirements.categories:
            if category in self.category_to_type_mapping:
                query_terms.extend(self.category_to_type_mapping[category])
        
        # Add sensor-related terms (high priority)
        for sensor in requirements.sensors:
            query_terms.append(sensor.value)
        
        # Add meaningful keywords only if we have them (lower priority)
        if requirements.keywords:
            query_terms.extend(requirements.keywords[:3])  # Limit to 3 most relevant keywords
        
        # Remove duplicates and create query
        unique_terms = list(set(query_terms))
        
        # Construct a simpler, more reliable Solr query
        if unique_terms:
            # Create separate field queries
            field_queries = []
            term_string = " OR ".join(unique_terms)
            
            # Simple approach: search each field separately
            field_queries.append(f"name:({term_string})")
            field_queries.append(f"type:({term_string})")
            field_queries.append(f"description:({term_string})")
            field_queries.append(f"content:({term_string})")
            
            search_params["text_query"] = " OR ".join(field_queries)
        else:
            search_params["text_query"] = "*:*"  # Fallback to all results
        
        # Add filters based on requirements
        if requirements.environment and requirements.environment != EnvironmentType.UNKNOWN:
            search_params["filters"]["environment"] = requirements.environment.value
        
        # Add boost fields for performance requirements
        if "best" in requirements.performance_requirements:
            search_params["boost_fields"] = ["name^2", "description^1.5"]
        
        # Add must-include terms for specific sensors
        if requirements.sensors:
            search_params["must_include"] = [sensor.value for sensor in requirements.sensors]
        
        return search_params

def test_query_processor():
    """Test the query processor with example queries."""
    processor = NLQueryProcessor()
    translator = QueryToSearchTranslator()
    
    test_queries = [
        "What is the best SLAM package for a robot with a 3D LiDAR and an IMU in a large, outdoor environment?",
        "I need a navigation stack for indoor environments with stereo cameras",
        "Recommend a localization package for outdoor robots with GPS and wheel odometry",
        "Find perception components for object detection using depth cameras",
        "What planning algorithms work well with 2D LiDAR in real-time?"
    ]
    
    for query in test_queries:
        print(f"\n" + "="*60)
        print(f"Query: {query}")
        print("-"*60)
        
        requirements = processor.parse_query(query)
        search_params = translator.translate_to_search_params(requirements)
        
        print(f"Requirements: {requirements}")
        print(f"Search params: {search_params}")

if __name__ == "__main__":
    test_query_processor()
