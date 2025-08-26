"""
Vector Integration and Hybrid Search Demonstration for ROS Component Explorer.
This script demonstrates the complete workflow from generating embeddings to performing hybrid search.
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict
import requests # Added for field verification

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.vector_generator import VectorGenerator
from backend.schema_updater import SolrSchemaUpdater
from backend.solr_manager import SolrManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorIntegrationDemo:
    """Demonstrates vector integration and hybrid search capabilities."""
    
    def __init__(self):
        self.vector_generator = VectorGenerator()
        self.schema_updater = SolrSchemaUpdater()
        self.solr_manager = SolrManager("data/components_clean.ttl")
    
    def run_complete_demo(self):
        """Run the complete demonstration workflow."""
        logger.info("=" * 60)
        logger.info("ROS Component Explorer - Vector Integration Demo")
        logger.info("=" * 60)
        
        try:
            # Step 1: Update Solr schema to support vectors
            self._update_schema()
            
            # Step 2: Generate vector embeddings
            components_with_vectors = self._generate_embeddings()
            
            # Step 3: Add vectors to Solr documents
            self._add_vectors_to_solr(components_with_vectors)
            
            # Step 4: Demonstrate different search types
            self._demonstrate_search_capabilities()
            
            logger.info("=" * 60)
            logger.info("Demo completed successfully!")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            raise
    
    def _update_schema(self):
        """Update Solr schema to add vector field."""
        logger.info("\nStep 1: Updating Solr Schema")
        logger.info("-" * 40)
        
        # Check Solr version first
        solr_version = self.schema_updater.get_solr_version()
        if solr_version:
            logger.info(f"Detected Solr version: {solr_version}")
        
        # List available field types
        field_types = self.schema_updater.list_field_types()
        if field_types:
            logger.info(f"Available field types: {', '.join(field_types[:10])}...")
            if len(field_types) > 10:
                logger.info(f"... and {len(field_types) - 10} more")
        
        # Check if vector field already exists
        if self.schema_updater.check_field_exists("vector"):
            logger.info("Vector field already exists in schema")
            
            # Check if the field needs to be recreated (wrong configuration)
            logger.info("Checking vector field configuration...")
            try:
                from backend.schema_updater import SolrSchemaUpdater
                updater = SolrSchemaUpdater()
                fields = updater.list_fields()
                if fields and "vector" in fields:
                    # Get field details to check configuration
                    response = requests.get("http://localhost:8984/solr/ros_explorer/schema/fields/vector")
                    if response.status_code == 200:
                        field_info = response.json()
                        is_multi_valued = field_info.get('multiValued', False)
                        if not is_multi_valued:
                            logger.warning("Vector field exists but is not multiValued. Recreating...")
                            # Delete and recreate the field
                            if updater.delete_field("vector"):
                                logger.info("Deleted existing vector field")
                            else:
                                logger.error("Failed to delete existing vector field")
                                return
                        else:
                            logger.info("Vector field configuration is correct")
                            return
            except Exception as e:
                logger.warning(f"Could not verify field configuration: {e}")
                # Continue with field creation/recreation
        
        # Get vector dimension from the model
        vector_dim = self.vector_generator.get_vector_dimension()
        logger.info(f"Vector dimension: {vector_dim}")
        
        # Try to add vector field with automatic field type detection
        success = self.schema_updater.add_vector_field("vector", vector_dim)
        if success:
            logger.info("Successfully added vector field to Solr schema")
        else:
            logger.warning("Failed to add vector field with automatic detection, trying legacy approach...")
            
            # Try legacy approach as fallback
            success = self.schema_updater.add_vector_field_legacy("vector", vector_dim)
            if success:
                logger.info("Successfully added legacy vector field to Solr schema")
                logger.warning("Note: Using text field for vector storage. KNN search may not be available.")
            else:
                raise Exception("Failed to add vector field to schema with all available methods")
        
        # Verify the field was added
        fields = self.schema_updater.list_fields()
        if fields and "vector" in fields:
            logger.info("Vector field verified in schema")
        else:
            raise Exception("Vector field not found in schema after addition")
    
    def _generate_embeddings(self) -> List[Dict]:
        """Generate vector embeddings for components."""
        logger.info("\nStep 2: Generating Vector Embeddings")
        logger.info("-" * 40)
        
        # Get all components from Solr
        components = self.solr_manager.get_all_components()
        logger.info(f"Retrieved {len(components)} components from Solr")
        
        # Generate embeddings
        components_with_vectors = self.vector_generator.generate_embeddings(components)
        logger.info(f"Generated embeddings for {len(components_with_vectors)} components")
        
        # Save embeddings to file for future use
        embeddings_file = "data/components_with_vectors.json"
        self.vector_generator.save_embeddings(components_with_vectors, embeddings_file)
        logger.info(f"Saved embeddings to {embeddings_file}")
        
        return components_with_vectors
    
    def _add_vectors_to_solr(self, components_with_vectors: List[Dict]):
        """Add vector embeddings to Solr documents."""
        logger.info("\nStep 3: Adding Vectors to Solr Documents")
        logger.info("-" * 40)
        
        success = self.solr_manager.add_vectors_to_documents(components_with_vectors)
        if success:
            logger.info("Successfully added vectors to Solr documents")
        else:
            raise Exception("Failed to add vectors to Solr documents")
    
    def _demonstrate_search_capabilities(self):
        """Demonstrate different types of search capabilities."""
        logger.info("\nStep 4: Demonstrating Search Capabilities")
        logger.info("-" * 40)
        
        # 1. Traditional text search
        self._demo_text_search()
        
        # 2. Semantic search
        self._demo_semantic_search()
        
        # 3. Hybrid search
        self._demo_hybrid_search()
        
        # 4. Filtered search
        self._demo_filtered_search()
    
    def _demo_text_search(self):
        """Demonstrate traditional text search."""
        logger.info("\n--- Traditional Text Search ---")
        
        # Search for components related to "localization"
        query = "localization"
        results = self.solr_manager.search_components(query)
        
        logger.info(f"Text search for '{query}' returned {len(results)} results:")
        for i, result in enumerate(results[:3]):  # Show top 3
            logger.info(f"  {i+1}. {result['name']} ({result['class']})")
    
    def _demo_semantic_search(self):
        """Demonstrate semantic search using vectors."""
        logger.info("\n--- Semantic Search ---")
        
        # Create a query vector for "robot navigation and mapping"
        query_text = "robot navigation and mapping"
        query_vector = self.vector_generator.model.encode([query_text], convert_to_numpy=True)[0].tolist()
        
        # Perform semantic search
        results = self.solr_manager.semantic_search(query_vector, k=5)
        
        logger.info(f"Semantic search for '{query_text}' returned {len(results)} results:")
        for i, result in enumerate(results[:3]):  # Show top 3
            score = result.get('score', 0.0)
            logger.info(f"  {i+1}. {result['name']} ({result['class']}) - Score: {score:.4f}")
    
    def _demo_hybrid_search(self):
        """Demonstrate hybrid search combining text and semantic."""
        logger.info("\n--- Hybrid Search ---")
        
        # Text query
        text_query = "sensor driver"
        
        # Semantic query
        semantic_text = "hardware interface for data acquisition"
        query_vector = self.vector_generator.model.encode([semantic_text], convert_to_numpy=True)[0].tolist()
        
        # Perform hybrid search
        results = self.solr_manager.hybrid_search(
            text_query=text_query,
            query_vector=query_vector,
            k=5,
            semantic_weight=0.6
        )
        
        logger.info(f"Hybrid search returned {len(results)} results:")
        for i, result in enumerate(results[:3]):  # Show top 3
            hybrid_score = result.get('hybrid_score', 0.0)
            logger.info(f"  {i+1}. {result['name']} ({result['class']}) - Hybrid Score: {hybrid_score:.4f}")
    
    def _demo_filtered_search(self):
        """Demonstrate filtered search with metadata constraints."""
        logger.info("\n--- Filtered Search ---")
        
        # Define filters
        filters = {
            'ros_version': 'ROS 2',
            'type': 'SensorDriverComponent'
        }
        
        # Text query
        text_query = "laser"
        
        # Semantic query
        semantic_text = "distance measurement and scanning"
        query_vector = self.vector_generator.model.encode([semantic_text], convert_to_numpy=True)[0].tolist()
        
        # Perform filtered hybrid search
        results = self.solr_manager.hybrid_search(
            text_query=text_query,
            query_vector=query_vector,
            k=5,
            filters=filters,
            semantic_weight=0.5
        )
        
        logger.info(f"Filtered search (ROS 2 + SensorDriverComponent) returned {len(results)} results:")
        for i, result in enumerate(results[:3]):  # Show top 3
            hybrid_score = result.get('hybrid_score', 0.0)
            logger.info(f"  {i+1}. {result['name']} ({result['class']}) - Hybrid Score: {hybrid_score:.4f}")
    
    def run_performance_test(self):
        """Run performance tests for different search types."""
        logger.info("\n" + "=" * 60)
        logger.info("Performance Testing")
        logger.info("=" * 60)
        
        import time
        
        # Test text search performance
        start_time = time.time()
        for _ in range(10):
            self.solr_manager.search_components("sensor")
        text_search_time = time.time() - start_time
        logger.info(f"Text search (10 queries): {text_search_time:.4f} seconds")
        
        # Test semantic search performance
        query_vector = self.vector_generator.model.encode(["robot navigation"], convert_to_numpy=True)[0].tolist()
        start_time = time.time()
        for _ in range(10):
            self.solr_manager.semantic_search(query_vector, k=5)
        semantic_search_time = time.time() - start_time
        logger.info(f"Semantic search (10 queries): {semantic_search_time:.4f} seconds")
        
        # Test hybrid search performance
        start_time = time.time()
        for _ in range(10):
            self.solr_manager.hybrid_search("sensor", query_vector, k=5)
        hybrid_search_time = time.time() - start_time
        logger.info(f"Hybrid search (10 queries): {hybrid_search_time:.4f} seconds")


def main():
    """Main function to run the demonstration."""
    try:
        demo = VectorIntegrationDemo()
        
        # Run the complete demo
        demo.run_complete_demo()
        
        # Run performance tests
        demo.run_performance_test()
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 