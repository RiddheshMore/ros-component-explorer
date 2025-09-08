#!/usr/bin/env python3
"""Test the UI deduplication logic."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.solr_manager import SolrManager

def test_deduplication():
    """Test the deduplication logic used in the UI."""
    # Initialize Solr manager
    sm = SolrManager('data/components_clean.ttl')
    all_components = sm.get_all_components()
    
    print(f"Total components from Solr: {len(all_components)}")
    
    # Apply the same deduplication logic as in the UI
    unique_components = {}
    for component in all_components:
        name = component.get('name', '')
        class_name = component.get('class', '')
        
        # Handle cases where name or class might be lists
        if isinstance(name, list):
            name = name[0] if name else ''
        if isinstance(class_name, list):
            class_name = class_name[0] if class_name else ''
        
        # Ensure we have string values
        name = str(name)
        class_name = str(class_name)
        
        if name in unique_components:
            # Prefer components with "Component" suffix (newer format)
            existing_class = unique_components[name].get('class', '')
            if isinstance(existing_class, list):
                existing_class = existing_class[0] if existing_class else ''
            existing_class = str(existing_class)
            
            if 'Component' in class_name and 'Component' not in existing_class:
                # Update the component's name and class to ensure they're strings
                component['name'] = name
                component['class'] = class_name
                unique_components[name] = component
            elif 'Component' not in class_name and 'Component' in existing_class:
                # Keep the existing one (already has Component suffix)
                pass
            else:
                # Both have same format, keep the first one
                pass
        else:
            # Update the component's name and class to ensure they're strings
            component['name'] = name
            component['class'] = class_name
            unique_components[name] = component
    
    print(f"Unique components after deduplication: {len(unique_components)}")
    
    # Show the unique components in alphabetical order
    sorted_names = sorted(unique_components.keys(), key=str.lower)
    print("\nUnique components (alphabetical order):")
    for i, name in enumerate(sorted_names, 1):
        component = unique_components[name]
        print(f"{i:2d}. {name} ({component['class']})")

if __name__ == "__main__":
    test_deduplication()
