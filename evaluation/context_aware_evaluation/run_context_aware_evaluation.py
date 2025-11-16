"""
Context-Aware Evaluation for ROS Component Explorer
Evaluates search performance with developer-centric queries that include existing packages and context
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import time
from datetime import datetime
from typing import List, Dict, Tuple
import numpy as np

from backend.solr_manager import SolrManager
from backend.vector_generator import VectorGenerator

def calculate_precision_recall_f1(retrieved: List[str], relevant: List[str], k: int = 10) -> Tuple[float, float, float]:
    """Calculate Precision@k, Recall@k, and F1@k"""
    retrieved_k = retrieved[:k]
    
    # Normalize package names for comparison (lowercase, replace spaces with underscores)
    retrieved_normalized = {normalize_package_name(p) for p in retrieved_k}
    relevant_normalized = {normalize_package_name(p) for p in relevant}
    
    if not relevant_normalized:
        return 0.0, 0.0, 0.0
    
    true_positives = len(retrieved_normalized & relevant_normalized)
    precision = true_positives / len(retrieved_k) if len(retrieved_k) > 0 else 0.0
    recall = true_positives / len(relevant_normalized)
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return precision, recall, f1

def normalize_package_name(name: str) -> str:
    """Normalize package name for comparison"""
    # Convert to lowercase and replace spaces with underscores
    return name.lower().replace(' ', '_').replace('-', '_')

def calculate_ndcg(retrieved: List[str], relevant: List[str], k: int = 10) -> float:
    """Calculate Normalized Discounted Cumulative Gain@k"""
    retrieved_k = retrieved[:k]
    
    # Normalize package names for comparison
    relevant_normalized = {normalize_package_name(p) for p in relevant}
    
    # Calculate DCG
    dcg = 0.0
    for i, pkg in enumerate(retrieved_k):
        if normalize_package_name(pkg) in relevant_normalized:
            dcg += 1.0 / np.log2(i + 2)  # i+2 because we start from 1
    
    # Calculate IDCG
    idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(relevant), k)))
    
    return dcg / idcg if idcg > 0 else 0.0

def calculate_map(retrieved: List[str], relevant: List[str], k: int = 10) -> float:
    """Calculate Mean Average Precision@k"""
    retrieved_k = retrieved[:k]
    
    # Normalize package names for comparison
    relevant_normalized = {normalize_package_name(p) for p in relevant}
    
    if not relevant_normalized:
        return 0.0
    
    precisions = []
    num_relevant = 0
    
    for i, pkg in enumerate(retrieved_k):
        if normalize_package_name(pkg) in relevant_normalized:
            num_relevant += 1
            precision_at_i = num_relevant / (i + 1)
            precisions.append(precision_at_i)
    
    return sum(precisions) / len(relevant_normalized) if precisions else 0.0

def calculate_mrr(retrieved: List[str], relevant: List[str]) -> float:
    """Calculate Mean Reciprocal Rank"""
    # Normalize package names for comparison
    relevant_normalized = {normalize_package_name(p) for p in relevant}
    
    for i, pkg in enumerate(retrieved):
        if normalize_package_name(pkg) in relevant_normalized:
            return 1.0 / (i + 1)
    return 0.0

def calculate_success_at_k(retrieved: List[str], relevant: List[str], k: int = 10) -> bool:
    """Calculate whether at least one relevant package is in top-k"""
    retrieved_k = retrieved[:k]
    
    # Normalize package names for comparison
    retrieved_normalized = {normalize_package_name(p) for p in retrieved_k}
    relevant_normalized = {normalize_package_name(p) for p in relevant}
    
    return len(retrieved_normalized & relevant_normalized) > 0

def evaluate_search_method(solr_manager: SolrManager, vector_gen: VectorGenerator, 
                          queries: List[Dict], search_method: str, alpha: float = 0.7) -> Dict:
    """
    Evaluate a search method on context-aware queries
    
    Args:
        solr_manager: SolrManager instance
        vector_gen: VectorGenerator instance
        queries: List of query dictionaries with context
        search_method: 'keyword', 'vector', or 'hybrid'
        alpha: Alpha value for hybrid search (only used if search_method='hybrid')
    
    Returns:
        Dictionary with evaluation metrics
    """
    print(f"\nEvaluating {search_method.upper()} search...")
    
    # WARMUP: Run 2 warmup queries to load models and caches
    # This ensures we measure actual search performance, not model loading time
    print(f"  Running warmup queries (not included in metrics)...")
    warmup_query = "robot navigation slam"
    for _ in range(2):
        if search_method == "keyword":
            _ = solr_manager.search_components(warmup_query, max_results=30)
        elif search_method == "vector":
            query_vector = vector_gen.embed(warmup_query)
            _ = solr_manager.semantic_search(query_vector, k=30)
        elif search_method == "hybrid":
            query_vector = vector_gen.embed(warmup_query)
            _ = solr_manager.hybrid_search(warmup_query, query_vector, k=30, semantic_weight=alpha)
    print(f"  ✓ Warmup complete\n")
    
    results = {
        "method": search_method,
        "alpha": alpha if search_method == "hybrid" else None,
        "per_query_metrics": [],
        "aggregate_metrics": {}
    }
    
    # Metrics storage
    precisions, recalls, f1_scores = [], [], []
    ndcg_scores, map_scores, mrr_scores = [], [], []
    success_count = 0
    latencies = []
    
    for query_data in queries:
        query_id = query_data["id"]
        query_text = query_data["query"]
        context = query_data.get("context", {})
        relevant_packages = query_data["relevant_packages"]
        
        print(f"  Query {query_id}: {query_text[:60]}...")
        
        # Measure search latency
        start_time = time.time()
        
        if search_method == "keyword":
            search_results = solr_manager.search_components(query_text, max_results=30)
        elif search_method == "vector":
            query_vector = vector_gen.embed(query_text)
            search_results = solr_manager.semantic_search(query_vector, k=30)
        elif search_method == "hybrid":
            query_vector = vector_gen.embed(query_text)
            search_results = solr_manager.hybrid_search(query_text, query_vector, k=30, semantic_weight=alpha)
        else:
            raise ValueError(f"Unknown search method: {search_method}")
        
        latency = (time.time() - start_time) * 1000  # Convert to milliseconds
        latencies.append(latency)
        
        # Extract package names from results
        # Handle both string and list fields
        retrieved_packages = []
        for doc in search_results:
            # Get package name - handle list or string format
            pkg_name = doc.get('package_name', doc.get('name', doc.get('package', '')))
            if isinstance(pkg_name, list):
                pkg_name = pkg_name[0] if pkg_name else ''
            retrieved_packages.append(pkg_name)
        
        # Calculate metrics
        precision, recall, f1 = calculate_precision_recall_f1(retrieved_packages, relevant_packages, k=10)
        ndcg = calculate_ndcg(retrieved_packages, relevant_packages, k=10)
        map_score = calculate_map(retrieved_packages, relevant_packages, k=10)
        mrr = calculate_mrr(retrieved_packages, relevant_packages)
        success = calculate_success_at_k(retrieved_packages, relevant_packages, k=10)
        
        # Store metrics
        precisions.append(precision)
        recalls.append(recall)
        f1_scores.append(f1)
        ndcg_scores.append(ndcg)
        map_scores.append(map_score)
        mrr_scores.append(mrr)
        if success:
            success_count += 1
        
        # Store per-query results
        results["per_query_metrics"].append({
            "query_id": query_id,
            "query": query_text,
            "context": context,
            "relevant_count": len(relevant_packages),
            "retrieved_count": len(retrieved_packages),
            "precision@10": round(precision, 4),
            "recall@10": round(recall, 4),
            "f1@10": round(f1, 4),
            "ndcg@10": round(ndcg, 4),
            "map@10": round(map_score, 4),
            "mrr": round(mrr, 4),
            "success@10": success,
            "latency_ms": round(latency, 2),
            "top_5_results": retrieved_packages[:5]
        })
    
    # Calculate aggregate metrics
    results["aggregate_metrics"] = {
        "precision@10": {
            "mean": round(np.mean(precisions), 4),
            "std": round(np.std(precisions), 4)
        },
        "recall@10": {
            "mean": round(np.mean(recalls), 4),
            "std": round(np.std(recalls), 4)
        },
        "f1@10": {
            "mean": round(np.mean(f1_scores), 4),
            "std": round(np.std(f1_scores), 4)
        },
        "ndcg@10": {
            "mean": round(np.mean(ndcg_scores), 4),
            "std": round(np.std(ndcg_scores), 4)
        },
        "map@10": {
            "mean": round(np.mean(map_scores), 4),
            "std": round(np.std(map_scores), 4)
        },
        "mrr": {
            "mean": round(np.mean(mrr_scores), 4),
            "std": round(np.std(mrr_scores), 4)
        },
        "success@10": {
            "rate": round((success_count / len(queries)) * 100, 2),
            "count": f"{success_count}/{len(queries)}"
        },
        "latency_ms": {
            "mean": round(np.mean(latencies), 2),
            "std": round(np.std(latencies), 2),
            "min": round(np.min(latencies), 2),
            "max": round(np.max(latencies), 2)
        }
    }
    
    print(f"\n  ✓ {search_method.upper()} Results:")
    print(f"    F1@10: {results['aggregate_metrics']['f1@10']['mean']:.4f}")
    print(f"    NDCG@10: {results['aggregate_metrics']['ndcg@10']['mean']:.4f}")
    print(f"    MAP@10: {results['aggregate_metrics']['map@10']['mean']:.4f}")
    print(f"    Success@10: {results['aggregate_metrics']['success@10']['rate']}%")
    print(f"    Latency: {results['aggregate_metrics']['latency_ms']['mean']:.2f}ms")
    
    return results

def main():
    print("=" * 80)
    print("CONTEXT-AWARE EVALUATION FOR ROS COMPONENT EXPLORER")
    print("=" * 80)
    print()
    print("This evaluation tests search performance with developer-centric queries")
    print("that include existing packages, hardware constraints, and integration context.")
    print()
    
    # Load context-aware queries
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(script_dir, "context_aware_queries_dataset.json")
    
    with open(dataset_path, 'r') as f:
        dataset = json.load(f)
    
    queries = dataset["queries"]
    print(f"✓ Loaded {len(queries)} context-aware queries")
    print(f"  - Integration/Compatibility: {dataset['metadata']['query_types']['integration_compatibility']}")
    print(f"  - Dependency-Based: {dataset['metadata']['query_types']['dependency_based']}")
    print(f"  - Hardware-Constrained: {dataset['metadata']['query_types']['hardware_constrained']}")
    print(f"  - Feature Addition: {dataset['metadata']['query_types']['feature_addition']}")
    print(f"  - Replacement/Alternative: {dataset['metadata']['query_types']['replacement_alternative']}")
    print()
    
    # Initialize Solr manager
    ttl_file = os.path.join(os.path.dirname(script_dir), "data", "ros_knowledge_graph.ttl")
    solr_manager = SolrManager(ttl_file)
    vector_gen = VectorGenerator()
    print("✓ Connected to Solr")
    print("✓ Initialized Vector Generator")
    print()
    
    # Run evaluations for all search methods
    all_results = {
        "metadata": {
            "evaluation_type": "context_aware",
            "dataset": "context_aware_queries_dataset.json",
            "num_queries": len(queries),
            "evaluation_date": datetime.now().isoformat(),
            "query_types": dataset["metadata"]["query_types"]
        },
        "methods": []
    }
    
    # 1. Keyword Search (BM25)
    keyword_results = evaluate_search_method(solr_manager, vector_gen, queries, "keyword")
    all_results["methods"].append(keyword_results)
    
    # 2. Vector Semantic Search
    vector_results = evaluate_search_method(solr_manager, vector_gen, queries, "vector")
    all_results["methods"].append(vector_results)
    
    # 3. Hybrid Search (α=0.5)
    hybrid_05_results = evaluate_search_method(solr_manager, vector_gen, queries, "hybrid", alpha=0.5)
    all_results["methods"].append(hybrid_05_results)
    
    # 4. Hybrid Search (α=0.7)
    hybrid_07_results = evaluate_search_method(solr_manager, vector_gen, queries, "hybrid", alpha=0.7)
    all_results["methods"].append(hybrid_07_results)
    
    # 5. Hybrid Search (α=1.0 - Pure Vector)
    hybrid_10_results = evaluate_search_method(solr_manager, vector_gen, queries, "hybrid", alpha=1.0)
    all_results["methods"].append(hybrid_10_results)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(script_dir, f"context_aware_eval_results_{timestamp}.json")
    
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print()
    print("=" * 80)
    print("EVALUATION COMPLETE")
    print("=" * 80)
    print()
    print(f"Results saved to: {output_file}")
    print()
    
    # Print summary comparison
    print("SUMMARY COMPARISON:")
    print("-" * 80)
    print(f"{'Method':<25} {'F1@10':<10} {'NDCG@10':<10} {'MAP@10':<10} {'Success':<12} {'Latency':<10}")
    print("-" * 80)
    
    for method_result in all_results["methods"]:
        method_name = method_result["method"]
        if method_result["alpha"] is not None:
            method_name += f" (α={method_result['alpha']})"
        
        f1 = method_result["aggregate_metrics"]["f1@10"]["mean"]
        ndcg = method_result["aggregate_metrics"]["ndcg@10"]["mean"]
        map_score = method_result["aggregate_metrics"]["map@10"]["mean"]
        success = method_result["aggregate_metrics"]["success@10"]["rate"]
        latency = method_result["aggregate_metrics"]["latency_ms"]["mean"]
        
        print(f"{method_name:<25} {f1:<10.4f} {ndcg:<10.4f} {map_score:<10.4f} {success:<11.2f}% {latency:<9.2f}ms")
    
    print("-" * 80)
    print()

if __name__ == "__main__":
    main()
