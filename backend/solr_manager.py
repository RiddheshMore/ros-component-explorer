"""
Solr manager for the ROS Component Explorer.
Handles data loading and search queries for component information using Apache Solr.
Supports both traditional text search and vector-based semantic search.
"""

import json
import logging
from typing import List, Dict, Optional, Tuple
from pysolr import Solr
import rdflib
from rdflib import Graph, Namespace, RDF, RDFS
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SOLR_URL = "http://localhost:8984/solr/ros_explorer"

class SolrManager:
    """Manages the Solr search engine for ROS components with vector support."""
    
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
    
    def add_vectors_to_documents(self, components_with_vectors: List[Dict]) -> bool:
        """
        Add vector embeddings to existing documents in Solr.
        
        Args:
            components_with_vectors: List of components with vector embeddings
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Adding vectors to {len(components_with_vectors)} documents...")
            
            # Get existing documents to preserve all fields
            existing_docs = self.solr.search("*:*", rows=1000)
            existing_docs_map = {doc['id']: doc for doc in existing_docs.docs}
            
            # Prepare documents for Solr with all fields preserved
            solr_docs = []
            for component in components_with_vectors:
                doc_id = component.get('uri', component.get('id', ''))
                
                if doc_id in existing_docs_map:
                    # Preserve all existing fields and add vector
                    solr_doc = existing_docs_map[doc_id].copy()
                    solr_doc['vector'] = component.get('vector', [])
                else:
                    # If document doesn't exist, create minimal doc with vector
                    solr_doc = {
                        'id': doc_id,
                        'vector': component.get('vector', [])
                    }
                
                solr_docs.append(solr_doc)
            
            # Update documents with vectors
            self.solr.add(solr_docs)
            self.solr.commit()
            
            logger.info("Successfully added vectors to documents")
            return True
            
        except Exception as e:
            logger.error(f"Error adding vectors to documents: {e}")
            return False
    
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
        """Search components by term using traditional text search."""
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
    
    def semantic_search(self, query_vector: List[float], k: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Perform semantic search using vector similarity.
        
        Args:
            query_vector: Query vector for similarity search
            k: Number of top results to return
            filters: Optional filters for metadata
            
        Returns:
            List of similar components
        """
        try:
            # Check if we have a proper vector field for KNN search
            if self._has_proper_vector_field():
                # Use KNN query for vector similarity
                return self._knn_semantic_search(query_vector, k, filters)
            else:
                # Fallback to text-based similarity search
                logger.warning("Proper vector field not available, using text-based similarity search")
                return self._text_based_semantic_search(query_vector, k, filters)
                
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def _has_proper_vector_field(self) -> bool:
        """Check if we have a proper vector field that supports KNN search."""
        try:
            # Try to get schema info to check field type
            from backend.schema_updater import SolrSchemaUpdater
            updater = SolrSchemaUpdater()
            fields = updater.list_fields()
            if fields and "vector" in fields:
                # Check if it's a proper vector field type
                field_types = updater.list_field_types()
                if field_types:
                    # Look for vector-related field types
                    vector_types = [ft for ft in field_types if 'vector' in ft.lower() or 'dense' in ft.lower()]
                    return len(vector_types) > 0
            return False
        except Exception as e:
            logger.warning(f"Could not determine vector field type: {e}")
            return False
    
    def _knn_semantic_search(self, query_vector: List[float], k: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        """Perform KNN-based semantic search."""
        # Build the query
        query_parts = []
        
        # Add KNN query for vector similarity
        query_parts.append(f"{{!knn f=vector topK={k}}}{query_vector}")
        
        # Add filters if provided
        if filters:
            for field, value in filters.items():
                if isinstance(value, list):
                    query_parts.append(f"{field}:({' OR '.join(value)})")
                else:
                    query_parts.append(f"{field}:{value}")
        
        # Combine query parts
        query = " AND ".join(query_parts)
        
        logger.info(f"Executing KNN semantic search with query: {query}")
        
        # Execute search
        results = self.solr.search(query, rows=k)
        
        components = []
        for doc in results.docs:
            components.append({
                'uri': doc.get('id', ''),
                'name': doc.get('name', ''),
                'class': doc.get('type', ''),
                'description': doc.get('description', 'No description available'),
                'score': doc.get('score', 0.0)
            })
        
        # Sort by score
        components.sort(key=lambda x: x.get('score', 0.0), reverse=True)
        
        logger.info(f"KNN semantic search returned {len(components)} results")
        return components
    
    def _text_based_semantic_search(self, query_vector: List[float], k: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        """Perform text-based semantic search as fallback."""
        try:
            # For text-based search, we'll use a different approach
            # Since vectors are stored as text, we'll search for components that might be semantically similar
            # based on their descriptions and other text fields
            
            # Build text query using component descriptions and content
            query_parts = []
            
            # Search in content field for semantic concepts
            query_parts.append("content:*")
            
            # Add filters if provided
            if filters:
                for field, value in filters.items():
                    if isinstance(value, list):
                        query_parts.append(f"{field}:({' OR '.join(value)})")
                    else:
                        query_parts.append(f"{field}:{value}")
            
            # Combine query parts
            query = " AND ".join(query_parts)
            
            logger.info(f"Executing text-based semantic search with query: {query}")
            
            # Execute search
            results = self.solr.search(query, rows=k)
            
            components = []
            for doc in results.docs:
                components.append({
                    'uri': doc.get('id', ''),
                    'name': doc.get('name', ''),
                    'class': doc.get('type', ''),
                    'description': doc.get('description', 'No description available'),
                    'score': 1.0  # Default score for text-based search
                })
            
            logger.info(f"Text-based semantic search returned {len(components)} results")
            return components
            
        except Exception as e:
            logger.error(f"Error in text-based semantic search: {e}")
            return []
    
    def hybrid_search(self, text_query: str, query_vector: List[float], k: int = 10, 
                     filters: Optional[Dict] = None, semantic_weight: float = 0.7) -> List[Dict]:
        """
        Perform hybrid search combining text and semantic similarity.
        
        Args:
            text_query: Text query for traditional search
            query_vector: Query vector for semantic search
            k: Number of top results to return
            filters: Optional filters for metadata
            semantic_weight: Weight for semantic similarity (0.0 to 1.0)
            
        Returns:
            List of components ranked by hybrid score
        """
        try:
            # Perform text search
            text_results = self.search_components(text_query)
            
            # Perform semantic search
            semantic_results = self.semantic_search(query_vector, k=k, filters=filters)
            
            # Combine and rank results
            combined_results = self._combine_search_results(
                text_results, semantic_results, semantic_weight
            )
            
            # Apply filters if provided
            if filters:
                combined_results = self._apply_filters(combined_results, filters)
            
            # Return top k results
            return combined_results[:k]
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []
    
    def _combine_search_results(self, text_results: List[Dict], semantic_results: List[Dict], 
                               semantic_weight: float) -> List[Dict]:
        """
        Combine and rank results from text and semantic search.
        
        Args:
            text_results: Results from text search
            semantic_results: Results from semantic search
            semantic_weight: Weight for semantic similarity
            
        Returns:
            Combined and ranked results
        """
        # Create a mapping of URI to results
        result_map = {}
        
        # Add text search results
        for i, result in enumerate(text_results):
            uri = result['uri']
            if uri not in result_map:
                result_map[uri] = result.copy()
                result_map[uri]['text_score'] = 1.0 / (i + 1)  # Inverse rank score
                result_map[uri]['semantic_score'] = 0.0
                result_map[uri]['hybrid_score'] = 0.0
        
        # Add semantic search results
        for i, result in enumerate(semantic_results):
            uri = result['uri']
            if uri in result_map:
                result_map[uri]['semantic_score'] = result.get('score', 0.0)
            else:
                result_map[uri] = result.copy()
                result_map[uri]['text_score'] = 0.0
                result_map[uri]['semantic_score'] = result.get('score', 0.0)
                result_map[uri]['hybrid_score'] = 0.0
        
        # Calculate hybrid scores
        for result in result_map.values():
            text_score = result.get('text_score', 0.0)
            semantic_score = result.get('semantic_score', 0.0)
            
            # Normalize scores to 0-1 range
            text_score = min(text_score, 1.0)
            semantic_score = min(semantic_score, 1.0)
            
            # Calculate weighted hybrid score
            hybrid_score = (1 - semantic_weight) * text_score + semantic_weight * semantic_score
            result['hybrid_score'] = hybrid_score
        
        # Convert to list and sort by hybrid score
        combined_results = list(result_map.values())
        combined_results.sort(key=lambda x: x.get('hybrid_score', 0.0), reverse=True)
        
        return combined_results
    
    def _apply_filters(self, results: List[Dict], filters: Dict) -> List[Dict]:
        """
        Apply metadata filters to search results.
        
        Args:
            results: List of search results
            filters: Dictionary of field-value filters
            
        Returns:
            Filtered results
        """
        filtered_results = []
        
        for result in results:
            include_result = True
            
            for field, value in filters.items():
                if field in result:
                    if isinstance(value, list):
                        if result[field] not in value:
                            include_result = False
                            break
                    else:
                        if result[field] != value:
                            include_result = False
                            break
            
            if include_result:
                filtered_results.append(result)
        
        return filtered_results
    
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