# OutputBuilderTemplate API v2.0 Migration Guide

## Overview

API v2.0 unifies the parameter interface across all output building methods to support metadata preservation for all item types, not just `found_items` and `extra_items`.

**Version**: 2.0.0  
**Date**: December 16, 2025  
**Status**: ✅ Complete and Tested

---

## Critical Bug Fix

### Issue: `is_pass` Calculation Ignored `extra_items`

**Problem**: When using `extra_items` with `extra_severity=Severity.FAIL`, the checker would incorrectly report `PASS` even with FAIL violations in ERROR01 group.

**Root Cause**: `is_pass` calculation only checked `missing_items`:
```python
# Old (buggy)
is_pass = not missing_items or len(missing_items) == 0
# extra_items were completely ignored!
```

**Fix**: Now includes `extra_items` in pass/fail logic:
```python
# New (correct)
is_pass = not missing_items or len(missing_items) == 0
# Also check extra_items if they have FAIL severity
if is_pass and extra_items and extra_severity == Severity.FAIL:
    is_pass = False
```

**Impact**: IMP-10-0-0-11 now correctly shows `FAIL` when violations exist (previously showed `PASS`).

---

## What Changed

### 1. Unified Parameter Types

All item parameters now accept **`Union[Dict[str, Dict[str, Any]], List[str]]`**:

| Parameter | Old Type | New Type | Notes |
|-----------|----------|----------|-------|
| `found_items` | `Dict` | `Union[Dict, List]` | Dict was already supported |
| `missing_items` | `List[str]` | `Union[Dict, List]` | ⭐ Now supports metadata |
| `waived_items` | `List[str]` | `Union[Dict, List]` | ⭐ Now supports metadata |
| `unused_waivers` | `List[str]` | `Union[Dict, List]` | ⭐ Now supports metadata |
| `extra_items` | `Dict` | `Union[Dict, List]` | Dict was already supported |

### 2. Auto-Conversion for Backward Compatibility

**Internal `_ensure_dict()` function** automatically converts `List[str]` to `Dict[str, Dict]`:

```python
def _ensure_dict(items):
    """Convert List[str] to Dict[str, Dict[str, Any]] for uniform processing."""
    if items is None:
        return {}
    if isinstance(items, dict):
        return items
    # Auto-convert List to Dict
    return {item: {} for item in items}
```

**Result**: All existing checkers using `List[str]` continue to work without changes.

### 3. Metadata Format

When using Dict format, include metadata for source file/line display:

```python
items = {
    "item_name": {
        "line_number": 123,           # Required for line display
        "file_path": "/path/to/file",  # Required for file display
        "line_content": "...",         # Optional, for context
        # Add any custom metadata as needed
    }
}
```

---

## Migration Examples

### Example 1: Type 1 Checker - Simple List to Dict

**Old Code (still works)**:
```python
missing_items = ["path_group_A", "path_group_B"]

return self.build_complete_output(
    found_items={},
    missing_items=missing_items  # List[str]
)
```

**New Code (recommended)**:
```python
missing_items = {
    "path_group_A": {
        "line_number": 45,
        "file_path": "reports/timing.rpt"
    },
    "path_group_B": {
        "line_number": 67,
        "file_path": "reports/timing.rpt"
    }
}

return self.build_complete_output(
    found_items={},
    missing_items=missing_items  # Dict[str, Dict]
)
```

### Example 2: Using `missing_items` Instead of `extra_items` Workaround

**Old Code (workaround)**:
```python
# Had to use extra_items to preserve metadata
violation_items = {
    "violation_1": {"line_number": 10, "file_path": "report.txt"}
}
clean_items = {
    "clean_group": {"line_number": 5, "file_path": "report.txt"}
}

return self.build_complete_output(
    found_items=clean_items,
    extra_items=violation_items,        # Workaround for metadata
    extra_severity=Severity.FAIL,       # Needed for FAIL status
    extra_reason="Violation found",
    extra_desc="Violations detected"
)
```

**New Code (natural way)**:
```python
# Now can use missing_items directly with metadata
violation_items = {
    "violation_1": {"line_number": 10, "file_path": "report.txt"}
}
clean_items = {
    "clean_group": {"line_number": 5, "file_path": "report.txt"}
}

return self.build_complete_output(
    found_items=clean_items,
    missing_items=violation_items,      # Natural semantic
    missing_severity=Severity.FAIL,     # Optional, FAIL is default
    missing_reason="Violation found",
    missing_desc="Violations detected"
)
```

### Example 3: waived_items with Metadata

**Old Code**:
```python
waived_items = ["item1", "item2"]  # No metadata preserved
```

**New Code**:
```python
waived_items = {
    "item1": {
        "line_number": 100,
        "file_path": "constraints.sdc",
        "line_content": "set_false_path -from [get_clocks clk_a]"
    },
    "item2": {
        "line_number": 150,
        "file_path": "constraints.sdc"
    }
}
```

### Example 4: unused_waivers with Metadata

**Old Code**:
```python
unused_waivers = ["waiver_pattern_1", "waiver_pattern_2"]
```

**New Code**:
```python
unused_waivers = {
    "waiver_pattern_1": {
        "line_number": 25,
        "file_path": "waivers.yaml"
    },
    "waiver_pattern_2": {
        "line_number": 30,
        "file_path": "waivers.yaml"
    }
}
```

---

## Affected Methods

All three core methods updated:

### 1. `build_details_from_items()`

**Signature Change**:
```python
def build_details_from_items(
    self,
    found_items: Optional[Union[Dict[str, Dict[str, Any]], List[str]]] = None,
    missing_items: Optional[Union[Dict[str, Dict[str, Any]], List[str]]] = None,
    waived_items: Optional[Union[Dict[str, Dict[str, Any]], List[str]]] = None,
    unused_waivers: Optional[Union[Dict[str, Dict[str, Any]], List[str]]] = None,
    # ... other parameters
) -> List[DetailItem]:
```

### 2. `build_result_groups()`

**Signature Change**:
```python
def build_result_groups(
    self,
    found_items: Optional[Union[Dict[str, Dict[str, Any]], List[str]]] = None,
    missing_items: Optional[Union[Dict[str, Dict[str, Any]], List[str]]] = None,
    waived_items: Optional[Union[Dict[str, Dict[str, Any]], List[str]]] = None,
    unused_waivers: Optional[Union[Dict[str, Dict[str, Any]], List[str]]] = None,
    # ... other parameters
) -> Dict[str, Dict[str, Any]]:
```

### 3. `build_complete_output()`

**Signature Change**:
```python
def build_complete_output(
    self,
    found_items: Optional[Union[Dict[str, Dict[str, Any]], List[str]]] = None,
    missing_items: Optional[Union[Dict[str, Dict[str, Any]], List[str]]] = None,
    waived_items: Optional[Union[Dict[str, Dict[str, Any]], List[str]]] = None,
    unused_waivers: Optional[Union[Dict[str, Dict[str, Any]], List[str]]] = None,
    extra_items: Optional[Union[Dict[str, Dict[str, Any]], List[str]]] = None,
    # ... other parameters
) -> CheckResult:
```

---

## New Parameters

### `missing_severity`

Control severity of `missing_items` explicitly:

```python
return self.build_complete_output(
    missing_items=violations,
    missing_severity=Severity.FAIL,  # Default is FAIL
    # Or: Severity.WARN, Severity.INFO
)
```

**Use Cases**:
- Type 2 checkers where missing items might be WARN instead of FAIL
- Custom severity logic based on context

### `extra_severity` (existing, now properly documented)

Control severity of `extra_items`:

```python
return self.build_complete_output(
    extra_items=unexpected_items,
    extra_severity=Severity.FAIL,  # Default is WARN for Type 2
)
```

---

## Internal Implementation Details

### Auto-Conversion Logic

All item parameters go through `_ensure_dict()` at method entry:

```python
# In build_complete_output(), build_details_from_items(), build_result_groups()
found_items = self._ensure_dict(found_items)
missing_items = self._ensure_dict(missing_items)
waived_items = self._ensure_dict(waived_items)
unused_waivers = self._ensure_dict(unused_waivers)
extra_items = self._ensure_dict(extra_items)
```

### Metadata Extraction

When iterating over Dict items:

```python
# Iterate over keys (item names)
for item in missing_items.keys():
    metadata = missing_items[item]
    line_num = metadata.get('line_number', 'N/A')
    file_path = metadata.get('file_path', default_file)
    
    # Build DetailItem with metadata
    details.append(DetailItem(
        name=item,
        source_file=file_path,
        line_number=line_num,
        severity=Severity.FAIL,
        reason="Item not found"
    ))
```

### Group Building

Groups only show item names (keys), not metadata:

```python
if missing_items:
    error_groups["ERROR01"] = {
        "description": "Items not found",
        "items": sorted(set(missing_items.keys()))  # Only names
    }
```

---

## Backward Compatibility

### 100% Compatible

✅ All existing checkers using `List[str]` continue to work  
✅ No changes required for existing code  
✅ `len(items)` works for both Dict and List  
✅ Boolean checks `if items:` work for both types

### Test Results

Verified with IMP-10-0-0-11:
- ✅ Dict format with metadata: Works correctly
- ✅ `extra_items` with `extra_severity=FAIL`: Now correctly shows FAIL status
- ✅ Metadata displayed in details (source_file, line_number)
- ✅ Groups show clean item names without metadata clutter

---

## Benefits of API v2.0

### 1. Consistent Interface
- All parameters follow same pattern: `Union[Dict, List]`
- No more confusion about which parameters support metadata

### 2. Natural Semantics
- Use `missing_items` for violations (not `extra_items` workaround)
- Use `waived_items` with full file/line context
- Use `unused_waivers` with source location

### 3. Enhanced Debugging
- Every item can show where it came from
- Easier to trace issues back to source files
- Better user experience with complete information

### 4. Future-Proof
- Easy to add more metadata fields
- Extensible for custom checker needs
- Foundation for advanced features

---

## Best Practices

### DO ✅

1. **Use Dict format for new checkers**
   ```python
   items = {name: {"line_number": n, "file_path": f} for ...}
   ```

2. **Include source location metadata**
   ```python
   {"line_number": 123, "file_path": "report.rpt"}
   ```

3. **Use natural parameter names**
   ```python
   # Violations → missing_items (not extra_items)
   missing_items=violations
   ```

4. **Leverage auto-conversion**
   ```python
   # Both work, prefer Dict for new code
   missing_items=["item1", "item2"]  # List (backward compat)
   missing_items={"item1": {}, "item2": {}}  # Dict (recommended)
   ```

### DON'T ❌

1. **Don't mix formats inconsistently**
   ```python
   # Bad: Inconsistent
   found_items={"item": {}}  # Dict
   missing_items=["item"]     # List
   
   # Good: Consistent
   found_items={"item": {}}
   missing_items={"item": {}}
   ```

2. **Don't use extra_items for violations**
   ```python
   # Old workaround (still works but not recommended)
   extra_items=violations
   extra_severity=Severity.FAIL
   
   # New natural way
   missing_items=violations
   ```

3. **Don't forget metadata**
   ```python
   # Minimal metadata, loses context
   {"item": {}}
   
   # Rich metadata, better UX
   {"item": {"line_number": 10, "file_path": "file.txt"}}
   ```

---

## Troubleshooting

### Q: My checker shows PASS when it should FAIL

**A**: If using `extra_items` with `extra_severity=Severity.FAIL`, ensure you're on API v2.0. The bug fix ensures `extra_items` are included in `is_pass` calculation.

### Q: Can I mix Dict and List parameters?

**A**: Yes! Auto-conversion handles this automatically:
```python
build_complete_output(
    found_items={"item": {}},      # Dict
    missing_items=["item1", "item2"]  # List - auto-converted
)
```

### Q: How do I migrate existing List-based checkers?

**A**: No migration required! They continue to work. To add metadata:
1. Convert List to Dict: `{item: {} for item in list}`
2. Add metadata: `{item: {"line_number": n, "file_path": f} ...}`
3. Test and deploy

### Q: What if I don't have line_number or file_path?

**A**: Use empty Dict:
```python
{"item": {}}  # No metadata, but enables future additions
```
Or use `default_file` parameter:
```python
build_complete_output(
    missing_items={"item": {}},
    default_file="N/A"  # Fallback when file_path missing
)
```

---

## Version History

### v2.0.0 (December 16, 2025)
- ✅ Unified all item parameters to `Union[Dict, List]`
- ✅ Added auto-conversion via `_ensure_dict()`
- ✅ Fixed `is_pass` bug (ignored `extra_items`)
- ✅ Added `missing_severity` parameter
- ✅ Updated docstrings for all three core methods
- ✅ Verified backward compatibility
- ✅ Tested with IMP-10-0-0-11 checker

### v1.1.0 (Previous)
- Added `extra_severity` parameter
- Supported Dict for `found_items` and `extra_items`
- List-only for `missing_items`, `waived_items`, `unused_waivers`

---

## References

- **Template File**: `output_builder_template.py`
- **Example Checker**: `IMP-10-0-0-11.py` (Type 1 with Dict metadata)
- **Enhancement Proposal**: `ENHANCEMENT_PROPOSAL.md`
- **Developer Guide**: `DEVELOPER_TASK_PROMPTS.md`

---

## Summary

API v2.0 provides a unified, flexible, and backward-compatible interface for building checker outputs with full metadata support. All existing checkers continue to work unchanged, while new checkers can leverage rich metadata for better user experience and debugging.

**Key Takeaway**: Use Dict format with metadata for new code, but don't worry about migrating old code - it just works! 🎉
