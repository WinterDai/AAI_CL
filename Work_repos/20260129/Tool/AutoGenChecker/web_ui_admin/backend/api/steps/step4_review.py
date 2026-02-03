"""
Step 4: README Review
User can Keep/AI-Edit/Manual-Edit/Reset the generated README before proceeding to code generation.

Matches CLI's _user_review_readme() in readme_generation_mixin.py with:
- [K]eep: Accept current README and proceed
- [A]I-edit: AI-assisted modification (describe changes)
- [E]dit: Manual edit in editor
- [L]oad: Reload from file
- [B]ack: Go back to Step 3
- [R]eset: Restore initial TODO template
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


# ============================================================================
# Helper Functions
# ============================================================================

def get_workspace_root() -> Path:
    """Get CHECKLIST workspace root path."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "Check_modules").exists():
            return parent
    # Fallback
    return current.parent.parent.parent.parent.parent.parent.parent / "CHECKLIST"


def save_readme_to_file(readme_content: str, module: str, item_id: str) -> str:
    """Save README to the expected location."""
    workspace = get_workspace_root()
    readme_file = workspace / "Check_modules" / module / "scripts" / "doc" / f"{item_id}_README.md"
    readme_file.parent.mkdir(parents=True, exist_ok=True)
    readme_file.write_text(readme_content, encoding='utf-8')
    print(f"[Step4] 💾 README saved to {readme_file}")
    return str(readme_file)


def load_readme_from_file(module: str, item_id: str) -> Optional[str]:
    """Load README from file."""
    workspace = get_workspace_root()
    readme_file = workspace / "Check_modules" / module / "scripts" / "doc" / f"{item_id}_README.md"
    if readme_file.exists():
        return readme_file.read_text(encoding='utf-8')
    return None


def restore_readme_backup(module: str, item_id: str) -> Optional[str]:
    """Restore README from backup (.backup file)."""
    workspace = get_workspace_root()
    backup_file = workspace / "Check_modules" / module / "scripts" / "doc" / f"{item_id}_README.md.backup"
    readme_file = workspace / "Check_modules" / module / "scripts" / "doc" / f"{item_id}_README.md"
    
    if backup_file.exists():
        content = backup_file.read_text(encoding='utf-8')
        readme_file.write_text(content, encoding='utf-8')
        print(f"[Step4] 🔄 README restored from backup")
        return content
    return None


def save_hints_to_file(module: str, item_id: str, hints: str) -> bool:
    """Save hints (AI edit request) to hints.txt."""
    if not hints or not hints.strip():
        return False
    
    workspace = get_workspace_root()
    txt_path = workspace / "Work" / "phase-1-dev" / module / "hints.txt"
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Read existing content
    existing_content = ""
    if txt_path.exists():
        existing_content = txt_path.read_text(encoding='utf-8')
    
    try:
        if not existing_content:
            new_content = f'=== {item_id} ===\n[{timestamp}]\n{hints}\n'
        elif f'=== {item_id} ===' not in existing_content:
            new_content = existing_content
            if not new_content.endswith('\n'):
                new_content += '\n'
            new_content += f'\n=== {item_id} ===\n[{timestamp}]\n{hints}\n'
        else:
            # Insert new version at end of item's section
            lines = existing_content.split('\n')
            new_lines = []
            in_item = False
            inserted = False
            
            for line in lines:
                if line.strip() == f'=== {item_id} ===':
                    in_item = True
                    new_lines.append(line)
                    continue
                
                if in_item and line.startswith('=== ') and line.endswith(' ==='):
                    if not inserted:
                        new_lines.append(f'[{timestamp}]')
                        new_lines.append(hints)
                        new_lines.append('')
                        inserted = True
                    in_item = False
                
                new_lines.append(line)
            
            if in_item and not inserted:
                new_lines.append(f'[{timestamp}]')
                new_lines.append(hints)
            
            new_content = '\n'.join(new_lines)
        
        txt_path.write_text(new_content, encoding='utf-8')
        print(f"[Step4] 💾 Hints saved to {txt_path}")
        return True
    except Exception as e:
        print(f"[Step4] ⚠️ Failed to save hints: {e}")
        return False


# ============================================================================
# Request Models
# ============================================================================

class ReadmeReviewRequest(BaseModel):
    """README review request model."""
    action: str  # 'keep', 'edit', 'ai_edit', 'reset', 'load', 'back'
    module: str = ''
    item_id: str = ''
    readme: str = ''  # Current README content
    edited_readme: str | None = None  # Edited content (if action='edit')
    ai_prompt: str | None = None  # AI modification request (if action='ai_edit')
    llm_provider: str = 'jedai'
    llm_model: str = 'claude-sonnet-4-5'


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/review-readme")
async def review_readme(request: ReadmeReviewRequest):
    """
    Handle README review actions.
    
    Matches CLI's _user_review_readme() in readme_generation_mixin.py
    
    Actions:
    - keep: Accept current README and proceed to Step 5
    - edit: Save manually edited README and proceed to Step 5
    - ai_edit: Use AI to modify README based on user's prompt
    - load: Reload README from file (if modified externally)
    - back: Go back to Step 3 (regenerate README)
    - reset: Restore initial TODO template from backup
    """
    try:
        if request.action == 'keep':
            # Save README to file before proceeding
            if request.module and request.item_id and request.readme:
                save_readme_to_file(request.readme, request.module, request.item_id)
            
            return {
                "status": "success",
                "action": "keep",
                "readme": request.readme,
                "next_step": 5,
                "message": "README accepted. Ready for code generation."
            }
        
        elif request.action == 'edit':
            if not request.edited_readme:
                raise HTTPException(
                    status_code=400,
                    detail="edited_readme is required for 'edit' action"
                )
            
            # Save edited README to file
            if request.module and request.item_id:
                save_readme_to_file(request.edited_readme, request.module, request.item_id)
            
            return {
                "status": "success",
                "action": "edit",
                "readme": request.edited_readme,
                "next_step": 5,
                "message": "README updated with your edits. Ready for code generation."
            }
        
        elif request.action == 'ai_edit':
            if not request.ai_prompt:
                raise HTTPException(
                    status_code=400,
                    detail="ai_prompt is required for 'ai_edit' action"
                )
            
            if not request.readme:
                raise HTTPException(
                    status_code=400,
                    detail="readme content is required for 'ai_edit' action"
                )
            
            # Save the AI edit request as hints
            if request.module and request.item_id:
                save_hints_to_file(request.module, request.item_id, request.ai_prompt)
            
            # Call AI to modify README
            modified_readme = await ai_modify_readme(
                current_readme=request.readme,
                user_prompt=request.ai_prompt,
                llm_provider=request.llm_provider,
                llm_model=request.llm_model
            )
            
            # Save modified README to file
            if request.module and request.item_id:
                save_readme_to_file(modified_readme, request.module, request.item_id)
            
            return {
                "status": "success",
                "action": "ai_edit",
                "readme": modified_readme,
                "next_step": None,  # Stay on Step 4 for review
                "message": "README modified by AI. Please review the changes."
            }
        
        elif request.action == 'load':
            if not request.module or not request.item_id:
                raise HTTPException(
                    status_code=400,
                    detail="module and item_id are required for 'load' action"
                )
            
            loaded_readme = load_readme_from_file(request.module, request.item_id)
            if loaded_readme:
                return {
                    "status": "success",
                    "action": "load",
                    "readme": loaded_readme,
                    "next_step": None,
                    "message": "README reloaded from file."
                }
            else:
                return {
                    "status": "warning",
                    "action": "load",
                    "readme": request.readme,
                    "next_step": None,
                    "message": "README file not found. Using current content."
                }
        
        elif request.action == 'back':
            return {
                "status": "success",
                "action": "back",
                "next_step": 3,
                "message": "Going back to Step 3 for README regeneration."
            }
        
        elif request.action == 'reset':
            if not request.module or not request.item_id:
                raise HTTPException(
                    status_code=400,
                    detail="module and item_id are required for 'reset' action"
                )
            
            restored_readme = restore_readme_backup(request.module, request.item_id)
            if restored_readme:
                return {
                    "status": "success",
                    "action": "reset",
                    "readme": restored_readme,
                    "next_step": 3,  # Go back to Step 3 after reset
                    "message": "README reset to initial template. Returning to Step 3."
                }
            else:
                return {
                    "status": "warning",
                    "action": "reset",
                    "readme": request.readme,
                    "next_step": 3,
                    "message": "No backup found. Returning to Step 3 for regeneration."
                }
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown action: {request.action}. Must be 'keep', 'edit', 'ai_edit', 'load', 'back', or 'reset'."
            )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Step4] ❌ README review failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"README review failed: {str(e)}"
        )


async def ai_modify_readme(
    current_readme: str,
    user_prompt: str,
    llm_provider: str = 'jedai',
    llm_model: str = 'claude-sonnet-4-5'
) -> str:
    """
    Use AI to modify README based on user's natural language request.
    
    Matches CLI's _ai_modify_readme() in readme_generation_mixin.py
    """
    # Import LLM client manager
    _backend_dir = Path(__file__).resolve().parent.parent.parent
    if str(_backend_dir) not in sys.path:
        sys.path.insert(0, str(_backend_dir))
    
    from llm_client_manager import llm_client_manager
    
    # Import LLM utilities
    _tool_dir = Path(__file__).resolve().parent.parent.parent.parent
    if str(_tool_dir) not in sys.path:
        sys.path.insert(0, str(_tool_dir))
    
    try:
        from utils.models import LLMCallConfig
    except ImportError:
        from AutoGenChecker.utils.models import LLMCallConfig
    
    # Build AI prompt for modification
    modification_prompt = f"""You are modifying a checker README based on user request.

====================================================================================
USER REQUEST:
====================================================================================
{user_prompt}

====================================================================================
CURRENT README:
====================================================================================
{current_readme}

====================================================================================
MODIFICATION INSTRUCTIONS:
====================================================================================
1. Read the user's request carefully
2. Locate the relevant sections in the README
3. Make ONLY the requested changes
4. Keep the overall structure and format intact
5. DO NOT change sections unrelated to the request
6. Preserve all markdown formatting
7. Return the COMPLETE modified README (not just the changed parts)

⚠️ CRITICAL RULES:
- If user asks to change descriptions: Update the "## Output Descriptions" section
- If user asks about patterns: Update pattern_items in Type 2/3 configurations
- If user asks about waivers: Update waive_items in Type 3/4 configurations
- If user asks about examples: Update the Sample Output sections
- Keep the exact same heading structure (##, ###, etc.)
- DO NOT wrap output in ```markdown``` - return raw markdown

====================================================================================
OUTPUT REQUIREMENTS:
====================================================================================
Return the COMPLETE modified README with:
- Same structure as original
- Only the requested changes applied
- All other content preserved
- Valid markdown formatting
"""

    # Get LLM client
    llm_client = llm_client_manager.get_client(
        provider=llm_provider,
        model=llm_model,
        verbose=True
    )
    
    # Call LLM
    config = LLMCallConfig(
        temperature=0.3,  # Low temp for accurate editing
        max_tokens=20000,  # Large to handle full README
    )
    
    print(f"[Step4] 🤖 AI modifying README based on: {user_prompt[:100]}...")
    response = llm_client.complete(modification_prompt, config=config)
    
    # Extract modified README
    modified_readme = response.text.strip()
    
    # Remove markdown code block if present
    if modified_readme.startswith('```markdown'):
        modified_readme = modified_readme[len('```markdown'):].strip()
    if modified_readme.startswith('```'):
        lines = modified_readme.split('\n')
        modified_readme = '\n'.join(lines[1:])
    if modified_readme.endswith('```'):
        modified_readme = modified_readme[:-3].strip()
    
    print(f"[Step4] ✅ README modified, {len(modified_readme)} chars")
    
    return modified_readme
