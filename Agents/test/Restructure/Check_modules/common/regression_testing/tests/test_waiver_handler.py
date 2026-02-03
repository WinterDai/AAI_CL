import unittest
from unittest.mock import MagicMock
from Check_modules.common.checker_templates.waiver_handler_template import WaiverHandlerMixin

class TestWaiverHandler(unittest.TestCase, WaiverHandlerMixin):
    def test_matches_waiver_pattern(self):
        # Exact match
        self.assertTrue(self.matches_waiver_pattern('item1', ['item1']))
        self.assertFalse(self.matches_waiver_pattern('item1', ['item2']))
        
        # Wildcard match
        self.assertTrue(self.matches_waiver_pattern('lib/cell', ['lib/*']))
        self.assertTrue(self.matches_waiver_pattern('test_123', ['test_*']))
        self.assertFalse(self.matches_waiver_pattern('other/cell', ['lib/*']))
        
        # Regex match
        self.assertTrue(self.matches_waiver_pattern('module_123', ['regex:module_\\d+']))
        self.assertFalse(self.matches_waiver_pattern('module_abc', ['regex:module_\\d+']))

    def test_parse_waive_items(self):
        # List format
        raw_list = ['item1', 'item2']
        result = self.parse_waive_items(raw_list)
        self.assertEqual(result, {'item1': '', 'item2': ''})
        
        # Dict format
        raw_dict = [{'name': 'item1', 'reason': 'r1'}, {'name': 'item2', 'reason': 'r2'}]
        result = self.parse_waive_items(raw_dict)
        self.assertEqual(result, {'item1': 'r1', 'item2': 'r2'})

    def test_classify_items_by_waiver(self):
        all_items = ['item1', 'item2', 'item3']
        waive_dict = {'item1': 'reason'}
        
        waived, unwaived = self.classify_items_by_waiver(all_items, waive_dict)
        
        self.assertEqual(waived, ['item1'])
        self.assertEqual(unwaived, ['item2', 'item3'])
        
        # With pattern matching
        all_items = ['lib/c1', 'lib/c2', 'other/c1']
        waive_dict = {'lib/*': ''}
        
        waived, unwaived = self.classify_items_by_waiver(all_items, waive_dict, use_pattern_matching=True)
        self.assertEqual(len(waived), 2)
        self.assertEqual(unwaived, ['other/c1'])

    def test_find_unused_waivers(self):
        waive_dict = {'item1': '', 'item2': ''}
        items_found = ['item1']
        
        unused = self.find_unused_waivers(waive_dict, items_found)
        self.assertEqual(unused, ['item2'])

    def test_format_waiver_reason(self):
        reason = self.format_waiver_reason('Base', 'Waiver', add_tag=True)
        self.assertEqual(reason, 'Base: Waiver[WAIVER]')
        
        reason = self.format_waiver_reason('Base', add_tag=True)
        self.assertEqual(reason, 'Base[WAIVER]')

    def test_get_waiver_value(self):
        # Mock get_waivers
        self.get_waivers = MagicMock(return_value={'value': 0})
        self.assertEqual(self.get_waiver_value(), 0)
        
        self.get_waivers = MagicMock(return_value={})
        self.assertEqual(self.get_waiver_value(default=1), 1)

    def test_apply_type1_type2_waiver(self):
        # Case 1: Waiver = 0 (Force PASS, INFO)
        self.get_waivers = MagicMock(return_value={'value': 0})
        is_pass, severity, reason = self.apply_type1_type2_waiver(
            is_pass_normal_mode=False,
            fail_reason="Fail",
            info_reason="Info"
        )
        self.assertTrue(is_pass)
        self.assertEqual(severity, 'INFO')
        self.assertIn('[WAIVED_AS_INFO]', reason)
        
        # Case 2: Waiver != 0, Normal PASS
        self.get_waivers = MagicMock(return_value={'value': 'N/A'})
        is_pass, severity, reason = self.apply_type1_type2_waiver(
            is_pass_normal_mode=True,
            fail_reason="Fail",
            info_reason="Info"
        )
        self.assertTrue(is_pass)
        self.assertEqual(severity, 'INFO')
        self.assertNotIn('[WAIVED_AS_INFO]', reason)
        
        # Case 3: Waiver != 0, Normal FAIL
        is_pass, severity, reason = self.apply_type1_type2_waiver(
            is_pass_normal_mode=False,
            fail_reason="Fail",
            info_reason="Info"
        )
        self.assertFalse(is_pass)
        self.assertEqual(severity, 'FAIL')

if __name__ == '__main__':
    unittest.main()
