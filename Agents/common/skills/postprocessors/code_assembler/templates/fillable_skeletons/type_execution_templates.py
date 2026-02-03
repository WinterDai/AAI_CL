"""
Fillable Skeleton Templates for Type Execution Methods

These templates are used in LLM prompts to provide concrete "fillable frameworks".
Each template consists of 90% complete code + 10% TODO markers.

Design Principles:
1. FIXED sections are written explicitly (API calls, parameter passing)
2. Business logic uses TODO + example placeholders
3. Critical constraints are explicitly marked with ⚠️ CRITICAL
4. Aligned with AutoGenChecker approach, adapted to three-layer architecture

Usage in Prompt:
```
Implement _execute_type3() based on the following fillable framework:

{get_type3_fillable_template()}

TODO sections are what you need to fill based on business logic.
FIXED sections must remain unchanged.
```
"""

def get_type1_fillable_template() -> str:
    """
    Type 1: Boolean Check (no waiver)
    
    Key Characteristics:
    - Calls execute_boolean_check()
    - has_waiver=False
    - Reuses _boolean_check_logic()
    """
    return '''
def _execute_type1(self, parsed_data: Dict[str, Any]) -> CheckResult:
    """
    Type 1: Boolean check - Existence check, no waiver
    
    Business Logic: Check if certain items exist (e.g., files loaded successfully)
    Pass Condition: All required items exist
    Fail Condition: Any required item is missing
    """
    # FIXED: Type1/4 share Boolean Check Logic
    def parse_data():
        """Call shared Boolean Check Logic"""
        return self._boolean_check_logic(parsed_data)
    
    # FIXED: Type1 framework call signature
    return self.execute_boolean_check(
        parse_data_func=parse_data,
        has_waiver=False,  # ← Type1 characteristic: no waiver
        found_desc=self.FOUND_DESC,  # ← Use class constant
        missing_desc=self.MISSING_DESC,
        extra_desc=self.EXTRA_DESC,
        name_extractor=self._build_name_extractor()  # ← Need to implement this helper
    )
'''


def get_type2_fillable_template() -> str:
    """
    Type 2: Value Check (no waiver)
    
    Key Characteristics:
    - Calls execute_value_check()
    - has_waiver=False
    - Reuses _pattern_check_logic()
    """
    return '''
def _execute_type2(self, parsed_data: Dict[str, Any]) -> CheckResult:
    """
    Type 2: Value check - Pattern matching, no waiver
    
    Business Logic: Search for patterns in pattern_items
    Pass Condition: All patterns found
    Fail Condition: Any pattern not found
    """
    # FIXED: Type2/3 share Pattern Check Logic
    def parse_data():
        """Call shared Pattern Check Logic"""
        return self._pattern_check_logic(parsed_data)
    
    # FIXED: Type2 framework call signature
    return self.execute_value_check(
        parse_data_func=parse_data,
        has_waiver=False,  # ← Type2 characteristic: no waiver
        found_desc="Pattern found",  # ← Customizable description
        missing_desc="Pattern not found",
        extra_desc=self.EXTRA_DESC,
        name_extractor=self._build_name_extractor()
    )
'''


def get_type3_fillable_template() -> str:
    """
    Type 3: Value Check with Waiver (has waiver)
    
    ⚠️ CRITICAL Characteristics:
    - Calls execute_value_check()
    - has_waiver=True
    - MUST include info_items parameter
    - extra_severity=Severity.FAIL
    - Reuses _pattern_check_logic()
    """
    return '''
def _execute_type3(self, parsed_data: Dict[str, Any]) -> CheckResult:
    """
    Type 3: Value check with waiver - Pattern matching + waiver support
    
    Business Logic: Same as Type2 (pattern search), but with waiver support
    Pass Condition: Pattern found OR waiver is valid
    Fail Condition: Pattern not found AND waiver is invalid/expired
    """
    # ⚠️ CRITICAL: Type3 MUST prepare info_items (can be empty dict)
    # info_items are used to display informational entries (don't affect PASS/FAIL)
    # TODO: Build info_items based on parsed_data (if you need to display information)
    info_items = {}
    
    # Example: If you need to display file path information
    # netlist_info = parsed_data.get('netlist_info', {})
    # if netlist_info.get('path'):
    #     info_items['File Path'] = {
    #         'line_number': 0,
    #         'file_path': '',
    #         'reason': f"Found at: {netlist_info['path']}"
    #     }
    
    # FIXED: Type2/3 share Pattern Check Logic
    def parse_data():
        """Call shared Pattern Check Logic (same as Type2)"""
        return self._pattern_check_logic(parsed_data)
    
    # FIXED: Type3 framework call signature
    # ⚠️ CRITICAL: Note the difference from Type2
    return self.execute_value_check(
        parse_data_func=parse_data,
        has_waiver=True,  # ← Type3 characteristic: enable waiver
        info_items=info_items,  # ← Type3 characteristic: MUST include (can be empty)
        found_desc="Pattern found",
        missing_desc="Pattern not found",
        extra_desc=self.EXTRA_DESC,
        extra_severity=Severity.FAIL,  # ← Type3 characteristic: extra errors as FAIL
        name_extractor=self._build_name_extractor()
    )
'''


def get_type4_fillable_template() -> str:
    """
    Type 4: Boolean Check with Waiver (has waiver)
    
    Key Characteristics:
    - Calls execute_boolean_check()
    - has_waiver=True
    - Reuses _boolean_check_logic()
    """
    return '''
def _execute_type4(self, parsed_data: Dict[str, Any]) -> CheckResult:
    """
    Type 4: Boolean check with waiver - Existence check + waiver support
    
    Business Logic: Same as Type1 (existence check), but with waiver support
    Pass Condition: Item exists OR waiver is valid
    Fail Condition: Item missing AND waiver is invalid/expired
    """
    # FIXED: Type1/4 share Boolean Check Logic
    def parse_data():
        """Call shared Boolean Check Logic (same as Type1)"""
        return self._boolean_check_logic(parsed_data)
    
    # FIXED: Type4 framework call signature
    return self.execute_boolean_check(
        parse_data_func=parse_data,
        has_waiver=True,  # ← Type4 characteristic: enable waiver
        found_desc=self.FOUND_DESC,
        missing_desc=self.MISSING_DESC,
        extra_desc=self.EXTRA_DESC,
        name_extractor=self._build_name_extractor()
    )
'''


def get_layer2_boolean_logic_template() -> str:
    """
    Layer 2: Boolean Check Logic (shared by Type1/4)
    
    Core Business Logic: Determine found/missing/extra from parsed_data
    """
    return '''
def _boolean_check_logic(self, parsed_data: Dict[str, Any]) -> tuple:
    """
    Boolean Check Logic (shared by Type1/4)
    
    Core Business Logic: Determine which items exist and which are missing
    
    Returns:
        tuple: (found_items, missing_items, extra_items)
        - found_items: Dict[str, Dict] - key is item name, value is metadata
        - missing_items: Dict[str, Dict] - ⚠️ MUST be Dict, NOT List
        - extra_items: Dict[str, Dict] - additionally discovered items
    
    ⚠️ CRITICAL: All items MUST be in Dict[str, Dict] format:
    {
        'item_name': {
            'line_number': 123,  # REQUIRED for source tracking
            'file_path': '/path/to/file',  # REQUIRED
            'reason': 'Additional info'  # Optional
        }
    }
    """
    # TODO: Extract necessary data from parsed_data
    # Example structure:
    # items = parsed_data.get('items', [])
    # or
    # netlist_info = parsed_data.get('netlist_info', {})
    # spef_info = parsed_data.get('spef_info', {})
    
    found_items = {}
    missing_items = {}
    extra_items = {}
    
    # TODO: Implement business logic - determine found/missing
    # Example logic:
    # for item in items:
    #     if item['status'] == 'Success':
    #         found_items[item['name']] = {
    #             'line_number': item.get('line', 0),
    #             'file_path': item.get('file', ''),
    #             'reason': 'Found successfully'
    #         }
    #     else:
    #         missing_items[item['name']] = {
    #             'reason': f"Status: {item['status']}"
    #         }
    
    # ⚠️ CRITICAL: Ensure returning Dict[str, Dict], not List!
    return found_items, missing_items, extra_items
'''


def get_layer2_pattern_logic_template() -> str:
    """
    Layer 2: Pattern Check Logic (shared by Type2/3)
    
    Core Business Logic: Match pattern_items
    """
    return '''
def _pattern_check_logic(self, parsed_data: Dict[str, Any]) -> tuple:
    """
    Pattern Check Logic (shared by Type2/3)
    
    Core Business Logic: Search for patterns in pattern_items
    
    Returns:
        tuple: (found_items, missing_items, extra_items)
    """
    # FIXED: Get pattern_items
    requirements = self.item_data.get('requirements', {})
    pattern_items = requirements.get('pattern_items', [])
    
    found_items = {}
    missing_items = {}
    extra_items = {}
    
    # TODO: Extract content from parsed_data for searching
    # Example:
    # content = parsed_data.get('extracted_content', [])
    
    # TODO: Implement pattern matching logic
    # Example:
    # for pattern in pattern_items:
    #     matched = False
    #     for line in content:
    #         if self._match_pattern(line, [pattern]):
    #             found_items[pattern] = {
    #                 'line_number': line.get('line_num', 0),
    #                 'file_path': line.get('file', ''),
    #                 'matched': line.get('text', '')
    #             }
    #             matched = True
    #             break
    #     if not matched:
    #         missing_items[pattern] = {
    #             'reason': 'Pattern not found in input files'
    #         }
    
    return found_items, missing_items, extra_items
'''


def get_layer1_parse_template() -> str:
    """
    Layer 1: Input File Parsing
    
    Core Business Logic: Parse input files and extract data
    """
    return '''
def _parse_input_files(self) -> Dict[str, Any]:
    """
    Parse input files to extract data for checking.
    
    Returns:
        Dict[str, Any] with structure:
        {
            'items': [...],  # or other business-relevant keys
            'metadata': {...},
            'errors': [...]
        }
    
    ⚠️ CRITICAL: Return MUST be Dict, used by subsequent Type methods
    """
    # FIXED: Validate input files
    # IMPORTANT: validate_input_files() returns TUPLE: (valid_files, missing_files)
    valid_files, missing_files = self.validate_input_files()
    if not valid_files:
        raise ConfigurationError("No valid input files found")
    
    # TODO: Implement file parsing logic
    # Available template helpers:
    # - self.parse_log_with_patterns(file_path, patterns)
    # - self.normalize_command(text)
    
    # Example structure:
    result = {
        'items': [],  # TODO: Fill with actual parsed data
        'metadata': {'total': 0},
        'errors': []
    }
    
    # TODO: Parse each input file
    # for file_path in valid_files:
    #     with open(file_path, 'r', errors='ignore') as f:
    #         for line_num, line in enumerate(f, 1):
    #             # Parsing logic...
    #             pass
    
    return result
'''


# ============================================================================
# Critical Pattern Checklist - For validating LLM-generated code
# ============================================================================

CRITICAL_CHECKLIST = '''
## 🚨 Critical Pattern Checklist

Before generating code, confirm the following patterns:

### Layer 1 (Parsing)
- [ ] `_parse_input_files()` returns `Dict[str, Any]`
- [ ] Returned Dict contains necessary keys (e.g., items, metadata, errors)
- [ ] Uses `valid_files, missing_files = self.validate_input_files()` (note: returns TUPLE)

### Layer 2 (Logic)
- [ ] `_boolean_check_logic(parsed_data)` returns `Tuple[Dict, Dict, Dict]`
- [ ] `_pattern_check_logic(parsed_data)` returns `Tuple[Dict, Dict, Dict]`
- [ ] **found_items, missing_items, extra_items MUST ALL be `Dict[str, Dict]`, NOT List**
- [ ] Each item's value MUST contain `line_number` and `file_path` keys

### Layer 3 (Execution)
- [ ] Type1: `execute_boolean_check(..., has_waiver=False)`
- [ ] Type2: `execute_value_check(..., has_waiver=False)`
- [ ] Type3: `execute_value_check(..., has_waiver=True, info_items={...})` ← **MUST include info_items**
- [ ] Type4: `execute_boolean_check(..., has_waiver=True)`
- [ ] All Types use `parse_data_func=lambda: ...` to wrap logic calls

### Common Patterns
- [ ] Class constants use `self.FOUND_DESC` etc.
- [ ] name_extractor uses `self._build_name_extractor()`
- [ ] Type3's extra_severity set to `Severity.FAIL`

### Data Structure Rules
```python
# ✅ CORRECT
missing_items["Item Name"] = {"reason": "..."}

# ❌ WRONG
missing_items.append("Item Name")
```
'''
