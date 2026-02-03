"""
Step 5: Code Generation API.

Generate complete checker code with multi-phase AI generation.
**Directly delegates to CLI's IntelligentCheckerAgent for 100% consistency.**
"""

import sys
import os
from pathlib import Path
from typing import Optional, Any, List, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import traceback
import logging

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Path Setup - MUST run before any CLI imports
# ============================================================================

def setup_cli_paths():
    """Setup Python paths for CLI module imports."""
    current_file = Path(__file__).resolve()
    
    # Path structure:
    # step5_code.py at: Tool/AutoGenChecker/web_ui/backend/api/steps/
    # parents[0] = steps/
    # parents[1] = api/
    # parents[2] = backend/
    # parents[3] = web_ui/
    # parents[4] = AutoGenChecker/
    # parents[5] = Tool/
    # parents[6] = CHECKLIST_V4/
    
    # Backend dir: web_ui/backend/
    backend_dir = current_file.parents[2]
    
    # Tool dir: Tool/AutoGenChecker/
    tool_dir = current_file.parents[4]
    
    # Project root: CHECKLIST_V4/
    project_root = current_file.parents[6]
    
    # CHECKLIST root: CHECKLIST_V4/CHECKLIST/
    checklist_root = project_root / "CHECKLIST"
    
    if not checklist_root.exists():
        # Fallback: search parents for Check_modules
        for parent in current_file.parents:
            if (parent / "Check_modules").exists():
                checklist_root = parent
                break
    
    paths_to_add = [
        str(backend_dir),
        str(tool_dir),
        str(tool_dir / "workflow"),
        str(tool_dir / "workflow" / "mixins"),
        str(tool_dir / "prompt_templates"),
        str(tool_dir / "utils"),
    ]
    
    if checklist_root and checklist_root.exists():
        paths_to_add.append(str(checklist_root / "Check_modules" / "common"))
        # Set environment variable for CLI compatibility
        os.environ["CHECKLIST_ROOT"] = str(checklist_root)
    
    for path in paths_to_add:
        if path and path not in sys.path:
            sys.path.insert(0, path)
    
    return checklist_root


def get_workspace_root() -> Path:
    """Get CHECKLIST workspace root path."""
    current = Path(__file__).resolve()
    
    # Method 1: Walk up parents looking for Check_modules
    for parent in current.parents:
        if (parent / "Check_modules").exists():
            return parent
    
    # Method 2: Use environment variable
    if os.environ.get("CHECKLIST_ROOT"):
        env_path = Path(os.environ["CHECKLIST_ROOT"])
        if env_path.exists() and (env_path / "Check_modules").exists():
            return env_path
    
    # Method 3: Known structure - parents[6] / CHECKLIST
    project_root = current.parents[6]  # CHECKLIST_V4
    checklist_dir = project_root / "CHECKLIST"
    if checklist_dir.exists() and (checklist_dir / "Check_modules").exists():
        return checklist_dir
    
    raise ValueError(f"Cannot find CHECKLIST workspace root. Searched from {current}")


# ============================================================================
# Request/Response Models
# ============================================================================

class CodeGenerationRequest(BaseModel):
    """Request model for code generation"""
    module: str
    item_id: str
    readme: str
    file_analysis: Optional[List[Dict[str, Any]]] = []
    config: Optional[Dict[str, Any]] = {}
    regenerate: bool = False
    llm_provider: str = 'jedai'
    llm_model: str = 'claude-sonnet-4'
    max_retry_attempts: int = 3  # From Settings page


class CodeGenerationResponse(BaseModel):
    """Response model for code generation"""
    status: str
    code: Optional[str] = None
    lines: int = 0
    quality_score: int = 0
    warnings: List[str] = []
    phases_log: List[str] = []
    saved_path: Optional[str] = None
    error: Optional[str] = None


class LoadCodeRequest(BaseModel):
    """Request to load existing code from file."""
    module: str
    item_id: str


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/generate-code", response_model=CodeGenerationResponse)
async def generate_code(request: CodeGenerationRequest):
    """
    Generate complete checker code using AI.
    
    **Directly uses CLI's IntelligentCheckerAgent._ai_implement_complete_code()
    for 100% consistency with CLI's 9-step workflow.**
    
    Multi-phase generation:
    - Phase 1: Header + Imports + Class + _parse_input_files()
    - Phase 2: Type 1 & Type 4 methods (boolean checks)
    - Phase 3: Type 2 & Type 3 methods (pattern checks)
    """
    phases_log = []
    
    try:
        # Setup paths for CLI imports
        setup_cli_paths()
        
        # Get workspace root - MUST not be None
        workspace_root = get_workspace_root()
        if workspace_root is None or not workspace_root.exists():
            raise ValueError(f"Cannot find CHECKLIST workspace root. Please check the directory structure.")
        
        phases_log.append(f"📋 Configuration: {request.item_id} ({request.module})")
        
        # Build config dict matching CLI format
        config = {
            'item_id': request.item_id,
            'module': request.module,
            'description': request.config.get('description', '') if request.config else '',
            'input_files': request.config.get('input_files', []) if request.config else [],
        }
        
        if not config.get('item_id') or not config.get('module'):
            raise ValueError("Invalid configuration: missing item_id or module")
        
        # Convert file_analysis list to dict format expected by CLI
        file_analysis_dict = {}
        if request.file_analysis:
            for i, analysis in enumerate(request.file_analysis):
                key = analysis.get('filename', f'file_{i}')
                file_analysis_dict[key] = analysis
        
        # Load existing skeleton
        checker_file = workspace_root / "Check_modules" / request.module / "scripts" / "checker" / f"{request.item_id}.py"
        backup_file = checker_file.parent / f"{request.item_id}.py.backup"
        existing_skeleton = ""
        skeleton_lines = 0
        
        # Handle regenerate: restore from backup
        if request.regenerate:
            if backup_file.exists():
                phases_log.append("🔄 Regenerate mode: Restoring from backup...")
                backup_content = backup_file.read_text(encoding='utf-8')
                # Restore backup to main file
                checker_file.write_text(backup_content, encoding='utf-8')
                existing_skeleton = backup_content
                skeleton_lines = len(backup_content.split('\n'))
                phases_log.append(f"    ✅ Restored {skeleton_lines} lines from backup")
                phases_log.append("    📝 Starting fresh generation from original skeleton")
            else:
                phases_log.append("    ⚠️ No backup found, proceeding with current file")
                if checker_file.exists():
                    existing_skeleton = checker_file.read_text(encoding='utf-8')
                    skeleton_lines = len(existing_skeleton.split('\n'))
        else:
            # Normal generation: load existing and create backup if needed
            if checker_file.exists():
                existing_skeleton = checker_file.read_text(encoding='utf-8')
                skeleton_lines = len(existing_skeleton.split('\n'))
                
                # Create backup if it doesn't exist
                if not backup_file.exists():
                    backup_file.write_text(existing_skeleton, encoding='utf-8')
                    phases_log.append(f"    📦 Created backup: {backup_file.name}")
        
        phases_log.append("🤖 Initializing CLI CodeGenerationMixin...")
        phases_log.append("    ⏳ Multi-phase generation (same as CLI Step 5)")
        phases_log.append("")
        
        # Import CLI's IntelligentCheckerAgent
        try:
            from workflow.intelligent_agent import IntelligentCheckerAgent
        except ImportError:
            try:
                from AutoGenChecker.workflow.intelligent_agent import IntelligentCheckerAgent
            except ImportError:
                # Fallback: use local implementation
                phases_log.append("    ⚠️ CLI agent not available, using fallback...")
                code, quality_score, warnings = generate_code_fallback(
                    config, file_analysis_dict, request.readme, 
                    existing_skeleton, request.llm_provider, request.llm_model
                )
                
                # Save and return
                checker_file.parent.mkdir(parents=True, exist_ok=True)
                checker_file.write_text(code, encoding='utf-8')
                
                return CodeGenerationResponse(
                    status="success",
                    code=code,
                    lines=len(code.split('\n')),
                    quality_score=quality_score,
                    warnings=warnings,
                    phases_log=phases_log,
                    saved_path=str(checker_file)
                )
        
        # Create agent instance (non-interactive mode for API)
        agent = IntelligentCheckerAgent(
            item_id=request.item_id,
            module=request.module,
            llm_provider=request.llm_provider,
            llm_model=request.llm_model,
            verbose=True,
            interactive=False,  # Non-interactive for API
        )
        
        # Cache the config and file_analysis (agent expects these)
        agent._cached_config = config
        agent._cached_file_analysis = file_analysis_dict
        agent._cached_readme = request.readme
        
        # Capture CLI's print output by redirecting stdout
        import io
        cli_output = io.StringIO()
        original_stdout = sys.stdout
        
        try:
            # Redirect stdout to capture CLI's print statements
            sys.stdout = cli_output
            
            # Call CLI's _ai_implement_complete_code directly
            # This is the EXACT same method used in CLI Step 5
            code = agent._ai_implement_complete_code(
                config=config,
                file_analysis=file_analysis_dict,
                readme=request.readme,
            )
        finally:
            # Always restore stdout
            sys.stdout = original_stdout
        
        # Get captured CLI output and add to phases_log
        cli_log_content = cli_output.getvalue()
        if cli_log_content:
            # Parse CLI output into log lines (filter empty and format nicely)
            for line in cli_log_content.split('\n'):
                if line.strip():  # Skip empty lines
                    phases_log.append(line)
        
        code_lines = len(code.split('\n'))
        # Note: CLI already prints summary, skip duplicate log here
        
        # Validate using CLI's method (quietly - results already in CLI output)
        is_complete, warnings = agent._validate_code_completeness_v2(
            code, existing_skeleton, code_lines
        )
        
        # Score using CLI's method
        quality_score = agent._score_generation_quality(code, skeleton_lines)
        
        # Save code to file (CLI also does this in Step 5)
        checker_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Clean up code markers
        cleaned_code = code.strip()
        if cleaned_code.startswith('```python'):
            lines = cleaned_code.split('\n')
            cleaned_code = '\n'.join(lines[1:])
        if cleaned_code.endswith('```'):
            cleaned_code = cleaned_code[:-3].strip()
        
        checker_file.write_text(cleaned_code, encoding='utf-8')
        saved_path = str(checker_file)
        
        phases_log.append("📊 [6/6] Summary")
        phases_log.append(f"    ✅ Generated {code_lines} lines of code")
        phases_log.append(f"    💾 Saved to: {saved_path}")
        
        return CodeGenerationResponse(
            status="success",
            code=cleaned_code,
            lines=code_lines,
            quality_score=quality_score,
            warnings=warnings,
            phases_log=phases_log,
            saved_path=saved_path
        )
        
    except Exception as e:
        error_msg = f"Code generation failed: {str(e)}"
        logger.error(error_msg)
        traceback.print_exc()
        
        phases_log.append(f"❌ Error: {error_msg}")
        
        return CodeGenerationResponse(
            status="error",
            error=error_msg,
            phases_log=phases_log
        )


def generate_code_fallback(
    config: Dict[str, Any],
    file_analysis: Dict[str, Any],
    readme: str,
    existing_skeleton: str,
    llm_provider: str,
    llm_model: str,
) -> tuple:
    """
    Fallback code generation when CLI agent is not available.
    Uses direct LLM calls with simplified prompts.
    """
    from llm_client_manager import llm_client_manager
    
    try:
        from utils.models import LLMCallConfig
    except ImportError:
        from AutoGenChecker.utils.models import LLMCallConfig
    
    llm_client = llm_client_manager.get_client(
        provider=llm_provider,
        model=llm_model,
        verbose=True
    )
    
    # Build comprehensive prompt
    prompt = build_fallback_prompt(config, file_analysis, readme, existing_skeleton)
    
    # Call LLM
    llm_config = LLMCallConfig(temperature=0.2, max_tokens=64000)
    response = llm_client.complete(prompt, config=llm_config)
    
    # Extract code
    code = extract_code_from_response(response.text)
    
    # Calculate quality
    quality_score = calculate_quality_score(code)
    
    # Validate
    warnings = []
    type_methods = ['_execute_type1', '_execute_type2', '_execute_type3', '_execute_type4']
    for method in type_methods:
        if f'def {method}(' not in code:
            warnings.append(f"Missing {method}() method")
    
    return code, quality_score, warnings


def build_fallback_prompt(
    config: Dict[str, Any],
    file_analysis: Dict[str, Any],
    readme: str,
    existing_skeleton: str,
) -> str:
    """Build prompt for fallback generation."""
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    mode_section = ""
    if existing_skeleton:
        mode_section = f"""⚠️ CRITICAL: MODIFY the skeleton template by filling TODO sections!

EXISTING SKELETON (YOUR TEMPLATE):
```python
{existing_skeleton}
```

YOUR TASK:
1. Keep the EXACT class structure and method signatures
2. Fill in ALL TODO sections with real implementation
3. Implement _parse_input_files() with actual parsing logic
4. Implement all 4 _execute_typeN() methods
5. Return the COMPLETE modified code"""
    else:
        mode_section = """Generate COMPLETE checker code from scratch following standard template."""
    
    return f"""Implement COMPLETE Python checker code for {config['item_id']}.

{mode_section}

Item: {config['item_id']}
Module: {config['module']}
Description: {config.get('description', 'N/A')}

File Analysis:
{file_analysis}

README Specifications (FOLLOW EXACTLY):
{readme}

⚠️ MANDATORY REQUIREMENTS:
1. Use Template Mixins: InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin
2. Implement _parse_input_files() returning {{'items': [...], 'metadata': {{}}, 'errors': []}}
3. Each item MUST have: {{'name': str, 'line_number': int, 'file_path': str}}
4. Implement ALL 4 type methods (_execute_type1 through _execute_type4)
5. ALL type methods MUST call build_complete_output()
6. Copy EXACT strings from README Output Descriptions for constants
7. Include Entry Point (main() and if __name__)
8. ⭐ MANDATORY COMMENTS: Add section header comments before EACH method/section:
   - Before _parse_input_files():
     # =========================================================================
     # Input File Parsing
     # =========================================================================
   - Before _execute_type1/2/3/4():
     # =========================================================================
     # Type N: [Description from README]
     # =========================================================================
   - Before helper methods like _matches_waiver():
     # =========================================================================
     # Helper Methods
     # =========================================================================
   - Before main():
     # =========================================================================
     # Entry Point
     # =========================================================================

⚠️ OUTPUT FORMAT:
- Return ONLY raw Python code
- Start with ################################################################################
- No markdown code blocks
"""


def extract_code_from_response(response: str) -> str:
    """Extract Python code from AI response."""
    import re
    
    code = response.strip()
    
    # Format 1: Raw code starting with file header
    if code.startswith('####'):
        return code
    
    # Format 2: Code block with python marker
    code_match = re.search(r'```python\s*(.+?)\s*```', code, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()
    
    # Format 3: Code block without language marker
    code_match = re.search(r'```\s*(.+?)\s*```', code, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()
    
    return code


def calculate_quality_score(code: str) -> int:
    """Calculate code quality score (0-100)."""
    score = 0
    
    # 25 points: Has main function
    if 'def main():' in code or 'def main(' in code:
        score += 25
    
    # 25 points: Has all 4 Type methods (6.25 each)
    type_methods = ['_execute_type1', '_execute_type2', '_execute_type3', '_execute_type4']
    for method in type_methods:
        if f'def {method}(' in code:
            score += 6.25
    
    # 20 points: Has _parse_input_files
    if 'def _parse_input_files(' in code:
        score += 20
    
    # 15 points: Line count reasonable
    lines = len(code.split('\n'))
    if 400 <= lines <= 1500:
        score += 15
    elif 200 <= lines <= 2000:
        score += 7
    
    # 15 points: No syntax errors
    try:
        import ast
        ast.parse(code)
        score += 15
    except:
        pass
    
    return int(score)


@router.post("/load-code")
async def load_code(request: LoadCodeRequest):
    """
    Load existing checker code from file (resume support).
    
    Loads from: Check_modules/{module}/scripts/checker/{item_id}.py
    """
    try:
        workspace_root = get_workspace_root()
        checker_file = workspace_root / "Check_modules" / request.module / "scripts" / "checker" / f"{request.item_id}.py"
        
        if not checker_file.exists():
            return {
                "status": "not_found",
                "exists": False,
                "message": f"No code found for {request.item_id}",
            }
        
        code = checker_file.read_text(encoding='utf-8')
        stat = checker_file.stat()
        
        from datetime import datetime
        mod_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        # Check backup
        backup_file = checker_file.parent / f"{request.item_id}.py.backup"
        has_backup = backup_file.exists()
        
        # Calculate quality score
        quality_score = calculate_quality_score(code)
        
        return {
            "status": "success",
            "exists": True,
            "code": code,
            "lines": len(code.split('\n')),
            "path": str(checker_file),
            "modified_time": mod_time,
            "has_backup": has_backup,
            "quality_score": quality_score,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "exists": False,
        }
