# IMP-11-0-0-01: Confirm the design has no power open/short and all instances are physically connected.

## Overview

**Check ID:** IMP-11-0-0-01  
**Description:** Confirm the design has no power open/short and all instances are physically connected.  
**Category:** Power Connectivity Verification  
**Input Files:** ${CHECKLIST_ROOT}/IP_project_folder/reports/lvs.rep.cls

The checker parses the LVS report file (.cls format) to extract overall run results. It identifies power connectivity issues through LVS mismatch.

---

## Check Logic

### Input Parsing

The checker parses the Pegasus LVS comparison report file (lvs.rep.cls) which contains:
- Overall run result (MATCH/MISMATCH)

**Key Patterns:**

```python
# Pattern 1: Extract overall LVS run result (primary pass/fail indicator)
pattern_run_result = r'^#####\s+Run Result\s*:\s*(\w+)\s*$'
# Example: "#####  Run Result                    :   MATCH"
# Captures: "MATCH" or "MISMATCH"
```

### Detection Logic

**Step 1: Parse LVS Report Header**
- Extract overall run result (MATCH/MISMATCH) from "Run Result" line

**Step 2: Generate Output**
- If Run Result = MATCH → PASS
- If Run Result = MISMATCH → FAIL

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `status_check`

**Selected Mode for this checker:** `status_check`

**Rationale:** This checker validates the LVS comparison status and power connectivity status of the design. It searches for specific power connectivity issues (open/short/unconnected) in the LVS report and reports only the violations found. The checker does not have a predefined list of items that must exist; instead, it examines the actual LVS results and reports any power connectivity problems detected. This is a status validation check where we verify that the design has no power connectivity issues, making `status_check` the appropriate mode.

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
item_desc = "Confirm the design has no power open/short and all instances are physically connected."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "LVS comparison passed - no power connectivity issues found"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "LVS comparison matched - all power connectivity requirements satisfied"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "LVS Run Result: MATCH | No power open/short detected | All instances physically connected"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "LVS comparison matched successfully | Power connectivity validated | All instances properly connected"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Power connectivity issues found in LVS report"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "LVS comparison failed - power connectivity requirements not satisfied"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "LVS Run Result: MISMATCH | Power open/short detected or instances unconnected"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "LVS comparison failed | Power connectivity requirements not satisfied"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Waived power connectivity violations"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Power connectivity violation waived per design review"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries for power connectivity check"
unused_waiver_reason = "Waiver not matched - no corresponding power connectivity violation found in LVS report"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [item_name]: LVS comparison matched successfully | Power connectivity validated | All instances properly connected"
  Example: "- Overall Run Result: LVS Run Result: MATCH | No power connectivity issues"

ERROR01 (Violation/Fail items):
  Format: "- [item_name]: LVS comparison failed | Power connectivity requirements not satisfied"
  Example: "- Overall Run Result: LVS Run Result: MISMATCH | Power open detected"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-01:
  description: "Confirm the design has no power open/short and all instances are physically connected."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/lvs.rep.cls
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs custom boolean validation of LVS report for power connectivity.
- Parses lvs.rep.cls file to extract overall run result
- PASS if: Run Result = MATCH
- FAIL if: Run Result = MISMATCH

**Sample Output (PASS):**
```
Status: PASS
Reason: LVS Run Result: MATCH | No power open/short detected | All instances physically connected

Log format (CheckList.rpt):
INFO01:
  - Overall Run Result: LVS Run Result: MATCH

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: Overall Run Result. In line 15, ${CHECKLIST_ROOT}/IP_project_folder/reports/lvs.rep.cls: LVS Run Result: MATCH | No power open/short detected | All instances physically connected
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: LVS Run Result: MISMATCH | Power open/short detected or instances unconnected

Log format (CheckList.rpt):
ERROR01:
  - Overall Run Result: LVS Run Result: MISMATCH

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: Overall Run Result. In line 15, ${CHECKLIST_ROOT}/IP_project_folder/reports/lvs.rep.cls: LVS Run Result: MISMATCH | Power open/short detected or instances unconnected
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-01:
  description: "Confirm the design has no power open/short and all instances are physically connected."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/lvs.rep.cls
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Power connectivity check is informational during early design phase"
      - "Note: LVS mismatches are expected before final power grid completion and do not block tapeout"
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

Log format (CheckList.rpt):
INFO01:
  - "Explanation: Power connectivity check is informational during early design phase"
  - "Note: LVS mismatches are expected before final power grid completion and do not block tapeout"
INFO02:
  - Overall Run Result: LVS Run Result: MISMATCH

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: Explanation: Power connectivity check is informational during early design phase. [WAIVED_INFO]
2: Info: Note: LVS mismatches are expected before final power grid completion and do not block tapeout. [WAIVED_INFO]
3: Info: Overall Run Result. In line 15, ${CHECKLIST_ROOT}/IP_project_folder/reports/lvs.rep.cls: LVS Run Result: MISMATCH | Power open/short detected or instances unconnected [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-01:
  description: "Confirm the design has no power open/short and all instances are physically connected."
  requirements:
    value: 1  # ⚠️ CRITICAL: MUST equal len(pattern_items)
    pattern_items:
      - "MATCH"  # Expected LVS run result status
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/lvs.rep.cls
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Description requires checking LVS status and connectivity
- pattern_items use STATUS VALUES (not cell names or paths)
- "MATCH" = expected LVS run result status

**Check Behavior:**
Type 2 searches pattern_items in LVS report to validate power connectivity.
- Extracts LVS run result status
- Compares against expected values in pattern_items
- PASS if: found_items contains all pattern_items (MATCH status)
- FAIL if: missing_items not empty (status not MATCH)

**Sample Output (PASS):**
```
Status: PASS
Reason: LVS comparison matched successfully | Power connectivity validated | All instances properly connected

Log format (CheckList.rpt):
INFO01:
  - MATCH: LVS Run Result status validated

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: MATCH. In line 15, ${CHECKLIST_ROOT}/IP_project_folder/reports/lvs.rep.cls: LVS comparison matched successfully | Power connectivity validated | All instances properly connected
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-01:
  description: "Confirm the design has no power open/short and all instances are physically connected."
  requirements:
    value: 1  # ⚠️ CRITICAL: MUST equal len(pattern_items)
    pattern_items:
      - "MATCH"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/lvs.rep.cls
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Power connectivity validation is informational during pre-tapeout phase"
      - "Note: LVS status mismatches are acceptable as power grid is still being optimized"
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

Log format (CheckList.rpt):
INFO01:
  - "Explanation: Power connectivity validation is informational during pre-tapeout phase"
  - "Note: LVS status mismatches are acceptable as power grid is still being optimized"
INFO02:
  - MISMATCH: LVS Run Result status (expected MATCH)

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: Explanation: Power connectivity validation is informational during pre-tapeout phase. [WAIVED_INFO]
2: Info: Note: LVS status mismatches are acceptable as power grid is still being optimized. [WAIVED_INFO]
3: Info: MISMATCH. In line 15, ${CHECKLIST_ROOT}/IP_project_folder/reports/lvs.rep.cls: LVS comparison failed | Power connectivity requirements not satisfied [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-01:
  description: "Confirm the design has no power open/short and all instances are physically connected."
  requirements:
    value: 1  # ⚠️ CRITICAL: MUST equal len(pattern_items)
    pattern_items:
      - "MATCH"  # GOLDEN VALUE: Expected LVS run result status
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/lvs.rep.cls
  waivers:
    value: 1
    waive_items:
      - name: "Overall Run Result"  # EXEMPTION: Item name to exempt
        reason: "Waived - LVS mismatch acceptable for this design phase per design review"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Extract LVS status from report
- Compare against pattern_items (expected MATCH status)
- Match found violations against waive_items by name
- Unwaived violations → ERROR (need fix)
- Waived violations → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
- PASS if all violations are waived

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived

Log format (CheckList.rpt):
INFO01:
  - Overall Run Result: LVS mismatch waived
WARN01:
  - (none - all waivers used)

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: Overall Run Result. In line 15, ${CHECKLIST_ROOT}/IP_project_folder/reports/lvs.rep.cls: Power connectivity violation waived per design review: Waived - LVS mismatch acceptable for this design phase per design review [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-01:
  description: "Confirm the design has no power open/short and all instances are physically connected."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/lvs.rep.cls
  waivers:
    value: 1
    waive_items:
      - name: "Overall Run Result"  # ⚠️ MUST match Type 3 waive_items
        reason: "Waived - LVS mismatch acceptable for this design phase per design review"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (item names to exempt)
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (no pattern_items), plus waiver classification:
- Parse LVS report for power connectivity violations
- Match violations against waive_items by name
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
- PASS if all violations are waived

**Sample Output:**
```
Status: PASS
Reason: All items waived

Log format (CheckList.rpt):
INFO01:
  - Overall Run Result: LVS mismatch waived
WARN01:
  - (none - all waivers used)

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: Overall Run Result. In line 15, ${CHECKLIST_ROOT}/IP_project_folder/reports/lvs.rep.cls: Power connectivity violation waived per design review: Waived - LVS mismatch acceptable for this design phase per design review [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 11.0_POWER_EMIR_CHECK --checkers IMP-11-0-0-01 --force

# Run individual tests
python IMP-11-0-0-01.py
```

---

## Notes

**Limitations:**
- Checker relies on Pegasus LVS report format (.cls file). Other LVS tools may require parser modifications.

**Known Issues:**
- Empty or missing lvs.rep.cls file → Return error in metadata
- LVS run not completed → Check for "Run Result" line existence

**Power Connectivity Detection Strategy:**
The checker identifies power issues through the overall LVS run result indicator (MATCH/MISMATCH).

**Edge Cases:**
- Empty or missing lvs.rep.cls file → Return error in metadata
- LVS run not completed → Check for "Run Result" line existence