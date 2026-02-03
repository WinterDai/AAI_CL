"""
Step 3: README Generation
Corresponds to CLI's readme_generation_mixin.py

This implements AI-powered README generation following the same logic
as _ai_generate_readme() in workflow/mixins/readme_generation_mixin.py

Key features matching CLI's intelligent_agent:
1. Backup existing README template before AI generation (.backup)
2. Save generated README to correct file path
3. Save user hints to hints.txt file
4. Load hints from hints.txt for resume functionality
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


# ============================================================================
# Helper Functions: Backup, Save, Hints (matches CLI workflow)
# ============================================================================

def get_workspace_root() -> Path:
    """Get CHECKLIST workspace root path."""
    # Navigate from backend/api/steps/ up to CHECKLIST_V4
    current = Path(__file__).resolve()
    # Go up: steps -> api -> backend -> web_ui -> AutoGenChecker -> Tool -> CHECKLIST_V4
    workspace = current.parent.parent.parent.parent.parent.parent.parent
    # Verify it's the correct workspace
    checklist_path = workspace / "CHECKLIST"
    if checklist_path.exists():
        return workspace / "CHECKLIST"
    # Alternative: check for Check_modules directly in parent
    for parent in current.parents:
        if (parent / "Check_modules").exists():
            return parent
    return workspace


def backup_readme_template(module: str, item_id: str) -> Optional[str]:
    """
    Backup existing README template BEFORE AI generation.
    Matches CLI's _backup_readme_template() in readme_generation_mixin.py
    
    Returns: backup file path if created, None otherwise
    """
    workspace = get_workspace_root()
    readme_file = workspace / "Check_modules" / module / "scripts" / "doc" / f"{item_id}_README.md"
    backup_file = readme_file.parent / f"{item_id}_README.md.backup"
    
    # Only backup if: (1) backup doesn't exist AND (2) source file exists
    if not backup_file.exists() and readme_file.exists():
        try:
            template_content = readme_file.read_text(encoding='utf-8')
            backup_file.write_text(template_content, encoding='utf-8')
            print(f"[Step3] 📦 Backed up TODO template: {backup_file}")
            return str(backup_file)
        except Exception as e:
            print(f"[Step3] ⚠️ Failed to backup template: {e}")
    
    return None


def save_readme_to_file(readme_content: str, module: str, item_id: str) -> str:
    """
    Save README to the expected location.
    Matches CLI's _save_readme_to_file() in readme_generation_mixin.py
    
    Returns: saved file path
    """
    workspace = get_workspace_root()
    readme_file = workspace / "Check_modules" / module / "scripts" / "doc" / f"{item_id}_README.md"
    
    # Create directory if not exists
    readme_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write README
    readme_file.write_text(readme_content, encoding='utf-8')
    print(f"[Step3] 💾 README saved to {readme_file}")
    
    return str(readme_file)


def get_hints_txt_path(module: str) -> Path:
    """Get module-level hints text file path."""
    workspace = get_workspace_root()
    return workspace / "Work" / "phase-1-dev" / module / "hints.txt"


def load_hints_from_file(module: str, item_id: str) -> Optional[Dict]:
    """
    Load hints from hints.txt file for a specific item.
    Matches CLI's load_latest_hints() in user_interaction.py
    
    Returns: Dict with 'latest', 'history', 'count' or None
    """
    import re
    
    txt_path = get_hints_txt_path(module)
    if not txt_path.exists():
        return None
    
    try:
        content = txt_path.read_text(encoding='utf-8')
        
        # Parse hints.txt format
        result = {}
        current_item = None
        current_timestamp = None
        current_lines = []
        
        for line in content.split('\n'):
            # Detect item separator: === IMP-16-0-0-01 ===
            item_match = re.match(r'^===\s*(\S+)\s*===$', line)
            if item_match:
                # Save previous content
                if current_item and current_timestamp:
                    hints = '\n'.join(current_lines).strip()
                    if hints:
                        if current_item not in result:
                            result[current_item] = []
                        result[current_item].append((current_timestamp, hints))
                
                current_item = item_match.group(1)
                current_timestamp = None
                current_lines = []
                continue
            
            # Detect timestamp: [2025-12-26 15:00:00]
            ts_match = re.match(r'^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]$', line)
            if ts_match:
                if current_item and current_timestamp:
                    hints = '\n'.join(current_lines).strip()
                    if hints:
                        if current_item not in result:
                            result[current_item] = []
                        result[current_item].append((current_timestamp, hints))
                
                current_timestamp = ts_match.group(1)
                current_lines = []
                continue
            
            if current_item and current_timestamp is not None:
                current_lines.append(line)
        
        # Save last item
        if current_item and current_timestamp:
            hints = '\n'.join(current_lines).strip()
            if hints:
                if current_item not in result:
                    result[current_item] = []
                result[current_item].append((current_timestamp, hints))
        
        # Return structured data for specific item
        if item_id in result and result[item_id]:
            versions = result[item_id]
            return {
                'latest': versions[-1][1],
                'history': versions,
                'count': len(versions)
            }
    except Exception as e:
        print(f"[Step3] ⚠️ Failed to load hints: {e}")
    
    return None


def save_hints_to_file(module: str, item_id: str, hints: str) -> bool:
    """
    Save hints to hints.txt file, appending new version.
    Matches CLI's save_hints_to_txt() in user_interaction.py
    """
    if not hints or not hints.strip():
        return False
    
    txt_path = get_hints_txt_path(module)
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Read existing content
    existing_content = ""
    if txt_path.exists():
        existing_content = txt_path.read_text(encoding='utf-8')
    
    # Check if same content already exists (avoid duplicates)
    existing_hints = load_hints_from_file(module, item_id)
    if existing_hints and existing_hints.get('latest') == hints:
        print(f"[Step3] ℹ️ Hints unchanged, skipping save")
        return True
    
    try:
        # Build new content
        if not existing_content:
            # Empty file
            new_content = f'=== {item_id} ===\n[{timestamp}]\n{hints}\n'
        elif f'=== {item_id} ===' not in existing_content:
            # New item, append to end
            new_content = existing_content
            if not new_content.endswith('\n'):
                new_content += '\n'
            new_content += f'\n=== {item_id} ===\n[{timestamp}]\n{hints}\n'
        else:
            # Existing item, insert new version at end of its section
            lines = existing_content.split('\n')
            new_lines = []
            in_item = False
            inserted = False
            
            for i, line in enumerate(lines):
                if line.strip() == f'=== {item_id} ===':
                    in_item = True
                    new_lines.append(line)
                    continue
                
                if in_item and line.startswith('=== ') and line.endswith(' ==='):
                    # End of current item section, insert before next item
                    if not inserted:
                        new_lines.append(f'[{timestamp}]')
                        new_lines.append(hints)
                        new_lines.append('')
                        inserted = True
                    in_item = False
                
                new_lines.append(line)
            
            # If item was last in file
            if in_item and not inserted:
                new_lines.append(f'[{timestamp}]')
                new_lines.append(hints)
            
            new_content = '\n'.join(new_lines)
        
        txt_path.write_text(new_content, encoding='utf-8')
        print(f"[Step3] 💾 Hints saved to {txt_path}")
        return True
    
    except Exception as e:
        print(f"[Step3] ⚠️ Failed to save hints: {e}")
        return False


# ============================================================================
# API Endpoints
# ============================================================================

class ReadmeGenerationRequest(BaseModel):
    """README generation request model."""
    module: str
    item_id: str
    item_name: str = ''
    description: str = ''
    input_files: list[str] = []
    file_analysis: list[Dict[str, Any]] = []
    llm_provider: str = 'jedai'
    llm_model: str = 'claude-sonnet-4-5'
    hints: str = ''  # User hints for README generation


class LoadHintsRequest(BaseModel):
    """Load hints request model."""
    module: str
    item_id: str


@router.post("/load-hints")
async def load_hints(request: LoadHintsRequest):
    """
    Load saved hints from hints.txt file.
    Matches CLI's load_latest_hints() in user_interaction.py
    """
    try:
        hints_data = load_hints_from_file(request.module, request.item_id)
        
        if hints_data:
            return {
                "status": "success",
                "has_hints": True,
                "latest": hints_data['latest'],
                "history": [{"timestamp": ts, "hints": h} for ts, h in hints_data['history']],
                "count": hints_data['count']
            }
        else:
            return {
                "status": "success",
                "has_hints": False,
                "latest": None,
                "history": [],
                "count": 0
            }
    except Exception as e:
        print(f"[Step3] ❌ Failed to load hints: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load hints: {str(e)}"
        )


class DeleteHintsRequest(BaseModel):
    """Delete hints request model."""
    module: str
    item_id: str
    timestamp: str  # Timestamp of the hints version to delete


@router.post("/delete-hints")
async def delete_hints(request: DeleteHintsRequest):
    """
    Delete a specific hints version from hints.txt file.
    """
    import re
    
    try:
        txt_path = get_hints_txt_path(request.module)
        if not txt_path.exists():
            return {
                "status": "success",
                "message": "No hints file exists",
                "deleted": False
            }
        
        content = txt_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        new_lines = []
        
        current_item = None
        skip_until_next = False
        target_item = request.item_id
        target_timestamp = request.timestamp
        deleted = False
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Detect item separator: === IMP-16-0-0-01 ===
            item_match = re.match(r'^===\s*(\S+)\s*===$', line)
            if item_match:
                current_item = item_match.group(1)
                skip_until_next = False
                new_lines.append(line)
                i += 1
                continue
            
            # Detect timestamp: [2025-12-26 15:00:00]
            ts_match = re.match(r'^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]$', line)
            if ts_match:
                timestamp = ts_match.group(1)
                
                # Check if this is the version to delete
                if current_item == target_item and timestamp == target_timestamp:
                    # Skip this timestamp and its content until next timestamp or item
                    skip_until_next = True
                    deleted = True
                    i += 1
                    continue
                else:
                    skip_until_next = False
                    new_lines.append(line)
                    i += 1
                    continue
            
            # If skipping, don't add this line
            if skip_until_next:
                # Check if next line is a timestamp or item separator (end of skip)
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if re.match(r'^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]$', next_line) or \
                       re.match(r'^===\s*(\S+)\s*===$', next_line):
                        skip_until_next = False
                i += 1
                continue
            
            new_lines.append(line)
            i += 1
        
        # Write back
        if deleted:
            # Clean up empty item sections
            final_content = '\n'.join(new_lines)
            # Remove empty item sections (=== ID === followed by another === or end)
            final_content = re.sub(r'===\s*\S+\s*===\n+(?====\s*\S+\s*===|$)', '', final_content)
            txt_path.write_text(final_content, encoding='utf-8')
            print(f"[Step3] 🗑️ Deleted hints version [{target_timestamp}] for {target_item}")
        
        return {
            "status": "success",
            "deleted": deleted,
            "message": f"Deleted hints version [{target_timestamp}]" if deleted else "Version not found"
        }
        
    except Exception as e:
        print(f"[Step3] ❌ Failed to delete hints: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete hints: {str(e)}"
        )


class SaveReadmeRequest(BaseModel):
    """Save README request model."""
    module: str
    item_id: str
    content: str


@router.post("/save-readme")
async def save_readme(request: SaveReadmeRequest):
    """
    Save README content to file (for manual editing).
    """
    try:
        workspace = get_workspace_root()
        readme_file = workspace / "Check_modules" / request.module / "scripts" / "doc" / f"{request.item_id}_README.md"
        
        # Create directory if not exists
        readme_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        readme_file.write_text(request.content, encoding='utf-8')
        print(f"[Step3] 💾 README saved to {readme_file}")
        
        return {
            "status": "success",
            "path": str(readme_file),
            "size": len(request.content)
        }
    except Exception as e:
        print(f"[Step3] ❌ Failed to save README: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save README: {str(e)}"
        )


@router.post("/load-readme")
async def load_readme(request: LoadHintsRequest):
    """
    Load existing README from file (for resume functionality).
    """
    try:
        workspace = get_workspace_root()
        readme_file = workspace / "Check_modules" / request.module / "scripts" / "doc" / f"{request.item_id}_README.md"
        
        if readme_file.exists():
            content = readme_file.read_text(encoding='utf-8')
            import os
            mtime = os.path.getmtime(readme_file)
            mod_time = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                "status": "success",
                "exists": True,
                "readme": content,
                "path": str(readme_file),
                "modified_time": mod_time,
                "size": len(content)
            }
        else:
            return {
                "status": "success",
                "exists": False,
                "readme": None,
                "path": str(readme_file)
            }
    except Exception as e:
        print(f"[Step3] ❌ Failed to load README: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load README: {str(e)}"
        )


@router.post("/generate-readme")
async def generate_readme(request: ReadmeGenerationRequest):
    """
    Generate comprehensive README using AI.
    
    Matches CLI's _ai_generate_readme() in readme_generation_mixin.py
    
    Key steps (matching CLI intelligent_agent):
    1. Backup existing README template (.backup)
    2. Save user hints to hints.txt
    3. Generate README with AI
    4. Save generated README to file path
    """
    try:
        # Import LLM client manager
        _backend_dir = Path(__file__).resolve().parent.parent.parent
        if str(_backend_dir) not in sys.path:
            sys.path.insert(0, str(_backend_dir))
        
        from llm_client_manager import llm_client_manager
        
        print(f"[Step3] 📝 Generating README for {request.item_id}")
        print(f"[Step3] LLM Provider: {request.llm_provider}, Model: {request.llm_model}")
        
        # Step 3.1: Backup existing README template BEFORE AI generation
        backup_path = backup_readme_template(request.module, request.item_id)
        if backup_path:
            print(f"[Step3] ✅ Backup created: {backup_path}")
        
        # Step 3.2: Save user hints to hints.txt (if provided AND different from latest)
        if request.hints and request.hints.strip():
            # Check if this is actually new content (not just loaded from history)
            existing_hints = load_hints_from_file(request.module, request.item_id)
            should_save = True
            
            if existing_hints:
                latest_hints = existing_hints.get('latest', '')
                # Don't save if hints are exactly the same as latest version
                # Also check if it's just a numbered version (1) xxx\n\n2) xxx pattern)
                if latest_hints == request.hints:
                    should_save = False
                    print(f"[Step3] ℹ️ Hints unchanged, skipping save")
            
            if should_save:
                hints_saved = save_hints_to_file(request.module, request.item_id, request.hints)
                if hints_saved:
                    print(f"[Step3] ✅ Hints saved to Work/phase-1-dev/{request.module}/hints.txt")
        
        # Import LLM utilities
        _tool_dir = Path(__file__).resolve().parent.parent.parent.parent
        if str(_tool_dir) not in sys.path:
            sys.path.insert(0, str(_tool_dir))
        
        try:
            from utils.models import LLMCallConfig
        except ImportError:
            from AutoGenChecker.utils.models import LLMCallConfig
        
        # Get or create LLM client (reuses existing instance)
        llm_client = llm_client_manager.get_client(
            provider=request.llm_provider,
            model=request.llm_model,
            verbose=True
        )
        
        print(f"[Step3] LLM client ready: {type(llm_client)}")
        
        # Build README generation prompt
        prompt = build_readme_generation_prompt(
            module=request.module,
            item_id=request.item_id,
            item_name=request.item_name,
            description=request.description,
            input_files=request.input_files,
            file_analysis=request.file_analysis,
            hints=request.hints
        )
        
        print(f"[Step3] Prompt built, length: {len(prompt)} chars")
        print(f"[Step3] 🤖 Calling LLM to generate README...")
        
        # Call LLM with appropriate config
        config = LLMCallConfig(
            model=request.llm_model,
            temperature=0.3,  # Medium temp for creativity
            max_tokens=16000  # Large for comprehensive README
        )
        
        llm_response = llm_client.complete(prompt, config=config)
        readme_content = llm_response.text
        
        print(f"[Step3] README generated, length: {len(readme_content)} chars")
        print(f"[Step3] First 200 chars: {readme_content[:200]}")
        
        # Extract README from markdown code block ONLY if LLM wrapped it
        # (be careful not to extract code blocks INSIDE the README)
        original_content = readme_content
        extracted_content = None
        
        if '```markdown' in readme_content:
            print(f"[Step3] Found ```markdown block, attempting extraction...")
            start = readme_content.find('```markdown') + len('```markdown')
            end = readme_content.find('```', start)
            if end != -1:
                extracted_content = readme_content[start:end].strip()
        elif readme_content.startswith('```'):
            # Only extract if the ENTIRE response is wrapped in a code block
            print(f"[Step3] Content starts with ```, attempting extraction...")
            start = 3
            # Skip language identifier if present
            first_newline = readme_content.find('\n', start)
            if first_newline != -1:
                start = first_newline + 1
            end = readme_content.rfind('```')
            if end > start:
                extracted_content = readme_content[start:end].strip()
        
        # Validate extraction: README should start with # (markdown heading)
        if extracted_content:
            if extracted_content.startswith('#') and len(extracted_content) > 100:
                readme_content = extracted_content
                print(f"[Step3] ✅ Extracted valid README: {len(readme_content)} chars")
            else:
                readme_content = original_content
                print(f"[Step3] ⚠️ Extraction invalid (len={len(extracted_content)}, starts={extracted_content[:20]}), using original")
        else:
            print(f"[Step3] No extraction needed, using original content")
        
        print(f"[Step3] Final README length: {len(readme_content)} chars")
        
        # Step 3.3: Save generated README to file (CRITICAL for resume)
        saved_path = save_readme_to_file(readme_content, request.module, request.item_id)
        print(f"[Step3] ✅ README saved to: {saved_path}")
        
        return {
            "readme": readme_content,
            "status": "success",
            "message": f"Generated {len(readme_content)} characters",
            "saved_path": saved_path,
            "backup_path": backup_path
        }
        
    except ImportError as e:
        print(f"[Step3] ❌ Import failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"LLM client import failed: {str(e)}"
        )
    except Exception as e:
        print(f"[Step3] ❌ README generation failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"README generation failed: {str(e)}"
        )


def build_readme_generation_prompt(
    module: str,
    item_id: str,
    item_name: str,
    description: str,
    input_files: list[str],
    file_analysis: list[Dict[str, Any]],
    hints: str = ''
) -> str:
    """
    Build prompt for README generation.
    Matches CLI's _build_readme_generation_prompt() in readme_generation_mixin.py
    """
    
    # Build file analysis summary with all 4 types
    file_info = ""
    if file_analysis:
        file_info += "\n\n" + "="*80 + "\n"
        file_info += "📁 INPUT FILE ANALYSIS (from Step 2) - ALL 4 TEMPLATE TYPES\n"
        file_info += "="*80 + "\n"
        for i, analysis in enumerate(file_analysis, 1):
            file_info += f"\nFile {i}: {analysis.get('filename', 'Unknown')}\n"
            file_info += f"Type: {analysis.get('fileType', 'Unknown')}\n"
            file_info += f"Path: {analysis.get('fullPath', 'Unknown')}\n\n"
            
            # Type 1: Boolean Check
            type1 = analysis.get('type1_boolean_check', {})
            if type1:
                file_info += "--- TYPE 1: BOOLEAN CHECK ---\n"
                file_info += f"Output Format: {type1.get('outputFormat', 'N/A')}\n"
                if type1.get('patterns'):
                    file_info += "Patterns:\n"
                    for pattern in type1['patterns']:
                        file_info += f"  - {pattern}\n"
                if type1.get('parsingStrategy'):
                    file_info += f"Parsing Strategy: {type1.get('parsingStrategy')}\n"
                file_info += "\n"
            
            # Type 2: Value Check
            type2 = analysis.get('type2_value_check', {})
            if type2:
                file_info += "--- TYPE 2: VALUE CHECK ---\n"
                file_info += f"Output Format: {type2.get('outputFormat', 'N/A')}\n"
                if type2.get('patterns'):
                    file_info += "Patterns:\n"
                    for pattern in type2['patterns']:
                        file_info += f"  - {pattern}\n"
                if type2.get('parsingStrategy'):
                    file_info += f"Parsing Strategy: {type2.get('parsingStrategy')}\n"
                file_info += "\n"
            
            # Type 3: Value Check with Waiver
            type3 = analysis.get('type3_value_with_waiver', {})
            if type3:
                file_info += "--- TYPE 3: VALUE CHECK WITH WAIVER ---\n"
                file_info += f"Output Format: {type3.get('outputFormat', 'N/A')}\n"
                if type3.get('patterns'):
                    file_info += "Patterns:\n"
                    for pattern in type3['patterns']:
                        file_info += f"  - {pattern}\n"
                if type3.get('parsingStrategy'):
                    file_info += f"Parsing Strategy: {type3.get('parsingStrategy')}\n"
                file_info += "\n"
            
            # Type 4: Boolean Check with Waiver
            type4 = analysis.get('type4_boolean_with_waiver', {})
            if type4:
                file_info += "--- TYPE 4: BOOLEAN CHECK WITH WAIVER ---\n"
                file_info += f"Output Format: {type4.get('outputFormat', 'N/A')}\n"
                if type4.get('patterns'):
                    file_info += "Patterns:\n"
                    for pattern in type4['patterns']:
                        file_info += f"  - {pattern}\n"
                if type4.get('parsingStrategy'):
                    file_info += f"Parsing Strategy: {type4.get('parsingStrategy')}\n"
                file_info += "\n"
            
            # Sample data (shared across types or from type1)
            if type1.get('sampleData'):
                sample = str(type1.get('sampleData'))
                file_info += f"Sample Data:\n{sample}\n"
            elif analysis.get('sampleData'):
                sample = str(analysis.get('sampleData'))
                file_info += f"Sample Data:\n{sample}\n"
                
            file_info += "-"*80 + "\n"
        
        file_info += "="*80 + "\n"
    
    # User hints section
    hints_section = ""
    if hints:
        hints_section = f"""

{"="*80}
💡 USER PROVIDED HINTS (CRITICAL - Follow these requirements!)
{"="*80}
{hints}

IMPORTANT: These hints contain domain-specific knowledge. Incorporate them into:
- Pattern definitions
- Check logic explanation
- Example configurations
{"="*80}
"""
    
    # Input files string
    input_files_str = ', '.join(input_files) if input_files else 'TBD'
    
    # Standard README template (matches CLI's template)
    readme_template = f'''# {item_id}: {description}

## Overview

**Check ID:** {item_id}  
**Description:** {description}  
**Category:** TODO - Add category (e.g., "Design Information Verification", "Timing Analysis")  
**Input Files:** `${{CHECKLIST_ROOT}}/IP_project_folder/reports/...`

TODO: Add functional description (2-3 sentences explaining what this checker validates and what problems it catches)

---

## Check Logic

### Input Parsing
TODO: Describe how to parse input files.

**Key Patterns (shared across all types):**
```python
# Pattern 1: [Description from file analysis above]
pattern1 = r'TODO: Select and adapt patterns from one of the 4 types above'
# Example: "TODO: Add example line from actual file"
```

### Detection Logic
TODO: Describe check logic step by step based on selected template type:
1. Read input file(s)
2. Search for patterns (use patterns from selected type)
3. Extract/validate data (follow parsing strategy from selected type)
4. Determine PASS/FAIL conditions (based on output format from selected type)

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `existence_check` | `status_check`

Choose ONE mode based on what pattern_items represents:

### Mode 1: `existence_check` - 存在性检查
**Use when:** pattern_items are items that SHOULD EXIST in input files

```
pattern_items: ["item_A", "item_B", "item_C"]
Input file contains: item_A, item_B

Result:
  found_items:   item_A, item_B    ← Pattern found in file
  missing_items: item_C            ← Pattern NOT found in file

PASS: All pattern_items found in file
FAIL: Some pattern_items not found in file
```

### Mode 2: `status_check` - 状态检查  
**Use when:** pattern_items are items to CHECK STATUS, only output matched items

```
pattern_items: ["port_A", "port_B"]
Input file contains: port_A(fixed), port_B(unfixed), port_C(unfixed)

Result:
  found_items:   port_A            ← Pattern matched AND status correct
  missing_items: port_B            ← Pattern matched BUT status wrong
  (port_C not output - not in pattern_items)

PASS: All matched items have correct status
FAIL: Some matched items have wrong status (or pattern not matched)
```

**Selected Mode for this checker:** TODO: Choose `existence_check` or `status_check`

**Rationale:** TODO: Explain why this mode is appropriate

---

## Output Descriptions (CRITICAL - Code Generator Uses These!)

This section defines the output strings used by `build_complete_output()` in the checker code.

```python
# Item description for this checker
item_desc = "{description}"

# PASS case descriptions - Split by Type semantics (API-026)
found_desc_type1_4 = "TODO: Type 1/4 - e.g., 'Block name found in implementation report'"
found_desc_type2_3 = "TODO: Type 2/3 - e.g., 'Required pattern matched (2/2)'"

# PASS reasons - Split by Type semantics
found_reason_type1_4 = "TODO: Type 1/4 - e.g., 'Block name entry found in implementation report'"
found_reason_type2_3 = "TODO: Type 2/3 - e.g., 'Required pattern matched and validated in report'"

# FAIL case descriptions
missing_desc_type1_4 = "TODO: Type 1/4 - e.g., 'Block name not found in implementation report'"
missing_desc_type2_3 = "TODO: Type 2/3 - e.g., 'Expected pattern not satisfied (1/2 missing)'"

# FAIL reasons
missing_reason_type1_4 = "TODO: Type 1/4 - e.g., 'Block name entry not found in implementation report'"
missing_reason_type2_3 = "TODO: Type 2/3 - e.g., 'Expected pattern not satisfied or missing from report'"

# WAIVED case descriptions
waived_desc = "TODO: e.g., 'Block name check waived'"
waived_base_reason = "TODO: Type 3/4 - e.g., 'Block name verification waived per design team approval'"

# UNUSED waivers
unused_desc = "TODO: e.g., 'Unused block name waiver entries'"
unused_waiver_reason = "TODO: e.g., 'Waiver not matched - no corresponding block name issue found'"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "TODO: Define format"
  Example: "TODO: Show example"

ERROR01 (Violation/Fail items):
  Format: "TODO: Define format"
  Example: "TODO: Show example"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
{item_id}:
  description: "{description}"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${{CHECKLIST_ROOT}}/IP_project_folder/reports/..."
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs custom boolean checks (file exists? config valid?).
PASS/FAIL based on checker's own validation logic.

**Sample Output (PASS):**
```
Status: PASS
Reason: [found_reason_type1_4]

Log format (item_id.log):
INFO01:
  - [item_name]

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: [item_name]. In line [N], [filepath]: [found_reason_type1_4]
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: [missing_reason_type1_4]

Log format (item_id.log):
ERROR01:
  - [item_name]

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: [item_name]. In line [N], [filepath]: [missing_reason_type1_4]
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
{item_id}:
  description: "{description}"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${{CHECKLIST_ROOT}}/IP_project_folder/reports/..."
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode
    waive_items:  # IMPORTANT: Use PLAIN STRING format
      - "Explanation: TODO: Why this check is informational only"
      - "Note: TODO: Why violations are acceptable"
```

**Sample Output (PASS with violations):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All violations waived as informational

Log format (item_id.log):
INFO01:
  - "Explanation: This check is informational only because [reason]"
  - "Note: Violations are expected in [scenario] and do not require fixes"
INFO02:
  - [item_name]

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: [waive_comment_1]. [WAIVED_INFO]
2: Info: [item_name]. In line [N], [filepath]: [missing_reason_type1_4] [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
{item_id}:
  description: "{description}"
  requirements:
    value: 2
    pattern_items:
      - "TODO: pattern1"
      - "TODO: pattern2"
  input_files:
    - "${{CHECKLIST_ROOT}}/IP_project_folder/reports/..."
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- If description contains "version": Use VERSION IDENTIFIERS ONLY (e.g., "22.11-s119_1")
- If description contains "filename"/"name": Use COMPLETE FILENAMES (e.g., "design.v")
- If description contains "status": Use STATUS VALUES (e.g., "Loaded", "Skipped")

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS/FAIL depends on check purpose:
- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)

**Sample Output (PASS):**
```
Status: PASS
Reason: [found_reason_type2_3]

Log format (item_id.log):
INFO01:
  - [item_name]

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: [item_name]. In line [N], [filepath]: [found_reason_type2_3]
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
{item_id}:
  description: "{description}"
  requirements:
    value: 0
    pattern_items:
      - "TODO: pattern1"
      - "TODO: pattern2"
  input_files:
    - "${{CHECKLIST_ROOT}}/IP_project_folder/reports/..."
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode
    waive_items:  # IMPORTANT: Use PLAIN STRING format
      - "Explanation: TODO: Why this check is informational only"
      - "Note: TODO: Why pattern mismatches are acceptable"
```

**CRITICAL Behavior (waivers.value=0):**
- NOTE: Type 2 has NO waiver logic. waive=0 is forced PASS mode only
- IMPORTANT: waive_items uses PLAIN STRINGS (NOT name/reason dict like Type 3/4!)
- waive_items serves as COMMENT ONLY (no matching/filtering logic)
- waive_items content printed as INFO with [WAIVED_INFO] tag
- ALL errors/mismatches force converted: ERROR→PASS, displayed as INFO with [WAIVED_AS_INFO] tag
- Check ALWAYS returns PASS (errors shown as INFO for tracking)
- Used when: Pattern check is informational, mismatches expected

**Sample Output (PASS with mismatches):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All mismatches waived as informational

Log format (item_id.log):
INFO01:
  - "TODO: Explain why mismatches are acceptable"
INFO02:
  - [mismatch_item]

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: [waive_comment]. [WAIVED_INFO]
2: Info: [mismatch_item]. In line [N], [filepath]: [missing_reason_type2_3] [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
{item_id}:
  description: "{description}"
  requirements:
    value: 2
    pattern_items:
      - "TODO: pattern1"
      - "TODO: pattern2"
  input_files:
    - "${{CHECKLIST_ROOT}}/IP_project_folder/reports/..."
  waivers:
    value: 2
    waive_items:
      - name: "TODO: object_name1"  # Object NAME to exempt, NOT pattern value
        reason: "Waived - TODO: reason"
      - name: "TODO: object_name2"
        reason: "Waived - TODO: reason"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:
- BOTH must be at SAME semantic level as description!
- pattern_items = VALUES to match (versions, status, conditions)
- waive_items.name = OBJECT NAMES to exempt (libraries, modules, views, files)

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Match found_items against waive_items
- Unwaived items → ERROR (need fix)
- Waived items → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all found_items (violations) are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived

Log format (item_id.log):
INFO01:
  - [waived_item_name]
WARN01:
  - [unused_waiver_name]

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: [waived_item_name]. In line [N], [filepath]: [waived_base_reason]: [specific waiver reason] [WAIVER]
Warn Occurrence: 1
1: Warn: [unused_waiver_name]. In line [N], [filepath]: [unused_waiver_reason]: [specific waiver reason] [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
{item_id}:
  description: "{description}"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${{CHECKLIST_ROOT}}/IP_project_folder/reports/..."
  waivers:
    value: 2
    waive_items:
      - name: "TODO: violation1"  # ⚠️ MUST match Type 3 waive_items
        reason: "Waived - TODO: reason"
      - name: "TODO: violation2"
        reason: "Waived - TODO: reason"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (keep exemption object names consistent)
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (no pattern_items), plus waiver classification:
- Match violations against waive_items
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output:**
```
Status: PASS
Reason: All items waived

Log format (item_id.log):
INFO01:
  - [waived_item_name]
WARN01:
  - [unused_waiver_name]

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: [waived_item_name]. In line [N], [filepath]: [waived_base_reason]: [specific waiver reason] [WAIVER]
Warn Occurrence: 1
1: Warn: [unused_waiver_name]. In line [N], [filepath]: [unused_waiver_reason]: [specific waiver reason] [WAIVER]
```
'''
    
    prompt = f"""You are filling in a README template for AutoGenChecker. DO NOT change the structure.
{hints_section}
{"="*80}
⚠️ CRITICAL: STRICT TEMPLATE COMPLIANCE REQUIRED
{"="*80}

You MUST:
1. Keep the EXACT markdown structure - same headings, same order, same format
2. Replace ONLY the "TODO:" text with actual content
3. DO NOT add new sections or remove existing sections
4. DO NOT change heading names or hierarchy
5. The "## Output Descriptions" section is MANDATORY - fill in ALL the python code strings!

{"="*80}
FILE ANALYSIS RESULTS (use this to fill TODOs):
{"="*80}
{file_info}

{"="*80}
CONFIG:
{"="*80}
Module: {module}
Item ID: {item_id}
Description: {description}
Input Files: {input_files_str}

{"="*80}
README TEMPLATE TO FILL (keep EXACT structure):
{"="*80}
{readme_template}

{"="*80}
OUTPUT REQUIREMENTS:
{"="*80}
Return the README with:
- Same structure as template (all ## headings preserved)
- All "TODO:" replaced with actual content
- "## Output Descriptions" section with filled python strings
- Real patterns and examples from file analysis
- ⚠️ CRITICAL: For Type 2/3, requirements.value MUST equal len(pattern_items)
  Example: If 2 patterns, use value: 2; if 3 patterns, use value: 3
- DO NOT wrap in ```markdown``` code block, just return raw markdown

{"="*80}
⚠️ STEP 0: Semantic Alignment Analysis (DO THIS FIRST!)
{"="*80}

Before defining pattern_items and waive_items, perform semantic alignment analysis:

**SEMANTIC LEVEL GUIDE - Common Description Patterns:**

1. **"List [X] version" / "Confirm [X] version is correct"**
   - Semantic: Extract VERSION IDENTIFIERS, not full paths or filenames
   - Example patterns: "22.11-s119_1", "v3.2", "231/23.11.000"
   - ✅ Pattern: `"22.11-s119_1"` (version only)
   - ❌ Pattern: `"innovus/221/22.11-s119_1"` (full path - too broad)

2. **"List [X] name" / "List [X] filename"**  
   - Semantic: Extract COMPLETE FILENAMES with extensions
   - Example patterns: "design.v", "CORE65GPSVT_v3.2.lib"
   - ✅ Pattern: `"CORE65GPSVT_v3.2.lib"` (complete filename)
   - ❌ Pattern: `"v3.2"` (version only - too narrow)

3. **"Confirm [X] was [not] modified" / "Check modification status"**
   - Semantic: Extract STATUS VALUES as strings
   - Example patterns: "MODIFIED", "UNMODIFIED", "YES", "NO"

4. **"Confirm no [X] exist" / "Check for [X]"**
   - Semantic: Extract COUNTS or existence status
   - Example patterns: "0", "5", "NONE", "FOUND"

🎯 KEY PRINCIPLE for Type 3/4 waivers:
- pattern_items = VALUES to match (versions, status, conditions)
- waive_items.name = OBJECT NAMES to exempt (libraries, modules, views, files)
- Example: If checking version "2.1.0", waive by library NAME "legacy_lib", NOT by version value
- NOT error descriptions like "ERROR: version not found" in waive_items.name

{"="*80}
IMPORTANT REMINDERS:
{"="*80}
1. Use REAL data from file analysis for patterns and examples
2. Show actual item names in INFO01/ERROR01 examples
3. For waivers.value=0: Show [WAIVED_AS_INFO] tag
4. For waivers.value>0: Show [WAIVER] tag
5. Make README a useful reference for developers testing ALL Type configurations!

Generate the README now:
"""
    
    return prompt
