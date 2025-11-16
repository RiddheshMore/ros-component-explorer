# 🤖 ROS Component Explorer

A hybrid semantic search system for discovering and exploring ROS 2 packages using knowledge graphs and vector embeddings. Combines traditional BM25 text search with BERT-based semantic understanding for intelligent package discovery.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![ROS 2](https://img.shields.io/badge/ROS-2-brightgreen.svg)](https://ros.org)

## 🌟 Features

### Core Capabilities
- 🔍 **Hybrid Semantic Search**: Combines BM25 text search with k-NN vector similarity (α-weighted)
- 🧠 **Context-Aware Queries**: Natural language understanding for complex robotics queries
- � **RDF Knowledge Graph**: 90 ROS 2 packages with semantic relationships and metadata
- 🎯 **Intelligent Recommendations**: Automatic discovery of compatible packages
- 🌐 **Modern Web Interface**: Real-time search with package details and comparisons

### Search Performance
- ⚡ **Vector Search**: 17ms average latency, 76.67% success rate
- 📈 **Keyword Search**: 25ms average latency, 70% success rate  
- � **Hybrid Search**: 50ms average latency, combines best of both approaches
- 🎯 **Evaluation Dataset**: 30 context-aware queries across 5 query types

## 🏗️ Architecture

The system uses a three-layer architecture with hybrid search capabilities:

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Search     │  │ Recommenda-  │  │   Launch     │      │
│  │   Tab        │  │   tions      │  │   File Gen   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                     Backend Layer                            │
│  ┌──────────────────┐  ┌─────────────────────────────┐     │
│  │  Solr Manager    │  │  Vector Search Manager      │     │
│  │  - BM25 Search   │  │  - Sentence-BERT Encoding  │     │
│  │  - Schema Mgmt   │  │  - KNN Similarity Search   │     │
│  │  - Hybrid Fusion │  │  - α-weighted Combination  │     │
│  └──────────────────┘  └─────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                     Data Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Apache Solr  │  │  RDF/TTL     │  │   Vector     │      │
│  │  (9.x)       │  │  Knowledge   │  │  Embeddings  │      │
│  │  - Indexing  │  │  Graph       │  │  (384-dim)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

For detailed architecture documentation, see:
- [ARCHITECTURE_README.md](ARCHITECTURE_README.md) - Architecture overview
- [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - Detailed component descriptions
- [architecture_diagram.mmd](architecture_diagram.mmd) - Mermaid diagram
- [query_flow_diagram.mmd](query_flow_diagram.mmd) - Search flow visualization

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Java 11+ (for Apache Solr)
- CUDA-capable GPU (optional, for faster vector encoding)
- 8GB RAM minimum, 16GB recommended

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/RiddheshMore/ros-component-explorer.git
   cd ros-component-explorer
   ```

2. **Set up Apache Solr**
   ```bash
   # Download and start Solr 9.x
   ./setup.sh
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the application**
   ```bash
   python main.py
   ```

5. **Access the web interface**
   Open your browser to `http://localhost:8083`

### Verify Installation
The system will automatically:
- Load 90 ROS 2 packages from `data/components_clean.ttl`
- Initialize Solr schema with vector field support
- Generate 384-dimensional embeddings using Sentence-BERT
- Start the NiceGUI web interface

## 📖 Usage Examples

### Web Interface Search Queries
Navigate to `http://localhost:8083` and try these context-aware queries:

**Integration Compatibility**
- "I'm using nav2 for autonomous navigation. What localization packages are compatible?"
- "My robot uses gazebo_ros2_control. What controller plugins work with it?"

**Hardware Constrained**
- "I have a Velodyne VLP-16 LIDAR. What SLAM packages support this sensor?"
- "I'm building a robot with RPLIDAR A1. What SLAM packages work with 2D LIDAR?"

**Dependency Based**
- "I'm using robot_localization for sensor fusion. What IMU drivers provide input?"
- "My navigation stack uses tf2. What packages depend on it?"

**Feature Addition**
- "I'm using nav2_costmap for obstacles. What costmap layers improve detection?"
- "I need to smooth my navigation paths. What smoothing algorithms work with nav2?"

### Python API
```python
from backend.solr_manager import SolrManager

# Initialize
solr = SolrManager(ttl_file='data/components_clean.ttl')

# Keyword search (BM25)
results = solr.search_components("localization", max_results=10)

# Vector search (Sentence-BERT + KNN)
results = solr.vector_search("robot pose estimation", k=10)

# Hybrid search (α=0.5 combines both)
results = solr.hybrid_search("navigation planning", k=10, alpha=0.5)
```

## 🔧 System Components

### Backend Modules

| Module | Purpose | Key Technologies |
|--------|---------|------------------|
| `solr_manager.py` | Search engine interface | Apache Solr, BM25, schema management |
| `vector_search_manager.py` | Semantic search engine | Sentence-BERT, KNN, hybrid fusion |
| `vector_generator.py` | Embedding generation | all-MiniLM-L6-v2, GPU acceleration |
| `schema_updater.py` | Database schema management | Dynamic field types, vector fields |
| `ros_agent.py` | LLM-powered ROS assistant | Package recommendations, Q&A |
| `standalone_ros_agent.py` | Standalone agent interface | Independent agent operations |

### Frontend Modules

| Module | Purpose | Key Features |
|--------|---------|--------------|
| `modern_ui.py` | Main web interface | Search, recommendations, launch file generation |
| `enhanced_ui.py` | Advanced UI features | Analytics dashboard, visualizations |

### Data Files

| File | Description | Size |
|------|-------------|------|
| `components_clean.ttl` | Main knowledge graph | 90 ROS 2 packages |
| `components_final.ttl` | Extended metadata | Additional properties |
| `components.ttl` | Original ontology | Base definitions |

## 🗄️ Dataset & Evaluation

### Knowledge Base
- **90 ROS 2 Packages** from diverse categories:
  - Navigation (nav2_*, move_base)
  - SLAM (slam_toolbox, cartographer_ros)
  - Localization (robot_localization, beluga_amcl)
  - Control (ros2_control, controllers)
  - Perception (vision packages, object recognition)
  - Sensors (camera/lidar drivers, IMU packages)

### Evaluation Framework
The system is evaluated on 30 context-aware queries across 5 types:
- **Integration Compatibility** (9 queries): Finding packages that work together
- **Dependency Based** (7 queries): Identifying required dependencies
- **Hardware Constrained** (6 queries): Hardware-specific package discovery
- **Feature Addition** (6 queries): Finding complementary features
- **Replacement Alternative** (2 queries): Finding alternative packages

See `evaluation/context_aware_evaluation/` for:
- `context_aware_queries_dataset.json` - 30 curated test queries
- `run_context_aware_evaluation.py` - Evaluation script
- Results with F1@10, NDCG@10, MAP@10, Success@10, and latency metrics

## 🔍 Search Methodology

### 1. Keyword Search (BM25)
Traditional information retrieval using Apache Solr:
- Tokenization and term frequency analysis
- Field boosting (name^2.0, description^1.5, content^1.0)
- **Performance**: 25ms average, 70% success rate

### 2. Vector Search (Sentence-BERT + KNN)
Semantic understanding using dense embeddings:
- Encode query with all-MiniLM-L6-v2 (384 dimensions)
- K-Nearest Neighbor search with cosine similarity
- **Performance**: 17ms average, 76.67% success rate

### 3. Hybrid Search (α-weighted)
Combines both approaches with tunable parameter:
```python
hybrid_score = α × vector_score + (1-α) × keyword_score
```
- **α=0.5**: Balanced combination (73.33% success)
- **α=0.7**: Vector-heavy (76.67% success)
- **α=1.0**: Pure vector search (76.67% success)

### Recommendation Algorithm
Intelligent package suggestions based on:
1. **Category Similarity** (+10 points per match)
2. **Topic Compatibility** (+5 points per shared topic)
3. **Keyword Matching** (+3 points for domain keywords)
4. **Common Utilities** (+2 points for infrastructure packages)

Packages scored and ranked with compatibility tiers:
- 🟢 Highly Compatible (score > 10)
- 🔵 Compatible (score > 5)
- ⚪ Related (score > 0)

## 📊 Performance Metrics

### Search Performance (30 context-aware queries)

| Method | F1@10 | NDCG@10 | MAP@10 | Success@10 | Latency |
|--------|-------|---------|--------|------------|---------|
| **Keyword (BM25)** | 0.171 | 0.345 | 0.255 | 70.00% | 25ms |
| **Vector (BERT)** | 0.187 | 0.407 | 0.316 | **76.67%** | **17ms** |
| **Hybrid (α=0.5)** | 0.182 | 0.401 | 0.315 | 73.33% | 51ms |
| **Hybrid (α=0.7)** | 0.187 | 0.406 | 0.316 | 76.67% | 51ms |

### Key Findings
- ✅ Vector search achieves **6.7% higher success rate** than keyword
- ⚡ Vector search is **32% faster** than keyword search
- 🎯 Hybrid search provides robustness but adds latency overhead
- 📈 NDCG@10 shows vector search ranks relevant packages **18% better**

### System Specifications
- **Vector Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Knowledge Base**: 90 ROS 2 packages, 1000+ RDF triples
- **Hardware**: GPU-accelerated encoding (CUDA), 16GB RAM
- **Solr Version**: 9.x with native KNN support

## 🛠️ Development

### Project Structure
```
ros-component-explorer/
├── backend/                   # Core processing modules
│   ├── solr_manager.py       # Solr interface & hybrid search
│   ├── vector_search_manager.py  # Vector search engine
│   ├── vector_generator.py   # Sentence-BERT embeddings
│   ├── schema_updater.py     # Schema management
│   └── ros_agent.py          # LLM-powered agent
├── frontend/                  # Web interface (NiceGUI)
│   ├── modern_ui.py          # Main UI with tabs
│   └── enhanced_ui.py        # Advanced features
├── data/                      # Knowledge base
│   ├── components_clean.ttl  # Main RDF graph (90 packages)
│   └── *.ttl                 # Additional ontologies
├── evaluation/                # Evaluation framework
│   └── context_aware_evaluation/
│       ├── context_aware_queries_dataset.json
│       └── run_context_aware_evaluation.py
├── architecture_diagram.mmd   # System architecture
├── query_flow_diagram.mmd    # Search flow
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
└── setup.sh                  # Solr setup script
```

### Key Technologies
- **Apache Solr 9.x**: Search engine with native KNN support
- **Sentence-Transformers**: all-MiniLM-L6-v2 for embeddings
- **NiceGUI**: Modern Python web framework
- **RDFLib**: RDF/TTL knowledge graph processing
- **PyTorch**: Neural network backend (GPU-accelerated)

### Running Evaluation
```bash
cd evaluation/context_aware_evaluation
python run_context_aware_evaluation.py
```

This runs all 30 queries and outputs:
- Per-query metrics (precision, recall, NDCG)
- Aggregate performance statistics
- Results saved to JSON with timestamp

## 📚 Documentation

### Architecture & Design
- � [ARCHITECTURE_README.md](ARCHITECTURE_README.md) - System overview and component descriptions
- 🏗️ [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - Detailed technical architecture
- 🔄 [architecture_diagram.mmd](architecture_diagram.mmd) - Visual system diagram (Mermaid)
- � [query_flow_diagram.mmd](query_flow_diagram.mmd) - Search query flow
- 📊 [relevance_calculation_diagram.mmd](relevance_calculation_diagram.mmd) - Scoring algorithm

### Conference Presentation
- 📑 [presentation.pdf](presentation.pdf) - IROS 2024 presentation slides
- 📄 [presentation.tex](presentation.tex) - LaTeX source for presentation
- 📘 [ROS_Component_Explorer.pdf](ROS_Component_Explorer.pdf) - Project report

### Code Documentation
- Comprehensive docstrings in all modules
- Type hints for better IDE support
- Inline comments for complex algorithms

## 🤝 Contributing

Contributions are welcome! This project is particularly interested in:

### Areas for Enhancement
- 📦 **Knowledge Base Expansion**: Add more ROS 2 packages to the dataset
- 🎯 **Query Dataset**: Contribute more context-aware test queries
- 🔧 **Feature Development**: New search algorithms or UI improvements
- 📊 **Evaluation Metrics**: Additional performance measures
- 🌐 **Integration**: APIs for ROS 2 development tools

### Contribution Process
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes with clear commit messages
4. Add tests if applicable
5. Update documentation
6. Submit a pull request

### Code Standards
- Follow PEP 8 style guidelines
- Add type hints for function parameters
- Include docstrings for public methods
- Test with the evaluation dataset

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

### Research Foundation
This work builds upon research in semantic search and knowledge graphs for robotics:
- Knowledge graph-based approaches for ROS package discovery
- RDF ontologies for robot software components
- Hybrid search combining lexical and semantic methods
- Context-aware query understanding for robotics domains

### Technology Stack
- **Apache Solr**: Enterprise search platform with KNN support
- **Sentence-Transformers** (UKPLab): Pre-trained semantic embeddings
- **NiceGUI** (Zauberzeug): Modern Python web framework
- **RDFLib**: Python library for RDF processing
- **PyTorch**: Deep learning framework for embeddings

## 📞 Contact & Links

- **Repository**: [github.com/RiddheshMore/ros-component-explorer](https://github.com/RiddheshMore/ros-component-explorer)
- **Branch**: `llm-semantic-search`
- **Conference**: IROS 2024 Presentation
- **Author**: Riddhesh More

## 🔄 Version History

### Current: v2.0.0 - Hybrid Semantic Search
- ✅ Implemented vector search with Sentence-BERT
- ✅ Built hybrid search combining BM25 + KNN
- ✅ Created 30-query evaluation dataset
- ✅ Achieved 76.67% success rate with 17ms latency
- ✅ Added intelligent package recommendations
- ✅ Developed modern web UI with 3 tabs

### Previous: v1.0.0 - Knowledge Graph Foundation
- RDF/TTL ontology with 90 ROS 2 packages
- Basic keyword search with Solr
- Simple web interface
- Package metadata extraction

---

**🚀 Get Started**: `python main.py` → Open `http://localhost:8083`

**💡 Pro Tip**: Try context-aware queries like "I'm using nav2 and need localization" for best results!