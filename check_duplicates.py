#!/usr/bin/env python3
"""Check for duplicate components in Solr."""

from pysolr import Solr
from collections import defaultdict

SOLR_URL = "http://localhost:8984/solr/ros_explorer"

def check_duplicates():
    """Check for duplicate components in Solr."""
    solr = Solr(SOLR_URL, timeout=10)
    
    # Get all documents from Solr
    results = solr.search("*:*", rows=1000)
    print(f"Total documents in Solr: {results.hits}")
    
    # Group by name to find duplicates
    by_name = defaultdict(list)
    by_uri = defaultdict(list)
    
    for doc in results.docs:
        name = doc.get('name', 'Unknown')
        uri = doc.get('id', 'Unknown')
        doc_type = doc.get('type', 'Unknown')
        
        # Handle cases where fields might be lists
        if isinstance(name, list):
            name = name[0] if name else 'Unknown'
        if isinstance(uri, list):
            uri = uri[0] if uri else 'Unknown'
        if isinstance(doc_type, list):
            doc_type = doc_type[0] if doc_type else 'Unknown'
        
        by_name[name].append({'uri': uri, 'type': doc_type, 'doc': doc})
        by_uri[uri].append({'name': name, 'type': doc_type, 'doc': doc})
    
    # Find duplicates by name
    name_duplicates = {name: docs for name, docs in by_name.items() if len(docs) > 1}
    print(f"\nComponents with duplicate names: {len(name_duplicates)}")
    
    for name, docs in name_duplicates.items():
        print(f"\n{name}:")
        for doc in docs:
            print(f"  - Class: {doc['type']}, URI: {doc['uri']}")
    
    # Find duplicates by URI
    uri_duplicates = {uri: docs for uri, docs in by_uri.items() if len(docs) > 1}
    print(f"\nComponents with duplicate URIs: {len(uri_duplicates)}")
    
    for uri, docs in uri_duplicates.items():
        print(f"\n{uri}:")
        for doc in docs:
            print(f"  - Name: {doc['name']}, Class: {doc['type']}")
    
    # Show all unique component names and their types
    print(f"\nAll unique components by name:")
    for name in sorted(by_name.keys()):
        docs = by_name[name]
        if len(docs) == 1:
            print(f"  {name}: {docs[0]['type']}")
        else:
            types = [doc['type'] for doc in docs]
            print(f"  {name}: {types} (DUPLICATE)")

if __name__ == "__main__":
    check_duplicates()
