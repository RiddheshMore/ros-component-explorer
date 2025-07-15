# ROS Component Explorer 

A semantic search and visualization tool for Robot Operating System (ROS) components, built as a proof-of-concept for the R&D proposal "Rich Descriptive Models for Reusable ROS Software Components."

## Project Overview

This application demonstrates how semantic descriptions of ROS components can be stored, searched, and visualized using RDF (Resource Description Framework) technology. The proof-of-concept includes:

- **Semantic Data Storage**: RDF/Turtle format for component descriptions
- **Search Interface**: Web-based UI for searching components by name, class, or description
- **Component Details**: Detailed view of component properties and relationships
- **Modular Architecture**: Separated backend (data management) and frontend (UI)

## Technology Stack

- **Backend**: Python 3.9+ with rdflib for RDF processing
- **Frontend**: NiceGUI for modern web-based interface
- **Data Format**: RDF/Turtle for semantic component descriptions
- **Database**: In-memory rdflib graph (simplified for PoC)

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
│   └── db_manager.py      # Database manager for RDF operations
└── frontend/
    ├── __init__.py
    └── ui.py              # NiceGUI user interface
```

## Installation and Setup

### Prerequisites

- Python 3.9 or higher
- pip (Python package installer)

### Installation Steps

1. **Clone or download the project files**

2. **Install dependencies**:
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


## Features Demonstrated

### Semantic Search
- Case-insensitive search across component names, classes, and descriptions
- Real-time search results as you type
- Support for partial matches and keyword search

### Component Visualization
- Card-based component display with key information
- Detailed property view in modal dialogs
- Clear presentation of component relationships

### RDF Data Model
- Semantic descriptions using RDF/Turtle format
- Extensible ontology for component properties
- Support for complex relationships between components

## Technical Details

### Data Model

The application uses a simple ontology for ROS components:

- **Classes**: LocalizationNode, SensorDriver, PathPlanner, Controller, PerceptionNode
- **Properties**: hasInput, hasOutput, description, updateRate, package, nodeType, etc.

### SPARQL Queries

The backend uses SPARQL queries for:
- Retrieving all components
- Searching components by text
- Getting detailed component information

### Architecture

- **Modular Design**: Separated concerns between data management and UI
- **Extensible**: Easy to add new component types and properties
- **Web-Based**: Accessible through any modern web browser

## Future Enhancements

This proof-of-concept can be extended with:

1. **Advanced Search**: Semantic similarity search, filtering by component type
2. **Component Relationships**: Visual graphs showing component dependencies
3. **Integration**: Connect to real ROS package repositories
4. **Advanced UI**: Interactive graphs, component comparison tools
5. **Persistent Storage**: Full RDF database (e.g., Blazegraph, GraphDB)

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port in `main.py` line 35
2. **Missing dependencies**: Ensure all requirements are installed
3. **Data file not found**: Check that `data/components.ttl` exists

### Logging

The application includes logging for debugging:
- Check console output for error messages
- Database operations are logged for troubleshooting

## Contributing

This is a proof-of-concept implementation. For production use, consider:

- Adding comprehensive error handling
- Implementing unit tests
- Adding configuration management
- Enhancing the UI with more interactive features

## License

This project is provided as a proof-of-concept for research and development purposes. 
