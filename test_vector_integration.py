#!/usr/bin/env python3
"""
Test script for vector integration functionality.
This script tests the basic functionality without requiring the full demo.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_vector_generator():
    """Test the vector generator functionality."""
    print("Testing Vector Generator...")
    
    try:
        from backend.vector_generator import VectorGenerator
        
        # Initialize generator
        generator = VectorGenerator()
        print(f"✓ Vector generator initialized with model: {generator.model_name}")
        print(f"✓ Vector dimension: {generator.vector_dimension}")
        
        # Test text processing
        test_component = {
            'name': 'Test Component',
            'type': 'TestType',
            'description': 'A test component for testing purposes',
            'package': 'test_package'
        }
        
        text = generator._create_component_text(test_component)
        print(f"✓ Text processing works: {text[:50]}...")
        
        print("✓ Vector generator test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Vector generator test failed: {e}")
        return False

def test_schema_updater():
    """Test the schema updater functionality."""
    print("\nTesting Schema Updater...")
    
    try:
        from backend.schema_updater import SolrSchemaUpdater
        
        # Initialize updater
        updater = SolrSchemaUpdater()
        print("✓ Schema updater initialized")
        
        # Test field existence check
        exists = updater.check_field_exists("vector")
        print(f"✓ Field existence check works: vector field exists = {exists}")
        
        # Test schema info retrieval
        schema_info = updater.get_schema_info()
        if schema_info:
            print("✓ Schema info retrieval works")
        else:
            print("⚠ Schema info retrieval returned None (may be expected)")
        
        print("✓ Schema updater test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Schema updater test failed: {e}")
        return False

def test_solr_manager():
    """Test the Solr manager functionality."""
    print("\nTesting Solr Manager...")
    
    try:
        from backend.solr_manager import SolrManager
        
        # Initialize manager
        manager = SolrManager("data/components_clean.ttl")
        print("✓ Solr manager initialized")
        
        # Test basic search
        results = manager.get_all_components()
        print(f"✓ Basic search works: found {len(results)} components")
        
        # Test text search
        text_results = manager.search_components("localization")
        print(f"✓ Text search works: found {len(text_results)} localization components")
        
        print("✓ Solr manager test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Solr manager test failed: {e}")
        return False

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing Module Imports...")
    
    modules = [
        'backend.vector_generator',
        'backend.schema_updater', 
        'backend.solr_manager',
        'sentence_transformers',
        'numpy',
        'pysolr'
    ]
    
    all_imports_ok = True
    
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module} imported successfully")
        except ImportError as e:
            print(f"✗ {module} import failed: {e}")
            all_imports_ok = False
    
    return all_imports_ok

def main():
    """Run all tests."""
    print("=" * 60)
    print("ROS Component Explorer - Vector Integration Tests")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_vector_generator,
        test_schema_updater,
        test_solr_manager
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Vector integration is ready to use.")
        print("\nNext steps:")
        print("1. Run the full demo: python backend/vector_demo.py")
        print("2. Start the web interface: python main.py")
        print("3. Check the README_VECTOR_INTEGRATION.md for detailed usage")
    else:
        print("⚠ Some tests failed. Check the errors above.")
        print("\nTroubleshooting:")
        print("1. Ensure all dependencies are installed: pip install -r requirements.txt")
        print("2. Check that Solr is running on port 8984")
        print("3. Verify the data/components_clean.ttl file exists")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 