"""
Developer Agent - Unit Tests
Tests individual components in isolation
"""
import unittest
import os
import sys
import tempfile
import shutil
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import AgentState, AgentConfig, LLMConfig, create_initial_state, generate_item_id
from cache import FileSystemCache, resume_from_checkpoint
from tools import (
    extract_file_patterns_from_spec_content,
    extract_file_patterns_from_spec,
    extract_keywords_from_spec,
    parse_item_spec,
    extract_log_snippet
)
from validator import (
    validate_10_2_compliance,
    determine_error_source,
    validate_atom_a_only,
    validate_atom_b_only
)
from prompts import (
    build_agent_a_prompt,
    build_agent_b_prompt,
    build_reflect_prompt,
    parse_agent_response,
    parse_agent_b_response
)
# MockLLMClient removed - using real JEDAI calls only


class TestState(unittest.TestCase):
    """Test state.py module"""
    
    def test_create_initial_state(self):
        """Test creating initial state"""
        state = create_initial_state("test_item.md")
        
        self.assertEqual(state["item_spec_path"], "test_item.md")
        self.assertEqual(state["current_stage"], "init")
        self.assertEqual(state["iteration_count"], 0)
        self.assertIsInstance(state["discovered_log_files"], list)
        self.assertIsInstance(state["validation_errors"], list)
    
    def test_generate_item_id(self):
        """Test item ID generation"""
        # Test with ItemSpec suffix
        self.assertEqual(
            generate_item_id("IMP-10-0-0-00_ItemSpec.md"),
            "IMP-10-0-0-00"
        )
        
        # Test with .md only
        self.assertEqual(
            generate_item_id("IMP-10-0-0-00.md"),
            "IMP-10-0-0-00"
        )
        
        # Test with path separators
        self.assertEqual(
            generate_item_id("items/IMP-10-0-0-00_ItemSpec.md"),
            "IMP-10-0-0-00"
        )


class TestCache(unittest.TestCase):
    """Test cache.py module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.cache = FileSystemCache(self.test_dir, max_checkpoints_per_hour=5)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir)
    
    def test_save_and_load_checkpoint(self):
        """Test saving and loading checkpoints"""
        state = create_initial_state("test_item.md")
        state["current_stage"] = "agent_a"
        state["atom_a_code"] = "def extract_context(): pass"
        
        # Save checkpoint
        checkpoint_id = self.cache.save_checkpoint("test_item", state)
        self.assertIsNotNone(checkpoint_id)
        self.assertIn("_", checkpoint_id)  # Format: {hour}_{time}
        
        # Load latest checkpoint
        loaded = self.cache.load_checkpoint("test_item")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["current_stage"], "agent_a")
        self.assertEqual(loaded["atom_a_code"], "def extract_context(): pass")
        
        # Load specific checkpoint
        loaded2 = self.cache.load_checkpoint("test_item", checkpoint_id)
        self.assertIsNotNone(loaded2)
        self.assertEqual(loaded2["current_stage"], "agent_a")
    
    def test_save_and_load_stage_output(self):
        """Test saving and loading stage outputs"""
        output = {"result": "success", "code_length": 100}
        
        self.cache.save_stage_output("test_item", "agent_a", output)
        
        loaded = self.cache.load_stage_output("test_item", "agent_a")
        self.assertEqual(loaded["result"], "success")
        self.assertEqual(loaded["code_length"], 100)
    
    def test_list_checkpoints(self):
        """Test listing checkpoints"""
        state = create_initial_state("test_item.md")
        
        # Save multiple checkpoints
        for i in range(3):
            state["iteration_count"] = i
            self.cache.save_checkpoint("test_item", state)
        
        checkpoints = self.cache.list_checkpoints("test_item")
        self.assertGreaterEqual(len(checkpoints), 1)  # At least 1 after cleanup
    
    def test_get_cache_stats(self):
        """Test cache statistics"""
        state = create_initial_state("test_item.md")
        self.cache.save_checkpoint("test_item", state)
        self.cache.save_stage_output("test_item", "load_spec", {"done": True})
        
        stats = self.cache.get_cache_stats("test_item")
        self.assertTrue(stats["exists"])
        self.assertTrue(stats["has_latest"])
        self.assertIn("load_spec", stats["stages"])


class TestTools(unittest.TestCase):
    """Test tools.py module"""
    
    def test_extract_file_patterns_from_spec_content(self):
        """Test extracting file patterns from spec content"""
        content = '''
        The parser should read from `*.log` files.
        Also check "*.v.gz" for netlists.
        SPEF files are in `*.spef` format.
        '''
        
        patterns = extract_file_patterns_from_spec_content(content)
        
        self.assertIn("*.log", patterns["sta_logs"])
        self.assertIn("*.v.gz", patterns["netlist_files"])
        self.assertIn("*.spef", patterns["spef_files"])
    
    def test_extract_file_patterns_from_spec(self):
        """Test extracting file patterns from parsed spec"""
        parsed_spec = {
            "implementation_hints": {
                "file_patterns": ["*.log", "*.rpt"]
            }
        }
        
        patterns = extract_file_patterns_from_spec(parsed_spec)
        self.assertIn("*.log", patterns)
        self.assertIn("*.rpt", patterns)
        
        # Test with empty spec
        patterns2 = extract_file_patterns_from_spec({})
        self.assertIn("*.log", patterns2)  # Default patterns
    
    def test_parse_item_spec(self):
        """Test ItemSpec parsing"""
        content = '''
# ItemSpec: IMP-10-0-0-00

## 1. Parsing Logic

Extract the following fields:
- `tool_name`: The name of the EDA tool
- `version`: Version number

## 2. Check Logic

Existence check: Verify that the tool was used.

## 3. Waiver Logic

Waiver keywords: "bypass", "skip"

## 4. Implementation Guide

File patterns: `*.log`, `*.rpt`
'''
        
        result = parse_item_spec(content)
        
        self.assertEqual(result["item_id"], "IMP-10-0-0-00")
        self.assertIn("parsing_logic", result)
        self.assertIn("check_logic", result)
        self.assertIn("waiver_logic", result)
    
    def test_extract_log_snippet(self):
        """Test log snippet extraction"""
        # Create temporary log file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("Line 1: Header\n")
            f.write("Line 2: Start processing\n")
            f.write("Line 3: Reading netlist from top.v\n")
            f.write("Line 4: Processing complete\n")
            f.write("Line 5: Footer\n")
            temp_file = f.name
        
        try:
            result = extract_log_snippet(temp_file, ["netlist"], context_lines=1)
            
            self.assertEqual(result["file_path"], temp_file)
            self.assertEqual(len(result["snippets"]), 1)
            self.assertEqual(result["snippets"][0]["keyword"], "netlist")
            self.assertEqual(result["snippets"][0]["line_number"], 3)
            self.assertIn("netlist", result["snippets"][0]["content"])
        finally:
            os.unlink(temp_file)


class TestValidator(unittest.TestCase):
    """Test validator.py module"""
    
    def test_valid_code_passes(self):
        """Test that valid code passes validation"""
        valid_code = '''
import re
import fnmatch

def extract_context(text: str, source_file: str):
    results = []
    for i, line in enumerate(text.split('\\n'), 1):
        if line.strip():
            results.append({
                "value": str(line.strip()),
                "source_file": source_file,
                "line_number": i,
                "matched_content": line,
                "parsed_fields": {}
            })
    return results

def validate_logic(text, pattern, parsed_fields=None, default_match="contains", regex_mode="search"):
    if parsed_fields is None:
        parsed_fields = {}
    
    text = str(text) if text is not None else ""
    pattern = str(pattern) if pattern is not None else ""
    
    # Priority 1: Alternatives
    if '|' in pattern:
        alternatives = [alt.strip() for alt in pattern.split('|') if alt.strip()]
        for alt in alternatives:
            if alt in text:
                return {'is_match': True, 'reason': f'Matched: {alt}', 'kind': 'alternatives'}
        return {'is_match': False, 'reason': 'No match', 'kind': 'alternatives'}
    
    # Priority 2: Regex
    if pattern.startswith('regex:'):
        regex_pattern = pattern[6:]
        try:
            if regex_mode == "match":
                match = re.match(regex_pattern, text)
            else:
                match = re.search(regex_pattern, text)
            if match:
                return {'is_match': True, 'reason': f'Regex matched', 'kind': 'regex'}
            return {'is_match': False, 'reason': 'Regex no match', 'kind': 'regex'}
        except re.error as e:
            return {'is_match': False, 'reason': f'Invalid Regex: {e}', 'kind': 'regex'}
    
    # Priority 3: Wildcard
    if '*' in pattern or '?' in pattern:
        if fnmatch.fnmatchcase(text, pattern):
            return {'is_match': True, 'reason': 'Wildcard matched', 'kind': 'wildcard'}
        return {'is_match': False, 'reason': 'Wildcard no match', 'kind': 'wildcard'}
    
    # Priority 4: Default
    if default_match == "exact":
        is_match = text == pattern
        return {'is_match': is_match, 'reason': 'Exact', 'kind': 'exact'}
    else:
        is_match = pattern in text
        return {'is_match': is_match, 'reason': 'Contains', 'kind': 'contains'}

def check_existence(items):
    is_match = len(items) > 0 if items else False
    return {'is_match': is_match, 'reason': f'Found {len(items) if items else 0}', 'evidence': items}
'''
        
        result = validate_10_2_compliance(valid_code, "requirements: {}")
        
        self.assertTrue(result["gate_results"].get("gate1_signature", False), 
                       f"gate1_signature failed: {result['errors']}")
        self.assertTrue(result["gate_results"].get("gate2_none_safety", False),
                       f"gate2_none_safety failed: {result['errors']}")
        self.assertTrue(result["gate_results"].get("gate2_alternatives", False),
                       f"gate2_alternatives failed: {result['errors']}")
    
    def test_forbidden_io_detected(self):
        """Test that forbidden IO operations are detected"""
        bad_code = '''
def extract_context(text, source_file):
    with open("file.txt") as f:  # Forbidden!
        return f.read()
    
def validate_logic(text, pattern, parsed_fields=None, default_match="contains", regex_mode="search"):
    return {'is_match': True, 'reason': '', 'kind': 'contains'}

def check_existence(items):
    return {'is_match': True, 'reason': '', 'evidence': items}
'''
        
        result = validate_10_2_compliance(bad_code, "")
        
        self.assertFalse(result["valid"])
        self.assertTrue(any("open" in e for e in result["errors"]))
    
    def test_determine_error_source(self):
        """Test error source determination"""
        # Atom A errors
        errors_a = ["FAIL [Gate1]: Missing keys in ParsedItem: {'value'}"]
        self.assertEqual(determine_error_source(errors_a), "atom_a")
        
        # Atom B errors
        errors_b = ["FAIL [Gate2]: Wildcard precedence test failed"]
        self.assertEqual(determine_error_source(errors_b), "atom_b")
        
        # Atom C errors
        errors_c = ["FAIL: Atom C failed to pass through 'evidence' list"]
        self.assertEqual(determine_error_source(errors_c), "atom_c")
        
        # Unknown errors
        errors_unknown = ["Some random error"]
        self.assertEqual(determine_error_source(errors_unknown), "unknown")


class TestPrompts(unittest.TestCase):
    """Test prompts.py module"""
    
    def test_build_agent_a_prompt(self):
        """Test Agent A prompt building"""
        prompt = build_agent_a_prompt(
            item_spec_content="# ItemSpec: TEST",
            log_snippets={"file.log": {"content": "test"}},
            parsed_spec={"parsing_logic": {"target_fields": []}}
        )
        
        self.assertIn("Parsing Expert Agent", prompt)
        self.assertIn("extract_context", prompt)
        self.assertIn("# ItemSpec: TEST", prompt)
    
    def test_build_agent_b_prompt(self):
        """Test Agent B prompt building"""
        prompt = build_agent_b_prompt(
            item_spec_content="# ItemSpec: TEST",
            atom_a_code="def extract_context(): pass",
            parsed_spec={"check_logic": {"type": "existence"}}
        )
        
        self.assertIn("Logic Developer Agent", prompt)
        self.assertIn("validate_logic", prompt)
        self.assertIn("def extract_context(): pass", prompt)
    
    def test_parse_agent_response(self):
        """Test parsing agent response"""
        response = '''
Here is the code:

```python
def extract_context(text, source_file):
    return []
```

This implementation handles all cases.
'''
        
        code, reasoning = parse_agent_response(response)
        
        self.assertIn("def extract_context", code)
        self.assertIn("handles all cases", reasoning)
    
    def test_parse_agent_b_response(self):
        """Test parsing Agent B response with multiple blocks"""
        response = '''
```python
def validate_logic(text, pattern, parsed_fields=None, default_match="contains", regex_mode="search"):
    return {'is_match': True, 'reason': '', 'kind': 'contains'}
```

```python
def check_existence(items):
    return {'is_match': True, 'reason': '', 'evidence': items}
```

```yaml
requirements:
  value: "test"
```
'''
        
        atom_b, atom_c, yaml_config, reasoning = parse_agent_b_response(response)
        
        self.assertIn("validate_logic", atom_b)
        self.assertIn("check_existence", atom_c)
        self.assertIn("requirements:", yaml_config)


# MockLLMClient tests removed - using real JEDAI calls only
# Run test_real_jedai.py for LLM integration testing


if __name__ == "__main__":
    # Run tests with verbosity
    unittest.main(verbosity=2)
