# 🤖 ROS Component Explorer

A hybrid semantic search system for discovering and exploring ROS 2 packages using knowledge graphs and vector embeddings. Combines traditional BM25 text search with BERT-based semantic understanding for intelligent package discovery.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![ROS 2](https://img.shields.io/badge/ROS-2-brightgreen.svg)](https://ros.org)

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
   
   **Option A: Automated Setup (Recommended)**
   ```bash
   # Download and start Solr 9.x
   ./setup.sh
   ```

   **Option B: Manual Setup**
   ```bash
   # Download Apache Solr 9.x
   wget https://archive.apache.org/dist/lucene/solr/9.0.0/solr-9.0.0.tgz
   tar -xzf solr-9.0.0.tgz
   
   # Start Solr on port 8984
   cd solr-9.0.0
   bin/solr start -p 8984
   
   # Create the 'ros_packages' collection
   bin/solr create -c ros_packages -p 8984
   ```

   **To manage Solr:**
   ```bash
   # Check Solr status
   bin/solr status
   
   # Stop Solr
   bin/solr stop -p 8984
   
   # Restart Solr
   bin/solr restart -p 8984
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the application**
   ```bash
   python main.py
   ```
   
   **Note**: The application expects Solr to be running on `http://localhost:8984`. Make sure Solr is started before running the application.

5. **Access the web interface**
   Open your browser to `http://localhost:8083`

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


### Areas for Enhancement
- 📦 **Knowledge Base Expansion**: Add more ROS 2 packages to the dataset
- 🎯 **Query Dataset**: Contribute more context-aware test queries
- 🔧 **Feature Development**: New search algorithms or UI improvements
- 📊 **Evaluation Metrics**: Additional performance measures
- 🌐 **Integration**: APIs for ROS 2 development tools


**🚀 Get Started**: `python main.py` → Open `http://localhost:8083`