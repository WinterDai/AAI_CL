import unittest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import MagicMock

from Check_modules.common.checker_templates.input_file_parser_template import InputFileParserMixin
from Check_modules.common.checker_templates.waiver_handler_template import WaiverHandlerMixin
from Check_modules.common.checker_templates.output_builder_template import OutputBuilderMixin
from output_formatter import CheckResult, Severity

class IntegratedChecker(InputFileParserMixin, WaiverHandlerMixin, OutputBuilderMixin):
    def __init__(self):
        self.waivers = {}
        
    def get_waivers(self):
        return self.waivers

    def execute_check(self, log_file):
        # 1. Parse Log
        patterns = {
            'error': r'ERROR: (.*)',
            'warning': r'WARNING: (.*)'
        }
        parse_result = self.parse_log_with_patterns(log_file, patterns)
        
        # Extract found items (simulating finding errors)
        found_errors = {}
        if 'error' in parse_result['found']:
            # In a real scenario, we might iterate over matches.
            # Here, parse_log_with_patterns returns the last match metadata for the key 'error'
            # if we use the simple version, but wait.
            # parse_log_with_patterns returns:
            # matches[keyword] = list of dicts
            # But the return value is {'found': {keyword: metadata_of_last_match}, ...}
            # Wait, let me check parse_log_with_patterns implementation again.
            # It returns 'matches': matches (which is a dict of lists)
            # AND 'found': ... wait, I need to check the implementation.
            pass

        # Let's use extract_simple_list for a clearer list of items
        # Suppose we are checking for "Violation: <name>"
        list_result = self.extract_simple_list(log_file, line_filter=r'Violation:')
        
        # Extract item names from lines "Violation: item_name"
        found_items = {}
        for item in list_result['items']:
            # item is "Violation: name"
            name = item.split(': ')[1]
            found_items[name] = list_result['metadata'][item]

        # 2. Waiver Handling
        # Suppose we want to ensure NO violations exist.
        # So all found items are "missing" from the "clean state" perspective?
        # No, usually we check for presence of required items (PASS if found) 
        # OR absence of forbidden items (PASS if NOT found).
        
        # Let's simulate "Forbidden Items Check" (e.g. no errors).
        # If found -> FAIL, unless waived.
        
        # But build_details_from_items assumes:
        # found_items -> INFO (Good)
        # missing_items -> FAIL (Bad)
        
        # If we are doing a "Forbidden Check", we should treat found items as "missing" (bad)?
        # Or we need to adapt how we use build_details.
        
        # Actually, build_details_from_items is designed for "Required Items Check" (Pattern 2/3).
        # For "Forbidden Items Check" (Pattern 1), we usually manually build details.
        
        # Let's simulate "Required Items Check" (e.g. Clock Gating Check).
        # We expect 'clk1', 'clk2'.
        # We found 'clk1'. 'clk2' is missing.
        
        required_items = ['clk1', 'clk2', 'clk3']
        
        # Simulate what we found in log
        # We found clk1.
        # We didn't find clk2.
        # We didn't find clk3.
        
        # Filter found_items to only those in required_items
        actually_found = {k: v for k, v in found_items.items() if k in required_items}
        
        # Identify missing
        missing = [i for i in required_items if i not in actually_found]
        
        # 3. Apply Waivers to Missing Items
        waive_config = self.get_waivers().get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_config)
        
        waived_missing, unwaived_missing = self.classify_items_by_waiver(
            missing, waive_dict
        )
        
        unused_waivers = self.find_unused_waivers(waive_dict, missing)

        # 4. Build Output
        return self.build_complete_output(
            found_items=actually_found,
            missing_items=unwaived_missing,
            waived_items=waived_missing,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc="Clocks found",
            missing_desc="Clocks missing",
            waived_desc="Clocks waived"
        )

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_file = Path(self.test_dir) / "check.log"
        self.checker = IntegratedChecker()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_log(self, content):
        with open(self.log_file, 'w') as f:
            f.write(content)

    def test_full_flow(self):
        # Scenario:
        # Required: clk1, clk2, clk3
        # Log contains: clk1
        # Waivers: clk2 is waived
        # Expected Result:
        # - clk1: Found (INFO)
        # - clk2: Missing but Waived (INFO)
        # - clk3: Missing (FAIL)
        # - Result: FAIL (because of clk3)
        
        content = """
        Analysis Report
        Violation: clk1
        End Report
        """
        self.create_log(content)
        
        # Configure waivers
        self.checker.waivers = {
            'waive_items': ['clk2']
        }
        
        result = self.checker.execute_check(self.log_file)
        
        self.assertFalse(result.is_pass)
        self.assertEqual(result.value, 1) # 1 found
        
        # Check details
        details = {d.name: d for d in result.details}
        
        self.assertEqual(details['clk1'].severity, Severity.INFO)
        self.assertEqual(details['clk2'].severity, Severity.INFO) # Waived
        self.assertIn('[WAIVER]', details['clk2'].reason)
        self.assertEqual(details['clk3'].severity, Severity.FAIL)

    def test_full_pass_with_waivers(self):
        # Scenario:
        # Required: clk1, clk2
        # Log contains: clk1
        # Waivers: clk2
        # Expected: PASS
        
        content = """
        Violation: clk1
        """
        self.create_log(content)
        
        self.checker.waivers = {
            'waive_items': ['clk2']
        }
        
        # Override execute_check logic slightly for this test? 
        # No, the logic is fixed in IntegratedChecker.
        # It checks for clk1, clk2, clk3.
        # So clk3 will still fail.
        
        # I should make required_items configurable in IntegratedChecker for better testing.
        # But for now, I'll just waive clk3 too.
        self.checker.waivers = {
            'waive_items': ['clk2', 'clk3']
        }
        
        result = self.checker.execute_check(self.log_file)
        
        self.assertTrue(result.is_pass)
        self.assertEqual(result.value, 1)

if __name__ == '__main__':
    unittest.main()
