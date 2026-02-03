"""
Step 8: Final Review API.

Provides T/M/O/V/R/F/Q actions for final review.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import traceback

router = APIRouter()


class ReviewActionRequest(BaseModel):
    """Request model for review actions"""
    module: str
    item_id: str
    code: str
    config: dict
    readme: str
    file_analysis: dict
    action: str  # 'T', 'M', 'O', 'V', 'R', 'F', 'Q'
    modification_request: Optional[str] = None  # For M/O actions


class ReviewActionResponse(BaseModel):
    """Response model for review actions"""
    status: str
    action: str
    result: Optional[dict] = None
    modified_code: Optional[str] = None
    message: Optional[str] = None
    next_step: Optional[int] = None
    error: Optional[str] = None


@router.post("/review-action", response_model=ReviewActionResponse)
async def review_action(request: ReviewActionRequest):
    """
    Handle final review actions.
    
    Actions:
    - T: Test Again - Re-run checker (redirect to Step 7)
    - M: Modify Code - Fix bugs or change logic with AI
    - O: Adjust Output - Change format/descriptions only
    - V: View Code - Return current code for display
    - R: Reset - Restore to skeleton template
    - F: Finalize - Mark complete & handle backups
    - Q: Quit - Save and exit
    
    Returns:
        ReviewActionResponse with action result
    """
    try:
        action = request.action.upper()
        
        if action == 'T':
            # Test Again - redirect to Step 7
            return ReviewActionResponse(
                status="success",
                action="T",
                message="Redirecting to Interactive Testing",
                next_step=7
            )
            
        elif action == 'M':
            # Modify Code with AI
            if not request.modification_request:
                return ReviewActionResponse(
                    status="error",
                    action="M",
                    error="Modification request is required"
                )
            
            modified_code = await _ai_modify_code(
                code=request.code,
                modification_request=request.modification_request,
                config=request.config,
                file_analysis=request.file_analysis,
                readme=request.readme,
                module=request.module,
                item_id=request.item_id
            )
            
            return ReviewActionResponse(
                status="success",
                action="M",
                modified_code=modified_code,
                message="Code modified successfully"
            )
            
        elif action == 'O':
            # Adjust Output format/descriptions
            if not request.modification_request:
                return ReviewActionResponse(
                    status="error",
                    action="O",
                    error="Output adjustment request is required"
                )
            
            modified_code = await _ai_adjust_output(
                code=request.code,
                adjustment_request=request.modification_request,
                readme=request.readme,
                module=request.module,
                item_id=request.item_id
            )
            
            return ReviewActionResponse(
                status="success",
                action="O",
                modified_code=modified_code,
                message="Output format adjusted successfully"
            )
            
        elif action == 'V':
            # View Code
            return ReviewActionResponse(
                status="success",
                action="V",
                result={"code": request.code, "lines": len(request.code.split('\n'))},
                message="Code retrieved"
            )
            
        elif action == 'R':
            # Reset to skeleton
            skeleton_code = await _get_skeleton_code(request.module, request.item_id)
            
            return ReviewActionResponse(
                status="success",
                action="R",
                modified_code=skeleton_code,
                message="Code reset to skeleton template"
            )
            
        elif action == 'F':
            # Finalize
            result = await _finalize_checker(
                code=request.code,
                module=request.module,
                item_id=request.item_id
            )
            
            return ReviewActionResponse(
                status="success",
                action="F",
                result=result,
                message="Checker finalized successfully",
                next_step=9
            )
            
        elif action == 'Q':
            # Quit - save and exit
            await _save_code(request.code, request.module, request.item_id)
            
            return ReviewActionResponse(
                status="success",
                action="Q",
                message="Code saved. Backups preserved.",
                next_step=9
            )
            
        else:
            return ReviewActionResponse(
                status="error",
                action=action,
                error=f"Unknown action: {action}"
            )
            
    except Exception as e:
        error_msg = f"Review action failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        traceback.print_exc()
        
        return ReviewActionResponse(
            status="error",
            action=request.action,
            error=error_msg
        )


async def _ai_modify_code(code: str, modification_request: str, config: dict, 
                          file_analysis: dict, readme: str, module: str, item_id: str) -> str:
    """Use AI to modify code based on user request."""
    try:
        from workflow.intelligent_agent import IntelligentCheckerAgent
        
        agent = IntelligentCheckerAgent(
            item_id=item_id,
            module=module,
            verbose=False,
            interactive=False
        )
        
        modified_code = agent._ai_modify_code(
            code=code,
            modification_request=modification_request,
            config=config,
            file_analysis=file_analysis,
            readme=readme
        )
        
        return modified_code
        
    except Exception as e:
        print(f"[ERROR] AI modify code failed: {e}")
        return code


async def _ai_adjust_output(code: str, adjustment_request: str, readme: str,
                           module: str, item_id: str) -> str:
    """Use AI to adjust output format/descriptions."""
    try:
        from workflow.intelligent_agent import IntelligentCheckerAgent
        
        agent = IntelligentCheckerAgent(
            item_id=item_id,
            module=module,
            verbose=False,
            interactive=False
        )
        
        modified_code = agent._ai_adjust_output(
            code=code,
            adjustment_request=adjustment_request,
            readme=readme
        )
        
        return modified_code
        
    except Exception as e:
        print(f"[ERROR] AI adjust output failed: {e}")
        return code


async def _get_skeleton_code(module: str, item_id: str) -> str:
    """Get skeleton template code."""
    try:
        from utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        backup_file = paths.workspace_root / "Check_modules" / module / "scripts" / "checker" / f"{item_id}.py.skeleton"
        
        if backup_file.exists():
            return backup_file.read_text(encoding='utf-8')
        
        return f"# Skeleton template for {item_id}\n# No backup found\n"
        
    except Exception as e:
        return f"# Error loading skeleton: {e}\n"


async def _finalize_checker(code: str, module: str, item_id: str) -> dict:
    """Finalize the checker - save and cleanup backups."""
    try:
        from utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        checker_dir = paths.workspace_root / "Check_modules" / module / "scripts" / "checker"
        code_file = checker_dir / f"{item_id}.py"
        
        # Save final code
        code_file.write_text(code, encoding='utf-8')
        
        # Remove backup files
        backup_patterns = ['.skeleton', '.bak', '.backup']
        removed_backups = []
        
        for pattern in backup_patterns:
            backup_file = checker_dir / f"{item_id}.py{pattern}"
            if backup_file.exists():
                backup_file.unlink()
                removed_backups.append(str(backup_file.name))
        
        return {
            "saved_to": str(code_file),
            "removed_backups": removed_backups,
            "status": "finalized"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }


async def _save_code(code: str, module: str, item_id: str):
    """Save code without removing backups."""
    try:
        from utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        code_file = paths.workspace_root / "Check_modules" / module / "scripts" / "checker" / f"{item_id}.py"
        code_file.write_text(code, encoding='utf-8')
        
    except Exception as e:
        print(f"[ERROR] Save code failed: {e}")
