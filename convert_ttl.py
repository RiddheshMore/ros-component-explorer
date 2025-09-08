#!/usr/bin/env python3
"""
Convert components.ttl from SPARQL INSERT format to proper Turtle format
"""

import os

def convert_sparql_to_turtle():
    """Convert SPARQL INSERT DATA format to pure Turtle format."""
    
    input_file = "data/components.ttl"
    output_file = "data/components_converted.ttl"
    
    print(f"Converting {input_file} to {output_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add necessary prefixes for proper Turtle format
    turtle_content = """@prefix ros: <http://example.org/ros-ontology#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

"""
    
    # Remove SPARQL wrapper
    if content.startswith("INSERT DATA {"):
        content = content[13:]  # Remove "INSERT DATA {"
    
    if content.endswith("}"):
        content = content[:-1]  # Remove closing "}"
    
    # Combine prefix declarations with content
    turtle_content += content.strip()
    
    # Write the converted content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(turtle_content)
    
    print(f"✅ Successfully converted to {output_file}")
    return output_file

if __name__ == "__main__":
    convert_sparql_to_turtle()
