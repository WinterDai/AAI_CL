# 10.0_sta_dcd_IMP-10-0-0-00 - Type 1

**Boolean Check**

---

## Overview

- **Category**: General Check
- **Type**: Type 1
- **Input Files**: `${CHECKLIST_ROOT}/IP_project_folder/logs/sta_post_syn.log`
- **Function**: Boolean pattern matching - checks if specific patterns exist or not exist in input files

## Check Logic

### Input Parsing

**Input Files**: ${CHECKLIST_ROOT}/IP_project_folder/logs/sta_post_syn.log

**Pattern Items**:
- `Generated on:*2025*`

**Method**: Line-by-line pattern matching using string search.

### Detection Logic

1. Search for pattern items in input files
2. If **any pattern found** → **PASS**
3. If **no patterns found** → **FAIL**


## Configuration

### Type 1 Configuration

Complete configuration example:

```python
checker = 10.0_sta_dcd_IMP-10-0-0-00(
    name='10.0_sta_dcd_IMP-10-0-0-00',
    pattern_items=[
        "Generated on:*2025*"
],
    found_logic='ANY',
    input_files=["${CHECKLIST_ROOT}/IP_project_folder/logs/sta_post_syn.log"]
)
```


## Output Format

### PASS Scenario

**Description**: Pattern not found: Confirm the netlist/spef version is correct.

**Example Output**:
```
INFO01: Pattern not found: Confirm the netlist/spef version is correct.
```

### FAIL Scenario

**Description**: Pattern found: Confirm the netlist/spef version is correct.

**Example Output**:
```
ERROR01: Pattern found: Confirm the netlist/spef version is correct.
```



## Testing

### Test Cases

**Test Case 1: PASS Condition**
- Input: File with no violations/patterns
- Expected: PASS status
- Output: Pattern not found: Confirm the netlist/spef version is correct.

**Test Case 2: FAIL Condition**
- Input: File with violations/patterns
- Expected: FAIL status
- Output: Pattern found: Confirm the netlist/spef version is correct.



## Version History

- **v1.0** (2025-12-19): Initial implementation
  - Type 1 checker
  - Input parsing: ${CHECKLIST_ROOT}/IP_project_folder/logs/sta_post_syn.log
  - Configuration validated
  - Test cases defined

---

**Generated**: 2025-12-19  
**Checker**: 10.0_sta_dcd_IMP-10-0-0-00  
**Type**: 1