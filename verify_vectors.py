#!/usr/bin/env python3
"""
Vector Verification Utility
Checks if ROS packages/components are stored as vectors in Apache Solr
"""

import requests
import json
from typing import Dict, List, Any
import sys

class VectorVerifier:
    def __init__(self, solr_url: str = "http://localhost:8984/solr/ros_explorer"):
        self.solr_url = solr_url
        
    def check_solr_connection(self) -> bool:
        """Check if Solr is running and accessible"""
        try:
            response = requests.get(f"{self.solr_url}/admin/ping", timeout=5)
            if response.status_code == 200:
                print("✅ Solr is running and accessible")
                return True
            else:
                print(f"❌ Solr ping failed with status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to Solr: {e}")
            return False
    
    def get_total_documents(self) -> int:
        """Get total number of documents in Solr"""
        try:
            response = requests.get(f"{self.solr_url}/select", params={
                'q': '*:*',
                'rows': '0',
                'wt': 'json'
            })
            data = response.json()
            total = data['response']['numFound']
            print(f"📊 Total documents in Solr: {total}")
            return total
        except Exception as e:
            print(f"❌ Error getting document count: {e}")
            return 0
    
    def check_vector_field_exists(self) -> bool:
        """Check if vector field exists in Solr schema"""
        try:
            response = requests.get(f"{self.solr_url}/schema/fields/vector")
            if response.status_code == 200:
                field_info = response.json()
                print("✅ Vector field exists in schema")
                print(f"   Field type: {field_info['field'].get('type', 'Unknown')}")
                print(f"   Stored: {field_info['field'].get('stored', 'Unknown')}")
                print(f"   Indexed: {field_info['field'].get('indexed', 'Unknown')}")
                return True
            else:
                print("❌ Vector field does not exist in schema")
                return False
        except Exception as e:
            print(f"❌ Error checking vector field: {e}")
            return False
    
    def count_documents_with_vectors(self) -> Dict[str, int]:
        """Count how many documents have vector data"""
        try:
            # Count documents with vector field
            response = requests.get(f"{self.solr_url}/select", params={
                'q': 'vector:*',
                'rows': '0',
                'wt': 'json'
            })
            data = response.json()
            with_vectors = data['response']['numFound']
            
            # Count documents without vector field
            response = requests.get(f"{self.solr_url}/select", params={
                'q': '*:* AND -vector:*',
                'rows': '0',
                'wt': 'json'
            })
            data = response.json()
            without_vectors = data['response']['numFound']
            
            result = {
                'with_vectors': with_vectors,
                'without_vectors': without_vectors,
                'total': with_vectors + without_vectors
            }
            
            print(f"📈 Documents with vectors: {with_vectors}")
            print(f"📉 Documents without vectors: {without_vectors}")
            print(f"📊 Coverage: {(with_vectors/result['total']*100):.1f}%" if result['total'] > 0 else "N/A")
            
            return result
        except Exception as e:
            print(f"❌ Error counting vectorized documents: {e}")
            return {'with_vectors': 0, 'without_vectors': 0, 'total': 0}
    
    def sample_vector_data(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Get sample documents with their vector data"""
        try:
            response = requests.get(f"{self.solr_url}/select", params={
                'q': 'vector:*',
                'fl': 'id,name,vector',
                'rows': str(limit),
                'wt': 'json'
            })
            data = response.json()
            docs = data['response']['docs']
            
            print(f"🔍 Sample vector data (showing {len(docs)} documents):")
            for i, doc in enumerate(docs, 1):
                component_id = doc.get('id', 'Unknown')
                name = doc.get('name', ['Unknown'])[0] if isinstance(doc.get('name'), list) else doc.get('name', 'Unknown')
                vector = doc.get('vector', [])
                vector_length = len(vector) if vector else 0
                
                print(f"   {i}. ID: {component_id}")
                print(f"      Name: {name}")
                print(f"      Vector dimensions: {vector_length}")
                if vector and len(vector) > 0:
                    # Show first few values
                    sample_values = vector[:5]
                    print(f"      Sample values: {sample_values}")
                    
                    # Check if values are numeric strings
                    try:
                        numeric_values = [float(v) for v in sample_values]
                        print(f"      Numeric range: {min(numeric_values):.4f} to {max(numeric_values):.4f}")
                    except:
                        print("      Values are not numeric")
                print()
            
            return docs
        except Exception as e:
            print(f"❌ Error getting sample vector data: {e}")
            return []
    
    def check_vector_dimensions(self) -> Dict[str, int]:
        """Check vector dimensions across all documents"""
        try:
            response = requests.get(f"{self.solr_url}/select", params={
                'q': 'vector:*',
                'fl': 'id,vector',
                'rows': '100',
                'wt': 'json'
            })
            data = response.json()
            docs = data['response']['docs']
            
            dimensions = {}
            for doc in docs:
                vector = doc.get('vector', [])
                dim = len(vector) if vector else 0
                dimensions[dim] = dimensions.get(dim, 0) + 1
            
            print("📏 Vector dimensions distribution:")
            for dim, count in sorted(dimensions.items()):
                print(f"   {dim} dimensions: {count} documents")
            
            return dimensions
        except Exception as e:
            print(f"❌ Error checking vector dimensions: {e}")
            return {}
    
    def verify_vector_quality(self) -> Dict[str, Any]:
        """Verify the quality of stored vectors"""
        try:
            response = requests.get(f"{self.solr_url}/select", params={
                'q': 'vector:*',
                'fl': 'id,vector',
                'rows': '10',
                'wt': 'json'
            })
            data = response.json()
            docs = data['response']['docs']
            
            quality_stats = {
                'empty_vectors': 0,
                'non_numeric_vectors': 0,
                'valid_vectors': 0,
                'dimension_consistency': True,
                'expected_dimension': None
            }
            
            dimensions_seen = set()
            
            for doc in docs:
                vector = doc.get('vector', [])
                
                if not vector or len(vector) == 0:
                    quality_stats['empty_vectors'] += 1
                    continue
                
                dimensions_seen.add(len(vector))
                
                try:
                    # Try to convert to float
                    numeric_vector = [float(v) for v in vector]
                    quality_stats['valid_vectors'] += 1
                    
                    if quality_stats['expected_dimension'] is None:
                        quality_stats['expected_dimension'] = len(vector)
                        
                except (ValueError, TypeError):
                    quality_stats['non_numeric_vectors'] += 1
            
            if len(dimensions_seen) > 1:
                quality_stats['dimension_consistency'] = False
            
            print("🔍 Vector Quality Analysis:")
            print(f"   ✅ Valid numeric vectors: {quality_stats['valid_vectors']}")
            print(f"   ❌ Empty vectors: {quality_stats['empty_vectors']}")
            print(f"   ❌ Non-numeric vectors: {quality_stats['non_numeric_vectors']}")
            print(f"   📏 Dimension consistency: {'✅ Consistent' if quality_stats['dimension_consistency'] else '❌ Inconsistent'}")
            if quality_stats['expected_dimension']:
                print(f"   📐 Expected dimension: {quality_stats['expected_dimension']}")
            
            return quality_stats
        except Exception as e:
            print(f"❌ Error verifying vector quality: {e}")
            return {}
    
    def run_full_verification(self) -> bool:
        """Run complete vector verification"""
        print("🔍 ROS Component Explorer - Vector Verification\n")
        print("=" * 60)
        
        # Step 1: Check Solr connection
        if not self.check_solr_connection():
            return False
        print()
        
        # Step 2: Check total documents
        total_docs = self.get_total_documents()
        if total_docs == 0:
            print("❌ No documents found in Solr")
            return False
        print()
        
        # Step 3: Check vector field
        vector_field_exists = self.check_vector_field_exists()
        print()
        
        # Step 4: Count vectorized documents
        vector_stats = self.count_documents_with_vectors()
        print()
        
        # Step 5: Check vector dimensions
        self.check_vector_dimensions()
        print()
        
        # Step 6: Sample vector data
        self.sample_vector_data()
        
        # Step 7: Quality check
        self.verify_vector_quality()
        print()
        
        # Final assessment
        print("=" * 60)
        print("📋 VERIFICATION SUMMARY:")
        
        if vector_stats['with_vectors'] > 0:
            print("✅ VECTORS ARE STORED!")
            print(f"   • {vector_stats['with_vectors']} components have vector embeddings")
            print(f"   • Vector coverage: {(vector_stats['with_vectors']/vector_stats['total']*100):.1f}%")
            print("   • Vectors can be used for semantic search")
            return True
        else:
            print("❌ NO VECTORS FOUND!")
            print("   • Components are stored but without vector embeddings")
            print("   • Run vector generation to enable semantic search")
            return False

def main():
    verifier = VectorVerifier()
    success = verifier.run_full_verification()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
