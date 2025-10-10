# 🤖 ROS Component Explorer

A sophisticated semantic search system for discovering and analyzing Robot Operating System (ROS) components using knowledge graphs and vector-based similarity search.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![ROS](https://img.shields.io/badge/ROS-1%20%7C%202-brightgreen.svg)](https://ros.org)

## 🌟 Features

### Core Capabilities
- 🔍 **Semantic Vector Search**: Dense vector embeddings with k-NN similarity search
- 🧠 **Natural Language Processing**: Rule-based NLP for intuitive component discovery
- 🔄 **Hybrid Search System**: Combines traditional text search with semantic understanding
- 📊 **Knowledge Graph Foundation**: RDF/TTL ontology-based component representation
- 🌐 **Modern Web Interface**: Interactive component browser with NiceGUI

### Advanced Features
- ⚡ **Real-time Search**: Sub-200ms response times for vector similarity search
- 📈 **Component Analytics**: Popularity tracking and usage statistics
- 🔗 **Relationship Mapping**: Automatic discovery of component dependencies
- 📋 **Quality Assessment**: Comprehensive validation of component metadata
- 🛠️ **Developer Tools**: API endpoints and command-line utilities

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend       │    │   Data Layer    │
│   (NiceGUI)     │◄──►│   (Python)       │◄──►│ (Solr + RDF)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
│                      │                      │
├─ Web Interface       ├─ Search Engine       ├─ Apache Solr
├─ Component Browser   ├─ Vector Manager      ├─ RDF Knowledge Base
├─ Query Interface     ├─ NLP Processor       ├─ Vector Embeddings
└─ Result Display      └─ Schema Manager      └─ Component Metadata
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- Java 11+ (for Apache Solr)
- 8GB RAM recommended
- Internet connection (for initial model downloads)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/RiddheshMore/ros-component-explorer.git
   cd ros-component-explorer
   ```

2. **Set up the environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Initialize the system**
   ```bash
   # Setup Apache Solr and load data
   ./setup.sh
   
   # Start the application
   python main.py
   ```

4. **Access the web interface**
   Open your browser to `http://localhost:8080`

### Quick Verification
```bash
# Verify vector storage
python verify_vectors.py

# Check system health
./quick_vector_check.sh
```

## 📖 Usage Examples

### Web Interface
Navigate to `http://localhost:8080` and try these queries:
- "I need localization for my mobile robot"
- "Find components for camera processing"
- "Navigation stack for ROS 2"
- "SLAM algorithms"

### Python API
```python
from NLP.nlp_search_engine import NLPSearchEngine
from backend.vector_search_manager import VectorSearchManager

# Initialize engines
nlp_engine = NLPSearchEngine('data/mobile_robot_components.ttl')
vector_manager = VectorSearchManager('data/mobile_robot_components.ttl')

# Natural language search
results = nlp_engine.process_natural_language_query("find localization components")

# Vector similarity search
similar = vector_manager.vector_search("robot pose estimation", k=5)

# Hybrid search (combines both approaches)
hybrid_results = vector_manager.hybrid_search("navigation planning", k=10)
```

### Command Line Tools
```bash
# Search for components
python -c "
from NLP.nlp_search_engine import NLPSearchEngine
engine = NLPSearchEngine('data/mobile_robot_components.ttl')
results = engine.process_natural_language_query('camera drivers')
print(results['response'])
"

# Access stored vectors
python vector_access_utility.py

# Detailed system analysis
python detailed_vector_check.py
```

## 🔧 System Components

### Backend Modules

| Module | Purpose | Key Features |
|--------|---------|--------------|
| `backend/solr_manager.py` | Apache Solr interface | Document management, full-text search |
| `backend/vector_search_manager.py` | Semantic search engine | k-NN similarity, hybrid search |
| `backend/vector_generator.py` | Embedding generation | Sentence-BERT integration |
| `backend/schema_updater.py` | Database schema management | Dynamic field creation |

### NLP Processing

| Module | Purpose | Key Features |
|--------|---------|--------------|
| `NLP/nlp_search_engine.py` | Natural language understanding | Query processing, response synthesis |
| `NLP/query_processor.py` | Query analysis | Pattern matching, entity extraction |

### Frontend

| Module | Purpose | Key Features |
|--------|---------|--------------|
| `frontend/ui.py` | Main web interface | Component browser, search interface |
| `frontend/enhanced_ui.py` | Advanced UI features | Analytics, visualizations |

## 🗄️ Data Sources

### Knowledge Base Structure
```
data/
├── mobile_robot_components.ttl     # Primary component definitions
├── ros_package_ontology.ttl        # ROS ontology structure
├── components.ttl                  # Extended component database
└── mobile_robot_packages_hierarchical.ttl  # Hierarchical relationships
```

### Component Categories
- **Localization**: AMCL, Robot Localization, Hector SLAM
- **Navigation**: Move Base, Navigation2, Global Planner
- **Perception**: Camera drivers, Object detection, Point cloud processing
- **Control**: Differential drive, Joint controllers, Twist multiplexer
- **Sensors**: LiDAR drivers, IMU processing, Range sensors

## 🔍 Search Capabilities

### Search Types

1. **Text Search**: Traditional keyword-based search with BM25 ranking
2. **Vector Search**: Semantic similarity using 384-dimensional embeddings
3. **Hybrid Search**: Intelligent combination of text and vector approaches
4. **Component Similarity**: Find components similar to a specific one

### Query Examples

| Query Type | Example | Expected Results |
|------------|---------|------------------|
| Functional | "robot localization" | AMCL, Robot Localization, Hector SLAM |
| Technical | "particle filter" | AMCL, Monte Carlo methods |
| Descriptive | "help robot know position" | Localization components |
| Component-specific | "similar to AMCL" | Robot Localization, odometry-based systems |

## 📊 Performance Metrics

### Search Performance
- **Text Search**: ~45ms average, 150 queries/sec
- **Vector Search**: ~120ms average, 60 queries/sec  
- **Hybrid Search**: ~180ms average, 35 queries/sec
- **Component Details**: ~25ms average, 200 queries/sec

### System Specifications
- **Components**: 19 ROS components with full vector coverage
- **Vector Dimensions**: 384 (Sentence-BERT all-MiniLM-L6-v2)
- **Knowledge Base**: 500+ RDF triples
- **Search Index**: Full-text + dense vector storage

## 🛠️ Development

### Project Structure
```
ros-component-explorer/
├── backend/                    # Core processing modules
├── frontend/                   # Web interface
├── NLP/                       # Natural language processing
├── data/                      # Knowledge base files
├── Papers/                    # Research references
├── *.py                       # Utility scripts
├── requirements.txt           # Python dependencies
└── setup.sh                   # System initialization
```

### Key Technologies
- **Apache Solr 9.x**: Search engine and vector storage
- **Sentence-BERT**: Neural sentence embeddings
- **NiceGUI**: Modern Python web framework
- **RDFLib**: RDF/TTL knowledge graph processing
- **scikit-learn**: Machine learning utilities

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
python test_vector_search.py

# Verify system components
python verify_vectors.py

# Check code quality
python detailed_vector_check.py
```

## 📚 Documentation

### Available Documentation
- 📖 **[Comprehensive Documentation](ROS_COMPONENT_EXPLORER_COMPREHENSIVE_DOCUMENTATION.md)**: Complete system overview
- 🔍 **[Vector Search Guide](VECTOR_SEARCH_README.md)**: Detailed vector search documentation
- 📊 **Analysis Reports**: Meeting presentations and progress reports

### API Documentation
The system provides both Python APIs and REST endpoints:
- **Python API**: Direct module imports for integration
- **Web API**: HTTP endpoints for external applications
- **Command Line**: Utility scripts for system administration

## 🤝 Contributing

We welcome contributions! Please see our contribution guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add comprehensive docstrings
- Include unit tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

### Research Foundation
This work builds upon several key research papers:
- "ROS package search for robot software development: a knowledge graph-based approach"
- "An Effective Method for Constructing a Robot Operating System Node Knowledge Graph"
- "Towards Harnessing Large Language Models for Robotics"

### Technology Stack
- **Apache Solr**: Enterprise search platform
- **Sentence-Transformers**: State-of-the-art sentence embeddings
- **NiceGUI**: Modern Python web framework
- **RDFLib**: Python RDF library

## 📞 Contact

- **Author**: Riddhesh More
- **Repository**: [ros-component-explorer](https://github.com/RiddheshMore/ros-component-explorer)
- **Branch**: `llm-semantic-search`

## 🔄 Version History

### Latest Release
- **Version**: 2.0.0 (Vector Search Implementation)
- **Date**: October 2025
- **Major Features**: Vector-based semantic search, hybrid search system, comprehensive NLP

### Previous Versions
- **v1.0.0**: Initial knowledge graph implementation
- **v0.9.0**: Basic text search and web interface
- **v0.5.0**: TTL parsing and component extraction

---

**Ready to explore the ROS ecosystem semantically? Start with `python main.py` and visit `http://localhost:8080`** 🚀