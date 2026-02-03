# Agent Optimization Guide

**Version**: 1.0.0  
**Date**: 2025-12-22  
**Purpose**: Document systematic issues in AI-generated checker code and prevention strategies

---

## 📋 Overview

This guide documents 7 critical issues discovered during IMP-2-0-0-02 development and provides concrete solutions to prevent recurrence in future AI-generated checkers.

---

## 🚨 Problem Summary

### Severity Classification
- **🔴 CRITICAL**: Logic errors causing incorrect PASS/FAIL determination
- **🟠 HIGH**: Data format errors causing runtime crashes
- **🟡 MEDIUM**: Missing features or API parameters
- **🟢 LOW**: Minor inconsistencies

---

## 1. 🔴 CRITICAL: Type 3/4 Waiver Logic Misunderstanding

### Problem
Agent fundamentally misunderstood waiver targets:
- **Agent thought**: Waive violations (found but not expected)
- **Correct**: Waive FAIL patterns (expected but not found = missing_items)

### Impact
- Type 3 showed PASS when should FAIL
- Wrong items marked as waived
- Logic opposite of intended behavior

### Example Error
```python
# ❌ WRONG - Agent waived violations (found items)
for violation in violations:  # Items that EXIST but shouldn't
    if waiver_matches:
        waived_items.append(violation)  # WRONG TARGET!
```

### Correct Implementation
```python
# ✅ CORRECT - Waive missing_items (FAIL patterns)
for pattern in pattern_items:  # Expected patterns
    if pattern_not_found:
        if waiver_matches:
            waived_items.append(pattern)  # Waive the FAIL pattern
        else:
            missing_items.append(pattern)  # Still FAIL
```

### Root Cause
Template examples didn't explicitly state: **"Waivers target FAIL patterns, not violations"**

### Prevention Strategy
✅ Add explicit statement in Type 3/4 hints:
```markdown
⚠️ CRITICAL CONCEPT:
- Waivers target FAIL patterns (expected but not found = missing_items)
- Waivers DO NOT target violations (found but not expected = extra_items)
- Type 3: Waive missing patterns that cause FAIL
- Type 4: Waive violations that cause FAIL (no items found)
```

---

## 2. 🟠 HIGH: Data Format Confusion

### Problem 2a: waive_dict.values() Type
```python
# ❌ WRONG - Agent treated as dicts
for waiver in waive_dict.values():  # Actually strings!
    reason = waiver.get('reason')  # AttributeError!
```

**API Truth**: `waive_dict: Dict[str, str]` where `{name: reason}`

### Problem 2b: unused_waivers Format
```python
# ❌ WRONG - Agent used Dict[str, Dict]
unused_waivers = {
    'waiver1': {'reason': 'text', 'line_number': 0}
}
```

**Correct**: `List[str]` for simple cases, `Dict[str, Dict]` only when metadata needed

### Problem 2c: Type 3/4 Items Format
```python
# ❌ WRONG - Agent mixed formats
waived_items = {'item1': {'details': 'text'}}  # Dict format
missing_items = ['item2', 'item3']  # List format
```

**Correct**: Consistent format across all item collections

### Prevention Strategy
✅ Add data format reference table:
```python
# MANDATORY DATA FORMATS
waive_dict: Dict[str, str] = {'name': 'reason'}  # After parse_waive_items()
waived_items: List[str] = ['item1', 'item2']     # Simple list
missing_items: List[str] = ['item3', 'item4']    # Consistent format
unused_waivers: List[str] = ['waiver1']          # Simple list
```

---

## 3. 🟡 MEDIUM: Missing API Parameters

### Problem
Type 2 implementation missing critical parameters:
```python
# ❌ WRONG - Missing parameters
return self.build_complete_output(
    found_items=found,
    missing_items=missing
    # Missing: value, has_pattern_items, has_waiver_value
)
```

### Impact
- Incorrect PASS/FAIL determination
- Wrong logic path in OutputBuilderMixin

### Prevention Strategy
✅ Add parameter checklist per type:
```python
# Type 2 REQUIRED Parameters:
value=expected_value,              # From requirements.value
has_pattern_items=True,            # Always True for Type 2
has_waiver_value=False,            # Always False for Type 2
found_desc="...",
missing_desc="...",
found_reason="...",
missing_reason="..."
```

---

## 4. 🟡 MEDIUM: Name Matching Pattern Error

### Problem
Name extraction stopped at first dot delimiter:
```python
# ❌ WRONG - Stopped at .11a
name = "PLN6FF_...001.11a"  # Missing .encrypt suffix

# Expected
name = "PLN6FF_...001.11a.encrypt"
```

### Impact
- No matches found
- All patterns reported as missing

### Prevention Strategy
✅ Add filename extraction examples:
```python
# CORRECT: Extract full filename with all suffixes
filename = Path(line).name  # Gets full name including .encrypt
# Example: 'PLN6FF_001.11a.encrypt' → Keep entire string

# Common patterns to preserve:
# - .encrypt suffix
# - .gz suffix
# - Version numbers (v1.2.3)
# - Multiple dots (file.tar.gz)
```

---

## 5. 🟢 LOW: Missing send_message() Method

### Problem
LLMCheckerAgent missing method used in Step 8 [M] Modify Code:
```python
# AttributeError: 'LLMCheckerAgent' object has no attribute 'send_message'
```

### Impact
- Step 8 [M] feature broken
- Agent can't modify code based on user feedback

### Prevention Strategy
✅ Method added to LLMCheckerAgent (lines 103-118)
✅ Tested in Step 8 Final Review workflow

---

## 6. 🟢 LOW: Step 8 [T] Test Again Behavior

### Problem
[T] only re-ran current test, didn't return to Step 7 interactive testing menu.

### Impact
- Poor UX - users forced to restart workflow
- Can't switch between Type 1/2/3/4 after Step 8

### Prevention Strategy
✅ Modified [T] to call `self._interactive_testing()` and return to Step 8
✅ Better workflow continuity

---

## 7. 🟠 HIGH: Incomplete README Parameter Examples

### Problem
README examples missing critical parameters:
```python
# Example showed:
self.build_complete_output(
    found_items=found,
    missing_items=missing
)
# Missing: reason/desc parameters → generic "Item found" output
```

### Impact
- Agent generated code without reason parameters
- Reports showed generic text instead of meaningful descriptions
- Affects ALL generated checkers

### Prevention Strategy
✅ **MANDATORY**: All README examples MUST include:
```python
# COMPLETE Example (REQUIRED in all READMEs)
return self.build_complete_output(
    found_items=found,
    missing_items=missing,
    
    # ⚠️ REQUIRED: Without these, output is generic!
    found_desc="Successful checks",
    missing_desc="Failed checks",
    found_reason="Item passed verification",
    missing_reason="Item failed verification",
    
    # Type 3/4 additions
    waived_items=waived,
    waived_desc="Waived failures",
    waived_base_reason="Failure waived per design approval",
    unused_waivers=unused,
    unused_waiver_reason="Waiver defined but no violation matched"
)
```

---

## 🎯 Implementation Priorities

### Phase 1: Critical Fixes (IMMEDIATE)
1. ✅ Update api_v2_reference.py Type 3/4 hints with waiver concept clarity
2. ✅ Add data format reference table
3. ✅ Add API parameter checklists per type

### Phase 2: Template Enhancement (HIGH)
4. ✅ Update all README examples with complete parameters
5. ✅ Add validation hints for common mistakes
6. ✅ Include filename extraction examples

### Phase 3: Validation (MEDIUM)
7. ⬜ Add runtime validation for common format errors
8. ⬜ Create pre-submission checklist for agent
9. ⬜ Implement format checker in BaseChecker

---

## 📊 Success Metrics

### Before Optimization
- IMP-2-0-0-02: 7 major issues requiring manual fixes
- 3 data format errors
- 1 critical logic error
- Average 4-5 iterations to working code

### After Optimization (Target)
- < 2 issues per checker
- 0 critical logic errors
- 0 data format errors
- Average 1-2 iterations to working code

---

## 🔄 Continuous Improvement

### Feedback Loop
1. **Document new issues**: Add to this guide when discovered
2. **Update templates**: Reflect learnings in prompts
3. **Enhance validation**: Add checks for common mistakes
4. **Share knowledge**: Update team documentation

### Next Steps
- [ ] Apply optimizations to checker_prompt_v2.py
- [ ] Regenerate problematic checkers with improved templates
- [ ] Monitor next 10 checker generations for improvement
- [ ] Update DEVELOPER_TASK_PROMPTS.md with insights

---

## 📚 Related Documentation

- [DEVELOPER_TASK_PROMPTS_v3.md](../../doc/DEVELOPER_TASK_PROMPTS_v3.md) - Task workflow
- [OUTPUT_FORMATTER_GUIDE.md](../../doc/OUTPUT_FORMATTER_GUIDE.md) - Output API reference
- [checker_templates/README.md](../../../CHECKLIST/Check_modules/common/checker_templates/README.md) - Template examples

---

**Remember**: The goal is not to eliminate all AI errors, but to prevent systematic, recurring issues that waste development time. Focus on high-impact, high-frequency problems first.
