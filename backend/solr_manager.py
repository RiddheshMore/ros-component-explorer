"""
Apache Solr Database Manager for the ROS Component Explorer.

Handles data loading and search queries for ROS component information using Apache Solr.
Provides functionality for:
- Loading ROS component data from TTL/RDF knowledge graphs
- Indexing components in Solr for full-text search
- Supporting both traditional text search and vector-based semantic search
- Managing component metadata, properties, and relationships
"""

import json
import logging
from typing import List, Dict, Optional, Tuple
from pysolr import Solr
import rdflib
from rdflib import Graph, Namespace, RDF, RDFS, URIRef
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SOLR_URL = "http://localhost:8984/solr/ros_explorer"
ROS = Namespace("http://www.ros.org/ontology#")
DCTERMS = Namespace("http://purl.org/dc/terms/")

class SolrManager:
    """
    Manages the Apache Solr search engine for ROS components.
    
    Provides comprehensive database functionality including:
    - TTL/RDF data loading and parsing
    - Component indexing with metadata
    - Text-based and semantic search capabilities
    - Component relationship management
    """
    
    def __init__(self, ttl_file: str):
        self.ttl_file = ttl_file
        self.solr_url = SOLR_URL  # Store Solr URL for direct API calls
        self.solr = Solr(SOLR_URL, timeout=10)
        self._ensure_data_loaded()
    
    def _ensure_data_loaded(self):
        """
        Ensure ROS component data is loaded into Solr.
        
        Checks if Solr already contains indexed data, and if not,
        loads and indexes the TTL/RDF knowledge graph data.
        """
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
    
    def _extract_components_from_graph(self, g: Graph, is_additional_file: bool = False):
        """
        Extract component data from an RDF graph and convert to Solr documents.
        
        Args:
            g: The RDF graph to process
            is_additional_file: Whether this is an additional file being loaded
        
        Returns:
            List of component dictionaries ready for Solr indexing
        """
        # Use global namespaces
        
        # Extract component data
        components = []
        
        # Find all component instances
        logger.info("Looking for component instances...")
        component_types = [
            ROS.LocalizationComponent,
            ROS.NavigationComponent,
            ROS.SensorDriverComponent,
            ROS.PathPlannerComponent,
            ROS.ControllerComponent,
            ROS.PerceptionComponent,
            ROS.IntegrationComponent,
            # Add Package types for hierarchical TTL compatibility
            ROS.LocalizationPackage,
            ROS.NavigationPackage,
            ROS.SensorPackage,
            ROS.PathPlannerPackage,
            ROS.ControlPackage,  # Fixed: was ControllerPackage
            ROS.PerceptionPackage,
            ROS.IntegrationPackage,
            ROS.MappingPackage,
            ROS.UtilityPackage,
            ROS.ManipulationPackage,
            ROS.SimulationPackage  # Added for simulation environment support
        ]
        
        # Add additional component types for expanded files
        if is_additional_file:
            component_types.extend([
                ROS.ManipulationComponent,
                ROS.SimulationComponent
            ])
        
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
                
                # Get update rate and handle non-numeric values
                update_rate = None
                for _, _, rate_obj in g.triples((component_uri, ROS.hasUpdateRate, None)):
                    rate_str = str(rate_obj)
                    # Try to parse as float, if it fails use "0.0"
                    try:
                        float(rate_str)
                        update_rate = rate_str
                    except ValueError:
                        update_rate = "0.0"  # Default for non-numeric values
                    break
                
                # Get ROS version
                ros_version = None
                for _, _, version_obj in g.triples((component_uri, ROS.rosVersion, None)):
                    ros_version = str(version_obj)
                    break
                
                # Get repository URL (check both repositoryURL and repositoryUrl)
                repository_url = None
                for _, _, repo_obj in g.triples((component_uri, ROS.repositoryURL, None)):
                    repository_url = str(repo_obj)
                    break
                if not repository_url:
                    for _, _, repo_obj in g.triples((component_uri, ROS.repositoryUrl, None)):
                        repository_url = str(repo_obj)
                        break
                
                # Get maintainer
                maintainer = None
                for _, _, maintainer_obj in g.triples((component_uri, ROS.maintainer, None)):
                    maintainer = str(maintainer_obj)
                    break
                
                # Get license type
                license_type = None
                for _, _, license_obj in g.triples((component_uri, ROS.licenseType, None)):
                    license_type = str(license_obj)
                    break
                
                # Get last updated date
                last_updated = None
                for _, _, date_obj in g.triples((component_uri, ROS.lastUpdated, None)):
                    last_updated = str(date_obj)
                    break
                
                # Get package version
                package_version = None
                for _, _, version_obj in g.triples((component_uri, ROS.packageVersion, None)):
                    package_version = str(version_obj)
                    break
                
                # Get distribution
                distribution = None
                for _, _, dist_obj in g.triples((component_uri, ROS.distribution, None)):
                    distribution = str(dist_obj)
                    break
                
                # Get primary function
                primary_function = None
                for _, _, func_obj in g.triples((component_uri, ROS.primaryFunction, None)):
                    primary_function = str(func_obj)
                    break
                
                # Get implemented algorithms
                algorithms = []
                for _, _, algo_obj in g.triples((component_uri, ROS.implementsAlgorithm, None)):
                    algo_name = str(algo_obj)
                    if algo_name not in algorithms:
                        algorithms.append(algo_name)
                
                # Get required hardware
                required_hardware = []
                for _, _, hw_obj in g.triples((component_uri, ROS.requiresHardware, None)):
                    hw_name = str(hw_obj).split('#')[-1] if '#' in str(hw_obj) else str(hw_obj)
                    if hw_name not in required_hardware:
                        required_hardware.append(hw_name)
                
                # Get supported hardware
                supported_hardware = []
                for _, _, hw_obj in g.triples((component_uri, ROS.supportsHardware, None)):
                    hw_name = str(hw_obj).split('#')[-1] if '#' in str(hw_obj) else str(hw_obj)
                    if hw_name not in supported_hardware:
                        supported_hardware.append(hw_name)
                
                # Get dependencies (both build and runtime)
                dependencies = []
                for _, _, dep_obj in g.triples((component_uri, ROS.buildDependsOn, None)):
                    dep_name = str(dep_obj).split('#')[-1] if '#' in str(dep_obj) else str(dep_obj)
                    if dep_name not in dependencies:
                        dependencies.append(dep_name)
                for _, _, dep_obj in g.triples((component_uri, ROS.runtimeDependsOn, None)):
                    dep_name = str(dep_obj).split('#')[-1] if '#' in str(dep_obj) else str(dep_obj)
                    if dep_name not in dependencies:
                        dependencies.append(dep_name)
                
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
                
                # Generate tags from package data
                tags = []
                # Add type as tag (lowercase)
                if type_name:
                    tags.append(type_name.lower().replace('package', ''))
                # Add tags based on topics
                topic_keywords = {
                    'laser': 'lidar', 'lidar': 'lidar', 'scan': 'lidar',
                    'pointcloud': 'pointcloud', 'point_cloud': 'pointcloud',
                    'image': 'camera', 'camera': 'camera',
                    'imu': 'imu',
                    'odom': 'odometry', 'odometry': 'odometry',
                    'cmd_vel': 'control', 'twist': 'control',
                    'map': 'mapping', 'occupancygrid': 'mapping',
                    'pose': 'localization', 'amcl': 'localization',
                    'path': 'navigation', 'goal': 'navigation',
                    'tf': 'transform', 'transform': 'transform'
                }
                for topic in subscribed_topics + published_topics:
                    topic_lower = topic.lower()
                    for keyword, tag in topic_keywords.items():
                        if keyword in topic_lower and tag not in tags:
                            tags.append(tag)
                # Add tags from description
                desc_lower = (description or '').lower()
                if 'slam' in desc_lower and 'slam' not in tags:
                    tags.append('slam')
                if 'planning' in desc_lower and 'planning' not in tags:
                    tags.append('planning')
                if 'autonomous' in desc_lower and 'autonomous' not in tags:
                    tags.append('autonomous')
                if 'perception' in desc_lower and 'perception' not in tags:
                    tags.append('perception')
                # Add simulation-specific tags
                if 'simulation' in type_name.lower() or 'simulator' in desc_lower:
                    if 'simulation' not in tags:
                        tags.append('simulation')
                if any(word in desc_lower for word in ['physics', 'gazebo', 'isaac', 'webots', 'unity', 'coppeliasim', 'stage']) and 'physics' not in tags:
                    tags.append('physics')
                if 'rendering' in desc_lower or 'visualization' in desc_lower or '3d' in desc_lower:
                    if 'visualization' not in tags:
                        tags.append('visualization')
                if 'sensor simulation' in desc_lower or 'sensor emulation' in desc_lower:
                    if 'sensor-emulation' not in tags:
                        tags.append('sensor-emulation')
                
                # Create Solr document
                doc = {
                    'id': str(component_uri),
                    'name': label,
                    'type': type_name,
                    'description': description or "No description available",
                    'package': package or "Unknown package",
                    'update_rate': update_rate or "0.0",  # Default to "0.0" for missing values
                    'ros_version': ros_version or "Unknown",
                    'repository_url': repository_url or "",
                    'author': maintainer or "Unknown",  # UI expects 'author' field
                    'license': license_type or "Unknown",  # UI expects 'license' field
                    'last_updated': last_updated or "Unknown",
                    'package_version': package_version or "Unknown",
                    'distribution': distribution or "Unknown",
                    'primary_function': primary_function or "",
                    'algorithms': algorithms,  # List of implemented algorithms
                    'required_hardware': required_hardware,  # List of required hardware
                    'supported_hardware': supported_hardware,  # List of supported hardware
                    'dependencies': dependencies,  # List of dependencies
                    'dependencies_count': len(dependencies),  # Count for UI
                    'tags': tags,  # Generated tags
                    'subscribed_topics': subscribed_topics,
                    'published_topics': published_topics,
                    'content': f"{label} {type_name} {description or ''} {package or ''} {' '.join(subscribed_topics)} {' '.join(published_topics)} {' '.join(tags)} {' '.join(algorithms)} {primary_function or ''}"
                }
                
                logger.info(f"Created document for {label}: {doc}")
                components.append(doc)
            
            type_counts[type_name] = count
        
        # Log component type statistics
        logger.info(f"Component type counts: {type_counts}")
        logger.info(f"Total components found: {len(components)}")
        return components
        
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
        
        # Extract and index components
        components = self._extract_components_from_graph(g)
        
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
            
    def load_additional_ttl_file(self, ttl_file_path: str):
        """
        Load an additional TTL file into Solr without clearing existing data.
        
        Args:
            ttl_file_path: Path to the additional TTL file
        """
        # Parse the TTL file
        g = Graph()
        try:
            logger.info(f"Parsing additional TTL file: {ttl_file_path}")
            g.parse(ttl_file_path, format="turtle")
            logger.info(f"Additional TTL file parsed successfully. Graph has {len(g)} triples.")
        except Exception as e:
            logger.error(f"Error parsing additional TTL file: {e}")
            raise
            
        # Extract components from the additional file
        components = self._extract_components_from_graph(g, is_additional_file=True)
        
        # Index documents in Solr
        if components:
            try:
                logger.info(f"Indexing {len(components)} additional documents in Solr...")
                self.solr.add(components)
                self.solr.commit()
                logger.info(f"Successfully indexed {len(components)} additional components in Solr")
            except Exception as e:
                logger.error(f"Error indexing additional documents in Solr: {e}")
                raise
        else:
            logger.warning("No additional components found to index!")
    
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
                    solr_doc['content_vector'] = component.get('vector', [])
                else:
                    # If document doesn't exist, create minimal doc with vector
                    solr_doc = {
                        'id': doc_id,
                        'content_vector': component.get('vector', [])
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
    
    def get_all_components(self, max_results: int = 1000) -> List[Dict]:
        """Get all components from Solr."""
        try:
            results = self.solr.search("*:*", rows=max_results)
            components = []
            for doc in results.docs:
                components.append({
                    'id': doc.get('id', ''),
                    'uri': doc.get('id', ''),
                    'name': doc.get('name', ''),
                    'type': doc.get('type', ''),
                    'class': doc.get('type', ''),
                    'description': doc.get('description', 'No description available'),
                    'package': doc.get('package', 'Unknown'),
                    'ros_version': doc.get('ros_version', 'Unknown'),
                    'update_rate': doc.get('update_rate', '0.0'),
                    'repository_url': doc.get('repository_url', ''),
                    'published_topics': doc.get('published_topics', []),
                    'subscribed_topics': doc.get('subscribed_topics', []),
                    # Add all new metadata fields
                    'distribution': doc.get('distribution', 'Unknown'),
                    'package_version': doc.get('package_version', 'Unknown'),
                    'last_updated': doc.get('last_updated', 'Unknown'),
                    'algorithms': doc.get('algorithms', []),
                    'required_hardware': doc.get('required_hardware', []),
                    'supported_hardware': doc.get('supported_hardware', []),
                    'primary_function': doc.get('primary_function', 'Unknown'),
                    'maintainer': doc.get('maintainer', 'Unknown'),
                    'author': doc.get('author', 'Unknown'),
                    'license': doc.get('license', 'Unknown')
                })
            return components
        except Exception as e:
            logger.error(f"Error getting all components: {e}")
            return []
    
    def search_components(self, search_term: str, max_results: int = 1000) -> List[Dict]:
        """Search components by term using traditional text search (BM25)."""
        if not search_term.strip():
            return self.get_all_components()
        
        try:
            # Check if this is already a structured Solr query
            if any(field in search_term for field in ['name:', 'type:', 'content:', 'description:']):
                # This is already a structured query, use it directly
                query = search_term
            else:
                # Split query into tokens and search for individual words (like BM25)
                # This provides better recall for natural language queries
                tokens = search_term.lower().split()
                # Filter out common stopwords for better precision
                stopwords = {'i', 'me', 'my', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
                meaningful_tokens = [t for t in tokens if t not in stopwords and len(t) > 2]
                
                if not meaningful_tokens:
                    # If all tokens are stopwords, use original search_term
                    query = f"content:({search_term})"
                else:
                    # Build query with individual tokens (OR across tokens, AND across fields)
                    token_query = ' OR '.join(meaningful_tokens)
                    query = f"content:({token_query}) OR description:({token_query}) OR name:({token_query})"
            
            results = self.solr.search(query, rows=max_results)
            
            components = []
            for doc in results.docs:
                # Extract values from lists (Solr returns multi-valued fields as lists)
                name = doc.get('name', [''])[0] if isinstance(doc.get('name'), list) else doc.get('name', '')
                pkg_type = doc.get('type', [''])[0] if isinstance(doc.get('type'), list) else doc.get('type', '')
                description = doc.get('description', ['No description available'])[0] if isinstance(doc.get('description'), list) else doc.get('description', 'No description available')
                
                components.append({
                    'id': doc.get('id', ''),
                    'uri': doc.get('id', ''),
                    'name': name,
                    'type': pkg_type,
                    'class': pkg_type,
                    'description': description,
                    'package': doc.get('package', 'Unknown'),
                    'ros_version': doc.get('ros_version', 'Unknown'),
                    'update_rate': doc.get('update_rate', '0.0'),
                    'repository_url': doc.get('repository_url', ''),
                    'published_topics': doc.get('published_topics', []),
                    'subscribed_topics': doc.get('subscribed_topics', []),
                    'relevance_score': doc.get('score', 0.0),
                    'search_type': 'text',
                    # Add all new metadata fields
                    'distribution': doc.get('distribution', 'Unknown'),
                    'package_version': doc.get('package_version', 'Unknown'),
                    'last_updated': doc.get('last_updated', 'Unknown'),
                    'algorithms': doc.get('algorithms', []),
                    'required_hardware': doc.get('required_hardware', []),
                    'supported_hardware': doc.get('supported_hardware', []),
                    'primary_function': doc.get('primary_function', 'Unknown'),
                    'maintainer': doc.get('maintainer', 'Unknown'),
                    'author': doc.get('author', 'Unknown'),
                    'license': doc.get('license', 'Unknown')
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
            # Check if content_vector field exists (our dense vector field)
            if fields and "content_vector" in fields:
                # Check if knn_vector field type exists
                field_types = updater.list_field_types()
                if field_types:
                    # Look for our knn_vector_384 field type
                    has_knn_type = 'knn_vector_384' in field_types
                    if has_knn_type:
                        logger.info("Found proper dense vector field 'content_vector' with knn_vector_384 type")
                    return has_knn_type
            return False
        except Exception as e:
            logger.warning(f"Could not determine vector field type: {e}")
            return False
    
    def _knn_semantic_search(self, query_vector: List[float], k: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        """Perform KNN-based semantic search using Solr's native dense vector field."""
        import requests
        
        # Convert vector to string format for Solr
        vector_str = "[" + ",".join(str(v) for v in query_vector) + "]"
        
        # Build k-NN query using JSON Query DSL
        query_json = {
            "query": f"{{!knn f=content_vector topK={k}}}{vector_str}",
            "fields": "id,name,type,description,package,ros_version,repository_url,subscribed_topics,published_topics,score,distribution,package_version,last_updated,algorithms,required_hardware,supported_hardware,primary_function,maintainer,author,license",
            "limit": k
        }
        
        # Add filters if provided
        if filters:
            filter_queries = []
            for field, value in filters.items():
                if isinstance(value, list):
                    filter_queries.append(f"{field}:({' OR '.join(value)})")
                else:
                    filter_queries.append(f"{field}:{value}")
            if filter_queries:
                query_json["filter"] = filter_queries
        
        logger.info(f"Executing KNN semantic search (k={k})")
        
        # Execute search using JSON API
        try:
            response = requests.post(
                f"{self.solr_url}/query",
                json=query_json,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code != 200:
                logger.error(f"KNN search failed: {response.text}")
                return []
            
            data = response.json()
            docs = data.get('response', {}).get('docs', [])
            
            components = []
            for doc in docs:
                components.append({
                    'uri': doc.get('id', ''),
                    'name': doc.get('name', ''),
                    'class': doc.get('type', ''),
                    'description': doc.get('description', 'No description available'),
                    'score': doc.get('score', 0.0),
                    'package': doc.get('package', ''),
                    'ros_version': doc.get('ros_version', ''),
                    'repository_url': doc.get('repository_url', ''),
                    'subscribed_topics': doc.get('subscribed_topics', []),
                    'published_topics': doc.get('published_topics', []),
                    'type': doc.get('type', ''),
                    # Add all new metadata fields
                    'distribution': doc.get('distribution', 'Unknown'),
                    'package_version': doc.get('package_version', 'Unknown'),
                    'last_updated': doc.get('last_updated', 'Unknown'),
                    'algorithms': doc.get('algorithms', []),
                    'required_hardware': doc.get('required_hardware', []),
                    'supported_hardware': doc.get('supported_hardware', []),
                    'primary_function': doc.get('primary_function', 'Unknown'),
                    'maintainer': doc.get('maintainer', 'Unknown'),
                    'author': doc.get('author', 'Unknown'),
                    'license': doc.get('license', 'Unknown')
                })
            
            # Log results
            top_results = [f"{r.get('name', 'unknown')}: {r.get('score', 0):.3f}" for r in components[:3]]
            logger.info(f"KNN semantic search returned {len(components)} results: {top_results}")
            return components
            
        except Exception as e:
            logger.error(f"Error in KNN search: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _text_based_semantic_search(self, query_vector: List[float], k: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Perform semantic search using Python-based vector similarity.
        Since Solr doesn't have native vector field support, we compute similarity in Python.
        """
        try:
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity
            
            logger.info("Using Python-based vector similarity search (Solr vector field not available)")
            
            # Get all components with their vectors
            all_results = self.solr.search("*:*", rows=1000)
            
            if not all_results.docs:
                logger.warning("No components found in Solr")
                return []
            
            # Convert query vector to numpy array
            query_vec_np = np.array(query_vector).reshape(1, -1)
            
            # Score components based on vector similarity
            scored_components = []
            
            for doc in all_results.docs:
                try:
                    # Apply filters if provided
                    if filters:
                        passes_filters = True
                        for field, value in filters.items():
                            doc_value = doc.get(field, '')
                            if isinstance(value, list):
                                if doc_value not in value:
                                    passes_filters = False
                                    break
                            else:
                                if doc_value != value:
                                    passes_filters = False
                                    break
                        if not passes_filters:
                            continue
                    
                    # Get component vector if available (check both vector and content_vector fields)
                    component_vector = doc.get('content_vector', doc.get('vector', []))
                    
                    # Calculate similarity score
                    if component_vector and len(component_vector) > 0:
                        try:
                            # Parse vector if it's a string
                            if isinstance(component_vector, str):
                                component_vector = eval(component_vector)
                            
                            # Compute cosine similarity
                            doc_vec_np = np.array(component_vector).reshape(1, -1)
                            similarity = cosine_similarity(query_vec_np, doc_vec_np)[0, 0]
                            score = max(0.0, min(1.0, similarity))  # Clamp to 0-1
                        except:
                            # If vector parsing fails, use default score
                            score = 0.5
                    else:
                        # Default score if no vector available
                        score = 0.3
                    
                    scored_components.append({
                        'uri': doc.get('id', ''),
                        'name': doc.get('name', ''),
                        'class': doc.get('type', ''),
                        'description': doc.get('description', 'No description available'),
                        'score': score,
                        'package': doc.get('package', ''),
                        'ros_version': doc.get('ros_version', ''),
                        'repository_url': doc.get('repository_url', ''),
                        'subscribed_topics': doc.get('subscribed_topics', []),
                        'published_topics': doc.get('published_topics', []),
                        'type': doc.get('type', ''),
                        # Add all new metadata fields
                        'distribution': doc.get('distribution', 'Unknown'),
                        'package_version': doc.get('package_version', 'Unknown'),
                        'last_updated': doc.get('last_updated', 'Unknown'),
                        'algorithms': doc.get('algorithms', []),
                        'required_hardware': doc.get('required_hardware', []),
                        'supported_hardware': doc.get('supported_hardware', []),
                        'primary_function': doc.get('primary_function', 'Unknown'),
                        'maintainer': doc.get('maintainer', 'Unknown'),
                        'author': doc.get('author', 'Unknown'),
                        'license': doc.get('license', 'Unknown')
                    })
                
                except Exception as e:
                    logger.debug(f"Error scoring component: {e}")
                    continue
            
            # Sort by score
            scored_components.sort(key=lambda x: x.get('score', 0.0), reverse=True)
            
            # Return top k results
            result = scored_components[:k]
            
            # Log results
            top_results = [f"{r.get('name', 'unknown')[:30]}: {r.get('score', 0):.3f}" for r in result[:3]]
            logger.info(f"Vector-based semantic search returned {len(result)} results with scores: {top_results}")
            return result
            
        except Exception as e:
            logger.error(f"Error in vector-based semantic search: {e}")
            import traceback
            traceback.print_exc()
            # Final fallback - just return first k components
            try:
                all_results = self.solr.search("*:*", rows=k)
                return [{
                    'uri': doc.get('id', ''),
                    'name': doc.get('name', ''),
                    'class': doc.get('type', ''),
                    'description': doc.get('description', 'No description available'),
                    'score': 0.5,
                    'type': doc.get('type', '')
                } for doc in all_results.docs]
            except:
                return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            import math
            
            # Ensure vectors have the same length
            if len(vec1) != len(vec2):
                return 0.0
            
            # Calculate dot product
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            
            # Calculate magnitudes
            magnitude1 = math.sqrt(sum(a * a for a in vec1))
            magnitude2 = math.sqrt(sum(b * b for b in vec2))
            
            # Avoid division by zero
            if magnitude1 == 0.0 or magnitude2 == 0.0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = dot_product / (magnitude1 * magnitude2)
            return max(0.0, min(1.0, similarity))  # Clamp between 0 and 1
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
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
            # Perform text search (limit to k*5 to avoid processing 1000s of results)
            # This significantly improves performance while maintaining search quality
            text_results = self.search_components(text_query, max_results=k*5)
            
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
            Combined and ranked results ranked by hybrid score
        """
        # Create a mapping of URI to results
        result_map = {}
        
        # Add text search results with their actual BM25 scores
        text_weight = 1.0 - semantic_weight
        max_text_score = max([r.get('relevance_score', 0.0) for r in text_results]) if text_results else 1.0
        
        for i, result in enumerate(text_results):
            uri = result['uri']
            if uri not in result_map:
                result_map[uri] = result.copy()
                # Use actual BM25 relevance score (normalized)
                raw_score = result.get('relevance_score', 0.0)
                normalized_score = raw_score / max_text_score if max_text_score > 0 else 0.0
                result_map[uri]['text_score'] = normalized_score
                result_map[uri]['semantic_score'] = 0.0
                result_map[uri]['is_text_match'] = True
                result_map[uri]['hybrid_score'] = 0.0
        
        # Add semantic search results
        for i, result in enumerate(semantic_results):
            uri = result['uri']
            semantic_score = result.get('score', 0.0)
            
            if uri in result_map:
                # Update semantic score for text matches
                result_map[uri]['semantic_score'] = semantic_score
            else:
                # Non-text-matching results
                result_map[uri] = result.copy()
                result_map[uri]['text_score'] = 0.0
                result_map[uri]['semantic_score'] = semantic_score
                result_map[uri]['is_text_match'] = False
                result_map[uri]['hybrid_score'] = 0.0
        
        # Calculate hybrid scores - giving preference to text matches
        for result in result_map.values():
            text_score = result.get('text_score', 0.0)
            semantic_score = result.get('semantic_score', 0.0)
            is_text_match = result.get('is_text_match', False)
            
            # Normalize scores to 0-1 range
            text_score = min(text_score, 1.0)
            semantic_score = min(semantic_score, 1.0)
            
            # Calculate weighted hybrid score
            # Prioritize semantic relevance while giving slight preference to text matches
            if is_text_match:
                # Text matches get small boost, but semantic score is primary
                hybrid_score = text_weight * text_score + semantic_weight * semantic_score + 0.02
            else:
                # Non-text matches rely only on semantic relevance
                hybrid_score = semantic_weight * semantic_score
            
            result['hybrid_score'] = min(1.0, hybrid_score)  # Cap at 1.0
        
        # Convert to list and sort by hybrid score
        combined_results = list(result_map.values())
        combined_results.sort(key=lambda x: x.get('hybrid_score', 0.0), reverse=True)
        
        logger.info(f"Combined {len(text_results)} text results with {len(semantic_results)} semantic results -> {len(combined_results)} total")
        logger.info(f"Top 3 combined scores: {[f'{r.get('name', 'unknown')[:30]}: {r.get('hybrid_score', 0):.3f}' for r in combined_results[:3]]}")
        
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