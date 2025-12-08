#!/usr/bin/env python3
"""
Manual Indexing Script for ROS Component Explorer.

This script allows manual indexing of ROS components from TTL files into Apache Solr.
Use this script to:
- Re-index all components from the default data files
- Add new TTL files to the index
- Clear and rebuild the entire index

Usage:
    python index_components.py                    # Index default components
    python index_components.py --file custom.ttl  # Index a specific TTL file
    python index_components.py --clear            # Clear index before loading
    python index_components.py --list             # List all indexed components
"""

import argparse
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_solr_connection():
    """Check if Solr is running and accessible."""
    import requests
    try:
        response = requests.get("http://localhost:8984/solr/ros_explorer/admin/ping", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def clear_index():
    """Clear all documents from the Solr index."""
    from pysolr import Solr
    
    print("Clearing existing index...")
    solr = Solr("http://localhost:8984/solr/ros_explorer", timeout=10)
    solr.delete(q="*:*")
    solr.commit()
    print("Index cleared successfully.")


def list_components():
    """List all indexed components."""
    from pysolr import Solr
    
    solr = Solr("http://localhost:8984/solr/ros_explorer", timeout=10)
    results = solr.search("*:*", rows=1000)
    
    print(f"\nTotal indexed components: {results.hits}")
    print("-" * 60)
    
    if results.hits > 0:
        # Group by type
        by_type = {}
        for doc in results.docs:
            comp_type = doc.get('type', 'Unknown')
            if comp_type not in by_type:
                by_type[comp_type] = []
            by_type[comp_type].append(doc.get('name', 'Unknown'))
        
        for comp_type, names in sorted(by_type.items()):
            print(f"\n{comp_type} ({len(names)}):")
            for name in sorted(names):
                print(f"  - {name}")
    else:
        print("No components indexed yet.")


def index_ttl_file(ttl_file: str, clear_first: bool = False):
    """Index a TTL file into Solr."""
    from backend.solr_manager import SolrManager
    
    file_path = Path(ttl_file)
    if not file_path.exists():
        # Try relative to data directory
        file_path = project_root / "data" / ttl_file
        if not file_path.exists():
            print(f"Error: TTL file not found: {ttl_file}")
            return False
    
    if clear_first:
        clear_index()
    
    print(f"Indexing components from: {file_path}")
    
    try:
        solr_manager = SolrManager(str(file_path))
        total = len(solr_manager.get_all_components())
        print(f"Successfully indexed {total} components.")
        return True
    except Exception as e:
        print(f"Error indexing components: {e}")
        return False


def index_all_default_files(clear_first: bool = False):
    """Index all default TTL files."""
    from backend.solr_manager import SolrManager
    
    # Priority order of TTL files
    ttl_files = [
        "components_clean.ttl",
        "expanded_components_ros.ttl",
        "mobile_robot_packages_hierarchical.ttl",
    ]
    
    if clear_first:
        clear_index()
    
    # Load primary file
    primary_file = project_root / "data" / ttl_files[0]
    if primary_file.exists():
        print(f"Loading primary file: {primary_file}")
        solr_manager = SolrManager(str(primary_file))
        
        # Load additional files
        for ttl_file in ttl_files[1:]:
            file_path = project_root / "data" / ttl_file
            if file_path.exists():
                print(f"Loading additional file: {file_path}")
                try:
                    solr_manager.load_additional_ttl_file(str(file_path))
                except Exception as e:
                    print(f"Warning: Could not load {ttl_file}: {e}")
        
        total = len(solr_manager.get_all_components())
        print(f"\nTotal components indexed: {total}")
        return True
    else:
        print(f"Error: Primary TTL file not found: {primary_file}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Index ROS components into Apache Solr",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python index_components.py                     # Index all default TTL files
  python index_components.py --file data.ttl    # Index a specific TTL file
  python index_components.py --clear            # Clear and re-index everything
  python index_components.py --list             # Show all indexed components
        """
    )
    
    parser.add_argument(
        "--file", "-f",
        help="Path to a specific TTL file to index"
    )
    parser.add_argument(
        "--clear", "-c",
        action="store_true",
        help="Clear existing index before indexing"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all indexed components"
    )
    
    args = parser.parse_args()
    
    print("ROS Component Explorer - Manual Indexing Tool")
    print("=" * 50)
    
    # Check Solr connection
    if not check_solr_connection():
        print("\nError: Cannot connect to Solr!")
        print("Make sure Solr is running on http://localhost:8984")
        print("Start Solr with: ./solr-9.4.1/bin/solr start -p 8984")
        sys.exit(1)
    
    print("Solr connection: OK")
    
    if args.list:
        list_components()
    elif args.file:
        index_ttl_file(args.file, args.clear)
    else:
        index_all_default_files(args.clear)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
