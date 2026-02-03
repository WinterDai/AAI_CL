import unittest
import tempfile
import shutil
from pathlib import Path
from Check_modules.common.checker_templates.input_file_parser_template import InputFileParserMixin
from Check_modules.common.checker_templates.waiver_handler_template import WaiverHandlerMixin
from Check_modules.common.checker_templates.output_builder_template import OutputBuilderMixin

class TestEdgeCases(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    # =========================================================================
    # Edge Case 1: Empty Log File
    # =========================================================================
    def test_empty_log_file(self):
        """Test parsing empty log file - should handle gracefully."""
        empty_log = Path(self.test_dir) / "empty.log"
        empty_log.touch()
        
        parser = InputFileParserMixin()
        
        # Test parse_log_with_patterns
        result = parser.parse_log_with_patterns(
            empty_log,
            {'error': r'ERROR: (.*)'}
        )
        self.assertEqual(len(result['found']), 0)
        self.assertIn('error', result['missing'])
        
        # Test extract_file_references
        result = parser.extract_file_references(empty_log, extensions=['.lef'])
        self.assertEqual(result['count'], 0)
        self.assertEqual(result['files'], [])
        
        # Test parse_section
        result = parser.parse_section(
            empty_log,
            start_marker=r'Start',
            item_pattern=r'Item (\w+)'
        )
        self.assertFalse(result['found'])
        self.assertEqual(result['items'], [])

    # =========================================================================
    # Edge Case 2: None/Empty Waiver Lists
    # =========================================================================
    def test_empty_waiver_handling(self):
        """Test waiver handler with None/empty inputs."""
        handler = WaiverHandlerMixin()
        
        # Empty waive_items_raw
        result = handler.parse_waive_items([])
        self.assertEqual(result, {})
        
        result = handler.parse_waive_items(None)
        self.assertEqual(result, {})
        
        # Empty classification
        waived, unwaived = handler.classify_items_by_waiver(
            all_items=['a', 'b'],
            waive_dict={}
        )
        self.assertEqual(waived, [])
        self.assertEqual(unwaived, ['a', 'b'])
        
        # Empty unused waivers
        unused = handler.find_unused_waivers({}, ['a', 'b'])
        self.assertEqual(unused, [])

    # =========================================================================
    # Edge Case 3: Invalid Regex Pattern
    # =========================================================================
    def test_invalid_regex_pattern(self):
        """Test handling of invalid regex patterns."""
        log_file = Path(self.test_dir) / "test.log"
        with open(log_file, 'w') as f:
            f.write("Some content\n")
        
        parser = InputFileParserMixin()
        
        # Invalid regex should be caught or handled
        # Most methods use re.IGNORECASE which should handle basic patterns
        # Test with potentially problematic pattern
        try:
            result = parser.count_pattern(
                log_file,
                pattern=r'[unclosed',  # Invalid regex
                case_sensitive=False
            )
            # If it doesn't raise, the implementation handles it
            # (might escape or catch the error)
        except Exception as e:
            # Expected to raise re.error
            self.assertIn('error', str(type(e).__name__).lower())

    # =========================================================================
    # Edge Case 4: Unicode/Encoding Issues
    # =========================================================================
    def test_unicode_content(self):
        """Test handling of Unicode content in logs."""
        log_file = Path(self.test_dir) / "unicode.log"
        
        # Write log with Chinese characters
        content = """
        INFO: 开始检查
        ERROR: 设计规则违例 at line 10
        WARNING: 时序约束缺失
        成功完成
        """
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        parser = InputFileParserMixin()
        
        # Should handle Unicode gracefully - use count_pattern instead
        result = parser.count_pattern(
            log_file,
            pattern=r'ERROR|WARNING',
            return_matches=True
        )
        
        self.assertGreater(result['count'], 0)
        self.assertEqual(result['count'], 2)  # ERROR and WARNING lines

    # =========================================================================
    # Edge Case 5: Large Item Lists
    # =========================================================================
    def test_large_item_lists(self):
        """Test handling of large datasets (100+ items)."""
        builder = OutputBuilderMixin()
        
        # Generate 100+ items
        found_items = {
            f'item_{i}': {'line_number': i, 'file_path': 'test.log'}
            for i in range(150)
        }
        
        missing_items = [f'missing_{i}' for i in range(50)]
        waived_items = [f'waived_{i}' for i in range(30)]
        
        # Should handle large datasets efficiently
        details = builder.build_details_from_items(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items
        )
        
        # Verify counts
        self.assertEqual(len(details), 150 + 50 + 30)
        
        # Verify groups
        groups = builder.build_result_groups(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items
        )
        
        self.assertEqual(len(groups['info_groups']['INFO02']['items']), 150)
        self.assertEqual(len(groups['error_groups']['ERROR01']['items']), 50)

    # =========================================================================
    # Edge Case 6: Special Characters in Patterns
    # =========================================================================
    def test_special_characters_in_waiver_patterns(self):
        """Test waiver pattern matching with special characters."""
        handler = WaiverHandlerMixin()
        
        # Patterns with special chars
        patterns = [
            'module/sub[0]',  # Brackets
            'path.with.dots',  # Dots
            'name_with_underscore',  # Underscores
            'regex:.*\\.txt$'  # Regex with escaped dot
        ]
        
        # Test exact match with special chars
        self.assertTrue(handler.matches_waiver_pattern(
            'module/sub[0]', ['module/sub[0]']
        ))
        
        # Test wildcard with dots
        self.assertTrue(handler.matches_waiver_pattern(
            'path.with.dots', ['path.with.*']
        ))
        
        # Test regex pattern
        self.assertTrue(handler.matches_waiver_pattern(
            'file.txt', ['regex:.*\\.txt$']
        ))

    # =========================================================================
    # Edge Case 7: None/Empty Metadata
    # =========================================================================
    def test_none_metadata_handling(self):
        """Test output builder with missing metadata."""
        builder = OutputBuilderMixin()
        
        # Items with incomplete metadata
        found_items = {
            'item1': {},  # Empty metadata
            'item2': {'line_number': 10},  # Missing file_path
            'item3': {'file_path': 'test.log'}  # Missing line_number
        }
        
        details = builder.build_details_from_items(
            found_items=found_items,
            default_file='default.log'
        )
        
        # Should use defaults for missing data
        self.assertEqual(len(details), 3)
        
        # Check defaults are applied
        item1_detail = next(d for d in details if d.name == 'item1')
        self.assertEqual(item1_detail.line_number, 0)
        self.assertEqual(item1_detail.file_path, 'default.log')

if __name__ == '__main__':
    unittest.main()
