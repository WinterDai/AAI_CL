import unittest
from unittest.mock import MagicMock, patch
from Check_modules.common.checker_templates.output_builder_template import OutputBuilderMixin
from output_formatter import DetailItem, Severity, CheckResult

class TestOutputBuilder(unittest.TestCase, OutputBuilderMixin):
    def test_extract_item_metadata(self):
        found_items = {
            'item1': {'line_number': 10, 'file_path': 'f1', 'line_content': 'c1'}
        }
        
        meta = self.extract_item_metadata('item1', found_items)
        self.assertEqual(meta['line_number'], 10)
        
        meta = self.extract_item_metadata('item2', found_items, default_file='def')
        self.assertEqual(meta['file_path'], 'def')
        self.assertEqual(meta['line_number'], 0)

    def test_extract_path_after_delimiter(self):
        metadata = {'line_content': 'Generating report > /path/to/report.rpt'}
        path = self.extract_path_after_delimiter('item', metadata)
        self.assertEqual(path, '/path/to/report.rpt')
        
        metadata = {'line_content': 'No delimiter here'}
        path = self.extract_path_after_delimiter('item', metadata)
        self.assertEqual(path, 'item')

    def test_extract_filename_from_path(self):
        metadata = {'line_content': 'Generating report > /path/to/report.rpt'}
        filename = self.extract_filename_from_path('item', metadata)
        self.assertEqual(filename, 'report.rpt')
        
        metadata = {'file_path': '/path/to/file.txt', 'line_content': ''}
        filename = self.extract_filename_from_path('item', metadata)
        self.assertEqual(filename, 'file.txt')

    def test_build_details_from_items(self):
        found_items = {'item1': {'line_number': 1}}
        missing_items = ['item2']
        waived_items = ['item3']
        unused_waivers = ['item4']
        waive_dict = {'item3': 'reason'}
        
        details = self.build_details_from_items(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict
        )
        
        self.assertEqual(len(details), 4)
        
        # Check severities
        severities = {d.name: d.severity for d in details}
        self.assertEqual(severities['item1'], Severity.INFO)
        self.assertEqual(severities['item2'], Severity.FAIL)
        self.assertEqual(severities['item3'], Severity.INFO)
        self.assertEqual(severities['item4'], Severity.WARN)
        
        # Check waiver reason
        waived_detail = next(d for d in details if d.name == 'item3')
        self.assertIn('[WAIVER]', waived_detail.reason)
        self.assertIn('reason', waived_detail.reason)

    def test_build_result_groups(self):
        found_items = {'item1': {}}
        missing_items = ['item2']
        waived_items = ['item3']
        unused_waivers = ['item4']
        
        groups = self.build_result_groups(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers
        )
        
        self.assertIn('INFO01', groups['info_groups']) # Waived
        self.assertIn('INFO02', groups['info_groups']) # Found
        self.assertIn('ERROR01', groups['error_groups']) # Missing
        self.assertIn('WARN01', groups['warn_groups']) # Unused
        
        self.assertEqual(groups['info_groups']['INFO01']['items'], ['item3'])
        self.assertEqual(groups['info_groups']['INFO02']['items'], ['item1'])

    def test_build_complete_output(self):
        found_items = {'item1': {}}
        missing_items = ['item2']
        
        # Mock create_check_result to avoid complex object creation if needed, 
        # but since we import real one, let's see if it works.
        # The real create_check_result returns a CheckResult object.
        
        result = self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            value=10
        )
        
        self.assertIsInstance(result, CheckResult)
        self.assertEqual(result.value, 10)
        self.assertFalse(result.is_pass)
        self.assertTrue(len(result.details) > 0)

if __name__ == '__main__':
    unittest.main()
