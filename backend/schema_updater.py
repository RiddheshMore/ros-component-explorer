"""
Apache Solr Schema Updater for Vector Embeddings.

Updates the Solr schema to support vector embeddings for semantic search.
Handles adding vector fields, configuring field types, and managing
schema compatibility across different Solr versions.

This enables the storage and indexing of dense vector representations
of ROS component descriptions for similarity-based search capabilities.
"""

import logging
import requests
import json
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SolrSchemaUpdater:
    """
    Updates Apache Solr schema to support vector embeddings for semantic search.
    
    Manages schema modifications including:
    - Adding vector field types for different Solr versions
    - Configuring dense vector storage and indexing
    - Handling schema compatibility and validation
    """
    
    def __init__(self, solr_url: str = "http://localhost:8984/solr/ros_explorer"):
        self.solr_url = solr_url
        self.schema_url = f"{solr_url}/schema"
    
    def add_vector_field(self, field_name: str = "vector", dimension: int = 384) -> bool:
        """
        Add a vector field to the Solr schema.
        Tries different field types based on Solr version compatibility.
        
        Args:
            field_name: Name of the vector field
            dimension: Dimension of the vectors
            
        Returns:
            True if successful, False otherwise
        """
        # Try different field types in order of preference
        field_types = [
            {
                "type": "DenseVectorField",
                "config": {
                    "name": field_name,
                    "type": "DenseVectorField",
                    "dims": dimension,
                    "stored": True,
                    "indexed": True
                }
            },
            {
                "type": "VectorField",
                "config": {
                    "name": field_name,
                    "type": "VectorField",
                    "dimension": dimension,
                    "stored": True,
                    "indexed": True
                }
            },
            {
                "type": "TextField",
                "config": {
                    "name": field_name,
                    "type": "TextField",
                    "stored": True,
                    "indexed": True,
                    "multiValued": False
                }
            }
        ]
        
        for field_type_info in field_types:
            field_type = field_type_info["type"]
            field_config = field_type_info["config"]
            
            logger.info(f"Trying to add vector field '{field_name}' with type '{field_type}' and dimension {dimension}")
            
            try:
                # Define the field configuration
                add_field_config = {
                    "add-field": field_config
                }
                
                # Send request to update schema
                response = requests.post(
                    self.schema_url,
                    json=add_field_config,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully added vector field '{field_name}' with type '{field_type}'")
                    return True
                else:
                    logger.warning(f"Failed to add field with type '{field_type}'. Status: {response.status_code}")
                    if response.status_code == 400:
                        error_response = response.json()
                        logger.warning(f"Error details: {error_response.get('error', {}).get('msg', 'Unknown error')}")
                    continue
                    
            except Exception as e:
                logger.warning(f"Error trying field type '{field_type}': {e}")
                continue
        
        logger.error(f"Failed to add vector field '{field_name}' with any supported field type")
        return False
    
    def add_vector_field_legacy(self, field_name: str = "vector", dimension: int = 384) -> bool:
        """
        Add a vector field using legacy approach (for older Solr versions).
        This creates a text field that can store vector data as space-separated values.
        
        Args:
            field_name: Name of the vector field
            dimension: Dimension of the vectors
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a text field that can store vector data
            field_config = {
                "add-field": {
                    "name": field_name,
                    "type": "text_general",
                    "stored": True,
                    "indexed": True,
                    "multiValued": True  # Allow multiple values for vector arrays
                }
            }
            
            logger.info(f"Adding legacy vector field '{field_name}' as text_general with multiValued=true")
            
            response = requests.post(
                self.schema_url,
                json=field_config,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully added legacy vector field '{field_name}'")
                return True
            else:
                logger.error(f"Failed to add legacy vector field. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding legacy vector field: {e}")
            return False
    
    def check_field_exists(self, field_name: str = "vector") -> bool:
        """
        Check if a field exists in the schema.
        
        Args:
            field_name: Name of the field to check
            
        Returns:
            True if field exists, False otherwise
        """
        try:
            response = requests.get(f"{self.schema_url}/fields/{field_name}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error checking field existence: {e}")
            return False
    
    def get_schema_info(self) -> Optional[dict]:
        """
        Get current schema information.
        
        Returns:
            Schema information dictionary or None if failed
        """
        try:
            response = requests.get(f"{self.schema_url}")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get schema. Status: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting schema: {e}")
            return None
    
    def get_solr_version(self) -> Optional[str]:
        """
        Get the Solr version information.
        
        Returns:
            Solr version string or None if failed
        """
        try:
            response = requests.get(f"{self.solr_url.replace('/schema', '')}/admin/info/system")
            if response.status_code == 200:
                info = response.json()
                version = info.get('lucene', {}).get('solr-spec-version', 'Unknown')
                logger.info(f"Solr version: {version}")
                return version
            else:
                logger.warning(f"Failed to get Solr version. Status: {response.status_code}")
                return None
        except Exception as e:
            logger.warning(f"Error getting Solr version: {e}")
            return None
    
    def list_fields(self) -> Optional[list]:
        """
        List all fields in the schema.
        
        Returns:
            List of field names or None if failed
        """
        try:
            response = requests.get(f"{self.schema_url}/fields")
            if response.status_code == 200:
                fields_data = response.json()
                field_names = [field['name'] for field in fields_data.get('fields', [])]
                return field_names
            else:
                logger.error(f"Failed to get fields. Status: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error listing fields: {e}")
            return None
    
    def list_field_types(self) -> Optional[list]:
        """
        List all available field types in the schema.
        
        Returns:
            List of field type names or None if failed
        """
        try:
            response = requests.get(f"{self.schema_url}/fieldtypes")
            if response.status_code == 200:
                fieldtypes_data = response.json()
                fieldtype_names = [ft['name'] for ft in fieldtypes_data.get('fieldTypes', [])]
                return fieldtype_names
            else:
                logger.error(f"Failed to get field types. Status: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error listing field types: {e}")
            return None
    
    def delete_field(self, field_name: str) -> bool:
        """
        Delete a field from the schema.
        
        Args:
            field_name: Name of the field to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            delete_config = {
                "delete-field": {
                    "name": field_name
                }
            }
            
            logger.info(f"Deleting field '{field_name}'")
            
            response = requests.post(
                self.schema_url,
                json=delete_config,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully deleted field '{field_name}'")
                return True
            else:
                logger.error(f"Failed to delete field. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting field: {e}")
            return False 