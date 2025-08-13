"""
Solr manager for the ROS Component Explorer.
Handles data loading and search queries for component information using Apache Solr.
"""

import json
import logging
from typing import List, Dict, Optional
from pysolr import Solr
import rdflib
from rdflib import Graph, Namespace, RDF, RDFS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SOLR_URL = "http://localhost:8984/solr/ros_explorer"

class SolrManager:
    """Manages the Solr search engine for ROS components."""
    
    def __init__(self, ttl_file: str):
        self.ttl_file = ttl_file
        self.solr = Solr(SOLR_URL, timeout=10)
        self._ensure_data_loaded()
    
    def _ensure_data_loaded(self):
        """Load TTL data into Solr if the core is empty."""
        try:
            # Check if data exists
            results = self.solr.search("*:*", rows=1)
            if results.hits > 0:
                logger.info(f"Solr already has {results.hits} documents.")
                return
            
            # Load TTL data
            logger.info("Loading TTL data into Solr...")
            self._load_ttl_data()
            logger.info("TTL data loaded successfully into Solr.")
            
        except Exception as e:
            logger.error(f"Error checking/loading Solr data: {e}")
            raise
    
    def _load_ttl_data(self):
        """Parse TTL file and convert to Solr documents."""
        # Parse the TTL file
        g = Graph()
        try:
            logger.info(f"Parsing TTL file: {self.ttl_file}")
            g.parse(self.ttl_file, format="turtle")
            logger.info(f"TTL file parsed successfully. Graph has {len(g)} triples.")
        except Exception as e:
            logger.error(f"Error parsing TTL file: {e}")
            raise
        
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
            ROS.PerceptionComponent
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
                    'type': str(component_type).split('#')[-1],
                    'description': description or "No description available",
                    'package': package or "Unknown package",
                    'update_rate': update_rate or "Unknown",
                    'ros_version': ros_version or "Unknown",
                    'subscribed_topics': subscribed_topics,
                    'published_topics': published_topics,
                    'content': f"{label} {str(component_type).split('#')[-1]} {description or ''} {package or ''} {' '.join(subscribed_topics)} {' '.join(published_topics)}"
                }
                
                logger.info(f"Created document for {label}: {doc}")
                components.append(doc)
        
        logger.info(f"Total components found: {len(components)}")
        
        # Index documents in Solr
        if components:
            try:
                logger.info(f"Indexing {len(components)} documents in Solr...")
                self.solr.add(components)
                self.solr.commit()
                logger.info(f"Successfully indexed {len(components)} components in Solr")
            except Exception as e:
                logger.error(f"Error indexing documents in Solr: {e}")
                raise
        else:
            logger.warning("No components found to index!")
    
    def get_all_components(self) -> List[Dict]:
        """Get all components from Solr."""
        try:
            results = self.solr.search("*:*", rows=1000)
            components = []
            for doc in results.docs:
                components.append({
                    'uri': doc.get('id', ''),
                    'name': doc.get('name', ''),
                    'class': doc.get('type', ''),
                    'description': doc.get('description', 'No description available')
                })
            return components
        except Exception as e:
            logger.error(f"Error getting all components: {e}")
            return []
    
    def search_components(self, search_term: str) -> List[Dict]:
        """Search components by term."""
        if not search_term.strip():
            return self.get_all_components()
        
        try:
            # Use Solr's built-in text search
            query = f"content:*{search_term}* OR name:*{search_term}* OR type:*{search_term}*"
            results = self.solr.search(query, rows=1000)
            
            components = []
            for doc in results.docs:
                components.append({
                    'uri': doc.get('id', ''),
                    'name': doc.get('name', ''),
                    'class': doc.get('type', ''),
                    'description': doc.get('description', 'No description available')
                })
            return components
        except Exception as e:
            logger.error(f"Error searching components: {e}")
            return []
    
    def get_component_details(self, component_uri: str) -> Optional[Dict]:
        """Get detailed information about a specific component."""
        try:
            query = f'id:"{component_uri}"'
            results = self.solr.search(query, rows=1)
            
            if results.hits == 0:
                return None
            
            doc = results.docs[0]
            details = {
                'uri': doc.get('id', ''),
                'name': doc.get('name', ''),
                'class': doc.get('type', ''),
                'properties': {
                    'package': doc.get('package', 'Unknown'),
                    'update_rate': doc.get('update_rate', 'Unknown'),
                    'ros_version': doc.get('ros_version', 'Unknown'),
                    'subscribed_topics': doc.get('subscribed_topics', []),
                    'published_topics': doc.get('published_topics', [])
                }
            }
            return details
        except Exception as e:
            logger.error(f"Error getting component details: {e}")
            return None 