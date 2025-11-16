"""
Vector embedding generator for ROS components.

Generates dense vector representations using pre-trained Sentence-BERT models
for semantic search capabilities. This enables similarity-based component matching
beyond traditional keyword search.
"""

import os
import logging
import numpy as np
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
import json

# Force offline mode for transformers
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorGenerator:
    """
    Generates vector embeddings for ROS component text data.
    
    Uses pre-trained Sentence-BERT models to create dense vector representations
    of component descriptions, enabling semantic similarity search and clustering.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the vector generator with a pre-trained model.
        
        Args:
            model_name: Name of the Sentence-BERT model to use
        """
        self.model_name = model_name
        logger.info(f"Loading Sentence-BERT model: {model_name} (OFFLINE MODE)")
        
        # Check if model is cached
        cache_dir = os.path.expanduser("~/.cache/torch/sentence_transformers")
        logger.info(f"Using cache directory: {cache_dir}")
        
        try:
            self.model = SentenceTransformer(model_name)
            self.vector_dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded successfully. Vector dimension: {self.vector_dimension}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            logger.error("Model may not be cached. Run setup_offline.sh to download the model.")
            raise
    
    def generate_embeddings(self, components: List[Dict]) -> List[Dict]:
        """
        Generate vector embeddings for a list of components.
        
        Args:
            components: List of component dictionaries with text data
            
        Returns:
            List of components with added vector embeddings
        """
        logger.info(f"Generating embeddings for {len(components)} components...")
        
        # Prepare text for embedding
        texts = []
        for component in components:
            # Create comprehensive text representation
            text = self._create_component_text(component)
            texts.append(text)
        
        # Generate embeddings
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        
        # Add embeddings to components
        enhanced_components = []
        for i, component in enumerate(components):
            enhanced_component = component.copy()
            enhanced_component['vector'] = embeddings[i].tolist()
            enhanced_components.append(enhanced_component)
        
        logger.info(f"Generated embeddings for {len(enhanced_components)} components")
        return enhanced_components
    
    def _create_component_text(self, component: Dict) -> str:
        """
        Create comprehensive text representation for a component.
        
        Args:
            component: Component dictionary
            
        Returns:
            Concatenated text string for embedding
        """
        text_parts = []
        
        # Add basic information
        if 'name' in component:
            text_parts.append(str(component['name']))
        
        if 'type' in component:
            text_parts.append(str(component['type']))
        
        if 'description' in component:
            text_parts.append(str(component['description']))
        
        if 'package' in component:
            text_parts.append(str(component['package']))
        
        # Add topic information
        if 'subscribed_topics' in component and component['subscribed_topics']:
            topics_text = " ".join([str(topic) for topic in component['subscribed_topics']])
            text_parts.append(f"subscribes to: {topics_text}")
        
        if 'published_topics' in component and component['published_topics']:
            topics_text = " ".join([str(topic) for topic in component['published_topics']])
            text_parts.append(f"publishes: {topics_text}")
        
        # Add technical details
        if 'ros_version' in component:
            text_parts.append(f"ROS version: {component['ros_version']}")
        
        if 'update_rate' in component:
            text_parts.append(f"update rate: {component['update_rate']}")
        
        # Join all parts with spaces
        return " ".join(text_parts)
    
    def embed(self, text: str) -> List[float]:
        """
        Generate a vector embedding for a single text string (e.g., a query).
        
        Args:
            text: Text string to embed
            
        Returns:
            Vector embedding as a list of floats
        """
        try:
            embedding = self.model.encode([text], convert_to_numpy=True)[0]
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            return None
    
    def get_vector_dimension(self) -> int:
        """Get the dimension of the generated vectors."""
        return self.vector_dimension
    
    def save_embeddings(self, components: List[Dict], filename: str):
        """
        Save components with embeddings to a JSON file.
        
        Args:
            components: List of components with embeddings
            filename: Output filename
        """
        logger.info(f"Saving embeddings to {filename}")
        
        # Convert numpy arrays to lists for JSON serialization
        serializable_components = []
        for component in components:
            serializable_component = component.copy()
            if 'vector' in serializable_component:
                serializable_component['vector'] = serializable_component['vector']
            serializable_components.append(serializable_component)
        
        with open(filename, 'w') as f:
            json.dump(serializable_components, f, indent=2)
        
        logger.info(f"Saved {len(serializable_components)} components with embeddings to {filename}")
    
    def load_embeddings(self, filename: str) -> List[Dict]:
        """
        Load components with embeddings from a JSON file.
        
        Args:
            filename: Input filename
            
        Returns:
            List of components with embeddings
        """
        logger.info(f"Loading embeddings from {filename}")
        
        with open(filename, 'r') as f:
            components = json.load(f)
        
        logger.info(f"Loaded {len(components)} components with embeddings from {filename}")
        return components 