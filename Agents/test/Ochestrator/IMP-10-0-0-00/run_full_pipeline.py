# -*- coding: utf-8 -*-
"""
Full Pipeline Debug Run for IMP-10-0-0-00

This script runs the complete Orchestrator pipeline:
ContextAgent -> CodeGenAgent -> ValidationAgent

Output will be saved to this directory.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Setup paths
_SCRIPT_DIR = Path(__file__).resolve().parent
_AGENT_DIR = _SCRIPT_DIR.parents[2]  # test/Ochestrator/IMP-10-0-0-00 -> Agent
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

# Output directory
OUTPUT_DIR = _SCRIPT_DIR


def get_test_item_spec():
    """
    Get the test Item Spec for IMP-10-0-0-00
    
    This simulates what ContextAgent would produce.
    """
    return {
        "item_id": "IMP-10-0-0-00",
        "description": "Confirm the netlist/spef version is correct.",
        "check_module": "IMP",
        "detected_type": 1,
        "requirements": {
            "value": "N/A",
            "pattern_items": []
        },
        "input_files": "logs/sta_post_syn.log",
        "waivers": {
            "value": "N/A",
            "waive_items": []
        },
        "check_logic": {
            "parsing_method": "Read STA log and extract netlist/SPEF file info",
            "pass_fail_logic": "PASS if both files read successfully, FAIL otherwise",
            "regex_patterns": [
                r"Read Netlist:\s*(.+)",
                r"Read SPEF:\s*(.+)",
                r"Status:\s*(Success|Failed)",
            ]
        },
        "file_analysis": {
            "sample_lines": [
                "INFO: Starting STA analysis",
                "INFO: Read Netlist: /designs/block_a/netlist_v1.v.gz",
                "  > Status: Success",
                "  > Version: Cadence Genus 23.15",
                "INFO: Read SPEF: /designs/block_a/parasitic.spef.gz",
                "  > Status: Success",
                "  > SPEF Version: IEEE 1481-1999",
                "INFO: Analysis complete"
            ]
        },
        "type_execution_specs": [
            {
                "type_id": 1,
                "description": "Boolean check - netlist and SPEF read successfully",
                "pass_condition": "Both files read with Status: Success",
                "fail_condition": "Any file read failed",
                "needs_pattern_search": False,
                "needs_waiver_logic": False
            },
            {
                "type_id": 2,
                "description": "Value check with pattern matching",
                "pass_condition": "Pattern items found in output",
                "fail_condition": "Pattern items not found",
                "needs_pattern_search": True,
                "needs_waiver_logic": False
            },
            {
                "type_id": 3,
                "description": "Value check with waiver logic",
                "pass_condition": "Pattern items found or waiver valid",
                "fail_condition": "Pattern items not found and waiver invalid",
                "needs_pattern_search": True,
                "needs_waiver_logic": True
            },
            {
                "type_id": 4,
                "description": "Boolean check with waiver logic",
                "pass_condition": "Check passed or waiver valid",
                "fail_condition": "Check failed and waiver invalid/expired",
                "needs_pattern_search": False,
                "needs_waiver_logic": True
            }
        ]
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


async def run_full_pipeline():
    """Run the complete pipeline"""
    print("=" * 70)
    print("Full Pipeline Debug Run: IMP-10-0-0-00")
    print("=" * 70)
    print(f"Output Directory: {OUTPUT_DIR}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Import agents
    from agents.orchestrator.agent import (
        OrchestratorAgent, 
        PipelineConfig,
        HAS_CONTEXT_AGENT,
        HAS_CODEGEN_AGENT,
        HAS_VALIDATION_AGENT
    )
    
    print("Agent Availability:")
    print(f"  - ContextAgent: {HAS_CONTEXT_AGENT}")
    print(f"  - CodeGenAgent: {HAS_CODEGEN_AGENT}")
    print(f"  - ValidationAgent: {HAS_VALIDATION_AGENT}")
    print()
    
    # Get test item spec
    item_spec = get_test_item_spec()
    save_json(item_spec, "input_item_spec.json")
    
    # Configure pipeline
    config = PipelineConfig(
        run_context_agent=False,        # Skip - we provide item_spec directly
        run_codegen_agent=True,
        run_validation_agent=True,
        validation_use_mock_llm=True,   # Use Mock LLM for validation
        debug_mode=True,
    )
    
    # Create orchestrator
    orchestrator = OrchestratorAgent(config=config, debug_mode=True)
    
    # Run pipeline
    print("-" * 70)
    print("Starting Pipeline Execution...")
    print("-" * 70)
    
    start_time = datetime.now()
    
    result = await orchestrator.process({
        "item_spec": item_spec,
        "output_dir": str(OUTPUT_DIR),
    })
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print()
    print("-" * 70)
    print("Pipeline Execution Complete")
    print("-" * 70)
    print(f"Duration: {duration:.2f} seconds")
    print(f"Status: {result.status}")
    print()
    
    # Save results
    print("Saving Results...")
    
    # 1. Pipeline summary
    if result.artifacts:
        pipeline_summary = result.artifacts.get("pipeline_summary", {})
        save_json(pipeline_summary, "pipeline_summary.json")
        
        # Activity log
        activity_log = result.artifacts.get("activity_log", [])
        if activity_log:
            save_text("\n".join(activity_log), "activity_log.txt")
    
    # 2. Generated code
    if result.result:
        save_text(result.result, "generated_checker.py")
        print(f"  Generated code length: {len(result.result)} chars")
    
    # 3. Validation report
    if result.artifacts:
        validation_report = result.artifacts.get("validation_report")
        if validation_report:
            if isinstance(validation_report, dict):
                save_json(validation_report, "validation_result.json")
                if "report" in validation_report:
                    save_text(validation_report["report"], "validation_report.md")
            elif isinstance(validation_report, str):
                save_text(validation_report, "validation_report.md")
    
    # 4. Debug info
    debug_info = {
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": duration,
        "status": result.status,
        "errors": result.errors if hasattr(result, 'errors') else [],
        "config": {
            "run_context_agent": config.run_context_agent,
            "run_codegen_agent": config.run_codegen_agent,
            "run_validation_agent": config.run_validation_agent,
            "validation_use_mock_llm": config.validation_use_mock_llm,
        }
    }
    save_json(debug_info, "debug_info.json")
    
    # Print summary
    print()
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    
    if result.artifacts:
        summary = result.artifacts.get("pipeline_summary", {})
        print(f"  Context Status: {summary.get('context_status', 'Skipped')}")
        print(f"  CodeGen Status: {summary.get('codegen_status', 'N/A')}")
        print(f"  Validation Status: {summary.get('validation_status', 'N/A')}")
        print(f"  Has Generated Code: {summary.get('has_generated_code', False)}")
        
        if summary.get('errors'):
            print(f"\n  Errors:")
            for err in summary['errors']:
                print(f"    - {err}")
    
    print()
    print(f"Output files saved to: {OUTPUT_DIR}")
    print()
    
    return result.status == "success"


if __name__ == "__main__":
    success = asyncio.run(run_full_pipeline())
    sys.exit(0 if success else 1)
