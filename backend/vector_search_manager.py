"""
Enhanced Vector-Based Search Manager for ROS Component Explorer.

This module implements proper vector-based k-NN search for ROS components:
1. Loads all packages as dense vector embeddings into Solr
2. Converts user queries into vectors using the same embedding model
3. Uses k-NN similarity search to find the most relevant packages
4. Combines semantic search with traditional text search for hybrid results
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
import json

from backend.solr_manager import SolrManager
from backend.vector_generator import VectorGenerator
from backend.schema_updater import SolrSchemaUpdater

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorSearchManager:
    """
    Manages vector-based semantic search for ROS components.
    
    Provides enhanced search capabilities by:
    - Loading components as dense vector embeddings
    - Converting user queries to vectors
    - Performing k-NN similarity search
    - Combining semantic and text-based results
    """
    
    def __init__(self, ttl_file: str, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the vector search manager.
        
        Args:
            ttl_file: Path to the TTL knowledge base file
            model_name: Name of the Sentence-BERT model for embeddings
        """
        self.ttl_file = ttl_file
        self.model_name = model_name
        
        # Initialize components
        self.solr_manager = SolrManager(ttl_file)
        self.vector_generator = VectorGenerator(model_name)
        self.schema_updater = SolrSchemaUpdater()
        
        # Ensure vector support is set up
        self._setup_vector_support()
        
        # Load and vectorize components if needed
        self._ensure_components_vectorized()
        
    def _setup_vector_support(self):
        """Set up Solr schema to support vector fields."""
        try:
            logger.info("Setting up vector support in Solr schema...")
            
            # Add vector field to schema
            vector_dim = self.vector_generator.get_vector_dimension()
            success = self.schema_updater.add_vector_field("vector", vector_dim)
            
            if success:
                logger.info(f"Vector field added successfully (dimension: {vector_dim})")
            else:
                logger.warning("Could not add proper vector field, will use fallback")
                
        except Exception as e:
            logger.error(f"Error setting up vector support: {e}")
            
    def _ensure_components_vectorized(self):
        """Ensure all components in Solr have vector embeddings."""
        try:
            # Check if components already have vectors
            if self._components_have_vectors():
                logger.info("Components already have vector embeddings")
                return
                
            logger.info("Generating vector embeddings for all components...")
            
            # Get all components from Solr
            all_components = self.solr_manager.get_all_components()
            
            if not all_components:
                logger.warning("No components found in Solr")
                return
                
            # Generate embeddings
            components_with_vectors = self.vector_generator.generate_embeddings(all_components)
            
            # Update Solr documents with vectors
            success = self.solr_manager.add_vectors_to_documents(components_with_vectors)
            
            if success:
                logger.info(f"Successfully added vector embeddings to {len(components_with_vectors)} components")
            else:
                logger.error("Failed to add vector embeddings to Solr")
                
        except Exception as e:
            logger.error(f"Error ensuring components are vectorized: {e}")
            
    def _components_have_vectors(self) -> bool:
        """Check if components in Solr already have vector embeddings."""
        try:
            # Query for a few documents with vector field
            results = self.solr_manager.solr.search("*:*", fl="id,vector", rows=5)
            
            # Check if any document has a non-empty vector field
            for doc in results.docs:
                if 'vector' in doc and doc['vector']:
                    return True
                    
            return False
            
        except Exception as e:
            logger.warning(f"Could not check if components have vectors: {e}")
            return False
            
    def vector_search(self, query: str, k: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Perform vector-based semantic search for a user query.
        
        Args:
            query: User's natural language query
            k: Number of top results to return
            filters: Optional filters for component metadata
            
        Returns:
            List of most relevant components based on semantic similarity
        """
        try:
            logger.info(f"Performing vector search for query: '{query}'")
            
            # Convert query to vector
            query_vector = self._query_to_vector(query)
            
            if query_vector is None:
                logger.error("Failed to convert query to vector")
                return []
                
            # Perform k-NN semantic search
            results = self.solr_manager.semantic_search(query_vector, k, filters)
            
            logger.info(f"Vector search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
            
    def _query_to_vector(self, query: str) -> Optional[List[float]]:
        """
        Convert a user query string to a vector embedding.
        
        Args:
            query: User's natural language query
            
        Returns:
            Vector embedding as list of floats, or None if conversion fails
        """
        try:
            # Use the same model as used for component embeddings
            embedding = self.vector_generator.model.encode([query], convert_to_numpy=True)[0]
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error converting query to vector: {e}")
            return None
            
    def hybrid_search(self, query: str, k: int = 10, filters: Optional[Dict] = None, 
                     semantic_weight: float = 0.7) -> List[Dict]:
        """
        Perform hybrid search combining vector similarity and text search.
        
        Args:
            query: User's natural language query
            k: Number of top results to return
            filters: Optional filters for component metadata
            semantic_weight: Weight for semantic similarity (0.0 to 1.0)
            
        Returns:
            List of components ranked by hybrid relevance score
        """
        try:
            logger.info(f"Performing hybrid search for query: '{query}'")
            
            # Get vector representation
            query_vector = self._query_to_vector(query)
            
            if query_vector is None:
                # Fallback to text search only
                logger.warning("Vector conversion failed, using text search only")
                return self.solr_manager.search_components(query)
                
            # Perform hybrid search
            results = self.solr_manager.hybrid_search(
                text_query=query,
                query_vector=query_vector,
                k=k,
                filters=filters,
                semantic_weight=semantic_weight
            )
            
            logger.info(f"Hybrid search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []
            
    def find_similar_components(self, component_id: str, k: int = 5) -> List[Dict]:
        """
        Find components similar to a given component using vector similarity.
        
        Args:
            component_id: ID of the reference component
            k: Number of similar components to return
            
        Returns:
            List of similar components
        """
        try:
            # Get the reference component's vector
            component_data = self.solr_manager.get_component_details(component_id)
            
            if not component_data or 'vector' not in component_data:
                logger.error(f"Component {component_id} not found or has no vector")
                return []
                
            component_vector = component_data['vector']
            
            # Find similar components
            results = self.solr_manager.semantic_search(component_vector, k + 1)  # +1 to exclude self
            
            # Remove the reference component from results
            similar_components = [r for r in results if r.get('uri') != component_id][:k]
            
            logger.info(f"Found {len(similar_components)} similar components to {component_id}")
            return similar_components
            
        except Exception as e:
            logger.error(f"Error finding similar components: {e}")
            return []
            
    def get_component_clusters(self, num_clusters: int = 10) -> Dict[str, List[Dict]]:
        """
        Group components into clusters based on vector similarity.
        
        Args:
            num_clusters: Number of clusters to create
            
        Returns:
            Dictionary mapping cluster labels to lists of components
        """
        try:
            from sklearn.cluster import KMeans
            
            logger.info(f"Clustering components into {num_clusters} groups...")
            
            # Get all components with vectors
            all_components = self.solr_manager.get_all_components()
            components_with_vectors = [c for c in all_components if 'vector' in c and c['vector']]
            
            if len(components_with_vectors) < num_clusters:
                logger.warning(f"Not enough components with vectors ({len(components_with_vectors)}) for {num_clusters} clusters")
                return {}
                
            # Extract vectors
            vectors = np.array([c['vector'] for c in components_with_vectors])
            
            # Perform clustering
            kmeans = KMeans(n_clusters=num_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(vectors)
            
            # Group components by cluster
            clusters = {}
            for i, component in enumerate(components_with_vectors):
                cluster_id = f"cluster_{cluster_labels[i]}"
                if cluster_id not in clusters:
                    clusters[cluster_id] = []
                clusters[cluster_id].append(component)
                
            logger.info(f"Created {len(clusters)} clusters")
            return clusters
            
        except Exception as e:
            logger.error(f"Error clustering components: {e}")
            return {}
            
    def reindex_vectors(self):
        """Re-generate and update all vector embeddings."""
        try:
            logger.info("Re-indexing all vector embeddings...")
            
            # Get all components
            all_components = self.solr_manager.get_all_components()
            
            # Generate fresh embeddings
            components_with_vectors = self.vector_generator.generate_embeddings(all_components)
            
            # Update Solr
            success = self.solr_manager.add_vectors_to_documents(components_with_vectors)
            
            if success:
                logger.info(f"Successfully re-indexed {len(components_with_vectors)} components")
            else:
                logger.error("Failed to re-index vector embeddings")
                
        except Exception as e:
            logger.error(f"Error re-indexing vectors: {e}")
            
    def get_search_stats(self) -> Dict[str, any]:
        """Get statistics about the vector search setup."""
        try:
            stats = {
                "total_components": 0,
                "components_with_vectors": 0,
                "vector_dimension": self.vector_generator.get_vector_dimension(),
                "model_name": self.model_name,
                "vector_field_available": self.solr_manager._has_proper_vector_field()
            }
            
            # Count components
            all_components = self.solr_manager.get_all_components()
            stats["total_components"] = len(all_components)
            
            # Count components with vectors
            components_with_vectors = [c for c in all_components if 'vector' in c and c['vector']]
            stats["components_with_vectors"] = len(components_with_vectors)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting search stats: {e}")
            return {}
