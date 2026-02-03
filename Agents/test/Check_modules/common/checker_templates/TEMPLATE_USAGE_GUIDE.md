# OutputBuilderTemplate Usage Guide

## Overview

The `OutputBuilderTemplate` provides a unified API for building CheckResult outputs in AutoGenChecker. This guide covers common usage patterns, best practices, and troubleshooting.

**Current Version**: 2.0.0  
**Date**: December 16, 2025

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core Concepts](#core-concepts)
3. [Common Patterns](#common-patterns)
4. [Advanced Features](#advanced-features)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)

---

## Quick Start

### Minimal Example

```python
from base_checker import BaseChecker
from output_builder_template import OutputBuilderMixin

class MyChecker(BaseChecker, OutputBuilderMixin):
    def execute_check(self):
        # Parse your data
        found_items = {"item1": {"line_number": 10, "file_path": "file.txt"}}
        missing_items = {"item2": {"line_number": 20, "file_path": "file.txt"}}
        
        # Build complete output in one call
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items
        )
```

That's it! The template automatically:
- Creates detail items with metadata
- Generates INFO/ERROR groups
- Calculates pass/fail status
- Formats output for log and report

---

## Core Concepts

### 1. Item Categories

Items are categorized into five types:

| Category | Type | Purpose | Example |
|----------|------|---------|---------|
| `found_items` | Dict/List | Items that passed checks | Clean timing paths |
| `missing_items` | Dict/List | Items that failed checks | Missing constraints |
| `waived_items` | Dict/List | Items waived by waivers | Waived violations |
| `unused_waivers` | Dict/List | Waivers with no matches | Obsolete waiver patterns |
| `extra_items` | Dict/List | Unexpected items (Type 2) | Items not in pattern_items |

### 2. Metadata Structure

**Dict Format (v2.0 - Recommended)**:
```python
items = {
    "item_name": {
        "line_number": 123,        # Required for line display
        "file_path": "/path/file", # Required for file display
        "line_content": "...",     # Optional, for context
        # Add custom fields as needed
    }
}
```

**List Format (v1.x - Backward Compatible)**:
```python
items = ["item1", "item2"]  # Auto-converted to Dict
```

### 3. Severity Levels

```python
Severity.INFO  # Found items, waived items
Severity.WARN  # Unused waivers, Type 2 extra_items (default)
Severity.FAIL  # Missing items, Type 1 extra_items (violations)
```

### 4. Tag System

| Tag | Usage | Display |
|-----|-------|---------|
| `[WAIVER]` | Type 3/4 waived items (normal) | Report only |
| `[WAIVED_INFO]` | Type 1/2 waive_items (waiver=0) | Report only |
| `[WAIVED_AS_INFO]` | Auto-converted violations (waiver=0) | Report only |

**Log files show clean names, report files show tags in reason field.**

---

## Common Patterns

### Pattern 1: Type 1 Simple Check

**Scenario**: Check if required items exist (e.g., timing paths are clean).

```python
class TimingChecker(BaseChecker, OutputBuilderMixin):
    def execute_check(self):
        # Parse timing report
        clean_paths = self.parse_clean_paths()
        violated_paths = self.parse_violations()
        
        return self.build_complete_output(
            found_items=clean_paths,
            missing_items=violated_paths,
            found_reason="Path group clean",
            missing_reason="Path group has violations",
            found_desc="Clean path groups",
            missing_desc="Violated path groups"
        )
```

**Output Example**:
```
FAIL:CHECKER:Description
CHECKER-ERROR01: Violated path groups:
  Severity: Fail Occurrence: 2
  - setup_path: slack=-0.1ns (10 violations)
  - hold_path: slack=-0.05ns (5 violations)
```

### Pattern 2: Type 1 with Violations as Extra Items

**Scenario**: Type 1 checker where violations are "extra" items not expected.

```python
class CleanChecker(BaseChecker, OutputBuilderMixin):
    def execute_check(self):
        clean_items = self.parse_clean_items()
        violations = self.parse_violations()
        
        return self.build_complete_output(
            found_items=clean_items,
            extra_items=violations,
            extra_severity=Severity.FAIL,  # Critical - must be FAIL
            extra_reason="Violation detected",
            extra_desc="Violations found"
        )
```

**Why use extra_items?** When semantically the violations are "extra" things that shouldn't exist, not "missing" things that should exist.

### Pattern 3: Type 2 Pattern Matching

**Scenario**: Check items against expected pattern_items.

```python
class PatternChecker(BaseChecker, OutputBuilderMixin):
    def execute_check(self):
        pattern_items = self.get_requirements()['pattern_items']
        found_items = self.parse_found_items()
        
        # Categorize
        matched = {k: v for k, v in found_items.items() if k in pattern_items}
        extra = {k: v for k, v in found_items.items() if k not in pattern_items}
        missing = {p: {} for p in pattern_items if p not in found_items}
        
        return self.build_complete_output(
            found_items=matched,
            missing_items=missing,
            extra_items=extra,
            extra_severity=Severity.WARN,  # Type 2 default
            extra_reason="Not in pattern_items",
            extra_desc="Unexpected items"
        )
```

**Output Example**:
```
PASS:CHECKER:Description
CHECKER-INFO01: Items found: 10
CHECKER-WARN01: Unexpected items:
  Severity: Warn Occurrence: 2
  - extra_item1
  - extra_item2
```

### Pattern 4: Type 3 with Waivers

**Scenario**: Check with pattern-based waivers.

```python
class WaiverChecker(BaseChecker, OutputBuilderMixin):
    def execute_check(self):
        all_items = self.parse_all_items()
        pattern_items = self.get_requirements()['pattern_items']
        
        # Find violations
        violations = {k: v for k, v in all_items.items() if k not in pattern_items}
        
        # Apply waivers
        waivers = self.get_waivers()
        waive_dict = self.parse_waive_items(waivers['waive_items'])
        
        waived = {k: v for k, v in violations.items() if k in waive_dict}
        unwaived = {k: v for k, v in violations.items() if k not in waive_dict}
        
        # Find unused waivers
        unused = {w: {} for w in waive_dict.keys() if w not in violations}
        
        return self.build_complete_output(
            found_items=all_items,
            missing_items=unwaived,
            waived_items=waived,
            unused_waivers=unused,
            waive_dict=waive_dict,
            waived_tag="[WAIVER]",  # Type 3/4 use [WAIVER]
            waived_base_reason="Item not in pattern",
            missing_reason="Unwaived violation"
        )
```

**Output Example (Normal Mode)**:
```
FAIL:CHECKER:Description
CHECKER-INFO01: Items waived:
  Severity: Info Occurrence: 1
  - waived_item[WAIVER]
CHECKER-ERROR01: Unwaived violations:
  Severity: Fail Occurrence: 2
  - violation1
  - violation2
CHECKER-WARN01: Unused waivers:
  Severity: Warn Occurrence: 1
  - unused_pattern[WAIVER]
```

### Pattern 5: Waiver=0 Mode (Type 1/2)

**Scenario**: Waiver value set to 0, all violations converted to INFO.

```python
# Configuration file
waivers:
  value: 0
  waive_items:
  - "All violations acceptable for current design phase"
```

**Checker Code (No Changes Needed!)**:
```python
class WaiverZeroChecker(BaseChecker, OutputBuilderMixin):
    def execute_check(self):
        violations = self.parse_violations()
        
        # Same code as normal mode
        return self.build_complete_output(
            found_items={},
            missing_items=violations
        )
```

**Output Example (Waiver=0 Mode)**:
```
PASS:CHECKER:Description
CHECKER-INFO01: [WAIVED_INFO]: Waived information:
  Severity: Info Occurrence: 1
  - All violations acceptable for current design phase
CHECKER-INFO02: [WAIVED_AS_INFO]: Items not found:
  Severity: Info Occurrence: 2
  - violation1[WAIVED_AS_INFO]
  - violation2[WAIVED_AS_INFO]
```

**Template automatically detects waiver=0 and converts FAIL→INFO!**

---

## Advanced Features

### Custom Name Extraction

When item names need transformation from metadata:

```python
def extract_display_name(item_name: str, metadata: Dict) -> str:
    """Extract custom display name from metadata."""
    line_content = metadata.get('line_content', '')
    if match := re.search(r'File: (\S+)', line_content):
        return match.group(1)
    return item_name

return self.build_complete_output(
    found_items=items,
    name_extractor=extract_display_name
)
```

### Multiple Severity Levels

Control severity for different item types:

```python
return self.build_complete_output(
    missing_items=critical_missing,
    extra_items=warnings,
    missing_severity=Severity.FAIL,  # Critical failures
    extra_severity=Severity.WARN     # Minor warnings
)
```

### Metadata Helper

Use helper method for parsing:

```python
metadata = self.extract_metadata_from_lines(
    lines=file_lines,
    pattern=r'Item: (\w+) at line (\d+)',
    file_path=report_path
)
# Returns: {"item_name": {"line_number": N, "file_path": path}}
```

### Custom Group Descriptions

Override default descriptions:

```python
return self.build_complete_output(
    found_items=found,
    missing_items=missing,
    found_desc="✅ Successfully verified items",
    missing_desc="❌ Items requiring attention",
    waived_desc="⚠️ Waived for current phase"
)
```

---

## Troubleshooting

### Issue 1: Shows PASS but has ERROR01 group

**Symptom**: Checker shows `PASS` but ERROR01 group has violations.

**Cause**: Using `extra_items` without `extra_severity=Severity.FAIL`.

**Solution**:
```python
# Wrong
return self.build_complete_output(
    extra_items=violations  # Defaults to WARN
)

# Correct
return self.build_complete_output(
    extra_items=violations,
    extra_severity=Severity.FAIL  # Force FAIL status
)
```

### Issue 2: Metadata not displayed

**Symptom**: Source file/line not showing in details.

**Cause**: Using List format instead of Dict.

**Solution**:
```python
# Wrong
items = ["item1", "item2"]

# Correct
items = {
    "item1": {"line_number": 10, "file_path": "file.txt"},
    "item2": {"line_number": 20, "file_path": "file.txt"}
}
```

### Issue 3: Tag duplicated in log

**Symptom**: Tags like `[WAIVER]` appear twice in log file.

**Solution**: This was a bug in v1.x, fixed in v2.0. Upgrade to v2.0.

### Issue 4: Waiver=0 not working

**Symptom**: Waiver=0 mode not converting FAIL→INFO.

**Cause**: Missing waiver handler methods in base class.

**Solution**: Ensure your checker inherits from proper base class with:
- `should_convert_fail_to_info()`
- `get_waivers()`
- `parse_waive_items()`
- `apply_type1_type2_waiver()`

### Issue 5: AttributeError on .keys()

**Symptom**: `AttributeError: 'list' object has no attribute 'keys'`

**Cause**: Internal bug when mixing List/Dict in waiver=0 mode (v2.0 early versions).

**Solution**: Upgrade to v2.0 final (December 16, 2025) which includes auto-conversion fix.

---

## Best Practices

### DO ✅

1. **Use Dict format for new checkers**
   ```python
   items = {name: {"line_number": n, "file_path": f}}
   ```

2. **Use build_complete_output() for simple cases**
   ```python
   return self.build_complete_output(found=..., missing=...)
   ```

3. **Provide meaningful descriptions**
   ```python
   missing_reason="Clock domain constraint missing"
   missing_desc="Required constraints not found"
   ```

4. **Set explicit severity when needed**
   ```python
   extra_severity=Severity.FAIL  # For critical violations
   ```

5. **Include source location metadata**
   ```python
   {"line_number": 123, "file_path": "report.rpt"}
   ```

### DON'T ❌

1. **Don't mix Dict and List inconsistently**
   ```python
   # Inconsistent
   found_items={"item": {}}  # Dict
   missing_items=["item"]     # List
   ```

2. **Don't forget extra_severity for FAIL violations**
   ```python
   # Wrong - shows PASS
   extra_items=critical_errors
   
   # Correct - shows FAIL
   extra_items=critical_errors,
   extra_severity=Severity.FAIL
   ```

3. **Don't use extra_items for semantic "missing" items**
   ```python
   # Confusing
   extra_items=missing_constraints
   
   # Clear
   missing_items=missing_constraints
   ```

4. **Don't manually format tags**
   ```python
   # Wrong - tag handling is automatic
   reason=f"{base}[WAIVER]"
   
   # Correct - use waived_tag parameter
   waived_tag="[WAIVER]"
   ```

### Performance Tips

1. **Pre-build Dict once** - Don't recreate for each method call
   ```python
   items_dict = {k: {"line_number": n} for k, n in parsed}
   return self.build_complete_output(found_items=items_dict)
   ```

2. **Use helper methods** - Don't duplicate metadata extraction logic
   ```python
   metadata = self.extract_metadata_from_lines(...)
   ```

3. **Batch file reads** - Parse files once, reuse results
   ```python
   data = self._parse_input_files()  # Once
   found = data['found']
   missing = data['missing']
   ```

### Code Organization

```python
class MyChecker(BaseChecker, OutputBuilderMixin):
    def execute_check(self):
        """Main entry point - keep simple."""
        data = self._parse_input_files()
        return self._build_output(data)
    
    def _parse_input_files(self) -> Dict:
        """Parse and categorize items."""
        # Parsing logic here
        return {"found": {...}, "missing": {...}}
    
    def _build_output(self, data: Dict) -> CheckResult:
        """Build CheckResult from parsed data."""
        return self.build_complete_output(
            found_items=data['found'],
            missing_items=data['missing']
        )
```

---

## Version History

### v2.0.0 (December 16, 2025)
- ✅ Unified Union[Dict, List] interface for all items
- ✅ Automatic List→Dict conversion
- ✅ Fixed is_pass calculation bug
- ✅ Simplified Tag display logic
- ✅ Enhanced documentation

### v1.1.0 (December 8, 2025)
- Added extra_severity parameter
- Dict support for found_items and extra_items
- Waiver=0 auto-detection

### v1.0.0 (Initial)
- Basic detail and group building
- List-based parameters only

---

## See Also

- **API_V2_MIGRATION_GUIDE.md** - Detailed migration instructions
- **ENHANCEMENT_PROPOSAL.md** - Future improvements roadmap
- **output_builder_template.py** - Source code with inline documentation
- **DEVELOPER_TASK_PROMPTS.md** - Checker development workflow

---

## Support

For questions or issues:
1. Check this guide and API_V2_MIGRATION_GUIDE.md
2. Review example checkers in Check_modules/*/scripts/checker/
3. Contact: yyin@cadence.com

**Happy Checking! 🎉**
