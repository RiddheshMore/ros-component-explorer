#!/usr/bin/env python3
"""
Simple test of the LLM query processor.
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from LLM.query_processor import NLQueryProcessor
    print("✅ Imported NLQueryProcessor")
    
    processor = NLQueryProcessor()
    print("✅ Created processor instance")
    
    query = "What is the best SLAM package for outdoor robots?"
    print(f"🔍 Testing query: {query}")
    
    result = processor.parse_query(query)
    print("✅ Query parsed successfully")
    
    print(f"📋 Results:")
    print(f"   Categories: {[c.value for c in result.categories]}")
    print(f"   Environment: {result.environment.value if result.environment else 'None'}")
    print(f"   Primary function: {result.primary_function}")
    print(f"   Keywords: {result.keywords}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
