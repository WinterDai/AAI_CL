"""
Developer Agent - Integration Tests
Tests the complete workflow and component interactions

NOTE: LLM integration tests are in test_real_jedai.py
This file tests non-LLM components only
"""
import unittest
import os
import sys
import tempfile
import shutil
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import AgentState, AgentConfig, create_initial_state, generate_item_id
from cache import FileSystemCache
from tools import parse_item_spec, extract_log_snippet
from validator import validate_10_2_compliance, determine_error_source
from prompts import (
    build_agent_a_prompt,
    build_agent_b_prompt,
    build_reflect_prompt,
    parse_agent_response,
    parse_agent_b_response
)
from nodes import (
    load_spec_node,
    discover_logs_node,
    validate_node,
    should_continue
)


class TestEndToEndWorkflow(unittest.TestCase):
    """Test complete agent workflow (non-LLM components)"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        
        # Create test ItemSpec
        self.item_spec_dir = os.path.join(self.test_dir, "item_specs")
        os.makedirs(self.item_spec_dir)
        
        self.item_spec_path = os.path.join(self.item_spec_dir, "TEST-01-0-0-00_ItemSpec.md")
        with open(self.item_spec_path, 'w', encoding='utf-8') as f:
            f.write('''# ItemSpec: TEST-01-0-0-00

## 1. Parsing Logic

Target fields:
- `tool_name`: The name of the EDA tool
- `version`: Version string

## 2. Check Logic

Type: existence
Description: Check that tool information exists

## 3. Waiver Logic

Waiver keywords: "waiver", "exception"

## 4. Implementation Guide

File patterns: `*.log`
''')
        
        # Create test log file
        self.log_dir = os.path.join(self.test_dir, "logs")
        os.makedirs(self.log_dir)
        
        self.log_path = os.path.join(self.log_dir, "test.log")
        with open(self.log_path, 'w', encoding='utf-8') as f:
            f.write('''Tool: TestTool
Version: 1.2.3
Date: 2024-01-01
Processing started...
Reading netlist from top.v
Analysis complete.
''')
        
        # Create cache directory
        self.cache_dir = os.path.join(self.test_dir, "cache")
        os.makedirs(self.cache_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir)
    
    def test_load_spec_node(self):
        """Test load_spec_node"""
        state = create_initial_state(self.item_spec_path)
        
        result = load_spec_node(state)
        
        self.assertEqual(result["current_stage"], "load_spec")
        self.assertIsNotNone(result["item_spec_content"])
        self.assertIn("TEST-01-0-0-00", result["item_spec_content"])
        self.assertIsNotNone(result["parsed_spec"])
        self.assertEqual(result["parsed_spec"]["item_id"], "TEST-01-0-0-00")
    
    def test_discover_logs_node(self):
        """Test discover_logs_node"""
        state = create_initial_state(self.item_spec_path)
        with open(self.item_spec_path, 'r', encoding='utf-8') as f:
            state["item_spec_content"] = f.read()
        state["search_root"] = self.log_dir
        
        result = discover_logs_node(state)
        
        self.assertEqual(result["current_stage"], "discover")
        self.assertIsInstance(result["discovered_log_files"], list)
    
    def test_validate_node(self):
        """Test validate_node with valid code"""
        state = create_initial_state(self.item_spec_path)
        state["current_stage"] = "validate"
        state["requirements_yaml"] = "requirements: {}"
        
        # Provide valid code for all atoms
        state["atom_a_code"] = '''
import re

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
'''
        
        state["atom_b_code"] = '''
import re
import fnmatch

def validate_logic(text, pattern, parsed_fields=None, default_match="contains", regex_mode="search"):
    if parsed_fields is None:
        parsed_fields = {}
    
    text = str(text) if text is not None else ""
    pattern = str(pattern) if pattern is not None else ""
    
    if '|' in pattern:
        alternatives = [alt.strip() for alt in pattern.split('|') if alt.strip()]
        for alt in alternatives:
            if alt in text:
                return {'is_match': True, 'reason': f'Matched: {alt}', 'kind': 'alternatives'}
        return {'is_match': False, 'reason': 'No match', 'kind': 'alternatives'}
    
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
    
    if '*' in pattern or '?' in pattern:
        if fnmatch.fnmatchcase(text, pattern):
            return {'is_match': True, 'reason': 'Wildcard matched', 'kind': 'wildcard'}
        return {'is_match': False, 'reason': 'Wildcard no match', 'kind': 'wildcard'}
    
    if default_match == "exact":
        is_match = text == pattern
        return {'is_match': is_match, 'reason': 'Exact', 'kind': 'exact'}
    else:
        is_match = pattern in text
        return {'is_match': is_match, 'reason': 'Contains', 'kind': 'contains'}
'''
        
        state["atom_c_code"] = '''
def check_existence(items):
    is_match = len(items) > 0 if items else False
    return {'is_match': is_match, 'reason': f'Found {len(items) if items else 0}', 'evidence': items}
'''
        
        result = validate_node(state)
        
        self.assertIn("gate_results", result)
        self.assertIn("validation_errors", result)
        self.assertEqual(result["current_stage"], "validate")
    
    def test_should_continue_logic(self):
        """Test should_continue routing logic"""
        state = create_initial_state("test.md")
        
        # Test pass - no validation errors means done
        state["validation_errors"] = []
        self.assertEqual(should_continue(state), "done")
        
        # Test fail within iterations with atom_a error
        state["validation_errors"] = ["FAIL [Gate1]: Missing keys"]
        state["iteration_count"] = 1
        state["error_source"] = "atom_a"
        self.assertEqual(should_continue(state), "reflect_a")
        
        # Test fail with atom_b error
        state["error_source"] = "atom_b"
        self.assertEqual(should_continue(state), "reflect_b")
        
        # Test max iterations exceeded
        state["iteration_count"] = 10
        self.assertEqual(should_continue(state), "human_required")
    
    def test_cache_checkpoint_and_resume(self):
        """Test checkpoint save and resume"""
        cache = FileSystemCache(self.cache_dir)
        
        # Create and save state
        state = create_initial_state(self.item_spec_path)
        state["current_stage"] = "agent_a"
        state["item_spec_content"] = "test content"
        state["discovered_log_files"] = [self.log_path]
        
        checkpoint_id = cache.save_checkpoint("TEST-01-0-0-00", state)
        
        # Load from checkpoint
        resumed = cache.load_checkpoint("TEST-01-0-0-00")
        
        self.assertIsNotNone(resumed)
        self.assertEqual(resumed["current_stage"], "agent_a")
        self.assertEqual(resumed["item_spec_content"], "test content")
    
    def test_build_graph_structure(self):
        """Test that graph builds correctly (skipped if langgraph not installed)"""
        try:
            from graph import build_agent_graph
            graph = build_agent_graph()
            self.assertIsNotNone(graph)
        except ImportError:
            self.skipTest("LangGraph not installed")


class TestValidatorIntegration(unittest.TestCase):
    """Test validator integration scenarios"""
    
    def test_gate1_signature_validation(self):
        """Test Gate 1 signature validation"""
        code1 = '''
def validate_logic(text, pattern, parsed_fields=None, default_match="contains", regex_mode="search"):
    return {'is_match': True, 'reason': '', 'kind': 'contains'}

def check_existence(items):
    return {'is_match': True, 'reason': '', 'evidence': items}
'''
        result1 = validate_10_2_compliance(code1, "")
        self.assertFalse(result1["gate_results"].get("gate1_signature", True))
        
    def test_gate2_none_safety(self):
        """Test Gate 2 None safety"""
        code = '''
def extract_context(text, source_file):
    return []

def validate_logic(text, pattern, parsed_fields=None, default_match="contains", regex_mode="search"):
    if parsed_fields is None:
        parsed_fields = {}
    text = str(text) if text is not None else ""
    pattern = str(pattern) if pattern is not None else ""
    return {'is_match': True, 'reason': '', 'kind': 'contains'}

def check_existence(items):
    return {'is_match': True, 'reason': '', 'evidence': items}
'''
        result = validate_10_2_compliance(code, "")
        self.assertTrue(result["gate_results"].get("gate2_none_safety", False))
    
    def test_gate2_alternatives_precedence(self):
        """Test Gate 2 alternatives precedence"""
        code = '''
import re
import fnmatch

def extract_context(text, source_file):
    return []

def validate_logic(text, pattern, parsed_fields=None, default_match="contains", regex_mode="search"):
    if parsed_fields is None:
        parsed_fields = {}
    text = str(text) if text is not None else ""
    pattern = str(pattern) if pattern is not None else ""
    
    if '|' in pattern:
        alternatives = [alt.strip() for alt in pattern.split('|') if alt.strip()]
        for alt in alternatives:
            if alt in text:
                return {'is_match': True, 'reason': f'Matched: {alt}', 'kind': 'alternatives'}
        return {'is_match': False, 'reason': 'No match', 'kind': 'alternatives'}
    
    if pattern.startswith('regex:'):
        regex_pattern = pattern[6:]
        try:
            match = re.search(regex_pattern, text)
            if match:
                return {'is_match': True, 'reason': f'Regex matched', 'kind': 'regex'}
            return {'is_match': False, 'reason': 'Regex no match', 'kind': 'regex'}
        except re.error as e:
            return {'is_match': False, 'reason': f'Invalid Regex: {e}', 'kind': 'regex'}
    
    if '*' in pattern or '?' in pattern:
        if fnmatch.fnmatchcase(text, pattern):
            return {'is_match': True, 'reason': 'Wildcard matched', 'kind': 'wildcard'}
        return {'is_match': False, 'reason': 'Wildcard no match', 'kind': 'wildcard'}
    
    if default_match == "exact":
        is_match = text == pattern
    else:
        is_match = pattern in text
    return {'is_match': is_match, 'reason': 'Default', 'kind': 'contains'}

def check_existence(items):
    return {'is_match': len(items) > 0, 'reason': '', 'evidence': items}
'''
        result = validate_10_2_compliance(code, "")
        self.assertTrue(result["gate_results"].get("gate2_alternatives", False))


class TestPromptsIntegration(unittest.TestCase):
    """Test prompt generation integration"""
    
    def test_full_prompt_generation_cycle(self):
        """Test complete prompt generation cycle"""
        item_spec = '''# ItemSpec: TEST-01

## 1. Parsing Logic

Extract: `tool_name`, `version`

## 2. Check Logic

Type: existence
'''
        
        parsed_spec = parse_item_spec(item_spec)
        
        # Build Agent A prompt
        prompt_a = build_agent_a_prompt(
            item_spec_content=item_spec,
            log_snippets={"test.log": {"content": "Tool: ABC\nVersion: 1.0"}},
            parsed_spec=parsed_spec
        )
        
        self.assertIn("extract_context", prompt_a)
        self.assertIn("TEST-01", prompt_a)
        
        # Simulate Agent A response and parse
        response_a = '''
```python
def extract_context(text, source_file):
    return []
```
'''
        code_a, _ = parse_agent_response(response_a)
        self.assertIn("def extract_context", code_a)
        
        # Build Agent B prompt
        prompt_b = build_agent_b_prompt(
            item_spec_content=item_spec,
            atom_a_code=code_a,
            parsed_spec=parsed_spec
        )
        
        self.assertIn("validate_logic", prompt_b)
        self.assertIn("def extract_context", prompt_b)
        
        # Build Reflect prompt
        prompt_r = build_reflect_prompt(
            validation_errors=["FAIL [Gate1]: Missing keys"],
            gate_results={},
            previous_code=code_a,
            error_source="atom_a"
        )
        
        self.assertIn("FAIL [Gate1]", prompt_r)


if __name__ == "__main__":
    unittest.main(verbosity=2)
