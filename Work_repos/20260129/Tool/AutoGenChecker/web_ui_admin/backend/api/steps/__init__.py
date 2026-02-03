"""
Step-by-step API modules for web UI.
Each step corresponds to CLI's workflow mixins.
"""

# Setup path BEFORE importing modules that need AutoGenChecker utils
import sys
from pathlib import Path

# Add AutoGenChecker root to path for utils imports
# Path: __init__.py -> steps/ -> api/ -> backend/ -> web_ui/ -> AutoGenChecker/
_autogen_root = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_autogen_root) not in sys.path:
    sys.path.insert(0, str(_autogen_root))

from .step1_config import router as step1_router
from .step2_file_analysis import router as step2_router
from .step3_readme import router as step3_router
from .step4_review import router as step4_router
from .step5_code import router as step5_router
from .step6_selfcheck import router as step6_router
from .step7_testing import router as step7_router
from .step8_final_review import router as step8_router
from .step9_package import router as step9_router

__all__ = [
    'step1_router', 'step2_router', 'step3_router', 
    'step4_router', 'step5_router', 'step6_router',
    'step7_router', 'step8_router', 'step9_router'
]
