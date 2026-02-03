"""
Step 2: File Analysis
Corresponds to CLI's file_analysis_mixin.py

This implements the same file analysis logic as _ai_analyze_input_files()
in workflow/mixins/file_analysis_mixin.py
"""

import os
import sys
import glob
import json
import re
from pathlib import Path
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import LLM models
try:
    from utils.models import LLMCallConfig
except ImportError:
    from AutoGenChecker.utils.models import LLMCallConfig

router = APIRouter()

# Get CHECKLIST root directory
CHECKLIST_ROOT = Path(os.environ.get(
    "CHECKLIST_ROOT",
    Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent / "CHECKLIST"
))


class FileStatsRequest(BaseModel):
    """File statistics request model."""
    file_path: str


class FileAnalysisRequest(BaseModel):
    """
    File analysis request model.
    Corresponds to CLI's _call_ai_for_file_analysis() parameters.
    """
    file_path: str
    file_type: str
    llm_provider: str = 'jedai'
    llm_model: str = 'claude-sonnet-4-5'
    description: str = ''  # Checker description for context


def expand_path_variables(path: str) -> str:
    """
    Expand environment variables in path.
    Matches CLI's _expand_path_variables() in file_analysis_mixin.py
    """
    # Replace ${CHECKLIST_ROOT}
    if '${CHECKLIST_ROOT}' in path:
        path = path.replace('${CHECKLIST_ROOT}', str(CHECKLIST_ROOT))
    
    # Replace ${IP_PROJECT_FOLDER}
    if '${IP_PROJECT_FOLDER}' in path:
        ip_folder = CHECKLIST_ROOT / "IP_project_folder"
        path = path.replace('${IP_PROJECT_FOLDER}', str(ip_folder))
    
    # Replace ${WORK}
    if '${WORK}' in path:
        work_folder = CHECKLIST_ROOT / "Work"
        path = path.replace('${WORK}', str(work_folder))
    
    # Expand environment variables
    path = os.path.expandvars(path)
    
    return path


@router.post("/file-stats")
async def get_file_stats(request: FileStatsRequest) -> Dict[str, Any]:
    """
    Get file statistics (lines, size).
    
    Args:
        request: File path to analyze
        
    Returns:
        Dict with file statistics
    """
    # Expand path variables first
    file_path_str = expand_path_variables(request.file_path)
    
    # Normalize path separators
    file_path_str = file_path_str.replace('/', os.sep).replace('\\', os.sep)
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


class FileContentRequest(BaseModel):
    """File content request model."""
    file_path: str
    max_lines: int = 500  # Limit lines for large files


@router.post("/file-content")
async def get_file_content(request: FileContentRequest) -> Dict[str, Any]:
    """
    Get file content for display.
    
    Args:
        request: File path and max lines to read
        
    Returns:
        Dict with file content and metadata
    """
    # Expand path variables first
    file_path_str = expand_path_variables(request.file_path)
    
    # Normalize path separators
    file_path_str = file_path_str.replace('/', os.sep).replace('\\', os.sep)
    file_path = Path(file_path_str)
    
    try:
        # Check if file exists
        if not file_path.exists():
            return {
                "success": False,
                "content": "",
                "error": f"File not found: {file_path}",
                "total_lines": 0,
                "truncated": False
            }
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        truncated = total_lines > request.max_lines
        
        # Limit to max_lines
        if truncated:
            content = ''.join(lines[:request.max_lines])
        else:
            content = ''.join(lines)
        
        return {
            "success": True,
            "content": content,
            "error": None,
            "total_lines": total_lines,
            "truncated": truncated,
            "shown_lines": min(total_lines, request.max_lines)
        }
        
    except Exception as e:
        return {
            "success": False,
            "content": "",
            "error": str(e),
            "total_lines": 0,
            "truncated": False
        }


@router.post("/analyze-file")
async def analyze_file(request: FileAnalysisRequest) -> Dict[str, Any]:
    """
    Analyze file with LLM to extract patterns and sample data.
    
    Corresponds to CLI's _call_ai_for_file_analysis() in file_analysis_mixin.py
    Uses the same prompt structure from _build_file_analysis_prompt()
    
    Args:
        request: File path, type, and LLM config
        
    Returns:
        Dict with analysis results matching CLI's structure:
        - file_type: Detected file type
        - patterns: List of key patterns with regex
        - sample_data: Real data samples
        - parsing_strategy: Recommended parsing approach
        - output_format: INFO/ERROR format definition
        - template_recommendations: Template helper suggestions
    """
    # Expand path variables
    file_path_str = expand_path_variables(request.file_path)
    
    # Normalize path separators
    file_path_str = file_path_str.replace('/', os.sep).replace('\\', os.sep)
    file_path = Path(file_path_str)
    
    try:
        # Check if file exists
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {file_path}"
            )
        
        # Read ENTIRE file content - LLM needs complete context to find relevant patterns
        # Modern LLMs can handle large context, and checker analysis requires seeing all data
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()  # Read entire file
                
                # Only limit if file is extremely large (>500KB)
                # Most report/log files are under this size
                max_bytes = 500 * 1024
                if len(content.encode('utf-8')) > max_bytes:
                    # Keep first 80% to capture most patterns
                    truncate_point = int(len(content) * 0.8)
                    content = content[:truncate_point]
                    content += "\n\n... [File truncated - showing first 80% for analysis] ..."
                
                line_count = content.count('\n') + 1
                print(f"[DEBUG] File content: {len(content)} chars, {line_count} lines")
                print(f"[DEBUG] First 500 chars:\n{content[:500]}")
                    
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read file: {str(e)}"
            )
        
        # Import LLM client manager
        _backend_dir = Path(__file__).resolve().parent.parent.parent
        if str(_backend_dir) not in sys.path:
            sys.path.insert(0, str(_backend_dir))
        
        from llm_client_manager import llm_client_manager
        
        print(f"[DEBUG] Analyzing file: {file_path}")
        print(f"[DEBUG] LLM Provider: {request.llm_provider}, Model: {request.llm_model}")
        
        try:
            # Get or create LLM client (reuses existing instance)
            llm_client = llm_client_manager.get_client(
                provider=request.llm_provider,
                model=request.llm_model,
                verbose=True
            )
            
            print(f"[DEBUG] LLM client ready: {type(llm_client)}")
            
            # Build prompt using CLI's _build_file_analysis_prompt() structure
            prompt = build_file_analysis_prompt(
                file_path.name,
                content,
                request.description,
                similar_examples=None  # TODO: Implement similar example search
            )
            
            print(f"[DEBUG] Prompt built, length: {len(prompt)} chars")
            print(f"[DEBUG] Calling LLM...")
            
            # Call LLM with low temperature (matches CLI: temperature=0.1)
            # Use complete() method with LLMCallConfig
            config = LLMCallConfig(
                model=request.llm_model,
                temperature=0.1,
                max_tokens=4096
            )
            llm_response = llm_client.complete(prompt, config=config)
            response_text = llm_response.text
            
            print(f"[DEBUG] LLM response received, length: {len(response_text)} chars")
            print(f"[DEBUG] ===== LLM RESPONSE START =====")
            print(response_text[:2000])  # Print first 2000 chars
            print(f"[DEBUG] ===== LLM RESPONSE END =====")
            
            # Parse AI response to extract structured analysis
            # Matches CLI's _parse_ai_file_analysis()
            analysis = parse_ai_file_analysis(response_text)
            
            print(f"[DEBUG] ===== PARSED ANALYSIS =====")
            print(f"[DEBUG] File type: {analysis.get('file_type', 'N/A')}")
            print(f"[DEBUG] Patterns count: {len(analysis.get('patterns', []))}")
            print(f"[DEBUG] Patterns: {analysis.get('patterns', [])}")
            print(f"[DEBUG] =============================")
            analysis['exists'] = True
            
            print(f"[DEBUG] Analysis parsed successfully")
            
            return analysis
            
        except ImportError as e:
            # LLM client not available, return basic analysis
            print(f"[ERROR] LLM client import failed: {e}")
            print(f"[ERROR] Exception type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            import traceback
            traceback.print_exc()
            
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
                "exists": True,
                "file_type": request.file_type,
                "patterns": basic_patterns,
                "sample_data": content[:500] + "\n...\n(First 500 characters - LLM analysis failed)",
                "parsing_strategy": "Basic line-by-line parsing",
                "template_recommendations": [],
                "status": "success",
                "note": f"Basic analysis (LLM import failed: {str(e)})"
            }
        except Exception as e:
            print(f"[ERROR] LLM call failed: {e}")
            print(f"[ERROR] Exception type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


def build_file_analysis_prompt(
    filename: str,
    content: str,
    description: str,
    similar_examples: List[Dict[str, Any]] | None = None,
) -> str:
    """
    Build prompt for AI file analysis.
    
    Matches CLI's _build_file_analysis_prompt() in file_analysis_mixin.py
    """
    
    # Build examples section if available
    examples_section = ""
    if similar_examples:
        examples_section = "\n\n" + "="*80 + "\n"
        examples_section += "📚 SIMILAR FILE PARSING EXAMPLES (Reference for parsing logic)\n"
        examples_section += "="*80 + "\n\n"
        
        for i, example in enumerate(similar_examples, 1):
            examples_section += f"Example {i}: {example['item_id']}\n"
            examples_section += f"Description: {example['description']}\n"
            
            if example.get('patterns'):
                examples_section += f"Patterns used:\n"
                for pattern in example['patterns'][:3]:
                    examples_section += f"  - r'{pattern}'\n"
            
            if example.get('parsing_snippet') and example['parsing_snippet'] != 'N/A':
                examples_section += f"\nParsing method excerpt:\n```python\n{example['parsing_snippet']}\n```\n"
            
            examples_section += "\n" + "-"*40 + "\n\n"
        
        examples_section += "Use these examples as reference for:\n"
        examples_section += "- Similar regex patterns that work for this file type\n"
        examples_section += "- Proven parsing strategies\n"
        examples_section += "- Common field extraction logic\n"
        examples_section += "="*80 + "\n"
    
    # This is the EXACT prompt from CLI's _build_file_analysis_prompt()
    return f"""Analyze this input file for checker development (DEVELOPER_TASK_PROMPTS.md Phase 1).

Checker Description: {description}
File: {filename}
{examples_section}
File Content (COMPLETE FILE - all lines):
```
{content}
```

CRITICAL INSTRUCTIONS:
1. **Analyze based on the CHECKER DESCRIPTION above** - Understand what this checker needs to validate/extract
2. **Find RELEVANT patterns in the COMPLETE file content** - Scan the entire file to identify patterns related to the checker's purpose
3. ONLY use patterns visible in the ACTUAL CONTENT above - do NOT invent patterns for "typical" files
4. **Generate analysis for ALL 4 Template Types** - Each Type serves different checker architecture
5. ALL examples MUST be exact lines copied from the content above

====================================================================================
📚 UNDERSTAND THE 4 TEMPLATE TYPES (Read Carefully Before Analysis)
====================================================================================

**Type 1: Boolean Check** - Custom validation logic
   - Checker defines its own PASS/FAIL criteria
   - NO pattern_items list (requirements.value = N/A)
   - Checker examines file content and makes boolean decision
   - Examples: "File exists?", "Block name present?", "Valid format?"
   
**Type 2: Value Check** - Search for expected values
   - Requires pattern_items list (requirements.value > 0)
   - pattern_items = EXPECTED VALUES to find in file
   - Compare: found_items vs pattern_items
   - CRITICAL: If description mentions:
     * "version" → pattern_items are VERSION IDs (e.g., "22.11-s119_1")
     * "filename" or "name" → pattern_items are FILENAMES (e.g., "design.v")
     * "status" → pattern_items are STATUS VALUES (e.g., "Loaded", "Skipped")
   
**Type 3: Value Check + Waiver** - Type 2 with exemptions
   - Same as Type 2 PLUS waiver support
   - pattern_items = VALUES to match (versions, status, etc.)
   - waive_items.name = OBJECT NAMES to exempt (libraries, modules, files)
   - DIFFERENT SEMANTIC LEVELS:
     * pattern_items: What VALUES to check
     * waive_items.name: Which OBJECTS are allowed to fail
   - Example: Check library versions (pattern_items=["v2.0"]), 
             but exempt specific libraries (waive_items.name=["lib_legacy", "lib_old"])
   
**Type 4: Boolean Check + Waiver** - Type 1 with exemptions
   - Custom boolean check PLUS waiver support
   - NO pattern_items (like Type 1)
   - waive_items.name = OBJECT NAMES to exempt from violations
   - CRITICAL: waive_items must be IDENTICAL to Type 3's waive_items
   - Only use if violations can be identified as named objects

====================================================================================
📊 OUTPUT FORMAT MODES (Critical for Type 2/3)
====================================================================================

**Mode 1: existence_check** - Verify items SHOULD EXIST
   - pattern_items = items that MUST be found in file
   - found_items = pattern_items found in file ✓
   - missing_items = pattern_items NOT found in file ✗
   - PASS if missing_items is empty

**Mode 2: status_check** - Verify item STATUS
   - pattern_items = items to CHECK STATUS
   - Only output items that match pattern_items
   - found_items = items with CORRECT status ✓
   - missing_items = items with WRONG status ✗
   - Don't output items not in pattern_items

====================================================================================
🎯 HIERARCHICAL ANALYSIS TASK - INCREMENTAL TYPE STRUCTURE
====================================================================================

⚠️ CRITICAL DESIGN PRINCIPLE: PATTERNS ARE SHARED, CONFIGS ARE LAYERED

**Type 1 = Base Patterns** (shared by all types)
**Type 2 = Type 1 + pattern_items usage**
**Type 3 = Type 2 + waive_items usage**
**Type 4 = Type 1 + waive_items usage** (skips pattern_items)

====================================================================================

**Step 1: Generate BASE PATTERNS (Type 1)**
These patterns are used by ALL 4 types for parsing the input file.

Provide 2-4 key patterns that extract:
- Primary data fields (e.g., block names, versions, status)
- Object identifiers (needed for Type 3/4 waivers)
- Any critical values (needed for Type 2/3 comparisons)

For each pattern:
- description: What this pattern extracts
- regex: Actual regex (e.g., r'^Block name:\s*(.+)$')
- example_from_file: EXACT line from file content above
- extracted_data: What group captures (e.g., "block name string")

**Type 1 Parsing Strategy**: Simple boolean check using base patterns
**Type 1 Sample Data**: Real examples from file

---

**Step 2: Type 2 - Add pattern_items Usage**
- **Inherit**: ALL base patterns from Type 1
- **Add**: "pattern_items_usage" section explaining:
  - Which extracted values should be compared to pattern_items
  - What constitutes found_items vs missing_items
  - Suggested pattern_items based on file content

**Type 2 Parsing Strategy**: Type 1 patterns + value comparison logic
**Type 2 Sample Data**: Same as Type 1 (base patterns don't change)

---

**Step 3: Type 3 - Add waive_items Usage**
- **Inherit**: ALL base patterns from Type 1
- **Inherit**: pattern_items usage from Type 2
- **Add**: "waive_items_usage" section explaining:
  - Which object names can be matched against waive_items.name
  - Waived vs unwaived violation classification
  - Suggested waive_items based on file content

**Type 3 Parsing Strategy**: Type 2 logic + waiver application
**Type 3 Sample Data**: Same as Type 1 (base patterns don't change)

---

**Step 4: Type 4 - Boolean + Waivers**
- **Inherit**: ALL base patterns from Type 1
- **Skip**: pattern_items (not used in Type 4)
- **Add**: "waive_items_usage" section (SAME as Type 3)

**Type 4 Parsing Strategy**: Type 1 boolean check + waiver application
**Type 4 Sample Data**: Same as Type 1 (base patterns don't change)

Output in JSON format with HIERARCHICAL STRUCTURE:
```json
{{
  "file_type": {{
    "primary_type": "block_identification_report",
    "confidence": "HIGH",
    "reasoning": "File contains block name identifier"
  }},
  
  "type1_boolean_check": {{
    "key_patterns": [
      {{
        "description": "Extract block name (base pattern used by all types)",
        "regex": "^Block name:\\\\s*(.+)$",
        "example_from_file": "Block name: CDN_104H_cdn_hs_phy_data_slice_EW",
        "extracted_data": "block_name string"
      }},
      {{
        "description": "Extract status value (base pattern used by all types)",
        "regex": "^Status:\\\\s*(\\\\w+)$",
        "example_from_file": "Status: PASS",
        "extracted_data": "status value"
      }}
    ],
    "parsing_strategy": {{
      "approach": "Boolean check using base patterns",
      "steps": [
        "Use base patterns to parse file",
        "Check if required data exists",
        "Return PASS if criteria met, FAIL otherwise"
      ],
      "method": "Simple boolean validation"
    }},
    "real_data_samples": {{
      "samples": [
        "Block name: CDN_104H_cdn_hs_phy_data_slice_EW",
        "Status: PASS"
      ]
    }}
  }},
  
  "type2_value_check": {{
    "key_patterns": "SAME_AS_TYPE1",
    "pattern_items_usage": {{
      "compared_values": "block_name (extracted by base pattern)",
      "logic": "Compare extracted block names to pattern_items list",
      "found_items": "Block names that exist in pattern_items",
      "missing_items": "Items in pattern_items not found in file"
    }},
    "parsing_strategy": {{
      "approach": "Use Type 1 base patterns + pattern_items comparison",
      "steps": [
        "Use Type 1 patterns to extract block names",
        "Compare extracted values to pattern_items",
        "Classify as found_items or missing_items"
      ],
      "method": "Value extraction and comparison"
    }},
    "suggested_pattern_items": [
      "CDN_104H_cdn_hs_phy_data_slice_EW"
    ],
    "suggested_pattern_items_reasoning": "Block names expected to be present in file",
    "real_data_samples": "SAME_AS_TYPE1"
  }},
  
  "type3_value_with_waiver": {{
    "key_patterns": "SAME_AS_TYPE1",
    "pattern_items_usage": "SAME_AS_TYPE2",
    "waive_items_usage": {{
      "matched_objects": "block_name (from base pattern)",
      "logic": "After Type 2 comparison, check violation objects against waive_items.name",
      "waived_items": "Violations where object name in waive_items",
      "unwaived_items": "Violations where object name NOT in waive_items"
    }},
    "parsing_strategy": {{
      "approach": "Type 2 logic + waiver classification",
      "steps": [
        "Use Type 1 patterns to extract data",
        "Apply Type 2 pattern_items comparison",
        "For violations, check object names against waive_items",
        "Classify as waived or unwaived"
      ],
      "method": "Value check with waiver logic"
    }},
    "suggested_pattern_items": "SAME_AS_TYPE2",
    "suggested_waive_items": [
      "CDN_104H_cdn_hs_phy_data_slice_EW",
      "legacy_block_name",
      "test_block"
    ],
    "suggested_waive_reasoning": "Object names (block names) that can be exempted from violations",
    "real_data_samples": "SAME_AS_TYPE1"
  }},
  
  "type4_boolean_with_waiver": {{
    "key_patterns": "SAME_AS_TYPE1",
    "waive_items_usage": "SAME_AS_TYPE3",
    "parsing_strategy": {{
      "approach": "Type 1 boolean check + waiver application",
      "steps": [
        "Use Type 1 patterns for boolean check",
        "If violations found, extract object names",
        "Apply Type 3 waiver logic (match against waive_items.name)",
        "Classify as waived or unwaived"
      ],
      "method": "Boolean check with waiver logic"
    }},
    "suggested_waive_items": "SAME_AS_TYPE3",
    "suggested_waive_reasoning": "MUST be identical to Type 3 waive_items",
    "real_data_samples": "SAME_AS_TYPE1"
  }},
  
  "template_recommendations": [
    "Type 1: Simple checks (file exists? data present?)",
    "Type 2: Value verification (check specific values against expected list)",
    "Type 3: Type 2 + exemptions (some violations are waived)",
    "Type 4: Type 1 + exemptions (boolean check with waivers)"
  ]
}}
```

IMPORTANT: 
- Generate realistic analysis for EACH of the 4 types
- Use ACTUAL content from the file provided
- Each type should have its own complete analysis structure
- Patterns and examples must come from the real file content
- Focus on technical details (patterns, parsing, suggestions)
- Output format strings (INFO01/ERROR01) will be defined in Step 3 README"""


def parse_ai_file_analysis(ai_response: str) -> Dict[str, Any]:
    """
    Parse AI's structured file analysis response with 4 template types.
    
    Returns technical analysis for all 4 types: patterns, parsing strategy,
    sample data, and configuration suggestions (pattern_items, waive_items).
    
    Output format definitions (INFO01/ERROR01) are generated in Step 3 README.
    """
    # Initialize structure for all 4 types
    analysis_result = {
        'file_type': 'analyzed',
        'type1_boolean_check': {
            'outputFormat': '',
            'patterns': [],
            'parsingStrategy': '',
            'sampleData': ''
        },
        'type2_value_check': {
            'outputFormat': '',
            'patterns': [],
            'parsingStrategy': '',
            'sampleData': ''
        },
        'type3_value_with_waiver': {
            'outputFormat': '',
            'patterns': [],
            'parsingStrategy': '',
            'sampleData': ''
        },
        'type4_boolean_with_waiver': {
            'outputFormat': '',
            'patterns': [],
            'parsingStrategy': '',
            'sampleData': ''
        },
        'templateRecommendations': []
    }
    
    # Try to parse JSON response
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
    if not json_match:
        print("[WARNING] No JSON block found in AI response")
        return _create_fallback_analysis()
    
    try:
        parsed = json.loads(json_match.group(1))
        print(f"[DEBUG] ===== PARSED JSON STRUCTURE =====")
        print(f"[DEBUG] Keys: {list(parsed.keys())}")
        
        # Extract file type
        file_type_obj = parsed.get('file_type', {})
        if isinstance(file_type_obj, dict):
            primary = file_type_obj.get('primary_type', 'analyzed')
            confidence = file_type_obj.get('confidence', '')
            analysis_result['file_type'] = f"{primary} [confidence: {confidence}]" if confidence else primary
        elif isinstance(file_type_obj, str):
            analysis_result['file_type'] = file_type_obj
        
        # Extract template recommendations
        analysis_result['templateRecommendations'] = parsed.get('template_recommendations', [])
        
        # Process each of the 4 types
        type_configs = [
            ('type1_boolean_check', 'type1_boolean_check'),
            ('type2_value_check', 'type2_value_check'),
            ('type3_value_with_waiver', 'type3_value_with_waiver'),
            ('type4_boolean_with_waiver', 'type4_boolean_with_waiver')
        ]
        
        # Store Type 1 base data for reference
        type1_patterns = []
        type1_sample_data = ''
        
        for result_key, parsed_key in type_configs:
            type_data = parsed.get(parsed_key, {})
            if not isinstance(type_data, dict):
                continue
            
            # Extract patterns (handle SAME_AS_TYPE1 reference)
            pattern_list = type_data.get('key_patterns', [])
            if pattern_list == "SAME_AS_TYPE1":
                # Use Type 1's patterns
                analysis_result[result_key]['patterns'] = type1_patterns
            else:
                extracted_patterns = _extract_patterns(pattern_list)
                analysis_result[result_key]['patterns'] = extracted_patterns
                # Save Type 1 patterns for later reference
                if result_key == 'type1_boolean_check':
                    type1_patterns = extracted_patterns
            
            # Extract parsing strategy
            strategy_obj = type_data.get('parsing_strategy', {})
            analysis_result[result_key]['parsingStrategy'] = _extract_parsing_strategy(strategy_obj)
            
            # Extract sample data (handle SAME_AS_TYPE1 reference)
            sample_obj = type_data.get('real_data_samples', {})
            if sample_obj == "SAME_AS_TYPE1":
                # Use Type 1's sample data
                analysis_result[result_key]['sampleData'] = type1_sample_data
            else:
                extracted_sample = _extract_sample_data(sample_obj)
                analysis_result[result_key]['sampleData'] = extracted_sample
                # Save Type 1 sample data for later reference
                if result_key == 'type1_boolean_check':
                    type1_sample_data = extracted_sample
            
            # Extract pattern_items_usage (Type 2/3)
            if 'pattern_items_usage' in type_data:
                usage = type_data['pattern_items_usage']
                if usage == "SAME_AS_TYPE2":
                    # Type 3 inherits from Type 2 - copy from previous type
                    if 'type2_value_check' in analysis_result:
                        analysis_result[result_key]['patternItemsUsage'] = analysis_result['type2_value_check'].get('patternItemsUsage', {})
                elif isinstance(usage, dict):
                    analysis_result[result_key]['patternItemsUsage'] = usage
            
            # Extract waive_items_usage (Type 3/4)
            if 'waive_items_usage' in type_data:
                usage = type_data['waive_items_usage']
                if usage == "SAME_AS_TYPE3":
                    # Type 4 inherits from Type 3 - copy from previous type
                    if 'type3_value_with_waiver' in analysis_result:
                        analysis_result[result_key]['waiveItemsUsage'] = analysis_result['type3_value_with_waiver'].get('waiveItemsUsage', {})
                elif isinstance(usage, dict):
                    analysis_result[result_key]['waiveItemsUsage'] = usage
            
            # Extract suggested configuration items (handle SAME_AS_TYPE2/TYPE3 references)
            if 'suggested_pattern_items' in type_data:
                items = type_data.get('suggested_pattern_items', [])
                if items == "SAME_AS_TYPE2" and 'type2_value_check' in analysis_result:
                    analysis_result[result_key]['suggestedPatternItems'] = analysis_result['type2_value_check'].get('suggestedPatternItems', [])
                    analysis_result[result_key]['suggestedPatternItemsReasoning'] = analysis_result['type2_value_check'].get('suggestedPatternItemsReasoning', '')
                else:
                    analysis_result[result_key]['suggestedPatternItems'] = items
                    analysis_result[result_key]['suggestedPatternItemsReasoning'] = type_data.get('suggested_pattern_items_reasoning', '')
            
            if 'suggested_waive_items' in type_data:
                items = type_data.get('suggested_waive_items', [])
                if items == "SAME_AS_TYPE3" and 'type3_value_with_waiver' in analysis_result:
                    analysis_result[result_key]['suggestedWaiveItems'] = analysis_result['type3_value_with_waiver'].get('suggestedWaiveItems', [])
                    analysis_result[result_key]['suggestedWaiveReasoning'] = analysis_result['type3_value_with_waiver'].get('suggestedWaiveReasoning', '')
                else:
                    analysis_result[result_key]['suggestedWaiveItems'] = items
                    analysis_result[result_key]['suggestedWaiveReasoning'] = type_data.get('suggested_waive_reasoning', '')
        
        print(f"[DEBUG] Successfully parsed all 4 types with hierarchical structure")
        return analysis_result
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON decode failed: {e}")
        return _create_fallback_analysis()
    except Exception as e:
        print(f"[ERROR] Unexpected parsing error: {e}")
        import traceback
        traceback.print_exc()
        return _create_fallback_analysis()


def _extract_patterns(pattern_list: Any) -> List[str]:
    """Extract patterns from various structures."""
    if not pattern_list:
        return []
    
    patterns = []
    if isinstance(pattern_list, list):
        for p in pattern_list:
            if isinstance(p, dict):
                desc = p.get('description', '')
                regex = p.get('regex', '')
                example = p.get('example_from_file', p.get('example', ''))
                
                if desc and regex:
                    pattern_text = f"{desc}\n  Regex: {regex}"
                    if example and len(example) < 200:
                        pattern_text += f"\n  Example: {example[:150]}"
                    patterns.append(pattern_text)
                elif desc:
                    patterns.append(desc)
            else:
                patterns.append(str(p))
    
    return patterns


def _extract_parsing_strategy(strategy_obj: Any) -> str:
    """Extract parsing strategy from various structures."""
    if not strategy_obj:
        return ''
    
    if isinstance(strategy_obj, dict):
        parts = []
        
        approach = strategy_obj.get('approach', '')
        if approach:
            parts.append(f"Approach: {approach}")
        
        steps = strategy_obj.get('steps', [])
        if isinstance(steps, list) and steps:
            parts.append("\nSteps:")
            for i, step in enumerate(steps, 1):
                parts.append(f"  {i}. {step}")
        elif steps:
            parts.append(f"\nSteps: {steps}")
        
        method = strategy_obj.get('method', '')
        if method:
            parts.append(f"\nMethod: {method}")
        
        return '\n'.join(parts) if parts else json.dumps(strategy_obj, indent=2)
    elif isinstance(strategy_obj, str):
        return strategy_obj
    else:
        return ''


def _extract_sample_data(sample_obj: Any) -> str:
    """Extract sample data from various structures."""
    if not sample_obj:
        return ''
    
    if isinstance(sample_obj, dict):
        samples = sample_obj.get('samples', [])
        if samples:
            return '\n'.join(str(s) for s in samples[:5])
        else:
            return str(sample_obj)
    elif isinstance(sample_obj, str):
        return sample_obj
    else:
        return ''


def _create_fallback_analysis() -> Dict[str, Any]:
    """Create fallback analysis when parsing fails."""
    fallback_type = {
        'patterns': ['Pattern analysis pending'],
        'parsingStrategy': 'Line-by-line parsing approach',
        'sampleData': 'Sample data extraction pending'
    }
    
    return {
        'file_type': 'analyzed',
        'type1_boolean_check': dict(fallback_type),
        'type2_value_check': dict(fallback_type),
        'type3_value_with_waiver': dict(fallback_type),
        'type4_boolean_with_waiver': dict(fallback_type),
        'templateRecommendations': []
    }


# ============================================================================
# Resume Support Endpoints - Save/Load file analysis
# ============================================================================

class SaveFileAnalysisRequest(BaseModel):
    """Request to save file analysis results."""
    module: str
    item_id: str
    file_analysis: List[Dict[str, Any]]


class LoadFileAnalysisRequest(BaseModel):
    """Request to load file analysis from file."""
    module: str
    item_id: str


@router.post("/save-file-analysis")
async def save_file_analysis(request: SaveFileAnalysisRequest):
    """
    Save file analysis results to JSON file.
    
    Matches CLI's behavior of saving to:
    Check_modules/{module}/scripts/doc/{item_id}_file_analysis.json
    """
    try:
        from .resume_manager import get_resume_manager
        
        manager = get_resume_manager(request.module, request.item_id)
        saved_path = manager.save_file_analysis(request.file_analysis)
        
        return {
            "status": "success",
            "message": f"File analysis saved to {saved_path}",
            "path": saved_path,
            "file_count": len(request.file_analysis),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


class RefineAnalysisRequest(BaseModel):
    """Request model for AI refinement of complete file analysis."""
    file_path: str
    current_analysis: Dict[str, Any]  # Contains patterns, parsing_strategy, output_format, sample_data
    user_feedback: str
    llm_provider: str = 'jedai'
    llm_model: str = 'claude-sonnet-4-5'


@router.post("/refine-analysis")
async def refine_analysis(request: RefineAnalysisRequest):
    """
    Use AI to refine complete file analysis based on user feedback.
    
    This allows interactive improvement of all analysis aspects:
    - Patterns (detection logic)
    - Output format (INFO/ERROR messages)
    - Parsing strategy (approach description)
    - Sample data (if needed)
    """
    try:
        # Import LLM client manager
        _backend_dir = Path(__file__).resolve().parent.parent.parent
        if str(_backend_dir) not in sys.path:
            sys.path.insert(0, str(_backend_dir))
        
        from llm_client_manager import llm_client_manager
        
        print(f"[Step2] 🔄 Refining analysis for {request.file_path}")
        print(f"[Step2] User feedback: {request.user_feedback}")
        
        # Get LLM client
        llm_client = llm_client_manager.get_client(
            provider=request.llm_provider,
            model=request.llm_model,
            verbose=True
        )
        
        # Read file content for context
        file_path = Path(expand_path_variables(request.file_path))
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Limit to 100KB for context
                if len(content) > 100 * 1024:
                    content = content[:100 * 1024]
        except Exception as e:
            content = "[File content unavailable]"
        
        # Build refinement prompt with full context
        current = request.current_analysis
        prompt = f"""You are refining a file analysis based on user feedback.

File Content (first 100KB):
===========================
{content[:5000]}
... [truncated]

Current Analysis:
================
Patterns:
{chr(10).join(f'  - {p}' for p in current.get('patterns', []))}

Output Format:
{current.get('output_format', 'N/A')}

Parsing Strategy:
{current.get('parsing_strategy', 'N/A')}

Sample Data:
{current.get('sample_data', 'N/A')[:500]}

User Feedback:
==============
{request.user_feedback}

Task:
=====
Based on the user feedback, provide a refined analysis with updated:
1. Patterns - improved detection patterns with regex
2. Output Format - INFO01/ERROR01 message formats
3. Parsing Strategy - detailed approach description
3. Sample Data - representative data examples (if needed)

Output Format (JSON):
{{
  "patterns": ["Pattern 1: description\\n  Regex: ^pattern$", "Pattern 2: ...", ...]
  "sample_data": "Sample data lines (if updated)"
}}

Provide ONLY the JSON output, no additional text.
"""
        
        # Call LLM
        config = LLMCallConfig(
            model=request.llm_model,
            temperature=0.3,
            max_tokens=3000
        )
        
        response = llm_client.complete(prompt, config=config)
        
        # Parse JSON response
        try:
            # Extract JSON from response (might be wrapped in ```json```)
            text = response.text.strip()
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            text = text.strip()
            
            result = json.loads(text)
            
            print(f"[Step2] ✅ Refinement successful")
            
            return {
                "status": "success",
                "patterns": result.get("patterns", current.get('patterns', [])),
                "output_format": result.get("output_format", current.get('output_format', '')),
                "parsing_strategy": result.get("parsing_strategy", current.get('parsing_strategy', '')),
                "sample_data": result.get("sample_data", current.get('sample_data', '')),
                "ai_raw_response": f"[Refined based on: {request.user_feedback[:100]}]"
            }
        except json.JSONDecodeError as e:
            print(f"[Step2] ❌ Failed to parse AI response as JSON: {e}")
            print(f"[Step2] Raw response: {response.text}")
            return {
                "status": "error",
                "error": "Failed to parse AI response",
                "raw_response": response.text
            }
    
    except Exception as e:
        print(f"[Step2] ❌ Refinement failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"AI refinement failed: {str(e)}"
        )


@router.post("/load-file-analysis")
async def load_file_analysis(request: LoadFileAnalysisRequest):
    """
    Load file analysis from JSON file (resume support).
    
    Loads from: Check_modules/{module}/scripts/doc/{item_id}_file_analysis.json
    """
    try:
        from .resume_manager import get_resume_manager
        
        manager = get_resume_manager(request.module, request.item_id)
        file_analysis = manager.load_file_analysis()
        
        if file_analysis is None:
            return {
                "status": "not_found",
                "exists": False,
                "message": f"No file analysis found for {request.item_id}",
            }
        
        paths = manager.get_paths()
        file_info = manager.get_file_info(paths['file_analysis'])
        
        return {
            "status": "success",
            "exists": True,
            "file_analysis": file_analysis,
            "file_count": len(file_analysis),
            "path": str(paths['file_analysis']),
            "modified_time": file_info['modified_time'] if file_info else None,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "exists": False,
        }
