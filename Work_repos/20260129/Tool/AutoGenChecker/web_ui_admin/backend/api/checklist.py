"""CHECKLIST directory scanning and management API."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import yaml
import glob

router = APIRouter()

# Get CHECKLIST root directory
CHECKLIST_ROOT = Path(os.environ.get(
    "CHECKLIST_ROOT",
    Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "CHECKLIST"
))

CHECK_MODULES_DIR = CHECKLIST_ROOT / "Check_modules"


class ModuleInfo(BaseModel):
    """Module information model."""
    module_id: str
    module_name: str
    item_count: int
    items: List[str]


class ItemDetail(BaseModel):
    """Item detail model."""
    item_id: str
    module: str
    description: str
    requirements: Dict[str, Any]
    input_files: List[str]
    waivers: Dict[str, Any]
    yaml_path: str


class YamlUpdateRequest(BaseModel):
    """YAML update request model."""
    yaml_content: str


class FileStatsRequest(BaseModel):
    """File statistics request model."""
    file_path: str


class FileAnalysisRequest(BaseModel):
    """File analysis request model."""
    file_path: str
    file_type: str
    llm_provider: str = 'jedai'
    llm_model: str = 'claude-sonnet-4-5'


def expand_checklist_root(text: str) -> str:
    """Expand ${CHECKLIST_ROOT} variable in text."""
    if not text:
        return text
    return text.replace("${CHECKLIST_ROOT}", str(CHECKLIST_ROOT))


def expand_file_patterns(patterns: List[str]) -> List[str]:
    """Expand glob patterns and ${CHECKLIST_ROOT} in file paths."""
    expanded_files = []
    for pattern in patterns:
        # Expand CHECKLIST_ROOT variable
        expanded_pattern = expand_checklist_root(pattern)
        
        # Glob expansion
        matched_files = glob.glob(expanded_pattern, recursive=True)
        if matched_files:
            expanded_files.extend(matched_files)
        else:
            # Keep original if no match (might be a reference file)
            expanded_files.append(expanded_pattern)
    
    return expanded_files


@router.get("/modules", response_model=List[ModuleInfo])
async def list_modules():
    """List all available checker modules."""
    if not CHECK_MODULES_DIR.exists():
        raise HTTPException(status_code=404, detail=f"Check_modules directory not found: {CHECK_MODULES_DIR}")
    
    modules = []
    
    for module_dir in sorted(CHECK_MODULES_DIR.iterdir()):
        if not module_dir.is_dir() or module_dir.name == "common":
            continue
        
        # Find all YAML files in inputs/items/
        items_dir = module_dir / "inputs" / "items"
        items = []
        
        if items_dir.exists():
            yaml_files = list(items_dir.glob("*.yaml")) + list(items_dir.glob("*.yml"))
            items = [f.stem for f in yaml_files]
        
        modules.append(ModuleInfo(
            module_id=module_dir.name,
            module_name=module_dir.name.replace("_", " ").title(),
            item_count=len(items),
            items=items
        ))
    
    return modules


@router.get("/modules/{module_id}/items/{item_id}", response_model=ItemDetail)
async def get_item_detail(module_id: str, item_id: str):
    """Get detailed information for a specific item."""
    module_dir = CHECK_MODULES_DIR / module_id
    
    if not module_dir.exists():
        raise HTTPException(status_code=404, detail=f"Module not found: {module_id}")
    
    # Try to find YAML file
    items_dir = module_dir / "inputs" / "items"
    yaml_path = items_dir / f"{item_id}.yaml"
    
    if not yaml_path.exists():
        yaml_path = items_dir / f"{item_id}.yml"
    
    if not yaml_path.exists():
        raise HTTPException(status_code=404, detail=f"Item YAML not found: {item_id}")
    
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)
        
        # Extract data with defaults
        description = yaml_data.get("description", "No description")
        requirements = yaml_data.get("requirements", {"value": "N/A", "pattern_items": []})
        input_files = yaml_data.get("input_files", [])
        waivers = yaml_data.get("waivers", {"value": "N/A", "waive_items": []})
        
        # Expand input file patterns
        expanded_input_files = expand_file_patterns(input_files)
        
        return ItemDetail(
            item_id=item_id,
            module=module_id,
            description=description,
            requirements=requirements,
            input_files=expanded_input_files,
            waivers=waivers,
            yaml_path=str(yaml_path)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading YAML: {str(e)}")


@router.put("/modules/{module_id}/items/{item_id}")
async def update_item_yaml(module_id: str, item_id: str, request: YamlUpdateRequest):
    """Update YAML file content for a specific item."""
    module_dir = CHECK_MODULES_DIR / module_id
    
    if not module_dir.exists():
        raise HTTPException(status_code=404, detail=f"Module not found: {module_id}")
    
    # Find YAML file
    items_dir = module_dir / "inputs" / "items"
    yaml_path = items_dir / f"{item_id}.yaml"
    
    if not yaml_path.exists():
        yaml_path = items_dir / f"{item_id}.yml"
    
    if not yaml_path.exists():
        raise HTTPException(status_code=404, detail=f"Item YAML not found: {item_id}")
    
    try:
        # Parse the YAML content to validate it
        yaml_data = yaml.safe_load(request.yaml_content)
        
        # Write back to file
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(request.yaml_content)
        
        return {
            "status": "success",
            "message": f"YAML file updated: {yaml_path}",
            "item_id": item_id,
            "module": module_id
        }
    
    except yaml.YAMLError as e:
        error_msg = str(e)
        # Provide helpful hints for common errors
        if "mapping values are not allowed" in error_msg:
            error_msg += "\n\n💡 提示：description字段中包含冒号(:)时需要加引号\n例如：description: \"Block name (e.g: cdn_hs_phy_data_slice)\""
        raise HTTPException(status_code=400, detail=f"YAML格式错误: {error_msg}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving YAML: {str(e)}")


@router.get("/checklist-root")
async def get_checklist_root():
    """Get CHECKLIST root directory path."""
    return {
        "checklist_root": str(CHECKLIST_ROOT),
        "check_modules_dir": str(CHECK_MODULES_DIR),
        "exists": CHECK_MODULES_DIR.exists()
    }


@router.post("/file-stats")
async def get_file_stats(request: FileStatsRequest) -> Dict[str, Any]:
    """
    Get file statistics (lines, size).
    
    Args:
        request: File path to analyze
        
    Returns:
        Dict with file statistics
    """
    # Normalize path separators
    file_path_str = request.file_path.replace('/', os.sep).replace('\\', os.sep)
    file_path = Path(file_path_str)
    
    try:
        # Check if file exists
        if not file_path.exists():
            return {
                "exists": False,
                "lines": "?",
                "size": "?",
                "error": f"File not found: {file_path}"
            }
        
        # Get file size
        size_bytes = file_path.stat().st_size
        if size_bytes < 1024:
            size_str = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
        
        # Count lines
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                line_count = sum(1 for _ in f)
        except Exception:
            line_count = "?"
        
        return {
            "exists": True,
            "lines": line_count,
            "size": size_str,
            "error": None
        }
        
    except Exception as e:
        return {
            "exists": False,
            "lines": "?",
            "size": "?",
            "error": str(e)
        }


@router.post("/analyze-file")
async def analyze_file(request: FileAnalysisRequest) -> Dict[str, Any]:
    """
    Analyze file with LLM to extract patterns and sample data.
    
    Args:
        request: File path and type to analyze
        
    Returns:
        Dict with patterns and sample_data
    """
    # Normalize path separators
    file_path_str = request.file_path.replace('/', os.sep).replace('\\', os.sep)
    file_path = Path(file_path_str)
    
    try:
        # Check if file exists
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {file_path}"
            )
        
        # Read file content (limit to first 500 lines for large files)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [f.readline() for _ in range(500)]
                file_content = ''.join(lines)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read file: {str(e)}"
            )
        
        # Import LLM client
        import sys
        from pathlib import Path
        _tool_dir = Path(__file__).resolve().parent.parent.parent.parent
        if str(_tool_dir) not in sys.path:
            sys.path.insert(0, str(_tool_dir))
        
        try:
            from llm_clients.factory import create_llm_client
            
            # Use user-provided LLM configuration
            provider = request.llm_provider
            llm_client = create_llm_client(
                provider, 
                model=request.llm_model,
                verbose=False
            )
            
            # Prepare analysis prompt (aligned with CLI's file_analysis_mixin.py)
            prompt = f"""Analyze this input file for checker development (DEVELOPER_TASK_PROMPTS.md Phase 1).

File: {file_path.name}
File Type: {request.file_type}

File Content (first 500 lines):
```
{file_content[:10000]}
```

CRITICAL: Follow Phase 1 Analysis Steps from DEVELOPER_TASK_PROMPTS.md v1.1.0

Please analyze and provide:

1. **File Type**: (timing_report, sta_log, synthesis_log, sdc_file, spef_annotation, etc.)

2. **Define Output Format FIRST** (determines parsing granularity):
   - INFO01 should display: <what field/data? file paths? views? items? counts?>
   - ERROR01 should display: <what violations? net names? error codes?>
   - Display format: "[item_name] (view: view_name)" vs "error_code: message"
   - This determines what data must be extracted and associated during parsing

3. **Key Patterns** (3-5 most important, based on output requirements):
   For each pattern provide:
   - Pattern description
   - Regex or search string (actual regex, e.g. r'\\*\\*ERROR:\\s*\\(SPEF-(\\d+)\\)\\s*(.+)')
   - Example line from file
   - What data to extract: error codes, net names, view associations, line numbers
   - How it relates to INFO01/ERROR01 output format

4. **Parsing Strategy**:
   - Multi-file handling: aggregate vs per-file results
   - How to iterate through file (line-by-line, section-by-section, etc.)
   - What to look for (keywords, headers, delimiters)
   - Edge cases: empty files, missing sections, format variations

5. **Real Data Samples** (3-5 lines minimum):
   ```
   Sample Line 1: <paste actual content>
   Sample Line 2: <paste actual content>
   Sample Line 3: <paste actual content>
   Pattern: <actual regex>
   Extraction: <what gets captured>
   ```

6. **Template Recommendations**:
   - Can use parse_log_with_patterns()? (for regex-based parsing)
   - Can use normalize_command()? (for text normalization)
   - Other template helpers applicable?

Format your response as structured JSON for easy parsing."""
            
            # Call LLM with low temperature for analysis (matching CLI)
            response = llm_client.chat(prompt, temperature=0.1)
            
            # Parse response - try JSON first, then fallback to text parsing
            patterns = []
            sample_data = ""
            file_type_detected = request.file_type
            parsing_strategy = ""
            output_format = ""
            template_recommendations = []
            
            # Try to parse JSON response
            import json
            import re
            
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group(1))
                    file_type_detected = parsed.get('file_type', request.file_type)
                    output_format = parsed.get('output_format', '')
                    
                    # Extract patterns
                    pattern_list = parsed.get('patterns', [])
                    if isinstance(pattern_list, list):
                        for p in pattern_list:
                            if isinstance(p, dict):
                                desc = p.get('description', '')
                                regex = p.get('regex', '')
                                example = p.get('example', '')
                                patterns.append(f"{desc} | Regex: {regex} | Example: {example}")
                            else:
                                patterns.append(str(p))
                    
                    parsing_strategy = parsed.get('parsing_strategy', '')
                    sample_data = parsed.get('sample_data', '')
                    template_recommendations = parsed.get('template_recommendations', [])
                    
                except json.JSONDecodeError:
                    pass
            
            # Fallback: text parsing if JSON fails
            if not patterns:
                if "PATTERNS:" in response or "Key Patterns" in response:
                    # Extract patterns section
                    pattern_section = ""
                    if "PATTERNS:" in response:
                        pattern_section = response.split("PATTERNS:")[1].split("SAMPLE")[0] if "SAMPLE" in response else response.split("PATTERNS:")[1]
                    elif "Key Patterns" in response:
                        pattern_section = response.split("Key Patterns")[1].split("Parsing Strategy")[0] if "Parsing Strategy" in response else response.split("Key Patterns")[1]
                    
                    for line in pattern_section.split('\n'):
                        line = line.strip()
                        if line and (line.startswith('-') or line.startswith('•') or line.startswith('Pattern')):
                            pattern_text = re.sub(r'^[-•]\s*', '', line).strip()
                            pattern_text = re.sub(r'^Pattern \d+:\s*', '', pattern_text).strip()
                            if pattern_text:
                                patterns.append(pattern_text)
                
                # Extract sample data
                if "SAMPLE" in response or "Real Data Samples" in response:
                    if "SAMPLE_DATA:" in response:
                        sample_data = response.split("SAMPLE_DATA:")[1].strip()
                    elif "Real Data Samples" in response:
                        sample_data = response.split("Real Data Samples")[1].split("Template")[0].strip() if "Template" in response else response.split("Real Data Samples")[1].strip()
                
                # Extract parsing strategy
                if "Parsing Strategy" in response:
                    strategy_section = response.split("Parsing Strategy")[1].split("Real Data")[0] if "Real Data" in response else response.split("Parsing Strategy")[1]
                    parsing_strategy = strategy_section.strip()[:500]
                
                # Extract output format
                if "Output Format" in response or "Define Output Format" in response:
                    format_section = ""
                    if "Output Format" in response:
                        format_section = response.split("Output Format")[1].split("Key Patterns")[0] if "Key Patterns" in response else response.split("Output Format")[1]
                    parsing_strategy = format_section.strip()[:500]

            
            # Ensure we have at least some patterns
            if len(patterns) == 0:
                patterns = [
                    f"Pattern 1: Key indicators in {request.file_type}",
                    "Pattern 2: Critical values or thresholds",
                    "Pattern 3: Error/warning messages"
                ]
            
            # Use first 500 chars of file as fallback sample if none extracted
            if not sample_data:
                sample_data = file_content[:500] + "\n...\n(Truncated for display)"
            
            return {
                "file_type": file_type_detected,
                "patterns": patterns[:5],  # Limit to 5 patterns
                "sample_data": sample_data[:1000],  # Limit sample size
                "parsing_strategy": parsing_strategy,
                "output_format": output_format,
                "template_recommendations": template_recommendations,
                "ai_raw_response": response[:2000],  # Include partial raw response for debugging
                "status": "success"
            }
            
        except ImportError as e:
            # LLM client not available, return basic analysis
            print(f"Warning: LLM client not available: {e}")
            
            # Basic pattern detection without LLM
            basic_patterns = []
            if request.file_type.lower() in ['report file', 'rpt']:
                basic_patterns = [
                    "Pattern 1: Error/Warning lines (ERROR:|WARNING:|FAIL)",
                    "Pattern 2: Timing violations (slack, setup, hold)",
                    "Pattern 3: Constraint violations"
                ]
            elif request.file_type.lower() in ['log file', 'log']:
                basic_patterns = [
                    "Pattern 1: Error messages (Error:|ERROR:)",
                    "Pattern 2: Warning messages (Warning:|WARN:)",
                    "Pattern 3: Status indicators (PASS|FAIL)"
                ]
            else:
                basic_patterns = [
                    f"Pattern 1: Key indicators in {request.file_type}",
                    "Pattern 2: Error/warning markers",
                    "Pattern 3: Numeric values"
                ]
            
            return {
                "patterns": basic_patterns,
                "sample_data": file_content[:500] + "\n...\n(First 500 characters)",
                "status": "success",
                "note": "Basic analysis (LLM not available)"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )
