#!/usr/bin/env python3
"""
Detailed Vector Component Analysis
Shows all components with vectors and helps debug admin interface issues
"""

import requests
import json
from typing import List, Dict, Any

def get_all_components_with_vectors():
    """Get all components and their vector status"""
    solr_url = "http://localhost:8984/solr/ros_explorer"
    
    try:
        # Get all documents with high row count to ensure we get everything
        response = requests.get(f"{solr_url}/select", params={
            'q': '*:*',
            'fl': 'id,name,vector',
            'rows': '100',  # Set high to get all
            'wt': 'json',
            'sort': 'id asc'  # Sort for consistent ordering
        })
        
        data = response.json()
        docs = data['response']['docs']
        total_found = data['response']['numFound']
        
        print(f"🔍 Complete Vector Analysis - Found {total_found} total components\n")
        print("=" * 80)
        
        components_with_vectors = []
        components_without_vectors = []
        
        for i, doc in enumerate(docs, 1):
            component_id = doc.get('id', 'Unknown')
            name = doc.get('name', ['Unknown'])[0] if isinstance(doc.get('name'), list) else doc.get('name', 'Unknown')
            vector = doc.get('vector', [])
            has_vector = vector is not None and len(vector) > 0
            vector_length = len(vector) if vector else 0
            
            component_info = {
                'index': i,
                'id': component_id,
                'name': name,
                'has_vector': has_vector,
                'vector_length': vector_length
            }
            
            if has_vector:
                components_with_vectors.append(component_info)
                status = "✅"
            else:
                components_without_vectors.append(component_info)
                status = "❌"
            
            print(f"{status} {i:2d}. {name}")
            print(f"    ID: {component_id}")
            print(f"    Vector: {'Yes' if has_vector else 'No'} ({vector_length} dimensions)")
            
            if has_vector and vector_length > 0:
                # Show first few vector values for verification
                sample_values = vector[:3]
                try:
                    numeric_sample = [f"{float(v):.4f}" for v in sample_values]
                    print(f"    Sample: [{', '.join(numeric_sample)}, ...]")
                except:
                    print(f"    Sample: {sample_values} (non-numeric)")
            print()
        
        print("=" * 80)
        print("📊 SUMMARY:")
        print(f"   Total components: {len(docs)}")
        print(f"   ✅ With vectors: {len(components_with_vectors)}")
        print(f"   ❌ Without vectors: {len(components_without_vectors)}")
        print(f"   📈 Vector coverage: {len(components_with_vectors)/len(docs)*100:.1f}%")
        
        if len(components_without_vectors) > 0:
            print("\n❌ Components missing vectors:")
            for comp in components_without_vectors:
                print(f"   - {comp['name']} ({comp['id']})")
        
        # Check for admin interface pagination issue
        print("\n🔍 ADMIN INTERFACE DEBUGGING:")
        check_admin_interface_pagination(solr_url)
        
        return components_with_vectors, components_without_vectors
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return [], []

def check_admin_interface_pagination(solr_url: str):
    """Check common pagination limits that might affect admin interface"""
    
    # Test different row limits
    test_limits = [10, 20, 25, 50]
    
    for limit in test_limits:
        try:
            response = requests.get(f"{solr_url}/select", params={
                'q': 'vector:*',
                'rows': str(limit),
                'wt': 'json'
            })
            data = response.json()
            returned = len(data['response']['docs'])
            total = data['response']['numFound']
            
            print(f"   Rows={limit}: Returns {returned} out of {total} total")
            
            if returned == 10 and limit > 10:
                print(f"   ⚠️  Possible admin interface default limit: {returned}")
                
        except Exception as e:
            print(f"   Error testing limit {limit}: {e}")

def check_solr_admin_query():
    """Show the exact query that might be used in Solr admin"""
    print("\n🌐 SOLR ADMIN INTERFACE QUERIES:")
    print("If you're using the Solr Admin UI, try these queries:")
    print()
    print("1. To see ALL components with vectors:")
    print("   Query: vector:*")
    print("   Fields: id,name,vector")
    print("   Rows: 50 (increase from default 10)")
    print()
    print("2. To count components with vectors:")
    print("   Query: vector:*")
    print("   Rows: 0")
    print("   Check 'numFound' in response")
    print()
    print("3. Direct admin URL with proper parameters:")
    admin_url = "http://localhost:8984/solr/#/ros_explorer/query"
    print(f"   {admin_url}")
    print("   Set rows=50 or higher to see all results")
    print()

if __name__ == "__main__":
    print("🔍 ROS Component Explorer - Complete Vector Analysis\n")
    
    with_vectors, without_vectors = get_all_components_with_vectors()
    check_solr_admin_query()
    
    if len(with_vectors) == 19:
        print("✅ SUCCESS: All 19 components have vectors!")
        print("   If you only see 10 in admin, increase the 'rows' parameter to 50+")
    elif len(with_vectors) > 0:
        print(f"⚠️  PARTIAL: {len(with_vectors)} components have vectors, {len(without_vectors)} missing")
    else:
        print("❌ FAILURE: No components have vectors")
