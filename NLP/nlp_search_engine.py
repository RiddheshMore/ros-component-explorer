"""
Rule-Based Natural Language Search Engine for ROS Component Explorer.

This module provides structured search capabilities by combining:
1. Rule-based natural language query processing using pattern matching
2. Structured search execution against Solr database
3. Template-based result synthesis and ranking
4. Context-aware recommendations using predefined rules

This system combines rule-based pattern matching with semantic search capabilities
to understand user queries and provide relevant component recommendations.
"""

import json
import logging
from typing import Dict, List, Optional, Tuple, Any
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from NLP.query_processor import NLQueryProcessor, QueryToSearchTranslator, QueryRequirements
from backend.solr_manager import SolrManager
from backend.vector_generator import VectorGenerator
from backend.vector_search_manager import VectorSearchManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NLPSearchEngine:
    """
    Rule-based natural language search engine for ROS components.
    
    Uses structured pattern matching and template-based response generation
    to understand user queries and provide relevant ROS component recommendations.
    """
    
    def __init__(self, ttl_file: str, use_semantic_search: bool = True):
        """
        Initialize the rule-based natural language search engine.
        
        Args:
            ttl_file: Path to the TTL knowledge base file
            use_semantic_search: Whether to enable semantic vector search alongside text search
        """
        self.ttl_file = ttl_file
        self.use_semantic_search = use_semantic_search
        
        # Initialize rule-based processing components
        self.query_processor = NLQueryProcessor()  # Pattern matching processor
        self.translator = QueryToSearchTranslator()  # Rule-based query translator
        self.solr_manager = SolrManager(ttl_file)  # Database interface
        self.vector_generator = VectorGenerator()  # Semantic embedding generator
        self.vector_search_manager = VectorSearchManager(ttl_file)  # Enhanced vector search
        
        # Response synthesis templates (predefined structured templates)
        self.response_templates = {
            "recommendation": self._get_recommendation_template(),
            "comparison": self._get_comparison_template(),
            "explanation": self._get_explanation_template(),
            "list": self._get_list_template()
        }
    
    def process_natural_language_query(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Process a natural language query using rule-based pattern matching.
        
        NOTE: Despite the method name, this uses structured pattern matching,
        keyword extraction, and predefined response templates.
        
        Args:
            query: Natural language query string
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary containing search results and template-generated response
        """
        logger.info(f"Processing natural language query: {query}")
        
        try:
            # Step 1: Parse the natural language query
            requirements = self.query_processor.parse_query(query)
            
            # Step 2: Translate to search parameters
            search_params = self.translator.translate_to_search_params(requirements)
            
            # Step 3: Execute multi-modal search
            search_results = self._execute_enhanced_search(search_params, requirements, max_results)
            
            # Step 4: Rank and filter results
            ranked_results = self._rank_and_filter_results(search_results, requirements)
            
            # Step 5: Synthesize human-readable response
            synthesized_response = self._synthesize_response(query, requirements, ranked_results)
            
            return {
                "query": query,
                "requirements": requirements.__dict__,
                "search_params": search_params,
                "results": ranked_results[:max_results],
                "synthesized_response": synthesized_response,
                "metadata": {
                    "total_found": len(search_results),
                    "returned": min(len(ranked_results), max_results),
                    "search_type": self._determine_search_type(requirements)
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "query": query,
                "error": str(e),
                "synthesized_response": f"I encountered an error while processing your query: {str(e)}"
            }
    
    def _execute_enhanced_search(self, search_params: Dict[str, Any], 
                                requirements: QueryRequirements, 
                                max_results: int) -> List[Dict]:
        """Execute enhanced search using vector-based k-NN and hybrid search."""
        
        # Determine if we should use hybrid search or vector-only search
        should_use_hybrid = (
            search_params["text_query"] and 
            (requirements.keywords or requirements.primary_function)
        )
        
        if should_use_hybrid:
            # Use hybrid search combining text and vector similarity
            semantic_query = self._build_semantic_query(requirements)
            if semantic_query:
                try:
                    results = self.vector_search_manager.hybrid_search(
                        query=semantic_query,
                        k=max_results,
                        semantic_weight=0.7  # Favor semantic similarity
                    )
                    
                    for result in results:
                        result["search_type"] = "hybrid"
                        
                    logger.info(f"Hybrid search found {len(results)} results")
                    return results
                    
                except Exception as e:
                    logger.warning(f"Hybrid search failed: {e}")
        
        # Fallback to separate text and vector searches
        all_results = []
        
        # Text-based search
        if search_params["text_query"]:
            try:
                text_results = self.solr_manager.search_components(
                    search_params["text_query"]
                )
                
                for result in text_results:
                    result["search_type"] = "text"
                    result["relevance_score"] = result.get("score", 0.0)
                all_results.extend(text_results)
                logger.info(f"Text search found {len(text_results)} results")
            except Exception as e:
                logger.warning(f"Text search failed: {e}")
        
        # Vector-based semantic search
        semantic_query = self._build_semantic_query(requirements)
        if semantic_query:
            try:
                # Use enhanced vector search manager for k-NN similarity search
                semantic_results = self.vector_search_manager.vector_search(
                    query=semantic_query,
                    k=max_results
                )
                
                for result in semantic_results:
                    result["search_type"] = "vector_knn"
                    result["relevance_score"] = result.get("score", 0.0)
                
                all_results.extend(semantic_results)
                logger.info(f"Vector k-NN search found {len(semantic_results)} results")
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")
        
        return all_results
    
    def _build_semantic_query(self, requirements: QueryRequirements) -> str:
        """Build a semantic query string from requirements."""
        query_parts = []
        
        if requirements.primary_function:
            query_parts.append(requirements.primary_function)
        
        if requirements.categories:
            query_parts.extend([cat.value for cat in requirements.categories])
        
        if requirements.sensors:
            query_parts.extend([sensor.value.replace("_", " ") for sensor in requirements.sensors])
        
        if requirements.environment:
            query_parts.append(f"{requirements.environment.value} environment")
        
        if requirements.keywords:
            query_parts.extend(requirements.keywords[:3])  # Limit keywords
        
        return " ".join(query_parts)
    
    def _rank_and_filter_results(self, results: List[Dict], requirements: QueryRequirements) -> List[Dict]:
        """Rank and filter results based on requirements."""
        if not results:
            return []
        
        # Remove duplicates (same URI)
        seen_uris = set()
        unique_results = []
        for result in results:
            uri = result.get("uri", "")
            if uri not in seen_uris:
                seen_uris.add(uri)
                unique_results.append(result)
        
        # Score results based on requirements
        scored_results = []
        for result in unique_results:
            score = self._calculate_relevance_score(result, requirements)
            result["final_score"] = score
            scored_results.append(result)
        
        # Sort by final score
        scored_results.sort(key=lambda x: x.get("final_score", 0.0), reverse=True)
        
        return scored_results
    
    def _calculate_relevance_score(self, result: Dict, requirements: QueryRequirements) -> float:
        """Calculate relevance score for a result based on requirements."""
        base_score = result.get("relevance_score", 0.0)
        
        # Start with a base score
        boost = 1.0
        
        # Get result fields for matching
        result_type = result.get("class", result.get("type", ""))
        if isinstance(result_type, list):
            result_type = " ".join(str(t) for t in result_type)
        result_type = str(result_type).lower()
        
        result_desc = result.get("description", "")
        if isinstance(result_desc, list):
            result_desc = " ".join(str(d) for d in result_desc)
        result_desc = str(result_desc).lower()
        
        result_name = result.get("name", "")
        if isinstance(result_name, list):
            result_name = " ".join(str(n) for n in result_name)
        result_name = str(result_name).lower()
        
        combined_text = f"{result_desc} {result_name} {result_type}"
        
        # Strong category matching boost
        category_match_bonus = 0.0
        for category in requirements.categories:
            category_terms = {
                'perception': ['perception', 'vision', 'detection', 'recognition', 'tracking', 'object'],
                'localization': ['localization', 'pose', 'position', 'slam', 'mapping'],
                'sensors': ['sensor', 'camera', 'lidar', 'imu', 'gps'],
                'navigation': ['navigation', 'planning', 'path', 'motion'],
                'control': ['control', 'controller', 'motor', 'actuator']
            }
            
            category_keywords = category_terms.get(category.value, [category.value])
            
            # Strong boost for exact type match
            if category.value in result_type:
                category_match_bonus += 1.0
            
            # Moderate boost for description/name matches
            for keyword in category_keywords:
                if keyword in combined_text:
                    category_match_bonus += 0.3
                    break  # Don't double-count same category
        
        # Strong sensor matching boost
        sensor_match_bonus = 0.0
        for sensor in requirements.sensors:
            sensor_keywords = sensor.value.replace("_", " ")
            if sensor_keywords in combined_text:
                sensor_match_bonus += 0.8
            
            # Additional specific sensor checks
            if sensor.value == "camera":
                camera_terms = ["camera", "vision", "image", "rgb", "stereo", "depth"]
                if any(term in combined_text for term in camera_terms):
                    sensor_match_bonus += 0.5
        
        # Penalize mismatched categories strongly
        category_penalty = 0.0
        if requirements.categories:
            # Check if this is clearly the wrong category
            wrong_category_indicators = {
                'perception': ['localization', 'slam', 'mapping', 'amcl', 'gmapping', 'cartographer'],
                'localization': ['detection', 'recognition', 'tracking', 'yolo', 'darknet'],
                'sensors': ['planner', 'controller', 'navigation']
            }
            
            for req_category in requirements.categories:
                wrong_indicators = wrong_category_indicators.get(req_category.value, [])
                if any(indicator in combined_text for indicator in wrong_indicators):
                    category_penalty += 0.5
        
        # Performance requirements
        perf_bonus = 0.0
        if "best" in requirements.performance_requirements:
            # Boost popular/well-known packages
            popular_indicators = ["nav", "slam", "move_base", "amcl", "gmapping", "darknet", "yolo"]
            for indicator in popular_indicators:
                if indicator in result_name:
                    perf_bonus += 0.1
        
        # Search type weighting
        search_type_bonus = 0.0
        if result.get("search_type") == "semantic":
            search_type_bonus += 0.1  # Slight preference for semantic matches
        
        # Apply all bonuses and penalties
        final_boost = boost + category_match_bonus + sensor_match_bonus + perf_bonus + search_type_bonus - category_penalty
        
        # Ensure we don't go negative
        final_boost = max(0.1, final_boost)
        
        return base_score * final_boost
    
    def _synthesize_response(self, query: str, requirements: QueryRequirements, results: List[Dict]) -> str:
        """Synthesize a human-readable response."""
        if not results:
            return self._generate_no_results_response(query, requirements)
        
        response_type = self._determine_response_type(query, requirements)
        
        if response_type == "recommendation":
            return self._generate_recommendation_response(query, requirements, results)
        elif response_type == "comparison":
            return self._generate_comparison_response(query, requirements, results)
        elif response_type == "explanation":
            return self._generate_explanation_response(query, requirements, results)
        else:
            return self._generate_list_response(query, requirements, results)
    
    def _determine_response_type(self, query: str, requirements: QueryRequirements) -> str:
        """Determine the type of response to generate."""
        query_lower = query.lower()
        
        if "best" in query_lower or "recommend" in query_lower:
            return "recommendation"
        elif "compare" in query_lower or "difference" in query_lower:
            return "comparison"
        elif "what is" in query_lower or "explain" in query_lower:
            return "explanation"
        else:
            return "list"
    
    def _determine_search_type(self, requirements: QueryRequirements) -> str:
        """Determine the primary search type used."""
        if requirements.categories or requirements.sensors:
            return "structured"
        elif requirements.keywords:
            return "semantic"
        else:
            return "text"
    
    def _generate_recommendation_response(self, query: str, requirements: QueryRequirements, results: List[Dict]) -> str:
        """Generate a recommendation-style response."""
        if not results:
            return "I couldn't find any components matching your requirements."
        
        top_result = results[0]
        
        # Handle list fields
        name = top_result['name']
        if isinstance(name, list):
            name = name[0] if name else "Unknown"
        
        description = top_result['description']
        if isinstance(description, list):
            description = description[0] if description else "No description available"
        
        response = f"Based on your requirements, I recommend **{name}**.\n\n"
        response += f"**Description:** {description}\n\n"
        
        if len(results) > 1:
            response += "**Alternative options:**\n"
            for i, result in enumerate(results[1:4], 2):  # Show top 3 alternatives
                alt_name = result['name']
                if isinstance(alt_name, list):
                    alt_name = alt_name[0] if alt_name else "Unknown"
                
                alt_desc = result['description']
                if isinstance(alt_desc, list):
                    alt_desc = alt_desc[0] if alt_desc else "No description"
                
                if len(alt_desc) > 100:
                    alt_desc = alt_desc[:100] + "..."
                
                response += f"{i}. **{alt_name}** - {alt_desc}\n"
        
        # Add reasoning based on requirements
        if requirements.sensors:
            sensor_names = [s.value.replace("_", " ") for s in requirements.sensors]
            response += f"\n**Why this recommendation:** This component is suitable for your sensor setup ({', '.join(sensor_names)})"
        
        if requirements.environment and requirements.environment.value != "unknown":
            response += f" and {requirements.environment.value} environments."
        
        return response
    
    def _generate_comparison_response(self, query: str, requirements: QueryRequirements, results: List[Dict]) -> str:
        """Generate a comparison-style response."""
        if len(results) < 2:
            return self._generate_recommendation_response(query, requirements, results)
        
        response = "Here's a comparison of the top options:\n\n"
        
        for i, result in enumerate(results[:3], 1):
            response += f"**{i}. {result['name']}**\n"
            response += f"   - {result['description'][:150]}...\n"
            response += f"   - Relevance Score: {result.get('final_score', 0.0):.2f}\n\n"
        
        return response
    
    def _generate_explanation_response(self, query: str, requirements: QueryRequirements, results: List[Dict]) -> str:
        """Generate an explanation-style response."""
        if not results:
            return "I couldn't find information about the requested component."
        
        top_result = results[0]
        response = f"**{top_result['name']}** is a ROS component that provides {top_result['description']}\n\n"
        
        # Add context based on category
        if requirements.categories:
            category = requirements.categories[0]
            response += f"As a **{category.value}** component, it's typically used for "
            
            if category.value == "slam":
                response += "simultaneous localization and mapping tasks.\n\n"
            elif category.value == "navigation":
                response += "robot navigation and path planning.\n\n"
            elif category.value == "perception":
                response += "sensor data processing and environment understanding.\n\n"
            else:
                response += f"{category.value}-related functionality.\n\n"
        
        return response
    
    def _generate_list_response(self, query: str, requirements: QueryRequirements, results: List[Dict]) -> str:
        """Generate a list-style response."""
        if not results:
            return "No components found matching your query."
        
        response = f"I found {len(results)} components matching your query:\n\n"
        
        for i, result in enumerate(results[:5], 1):
            name = result['name']
            if isinstance(name, list):
                name = name[0] if name else "Unknown"
            
            description = result['description']
            if isinstance(description, list):
                description = description[0] if description else "No description"
            
            if len(description) > 120:
                description = description[:120] + "..."
            
            response += f"**{i}. {name}**\n"
            response += f"   {description}\n\n"
        
        if len(results) > 5:
            response += f"... and {len(results) - 5} more results.\n"
        
        return response
    
    def _generate_no_results_response(self, query: str, requirements: QueryRequirements) -> str:
        """Generate a response when no results are found."""
        response = "I couldn't find any components that exactly match your requirements. "
        
        if requirements.categories:
            response += f"However, you might want to look for {requirements.categories[0].value} components in general. "
        
        response += "Try rephrasing your query or using broader terms."
        
        return response
    
    def _get_recommendation_template(self) -> str:
        return "Based on your requirements, I recommend {component}. {reasoning}"
    
    def _get_comparison_template(self) -> str:
        return "Here's a comparison of the top options: {comparison}"
    
    def _get_explanation_template(self) -> str:
        return "{component} is a {type} component that {description}. {context}"
    
    def _get_list_template(self) -> str:
        return "I found {count} components: {list}"

def test_nlp_search_engine():
    """Test the NLP search engine with example queries."""
    # Initialize with your TTL file
    ttl_file = "/home/ritz/Desktop/RnD/data/components.ttl"
    engine = NLPSearchEngine(ttl_file)
    
    test_queries = [
        "What is the best SLAM package for a robot with a 3D LiDAR and an IMU in a large, outdoor environment?",
        "I need a navigation stack for indoor environments",
        "Recommend localization packages for outdoor robots with GPS",
        "Find components for object detection",
        "What planning algorithms work with 2D LiDAR?"
    ]
    
    for query in test_queries:
        print(f"\n" + "="*80)
        print(f"Query: {query}")
        print("="*80)
        
        result = engine.process_natural_language_query(query)
        
        print(f"Synthesized Response:")
        print(result["synthesized_response"])
        print(f"\nFound {result['metadata']['total_found']} components")
        print(f"Search type: {result['metadata']['search_type']}")

if __name__ == "__main__":
    test_nlp_search_engine()
