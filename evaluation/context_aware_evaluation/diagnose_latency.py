"""
Diagnose latency components to understand where time is spent
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import time
import numpy as np
from backend.solr_manager import SolrManager
from backend.vector_generator import VectorGenerator

def measure_component_latency(num_iterations=10):
    """Measure latency of each component separately"""
    
    print("=" * 80)
    print("LATENCY COMPONENT DIAGNOSIS")
    print("=" * 80)
    print()
    
    # Initialize
    ttl_file = os.path.join(os.path.dirname(__file__), "..", "..", "data", "ros_knowledge_graph.ttl")
    solr_manager = SolrManager(ttl_file)
    vector_gen = VectorGenerator()
    
    test_query = "I'm using nav2 for navigation. What localization packages are compatible?"
    
    print(f"Test query: {test_query}")
    print(f"Iterations: {num_iterations}")
    print()
    
    # Warmup
    print("Running warmup...")
    for _ in range(3):
        _ = solr_manager.search_components(test_query, max_results=30)
        query_vector = vector_gen.embed(test_query)
        _ = solr_manager.semantic_search(query_vector, k=30)
    print("✓ Warmup complete\n")
    
    print("=" * 80)
    print("KEYWORD SEARCH BREAKDOWN")
    print("=" * 80)
    
    # 1. Keyword preprocessing only
    preprocessing_times = []
    for _ in range(num_iterations):
        start = time.time()
        # Simulate the preprocessing done in search_components
        tokens = test_query.lower().split()
        stopwords = {'i', 'me', 'my', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        meaningful_tokens = [t for t in tokens if t not in stopwords and len(t) > 2]
        token_query = ' OR '.join(meaningful_tokens)
        query = f"content:({token_query}) OR description:({token_query}) OR name:({token_query})"
        preprocessing_times.append((time.time() - start) * 1000)
    
    print(f"Preprocessing (tokenization + query building):")
    print(f"  Mean: {np.mean(preprocessing_times):.4f} ms")
    print(f"  Std:  {np.std(preprocessing_times):.4f} ms")
    print()
    
    # 2. Full keyword search (preprocessing + Solr)
    keyword_times = []
    for _ in range(num_iterations):
        start = time.time()
        _ = solr_manager.search_components(test_query, max_results=30)
        keyword_times.append((time.time() - start) * 1000)
    
    print(f"Full keyword search (preprocessing + Solr BM25):")
    print(f"  Mean: {np.mean(keyword_times):.4f} ms")
    print(f"  Std:  {np.std(keyword_times):.4f} ms")
    print()
    
    solr_only_time = np.mean(keyword_times) - np.mean(preprocessing_times)
    print(f"→ Pure Solr BM25 time (estimated): {solr_only_time:.4f} ms")
    print()
    
    print("=" * 80)
    print("VECTOR SEARCH BREAKDOWN")
    print("=" * 80)
    
    # 3. BERT encoding only
    encoding_times = []
    for _ in range(num_iterations):
        start = time.time()
        _ = vector_gen.embed(test_query)
        encoding_times.append((time.time() - start) * 1000)
    
    print(f"BERT encoding (query → 384-dim vector):")
    print(f"  Mean: {np.mean(encoding_times):.4f} ms")
    print(f"  Std:  {np.std(encoding_times):.4f} ms")
    print()
    
    # 4. Solr KNN search only (pre-encoded vector)
    query_vector = vector_gen.embed(test_query)
    knn_times = []
    for _ in range(num_iterations):
        start = time.time()
        _ = solr_manager.semantic_search(query_vector, k=30)
        knn_times.append((time.time() - start) * 1000)
    
    print(f"Solr KNN search (vector → results):")
    print(f"  Mean: {np.mean(knn_times):.4f} ms")
    print(f"  Std:  {np.std(knn_times):.4f} ms")
    print()
    
    # 5. Full vector search (encoding + KNN)
    vector_times = []
    for _ in range(num_iterations):
        start = time.time()
        query_vector = vector_gen.embed(test_query)
        _ = solr_manager.semantic_search(query_vector, k=30)
        vector_times.append((time.time() - start) * 1000)
    
    print(f"Full vector search (BERT + KNN):")
    print(f"  Mean: {np.mean(vector_times):.4f} ms")
    print(f"  Std:  {np.std(vector_times):.4f} ms")
    print()
    
    print("=" * 80)
    print("HYBRID SEARCH BREAKDOWN")
    print("=" * 80)
    
    # 6. Hybrid search (both paths + merging)
    hybrid_times = []
    for _ in range(num_iterations):
        start = time.time()
        query_vector = vector_gen.embed(test_query)
        _ = solr_manager.hybrid_search(test_query, query_vector, k=30, semantic_weight=0.7)
        hybrid_times.append((time.time() - start) * 1000)
    
    print(f"Full hybrid search (α=0.7):")
    print(f"  Mean: {np.mean(hybrid_times):.4f} ms")
    print(f"  Std:  {np.std(hybrid_times):.4f} ms")
    print()
    
    print("=" * 80)
    print("SUMMARY COMPARISON")
    print("=" * 80)
    print()
    print(f"{'Component':<40} {'Mean (ms)':<12} {'Std (ms)':<12}")
    print("-" * 64)
    print(f"{'Keyword preprocessing':<40} {np.mean(preprocessing_times):>10.4f}   {np.std(preprocessing_times):>10.4f}")
    print(f"{'Pure Solr BM25 (estimated)':<40} {solr_only_time:>10.4f}   {'N/A':>10}")
    print(f"{'Full keyword search':<40} {np.mean(keyword_times):>10.4f}   {np.std(keyword_times):>10.4f}")
    print()
    print(f"{'BERT query encoding':<40} {np.mean(encoding_times):>10.4f}   {np.std(encoding_times):>10.4f}")
    print(f"{'Solr KNN search':<40} {np.mean(knn_times):>10.4f}   {np.std(knn_times):>10.4f}")
    print(f"{'Full vector search':<40} {np.mean(vector_times):>10.4f}   {np.std(vector_times):>10.4f}")
    print()
    print(f"{'Full hybrid search (α=0.7)':<40} {np.mean(hybrid_times):>10.4f}   {np.std(hybrid_times):>10.4f}")
    print("-" * 64)
    print()
    
    print("KEY INSIGHTS:")
    print("-" * 80)
    print(f"• Pure BM25 inverted index:        ~{solr_only_time:.2f} ms (without preprocessing)")
    print(f"• Vector encoding (BERT):          ~{np.mean(encoding_times):.2f} ms")
    print(f"• KNN search (90 components):      ~{np.mean(knn_times):.2f} ms")
    print(f"• Keyword total:                   ~{np.mean(keyword_times):.2f} ms (with preprocessing)")
    print(f"• Vector total:                    ~{np.mean(vector_times):.2f} ms (encoding + KNN)")
    print(f"• Hybrid total:                    ~{np.mean(hybrid_times):.2f} ms (both + merging)")
    print()
    print("CONCLUSION:")
    print("-" * 80)
    if solr_only_time < np.mean(knn_times):
        print(f"✓ Pure BM25 ({solr_only_time:.2f}ms) IS faster than KNN ({np.mean(knn_times):.2f}ms)")
        print(f"  as expected for inverted index vs. vector similarity")
    else:
        print(f"⚠ Unexpected: BM25 ({solr_only_time:.2f}ms) slower than KNN ({np.mean(knn_times):.2f}ms)")
    print()
    print(f"The reason keyword search appears slower in evaluation is:")
    print(f"  1. Query preprocessing overhead: {np.mean(preprocessing_times):.2f}ms")
    print(f"  2. Network/serialization overhead")
    print(f"  3. Result processing overhead")
    print()

if __name__ == "__main__":
    measure_component_latency(num_iterations=20)
