"""
Main Entry Point Example - Complete Pipeline Demonstration

This demonstrates how to use the L0-L6 framework with custom Atom A/B/C functions.
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add all layers to path
work_dir = Path(__file__).parent
for layer in ['L0_Config', 'L1_IO', 'L2_Parsing', 'L3_Check', 'L4_Waiver', 'L5_Output', 'L6_Report']:
    sys.path.insert(0, str(work_dir / layer))

# Import framework layers
from config_validator import validate_and_normalize_config, determine_type
from io_engine import read_file_content
from parsing_orchestrator import orchestrate_parsing
from check_assembler import assemble_check
from waiver_engine import apply_waiver_rules
from output_controller import filter_output_keys
from log_formatter import generate_log_file, generate_summary_dict
from yaml_generator import generate_summary_yaml


# ============================================================================
# Example Atom Functions (User-provided implementations)
# ============================================================================

def example_atom_a(text: str) -> List[Dict[str, Any]]:
    """
    Example Atom A: Extract items from text
    
    This example extracts lines containing "RULE:" prefix
    Format: RULE: <rule_name> [optional_fields]
    """
    items = []
    for line_num, line in enumerate(text.split('\n'), 1):
        line = line.strip()
        if line.startswith('RULE:'):
            # Parse: RULE: rule_name [key=value, ...]
            match = re.match(r'RULE:\s*(\S+)\s*(?:\[(.*)\])?', line)
            if match:
                rule_name = match.group(1)
                fields_str = match.group(2) or ''
                
                # Parse optional fields
                parsed_fields = {}
                if fields_str:
                    for field in fields_str.split(','):
                        if '=' in field:
                            key, value = field.split('=', 1)
                            parsed_fields[key.strip()] = value.strip()
                
                items.append({
                    'value': rule_name,
                    'line_number': line_num,
                    'matched_content': line,
                    'parsed_fields': parsed_fields
                })
    
    return items


def example_atom_b(
    text: str,
    pattern: str,
    parsed_fields: Optional[Dict] = None,
    default_match: str = "contains",
    regex_mode: str = "search"
) -> Dict[str, Any]:
    """
    Example Atom B: Validate text against pattern
    
    Implements the locked semantics from Plan.txt:
    - Alternatives > Regex > Wildcard > Default
    - Case-sensitive matching
    """
    if parsed_fields is None:
        parsed_fields = {}
    
    # 1. Check alternatives (highest precedence)
    if '|' in pattern:
        alternatives = [alt.strip() for alt in pattern.split('|') if alt.strip()]
        for alt in alternatives:
            if alt == text:
                return {
                    'is_match': True,
                    'reason': f"Matched alternative: {alt}"
                }
        return {
            'is_match': False,
            'reason': "No alternative matched"
        }
    
    # 2. Check regex (if pattern contains regex chars)
    regex_chars = r'[\[\](){}*+?.^$\\]'
    if re.search(regex_chars, pattern):
        try:
            if regex_mode == "match":
                match = re.match(pattern, text)
            else:  # search
                match = re.search(pattern, text)
            
            if match:
                return {
                    'is_match': True,
                    'reason': f"Regex matched: {pattern}"
                }
            else:
                return {
                    'is_match': False,
                    'reason': "Regex no match"
                }
        except re.error as e:
            return {
                'is_match': False,
                'reason': f"Invalid Regex: {str(e)}"
            }
    
    # 3. Default matching (contains or exact)
    if default_match == "exact":
        is_match = (text == pattern)
    else:  # contains
        is_match = (pattern in text)
    
    return {
        'is_match': is_match,
        'reason': f"Default {default_match} match"
    }


def example_atom_c(parsed_items: List[Dict]) -> Dict[str, Any]:
    """
    Example Atom C: Check existence
    
    Simple existence check: at least one item found
    """
    if len(parsed_items) > 0:
        return {
            'is_match': True,
            'evidence': parsed_items
        }
    else:
        return {
            'is_match': False,
            'evidence': []
        }


# ============================================================================
# Main Pipeline
# ============================================================================

def run_checker(
    requirements: Dict[str, Any],
    waivers: Dict[str, Any],
    input_files: List[str],
    item_id: str,
    description: str,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Run complete checker pipeline
    
    Args:
        requirements: {'value': int|str|None, 'pattern_items': List[str]}
        waivers: {'value': int|str|None, 'waive_items': List[str]}
        input_files: List of input file paths
        item_id: Checker ID (e.g., "IMP-10-0-0-00")
        description: Checker description
        output_dir: Output directory for reports
        
    Returns:
        Final output dict (L5 output)
    """
    print(f"\n{'='*80}")
    print(f"Running Checker: {item_id}")
    print(f"Description: {description}")
    print('='*80)
    
    # L0: Config normalization
    print("\n[L0] Normalizing configuration...")
    config = validate_and_normalize_config(
        requirements=requirements,
        waivers=waivers,
        input_files=input_files,
        description=description
    )
    type_id = determine_type(config['req_value'], config['waiver_value'])
    print(f"  Type: {type_id}")
    print(f"  req_value: {config['req_value']}")
    print(f"  waiver_value: {config['waiver_value']}")
    print(f"  pattern_items: {len(config['pattern_items'])} patterns")
    
    # L2: Parsing (L1 IO is called internally)
    print("\n[L2] Parsing input files...")
    parsed_items_all, searched_files = orchestrate_parsing(
        input_files=config['input_files'],
        atom_a_func=example_atom_a,
        io_read_func=read_file_content
    )
    print(f"  Parsed items: {len(parsed_items_all)}")
    print(f"  Searched files: {len(searched_files)}")
    
    # L3: Check assembly
    print("\n[L3] Assembling check...")
    check_result = assemble_check(
        requirements=config,
        parsed_items_all=parsed_items_all,
        searched_files=searched_files,
        atom_b_func=example_atom_b,
        atom_c_func=example_atom_c,
        description=config['description']
    )
    print(f"  Status (before waiver): {check_result['status']}")
    print(f"  Found: {len(check_result.get('found_items', []))}")
    print(f"  Missing: {len(check_result.get('missing_items', []))}")
    print(f"  Extra: {len(check_result.get('extra_items', []))}")
    
    # L4: Waiver (if applicable)
    if type_id in [3, 4]:
        print("\n[L4] Applying waiver rules...")
        check_result = apply_waiver_rules(
            check_result=check_result,
            waive_items=config['waive_items'],
            waiver_value=config['waiver_value'],
            type_id=type_id,
            atom_b_func=example_atom_b
        )
        print(f"  Status (after waiver): {check_result['status']}")
        print(f"  Waived: {len(check_result.get('waived', []))}")
        print(f"  Unused waivers: {len(check_result.get('unused_waivers', []))}")
    
    # L5: Output filtering
    print("\n[L5] Filtering output keys...")
    final_output = filter_output_keys(check_result, type_id=type_id)
    print(f"  Output keys: {set(final_output.keys())}")
    
    # L6: Report generation
    print("\n[L6] Generating reports...")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate log file
    log_path = output_dir / f"{item_id}.log"
    generate_log_file(
        l5_output=final_output,
        type_id=type_id,
        item_id=item_id,
        item_desc=description,
        output_path=log_path
    )
    print(f"  Log: {log_path}")
    
    # Generate summary YAML
    summary_dict = generate_summary_dict(
        l5_output=final_output,
        type_id=type_id,
        item_id=item_id,
        item_desc=description
    )
    yaml_path = output_dir / f"{item_id}_summary.yaml"
    generate_summary_yaml(summary_dict, item_id, yaml_path)
    print(f"  YAML: {yaml_path}")
    
    print(f"\n{'='*80}")
    print(f"Final Status: {final_output['status']}")
    print('='*80 + '\n')
    
    return final_output


# ============================================================================
# Example Usage
# ============================================================================

def main():
    """Example: Run a Type 2 checker with pattern requirements"""
    import tempfile
    
    # Create example input file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.rpt') as f:
        f.write("""
Design Rules Report
===================

RULE: setup_violation [severity=error]
RULE: hold_violation [severity=error]
RULE: max_transition [severity=warning]

End of Report
""")
        test_file = f.name
    
    try:
        # Define requirements
        requirements = {
            'value': 3,  # Expect 3 rules
            'pattern_items': [
                'setup_violation',
                'hold_violation',
                'max_fanout'  # This one is missing
            ]
        }
        
        # Define waivers (none for Type 2)
        waivers = {
            'value': None,
            'waive_items': []
        }
        
        # Run checker
        output_dir = Path('example_output')
        result = run_checker(
            requirements=requirements,
            waivers=waivers,
            input_files=[test_file],
            item_id="EXAMPLE-01",
            description="Example design rule checker",
            output_dir=output_dir
        )
        
        # Display result
        print("Result Summary:")
        print(f"  Status: {result['status']}")
        print(f"  Found: {len(result['found_items'])} items")
        print(f"  Missing: {len(result['missing_items'])} items")
        print(f"  Extra: {len(result.get('extra_items', []))} items")
        
        if result['missing_items']:
            print("\nMissing patterns:")
            for item in result['missing_items']:
                print(f"  - {item['expected']}")
        
        if result.get('extra_items'):
            print("\nExtra items:")
            for item in result['extra_items']:
                print(f"  - {item['value']}")
        
    finally:
        Path(test_file).unlink()


if __name__ == '__main__':
    main()
