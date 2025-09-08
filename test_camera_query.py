#!/usr/bin/env python3
"""
Test script to debug LLM query processing
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from LLM.query_processor import NLQueryProcessor, QueryToSearchTranslator
from LLM.llm_search_engine import LLMSearchEngine
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_camera_query():
    """Test the camera object detection query."""
    
    print("Initializing LLM Search Engine...")
    engine = LLMSearchEngine("/home/ritz/ros-component-explorer/data/components_converted.ttl")
    
    processor = NLQueryProcessor()
    translator = QueryToSearchTranslator()
    
    # Test the exact query from the screenshot
    query = "Show me all the cameras that can be used for object detection and work with a Raspberry Pi"
    
    print(f"Original Query: {query}")
    print("=" * 60)
    
    # Parse the query
    requirements = processor.parse_query(query)
    
    print(f"Parsed Requirements:")
    print(f"  Primary Function: {requirements.primary_function}")
    print(f"  Categories: {[cat.value for cat in requirements.categories]}")
    print(f"  Sensors: {[sensor.value for sensor in requirements.sensors]}")
    print(f"  Environment: {requirements.environment.value if requirements.environment else 'None'}")
    print(f"  Performance Requirements: {requirements.performance_requirements}")
    print(f"  Constraints: {requirements.constraints}")
    print(f"  Keywords: {requirements.keywords}")
    print()
    
    # Translate to search parameters
    search_params = translator.translate_to_search_params(requirements)
    
    print(f"Search Parameters:")
    print(f"  Text Query: {search_params['text_query']}")
    print(f"  Filters: {search_params['filters']}")
    print(f"  Must Include: {search_params['must_include']}")
    print(f"  Should Include: {search_params['should_include']}")
    print(f"  Boost Fields: {search_params['boost_fields']}")
    
    # Test full search execution
    print("\n" + "=" * 80)
    print("FULL SEARCH RESULTS:")
    print("=" * 80)
    
    result = engine.process_natural_language_query(query, max_results=10)
    
    print(f"\nSynthesized Response:")
    print(result["synthesized_response"])
    
    print(f"\nComponents Found ({result['metadata']['total_found']} total):")
    print("-" * 50)
    
    for i, component in enumerate(result.get("components", []), 1):
        print(f"{i}. {component.get('name', 'Unknown')}")
        print(f"   Type: {component.get('type', component.get('class', 'Unknown'))}")
        print(f"   Score: {component.get('final_score', 0):.3f}")
        print(f"   Search Type: {component.get('search_type', 'unknown')}")
        print(f"   Description: {component.get('description', 'No description')[:100]}...")
        print()

if __name__ == "__main__":
    test_camera_query()
    test_camera_query()
