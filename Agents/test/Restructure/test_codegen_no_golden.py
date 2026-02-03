# -*- coding: utf-8 -*-
"""
Test CodeGen Agent without Golden Reference

This test validates that the CodeGen Agent can generate code
that matches the reference implementation (Check_10_0_0_00_aggressive.py)
without using Golden as a reference.

Key verification points:
1. Three-layer architecture (_parse_input_files, _boolean_check_logic, _pattern_check_logic)
2. Type execution methods (_execute_type1/2/3/4) using execute_boolean_check/execute_value_check
3. Data structure consistency (Dict not List for missing_items)
4. Waiver control (has_waiver=True/False)

Author: CodeGen Agent Test
Date: 2025-01-02
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Setup paths
_SCRIPT_DIR = Path(__file__).resolve().parent
_AGENT_DIR = _SCRIPT_DIR.parents[1]  # test/Restructure -> Agent
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

# Output directory
OUTPUT_DIR = _SCRIPT_DIR / "test_output_no_golden"
OUTPUT_DIR.mkdir(exist_ok=True)


def get_test_item_spec() -> Dict[str, Any]:
    """
    Get a comprehensive test Item Spec for IMP-10-0-0-00
    
    This should provide enough context for LLM to generate correct code
    without Golden reference.
    """
    return {
        "item_id": "IMP-10-0-0-00",
        "description": "Confirm the netlist/spef version is correct.",
        "check_module": "IMP",
        "detected_type": 1,
        
        # Requirements
        "requirements": {
            "value": "N/A",
            "pattern_items": []  # Type 1/4 don't use pattern_items
        },
        
        # Input files
        "input_files": "logs/sta_post_syn.log",
        
        # Waivers
        "waivers": {
            "value": "N/A",
            "waive_items": []
        },
        
        # Parse logic
        "parse_logic": {
            "file_type": "log",
            "parsing_method": "Parse STA log to extract netlist/SPEF file paths and version info",
            "key_patterns": [
                "Read Netlist: <path>",
                "Read SPEF: <path>",
                "Status: Success/Failed",
                "Skipping SPEF reading"
            ]
        },
        
        # Semantic intent (v3.8)
        "semantic_intent": {
            "check_target": "Verify netlist and SPEF file version information",
            "data_flow": "STA log → netlist/spef paths → actual files → version extraction",
            "involved_formats": [
                {"name": "STA_Log", "data_role": "indirect_reference", "role": "Provides file paths to SPEF/Netlist files"},
                {"name": "Verilog_Netlist", "data_role": "direct_source", "role": "Contains Genus tool version"},
                {"name": "SPEF", "data_role": "direct_source", "role": "Contains SPEF version and program info"}
            ]
        },
        
        # Extraction fields for regex
        "extraction_fields": {
            "sta_log": [
                {
                    "field_name": "netlist_path",
                    "regex_template": r"Read Netlist:\s*(.+)",
                    "description": "Extract netlist file path"
                },
                {
                    "field_name": "spef_path",
                    "regex_template": r"Read SPEF:\s*(.+)",
                    "description": "Extract SPEF file path"
                },
                {
                    "field_name": "status",
                    "regex_template": r"Status:\s*(Success|Failed)",
                    "description": "Extract read status"
                },
                {
                    "field_name": "spef_skip",
                    "regex_template": r"Skipping SPEF reading",
                    "description": "Detect SPEF skip"
                }
            ],
            "netlist": [
                {
                    "field_name": "tool_version",
                    "regex_template": r"Synthesis Solution\s+([\d\.\-\w]+)",
                    "description": "Extract Genus version"
                },
                {
                    "field_name": "gen_date",
                    "regex_template": r"Generated on:\s+(\w+\s+\d+\s+\d+)\s+([\d:]+)",
                    "description": "Extract generation date/time"
                }
            ],
            "spef": [
                {
                    "field_name": "spef_version",
                    "regex_template": r'\*VERSION\s+"([^"]+)"',
                    "description": "Extract SPEF version"
                },
                {
                    "field_name": "spef_date",
                    "regex_template": r'\*DATE\s+"([^"]+)"',
                    "description": "Extract SPEF date"
                },
                {
                    "field_name": "spef_program",
                    "regex_template": r'\*PROGRAM\s+"([^"]+)"',
                    "description": "Extract SPEF program name"
                }
            ]
        },
        
        # Type execution specs (all 4 types)
        "type_execution_specs": [
            {
                "type_id": 1,
                "description": "Boolean check - verify netlist and SPEF loaded successfully",
                "pass_condition": "Both files read with Status: Success",
                "fail_condition": "Any file read failed",
                "needs_pattern_search": False,
                "needs_waiver_logic": False,
                "framework_method": "execute_boolean_check(parse_data_func, has_waiver=False, ...)"
            },
            {
                "type_id": 2,
                "description": "Value check - match version info from pattern_items",
                "pass_condition": "Pattern items found in output",
                "fail_condition": "Pattern items not found",
                "needs_pattern_search": True,
                "needs_waiver_logic": False,
                "framework_method": "execute_value_check(parse_data_func, has_waiver=False, ...)"
            },
            {
                "type_id": 3,
                "description": "Value check with waiver - match pattern_items with waiver handling",
                "pass_condition": "Pattern items found or waived",
                "fail_condition": "Pattern items not found and not waived",
                "needs_pattern_search": True,
                "needs_waiver_logic": True,
                "framework_method": "execute_value_check(parse_data_func, has_waiver=True, info_items=..., ...)"
            },
            {
                "type_id": 4,
                "description": "Boolean check with waiver - verify load success with waiver handling",
                "pass_condition": "Both files read successfully or waived",
                "fail_condition": "Any file read failed and not waived",
                "needs_pattern_search": False,
                "needs_waiver_logic": True,
                "framework_method": "execute_boolean_check(parse_data_func, has_waiver=True, ...)"
            }
        ],
        
        # Class constants (from reference)
        "class_constants": {
            "FOUND_DESC": "Netlist/SPEF files loaded successfully",
            "MISSING_DESC": "Netlist/SPEF loading issues",
            "FOUND_REASON": "Status: Success",
            "MISSING_REASON": "File loading failed",
            "EXTRA_DESC": "Design has no spef/netlist file",
            "EXTRA_REASON": "Design has no spef/netlist file or unexpected error"
        },
        
        # Logic steps (three-layer architecture)
        "logic_steps": [
            "Layer 1 (_parse_input_files): Parse STA log → get netlist/spef paths → parse actual files → return Dict with netlist_info, spef_info, errors",
            "Layer 2a (_boolean_check_logic): Type1/4 shared - check file existence, return (found_items, missing_items, extra_items) as Dicts",
            "Layer 2b (_pattern_check_logic): Type2/3 shared - match pattern_items, return (found_items, missing_items, extra_items) as Dicts",
            "Layer 3 (_execute_typeN): Call framework methods execute_boolean_check or execute_value_check with appropriate parameters"
        ],
        
        # Architecture guidance
        "architecture_guidance": {
            "three_layer_design": True,
            "layer1_method": "_parse_input_files() -> Dict[str, Any]",
            "layer2_methods": [
                "_boolean_check_logic(parsed_data) -> Tuple[Dict, Dict, Dict]",
                "_pattern_check_logic(parsed_data) -> Tuple[Dict, Dict, Dict]"
            ],
            "layer3_methods": [
                "_execute_type1: call execute_boolean_check with has_waiver=False",
                "_execute_type2: call execute_value_check with has_waiver=False",
                "_execute_type3: call execute_value_check with has_waiver=True, info_items",
                "_execute_type4: call execute_boolean_check with has_waiver=True"
            ],
            "data_structure_rules": [
                "found_items: Dict[str, Dict] - key is item name, value is metadata",
                "missing_items: Dict[str, Dict] - MUST be Dict, not List",
                "extra_items: Dict[str, Dict] - for SPEF skip or errors"
            ]
        }
    }


def get_log_samples() -> Dict[str, str]:
    """Provide realistic log samples"""
    return {
        "sta_post_syn.log": """
INFO: Starting STA analysis for block_a
INFO: Read Netlist: /designs/block_a/synthesis/block_a_mapped.v.gz
  > Reading verilog netlist '/designs/block_a/synthesis/block_a_mapped.v.gz'
  > *** Netlist is unique
INFO: Read SPEF: /designs/block_a/parasitics/block_a_rc.spef.gz
  > Begin flow_step read_parasitics
  > End flow_step read_parasitics
INFO: Analysis complete
""",
        "netlist_sample.v": """
// Generated by Cadence Genus(TM) Synthesis Solution 23.15-s099_1
// Generated on: Nov 18 2025 15:58:15 IST (Nov 18 2025 10:28:15 UTC)
// ... netlist content ...
""",
        "spef_sample.spef": """
*SPEF "IEEE 1481-1999"
*DESIGN "block_a"
*DATE "Tue Jun 10 14:16:48 2025"
*VENDOR "Cadence"
*PROGRAM "Cadence Quantus Extraction"
*VERSION "23.1.0-p075 Tue Sep 26 09:27:40 PDT 2023"
// ... SPEF content ...
"""
    }


def save_json(data, filename):
    """Save data to JSON file"""
    filepath = OUTPUT_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    print(f"  Saved: {filepath.name}")
    return filepath


def save_text(text, filename):
    """Save text to file"""
    filepath = OUTPUT_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"  Saved: {filepath.name}")
    return filepath


async def run_codegen_without_golden():
    """Run CodeGen Agent without Golden reference"""
    print("=" * 70)
    print("CodeGen Test: NO GOLDEN Reference")
    print("=" * 70)
    print(f"Output Directory: {OUTPUT_DIR}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Import CodeGen Agent
    from agents.code_generation.agent import CodeGenerationAgent
    from agents.code_generation.models import CodeGenInput
    
    # Get test data
    item_spec = get_test_item_spec()
    log_samples = get_log_samples()
    
    save_json(item_spec, "input_item_spec.json")
    save_json(log_samples, "log_samples.json")
    
    # Create CodeGenInput WITHOUT golden_reference
    codegen_input = CodeGenInput(
        item_spec=item_spec,
        item_spec_path=None,
        log_samples=log_samples,
        reference_snippets=None,  # No pre-loaded snippets
        golden_reference=None,    # NO GOLDEN!
        golden_path=None,
        output_dir=str(OUTPUT_DIR)
    )
    
    # Create agent
    agent = CodeGenerationAgent(debug_mode=True)
    
    print("-" * 70)
    print("Running CodeGen Agent (NO GOLDEN)...")
    print("-" * 70)
    
    start_time = datetime.now()
    
    result = await agent.process(
        task={
            "item_spec": item_spec,
            "log_samples": log_samples,
            "golden_reference": None,  # Explicitly no golden
            "output_dir": str(OUTPUT_DIR)
        }
    )
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print()
    print("-" * 70)
    print("CodeGen Execution Complete")
    print("-" * 70)
    print(f"Duration: {duration:.2f} seconds")
    print(f"Status: {result.status}")
    print()
    
    # Save results
    print("Saving Results...")
    
    if result.result:
        save_text(result.result, "generated_checker.py")
        print(f"  Generated code length: {len(result.result)} chars")
    
    # Save artifacts
    if result.artifacts:
        save_json({
            "checker_id": result.artifacts.get("checker_id"),
            "validation_result": result.artifacts.get("validation_result"),
            "iterations": result.artifacts.get("iterations"),
        }, "codegen_artifacts.json")
    
    # Save metadata
    if result.metadata:
        save_json(result.metadata, "codegen_metadata.json")
    
    # Analyze the generated code
    if result.result:
        print()
        print("-" * 70)
        print("Analyzing Generated Code...")
        print("-" * 70)
        
        code = result.result
        
        # Check for key methods
        checks = [
            ("_parse_input_files", "def _parse_input_files(self" in code),
            ("_boolean_check_logic", "def _boolean_check_logic(self" in code),
            ("_pattern_check_logic", "def _pattern_check_logic(self" in code),
            ("_execute_type1", "def _execute_type1(self" in code),
            ("_execute_type2", "def _execute_type2(self" in code),
            ("_execute_type3", "def _execute_type3(self" in code),
            ("_execute_type4", "def _execute_type4(self" in code),
            ("execute_boolean_check", "execute_boolean_check(" in code),
            ("execute_value_check", "execute_value_check(" in code),
            ("has_waiver=True", "has_waiver=True" in code),
            ("has_waiver=False", "has_waiver=False" in code),
            ("Dict missing_items", "missing_items[" in code or "missing_items = {}" in code),
        ]
        
        print("\nStructure Check:")
        all_pass = True
        for name, found in checks:
            status = "✅" if found else "❌"
            print(f"  {status} {name}")
            if not found:
                all_pass = False
        
        print()
        if all_pass:
            print("✅ All structure checks passed!")
        else:
            print("❌ Some structure checks failed.")
    
    return result.status == "success"


if __name__ == "__main__":
    success = asyncio.run(run_codegen_without_golden())
    sys.exit(0 if success else 1)
