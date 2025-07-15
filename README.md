# ROS Component Explorer - Proof of Concept

A semantic search and visualization tool for Robot Operating System (ROS) components, built as a proof-of-concept for the R&D proposal "Rich Descriptive Models for Reusable ROS Software Components."

## Project Overview

This application demonstrates how semantic descriptions of ROS components can be stored, searched, and visualized using RDF (Resource Description Framework) technology. The proof-of-concept includes:

- **Semantic Data Storage**: RDF/Turtle format for component descriptions
- **Search Interface**: Web-based UI for searching components by name, class, or description
- **Component Details**: Detailed view of component properties and relationships
- **Modular Architecture**: Separated backend (data management) and frontend (UI)
- **Blazegraph Backend**: Uses Blazegraph as a triple store for persistent, scalable RDF storage
- **Repository & Wiki Links**: Each component card and details dialog can link to the ROS package repository and ROS Wiki page


## Technology Stack

- **Backend**: Python 3.9+ with Blazegraph (via HTTP SPARQL queries)
- **Frontend**: NiceGUI for modern web-based interface
- **Data Format**: RDF/Turtle for semantic component descriptions
- **Database**: Blazegraph triple store (Dockerized)

## Project Structure

```
ros-component-explorer/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── data/
│   └── components.ttl     # RDF/Turtle file with sample component data
├── backend/
│   ├── __init__.py
│   └── db_manager.py      # Blazegraph manager for RDF operations
└── frontend/
    ├── __init__.py
    └── ui.py              # NiceGUI user interface
```

## Installation and Setup

### Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Docker (for Blazegraph)

### Installation Steps

1. **Start Blazegraph with Docker**
   ```bash
   sudo docker run -d -p 9999:8080 --name blazegraph lyrasis/blazegraph:2.1.5
   ```
   - This maps your host’s port 9999 to the container’s port 8080 (where Blazegraph listens).
   - Access Blazegraph at [http://localhost:9999/bigdata](http://localhost:9999/bigdata)

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

4. **Access the application**:
   - Open your web browser
   - Navigate to `http://localhost:8080`
   - The application will automatically open in your default browser

## Usage

### Main Interface

1. **Search Components**: Use the search bar to find components by:
   - Component name (e.g., "AMCL", "GMapping")
   - Component class (e.g., "LocalizationNode", "SensorDriver")
   - Description keywords (e.g., "laser", "navigation", "perception")

2. **View All Components**: Click "Show All" to display all available components

3. **Component Details**: Click the "Details" button on any component card to view:
   - Full component description
   - Input and output message types
   - Update rates and package information
   - Additional properties and metadata
   - **Repo** and **Wiki** links (if available)

### Sample Data

The application comes with sample data for various ROS components:

**Localization Components:**
- AMCL (Adaptive Monte Carlo Localization)
- GMapping (SLAM mapping)

**Sensor Drivers:**
- SICK Scan Driver (laser scanner)
- Velodyne Driver (3D laser)
- IMU Driver (inertial measurement unit)

**Path Planning:**
- Move Base (navigation stack)
- Global Planner
- Local Planner

**Controllers:**
- Base Controller
- Joint Controller

**Perception:**
- Object Detection
- Point Cloud Processor
- SLAM Processor

## Features Demonstrated

### Semantic Search
- Case-insensitive search across component names, classes, and descriptions
- Real-time search results as you type
- Support for partial matches and keyword search

### Component Visualization
- Card-based component display with key information
- Detailed property view in modal dialogs
- Clear presentation of component relationships
- **Repo** and **Wiki** links for each component (if available)

### RDF Data Model
- Semantic descriptions using RDF/Turtle format
- Extensible ontology for component properties
- Support for complex relationships between components

### Blazegraph Backend
- All data is stored and queried via Blazegraph (Dockerized)
- No in-memory rdflib; all queries use HTTP SPARQL

### Duplicate Result Handling
- Deduplication logic in the backend ensures that each component appears only once in the UI, even if it has multiple inputs/outputs or other properties.

## Troubleshooting

### Duplicate Results in Search
- If you see duplicate cards for the same component, ensure you are using the latest code with deduplication logic in `backend/db_manager.py`.
- The backend deduplicates by component URI, label, class, and description.

### Blazegraph Connection Issues
- Make sure Blazegraph is running and accessible at [http://localhost:9999/bigdata](http://localhost:9999/bigdata)
- If you see connection errors, check Docker logs:
  ```bash
  sudo docker logs blazegraph
  ```
- If you see a 404 at `/blazegraph`, use `/bigdata` instead.
- If you see "Not a valid (absolute) URI: kb", update the backend to remove the `context-uri` parameter when uploading Turtle data.

### Port Already in Use
- Change the port in `main.py` if 8080 is already used by another service.

### Data file not found
- Check that `data/components.ttl` exists and is readable.

## Contributing

This is a proof-of-concept implementation. For production use, consider:

- Adding comprehensive error handling
- Implementing unit tests
- Adding configuration management
- Enhancing the UI with more interactive features

## License

This project is provided as a proof-of-concept for research and development purposes. 