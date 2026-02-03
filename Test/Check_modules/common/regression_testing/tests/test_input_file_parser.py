import unittest
import os
import tempfile
import shutil
from pathlib import Path
from Check_modules.common.checker_templates.input_file_parser_template import InputFileParserMixin

class TestInputFileParser(unittest.TestCase, InputFileParserMixin):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_file = Path(self.test_dir) / "test.log"
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_log_file(self, content):
        with open(self.log_file, 'w') as f:
            f.write(content)
        return self.log_file

    def test_parse_log_with_patterns(self):
        content = """
        INFO: Starting check
        ERROR: Design rule violation at line 10
        WARNING: Timing constraint missing
        INFO: Check completed
        """
        self.create_log_file(content)
        
        patterns = {
            'error': r'ERROR: (.*)',
            'warning': r'WARNING: (.*)',
            'missing': r'CRITICAL: (.*)'
        }
        
        results = self.parse_log_with_patterns(self.log_file, patterns)
        
        self.assertIn('error', results['found'])
        self.assertIn('warning', results['found'])
        self.assertIn('missing', results['missing'])
        
        # Verify extracted content
        # The parser returns metadata dict, not match object
        self.assertIn('Design rule violation', results['found']['error']['line_content'])
        self.assertIn('Timing constraint missing', results['found']['warning']['line_content'])

    def test_extract_file_references(self):
        content = """
        Reading file: design.lef
        Loading tech: tech.tlef
        """
        self.create_log_file(content)
        
        # extract_file_references returns a dict with 'files' key
        result = self.extract_file_references(self.log_file, extensions=['.lef', '.tlef'])
        
        self.assertIn('design.lef', result['files'])
        self.assertIn('tech.tlef', result['files'])
        self.assertEqual(len(result['files']), 2)

    def test_parse_section(self):
        content = """
        Start Section
        Item 1
        Item 2
        End Section
        """
        self.create_log_file(content)
        
        result = self.parse_section(
            self.log_file,
            start_marker=r'Start Section',
            end_marker=r'End Section',
            item_pattern=r'(Item \d+)'
        )
        
        self.assertTrue(result['found'])
        self.assertEqual(len(result['items']), 2)
        self.assertIn('Item 1', result['items'])

    def test_extract_command_blocks(self):
        content = """
        create_delay_corner -name corner1 -rc_corner rc1 @
        create_delay_corner -name corner2 -rc_corner rc2 @
        """
        self.create_log_file(content)
        
        # Renamed from parse_commands to extract_command_blocks
        result = self.extract_command_blocks(
            self.log_file,
            command='create_delay_corner',
            extract_params=['-name', '-rc_corner']
        )
        
        self.assertEqual(result['count'], 2)
        self.assertEqual(result['blocks'][0]['params']['-name'], 'corner1')
        self.assertEqual(result['blocks'][0]['params']['-rc_corner'], 'rc1')

    def test_extract_chain(self):
        content = """
        create_delay_corner -name corner1 -rc_corner rc1 @
        create_rc_corner -name rc1 -qrc_tech tech1 @
        """
        self.create_log_file(content)
        
        chain_spec = [
            {
                'in_command': 'create_delay_corner',
                'match_param': '-name',
                'extract_param': '-rc_corner'
            },
            {
                'in_command': 'create_rc_corner',
                'match_param': '-name',
                'extract_param': '-qrc_tech'
            }
        ]
        
        # Renamed from extract_chained_data to extract_chain
        result = self.extract_chain(
            [self.log_file],
            chain_spec,
            initial_values=['corner1']
        )
        
        self.assertEqual(result['corner1'], 'tech1')

    def test_extract_simple_list(self):
        content = """
        Header
        ---
        Item1
        Item2
        """
        self.create_log_file(content)
        
        # Renamed from parse_simple_list to extract_simple_list
        result = self.extract_simple_list(
            self.log_file,
            skip_patterns=[r'Header', r'---']
        )
        
        self.assertEqual(len(result['items']), 2)
        self.assertIn('Item1', result['items'])
        self.assertIn('Item2', result['items'])

if __name__ == '__main__':
    unittest.main()
