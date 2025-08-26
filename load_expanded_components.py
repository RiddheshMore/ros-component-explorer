#!/usr/bin/env python3
"""
Script to load expanded ROS components into the knowledge base.
This script loads the new components from expanded_components.ttl into Blazegraph.
"""

import requests
import logging
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BLAZEGRAPH_URL = "http://localhost:9999/bigdata/sparql"

def load_expanded_components():
    """Load the expanded components TTL file into Blazegraph."""
    try:
        # Read the expanded components TTL file
        ttl_file_path = "data/expanded_components.ttl"
        
        if not os.path.exists(ttl_file_path):
            logger.error(f"TTL file not found: {ttl_file_path}")
            return False
        
        with open(ttl_file_path, 'rb') as f:
            turtle_data = f.read()
        
        # Upload to Blazegraph
        resp = requests.post(
            BLAZEGRAPH_URL,
            data=turtle_data,
            headers={
                'Content-Type': 'text/turtle',
                'Accept': 'application/sparql-results+json',
            }
        )
        
        if resp.ok:
            logger.info("Successfully loaded expanded components into Blazegraph.")
            return True
        else:
            logger.error(f"Failed to load expanded components: {resp.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error loading expanded components: {e}")
        return False

def verify_components_loaded():
    """Verify that the new components have been loaded."""
    try:
        # Query for some of the new components
        query = """
        PREFIX ros: <http://example.org/ros-ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT ?component ?label WHERE {
            ?component rdfs:label ?label .
            FILTER(?label IN ("robot_localization", "realsense-ros", "TEB Local Planner", "darknet_ros (YOLO)"))
        }
        """
        
        resp = requests.post(
            BLAZEGRAPH_URL, 
            data={'query': query}, 
            headers={'Accept': 'application/sparql-results+json'}
        )
        
        if resp.ok:
            results = resp.json()['results']['bindings']
            logger.info(f"Found {len(results)} new components in the database:")
            for result in results:
                logger.info(f"  - {result['label']['value']}")
            return len(results) > 0
        else:
            logger.error(f"Failed to verify components: {resp.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying components: {e}")
        return False

def main():
    """Main function to load and verify expanded components."""
    logger.info("Loading expanded ROS components...")
    
    # Check if Blazegraph is running
    try:
        resp = requests.get(f"{BLAZEGRAPH_URL.replace('/sparql', '')}")
        if not resp.ok:
            logger.error("Blazegraph is not running. Please start Blazegraph first.")
            return 1
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to Blazegraph. Please ensure it's running on localhost:9999")
        return 1
    
    # Load the expanded components
    if load_expanded_components():
        logger.info("Expanded components loaded successfully!")
        
        # Verify the components were loaded
        if verify_components_loaded():
            logger.info("Verification completed successfully!")
        else:
            logger.warning("Verification failed - some components may not have been loaded correctly.")
    else:
        logger.error("Failed to load expanded components.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
