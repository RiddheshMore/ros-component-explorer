#!/usr/bin/env python3
"""
Script to reload ROS components into Solr.
This script clears the current Solr index and reloads all components from the components.ttl file.
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

def clear_solr_index():
    """Clear all documents from Solr index"""
    try:
        solr = Solr(SOLR_URL, timeout=10)
        logger.info("Clearing Solr index...")
        solr.delete(q='*:*')
        solr.commit()
        logger.info("Solr index cleared successfully.")
        return True
    except Exception as e:
        logger.error(f"Error clearing Solr index: {e}")
        return False

def reload_components_to_solr():
    """Reload all components from the TTL file into Solr."""
    try:
        # Initialize Solr connection
        solr = Solr(SOLR_URL, timeout=10)
        
        # Read the components TTL file
        ttl_file_path = "data/components.ttl"
        
        if not os.path.exists(ttl_file_path):
            logger.error(f"TTL file not found: {ttl_file_path}")
            return False
        
        # Parse the TTL file
        g = Graph()
        logger.info(f"Parsing TTL file: {ttl_file_path}")
        g.parse(ttl_file_path, format="turtle")
        logger.info(f"TTL file parsed successfully. Graph has {len(g)} triples.")
        
        # Define namespaces
        ROS = Namespace("http://example.org/ros-ontology#")
        DCTERMS = Namespace("http://purl.org/dc/terms/")
        
        # Extract component data
        components = []
        
        # Find all component instances
        logger.info("Looking for component instances...")
        component_types = [
            ROS.LocalizationComponent,
            ROS.SensorDriverComponent,
            ROS.PathPlannerComponent,
            ROS.ControllerComponent,
            ROS.PerceptionComponent,
            ROS.ManipulationComponent,
            ROS.SimulationComponent
        ]
        
        # Track the number of components found for each type
        type_counts = {}
        
        for component_type in component_types:
            type_name = str(component_type).split('#')[-1]
            count = 0
            logger.info(f"Looking for components of type: {type_name}")
            
            for component_uri, rdf_type, _ in g.triples((None, RDF.type, component_type)):
                count += 1
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
                for _, _, desc_obj in g.triples((component_uri, DCTERMS.description, None)):
                    description = str(desc_obj)
                    break
                
                # Get package info
                package = None
                for _, _, pkg_obj in g.triples((component_uri, ROS.isInPackage, None)):
                    package = str(pkg_obj)
                    break
                
                # Get update rate
                update_rate = None
                for _, _, rate_obj in g.triples((component_uri, ROS.hasUpdateRate, None)):
                    update_rate = str(rate_obj)
                    break
                
                # Get ROS version
                ros_version = None
                for _, _, version_obj in g.triples((component_uri, ROS.rosVersion, None)):
                    ros_version = str(version_obj)
                    break
                
                # Get subscribed topics
                subscribed_topics = []
                for _, _, topic_obj in g.triples((component_uri, ROS.subscribesToTopic, None)):
                    topic_name = str(topic_obj).split('#')[-1] if '#' in str(topic_obj) else str(topic_obj)
                    subscribed_topics.append(topic_name)
                
                # Get published topics
                published_topics = []
                for _, _, topic_obj in g.triples((component_uri, ROS.publishesTopic, None)):
                    topic_name = str(topic_obj).split('#')[-1] if '#' in str(topic_obj) else str(topic_obj)
                    published_topics.append(topic_name)
                
                # Create Solr document
                doc = {
                    'id': str(component_uri),
                    'name': label,
                    'type': type_name,
                    'description': description or "No description available",
                    'package': package or "Unknown package",
                    'update_rate': update_rate or "Unknown",
                    'ros_version': ros_version or "Unknown",
                    'subscribed_topics': subscribed_topics,
                    'published_topics': published_topics,
                    'content': f"{label} {type_name} {description or ''} {package or ''} {' '.join(subscribed_topics)} {' '.join(published_topics)}"
                }
                
                logger.info(f"Created document for {label}: {doc}")
                components.append(doc)
            
            type_counts[type_name] = count
        
        # Log component type statistics
        logger.info(f"Component type counts: {type_counts}")
        logger.info(f"Total components found: {len(components)}")
        
        # Index documents in Solr
        if components:
            try:
                logger.info(f"Indexing {len(components)} documents in Solr...")
                solr.add(components)
                solr.commit()
                logger.info(f"Successfully indexed {len(components)} components in Solr")
                return True
            except Exception as e:
                logger.error(f"Error indexing documents in Solr: {e}")
                return False
        else:
            logger.warning("No components found to index!")
            return False
            
    except Exception as e:
        logger.error(f"Error loading components to Solr: {e}")
        return False

def verify_components_in_solr():
    """Verify that components have been indexed in Solr."""
    try:
        solr = Solr(SOLR_URL, timeout=10)
        
        # Get total count
        all_results = solr.search("*:*", rows=0)
        component_count = all_results.hits
        logger.info(f"Total documents in Solr: {component_count}")
        
        # Get component types
        results = solr.search("*:*", rows=component_count)
        types = {}
        for doc in results.docs:
            doc_type = doc.get('type', 'Unknown')
            types[doc_type] = types.get(doc_type, 0) + 1
        
        logger.info("Component types in Solr:")
        for t, count in types.items():
            logger.info(f"  - {t}: {count}")
            
        return component_count > 0
        
    except Exception as e:
        logger.error(f"Error verifying components in Solr: {e}")
        return False

def main():
    """Main function to reload and verify components in Solr."""
    logger.info("Reloading ROS components into Solr...")
    
    # Check if Solr is running
    try:
        solr = Solr(SOLR_URL, timeout=10)
        solr.search("*:*", rows=1)  # Test connection
    except Exception as e:
        logger.error("Cannot connect to Solr. Please ensure it's running on localhost:8984")
        logger.error(f"Error: {e}")
        return 1
    
    # Clear existing index
    if not clear_solr_index():
        logger.error("Failed to clear Solr index.")
        return 1
    
    # Reload the components
    if reload_components_to_solr():
        logger.info("Components reloaded successfully into Solr!")
        
        # Verify the components were loaded
        if verify_components_in_solr():
            logger.info("Verification completed successfully!")
        else:
            logger.warning("Verification failed - some components may not have been loaded correctly.")
    else:
        logger.error("Failed to reload components into Solr.")
        return 1
    
    # Also load expanded components from expanded_components_ros.ttl if it exists
    expanded_file_path = "data/expanded_components_ros.ttl"
    if os.path.exists(expanded_file_path):
        logger.info(f"Found expanded components file: {expanded_file_path}")
        logger.info("You may want to load these components as well using load_expanded_components_solr.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
