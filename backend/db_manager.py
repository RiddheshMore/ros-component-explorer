"""
Database manager for the ROS Component Explorer.
Handles RDF data loading and SPARQL queries for component information.
"""

import rdflib
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS
from typing import List, Dict, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages the RDF graph database for ROS components."""
    
    def __init__(self, rdf_file: str):
        """
        Initialize the database manager.
        
        Args:
            rdf_file: Path to the Turtle RDF file containing component data
        """
        self.rdf_file = rdf_file
        self.graph = Graph()
        self.comp_ns = Namespace("http://example.org/ros-components#")
        
        # Bind namespaces for easier querying
        self.graph.bind("comp", self.comp_ns)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        
        logger.info(f"Initialized DatabaseManager with file: {rdf_file}")
    
    def load_data(self) -> bool:
        """
        Load/reload data from the Turtle file into the graph.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear existing data
            self.graph = Graph()
            self.graph.bind("comp", self.comp_ns)
            self.graph.bind("rdf", RDF)
            self.graph.bind("rdfs", RDFS)
            
            # Parse the Turtle file
            self.graph.parse(self.rdf_file, format="turtle")
            
            logger.info(f"Successfully loaded {len(self.graph)} triples from {self.rdf_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading data from {self.rdf_file}: {e}")
            return False
    
    def get_all_components(self) -> List[Dict]:
        """
        Fetch all component instances and their basic details.
        
        Returns:
            List of dictionaries containing component information
        """
        query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX comp: <http://example.org/ros-components#>
        
        SELECT ?component ?label ?class_type ?description
        WHERE {
            ?component a ?class_type .
            ?component rdfs:label ?label .
            OPTIONAL { ?component comp:description ?description }
            FILTER(?class_type IN (comp:LocalizationNode, comp:SensorDriver, comp:PathPlanner, comp:Controller, comp:PerceptionNode))
        }
        ORDER BY ?label
        """
        
        try:
            results = self.graph.query(query)
            components = []
            
            for row in results:
                component_info = {
                    'uri': str(row.component),
                    'name': str(row.label),
                    'class': str(row.class_type).split('#')[-1],  # Extract class name
                    'description': str(row.description) if row.description else "No description available"
                }
                components.append(component_info)
            
            logger.info(f"Retrieved {len(components)} components")
            return components
            
        except Exception as e:
            logger.error(f"Error querying all components: {e}")
            return []
    
    def search_components(self, search_term: str) -> List[Dict]:
        """
        Search for components matching the given term.
        
        Args:
            search_term: The search term to match against component names, classes, or descriptions
            
        Returns:
            List of dictionaries containing matching component information
        """
        if not search_term.strip():
            return self.get_all_components()
        
        # Case-insensitive search query
        query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX comp: <http://example.org/ros-components#>
        
        SELECT ?component ?label ?class_type ?description
        WHERE {
            ?component a ?class_type .
            ?component rdfs:label ?label .
            OPTIONAL { ?component comp:description ?description }
            FILTER(?class_type IN (comp:LocalizationNode, comp:SensorDriver, comp:PathPlanner, comp:Controller, comp:PerceptionNode))
            FILTER(
                REGEX(?label, ?search_term, "i") ||
                REGEX(?class_type, ?search_term, "i") ||
                (BOUND(?description) && REGEX(?description, ?search_term, "i"))
            )
        }
        ORDER BY ?label
        """
        
        try:
            results = self.graph.query(query, initBindings={'search_term': Literal(search_term)})
            components = []
            
            for row in results:
                component_info = {
                    'uri': str(row.component),
                    'name': str(row.label),
                    'class': str(row.class_type).split('#')[-1],
                    'description': str(row.description) if row.description else "No description available"
                }
                components.append(component_info)
            
            logger.info(f"Search for '{search_term}' returned {len(components)} results")
            return components
            
        except Exception as e:
            logger.error(f"Error searching components: {e}")
            return []
    
    def get_component_details(self, component_uri: str) -> Optional[Dict]:
        """
        Get detailed information for a specific component.
        
        Args:
            component_uri: The URI of the component to get details for
            
        Returns:
            Dictionary containing all component properties, or None if not found
        """
        query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX comp: <http://example.org/ros-components#>
        
        SELECT ?property ?value
        WHERE {
            <COMPONENT_URI> ?property ?value .
        }
        """
        
        try:
            # Replace the placeholder with the actual URI
            query = query.replace("<COMPONENT_URI>", f"<{component_uri}>")
            results = self.graph.query(query)
            
            details = {
                'uri': component_uri,
                'properties': {}
            }
            
            for row in results:
                property_name = str(row.property).split('#')[-1] if '#' in str(row.property) else str(row.property)
                value = str(row.value)
                
                # Handle special cases for better display
                if property_name == 'type':
                    details['class'] = value.split('#')[-1]
                elif property_name == 'label':
                    details['name'] = value
                else:
                    details['properties'][property_name] = value
            
            if not details.get('name'):
                logger.warning(f"No details found for component: {component_uri}")
                return None
            
            logger.info(f"Retrieved details for component: {details.get('name', 'Unknown')}")
            return details
            
        except Exception as e:
            logger.error(f"Error getting component details for {component_uri}: {e}")
            return None
    
    def get_component_count(self) -> int:
        """Get the total number of components in the database."""
        query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX comp: <http://example.org/ros-components#>
        
        SELECT (COUNT(?component) as ?count)
        WHERE {
            ?component a ?class_type .
            FILTER(?class_type IN (comp:LocalizationNode, comp:SensorDriver, comp:PathPlanner, comp:Controller, comp:PerceptionNode))
        }
        """
        
        try:
            results = self.graph.query(query)
            count = int(next(results)[0])
            return count
        except Exception as e:
            logger.error(f"Error getting component count: {e}")
            return 0 