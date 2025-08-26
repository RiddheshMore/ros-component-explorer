#!/usr/bin/env python3
"""
Quick Start Script for ROS Component Explorer with LLM Integration

This script provides an easy way to get started with the LLM-enhanced 
ROS Component Explorer. It can run the system in different modes.
"""

import sys
import os
import argparse

def print_banner():
    """Print welcome banner."""
    print("=" * 80)
    print("🚀 ROS Component Explorer - LLM Enhanced")
    print("=" * 80)
    print("Intelligent search for ROS packages and components")
    print("Now with natural language query capabilities!")
    print()

def run_demo():
    """Run the interactive LLM demo."""
    print("🧠 Starting LLM Interactive Demo...")
    print("This will let you test natural language queries.")
    print()
    
    try:
        from LLM.demo import interactive_demo
        interactive_demo()
    except ImportError as e:
        print(f"❌ Could not import LLM demo: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install -r requirements_llm.txt")

def run_tests():
    """Run comprehensive LLM tests."""
    print("🧪 Running comprehensive LLM tests...")
    print()
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, "test_llm_comprehensive.py"], cwd=os.getcwd())
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Could not run tests: {e}")
        return False

def run_web_ui():
    """Run the web-based UI."""
    print("🌐 Starting Web UI...")
    print("This will start the traditional web interface.")
    print("Navigate to http://localhost:8080 when ready.")
    print()
    
    try:
        import subprocess
        subprocess.run([sys.executable, "main.py"], cwd=os.getcwd())
    except Exception as e:
        print(f"❌ Could not start web UI: {e}")

def check_solr():
    """Check if Solr is running."""
    try:
        import requests
        response = requests.get("http://localhost:8984/solr/admin/cores?action=STATUS", timeout=5)
        if response.status_code == 200:
            print("✅ Solr is running on localhost:8984")
            return True
        else:
            print("⚠️ Solr responded but with status:", response.status_code)
            return False
    except Exception as e:
        print("❌ Solr is not running or not accessible")
        print("Make sure Solr is started on localhost:8984")
        print("Check the README for Solr setup instructions")
        return False

def check_dependencies():
    """Check if key dependencies are available."""
    missing = []
    
    try:
        import pysolr
    except ImportError:
        missing.append("pysolr")
    
    try:
        import sentence_transformers
    except ImportError:
        missing.append("sentence-transformers")
    
    try:
        import rdflib
    except ImportError:
        missing.append("rdflib")
    
    if missing:
        print("❌ Missing dependencies:", ", ".join(missing))
        print("Install them with: pip install -r requirements_llm.txt")
        return False
    else:
        print("✅ All key dependencies are available")
        return True

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="ROS Component Explorer - LLM Enhanced",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start.py --demo          # Interactive LLM demo
  python start.py --test          # Run comprehensive tests  
  python start.py --web           # Start web interface
  python start.py --check         # Check system status
        """
    )
    
    parser.add_argument("--demo", action="store_true", 
                       help="Run interactive LLM demo")
    parser.add_argument("--test", action="store_true",
                       help="Run comprehensive LLM tests")
    parser.add_argument("--web", action="store_true",
                       help="Start web-based UI")
    parser.add_argument("--check", action="store_true",
                       help="Check system status")
    
    args = parser.parse_args()
    
    print_banner()
    
    # If no arguments, show help and run demo
    if not any(vars(args).values()):
        print("No mode specified. Running system check and then demo...")
        print()
        
        # Check system
        deps_ok = check_dependencies()
        solr_ok = check_solr()
        
        if deps_ok and solr_ok:
            print("\n🎉 System looks good! Starting interactive demo...")
            print("(Use --help to see other options)")
            print()
            run_demo()
        else:
            print("\n❌ System check failed. Please fix the issues above.")
            return 1
    
    # Handle specific modes
    if args.check:
        print("🔍 Checking system status...")
        deps_ok = check_dependencies()
        solr_ok = check_solr()
        
        if deps_ok and solr_ok:
            print("\n✅ System is ready!")
            return 0
        else:
            print("\n❌ System has issues. See messages above.")
            return 1
    
    if args.demo:
        if not check_dependencies() or not check_solr():
            print("❌ System check failed. Cannot run demo.")
            return 1
        run_demo()
    
    if args.test:
        if not check_dependencies() or not check_solr():
            print("❌ System check failed. Cannot run tests.")
            return 1
        success = run_tests()
        return 0 if success else 1
    
    if args.web:
        if not check_dependencies() or not check_solr():
            print("❌ System check failed. Cannot start web UI.")
            return 1
        run_web_ui()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
