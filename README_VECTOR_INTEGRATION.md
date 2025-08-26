# ROS Component Explorer - Vector Integration & Hybrid Search

This document describes the advanced vector integration and hybrid search capabilities added to the ROS Component Explorer.

## Overview

The ROS Component Explorer now supports:
- **Vector Embeddings**: Using pre-trained Sentence-BERT models for semantic understanding
- **Hybrid Search**: Combining traditional text search with semantic similarity
- **Advanced Filtering**: Metadata-based filtering for refined search results
- **Performance Optimization**: Efficient vector search using Solr's KNN capabilities

## Architecture

### Phase 2: Vector Integration

#### 1. Vector Generation (`backend/vector_generator.py`)
- **Model**: Uses `all-MiniLM-L6-v2` Sentence-BERT model (384-dimensional vectors)
- **Text Processing**: Creates comprehensive text representations from component metadata
- **Embedding Generation**: Converts text to dense vector representations
- **Persistence**: Saves/loads embeddings to/from JSON files

#### 2. Schema Management (`backend/schema_updater.py`)
- **Dynamic Schema Updates**: Adds `DenseVectorField` to Solr schema
- **Field Configuration**: Configures vector field with proper dimensions
- **Validation**: Verifies field creation and existence

#### 3. Enhanced Solr Manager (`backend/solr_manager.py`)
- **Vector Support**: Stores and retrieves vector embeddings
- **Semantic Search**: Implements KNN-based similarity search
- **Hybrid Search**: Combines text and semantic search results
- **Result Ranking**: Intelligent scoring and ranking algorithms

### Phase 3: Hybrid Querying

#### 1. Search Types
- **Text Search**: Traditional keyword-based search
- **Semantic Search**: Vector similarity-based search
- **Hybrid Search**: Weighted combination of both approaches

#### 2. Query Construction
- **KNN Queries**: Uses Solr's `{!knn f=vector topK=N}` syntax
- **Filter Queries**: Applies metadata filters using `fq` parameters
- **Query Combination**: Intelligently merges different query types

#### 3. Result Combination
- **Score Normalization**: Normalizes scores from different search types
- **Weighted Ranking**: Configurable weights for semantic vs. text relevance
- **Deduplication**: Removes duplicate results across search types

## Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Solr
Ensure Solr is running on port 8984:
```bash
# Check if Solr is running
curl http://localhost:8984/solr/
```

### 3. Create Solr Core
```bash
curl "http://localhost:8984/solr/admin/cores?action=CREATE&name=ros_explorer&configSet=_default&wt=json"
```

## Usage

### 1. Basic Vector Integration Demo
```bash
python backend/vector_demo.py
```

This script demonstrates:
- Schema updates for vector support
- Embedding generation for components
- Vector indexing in Solr
- Different search capabilities
- Performance testing

### 2. Programmatic Usage

#### Generate Embeddings
```python
from backend.vector_generator import VectorGenerator

# Initialize generator
generator = VectorGenerator()

# Generate embeddings for components
components_with_vectors = generator.generate_embeddings(components)

# Save embeddings
generator.save_embeddings(components_with_vectors, "embeddings.json")
```

#### Update Solr Schema
```python
from backend.schema_updater import SolrSchemaUpdater

# Initialize updater
updater = SolrSchemaUpdater()

# Add vector field
success = updater.add_vector_field("vector", dimension=384)

# Verify field exists
exists = updater.check_field_exists("vector")
```

#### Perform Searches
```python
from backend.solr_manager import SolrManager

# Initialize manager
manager = SolrManager("data/components_clean.ttl")

# Text search
text_results = manager.search_components("localization")

# Semantic search
query_vector = [0.1, 0.2, ...]  # 384-dimensional vector
semantic_results = manager.semantic_search(query_vector, k=10)

# Hybrid search
hybrid_results = manager.hybrid_search(
    text_query="sensor",
    query_vector=query_vector,
    k=10,
    semantic_weight=0.7
)
```

### 3. Web Interface

The updated web interface provides:
- **Search Type Selection**: Choose between text, semantic, or hybrid search
- **Query Inputs**: Separate inputs for text and semantic queries
- **Advanced Options**: Configurable semantic weight and result limits
- **Filters**: ROS version and component type filtering
- **Results Display**: Tabular results with scores and actions

## Search Examples

### 1. Text Search
```
Query: "localization"
Results: Components containing "localization" in name, type, or description
```

### 2. Semantic Search
```
Query: "robot navigation and mapping"
Results: Components semantically similar to navigation and mapping concepts
```

### 3. Hybrid Search
```
Text Query: "sensor driver"
Semantic Query: "hardware interface for data acquisition"
Semantic Weight: 0.6
Results: Combined relevance from both text and semantic search
```

### 4. Filtered Search
```
Text Query: "laser"
Semantic Query: "distance measurement and scanning"
Filters: ROS 2, SensorDriverComponent
Results: Filtered results matching both queries and constraints
```

## Performance Characteristics

### Vector Generation
- **Model Loading**: ~2-3 seconds for Sentence-BERT
- **Embedding Generation**: ~0.1-0.2 seconds per component
- **Memory Usage**: ~150MB for model + embeddings

### Search Performance
- **Text Search**: ~0.01-0.05 seconds
- **Semantic Search**: ~0.05-0.1 seconds
- **Hybrid Search**: ~0.1-0.15 seconds

### Scalability
- **Vector Storage**: Linear growth with component count
- **Search Time**: Logarithmic growth with Solr's indexing
- **Memory**: Constant overhead per component

## Configuration

### Vector Model
```python
# Change model in VectorGenerator
generator = VectorGenerator("all-mpnet-base-v2")  # 768-dimensional
generator = VectorGenerator("all-MiniLM-L12-v2")  # 384-dimensional
```

### Semantic Weight
```python
# Adjust semantic vs. text weight in hybrid search
results = manager.hybrid_search(
    text_query="query",
    query_vector=vector,
    semantic_weight=0.8  # Higher semantic relevance
)
```

### Solr Configuration
```python
# Customize Solr connection
updater = SolrSchemaUpdater("http://localhost:8983/solr/custom_core")
manager = SolrManager("data.ttl", solr_url="http://localhost:8983/solr/custom_core")
```

## Troubleshooting

### Common Issues

#### 1. Solr Connection Errors
```bash
# Check Solr status
curl http://localhost:8984/solr/admin/cores?action=STATUS&wt=json

# Verify core exists
curl http://localhost:8984/solr/ros_explorer/select?q=*:*&rows=0&wt=json
```

#### 2. Vector Field Issues
```python
# Check if vector field exists
updater = SolrSchemaUpdater()
exists = updater.check_field_exists("vector")

# List all fields
fields = updater.list_fields()
print(fields)
```

#### 3. Memory Issues
```python
# Reduce batch size for large datasets
components_with_vectors = generator.generate_embeddings(components[:100])  # Process in batches
```

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with verbose logging
demo = VectorIntegrationDemo()
demo.run_complete_demo()
```

## Future Enhancements

### Planned Features
- **Multi-modal Search**: Support for code, documentation, and metadata
- **Real-time Updates**: Live vector updates for new components
- **Advanced Filtering**: Complex boolean and range filters
- **Result Clustering**: Group similar components automatically
- **Performance Monitoring**: Real-time search performance metrics

### Integration Opportunities
- **ROS Index**: Sync with official ROS component database
- **GitHub Integration**: Extract component information from repositories
- **Documentation Search**: Include README and documentation content
- **Community Feedback**: User ratings and usage statistics

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request

### Testing
```bash
# Run vector integration tests
python -m pytest tests/test_vector_integration.py

# Run performance benchmarks
python backend/vector_demo.py --benchmark
```

### Code Style
- Follow PEP 8 guidelines
- Include type hints
- Add comprehensive docstrings
- Write unit tests for new features

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **Sentence-BERT**: For providing pre-trained semantic models
- **Apache Solr**: For robust search and vector capabilities
- **ROS Community**: For component definitions and use cases
- **Open Source Contributors**: For feedback and improvements 