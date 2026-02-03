# -*- coding: utf-8 -*-
"""
Real JEDAI Test - Developer Agent
Uses actual JEDAI API to generate checker code for ANY ItemSpec

This script is a GENERIC test runner - it does NOT hardcode any specific ItemSpec.
All ItemSpec-specific information is extracted dynamically.

Usage:
  python test_real_jedai.py --item <item_spec_path>           # Run with specified ItemSpec
  python test_real_jedai.py --item <item_spec_path> --model azure-gpt-4o  # Use specific model
  python test_real_jedai.py --list-models                     # List available models
  python test_real_jedai.py --resume <item_id>                # Resume from cache

Examples:
  python test_real_jedai.py --item "Test/Check_modules/10.0_STA_DCD_CHECK/inputs/items/IMP-10-0-0-00.yaml"
  python test_real_jedai.py --item "path/to/ANY_ITEM.yaml" --model claude-sonnet-4-5
"""
import sys
import os
import argparse
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add paths
AGENT_DIR = Path(__file__).parent
sys.path.insert(0, str(AGENT_DIR))
sys.path.insert(0, str(AGENT_DIR.parent / "JEDAI"))

# Import modules
from llm_client import DEFAULT_MODEL, AVAILABLE_MODELS
from cache import FileSystemCache
from state import generate_item_id
from io_formatter import (
    print_formatted_prompt,
    print_formatted_response,
    print_formatted_validation,
    save_io_as_markdown
)

# Base directories (configurable)
WORKSPACE_ROOT = AGENT_DIR.parent.parent.parent  # codegen folder
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "Test" / "Codegen"


def get_item_id_from_path(item_spec_path: str) -> str:
    """
    Extract item_id from ItemSpec path (generic, no hardcoding)
    
    Examples:
        "items/IMP-10-0-0-00.yaml" -> "IMP-10-0-0-00"
        "path/to/ABC-1-2-3-04_ItemSpec.md" -> "ABC-1-2-3-04"
    """
    return generate_item_id(item_spec_path)


def setup_output_dirs(output_dir: Path, item_id: str) -> Dict[str, Path]:
    """
    Create output directories for a specific item
    
    Returns dict with paths: cache, output, logs
    """
    item_output_dir = output_dir / item_id
    paths = {
        "base": item_output_dir,
        "cache": item_output_dir / "cache",
        "output": item_output_dir / "output",
        "logs": item_output_dir / "logs"
    }
    
    for name, path in paths.items():
        path.mkdir(parents=True, exist_ok=True)
    
    print(f"[OK] Output directories created at: {item_output_dir}")
    return paths


def test_jedai_connection(model: str) -> bool:
    """Test JEDAI connection"""
    print("\n" + "="*60)
    print("Step 1: Testing JEDAI Connection")
    print("="*60)
    
    from jedai_langchain import JedaiLangChain
    
    jedai = JedaiLangChain()
    print(f"[OK] JEDAI connected successfully")
    
    # Test simple invocation with specified model
    llm = jedai.create_llm(model=model, temperature=0.1, max_tokens=100)
    response = llm.invoke("Say 'JEDAI connection test successful' in one line.")
    print(f"[OK] Test response: {response.content[:100]}...")
    
    return True


def load_item_spec(item_spec_path: str) -> Dict[str, Any]:
    """
    Load ItemSpec file and return raw Markdown content.
    
    The raw Markdown will be parsed into sections by prompts.py
    for selective injection to Agent A and Agent B.
    
    Returns:
        Dict with:
            - _item_id: Item identifier
            - _raw_markdown: Original Markdown content (for section parsing)
    """
    print("\n" + "="*60)
    print("Step 2: Loading ItemSpec")
    print("="*60)
    
    path = Path(item_spec_path)
    if not path.exists():
        # Try relative to workspace root
        path = WORKSPACE_ROOT / item_spec_path
    
    if not path.exists():
        raise FileNotFoundError(f"ItemSpec not found: {item_spec_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        raw_markdown = f.read()
    
    item_id = get_item_id_from_path(str(path))
    
    # Return raw markdown for section-based parsing
    spec = {
        "_item_id": item_id,
        "_raw_markdown": raw_markdown,  # Raw content for prompts.py to parse
    }
    
    print(f"[OK] Loaded ItemSpec: {path.name}")
    print(f"  - Item ID: {item_id}")
    print(f"  - Markdown size: {len(raw_markdown)} chars")
    
    # Preview sections
    from prompts import parse_itemspec_sections
    sections = parse_itemspec_sections(raw_markdown)
    for key, content in sections.items():
        if content:
            print(f"  - {key}: {len(content)} chars")
    
    return spec


def load_log_samples(item_spec: Dict[str, Any], log_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Load log file samples based on ItemSpec input_files configuration
    
    This is generic - it reads paths from the ItemSpec, not hardcoded
    """
    print("\n" + "="*60)
    print("Step 3: Loading Log Samples")
    print("="*60)
    
    snippets = {}
    input_files = item_spec.get('input_files', [])
    
    if not input_files:
        print("[WARN] No input_files specified in ItemSpec")
        return snippets
    
    for file_pattern in input_files:
        # Replace variables like ${CHECKLIST_ROOT}
        file_path = file_pattern.replace('${CHECKLIST_ROOT}', str(WORKSPACE_ROOT / "Test"))
        path = Path(file_path)
        
        if log_dir:
            # Override with specified log directory
            path = Path(log_dir) / path.name
        
        if path.exists():
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract sample (first 3000 chars or until meaningful content)
            sample = content[:3000]
            snippets[path.name] = {
                "content": sample,
                "path": str(path),
                "size": len(content)
            }
            print(f"[OK] Loaded log file: {path.name} ({len(content)} bytes)")
            print(f"  Sample preview ({len(sample)} chars):")
            for line in sample.split('\n')[:5]:
                print(f"    {line[:80]}")
            print("    ...")
        else:
            print(f"[WARN] Log file not found: {path}")
    
    return snippets


def run_agent_a(item_spec: Dict[str, Any], log_snippets: Dict[str, Any], 
                model: str, cache: FileSystemCache, output_dir: Path = None) -> str:
    """
    Run Agent A: Generate extract_context function
    
    Agent A receives: Section 1 (Parsing Logic) + Section 4.1 (Data Source)
    """
    print("\n" + "="*60)
    print("Step 4: Agent A - Generate extract_context")
    print("="*60)
    
    from llm_client import LLMClient
    from state import LLMConfig
    from prompts import build_agent_a_prompt, parse_agent_response
    
    item_id = item_spec.get("_item_id", "unknown")
    raw_markdown = item_spec.get("_raw_markdown", "")
    
    # Build prompt using raw Markdown (section parsing happens in build_agent_a_prompt)
    prompt = build_agent_a_prompt(
        item_spec_content=raw_markdown,
        log_snippets=log_snippets
    )
    
    print(f"[OK] Built Agent A prompt ({len(prompt)} chars)")
    print(f"  - Injects: Section 1 (Parsing Logic) + Section 4.1 (Data Source)")
    
    # Save inputs to cache
    cache.save_stage_output(item_id, "agent_a_input", {
        "timestamp": datetime.now().isoformat(),
        "prompt": prompt,
        "model": model,
        "log_snippets_count": len(log_snippets)
    })
    
    # Initialize LLM client
    config = LLMConfig(
        provider="jedai",
        model=model,
        temperature=0.2,
        max_tokens=4096
    )
    
    client = LLMClient(config)
    
    print(f"[...] Invoking {model} via JEDAI...")
    start_time = datetime.now()
    
    response = client.invoke(prompt)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"[OK] Response received in {elapsed:.2f}s ({len(response)} chars)")
    
    # Print formatted I/O
    print_formatted_prompt("Agent A", prompt)
    print_formatted_response("Agent A", response)
    
    # Save as Markdown files
    if output_dir:
        save_io_as_markdown(
            output_dir=str(output_dir),
            item_id=item_id,
            stage="agent_a",
            prompt=prompt,
            response=response,
            iteration=0  # First iteration
        )
    
    # Parse response
    atom_a_code, reasoning = parse_agent_response(response)
    
    print(f"[OK] Parsed Atom A code ({len(atom_a_code)} chars)")
    
    # Save outputs to cache
    cache.save_stage_output(item_id, "agent_a_output", {
        "timestamp": datetime.now().isoformat(),
        "response": response,
        "atom_a_code": atom_a_code,
        "reasoning": reasoning,
        "elapsed_seconds": elapsed
    })
    
    return atom_a_code


def run_agent_b(item_spec: Dict[str, Any], atom_a_code: str, 
                model: str, cache: FileSystemCache, output_dir: Path = None) -> tuple:
    """
    Run Agent B: Generate validate_logic & check_existence functions
    
    Agent B receives: Section 2 (Check Logic) + Section 3 (Waiver Logic) + Section 4.2 (Special Scenarios)
    """
    print("\n" + "="*60)
    print("Step 5: Agent B - Generate validate_logic & check_existence")
    print("="*60)
    
    from llm_client import LLMClient
    from state import LLMConfig
    from prompts import build_agent_b_prompt, parse_agent_b_response
    
    item_id = item_spec.get("_item_id", "unknown")
    raw_markdown = item_spec.get("_raw_markdown", "")
    
    # Build prompt using raw Markdown (section parsing happens in build_agent_b_prompt)
    prompt = build_agent_b_prompt(
        item_spec_content=raw_markdown,
        atom_a_code=atom_a_code
    )
    
    print(f"[OK] Built Agent B prompt ({len(prompt)} chars)")
    print(f"  - Injects: Section 2 (Check) + Section 3 (Waiver) + Section 4.2 (Scenarios)")
    
    # Save inputs to cache
    cache.save_stage_output(item_id, "agent_b_input", {
        "timestamp": datetime.now().isoformat(),
        "prompt": prompt,
        "model": model,
        "atom_a_code_length": len(atom_a_code)
    })
    
    # Initialize LLM client
    config = LLMConfig(
        provider="jedai",
        model=model,
        temperature=0.1,
        max_tokens=4096
    )
    
    client = LLMClient(config)
    
    print(f"[...] Invoking {model} via JEDAI...")
    start_time = datetime.now()
    
    response = client.invoke(prompt)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"[OK] Response received in {elapsed:.2f}s ({len(response)} chars)")
    
    # Print formatted I/O
    print_formatted_prompt("Agent B", prompt)
    print_formatted_response("Agent B", response)
    
    # Save as Markdown files
    if output_dir:
        save_io_as_markdown(
            output_dir=str(output_dir),
            item_id=item_id,
            stage="agent_b",
            prompt=prompt,
            response=response,
            iteration=0  # First iteration
        )
    
    # Parse response
    atom_b_code, atom_c_code, yaml_config, reasoning = parse_agent_b_response(response)
    
    print(f"[OK] Parsed Atom B code ({len(atom_b_code)} chars)")
    print(f"[OK] Parsed Atom C code ({len(atom_c_code)} chars)")
    print(f"[OK] Parsed YAML config ({len(yaml_config)} chars)")
    
    # Save outputs to cache
    cache.save_stage_output(item_id, "agent_b_output", {
        "timestamp": datetime.now().isoformat(),
        "response": response,
        "atom_b_code": atom_b_code,
        "atom_c_code": atom_c_code,
        "yaml_config": yaml_config,
        "reasoning": reasoning,
        "elapsed_seconds": elapsed
    })
    
    return atom_b_code, atom_c_code, yaml_config


def run_validation(atom_a_code: str, atom_b_code: str, atom_c_code: str,
                   yaml_config: str, item_id: str, cache: FileSystemCache,
                   output_dir: Path = None) -> Dict[str, Any]:
    """
    Run validation on generated code
    
    Generic implementation - no hardcoded item references
    """
    print("\n" + "="*60)
    print("Step 6: Validating Generated Code")
    print("="*60)
    
    from validator import validate_10_2_compliance
    
    # Combine all code for validation
    combined_code = f"{atom_a_code}\n\n{atom_b_code}\n\n{atom_c_code}"
    
    result = validate_10_2_compliance(combined_code, yaml_config)
    
    # Print formatted validation results
    print_formatted_validation(result['gate_results'], result['errors'])
    
    # Save as Markdown file
    if output_dir:
        save_io_as_markdown(
            output_dir=str(output_dir),
            item_id=item_id,
            stage="validation",
            gate_results=result['gate_results'],
            errors=result['errors'],
            iteration=0  # First iteration
        )
    
    # Save validation results to cache
    cache.save_stage_output(item_id, "validation", {
        "timestamp": datetime.now().isoformat(),
        "valid": result['valid'],
        "gate_results": result['gate_results'],
        "errors": result['errors']
    })
    
    return result


def save_outputs(item_id: str, output_dir: Path, model: str,
                 atom_a_code: str, atom_b_code: str, atom_c_code: str,
                 yaml_config: str, validation_result: Dict[str, Any]):
    """
    Save generated code and reports to output directory
    
    Generic implementation - uses item_id for file naming
    """
    print("\n" + "="*60)
    print("Step 7: Saving Outputs")
    print("="*60)
    
    output_path = output_dir / "output"
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    header = f"""# Generated by Developer Agent
# Item ID: {item_id}
# Model: {model}
# Generated at: {timestamp}

"""
    
    # Save Atom A
    atom_a_file = output_path / f"atom_a_{item_id}.py"
    with open(atom_a_file, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(atom_a_code)
    print(f"[OK] Saved Atom A to: {atom_a_file}")
    
    # Save Atom B
    atom_b_file = output_path / f"atom_b_{item_id}.py"
    with open(atom_b_file, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(atom_b_code)
    print(f"[OK] Saved Atom B to: {atom_b_file}")
    
    # Save Atom C
    atom_c_file = output_path / f"atom_c_{item_id}.py"
    with open(atom_c_file, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(atom_c_code)
    print(f"[OK] Saved Atom C to: {atom_c_file}")
    
    # Save YAML config
    if yaml_config:
        yaml_file = output_path / f"config_{item_id}.yaml"
        with open(yaml_file, 'w', encoding='utf-8') as f:
            f.write(f"# Generated by Developer Agent\n")
            f.write(f"# Item ID: {item_id}\n")
            f.write(f"# Generated at: {timestamp}\n\n")
            f.write(yaml_config)
        print(f"[OK] Saved YAML config to: {yaml_file}")
    
    # Save validation report
    report_file = output_path / f"validation_report_{item_id}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"Validation Report for {item_id}\n")
        f.write(f"Generated at: {timestamp}\n")
        f.write(f"Model: {model}\n")
        f.write("="*60 + "\n\n")
        f.write(f"Valid: {validation_result['valid']}\n\n")
        f.write(f"Gate Results:\n")
        for gate, passed in validation_result['gate_results'].items():
            f.write(f"  - {gate}: {passed}\n")
        f.write(f"\nErrors:\n")
        for err in validation_result['errors']:
            f.write(f"  - {err}\n")
    print(f"[OK] Saved validation report to: {report_file}")


def list_available_models():
    """List all available models"""
    print("Available Models:")
    print("="*60)
    for model_id, model_desc in AVAILABLE_MODELS:
        marker = " [DEFAULT]" if model_id == DEFAULT_MODEL else ""
        print(f"  {model_id:30s} - {model_desc}{marker}")
    print("="*60)
    print(f"\nUsage: python test_real_jedai.py --item <path> --model <model_name>")


def main():
    """Run real JEDAI test with generic ItemSpec"""
    parser = argparse.ArgumentParser(
        description='Developer Agent - Real JEDAI Test (Generic)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_real_jedai.py --item "path/to/IMP-10-0-0-00.yaml"
  python test_real_jedai.py --item "path/to/ANY_ITEM.yaml" --model azure-gpt-4o
  python test_real_jedai.py --list-models
        """
    )
    parser.add_argument('--item', '-i', type=str,
                       help='Path to ItemSpec file (YAML or Markdown)')
    parser.add_argument('--model', '-m', type=str, default=DEFAULT_MODEL,
                       help=f'LLM model to use (default: {DEFAULT_MODEL})')
    parser.add_argument('--list-models', '-l', action='store_true',
                       help='List available models and exit')
    parser.add_argument('--output-dir', '-o', type=str, default=str(DEFAULT_OUTPUT_DIR),
                       help='Output directory for generated files')
    parser.add_argument('--log-dir', type=str, default=None,
                       help='Override log file search directory')
    parser.add_argument('--resume', '-r', type=str, default=None,
                       help='Resume from cache for specified item_id')
    
    args = parser.parse_args()
    
    # List models if requested
    if args.list_models:
        list_available_models()
        return
    
    # Require --item unless resuming
    if not args.item and not args.resume:
        parser.error("--item is required (or use --resume to continue from cache)")
    
    # Configuration
    selected_model = args.model
    output_dir = Path(args.output_dir)
    
    print("="*60)
    print("Developer Agent - Real JEDAI Test")
    print("="*60)
    print(f"Model: {selected_model}")
    print(f"Output: {output_dir}")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)
    
    try:
        # Step 1: Test JEDAI connection
        test_jedai_connection(selected_model)
        
        # Step 2: Load ItemSpec
        item_spec = load_item_spec(args.item)
        item_id = item_spec["_item_id"]
        
        # Setup output directories
        paths = setup_output_dirs(output_dir, item_id)
        
        # Initialize cache
        cache = FileSystemCache(str(paths["cache"]))
        
        # Step 3: Load log samples
        log_snippets = load_log_samples(item_spec, args.log_dir)
        
        if not log_snippets:
            print("\n[WARN] No log samples found, proceeding with empty snippets")
        
        # Step 4: Agent A generation
        atom_a_code = run_agent_a(item_spec, log_snippets, selected_model, cache, paths["base"])
        
        # Step 5: Agent B generation
        atom_b_code, atom_c_code, yaml_config = run_agent_b(
            item_spec, atom_a_code, selected_model, cache, paths["base"]
        )
        
        # Step 6: Validation
        validation_result = run_validation(
            atom_a_code, atom_b_code, atom_c_code, yaml_config, item_id, cache, paths["base"]
        )
        
        # Step 7: Save outputs (Python files and reports)
        save_outputs(
            item_id, paths["base"], selected_model,
            atom_a_code, atom_b_code, atom_c_code, yaml_config, validation_result
        )
        
        # Summary
        print("\n" + "="*60)
        print("Test Summary")
        print("="*60)
        print(f"[OK] Item ID: {item_id}")
        print(f"[OK] Model used: {selected_model}")
        print(f"[OK] Generated files saved to: {paths['output']}")
        print(f"[OK] Markdown files saved to: {paths['base'] / item_id / 'markdown'}")
        print(f"[OK] Cache saved to: {paths['cache']}")
        print(f"[OK] Validation result: {'PASS' if validation_result['valid'] else 'FAIL'}")
        
        # Show gate results summary
        passed = sum(1 for v in validation_result['gate_results'].values() if v)
        total = len(validation_result['gate_results'])
        print(f"[OK] Gates passed: {passed}/{total}")
        print("="*60)
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
