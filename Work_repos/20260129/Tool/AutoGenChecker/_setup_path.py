"""
Helper script to add path setup to all modules that import from AutoGenChecker.

This makes all modules work regardless of whether they're imported as:
- `from AutoGenChecker.xxx import yyy`
- `from xxx import yyy` (when run from AutoGenChecker dir)
"""

import sys
from pathlib import Path

# Setup path for local imports
def setup_path():
    """Add AutoGenChecker parent dir to sys.path."""
    current_file = Path(__file__).resolve()
    autogenchecker_dir = current_file.parent
    tool_dir = autogenchecker_dir.parent
    
    # Add both Tool/ and Tool/AutoGenChecker/ to path
    for p in [str(tool_dir), str(autogenchecker_dir)]:
        if p not in sys.path:
            sys.path.insert(0, p)

# Call it immediately when imported
setup_path()
