"""
Database manager for the ROS Component Explorer.
Handles RDF data loading and SPARQL queries for component information.
"""

import requests
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BLAZEGRAPH_URL = "http://localhost:9999/bigdata/sparql"

class BlazegraphManager:
    """Manages the Blazegraph triple store for ROS components."""
    def __init__(self, ttl_file: str):
        self.ttl_file = ttl_file
        self.endpoint = BLAZEGRAPH_URL
        self._ensure_data_loaded()

    def _ensure_data_loaded(self):
        # Check if data exists by running a simple query
        query = """
        ASK { ?s ?p ?o }
        """
        resp = requests.post(self.endpoint, data={'query': query}, headers={'Accept': 'application/sparql-results+json'})
        if resp.ok and resp.json().get('boolean'):
            logger.info("Blazegraph already has data.")
            return
        # Otherwise, upload the TTL file
        with open(self.ttl_file, 'rb') as f:
            turtle_data = f.read()
        resp = requests.post(
            self.endpoint,
            data=turtle_data,
            headers={
                'Content-Type': 'text/turtle',
                'Accept': 'application/sparql-results+json',
            }
        )
        if resp.ok:
            logger.info("Uploaded Turtle data to Blazegraph.")
        else:
            logger.error(f"Failed to upload Turtle data: {resp.text}")

    def get_all_components(self) -> List[Dict]:
        query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX comp: <http://example.org/ros-components#>
        SELECT DISTINCT ?component ?label ?class ?description
        WHERE {
            ?component a ?class .
            ?component rdfs:label ?label .
            OPTIONAL { ?component comp:description ?description }
            FILTER(?class IN (comp:LocalizationNode, comp:SensorDriver, comp:PathPlanner, comp:Controller, comp:PerceptionNode))
        }
        ORDER BY ?label
        """
        resp = requests.post(self.endpoint, data={'query': query}, headers={'Accept': 'application/sparql-results+json'})
        results = resp.json()['results']['bindings']
        components = []
        for row in results:
            components.append({
                'uri': row['component']['value'],
                'name': row['label']['value'],
                'class': row['class']['value'].split('#')[-1],
                'description': row.get('description', {}).get('value', "No description available")
            })
        return components

    def search_components(self, search_term: str) -> List[Dict]:
        if not search_term.strip():
            return self.get_all_components()
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX comp: <http://example.org/ros-components#>
        SELECT DISTINCT ?component ?label ?class ?description ?input ?output
        WHERE {{
            ?component a ?class .
            ?component rdfs:label ?label .
            OPTIONAL {{ ?component comp:description ?description }}
            OPTIONAL {{ ?component comp:hasInput ?input }}
            OPTIONAL {{ ?component comp:hasOutput ?output }}
            FILTER(?class IN (comp:LocalizationNode, comp:SensorDriver, comp:PathPlanner, comp:Controller, comp:PerceptionNode))
            FILTER(
                REGEX(?label, "{search_term}", "i") ||
                REGEX(?class, "{search_term}", "i") ||
                (BOUND(?description) && REGEX(?description, "{search_term}", "i")) ||
                (BOUND(?input) && REGEX(?input, "{search_term}", "i")) ||
                (BOUND(?output) && REGEX(?output, "{search_term}", "i"))
            )
        }}
        ORDER BY ?label
        """
        resp = requests.post(self.endpoint, data={'query': query}, headers={'Accept': 'application/sparql-results+json'})
        results = resp.json()['results']['bindings']
        components = []
        seen = set()
        for row in results:
            key = (
                row['component']['value'],
                row['label']['value'],
                row['class']['value'].split('#')[-1],
                row.get('description', {}).get('value', "No description available")
            )
            if key not in seen:
                seen.add(key)
                components.append({
                    'uri': key[0],
                    'name': key[1],
                    'class': key[2],
                    'description': key[3]
                })
        return components

    def get_component_details(self, component_uri: str) -> Optional[Dict]:
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX comp: <http://example.org/ros-components#>
        SELECT ?property ?value
        WHERE {{
            <{component_uri}> ?property ?value .
        }}
        """
        resp = requests.post(self.endpoint, data={'query': query}, headers={'Accept': 'application/sparql-results+json'})
        results = resp.json()['results']['bindings']
        details = {
            'uri': component_uri,
            'properties': {}
        }
        for row in results:
            property_uri = row['property']['value']
            value = row['value']['value']
            if '#' in property_uri:
                property_name = property_uri.split('#')[-1]
            else:
                property_name = property_uri.split('/')[-1]
            if property_name == 'type' or property_uri.endswith('rdf-syntax-ns#type'):
                details['class'] = value.split('#')[-1]
            elif property_name == 'label' or property_uri.endswith('rdfs-schema#label'):
                details['name'] = value
            else:
                details['properties'][property_name] = value
        if not details.get('name'):
            logger.warning(f"No details found for component: {component_uri}")
            return None
        return details 