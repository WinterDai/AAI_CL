# OutputBuilderTemplate Quick Reference Card

**Version**: 2.0.0 | **Date**: 2025-12-16

---

## 🚀 ONE-LINE SOLUTION

```python
return self.build_complete_output(found_items=found, missing_items=missing)
```

That's it! Template handles everything automatically.

---

## 📊 Core Methods

```python
# ⭐ RECOMMENDED - One-step solution
build_complete_output(found_items, missing_items, ...)
  → Returns: CheckResult

# 🔧 Advanced - Step-by-step
build_details_from_items(found_items, missing_items, ...)
  → Returns: List[DetailItem]

build_result_groups(found_items, missing_items, ...)
  → Returns: Dict[info_groups, error_groups, warn_groups]

build_check_result(value, is_pass, details, **groups)
  → Returns: CheckResult
```

---

## 📦 Item Parameters (All accept Union[Dict, List])

```python
found_items      # Items that passed checks
missing_items    # Items that failed checks (unwaived)
waived_items     # Items waived by waivers
unused_waivers   # Unused waiver patterns
extra_items      # Unexpected items (Type 2)
```

---

## 🏷️ Metadata Format

### Dict (v2.0 - Recommended)
```python
items = {
    "item_name": {
        "line_number": 123,
        "file_path": "/path/file",
        "line_content": "..."  # optional
    }
}
```

### List (v1.x - Backward Compatible)
```python
items = ["item1", "item2"]  # Auto-converted to Dict
```

---

## 🎨 Severity Control

```python
Severity.INFO  # Found, waived items
Severity.WARN  # Unused waivers, Type 2 extra (default)
Severity.FAIL  # Missing items, Type 1 violations

# Override severity
missing_severity=Severity.FAIL  # Explicit FAIL for missing
extra_severity=Severity.FAIL    # FAIL instead of WARN for extra
```

---

## 🏷️ Tags

```
[WAIVER]          → Type 3/4 waivers (normal mode)
[WAIVED_INFO]     → Type 1/2 waive_items (waiver=0)
[WAIVED_AS_INFO]  → Converted violations (waiver=0)
```

**Log**: Clean names (tags in reason, hidden)  
**Report**: Full details with tags visible

---

## 🎯 Common Patterns

### Type 1: Simple Check
```python
return self.build_complete_output(
    found_items=clean_items,
    missing_items=violations
)
```

### Type 1: Violations as Extra
```python
return self.build_complete_output(
    found_items=clean_items,
    extra_items=violations,
    extra_severity=Severity.FAIL  # ⚠️ REQUIRED for FAIL status
)
```

### Type 2: Pattern Matching
```python
return self.build_complete_output(
    found_items=matched,
    missing_items=missing,
    extra_items=extra,
    extra_severity=Severity.WARN  # Type 2 default
)
```

### Type 3: With Waivers
```python
return self.build_complete_output(
    found_items=all_items,
    missing_items=unwaived,
    waived_items=waived,
    unused_waivers=unused,
    waive_dict=waiver_reasons,
    waived_tag="[WAIVER]"
)
```

### Waiver=0 (Auto)
```python
# No code changes needed!
# Template auto-detects waiver=0 and converts FAIL→INFO
return self.build_complete_output(
    found_items=found,
    missing_items=violations  # Auto-converted to INFO
)
```

---

## 🛠️ Customization

### Custom Descriptions
```python
found_desc="✅ Clean items"
missing_desc="❌ Items need attention"
waived_desc="⚠️ Waived for phase 1"
```

### Custom Name Extraction
```python
def extract_name(item, meta):
    return meta.get('custom_field', item)

build_complete_output(
    found_items=items,
    name_extractor=extract_name
)
```

### Multiple Severities
```python
build_complete_output(
    missing_items=critical,
    extra_items=warnings,
    missing_severity=Severity.FAIL,
    extra_severity=Severity.WARN
)
```

---

## ⚠️ Common Pitfalls

### ❌ Shows PASS with ERROR01
```python
# WRONG
extra_items=violations  # Defaults to WARN, is_pass=True

# CORRECT
extra_items=violations,
extra_severity=Severity.FAIL  # Forces is_pass=False
```

### ❌ No metadata displayed
```python
# WRONG
items = ["item1", "item2"]

# CORRECT
items = {"item1": {"line_number": 10, "file_path": "file.txt"}}
```

### ❌ Inconsistent types
```python
# WRONG (inconsistent)
found_items={"item": {}}  # Dict
missing_items=["item"]     # List

# CORRECT (consistent)
found_items={"item": {}}
missing_items={"item": {}}
```

---

## 📖 Full Documentation

- **[TEMPLATE_USAGE_GUIDE.md](TEMPLATE_USAGE_GUIDE.md)** - Complete usage guide
- **[API_V2_MIGRATION_GUIDE.md](API_V2_MIGRATION_GUIDE.md)** - Migration guide
- **[output_builder_template.py](output_builder_template.py)** - Source code

---

## 🆘 Quick Help

| Problem | Solution |
|---------|----------|
| Shows PASS but has errors | Add `extra_severity=Severity.FAIL` |
| No file/line info | Use Dict format with metadata |
| Tag duplicated | Upgrade to v2.0 |
| Waiver=0 not working | Check base class waiver methods |

---

## ✅ Best Practices

1. ✅ Use `build_complete_output()` for simple cases
2. ✅ Use Dict format with metadata for new code
3. ✅ Set `extra_severity=FAIL` for critical violations
4. ✅ Provide meaningful descriptions
5. ✅ Keep consistent types (all Dict or all List)

---

## 📊 v1.x vs v2.0

| Feature | v1.x | v2.0 |
|---------|------|------|
| Dict params (all) | ❌ | ✅ |
| Auto conversion | ❌ | ✅ |
| Correct is_pass | ❌ | ✅ |
| Clean tag logic | ❌ | ✅ |
| Backward compat | N/A | ✅ |

**Upgrade?** No changes needed! 100% backward compatible.

---

**Print this card** for quick reference while coding! 🖨️

**Last Updated**: December 16, 2025  
**Maintainer**: yyin@cadence.com
