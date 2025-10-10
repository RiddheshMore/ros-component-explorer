#!/bin/bash
# Quick Setup Script for ROS Component Explorer
# This script automates the setup process for the ROS Component Explorer

set -e  # Exit on any error

echo "🚀 ROS Component Explorer Setup Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if Java is installed
check_java() {
    echo ""
    echo "1. Checking Java installation..."
    if command -v java &> /dev/null; then
        JAVA_VERSION=$(java -version 2>&1 | head -1 | cut -d'"' -f2)
        print_status "Java $JAVA_VERSION is installed"
    else
        print_error "Java is not installed!"
        echo "Please install Java 11+ before continuing."
        echo "Ubuntu/Debian: sudo apt install openjdk-11-jdk"
        echo "macOS: brew install openjdk@11"
        exit 1
    fi
}

# Check if Python is installed
check_python() {
    echo ""
    echo "2. Checking Python installation..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_status "Python $PYTHON_VERSION is installed"
    else
        print_error "Python 3 is not installed!"
        echo "Please install Python 3.9+ before continuing."
        exit 1
    fi
}

# Download and setup Solr
setup_solr() {
    echo ""
    echo "3. Setting up Apache Solr..."
    
    SOLR_VERSION="9.4.1"
    SOLR_DIR="solr-$SOLR_VERSION"
    SOLR_ARCHIVE="$SOLR_DIR.tgz"
    
    if [ -d "$SOLR_DIR" ]; then
        print_warning "Solr directory $SOLR_DIR already exists"
        print_info "Skipping download. If you want to reinstall, remove the directory first."
    else
        print_info "Downloading Apache Solr $SOLR_VERSION..."
        wget -q "https://archive.apache.org/dist/solr/solr/$SOLR_VERSION/$SOLR_ARCHIVE" || {
            print_error "Failed to download Solr"
            echo "Please download manually from: https://solr.apache.org/downloads.html"
            exit 1
        }
        
        print_info "Extracting Solr..."
        tar -xzf "$SOLR_ARCHIVE"
        rm "$SOLR_ARCHIVE"
        print_status "Solr extracted to $SOLR_DIR"
    fi
    
    # Start Solr
    print_info "Starting Solr on port 8984..."
    cd "$SOLR_DIR"
    
    # Check if Solr is already running
    if curl -s "http://localhost:8984/solr/" > /dev/null 2>&1; then
        print_warning "Solr is already running on port 8984"
    else
        ./bin/solr start -p 8984 || {
            print_error "Failed to start Solr"
            exit 1
        }
        print_status "Solr started successfully on port 8984"
    fi
    
    # Create core
    print_info "Creating ros_explorer core..."
    ./bin/solr create_core -c ros_explorer -p 8984 || {
        print_warning "Core creation failed (may already exist)"
    }
    
    cd ..
    print_status "Solr setup complete"
}

# Setup Python environment
setup_python() {
    echo ""
    echo "4. Setting up Python environment..."
    
    # Create virtual environment
    if [ -d ".venv" ]; then
        print_warning "Virtual environment .venv already exists"
    else
        print_info "Creating virtual environment..."
        python3 -m venv .venv
        print_status "Virtual environment created"
    fi
    
    # Activate virtual environment
    print_info "Activating virtual environment..."
    source .venv/bin/activate
    
    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip > /dev/null 2>&1
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        print_info "Installing Python packages..."
        pip install -r requirements.txt > /dev/null 2>&1 || {
            print_error "Failed to install Python packages"
            echo "Try running manually: pip install -r requirements.txt"
            exit 1
        }
        print_status "Python packages installed successfully"
    else
        print_warning "requirements.txt not found"
    fi
}

# Configure Solr schema for vector search
configure_solr_schema() {
    echo ""
    echo "5. Configuring Solr schema for vector search..."
    
    # Wait a moment for Solr to be ready
    sleep 2
    
    # Add vector field type
    print_info "Adding vector field type..."
    curl -s -X POST "http://localhost:8984/solr/ros_explorer/schema" \
        -H 'Content-Type: application/json' \
        -d '{
            "add-field-type": {
                "name": "knn_vector",
                "class": "solr.DenseVectorField",
                "vectorDimension": "384",
                "similarityFunction": "cosine"
            }
        }' > /dev/null 2>&1 || print_warning "Vector field type may already exist"
    
    # Add vector field
    print_info "Adding vector field..."
    curl -s -X POST "http://localhost:8984/solr/ros_explorer/schema" \
        -H 'Content-Type: application/json' \
        -d '{
            "add-field": {
                "name": "vector",
                "type": "knn_vector",
                "stored": true,
                "indexed": true
            }
        }' > /dev/null 2>&1 || print_warning "Vector field may already exist"
    
    print_status "Solr schema configured for vector search"
}

# Test the setup
test_setup() {
    echo ""
    echo "6. Testing setup..."
    
    # Test Solr connection
    if curl -s "http://localhost:8984/solr/ros_explorer/select?q=*:*" > /dev/null 2>&1; then
        print_status "Solr connection test successful"
    else
        print_error "Solr connection test failed"
        exit 1
    fi
    
    # Test Python environment
    source .venv/bin/activate
    if python3 -c "import sentence_transformers, pysolr, rdflib, nicegui" 2>/dev/null; then
        print_status "Python environment test successful"
    else
        print_error "Python environment test failed"
        echo "Some required packages may not be installed correctly"
        exit 1
    fi
}

# Main setup function
main() {
    echo "This script will set up the ROS Component Explorer with:"
    echo "- Apache Solr 9.4.1 on port 8984"
    echo "- Python virtual environment with all dependencies"
    echo "- Solr schema configuration for vector search"
    echo ""
    read -p "Continue? [y/N]: " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    
    check_java
    check_python
    setup_solr
    setup_python
    configure_solr_schema
    test_setup
    
    echo ""
    echo "🎉 Setup Complete!"
    echo "================"
    echo ""
    print_status "Apache Solr is running on: http://localhost:8984/solr/"
    print_status "ROS Explorer core: http://localhost:8984/solr/ros_explorer/"
    print_status "Python virtual environment: .venv/"
    echo ""
    echo "Next steps:"
    echo "1. Activate the virtual environment: source .venv/bin/activate"
    echo "2. Run the application: python main.py"
    echo "3. Open your browser to: http://localhost:8080"
    echo ""
    echo "To test the LLM functionality:"
    echo "  python test_camera_query.py"
    echo ""
    echo "To run diagnostics:"
    echo "  python diagnose_solr.py"
    echo ""
    print_info "Enjoy exploring ROS components with AI-powered search! 🤖"
}

# Run main function
main "$@"
