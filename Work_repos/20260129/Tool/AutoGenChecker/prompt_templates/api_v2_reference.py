"""Enhanced code generation instructions for API v2.0 compliance."""

# Template generation instructions that enforce API v2.0 best practices


TEMPLATE_V2_INSTRUCTIONS = """
═══════════════════════════════════════════════════════════════════════════════
CODE GENERATION REQUIREMENTS - OutputBuilderTemplate API v2.0
═══════════════════════════════════════════════════════════════════════════════

⚠️ CRITICAL: Generate code using OutputBuilderTemplate API v2.0

## 1. REQUIRED IMPORTS

```python
from output_builder_template import OutputBuilderMixin
from output_formatter import Severity
```

## 2. METADATA FORMAT (MANDATORY)

Use Dict format for ALL items to preserve metadata:

```python
# ✅ CORRECT - Dict with metadata
items = {
    "item_name": {
        "line_number": line_num,      # Required
        "file_path": file_path,        # Required
        "line_content": line_text      # Optional but recommended
    }
}

# ❌ WRONG - List without metadata
items = ["item1", "item2"]  # Only for backward compatibility
```

## 3. PARSING LOGIC

Extract items WITH metadata in one pass:

```python
def _parse_input_files(self) -> Dict:
    \"\"\"Parse files and preserve metadata.\"\"\"
    found_items = {}
    missing_items = {}
    
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            # Extract item with metadata
            if match := re.match(pattern, line):
                item_name = match.group(1)
                found_items[item_name] = {
                    "line_number": line_num,
                    "file_path": str(file_path),
                    "line_content": line
                }
    
    return {"found": found_items, "missing": missing_items}
```

🔴 **FILENAME EXTRACTION - COMMON MISTAKES**
═══════════════════════════════════════════════════════════════════════════════
When extracting filenames from paths, preserve ALL suffixes!

❌ WRONG - Stops at first/second dot:
```python
name = line.split('.')[0]  # 'PLN6FF_001' - Missing .11a.encrypt!
name = '.'.join(line.split('.')[:2])  # 'PLN6FF_001.11a' - Missing .encrypt!
```

✅ CORRECT - Extract full filename:
```python
from pathlib import Path
name = Path(line).name  # 'PLN6FF_001.11a.encrypt' - Complete!

# OR if parsing from full path:
full_path = "/path/to/PLN6FF_001.11a.encrypt"
filename = Path(full_path).name  # Extracts: 'PLN6FF_001.11a.encrypt'
```

Common patterns that MUST be preserved:
- Multiple dots: `file.tar.gz`, `data.v1.2.json`
- Encrypt suffix: `*.encrypt`
- Compression: `*.gz`, `*.bz2`
- Version numbers: `lib_v1.2.3.a`
- Special formats: `file.11a.encrypt`, `data.001.backup`

Rule of thumb: Use `Path(line).name` to extract filename, NOT string splitting!
═══════════════════════════════════════════════════════════════════════════════

## 4. OUTPUT BUILDING (ONE-STEP SOLUTION)

Use `build_complete_output()` - the recommended approach.

### Complete API Signature:

```python
def build_complete_output(
    self,
    # Item collections (Dict or List)
    found_items: Optional[Union[Dict, List]] = None,
    missing_items: Optional[Union[Dict, List]] = None,
    waived_items: Optional[Union[Dict, List]] = None,
    unused_waivers: Optional[Union[Dict, List]] = None,
    extra_items: Optional[Dict] = None,
    
    # Waiver configuration
    waive_dict: Optional[Dict] = None,
    
    # Type flags
    has_pattern_items: bool = False,
    has_waiver_value: bool = False,
    
    # Metadata
    value: Any = "N/A",
    default_file: str = "N/A",
    name_extractor: Optional[Callable] = None,
    
    # Reason strings (str OR callable)
    found_reason: Union[str, Callable[[Dict], str]] = "Item found",
    missing_reason: Union[str, Callable[[Dict], str]] = "Item not found",
    waived_base_reason: str = "Item not found",  # ⚠️ ONLY str supported (NOT Callable)!
    extra_reason: Union[str, Callable[[Dict], str]] = "Unexpected item",
    unused_waiver_reason: str = "Waiver defined but no violation matched",
    
    # Group descriptions (static strings only)
    found_desc: str = "Items found",
    missing_desc: str = "Items not found",
    waived_desc: str = "Items waived",
    extra_desc: str = "Unexpected items",
    unused_desc: str = "Unused waivers",
    
    # Severity control
    missing_severity: Optional[Severity] = None,
    extra_severity: Optional[Severity] = None,
    waived_tag: str = "[WAIVER]"
) -> CheckResult
```

🔴 **API PARAMETER CHECKLISTS - MUST INCLUDE ALL!**
═══════════════════════════════════════════════════════════════════════════════
Without these parameters, output will be generic or logic will be incorrect!

⚠️ CRITICAL: Parameter naming - build_complete_output() accepts:
  - found_items, missing_items, waived_items, unused_waivers, extra_items
  - NO "unwaived_items" parameter! Use missing_items for unwaived violations

Type 1 (Boolean Check) REQUIRED:
✅ found_items=...
✅ missing_items=...  # OR extra_items with extra_severity=FAIL
✅ found_desc="..."
✅ missing_desc="..."  # OR extra_desc
✅ found_reason="..."
✅ missing_reason="..."  # OR extra_reason
✅ default_file="..."  # When using extra_items

Type 2 (Value Check) REQUIRED:
✅ found_items=...
✅ missing_items=...
✅ value=requirements.value  # ⚠️ CRITICAL! Missing = wrong logic!
✅ has_pattern_items=True     # ⚠️ CRITICAL! Missing = wrong logic!
✅ has_waiver_value=False    # ⚠️ CRITICAL! Missing = wrong logic!
✅ found_desc="..."
✅ missing_desc="..."
✅ found_reason="..."
✅ missing_reason="..."

Type 3 (Value Check + Waiver) REQUIRED:
✅ found_items=...
✅ missing_items=...
✅ waived_items=...
✅ unused_waivers=...
✅ waive_dict=...           # ⚠️ From parse_waive_items()!
✅ value=requirements.value
✅ has_pattern_items=True
✅ has_waiver_value=True    # ⚠️ CRITICAL for Type 3!
✅ waived_tag="[WAIVER]"     # ⚠️ MANDATORY for Type 3!
✅ found_desc="..."
✅ missing_desc="..."
✅ waived_desc="..."
✅ found_reason="..."
✅ missing_reason="..."
✅ waived_base_reason="..." # ⚠️ String only, NOT lambda!
✅ unused_waiver_reason="..."

Type 4 (Boolean + Waiver) REQUIRED:
✅ found_items=...
✅ missing_items=...  # unwaived violations
✅ waived_items=...
✅ unused_waivers=...
✅ waive_dict=...           # ⚠️ From parse_waive_items()!
✅ has_waiver_value=True    # ⚠️ CRITICAL for Type 4!
✅ waived_tag="[WAIVER]"     # ⚠️ MANDATORY for Type 4!
✅ found_desc="..."
✅ missing_desc="..."
✅ waived_desc="..."
✅ found_reason="..."
✅ missing_reason="..."
✅ waived_base_reason="..." # ⚠️ String only, NOT lambda!
✅ unused_waiver_reason="..."
═══════════════════════════════════════════════════════════════════════════════

### ⚠️ CRITICAL: Reason Parameters Support Callable!

All `*_reason` parameters (except `unused_waiver_reason`) can be:
- **String**: Static text for all items
- **Callable (lambda)**: Dynamic text based on item metadata

**⚠️ CRITICAL: Lambda Parameter is Metadata Dict, NOT Item Name!**

```python
# Static reason (same for all items)
found_reason="Item found in report"

# Dynamic reason (different per item)
# ✅ CORRECT: 'item' is metadata dict - access fields directly
found_reason=lambda item: f"Slack={item.get('slack', 0):.4f}ns"
missing_reason=lambda item: f"WNS={item.get('wns', 0):.4f}ns ({item.get('violation_count', 0)} violations)"

# ❌ WRONG: Don't try to use 'item' as dict key!
# missing_reason=lambda item: f"Error: {missing_items.get(item, {}).get('details')}"
#                                      ^^^^^^^^^^^^^^^^^
#                                      Can't use dict as dict key (unhashable)!
# ✅ CORRECT: Access metadata directly
# missing_reason=lambda item: f"Error: {item.get('details', 'N/A')}"
```

**Lambda Parameter Explanation:**
- `item` parameter = metadata dict `{'name': str, 'line_number': int, 'file_path': str, ...}`
- You can access: `item['name']`, `item.get('slack')`, `item.get('details')`, etc.
- DO NOT use `item` as a key to look up in another dict

## 6. WHEN TO USE STRING VS LAMBDA FOR REASONS

**⭐ Decision Guide: Check README Display Format Section**

The README file for each checker defines the exact output format under "Display Format":

### 📋 README shows STATIC format (same text for all items):
```yaml
# Example README Display Format:
# INFO01: "LVS rule deck found and version verified"
# ERROR01: "LVS rule deck missing or version mismatch"
```
→ **Use STRING constants:**
```python
FOUND_REASON = "LVS rule deck found and version verified"
MISSING_REASON = "LVS rule deck missing or version mismatch"
```

### 📋 README shows DYNAMIC format (with [...] placeholders):
```yaml
# Example README Display Format:
# INFO01: "[cell_name]: Rule deck [deck_name] (version: [version], tech: [tech_node])"
# ERROR01: "[cell_name]: [ERROR_TYPE] - [details]"
```
→ **Use LAMBDA functions:**
```python
FOUND_REASON = lambda item: (
    f"{item.get('cell_name', 'N/A')}: Rule deck {item.get('deck_name', 'N/A')} "
    f"(version: {item.get('version', 'N/A')}, tech: {item.get('tech_node', 'N/A')})"
)

MISSING_REASON = lambda item: (
    f"{item.get('cell_name', 'N/A')}: {item.get('error_type', 'ERROR')} - "
    f"{item.get('details', 'N/A')}"
)
```

**Key Implementation Rules:**
1. **ALWAYS read README Display Format** - it defines the exact output format
2. **Static format** (no [...] placeholders) → STRING
3. **Dynamic format** (with [...] placeholders) → LAMBDA  
4. **Lambda works for ALL types** (Type 1/2/3/4) - fully supported since 2025-12-22
5. **Ensure parsed items** contain all fields referenced in lambda

**✅ Modern Template: Lambda Fully Supported for All Types!**

```python
# ✅ Type 1/2 with dynamic format (waiver=0 compatible!)
return self.build_complete_output(
    found_reason=lambda item: f"{item['name']}: {item['status']}",
    missing_reason=lambda item: f"{item['name']}: {item['error']}"
)

# ✅ Type 1/2 with static format  
return self.build_complete_output(
    found_reason=self.FOUND_REASON,  # String constant
    missing_reason=self.MISSING_REASON
)

# ✅ Type 3/4 with dynamic format
return self.build_complete_output(
    found_reason=lambda item: f"Signal: {item['signal']} (slack: {item['slack']}ns)",
    missing_reason=lambda item: f"Signal: {item['signal']} (WNS: {item['wns']}ns)"
)
```

**Technical Details:**
- waiver_handler_template.py now wraps lambda with tag application
- When waiver=0 and reason is lambda: returns `lambda item: f"{original_lambda(item)}{tag}"`
- Compatible with all checker types and waiver modes

### README-Driven Example:

**If README "Display Format" shows:**
```
INFO01: "[signal_name] meets timing (slack: [slack]ns)"
ERROR01: "[signal_name] violates timing (WNS: [wns]ns)"
```

**Then implement with lambda:**
```python
FOUND_REASON = lambda item: (
    f"{item.get('signal_name', 'N/A')} meets timing "
    f"(slack: {item.get('slack', 0):.3f}ns)"
)

MISSING_REASON = lambda item: (
    f"{item.get('signal_name', 'N/A')} violates timing "
    f"(WNS: {item.get('wns', 0):.3f}ns)"
)
```

## 5. SEVERITY CONTROL

### For Type 1 Violations (extra_items):
```python
return self.build_complete_output(
    found_items=clean_items,
    extra_items=violations,
    extra_severity=Severity.FAIL,  # ⚠️ REQUIRED for FAIL status
    extra_reason="Violation detected",
    extra_desc="Violations found"
)
```

### For Type 2 Extra Items:
```python
return self.build_complete_output(
    found_items=matched,
    extra_items=extra,
    extra_severity=Severity.WARN,  # Type 2 default
    extra_reason="Not in pattern_items",
    extra_desc="Unexpected items"
)
```

## 6. WAIVER SUPPORT (Type 3/4)

⚠️ **CRITICAL: waived_desc Parameter Usage**

**ALL Types need waived_desc parameter** (but usage differs):
- **Type 1/2** (waivers=0): Used for waive_items comment "No waiver support for this check"
- **Type 3/4** (waivers>0): Used for actual waived violation item descriptions

Example:
```python
# Type 1/2 (waivers=0)
return self.build_complete_output(
    found_desc="Items found",
    missing_desc="Items missing",
    waived_desc="No waiver support"  # ✅ Comment for waive_items section
)

# Type 3/4 (waivers>0)
return self.build_complete_output(
    found_desc="Items found",
    missing_desc="Items missing",
    waived_desc="Waived violations",  # ✅ Description for actually waived items
    waived_base_reason="Violation waived per design approval"  # Type 3/4 ONLY
)
```

⚠️ **CRITICAL: waive_dict Format**

`parse_waive_items()` returns `Dict[str, str]` mapping waiver name to reason:
```python
waive_dict = {
    'item_name_1': 'Waiver reason 1',
    'item_name_2': 'Waiver reason 2'
}
```

❌ **COMMON ERROR**: Treating as `Dict[str, Dict]` with nested 'name' key:
```python
# WRONG! Will cause TypeError: string indices must be integers
for key in waive_dict:
    name = waive_dict[key]['name']  # ❌ WRONG!
    reason = waive_dict[key]['reason']  # ❌ WRONG!
```

✅ **CORRECT Usage**:
```python
# Correct way to iterate
for name, reason in waive_dict.items():
    print(f"{name}: {reason}")

# Correct way to check membership
if item_name in waive_dict:
    reason = waive_dict[item_name]

# Correct way to get unused waivers
used_names = {item['name'] for item in waived_items}
unused_waivers = [name for name in waive_dict if name not in used_names]
```

**Full Example**:
```python
def execute_check(self) -> CheckResult:
    # Parse waivers
    waivers = self.get_waivers()
    waive_dict = self.parse_waive_items(waivers['waive_items'])  # Returns Dict[str, str]
    
    # Apply waivers
    waived = {k: v for k, v in violations.items() if k in waive_dict}
    unwaived = {k: v for k, v in violations.items() if k not in waive_dict}
    unused = {w: {} for w in waive_dict if w not in violations}
    
    return self.build_complete_output(
        found_items=all_items,
        missing_items=unwaived,
        waived_items=waived,
        unused_waivers=unused,
        waive_dict=waive_dict,
        waived_tag="[WAIVER]"  # Type 3/4 use [WAIVER]
    )
```

## 7. FILE PATH HANDLING

Always extract file path from actual input:

```python
def _parse_input_files(self) -> Dict:
    input_files = self.get_input_files()
    file_path = Path(input_files[0])  # First input file
    
    items = {}
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            # ... parse logic ...
            items[name] = {
                "line_number": line_num,
                "file_path": str(file_path),  # Actual file path
                # NOT: "file_path": "N/A"  # ❌ WRONG
            }
    
    return {"items": items, "default_file": str(file_path)}
```

### ⚠️ CRITICAL: Input Files Access Pattern

**COMMON PITFALL - DO NOT USE `self.input_files`:**

```python
# ❌ WRONG - BaseChecker does NOT provide self.input_files attribute
for idx, file_path in enumerate(self.input_files, 1):
    file_name = Path(file_path).name

# ✅ CORRECT - Always get from item_data
input_files_list = self.item_data.get('input_files', [])
for idx, file_path in enumerate(input_files_list, 1):
    file_name = Path(file_path).name
```

**When this pattern is needed:**
- Type 1/2/3/4: When no violations exist, list all clean input files

**Example (Type 1 - no violations):**

```python
def _execute_type1(self) -> CheckResult:
    data = self._parse_input_files()
    violations = data.get('items', [])
    
    if not violations:
        # Need to show all input files as clean/found
        found_items = {}
        input_files_list = self.item_data.get('input_files', [])  # ✅ CORRECT
        for file_path in input_files_list:
            file_name = Path(file_path).name
            found_items[file_name] = {
                'name': f"{file_name} - Clean",
                'line_number': 0,
                'file_path': str(file_path)
            }
        missing_items = []
    else:
        found_items = {}
        missing_items = violations
    
    return self.build_complete_output(
        found_items=found_items,
        missing_items=missing_items,
        ...
    )
```

## 8. DEFAULT FILE (Type 1 Special Case)

For Type 1 checkers that use extra_items, pass default_file:

```python
return self.build_complete_output(
    found_items=clean_items,
    extra_items=violations,
    extra_severity=Severity.FAIL,
    default_file=str(file_path)  # Extract from first item or input
)
```

## 9. CODE STRUCTURE

```python
class CheckerName(BaseChecker, OutputBuilderMixin):
    \"\"\"Checker description.\"\"\"
    
    def execute_check(self) -> CheckResult:
        \"\"\"Main entry point.\"\"\"
        data = self._parse_input_files()
        return self._build_output(data)
    
    def _parse_input_files(self) -> Dict:
        \"\"\"Parse and categorize items with metadata.\"\"\"
        # Parsing logic here
        return {"found": {...}, "missing": {...}}
    
    def _build_output(self, data: Dict) -> CheckResult:
        \"\"\"Build CheckResult from parsed data.\"\"\"
        return self.build_complete_output(
            found_items=data['found'],
            missing_items=data['missing']
        )
```

## 10. COMMON MISTAKES TO AVOID

❌ Don't use List format for new code:
```python
items = ["item1", "item2"]  # Old style
```

❌ Don't forget extra_severity for FAIL violations:
```python
extra_items=violations  # Shows PASS even with errors!
```

❌ Don't lose metadata:
```python
items = {k: {} for k in names}  # No line_number/file_path
```

❌ Don't use "N/A" for file_path when real path available:
```python
"file_path": "N/A"  # Wrong
"file_path": str(actual_path)  # Correct
```

❌ Don't manually format tags:
```python
reason = f"{base}[WAIVER]"  # Wrong - automatic
```

✅ CORRECT PATTERNS:

```python
# Pattern 1: Dict with full metadata
items = {
    name: {
        "line_number": line_num,
        "file_path": str(file_path),
        "line_content": line_text
    }
}

# Pattern 2: One-step output building
return self.build_complete_output(
    found_items=found,
    missing_items=missing
)

# Pattern 3: Explicit FAIL severity
return self.build_complete_output(
    extra_items=violations,
    extra_severity=Severity.FAIL  # Must specify
)
```

═══════════════════════════════════════════════════════════════════════════════
⚠️ CRITICAL: DESCRIPTION/REASON CONSISTENCY ACROSS ALL TYPES
═══════════════════════════════════════════════════════════════════════════════

**RULE: Same category of output MUST use IDENTICAL descriptions across Type 1/2/3/4**

⚠️ **API-026 BREAKING CHANGE**: DESC constants are now split by Type (same as REASON split)

**Previous (API-025):**
```python
FOUND_DESC = "..."      # Unified for all Types
MISSING_DESC = "..."    # Unified for all Types
```

**New (API-026):**
```python
# Type 1/4: Boolean checks
FOUND_DESC_TYPE1_4 = "Tool version found"     # Emphasize "found/not found"
MISSING_DESC_TYPE1_4 = "Tool version not found"

# Type 2/3: Pattern checks
FOUND_DESC_TYPE2_3 = "Required pattern matched (2/2)"  # Emphasize "matched/satisfied"
MISSING_DESC_TYPE2_3 = "Expected pattern not satisfied"

# All Types: Waiver description unified
WAIVED_DESC = "Waived violations"
```

### 📝 WRITING STYLE GUIDELINES (API-026):

⚠️ **CRITICAL**: Follow Type NUMBER strictly - no semantic judgment!

**Type 1/4 (Boolean Checks):**
- Use **generic existence terms**: "found", "exists", "detected", "configured"
- Focus on **presence/absence**
- ✅ Pass `found_desc_type1_4`/`missing_desc_type1_4` to build_complete_output()
- ✅ Pass `found_reason_type1_4`/`missing_reason_type1_4` to build_complete_output()
- Examples:
  ✅ `FOUND_DESC_TYPE1_4 = "Tool version found in configuration"`
  ✅ `MISSING_DESC_TYPE1_4 = "Required item not found in setup file"`
  ✅ `FOUND_REASON_TYPE1_4 = "Tool version found in configuration"`
  ✅ `MISSING_REASON_TYPE1_4 = "Required item not found in setup file"`

**Type 2/3 (Pattern Matching Checks):**
- ✅ **MUST use one of these terms**: matched | satisfied | validated | compliant | fulfilled
  ❌ Avoid generic terms: "found", "exists", "detected"
- Focus on **requirement fulfillment**
- ✅ Pass `found_desc_type2_3`/`missing_desc_type2_3` to build_complete_output()
- ✅ Pass `found_reason_type2_3`/`missing_reason_type2_3` to build_complete_output()
- Include **counts** when checking multiple patterns
- Examples:
  ✅ `FOUND_DESC_TYPE2_3 = "Required pattern matched (2/2)"`
  ✅ `MISSING_DESC_TYPE2_3 = "Expected pattern not satisfied (1/2 missing)"`
  ✅ `FOUND_REASON_TYPE2_3 = "Required pattern matched and validated"`
  ✅ `MISSING_REASON_TYPE2_3 = "Expected pattern not satisfied or missing"

**Type 3/4 (With Waivers):**
- ✅ **MUST pass** all waiver-related parameters:
  - `waived_desc=self.WAIVED_DESC`
  - `waived_base_reason=self.WAIVED_BASE_REASON`
  - `unused_waiver_reason=self.UNUSED_WAIVER_REASON` (if unused_waivers)

**Key Difference:**
- Type 1/4: "X **found**" vs "X **not found**" (binary existence, use defaults)
- Type 2/3: "Pattern **matched**" vs "Pattern **missing**" (requirement satisfaction, custom reasons)

### ❌ WRONG - Different descriptions per Type:

```python
# Type 1
found_desc="Clean timing path groups (analyzed 9 views, 1 clean)"

# Type 4  
found_desc="Clean timing paths"  # ❌ INCONSISTENT!
```

### ✅ CORRECT - Unified descriptions for ALL Types:

```python
# Define ONCE at class level or as constants
FOUND_DESC = "Clean timing path groups"
MISSING_DESC = "Timing violations detected"
WAIVED_DESC = "Waived timing violations"
FOUND_REASON = "Path group meets timing requirements"
MISSING_REASON = "Timing violation detected"
WAIVED_BASE_REASON = "Timing violation waived per design approval"

# Type 1
return self.build_complete_output(
    found_items=found_items,
    missing_items=missing_items,
    found_desc=FOUND_DESC,          # Same
    missing_desc=MISSING_DESC,      # Same
    found_reason=FOUND_REASON,      # Same
    missing_reason=MISSING_REASON   # Same
)

# Type 3
return self.build_complete_output(
    found_items=found_clean,
    missing_items=missing_patterns,
    waived_items=waived_items,
    found_desc=FOUND_DESC,          # Same as Type 1
    missing_desc=MISSING_DESC,      # Same as Type 1
    waived_desc=WAIVED_DESC,        # Same as Type 4
    found_reason=FOUND_REASON,      # Same as Type 1
    missing_reason=MISSING_REASON,  # Same as Type 1
    waived_base_reason=WAIVED_BASE_REASON  # Same as Type 4
)

# Type 4
return self.build_complete_output(
    found_items=found_items,
    missing_items=unwaived_items,
    waived_items=waived_items,
    found_desc=FOUND_DESC,          # Same as Type 1
    missing_desc=MISSING_DESC,      # Same as Type 1
    waived_desc=WAIVED_DESC,        # Same as Type 3
    found_reason=FOUND_REASON,      # Same as Type 1
    missing_reason=MISSING_REASON,  # Same as Type 1
    waived_base_reason=WAIVED_BASE_REASON  # Same as Type 3
)
```

### WHY THIS MATTERS:

1. **User Consistency**: Users see same log format regardless of configuration
2. **Report Clarity**: ERROR01/INFO01/WARN01 descriptions stay consistent
3. **Maintainability**: Change description in ONE place, affects all Types
4. **Testing**: Easier to verify outputs when descriptions are predictable

═══════════════════════════════════════════════════════════════════════════════
VALIDATION CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

Before submitting generated code, verify:

✅ All items use Dict format with metadata
✅ line_number and file_path preserved from parsing
✅ extra_severity=Severity.FAIL set for violations
✅ build_complete_output() used (not manual building)
✅ default_file extracted from actual input file
✅ No hardcoded "N/A" where real path available
✅ Parsing logic extracts metadata in one pass
✅ Code follows three-method structure (execute → parse → build)
✅ **SAME descriptions used across ALL Type 1/2/3/4 implementations**

═══════════════════════════════════════════════════════════════════════════════
"""


def get_template_instructions() -> str:
    """Get template generation instructions for API v2.0."""
    return TEMPLATE_V2_INSTRUCTIONS


def get_type_specific_hints(checker_type: int) -> str:
    """Get type-specific generation hints."""
    hints = {
        1: """
TYPE 1 SPECIFIC HINTS:
----------------------
⚠️ CRITICAL: Type 1 has STRICT CONFIGURATION REQUIREMENTS!

MANDATORY CONFIGURATION:
1. requirements.value MUST be "N/A" (not a number)
2. When waivers.value = 0 (waiver=0 mode):
   - waive_items MUST contain a comment explaining why no waivers
   - Example: "Timing violations are acceptable for this design phase"

Configuration Example:
```yaml
requirements:
  pattern_items: []     # Empty for Type 1
  value: N/A           # ⚠️ MUST be N/A (not a number!)

waivers:
  value: 0             # waiver=0 mode
  waive_items:
    - "Timing violations are acceptable for this design phase"  # Comment required!
```

COMMON MISTAKES:
❌ value: 0 or value: 1  # Wrong - Type 1 doesn't use numeric value
❌ waive_items: []       # Wrong - needs comment when value=0
✅ value: N/A            # Correct
✅ waive_items: ["comment"]  # Correct for waiver=0

IMPLEMENTATION HINTS:
- Use `missing_items` for violations (semantic failures)
- OR use `extra_items` with `extra_severity=Severity.FAIL` (unexpected violations)
- Always set `default_file` when using extra_items
- Waiver=0 mode automatically supported (no code changes needed)

Code Example:
```python
def _execute_type1(self) -> CheckResult:
    data = self._parse_input_files()
    clean_items = data.get('clean_items', {})
    violations = data.get('violations', {})
    
    # Type 1: violations are missing_items or extra_items
    return self.build_complete_output(
        found_items=clean_items,
        missing_items=violations,  # OR extra_items=violations + extra_severity=FAIL
        found_desc=self.FOUND_DESC,
        missing_desc=self.MISSING_DESC,
        found_reason=self.FOUND_REASON,
        missing_reason=self.MISSING_REASON,
        default_file=data.get('default_file', 'N/A')  # For extra_items
    )
```

⚠️ VALIDATION CHECKLIST:
✅ requirements.value = "N/A" (not 0, not 1)
✅ waive_items has comment when waivers.value = 0
✅ Code uses missing_items OR (extra_items + extra_severity=FAIL)
""",
        2: """
TYPE 2 SPECIFIC HINTS:
----------------------
⚠️ CRITICAL: Type 2 pattern_items matching strategy depends on Check Logic!

MATCHING STRATEGY SELECTION (based on README Check Logic):
1. EXACT MATCH: When pattern_items are concrete names/identifiers to match
   - Example: Block names like 'cdn_hs_phy_data_slice'
   - Example: Cell names, instance names, specific identifiers
   - Use: `if pattern.lower() == item_name.lower()`

2. CONTAINS/SUBSTRING MATCH: When pattern_items are partial strings to search
   - Example: Looking for keywords in timing views
   - Example: Searching for patterns in error messages
   - Use: `if pattern.lower() in item_str.lower()`

3. REGEX MATCH: When pattern_items contain wildcards or regex patterns
   - Example: 'func_rc*' to match 'func_rcss', 'func_rcff'
   - Use: `if re.search(pattern, item_str, re.IGNORECASE)`

⚠️ HOW TO DECIDE: Read the README Check Logic description carefully!
- "Block name (e.g: cdn_hs_phy_data_slice)" → EXACT MATCH
- "Search for pattern in timing reports" → CONTAINS/SUBSTRING MATCH
- "Match wildcard pattern" → REGEX MATCH

MANDATORY STEPS:
1. Read Check Logic to determine matching strategy
2. Get pattern_items and expected value
3. For each pattern, match against parsed items using appropriate strategy
4. Count matched patterns
5. Compare count vs requirements.value
6. PASS only if count == value

Example 1 - EXACT MATCH (block names):
```yaml
# README says: "Block name (e.g: cdn_hs_phy_data_slice)"
pattern_items:
  - cdn_hs_phy_data_slice   # Exact block name to find
  - cdn_hs_phy_ctrl_slice   # Another exact block name
value: 2
```

Example 2 - SUBSTRING MATCH (descriptive patterns):
```yaml
# README says: "Find timing views matching patterns"
pattern_items:
  - "View 'func_rcss...' path_group 'reg2reg' setup"  # Descriptive string
  - "View 'func_rcff...' path_group 'default' hold"   # NOT exact item name
value: 2
```

CORRECT Implementation (EXACT MATCH - for block names, identifiers):
```python
def _execute_type2(self) -> CheckResult:
    data = self._parse_input_files()
    items = data.get('items', [])
    
    requirements = self.item_data.get('requirements', {})
    pattern_items = requirements.get('pattern_items', [])
    expected_value = requirements.get('value', 'N/A')
    
    found_items = {}
    missing_patterns = []
    
    for pattern in pattern_items:
        matched = False
        for item in items:
            item_name = item['name']
            # EXACT MATCH (case-insensitive) - use when pattern_items are concrete names
            if pattern.lower() == item_name.lower():
                found_items[pattern] = {
                    'name': item_name,
                    'line_number': item.get('line_number', 0),
                    'file_path': item.get('file_path', 'N/A')
                }
                matched = True
                break
        
        if not matched:
            missing_patterns.append(pattern)
    
    actual_count = len(found_items)
    
    return self.build_complete_output(
        found_items=found_items,
        missing_items=missing_patterns,
        found_desc=f"Found ({actual_count}/{expected_value})",
        missing_desc=f"Missing ({len(missing_patterns)} patterns not matched)",
        found_reason=self.FOUND_REASON,
        missing_reason=self.MISSING_REASON
    )
```

ALTERNATIVE Implementation (SUBSTRING MATCH - for descriptive patterns):
```python
def _execute_type2(self) -> CheckResult:
    # ... same setup ...
    
    for pattern in pattern_items:
        matched = False
        for item in items:
            # Build searchable string from item
            item_str = f"{item['view']}: {item['path_group']} ({item['timing_type']})"
            # SUBSTRING MATCH - use when pattern_items are descriptive strings
            if pattern.lower() in item_str.lower():
                found_items[item['name']] = {...}
                matched = True
                break
    # ... rest same ...
```

⚠️ KEY POINTS:
- READ the Check Logic to decide: EXACT vs SUBSTRING vs REGEX match
- "Block name (e.g: xxx)" → EXACT MATCH with `==`
- "Search for pattern..." → SUBSTRING MATCH with `in`
- Must compare len(found_items) vs requirements.value
- PASS only if count matches exactly

⚠️ VALIDATION CHECKLIST:
✅ Matching strategy matches Check Logic description
✅ Pattern matching case-insensitive
✅ Count comparison vs requirements.value
""",
        3: """
TYPE 3 SPECIFIC HINTS:
----------------------
⚠️ CRITICAL: Type 3 = Type 2 + Waiver Logic

🔴 **CRITICAL CONCEPT - READ THIS FIRST!**
═══════════════════════════════════════════════════════════════════════════════
WAIVERS TARGET FAIL PATTERNS (missing_items), NOT VIOLATIONS!

❌ WRONG UNDERSTANDING:
   "Waive violations" = Items that exist but shouldn't
   
✅ CORRECT UNDERSTANDING:
   "Waive FAIL patterns" = Expected patterns that are missing/violated
   
Type 3 Logic:
- Pattern found + clean → found_items (PASS) ✅
- Pattern NOT found OR violated + waived → waived_items (PASS) ✅  
- Pattern NOT found OR violated + NOT waived → missing_items (FAIL) ❌

Waiver targets: missing_items (what makes check FAIL)
NOT: violations or extra_items (unexpected items)
═══════════════════════════════════════════════════════════════════════════════

⚠️ MATCHING STRATEGY: Same as Type 2, depends on Check Logic!
- "Block name (e.g: xxx)" → EXACT MATCH: `pattern.lower() == item_name.lower()`
- "Search for pattern..." → SUBSTRING MATCH: `pattern.lower() in item_str.lower()`
- READ the Check Logic description to decide!

Type 3 Logic:
1. ONLY check patterns in pattern_items (NOT all violations!)
2. For each required pattern (using appropriate match strategy):
   - Clean (no violation) → satisfied ✅
   - Has violation but waived → satisfied ✅
   - Has violation but NOT waived → unsatisfied ❌
3. PASS if: ALL required patterns are satisfied (clean or waived)

🔴 **CRITICAL: REPORT ALL FOUND ITEMS, NOT JUST PATTERN MATCHES!**
═══════════════════════════════════════════════════════════════════════════════
🚨 MOST COMMON TYPE 3 BUG: Only reporting items that match pattern_items!

Type 3 must report ALL items found in input files, not just pattern matches!

Real-world Impact (IMP-2-0-0-11):
- User has pattern_items: ["PLN3ELO_17M_...014_ANT.11_2a.encrypt"]
- File actually contains: "PLN6FF_15M_...001_ANT.11a.encrypt"
- If you only report pattern matches:
  ❌ Output shows: "ERROR01: Pattern not found" 
  ❌ Output hides: "INFO01: Found PLN6FF_15M..."
  ❌ User has NO IDEA what's actually in the file!
- With ALL items reported:
  ✅ Output shows: "ERROR01: Pattern PLN3ELO not found"
  ✅ Output shows: "INFO01: Found PLN6FF_15M..." 
  ✅ User can compare and debug the mismatch!

📋 MANDATORY Type 3 BEHAVIOR:

found_items MUST contain:
1. Items matching required patterns (if found)
2. Items NOT matching patterns (STILL REPORT THESE!)
   → Users need to see what's actually in the file!

missing_items MUST contain:
- Required patterns (from pattern_items) that are not found/violated + not waived

waived_items MUST contain:
- Required patterns (from pattern_items) that are not found/violated + waived

❌ WRONG IMPLEMENTATION (DO NOT USE):
```python
# This ONLY reports pattern matches - missing other items!
found_items = {}
for pattern in pattern_items:
    for item in items:
        if matches(item, pattern):
            found_items[item] = ...  # Where are the other items?!
```

✅ CORRECT IMPLEMENTATION:
```python
# Step 1: Report ALL items found in file (complete visibility!)
all_found_items = {}
for item in items:
    all_found_items[item['name']] = {
        'name': item['name'],
        'line_number': item.get('line_number', 0),
        'file_path': item.get('file_path', 'N/A')
    }

# Step 2: Check which patterns are satisfied
missing_patterns = []
waived_patterns = []

for pattern in pattern_items:
    pattern_matched = False
    for item in items:
        if matches_pattern(item, pattern):  # Use appropriate match strategy
            pattern_matched = True
            break
    
    if not pattern_matched:
        # Pattern not found - check if waived
        if pattern in waive_dict:
            waived_patterns.append(pattern)
        else:
            missing_patterns.append(pattern)

# Step 3: Build output with ALL items
return self.build_complete_output(
    found_items=all_found_items,      # ALL items (complete visibility!)
    missing_items=missing_patterns,    # Patterns not found + not waived
    waived_items=waived_patterns,      # Patterns not found + waived
    waive_dict=waive_dict,
    ...
)
```

🔑 KEY PRINCIPLE:
- found_items = What's ACTUALLY in the file (complete list)
- missing_items = What's REQUIRED but not satisfied (from pattern_items)
- Users need BOTH to understand the situation!
═══════════════════════════════════════════════════════════════════════════════

MANDATORY STEPS:
1. Parse violations and clean items from input files
2. Get pattern_items from requirements
3. Get waive_items and parse into waive_dict
4. For each pattern in pattern_items:
   - Match using appropriate strategy (EXACT vs SUBSTRING based on Check Logic)
   - Check if clean → add to found_clean
   - Else check if has waived violation → add to found_waived
   - Else has unwaived violation → add to missing_patterns
5. **IMPORTANT**: Track ALL items found (pattern + non-pattern) for INFO
6. Build output with found/missing/waived/unused categories

COMMON MISTAKE: Using wrong matching strategy (substring when exact needed, or vice versa)
CORRECT: Read Check Logic to determine: EXACT MATCH vs SUBSTRING MATCH

Waiver Data Structure:
```yaml
waivers:
  waive_items:
    - "net_name1: violation details"
    - "net_name2: violation details"
```

🔴 **CRITICAL: DATA FORMAT SPECIFICATIONS**
═══════════════════════════════════════════════════════════════════════════════
MANDATORY DATA FORMATS (Type 3):

```python
# After parsing waivers
waive_dict: Dict[str, str] = {'name': 'reason'}  # NOT Dict[str, Dict]!

# Item collections (choose ONE format and be consistent)
found_clean: Dict[str, Dict] = {'item1': {'name': '...', 'line_number': 0}}
missing_patterns: Dict[str, Dict] = {'item2': {'name': '...', 'line_number': 0}}
found_waived: Dict[str, Dict] = {'item3': {'name': '...', 'line_number': 0}}

# OR use List[str] if no metadata needed:
found_clean: List[str] = ['item1', 'item2']
missing_patterns: List[str] = ['item3', 'item4']
found_waived: List[str] = ['item5', 'item6']

# Unused waivers (simple format)
unused_waivers: List[str] = ['waiver1', 'waiver2']  # Simple case
# OR with metadata:
unused_waivers: Dict[str, Dict] = {
    'waiver1': {'line_number': 0, 'reason': 'text'}
}
```

⚠️ COMMON MISTAKES:
❌ waive_dict.values() are dicts → NO! They are strings!
❌ Mix formats (Dict for waived, List for missing) → Be consistent!
❌ unused_waivers as Dict[str, str] → Use List[str] or Dict[str, Dict]!
═══════════════════════════════════════════════════════════════════════════════

CORRECT Implementation:
```python
def _execute_type3(self) -> CheckResult:
    # Step 1: Parse violations and clean items
    data = self._parse_input_files()
    clean_items = data.get('clean_items', [])  # Items without violations
    violations = data.get('items', [])          # Items with violations
    
    # Step 2: Get requirements and waivers
    requirements = self.item_data.get('requirements', {})
    pattern_items = requirements.get('pattern_items', [])
    
    waivers = self.get_waivers()
    waive_items_list = waivers.get('waive_items', [])
    waive_dict = self.parse_waive_items(waive_items_list)
    
    # Step 3: Track pattern satisfaction
    found_clean = {}      # Patterns satisfied by clean items
    found_waived = {}     # Patterns satisfied by waived violations
    missing_patterns = {} # Patterns with unwaived violations
    other_waived = {}     # Waived violations NOT in pattern_items (for info)
    used_waiver_patterns = set()
    
    # Step 4: Check each required pattern
    for pattern in pattern_items:
        pattern_satisfied = False
        
        # Check if pattern has clean match
        for item in clean_items:
            item_str = f"View '{item['view']}' path_group '{item['path_group']}' {item['timing_type']}"
            if pattern in item_str:
                item_name = f"View '{item['view']}' path_group '{item['path_group']}' {item['timing_type']}: clean"
                found_clean[item_name] = {'name': item_name, 'line_number': item.get('line_number', 0)}
                pattern_satisfied = True
                break
        
        # If not clean, check if pattern has waived violation
        if not pattern_satisfied:
            for violation in violations:
                vio_str = f"View '{violation['view']}' path_group '{violation['path_group']}' {violation['timing_type']}"
                if pattern in vio_str:
                    vio_name = f"View '{violation['view']}' path_group '{violation['path_group']}' {violation['timing_type']}: violation"
                    vio_data = {'name': vio_name, 'line_number': violation.get('line_number', 0)}
                    
                    # Check if waived
                    matched_waiver = None
                    for waiver_pattern in waive_dict.keys():
                        if self.match_waiver_entry(vio_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                            matched_waiver = waiver_pattern
                            used_waiver_patterns.add(waiver_pattern)
                            break
                    
                    if matched_waiver:
                        found_waived[vio_name] = vio_data
                        pattern_satisfied = True
                    else:
                        missing_patterns[vio_name] = vio_data
                    break
    
    # Step 5: Track other waived violations (not in pattern_items, for info only)
    for violation in violations:
        vio_str = f"View '{violation['view']}' path_group '{violation['path_group']}' {violation['timing_type']}"
        is_pattern_violation = any(pattern in vio_str for pattern in pattern_items)
        if not is_pattern_violation:
            vio_name = f"View '{violation['view']}' path_group '{violation['path_group']}' {violation['timing_type']}: violation"
            for waiver_pattern in waive_dict.keys():
                if self.match_waiver_entry(vio_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                    used_waiver_patterns.add(waiver_pattern)
                    other_waived[vio_name] = {'name': vio_name}
                    break
    
    # Step 6: Find unused waivers
    unused_waivers = {
        w: {'line_number': 0, 'reason': waive_dict[w]}
        for w in waive_dict.keys()
        if w not in used_waiver_patterns
    }
    
    # Step 7: Build output
    all_waived = {**found_waived, **other_waived}
    
    return self.build_complete_output(
        found_items=found_clean,         # Patterns satisfied by clean → INFO
        missing_items=missing_patterns,  # Patterns with unwaived violations → FAIL
        waived_items=all_waived,         # Waived violations (pattern + others) → INFO
        unused_waivers=unused_waivers,   # Unused waivers → WARN
        waive_dict=waive_dict,
        waived_tag="[WAIVER]",
        
        # ⚠️ DON'T use lambda for waived_base_reason (use string)
        found_reason=lambda item: f"Pattern satisfied (clean)",
        missing_reason=lambda item: f"Pattern violation (unwaived)",
        waived_base_reason="Timing violation waived",  # String, not lambda!
        unused_waiver_reason="Waiver defined but no violation matched",
        
        found_desc=f"Required patterns satisfied: {len(found_clean)}/{len(pattern_items)}",
        missing_desc="Required patterns with unwaived violations",
        waived_desc="Waived violations (may include non-pattern violations for info)"
    )
```

⚠️ KEY POINTS:
- Type 3 ONLY checks patterns in pattern_items (NOT all violations)
- Pattern satisfied = clean OR waived
- PASS if ALL required patterns are satisfied
- Other violations (not in pattern_items) can be shown for info but don't affect PASS/FAIL
- waived_tag="[WAIVER]" is MANDATORY for Type 3
- **USE LAMBDA for item-specific reasons**: found_reason, missing_reason
- **DON'T use lambda for waived_base_reason**: Use string instead (API limitation)
- **DON'T use lambda for descriptions**: found_desc, missing_desc, etc.

⚠️ COMMON API MISTAKES (DO NOT MAKE THESE!):
❌ waive_dict = self.parse_waive_items()  # WRONG! Missing argument!
❌ waive_items_raw = self.get_waive_items()  # WRONG! Converts dict to string for dict-format waive_items!
✅ waivers = self.get_waivers()
✅ waive_items_raw = waivers.get('waive_items', [])  # CORRECT! Preserves dict format
✅ waive_dict = self.parse_waive_items(waive_items_raw)

❌ waived_base_reason=lambda item: ...  # WRONG! Only str supported, NOT Callable!
✅ waived_base_reason="Violation waived"  # Correct - use static string

VALIDATION CHECKLIST:
✅ All violations parsed with metadata
✅ waive_dict created from waive_items
✅ Three-way split: waived, unwaived, unused
✅ waived_tag="[WAIVER]" specified
✅ All three categories passed to build_complete_output()
✅ Lambda used for *_reason parameters (NOT *_desc!)
""",
        4: """
TYPE 4 SPECIFIC HINTS:
----------------------
⚠️ Type 4: Boolean Check with Waiver Logic (Type 1 + Waivers)

🔴 **CRITICAL CONCEPT - READ THIS FIRST!**
═══════════════════════════════════════════════════════════════════════════════
WAIVERS TARGET FAIL CONDITION (no items found OR unwaived violations)!

❌ WRONG: Waive all found items/violations
✅ CORRECT: Waive violations that would cause FAIL

Type 4 Flow:
- No items found + no waiver → FAIL ❌
- No items found + waived → PASS ✅ (waive the FAIL condition)
- Items found with violations + all waived → PASS ✅
- Items found with violations + some NOT waived → FAIL ❌
═══════════════════════════════════════════════════════════════════════════════

CONCEPT:
- **Type 4 = Type 1 + Waiver Logic**
- Type 1: Checks ALL items, any violation = FAIL
- Type 4: Checks ALL items, but violations can be waived
  → Clean items: PASS ✅
  → Violations + waived: PASS ✅
  → Violations + NOT waived: FAIL ❌
- PASS if: All violations are either clean OR waived
- FAIL if: Any unwaived violations exist

CONFIGURATION:
```yaml
requirements:
  pattern_items: []     # Empty for Type 4 (checks ALL, not patterns)
  value: N/A           # ⚠️ MUST be N/A (boolean check, not value check)

waivers:
  value: 3             # Count of waived items (or N/A if no limit)
  waive_items:         # List of specific violations to waive
    - "View 'ss_0p8v_125c' path_group 'reg2reg' setup: WNS=-0.123ns (5 violations)"
    - "View 'ff_0p9v_m40c' path_group 'in2reg' hold: WNS=-0.056ns (2 violations)"
```

🔴 **DATA FORMAT SPECIFICATIONS (Type 4)**
═══════════════════════════════════════════════════════════════════════════════
```python
# After parsing waivers
waive_dict: Dict[str, str] = {'name': 'reason'}  # NOT Dict[str, Dict]!

# Item collections (consistent format)
found_items: Dict[str, Dict] = {'clean1': {'name': '...', 'line_number': 0}}
waived_items: Dict[str, Dict] = {'vio1': {'name': '...', 'line_number': 0}}
unwaived_items: Dict[str, Dict] = {'vio2': {'name': '...', 'line_number': 0}}

# Unused waivers
unused_waivers: List[str] = ['waiver1']  # OR Dict[str, Dict] with metadata
```
═══════════════════════════════════════════════════════════════════════════════

LOGIC FLOW:
1. Parse input → extract ALL violations and clean items
2. Classify clean items → found_items
3. For each violation:
   - Match against waive_items using pattern matching
   - Matched → waived_items ✅
   - Unmatched → unwaived_items ❌ (FAIL = missing_items)
4. Track unused waivers → unused_waivers
5. PASS if unwaived_items (missing_items) is empty

IMPLEMENTATION PATTERN:
```python
def _execute_type4(self) -> CheckResult:
    ```
    Type 4: Boolean check with waiver logic.
    
    Global check of all violations with waiver logic:
    - Clean items → found_items
    - Waived violations → waived_items
    - Unwaived violations → missing_items (FAIL)
    ```
    # 1. Parse input
    data = self._parse_input_files()
    all_violations = data.get('items', [])      # All violations
    clean_items = data.get('clean_items', [])   # Clean items
    
    # 2. Parse waivers
    waivers = self.get_waivers()
    waive_items_raw = waivers.get('waive_items', [])
    waive_dict = self.parse_waive_items(waive_items_raw)
    
    # 3. Build found_items from clean items
    found_items = {}
    for item in clean_items:
        item_name = item.get('name', str(item))
        found_items[item_name] = {
            'name': item_name,
            'line_number': item.get('line_number', 0),
            'file_path': item.get('file_path', 'N/A')
        }
    
    # 4. Apply waivers to violations
    waived_items = {}
    unwaived_items = {}
    used_waiver_patterns = set()
    
    for violation in all_violations:
        vio_name = violation.get('name', str(violation))
        vio_data = {
            'name': vio_name,
            'line_number': violation.get('line_number', 0),
            'file_path': violation.get('file_path', 'N/A')
        }
        
        # Check if this violation matches any waiver
        matched_waiver = None
        for waiver_pattern in waive_dict.keys():
            if self.match_waiver_entry(vio_name, {waiver_pattern: waive_dict[waiver_pattern]}):
                matched_waiver = waiver_pattern
                used_waiver_patterns.add(waiver_pattern)
                break
        
        if matched_waiver:
            waived_items[vio_name] = vio_data
        else:
            unwaived_items[vio_name] = vio_data
    
    # 5. Find unused waivers
    unused_waivers = {
        waiver_name: {
            'line_number': 0,
            'file_path': 'N/A',
            'reason': waive_dict[waiver_name]
        }
        for waiver_name in waive_dict.keys()
        if waiver_name not in used_waiver_patterns
    }
    
    # 6. Build output
    return self.build_complete_output(
        found_items=found_items,
        missing_items=unwaived_items,
        waived_items=waived_items,
        unused_waivers=unused_waivers,
        waive_dict=waive_dict,
        found_desc="Clean items (no violations)",
        missing_desc="Unwaived violations",
        waived_desc="Waived violations",
        found_reason="Item is clean",
        missing_reason="Violation detected (not waived)",
        waived_base_reason="Violation waived"
    )
```

⚠️ KEY DIFFERENCES FROM TYPE 3:
- Type 3: Only checks pattern_items (specific patterns)
- Type 4: Checks ALL violations (global check)
- Both use waive_items for waiver matching

VALIDATION CHECKLIST:
✅ requirements.value = "N/A" (not 0, not 1)
✅ waivers.value is count (or N/A)
✅ waive_items contains specific violation patterns
✅ Code checks ALL violations (not just patterns)
✅ Waiver matching uses match_waiver_entry()
✅ Clean items go to found_items
✅ Unwaived violations go to missing_items (FAIL)
"""
    }
    
    return hints.get(checker_type, "")
