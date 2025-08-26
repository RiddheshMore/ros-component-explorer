#!/usr/bin/env python3
"""
Solr Diagnostic Script
This script helps diagnose Solr setup and vector field configuration issues.
"""

import requests
import json
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_solr_status():
    """Check basic Solr status."""
    print("🔍 Checking Solr Status...")
    
    try:
        # Check main Solr endpoint
        response = requests.get("http://localhost:8984/solr/")
        if response.status_code == 200:
            print("✓ Solr is running on port 8984")
        else:
            print(f"✗ Solr returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to Solr on port 8984")
        print("  Make sure Solr is running: solr start -p 8984")
        return False
    except Exception as e:
        print(f"✗ Error checking Solr: {e}")
        return False
    
    return True

def check_core_status():
    """Check if the ros_explorer core exists and is accessible."""
    print("\n🔍 Checking Core Status...")
    
    try:
        # Check core status
        response = requests.get("http://localhost:8984/solr/admin/cores?action=STATUS&wt=json")
        if response.status_code == 200:
            cores = response.json()
            if 'ros_explorer' in cores['status']:
                print("✓ ros_explorer core exists and is accessible")
                core_info = cores['status']['ros_explorer']
                print(f"  - Core name: {core_info.get('name', 'Unknown')}")
                print(f"  - Core state: {core_info.get('state', 'Unknown')}")
                print(f"  - Instance directory: {core_info.get('instanceDir', 'Unknown')}")
            else:
                print("✗ ros_explorer core not found")
                print("  Available cores:", list(cores['status'].keys()))
                return False
        else:
            print(f"✗ Failed to get core status: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error checking core status: {e}")
        return False
    
    return True

def check_schema():
    """Check schema information."""
    print("\n🔍 Checking Schema...")
    
    try:
        # Get schema info
        response = requests.get("http://localhost:8984/solr/ros_explorer/schema")
        if response.status_code == 200:
            schema = response.json()
            print("✓ Schema accessible")
            
            # Check fields
            fields = schema.get('fields', [])
            field_names = [f['name'] for f in fields]
            print(f"  - Total fields: {len(fields)}")
            
            if 'vector' in field_names:
                print("✓ Vector field exists")
                vector_field = next(f for f in fields if f['name'] == 'vector')
                print(f"  - Vector field type: {vector_field.get('type', 'Unknown')}")
                print(f"  - Vector field stored: {vector_field.get('stored', 'Unknown')}")
                print(f"  - Vector field indexed: {vector_field.get('indexed', 'Unknown')}")
            else:
                print("✗ Vector field not found")
                print("  Available fields:", field_names[:10], "..." if len(field_names) > 10 else "")
            
            # Check field types
            field_types = schema.get('fieldTypes', [])
            field_type_names = [ft['name'] for ft in field_types]
            print(f"  - Total field types: {len(field_types)}")
            
            vector_types = [ft for ft in field_type_names if 'vector' in ft.lower()]
            if vector_types:
                print(f"  - Vector field types available: {vector_types}")
            else:
                print("  - No vector field types found")
                print("    This may indicate an older Solr version")
            
        else:
            print(f"✗ Failed to get schema: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error checking schema: {e}")
        return False
    
    return True

def check_solr_version():
    """Check Solr version information."""
    print("\n🔍 Checking Solr Version...")
    
    try:
        response = requests.get("http://localhost:8984/solr/ros_explorer/admin/info/system")
        if response.status_code == 200:
            info = response.json()
            version = info.get('lucene', {}).get('solr-spec-version', 'Unknown')
            print(f"✓ Solr version: {version}")
            
            # Check if version supports vector fields
            if version != 'Unknown':
                try:
                    major_version = int(version.split('.')[0])
                    if major_version >= 8:
                        print("✓ Solr version should support vector fields")
                    else:
                        print("⚠ Solr version may not support vector fields")
                        print("  Consider upgrading to Solr 8+ for full vector support")
                except ValueError:
                    print("⚠ Could not parse Solr version")
            else:
                print("⚠ Could not determine Solr version")
                
        else:
            print(f"✗ Failed to get version info: {response.status_code}")
    except Exception as e:
        print(f"✗ Error checking Solr version: {e}")

def check_data():
    """Check if there's data in the core."""
    print("\n🔍 Checking Data...")
    
    try:
        response = requests.get("http://localhost:8984/solr/ros_explorer/select?q=*:*&rows=0&wt=json")
        if response.status_code == 200:
            result = response.json()
            num_docs = result['response']['numFound']
            print(f"✓ Core contains {num_docs} documents")
            
            if num_docs > 0:
                # Check a sample document
                response = requests.get("http://localhost:8984/solr/ros_explorer/select?q=*:*&rows=1&wt=json")
                if response.status_code == 200:
                    sample = response.json()
                    if sample['response']['docs']:
                        doc = sample['response']['docs'][0]
                        print("✓ Sample document structure:")
                        for key, value in doc.items():
                            if key != 'vector':  # Don't show vector data
                                print(f"    - {key}: {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")
                        if 'vector' in doc:
                            vector_data = doc['vector']
                            if isinstance(vector_data, list):
                                print(f"    - vector: [{len(vector_data)} values]")
                            else:
                                print(f"    - vector: {str(vector_data)[:50]}...")
            else:
                print("⚠ Core is empty - no documents found")
                
        else:
            print(f"✗ Failed to check data: {response.status_code}")
    except Exception as e:
        print(f"✗ Error checking data: {e}")

def suggest_solutions():
    """Suggest solutions based on the diagnostic results."""
    print("\n💡 Suggested Solutions...")
    
    print("1. If Solr is not running:")
    print("   solr start -p 8984")
    
    print("\n2. If ros_explorer core doesn't exist:")
    print("   curl \"http://localhost:8984/solr/admin/cores?action=CREATE&name=ros_explorer&configSet=_default&wt=json\"")
    
    print("\n3. If vector field type is not supported:")
    print("   - Upgrade to Solr 8.0+ for DenseVectorField support")
    print("   - Or use the legacy text field approach (already implemented)")
    
    print("\n4. If you need to recreate the core:")
    print("   curl \"http://localhost:8984/solr/admin/cores?action=UNLOAD&core=ros_explorer&deleteIndex=true&deleteDataDir=true&wt=json\"")
    print("   curl \"http://localhost:8984/solr/admin/cores?action=CREATE&name=ros_explorer&configSet=_default&wt=json\"")
    
    print("\n5. For vector field issues:")
    print("   - Check Solr version compatibility")
    print("   - Verify configset has vector field types")
    print("   - Use the updated schema updater with fallback options")

def main():
    """Run the complete diagnostic."""
    print("=" * 60)
    print("🔧 Solr Diagnostic Tool")
    print("=" * 60)
    
    # Run all checks
    checks = [
        check_solr_status,
        check_core_status,
        check_schema,
        check_solr_version,
        check_data
    ]
    
    all_passed = True
    for check in checks:
        try:
            if not check():
                all_passed = False
        except Exception as e:
            print(f"✗ Check {check.__name__} failed with exception: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All checks passed! Solr should be working correctly.")
        print("You can now run: python backend/vector_demo.py")
    else:
        print("⚠ Some checks failed. See suggestions below.")
        suggest_solutions()
    
    print("=" * 60)

if __name__ == "__main__":
    main() 