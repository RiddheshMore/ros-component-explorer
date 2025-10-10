#!/usr/bin/env python3
"""
Vector Access Utility for ROS Component Explorer.

This utility provides various ways to access, examine, and work with 
the dense vector embeddings stored in Apache Solr.
"""

import json
import logging
from typing import List, Dict, Optional, Tuple
import numpy as np
from pysolr import Solr
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SOLR_URL = "http://localhost:8984/solr/ros_explorer"

class VectorAccessUtility:
    """Utility class for accessing vectors stored in Apache Solr."""
    
    def __init__(self, solr_url: str = SOLR_URL):
        self.solr_url = solr_url
        self.solr = Solr(solr_url, timeout=10)
        
    def get_component_vector(self, component_id: str) -> Optional[List[float]]:
        """
        Get the vector for a specific component.
        
        Args:
            component_id: ID/URI of the component
            
        Returns:
            Vector as list of floats, or None if not found
        """
        try:
            # Query for specific component
            results = self.solr.search(
                f'id:"{component_id}"',
                fl="id,name,vector",
                rows=1
            )
            
            if results.docs:
                doc = results.docs[0]
                vector = doc.get('vector')
                if vector:
                    # Handle different vector storage formats
                    if isinstance(vector, str):
                        # Vector stored as string, parse it
                        try:
                            return json.loads(vector)
                        except json.JSONDecodeError:
                            # Try parsing as space-separated values
                            return [float(x) for x in vector.split()]
                    elif isinstance(vector, list):
                        return vector
                    else:
                        logger.warning(f"Unknown vector format: {type(vector)}")
                        return None
                else:
                    logger.warning(f"No vector found for component {component_id}")
                    return None
            else:
                logger.warning(f"Component {component_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Error getting vector for {component_id}: {e}")
            return None
    
    def get_all_vectors(self, max_components: int = 100) -> Dict[str, List[float]]:
        """
        Get vectors for all components.
        
        Args:
            max_components: Maximum number of components to retrieve
            
        Returns:
            Dictionary mapping component IDs to their vectors
        """
        try:
            # Query for all components with vectors
            results = self.solr.search(
                "vector:*",  # Only get components that have vectors
                fl="id,name,vector",
                rows=max_components
            )
            
            vectors = {}
            for doc in results.docs:
                component_id = doc.get('id')
                vector = doc.get('vector')
                
                if component_id and vector:
                    # Parse vector based on format
                    if isinstance(vector, str):
                        try:
                            parsed_vector = json.loads(vector)
                        except json.JSONDecodeError:
                            parsed_vector = [float(x) for x in vector.split()]
                    elif isinstance(vector, list):
                        parsed_vector = vector
                    else:
                        continue
                        
                    vectors[component_id] = parsed_vector
            
            logger.info(f"Retrieved vectors for {len(vectors)} components")
            return vectors
            
        except Exception as e:
            logger.error(f"Error getting all vectors: {e}")
            return {}
    
    def examine_vector_stats(self) -> Dict[str, any]:
        """
        Get statistics about the vectors stored in Solr.
        
        Returns:
            Dictionary with vector statistics
        """
        try:
            # Get sample of vectors
            sample_vectors = self.get_all_vectors(max_components=50)
            
            if not sample_vectors:
                return {"error": "No vectors found"}
            
            # Calculate statistics
            all_vectors = list(sample_vectors.values())
            vector_arrays = [np.array(v) for v in all_vectors if v]
            
            if not vector_arrays:
                return {"error": "No valid vectors found"}
            
            # Get dimensions
            dimensions = [len(v) for v in all_vectors]
            
            # Calculate stats
            stats = {
                "total_components_with_vectors": len(sample_vectors),
                "vector_dimensions": {
                    "min": min(dimensions),
                    "max": max(dimensions),
                    "most_common": max(set(dimensions), key=dimensions.count)
                },
                "vector_value_stats": {},
                "sample_component_ids": list(sample_vectors.keys())[:10]
            }
            
            # Stats for first vector as example
            if vector_arrays:
                first_vector = vector_arrays[0]
                stats["vector_value_stats"] = {
                    "min_value": float(np.min(first_vector)),
                    "max_value": float(np.max(first_vector)),
                    "mean_value": float(np.mean(first_vector)),
                    "std_dev": float(np.std(first_vector))
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting vector stats: {e}")
            return {"error": str(e)}
    
    def search_by_vector_similarity(self, query_vector: List[float], k: int = 10) -> List[Dict]:
        """
        Search for components similar to a given vector.
        
        Args:
            query_vector: Vector to search for similar components
            k: Number of results to return
            
        Returns:
            List of similar components with similarity scores
        """
        try:
            # Use Solr's vector search capability
            # Format depends on Solr version and vector field configuration
            vector_str = ",".join([str(v) for v in query_vector])
            
            # Try different query formats
            query_formats = [
                f"{{!knn f=vector topK={k}}}{vector_str}",  # Solr 9.x format
                f"{{!func}}vectorSimilarity(vector,\"[{vector_str}]\")",  # Alternative format
            ]
            
            for query_format in query_formats:
                try:
                    results = self.solr.search(
                        query_format,
                        fl="id,name,description,score",
                        rows=k
                    )
                    
                    if results.docs:
                        components = []
                        for doc in results.docs:
                            components.append({
                                'id': doc.get('id', ''),
                                'name': doc.get('name', ''),
                                'description': doc.get('description', ''),
                                'score': doc.get('score', 0.0)
                            })
                        
                        logger.info(f"Found {len(components)} similar components")
                        return components
                        
                except Exception as e:
                    logger.warning(f"Query format failed: {query_format}, error: {e}")
                    continue
            
            logger.warning("All vector search query formats failed")
            return []
            
        except Exception as e:
            logger.error(f"Error in vector similarity search: {e}")
            return []
    
    def export_vectors_to_file(self, filename: str, format: str = "json"):
        """
        Export all vectors to a file.
        
        Args:
            filename: Output filename
            format: Export format ("json", "csv", "npy")
        """
        try:
            vectors = self.get_all_vectors(max_components=1000)
            
            if format == "json":
                with open(filename, 'w') as f:
                    json.dump(vectors, f, indent=2)
                    
            elif format == "csv":
                import csv
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['component_id'] + [f'dim_{i}' for i in range(384)])  # Assuming 384 dims
                    
                    for comp_id, vector in vectors.items():
                        writer.writerow([comp_id] + vector)
                        
            elif format == "npy":
                # Export as numpy array
                component_ids = list(vectors.keys())
                vector_matrix = np.array(list(vectors.values()))
                
                np.save(filename.replace('.npy', '_vectors.npy'), vector_matrix)
                np.save(filename.replace('.npy', '_ids.npy'), component_ids)
            
            logger.info(f"Exported {len(vectors)} vectors to {filename}")
            
        except Exception as e:
            logger.error(f"Error exporting vectors: {e}")
    
    def compare_component_vectors(self, component_id1: str, component_id2: str) -> Dict[str, float]:
        """
        Compare vectors of two components.
        
        Args:
            component_id1: First component ID
            component_id2: Second component ID
            
        Returns:
            Dictionary with similarity metrics
        """
        try:
            vector1 = self.get_component_vector(component_id1)
            vector2 = self.get_component_vector(component_id2)
            
            if not vector1 or not vector2:
                return {"error": "One or both vectors not found"}
            
            # Convert to numpy arrays
            v1 = np.array(vector1)
            v2 = np.array(vector2)
            
            # Calculate similarity metrics
            cosine_sim = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            euclidean_dist = np.linalg.norm(v1 - v2)
            dot_product = np.dot(v1, v2)
            
            return {
                "cosine_similarity": float(cosine_sim),
                "euclidean_distance": float(euclidean_dist),
                "dot_product": float(dot_product),
                "vector1_norm": float(np.linalg.norm(v1)),
                "vector2_norm": float(np.linalg.norm(v2))
            }
            
        except Exception as e:
            logger.error(f"Error comparing vectors: {e}")
            return {"error": str(e)}

def main():
    """Demonstrate vector access functionality."""
    print("🔍 ROS Component Explorer - Vector Access Utility")
    print("=" * 50)
    
    try:
        # Initialize utility
        vector_util = VectorAccessUtility()
        
        # Get vector statistics
        print("\n📊 Vector Statistics:")
        stats = vector_util.examine_vector_stats()
        for key, value in stats.items():
            print(f"  • {key}: {value}")
        
        # Get sample component with vector
        print("\n🎯 Sample Component Vector:")
        sample_vectors = vector_util.get_all_vectors(max_components=5)
        
        if sample_vectors:
            sample_id = list(sample_vectors.keys())[0]
            sample_vector = sample_vectors[sample_id]
            
            print(f"  Component ID: {sample_id}")
            print(f"  Vector dimension: {len(sample_vector)}")
            print(f"  First 10 values: {sample_vector[:10]}")
            print(f"  Vector norm: {np.linalg.norm(sample_vector):.6f}")
        
        # Export sample vectors
        print("\n💾 Exporting sample vectors...")
        vector_util.export_vectors_to_file("sample_vectors.json", "json")
        print("  ✅ Exported to sample_vectors.json")
        
        print("\n✅ Vector access utility demonstration complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
