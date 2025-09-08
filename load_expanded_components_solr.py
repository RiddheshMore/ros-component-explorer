#!/usr/bin/env python3
"""
Script to load expanded ROS components into Solr.
This script loads the new components from expanded_components.ttl into the Solr search engine.
"""

import json
import logging
import sys
import os
from pysolr import Solr
import rdflib
from rdflib import Graph, Namespace, RDF, RDFS

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SOLR_URL = "http://localhost:8984/solr/ros_explorer"

def load_expanded_components_to_solr():
    """Load the expanded components TTL file into Solr."""
    try:
        # Initialize Solr connection
        solr = Solr(SOLR_URL, timeout=10)
        
        # Read the expanded components TTL file
        ttl_file_path = "data/components.ttl"
        
        if not os.path.exists(ttl_file_path):
            logger.error(f"TTL file not found: {ttl_file_path}")
            return False
        
        # Parse the TTL file
        g = Graph()
        logger.info(f"Parsing TTL file: {ttl_file_path}")
        g.parse(ttl_file_path, format="turtle")
        logger.info(f"TTL file parsed successfully. Graph has {len(g)} triples.")
        
        # Define namespaces (using the ones from the original schema)
        COMP = Namespace("http://example.org/ros-components#")
        
        # Extract component data
        components = []
        
        # Find all component instances
        logger.info("Looking for component instances...")
        component_types = [
            COMP.LocalizationNode,
            COMP.SensorDriver,
            COMP.PathPlanner,
            COMP.PerceptionNode
        ]
        
        for component_type in component_types:
            logger.info(f"Looking for components of type: {component_type}")
            for component_uri, rdf_type, _ in g.triples((None, RDF.type, component_type)):
                logger.info(f"Found component: {component_uri}")
                
                # Get component label
                label = None
                for _, _, label_obj in g.triples((component_uri, RDFS.label, None)):
                    label = str(label_obj)
                    break
                
                if not label:
                    logger.warning(f"No label found for component: {component_uri}")
                    continue
                
                # Get description
                description = None
                for _, _, desc_obj in g.triples((component_uri, COMP.description, None)):
                    description = str(desc_obj)
                    break
                
                # Get package info
                package = None
                for _, _, pkg_obj in g.triples((component_uri, COMP.package, None)):
                    package = str(pkg_obj)
                    break
                
                # Get update rate
                update_rate = None
                for _, _, rate_obj in g.triples((component_uri, COMP.updateRate, None)):
                    update_rate = str(rate_obj)
                    break
                
                # Get ROS version
                ros_version = None
                for _, _, version_obj in g.triples((component_uri, COMP.rosVersion, None)):
                    ros_version = str(version_obj)
                    break
                
                # Get input topics
                input_topics = []
                for _, _, topic_obj in g.triples((component_uri, COMP.hasInput, None)):
                    input_topics.append(str(topic_obj))
                
                # Get output topics
                output_topics = []
                for _, _, topic_obj in g.triples((component_uri, COMP.hasOutput, None)):
                    output_topics.append(str(topic_obj))
                
                # Create Solr document
                doc = {
                    'id': str(component_uri),
                    'name': label,
                    'type': str(component_type).split('#')[-1],
                    'description': description or "No description available",
                    'package': package or "Unknown package",
                    'update_rate': update_rate or "Unknown",
                    'ros_version': ros_version or "Unknown",
                    'subscribed_topics': input_topics,
                    'published_topics': output_topics,
                    'content': f"{label} {str(component_type).split('#')[-1]} {description or ''} {package or ''} {' '.join(input_topics)} {' '.join(output_topics)}"
                }
                
                logger.info(f"Created document for {label}: {doc}")
                components.append(doc)
        
        logger.info(f"Total expanded components found: {len(components)}")
        
        # Index documents in Solr
        if components:
            try:
                logger.info(f"Indexing {len(components)} new documents in Solr...")
                solr.add(components)
                solr.commit()
                logger.info("Successfully indexed expanded components in Solr.")
                return True
            except Exception as e:
                logger.error(f"Error indexing documents in Solr: {e}")
                return False
        else:
            logger.warning("No components found to index.")
            return False
            
    except Exception as e:
        logger.error(f"Error loading expanded components to Solr: {e}")
        return False

def verify_components_in_solr():
    """Verify that the new components have been indexed in Solr."""
    try:
        solr = Solr(SOLR_URL, timeout=10)
        
        # Search for some of the new components
        new_component_names = ["robot_localization", "realsense-ros", "TEB Local Planner", "darknet_ros (YOLO)"]
        
        found_components = []
        for name in new_component_names:
            results = solr.search(f'name:"{name}"')
            if results.hits > 0:
                found_components.append(name)
                logger.info(f"✓ Found '{name}' in Solr")
            else:
                logger.warning(f"✗ '{name}' not found in Solr")
        
        # Get total count
        all_results = solr.search("*:*", rows=0)
        logger.info(f"Total documents in Solr: {all_results.hits}")
        
        return len(found_components) > 0
        
    except Exception as e:
        logger.error(f"Error verifying components in Solr: {e}")
        return False

def main():
    """Main function to load and verify expanded components in Solr."""
    logger.info("Loading expanded ROS components into Solr...")
    
    # Check if Solr is running
    try:
        solr = Solr(SOLR_URL, timeout=10)
        solr.search("*:*", rows=1)  # Test connection
    except Exception as e:
        logger.error("Cannot connect to Solr. Please ensure it's running on localhost:8984")
        logger.error(f"Error: {e}")
        return 1
    
    # Load the expanded components
    if load_expanded_components_to_solr():
        logger.info("Expanded components loaded successfully into Solr!")
        
        # Verify the components were loaded
        if verify_components_in_solr():
            logger.info("Verification completed successfully!")
        else:
            logger.warning("Verification failed - some components may not have been loaded correctly.")
    else:
        logger.error("Failed to load expanded components into Solr.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
