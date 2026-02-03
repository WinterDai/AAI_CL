# IMP-12-0-0-24: Confirm add the chipBoundary layer to check boundary DRC for test chip.

## Overview

**Check ID:** IMP-12-0-0-24  
**Description:** Confirm add the chipBoundary layer to check boundary DRC for test chip.  
**Category:** Physical Verification - DRC Layer Check  
**Input Files:** 
- `${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_DRC.rep`
- `${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_DRC.rep`

This checker verifies that the Chip_Boundary layer is included in DRC reports (Calibre or Pegasus format). The presence of this layer with a geometry count of 1 confirms that chip boundary DRC checks are properly configured for test chip validation.

---

## Check Logic

### Input Parsing

The checker supports both Calibre and Pegasus DRC report formats. It searches for the Chip_Boundary layer in the layer statistics section.

**Key Patterns:**

```python
# Pattern 1: Calibre format - Chip_Boundary layer with geometry count
pattern_calibre = r'^\s*LAYER\s+Chip_Boundary\s+\.+\s+TOTAL\s+Original\s+Geometry\s+Count\s+=\s+(\d+)'
# Example: "LAYER Chip_Boundary ............. TOTAL Original Geometry Count = 1"

# Pattern 2: Pegasus format - Chip_Boundary layer with geometry count
pattern_pegasus = r'^\s*LAYER\s+Chip_Boundary\s+\.+\s+Total\s+Original\s+Geometry:\s+(\d+)'
# Example: "LAYER Chip_Boundary ........................ Total Original Geometry:          1"
```

### Detection Logic

1. **File Format Detection**: Automatically detect Calibre or Pegasus format based on report header markers
2. **Layer Search**: Scan layer statistics section for "Chip_Boundary" layer entry
3. **Geometry Count Extraction**: Extract the geometry count value (should be 1 for valid chip boundary)
4. **Validation**: 
   - PASS: Chip_Boundary layer found with geometry count = 1
   - FAIL: Chip_Boundary layer not found OR geometry count ≠ 1
5. **Multi-file Support**: Aggregate results from multiple DRC reports (Calibre and/or Pegasus)

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `existence_check`

Choose ONE mode based on what pattern_items represents:

### Mode 1: `existence_check` - 存在性检查
**Use when:** pattern_items are items that SHOULD EXIST in input files

```
pattern_items: ["item_A", "item_B", "item_C"]
Input file contains: item_A, item_B

Result:
  found_items:   item_A, item_B    ← Pattern found in file
  missing_items: item_C            ← Pattern NOT found in file

PASS: All pattern_items found in file
FAIL: Some pattern_items not found in file
```

### Mode 2: `status_check` - 状态检查  
**Use when:** pattern_items are items to CHECK STATUS, only output matched items

```
pattern_items: ["port_A", "port_B"]
Input file contains: port_A(fixed), port_B(unfixed), port_C(unfixed)

Result:
  found_items:   port_A            ← Pattern matched AND status correct
  missing_items: port_B            ← Pattern matched BUT status wrong
  (port_C not output - not in pattern_items)

PASS: All matched items have correct status
FAIL: Some matched items have wrong status (or pattern not matched)
```

**Selected Mode for this checker:** `existence_check`

**Rationale:** This checker verifies that the Chip_Boundary layer exists in DRC reports with the correct geometry count (1). The pattern_items represent the expected layer identifier that SHOULD be present in the report. The checker searches for this layer and validates its presence and geometry count.

---

## Output Descriptions (CRITICAL - Code Generator Uses These!)

This section defines the output strings used by `build_complete_output()` in the checker code.
**Fill in these values based on the check logic above.**

```python
# ⚠️ CRITICAL: Description & Reason parameter usage by Type (API-026)
# Both DESC and REASON constants are split by Type for semantic clarity:
#   Type 1/4 (Boolean): Use DESC_TYPE1_4 & REASON_TYPE1_4 (emphasize "found/not found")
#   Type 2/3 (Pattern): Use DESC_TYPE2_3 & REASON_TYPE2_3 (emphasize "matched/satisfied")

# Item description for this checker
item_desc = "Confirm add the chipBoundary layer to check boundary DRC for test chip."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "Chip_Boundary layer found in DRC report with correct geometry count"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "Chip_Boundary layer matched in DRC report (1/1)"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Chip_Boundary layer found with geometry count = 1"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Required Chip_Boundary layer matched and validated with geometry count = 1"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Chip_Boundary layer not found in DRC report or incorrect geometry count"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Expected Chip_Boundary layer not satisfied (0/1 missing)"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Chip_Boundary layer not found in DRC report or geometry count ≠ 1"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Expected Chip_Boundary layer not satisfied or missing from DRC report"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Chip_Boundary layer requirement waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Chip_Boundary layer check waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries for Chip_Boundary layer check"
unused_waiver_reason = "Waiver not matched - Chip_Boundary layer found or no corresponding violation"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "LAYER Chip_Boundary: geometry_count={count} (Report: {report_type})"
  Example: "LAYER Chip_Boundary: geometry_count=1 (Report: Calibre)"

ERROR01 (Violation/Fail items):
  Format: "LAYER Chip_Boundary: {issue_description} (Report: {report_type})"
  Example: "LAYER Chip_Boundary: Not found in DRC report (Report: Pegasus)"
  Example: "LAYER Chip_Boundary: Invalid geometry count=0, expected 1 (Report: Calibre)"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-24:
  description: "Confirm add the chipBoundary layer to check boundary DRC for test chip."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_DRC.rep"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_DRC.rep"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs boolean validation: searches for Chip_Boundary layer in DRC reports and validates geometry count = 1.
PASS if layer found with correct count, FAIL otherwise.

**Sample Output (PASS):**
```
Status: PASS
Reason: Chip_Boundary layer found with geometry count = 1
INFO01:
  - LAYER Chip_Boundary: geometry_count=1 (Report: Calibre)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Chip_Boundary layer not found in DRC report or geometry count ≠ 1
ERROR01:
  - LAYER Chip_Boundary: Not found in DRC report (Report: Pegasus)
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-24:
  description: "Confirm add the chipBoundary layer to check boundary DRC for test chip."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_DRC.rep"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_DRC.rep"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Chip_Boundary layer check is informational for early design stages"
      - "Note: Boundary DRC violations are expected before final tape-out and do not block progress"
```

**CRITICAL Behavior (waivers.value=0):**
- NOTE: Type 1 has NO waiver logic. waive=0 is forced PASS mode only
- IMPORTANT: waive_items uses PLAIN STRINGS (NOT name/reason dict like Type 3/4!)
- waive_items serves as COMMENT ONLY (no matching/filtering logic)
- waive_items content printed as INFO with [WAIVED_INFO] tag
- ALL violations force converted: FAIL→PASS, displayed as INFO with [WAIVED_AS_INFO] tag
- Check ALWAYS returns PASS (violations shown as INFO for tracking)
- Used when: Check is informational only, violations expected/acceptable

**Sample Output (PASS with violations):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All violations waived as informational
INFO01 ([WAIVED_INFO] - waive_items as comment):
  - "Explanation: Chip_Boundary layer check is informational for early design stages"
  - "Note: Boundary DRC violations are expected before final tape-out and do not block progress"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - LAYER Chip_Boundary: Not found in DRC report (Report: Calibre) [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-24:
  description: "Confirm add the chipBoundary layer to check boundary DRC for test chip."
  requirements:
    value: 1
    pattern_items:
      - "Chip_Boundary"  # Layer name to search for in DRC reports
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_DRC.rep"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_DRC.rep"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Description requires checking for "chipBoundary layer" existence
- pattern_items contains the LAYER NAME identifier to search for
- Use simplified layer name: "Chip_Boundary" (matches DRC report format)
- DO NOT use full report line format or geometry count details

**Check Behavior:**
Type 2 searches for Chip_Boundary layer in DRC reports (existence check).
PASS if layer found with geometry count = 1 (missing_items empty).
FAIL if layer not found or geometry count ≠ 1 (missing_items contains "Chip_Boundary").

**Sample Output (PASS):**
```
Status: PASS
Reason: Required Chip_Boundary layer matched and validated with geometry count = 1
INFO01:
  - LAYER Chip_Boundary: geometry_count=1 (Report: Calibre)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Expected Chip_Boundary layer not satisfied or missing from DRC report
ERROR01:
  - LAYER Chip_Boundary: Not found in DRC report (Report: Pegasus)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-24:
  description: "Confirm add the chipBoundary layer to check boundary DRC for test chip."
  requirements:
    value: 1
    pattern_items:
      - "Chip_Boundary"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_DRC.rep"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_DRC.rep"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Chip_Boundary layer check is informational during pre-layout phase"
      - "Note: Layer mismatches are expected when using partial DRC rule decks and do not require fixes"
```

**CRITICAL Behavior (waivers.value=0):**
- NOTE: Type 2 has NO waiver logic. waive=0 is forced PASS mode only
- IMPORTANT: waive_items uses PLAIN STRINGS (NOT name/reason dict like Type 3/4!)
- waive_items serves as COMMENT ONLY (no matching/filtering logic)
- waive_items content printed as INFO with [WAIVED_INFO] tag
- ALL errors/mismatches force converted: ERROR→PASS, displayed as INFO with [WAIVED_AS_INFO] tag
- Check ALWAYS returns PASS (errors shown as INFO for tracking)
- Used when: Pattern check is informational, mismatches expected

**Sample Output (PASS with mismatches):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All mismatches waived as informational
INFO01 ([WAIVED_INFO] - waive_items as comment):
  - "Explanation: Chip_Boundary layer check is informational during pre-layout phase"
  - "Note: Layer mismatches are expected when using partial DRC rule decks and do not require fixes"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - LAYER Chip_Boundary: Not found in DRC report (Report: Calibre) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-24:
  description: "Confirm add the chipBoundary layer to check boundary DRC for test chip."
  requirements:
    value: 1
    pattern_items:
      - "Chip_Boundary"  # Layer name to search for in DRC reports
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_DRC.rep"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_DRC.rep"
  waivers:
    value: 2
    waive_items:
      - name: "Chip_Boundary"  # Waive missing layer for specific report
        reason: "Waived - Chip_Boundary layer not required for block-level DRC verification"
      - name: "Chip_Boundary"  # Waive incorrect geometry count
        reason: "Waived - Multiple chip boundaries acceptable for multi-die design"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:
- BOTH must be at SAME semantic level as description!
- Description requires checking "chipBoundary layer" → Use layer name identifier
- pattern_items: ["Chip_Boundary"] (layer name)
- waive_items.name: "Chip_Boundary" (same layer name format)
- DO NOT mix different semantic levels (e.g., layer name vs. full report line)

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same layer search logic as Type 2, plus waiver classification:
- Match missing/invalid layers against waive_items
- Unwaived issues → ERROR (need fix)
- Waived issues → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all layer issues are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - LAYER Chip_Boundary: Not found in DRC report (Report: Calibre) [WAIVER]
WARN01 (Unused Waivers):
  - Chip_Boundary: Waiver not matched - Chip_Boundary layer found or no corresponding violation
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-24:
  description: "Confirm add the chipBoundary layer to check boundary DRC for test chip."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_DRC.rep"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_DRC.rep"
  waivers:
    value: 2
    waive_items:
      - name: "Chip_Boundary"  # IDENTICAL to Type 3
        reason: "Waived - Chip_Boundary layer not required for block-level DRC verification"
      - name: "Chip_Boundary"  # IDENTICAL to Type 3
        reason: "Waived - Multiple chip boundaries acceptable for multi-die design"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (no pattern_items), plus waiver classification:
- Match violations against waive_items
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output:**
```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - LAYER Chip_Boundary: Not found in DRC report (Report: Pegasus) [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 12.0_PHYSICAL_VERIFICATION_CHECK --checkers IMP-12-0-0-24 --force

# Run individual tests
python IMP-12-0-0-24.py
```

---

## Notes

**Supported Report Formats:**
- Calibre DRC reports: Pattern `LAYER Chip_Boundary ............. TOTAL Original Geometry Count = 1`
- Pegasus DRC reports: Pattern `LAYER Chip_Boundary ........................ Total Original Geometry:          1`

**Validation Rules:**
- Chip_Boundary layer MUST exist in at least one DRC report
- Geometry count MUST equal 1 (single chip boundary polygon)
- Multiple reports are aggregated (if both Calibre and Pegasus reports provided, both are checked)

**Common Issues:**
- Layer name case-sensitive: Must be exactly "Chip_Boundary" (not "chip_boundary" or "CHIP_BOUNDARY")
- Geometry count validation: Count = 0 indicates missing boundary, Count > 1 indicates multiple boundaries (both are failures)
- Report format detection: Checker auto-detects Calibre vs Pegasus format based on header markers

**Limitations:**
- Does not validate boundary geometry correctness (only checks existence and count)
- Does not verify boundary coordinates or dimensions
- Assumes standard Calibre/Pegasus report format (custom report formats may not be parsed correctly)