"""
Integration Test: End-to-End Pipeline Test
Tests the complete flow from L0 to L6
"""

import sys
from pathlib import Path
import tempfile

# Add all layer directories to path
work_dir = Path(__file__).parent
for layer in ['L0_Config', 'L1_IO', 'L2_Parsing', 'L3_Check', 'L4_Waiver', 'L5_Output', 'L6_Report']:
    sys.path.insert(0, str(work_dir / layer))

# Import all layers
from config_validator import validate_and_normalize_config, determine_type, ConfigError
from io_engine import read_file_content, normalize_path
from parsing_orchestrator import orchestrate_parsing
from check_assembler import assemble_check
from waiver_engine import apply_waiver_rules
from output_controller import filter_output_keys
from log_formatter import generate_log_file, generate_summary_dict
from yaml_generator import generate_summary_yaml


def test_type1_existence_pass():
    """
    测试Type 1: Existence check PASS
    req.value = N/A, waiver.value = N/A
    """
    print("\n" + "="*80)
    print("Test: Type 1 Existence Check - PASS")
    print("="*80)
    
    # L0: Config normalization
    requirements = {'value': None, 'pattern_items': []}
    waivers = {'value': None, 'waive_items': []}
    
    # Create test file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.rpt') as f:
        f.write("test content line 1\n")
        f.write("important data line 2\n")
        test_file = f.name
    
    try:
        config = validate_and_normalize_config(
            requirements=requirements,
            waivers=waivers,
            input_files=[test_file],
            description="Type1 test checker"
        )
        
        type_id = determine_type(config['req_value'], config['waiver_value'])
        print(f"✓ L0: Type determined = {type_id}")
        assert type_id == 1
        
        # Mock Atom A (parser)
        def mock_atom_a(text, source_file):
            return [
                {
                    'value': 'important data',
                    'line_number': 2,
                    'matched_content': 'important data line 2',
                    'parsed_fields': {},
                    'source_file': source_file
                }
            ]
        
        # Mock IO read
        def mock_io_read(path):
            with open(path, 'r') as f:
                return f.read(), Path(path).resolve().as_posix()
        
        # L2: Parsing
        parsed_items_all, searched_files = orchestrate_parsing(
            input_files=config['input_files'],
            atom_a_func=mock_atom_a,
            io_read_func=mock_io_read
        )
        print(f"✓ L2: Parsed {len(parsed_items_all)} items from {len(searched_files)} files")
        
        # Mock Atom C (existence checker)
        def mock_atom_c(items):
            return {
                'is_match': True,  # Found
                'evidence': items
            }
        
        # Mock Atom B (not used in Type 1)
        def mock_atom_b(text, pattern, parsed_fields, default_match, regex_mode):
            return {'is_match': False}
        
        # L3: Check
        check_result = assemble_check(
            requirements=config,
            parsed_items_all=parsed_items_all,
            searched_files=searched_files,
            atom_b_func=mock_atom_b,
            atom_c_func=mock_atom_c,
            description=config['description']
        )
        print(f"✓ L3: Check status = {check_result['status']}")
        assert check_result['status'] == 'PASS'
        assert len(check_result['found_items']) == 1
        
        # L4: Waiver (Type 1 doesn't go through waiver)
        # Skip for Type 1
        
        # L5: Output filter
        final_output = filter_output_keys(check_result, type_id=type_id)
        print(f"✓ L5: Output keys = {set(final_output.keys())}")
        assert set(final_output.keys()) == {'status', 'found_items', 'missing_items'}
        
        # L6: Report generation
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            generate_log_file(
                l5_output=final_output,
                type_id=type_id,
                item_id="TEST-TYPE1-01",
                item_desc="Type1 existence test",
                output_path=log_path
            )
            print(f"✓ L6: Log file generated at {log_path}")
            assert log_path.exists()
            
            # Check log content
            log_content = log_path.read_text()
            assert "Status: PASS" in log_content
            assert "Found Items (1)" in log_content
        
        print("\n✅ Type 1 test PASSED\n")
        
    finally:
        Path(test_file).unlink()


def test_type2_pattern_with_missing():
    """
    测试Type 2: Pattern check with missing items
    req.value >= 1, waiver.value = N/A
    """
    print("\n" + "="*80)
    print("Test: Type 2 Pattern Check - FAIL (missing items)")
    print("="*80)
    
    # L0: Config
    requirements = {
        'value': 3,
        'pattern_items': ['pattern1', 'pattern2', 'pattern3']
    }
    waivers = {'value': None, 'waive_items': []}
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.rpt') as f:
        f.write("pattern1 found\n")
        f.write("pattern2 found\n")
        # pattern3 missing
        test_file = f.name
    
    try:
        config = validate_and_normalize_config(
            requirements=requirements,
            waivers=waivers,
            input_files=[test_file],
            description="Type2 test"
        )
        
        type_id = determine_type(config['req_value'], config['waiver_value'])
        print(f"✓ L0: Type = {type_id}, req_value = {config['req_value']}")
        assert type_id == 2
        
        # Mock Atom A
        def mock_atom_a(text, source_file):
            items = []
            for line_num, line in enumerate(text.split('\n'), 1):
                if 'pattern' in line:
                    items.append({
                        'value': line.strip(),
                        'line_number': line_num,
                        'matched_content': line.strip(),
                        'parsed_fields': {},
                        'source_file': source_file
                    })
            return items
        
        def mock_io_read(path):
            with open(path, 'r') as f:
                return f.read(), Path(path).resolve().as_posix()
        
        # L2: Parsing
        parsed_items_all, searched_files = orchestrate_parsing(
            input_files=config['input_files'],
            atom_a_func=mock_atom_a,
            io_read_func=mock_io_read
        )
        print(f"✓ L2: Parsed {len(parsed_items_all)} items")
        
        # Mock Atom B (contains matching)
        def mock_atom_b(text, pattern, parsed_fields, default_match, regex_mode):
            return {'is_match': pattern in text}
        
        def mock_atom_c(items):
            return {'is_match': False, 'evidence': []}
        
        # L3: Check
        check_result = assemble_check(
            requirements=config,
            parsed_items_all=parsed_items_all,
            searched_files=searched_files,
            atom_b_func=mock_atom_b,
            atom_c_func=mock_atom_c,
            description=config['description']
        )
        print(f"✓ L3: Status = {check_result['status']}")
        print(f"   Found = {len(check_result['found_items'])}, Missing = {len(check_result['missing_items'])}")
        
        assert check_result['status'] == 'FAIL'
        assert len(check_result['found_items']) == 2  # pattern1, pattern2
        assert len(check_result['missing_items']) == 1  # pattern3
        assert check_result['missing_items'][0]['expected'] == 'pattern3'
        
        # L5: Output
        final_output = filter_output_keys(check_result, type_id=type_id)
        print(f"✓ L5: Output filtered")
        
        # L6: Summary
        summary = generate_summary_dict(
            l5_output=final_output,
            type_id=type_id,
            item_id="TEST-TYPE2-01",
            item_desc="Type2 pattern test"
        )
        print(f"✓ L6: Summary generated, failures = {len(summary['failures'])}")
        
        print("\n✅ Type 2 test PASSED\n")
        
    finally:
        Path(test_file).unlink()


def test_type3_selective_waiver():
    """
    测试Type 3: Selective waiver
    req.value >= 1, waiver.value >= 0
    """
    print("\n" + "="*80)
    print("Test: Type 3 Selective Waiver")
    print("="*80)
    
    requirements = {
        'value': 2,
        'pattern_items': ['pattern1', 'pattern2']
    }
    waivers = {
        'value': 1,
        'waive_items': ['pattern2']  # Waive pattern2
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.rpt') as f:
        f.write("pattern1 found\n")
        # pattern2 missing, but will be waived
        test_file = f.name
    
    try:
        config = validate_and_normalize_config(
            requirements=requirements,
            waivers=waivers,
            input_files=[test_file],
            description="Type3 waiver test"
        )
        
        type_id = determine_type(config['req_value'], config['waiver_value'])
        print(f"✓ L0: Type = {type_id}, waiver_value = {config['waiver_value']}")
        assert type_id == 3
        
        def mock_atom_a(text, source_file):
            items = []
            for line_num, line in enumerate(text.split('\n'), 1):
                if 'pattern' in line:
                    items.append({
                        'value': line.strip(),
                        'line_number': line_num,
                        'matched_content': line.strip(),
                        'parsed_fields': {},
                        'source_file': source_file
                    })
            return items
        
        def mock_io_read(path):
            with open(path, 'r') as f:
                return f.read(), Path(path).resolve().as_posix()
        
        parsed_items_all, searched_files = orchestrate_parsing(
            input_files=config['input_files'],
            atom_a_func=mock_atom_a,
            io_read_func=mock_io_read
        )
        
        def mock_atom_b(text, pattern, parsed_fields, default_match, regex_mode):
            # Contains matching for check, exact for waiver
            if default_match == "contains":
                return {'is_match': pattern in text}
            else:  # exact
                return {'is_match': text == pattern}
        
        def mock_atom_c(items):
            return {'is_match': False, 'evidence': []}
        
        # L3: Check
        check_result = assemble_check(
            requirements=config,
            parsed_items_all=parsed_items_all,
            searched_files=searched_files,
            atom_b_func=mock_atom_b,
            atom_c_func=mock_atom_c,
            description=config['description']
        )
        print(f"✓ L3: Before waiver - Status = {check_result['status']}, Missing = {len(check_result['missing_items'])}")
        
        # L4: Apply waiver
        final_result = apply_waiver_rules(
            check_result=check_result,
            waive_items=config['waive_items'],
            waiver_value=config['waiver_value'],
            type_id=type_id,
            atom_b_func=mock_atom_b
        )
        print(f"✓ L4: After waiver - Missing = {len(final_result['missing_items'])}, Waived = {len(final_result['waived'])}")
        
        assert len(final_result['waived']) == 1
        assert final_result['waived'][0]['waiver_pattern'] == 'pattern2'
        
        # L5: Output
        final_output = filter_output_keys(final_result, type_id=type_id)
        print(f"✓ L5: Output filtered, keys = {set(final_output.keys())}")
        
        print("\n✅ Type 3 test PASSED\n")
        
    finally:
        Path(test_file).unlink()


def test_type4_global_waiver():
    """
    测试Type 4: Global waiver
    req.value = N/A, waiver.value >= 0
    """
    print("\n" + "="*80)
    print("Test: Type 4 Global Waiver")
    print("="*80)
    
    requirements = {'value': None, 'pattern_items': []}
    waivers = {
        'value': 0,  # Global waiver
        'waive_items': ['Global waiver comment']
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.rpt') as f:
        f.write("some content\n")
        test_file = f.name
    
    try:
        config = validate_and_normalize_config(
            requirements=requirements,
            waivers=waivers,
            input_files=[test_file],
            description="Type4 global waiver test"
        )
        
        type_id = determine_type(config['req_value'], config['waiver_value'])
        print(f"✓ L0: Type = {type_id}, waiver_value = {config['waiver_value']}")
        assert type_id == 4
        
        def mock_atom_a(text, source_file):
            return []  # No items found
        
        def mock_io_read(path):
            with open(path, 'r') as f:
                return f.read(), Path(path).resolve().as_posix()
        
        parsed_items_all, searched_files = orchestrate_parsing(
            input_files=config['input_files'],
            atom_a_func=mock_atom_a,
            io_read_func=mock_io_read
        )
        
        def mock_atom_b(text, pattern, parsed_fields, default_match, regex_mode):
            return {'is_match': False}
        
        def mock_atom_c(items):
            return {'is_match': False, 'evidence': []}  # Existence check fails
        
        # L3: Check
        check_result = assemble_check(
            requirements=config,
            parsed_items_all=parsed_items_all,
            searched_files=searched_files,
            atom_b_func=mock_atom_b,
            atom_c_func=mock_atom_c,
            description=config['description']
        )
        print(f"✓ L3: Before waiver - Status = {check_result['status']}")
        assert check_result['status'] == 'FAIL'
        
        # L4: Global waiver
        final_result = apply_waiver_rules(
            check_result=check_result,
            waive_items=config['waive_items'],
            waiver_value=config['waiver_value'],
            type_id=type_id,
            atom_b_func=mock_atom_b
        )
        print(f"✓ L4: After global waiver - Status = {final_result['status']}")
        
        # Global waiver: status forced to PASS, violations marked as INFO
        assert final_result['status'] == 'PASS'
        assert final_result['missing_items'][0]['severity'] == 'INFO'
        assert final_result['unused_waivers'] == []
        
        print("\n✅ Type 4 test PASSED\n")
        
    finally:
        Path(test_file).unlink()


if __name__ == '__main__':
    print("\n" + "="*80)
    print("INTEGRATION TEST SUITE: L0-L6 Pipeline")
    print("="*80)
    
    try:
        test_type1_existence_pass()
        test_type2_pattern_with_missing()
        test_type3_selective_waiver()
        test_type4_global_waiver()
        
        print("\n" + "="*80)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
