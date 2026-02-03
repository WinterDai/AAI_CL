"""
Start script for AutoGenChecker Web UI Backend.

This script starts the FastAPI backend server.
"""

import sys
import os
from pathlib import Path
import uvicorn

# Get directories
web_ui_dir = Path(__file__).parent
backend_dir = web_ui_dir / "backend"
autogen_root = web_ui_dir.parent  # AutoGenChecker root

# Add paths - AutoGenChecker root MUST be first for utils imports
sys.path.insert(0, str(autogen_root))
sys.path.insert(0, str(backend_dir))

def main():
    """Start the backend server."""
    print("="*80)
    print("AutoGenChecker Web UI - Backend Server")
    print("="*80)
    print()
    print("Starting FastAPI server...")
    print("API will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print()
    print("Press Ctrl+C to stop the server")
    print("="*80)
    print()
    
    # Change to backend directory so uvicorn can find app:app
    os.chdir(backend_dir)
    
    # Set PYTHONPATH for reload subprocess
    current_pythonpath = os.environ.get('PYTHONPATH', '')
    new_paths = f"{autogen_root};{backend_dir}"
    if current_pythonpath:
        os.environ['PYTHONPATH'] = f"{new_paths};{current_pythonpath}"
    else:
        os.environ['PYTHONPATH'] = new_paths
    
    print(f"PYTHONPATH: {os.environ['PYTHONPATH']}")
    
    # Start uvicorn server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        reload_dirs=[str(backend_dir)]
    )

if __name__ == "__main__":
    main()
