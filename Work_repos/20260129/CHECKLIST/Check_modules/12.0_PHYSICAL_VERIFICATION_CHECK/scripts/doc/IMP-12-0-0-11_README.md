# IMP-12-0-0-11: Confirm the DRC check result is clean. (fill the confidence level of not touching floorplan again in comment if fill no, for example, 90%~100%)

## Overview

**Check ID:** IMP-12-0-0-11  
**Description:** Confirm the DRC check result is clean. (fill the confidence level of not touching floorplan again in comment if fill no, for example, 90%~100%)  
**Category:** Physical Verification - DRC Compliance  
**Input Files:** 
- `${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_DRC.rep`
- `${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_DRC.rep`

This checker validates that all DRC (Design Rule Check) reports are clean (zero violations). It supports both Calibre and Pegasus DRC report formats, aggregates violations across all provided reports, and supports waiving specific DRC rule violations. The checker only passes when all DRC violations are either zero or fully waived.

---

## Check Logic

### Input Parsing

The checker parses two types of DRC reports with different formats:

**Calibre DRC Report Format:**
```python
# Pattern 1: Individual rule violation count
pattern_calibre_rule = r'^\s*RULECHECK\s+(\S+)\s+\.+\s+TOTAL\s+Result\s+Count\s+=\s+(\d+)\s+\((\d+)\)'
# Example: "RULECHECK EFP.VIA13.R.1.1 ..................................... TOTAL Result Count = 41    (41)"
# Group 1: DRC rule name (e.g., "EFP.VIA13.R.1.1")
# Group 2: Violation count (e.g., "41") - this is the primary count
# Group 3: Secondary count (e.g., "41") - ignored per user hints

# Pattern 2: Total DRC violations summary
pattern_calibre_total = r'^\s*TOTAL\s+DRC\s+Results\s+Generated:\s+(\d+)\s+\((\d+)\)'
# Example: "TOTAL DRC Results Generated:     16819 (49568208)"
# Group 1: Total violation count (e.g., "16819")
# Group 2: Secondary count (e.g., "49568208") - ignored per user hints
```

**Pegasus DRC Report Format:**
```python
# Pattern 1: Individual rule violation count
pattern_pegasus_rule = r'^\s*RULECHECK\s+(\S+)\s+\.+\s+Total\s+Result\s+(\d+)\s+\(\s*(\d+)\s*\)'
# Example: "RULECHECK RH_TN.WARN.1 ................................. Total Result        256 (     43219)"
# Group 1: DRC rule name (e.g., "RH_TN.WARN.1")
# Group 2: Violation count (e.g., "256") - this is the primary count
# Group 3: Secondary count (e.g., "43219") - ignored per user hints

# Pattern 2: Total DRC violations summary
pattern_pegasus_total = r'^\s*Total\s+DRC\s+Results\s*:\s*(\d+)\s+\(\s*(\d+)\s*\)'
# Example: "Total DRC Results                 : 258 (43252)"
# Group 1: Total violation count (e.g., "258")
# Group 2: Secondary count (e.g., "43252") - ignored per user hints
```

### Detection Logic

1. **Multi-Report Processing:**
   - Iterate through all provided DRC report files (Calibre and/or Pegasus)
   - Detect report type by parsing header or format patterns
   - Aggregate violations across all reports

2. **Violation Extraction:**
   - For each report, extract individual rule violations with format: `"RuleName: Count"`
   - Example: `"EFP.VIA13.R.1.1: 41"`, `"RH_TN.WARN.1: 256"`
   - Store rule name and violation count for each violation

3. **Total Count Calculation:**
   - Sum all violation counts across all reports
   - Verify total matches sum of individual rule violations

4. **Waiver Processing (Type 3/4):**
   - Match found violations against `waive_items` by rule name and count
   - Waiver format: `"RuleName: Count"` (e.g., `"RH_TN.WARN.1: 300"`)
   - Classify violations:
     - **Unwaived:** Violations not in waive_items → ERROR
     - **Waived:** Violations matching waive_items → INFO with [WAIVER] tag
     - **Unused waivers:** waive_items not matching any violation → WARN with [WAIVER] tag

5. **Clean Determination:**
   - **DRC Clean (PASS):** Total violations = 0 OR all violations are waived
   - **DRC Not Clean (FAIL):** Total violations > 0 AND some violations are unwaived

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `status_check`

Choose ONE mode based on what pattern_items represents:

### Mode 1: `existence_check` - Existence Check
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

### Mode 2: `status_check` - Status Check  
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

**Selected Mode for this checker:** `status_check`

**Rationale:** This checker validates DRC violation status (clean vs. not clean). The checker searches for DRC violations in reports and validates their status. Pattern items are not used in Type 1/4 (boolean check), but in Type 2/3 configurations, pattern_items would represent specific DRC rules to check. Only violations found in reports are output, making this a status check rather than existence check.

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
item_desc = "DRC check result validation"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "DRC clean - no violations found in all reports"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All DRC rules validated - no violations detected"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "All DRC reports show zero violations (DRC clean)"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All specified DRC rules validated with zero violations"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "DRC violations detected - design not clean"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "DRC rule violations detected - requirements not satisfied"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "DRC violations found in reports - design requires fixes"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "DRC rule violations detected - design rules not satisfied"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Waived DRC violations"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "DRC violation waived per design approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused DRC waiver entries"
unused_waiver_reason = "Waiver entry not matched - no corresponding DRC violation found in reports"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [rule_name]: [violation_count] violations - [found_reason]"
  Example: "- EFP.VIA13.R.1.1: 0 violations - All DRC reports show zero violations (DRC clean)"

ERROR01 (Violation/Fail items):
  Format: "- [rule_name]: [violation_count] violations - [missing_reason]"
  Example: "- EFP.VIA13.R.1.1: 41 violations - DRC violations found in reports - design requires fixes"
  Example: "- RH_TN.WARN.1: 256 violations - DRC violations found in reports - design requires fixes"

Summary Format:
  "Total DRC violations across all reports: [total_count]"
  "DRC Status: CLEAN" (if total = 0 or all waived)
  "DRC Status: NOT CLEAN - [unwaived_count] unwaived violations" (if violations exist)
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-11:
  description: "Confirm the DRC check result is clean. (fill the confidence level of not touching floorplan again in comment if fill no, for example, 90%~100%)"
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
Type 1 performs boolean DRC clean validation across all provided reports.
- Parses all Calibre and Pegasus DRC reports
- Aggregates total violation count across all reports
- PASS if total violations = 0 (DRC clean)
- FAIL if total violations > 0 (DRC not clean)

**Sample Output (PASS):**
```
Status: PASS
Reason: All DRC reports show zero violations (DRC clean)
INFO01:
  - Calibre_DRC.rep: 0 violations - All DRC reports show zero violations (DRC clean)
  - Pegasus_DRC.rep: 0 violations - All DRC reports show zero violations (DRC clean)
  - Summary: Total DRC violations across all reports: 0 - DRC Status: CLEAN
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: DRC violations found in reports - design requires fixes
ERROR01:
  - EFP.VIA13.R.1.1: 41 violations - DRC violations found in reports - design requires fixes
  - RH_TN.WARN.1: 256 violations - DRC violations found in reports - design requires fixes
  - Summary: Total DRC violations across all reports: 297 - DRC Status: NOT CLEAN - 297 unwaived violations
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-11:
  description: "Confirm the DRC check result is clean. (fill the confidence level of not touching floorplan again in comment if fill no, for example, 90%~100%)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_DRC.rep"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_DRC.rep"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: DRC violations are informational only for this design phase"
      - "Note: Violations will be addressed in final tape-out revision"
      - "Confidence Level: 95% - floorplan stable, only minor routing adjustments expected"
```

**CRITICAL Behavior (waivers.value=0):**
- NOTE: Type 1 has NO waiver logic. waive=0 is forced PASS mode only
- IMPORTANT: waive_items uses PLAIN STRINGS (NOT name/reason dict like Type 3/4!)
- waive_items serves as COMMENT ONLY (no matching/filtering logic)
- waive_items content printed as INFO with [WAIVED_INFO] tag
- ALL violations force converted: FAIL→PASS, displayed as INFO with [WAIVED_AS_INFO] tag
- Check ALWAYS returns PASS (violations shown as INFO for tracking)
- Used when: DRC check is informational only, violations expected/acceptable during development

**Sample Output (PASS with violations):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All violations waived as informational
INFO01 ([WAIVED_INFO] - waive_items as comment):
  - "Explanation: DRC violations are informational only for this design phase"
  - "Note: Violations will be addressed in final tape-out revision"
  - "Confidence Level: 95% - floorplan stable, only minor routing adjustments expected"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - EFP.VIA13.R.1.1: 41 violations - DRC violations found in reports - design requires fixes [WAIVED_AS_INFO]
  - RH_TN.WARN.1: 256 violations - DRC violations found in reports - design requires fixes [WAIVED_AS_INFO]
  - Summary: Total DRC violations: 297 (all waived as informational) [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-11:
  description: "Confirm the DRC check result is clean. (fill the confidence level of not touching floorplan again in comment if fill no, for example, 90%~100%)"
  requirements:
    value: 3
    pattern_items:
      - "EFP.VIA13.R.1.1: 0"
      - "RH_TN.WARN.1: 0"
      - "AN.R.20mg: 0"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_DRC.rep"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_DRC.rep"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Pattern items represent expected DRC rule status (rule name + expected violation count)
- Format: `"RuleName: ExpectedCount"` (e.g., `"EFP.VIA13.R.1.1: 0"`)
- ExpectedCount is typically `0` for clean DRC validation
- Use actual DRC rule names from file analysis

**Check Behavior:**
Type 2 searches for specific DRC rules in reports and validates their violation counts.
- Parse all DRC reports and extract rule violations
- Match found rules against pattern_items
- PASS if all pattern_items found with expected counts (typically 0)
- FAIL if any pattern_items missing or have non-zero counts

**Sample Output (PASS):**
```
Status: PASS
Reason: All specified DRC rules validated with zero violations
INFO01:
  - EFP.VIA13.R.1.1: 0 violations - All specified DRC rules validated with zero violations
  - RH_TN.WARN.1: 0 violations - All specified DRC rules validated with zero violations
  - AN.R.20mg: 0 violations - All specified DRC rules validated with zero violations
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-11:
  description: "Confirm the DRC check result is clean. (fill the confidence level of not touching floorplan again in comment if fill no, for example, 90%~100%)"
  requirements:
    value: 3
    pattern_items:
      - "EFP.VIA13.R.1.1: 0"
      - "RH_TN.WARN.1: 0"
      - "AN.R.20mg: 0"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_DRC.rep"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_DRC.rep"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Specific DRC rules are informational only for this design phase"
      - "Note: Rule violations will be addressed in final tape-out revision"
      - "Confidence Level: 90% - floorplan stable, minor routing adjustments expected"
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
  - "Explanation: Specific DRC rules are informational only for this design phase"
  - "Note: Rule violations will be addressed in final tape-out revision"
  - "Confidence Level: 90% - floorplan stable, minor routing adjustments expected"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - EFP.VIA13.R.1.1: 41 violations (expected 0) [WAIVED_AS_INFO]
  - RH_TN.WARN.1: 256 violations (expected 0) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-11:
  description: "Confirm the DRC check result is clean. (fill the confidence level of not touching floorplan again in comment if fill no, for example, 90%~100%)"
  requirements:
    value: 0  # ⚠️ GOLDEN VALUE: Expected violation count (0 = clean)
    pattern_items:
      - "0"  # Expected total violation count across all reports
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_DRC.rep"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_DRC.rep"
  waivers:
    value: 2
    waive_items:
      - name: "RH_TN.WARN.1: 300"  # ⚠️ EXEMPTION: Rule name + count to exempt
        reason: "Routing hierarchy warnings in legacy blocks - waived per IP vendor approval"
      - name: "AN.R.20mg: 290"
        reason: "Antenna ratio violations in test structures - waived per design review"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same DRC violation search logic as Type 2, plus waiver classification:
- Parse all DRC reports and extract rule violations
- Match found violations against waive_items by rule name and count
- Classify violations:
  - **Unwaived:** Violations not in waive_items → ERROR (need fix)
  - **Waived:** Violations matching waive_items → INFO with [WAIVER] tag (approved)
  - **Unused waivers:** waive_items not matching any violation → WARN with [WAIVER] tag
- PASS if all violations are waived (total unwaived = 0)
- FAIL if any unwaived violations exist

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - RH_TN.WARN.1: 300 violations - DRC violation waived per design approval: Routing hierarchy warnings in legacy blocks - waived per IP vendor approval [WAIVER]
  - AN.R.20mg: 290 violations - DRC violation waived per design approval: Antenna ratio violations in test structures - waived per design review [WAIVER]
  - Summary: Total DRC violations: 590 (all waived)
WARN01 (Unused Waivers):
  (none - all waivers matched violations)
```

**Sample Output (with unwaived violations):**
```
Status: FAIL
Reason: DRC rule violations detected - design rules not satisfied
ERROR01 (Unwaived):
  - EFP.VIA13.R.1.1: 41 violations - DRC violations found in reports - design requires fixes
INFO01 (Waived):
  - RH_TN.WARN.1: 300 violations - DRC violation waived per design approval: Routing hierarchy warnings in legacy blocks - waived per IP vendor approval [WAIVER]
  - Summary: Total DRC violations: 341 (41 unwaived, 300 waived)
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-11:
  description: "Confirm the DRC check result is clean. (fill the confidence level of not touching floorplan again in comment if fill no, for example, 90%~100%)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_DRC.rep"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_DRC.rep"
  waivers:
    value: 2
    waive_items:
      - name: "RH_TN.WARN.1: 300"  # ⚠️ MUST match Type 3 waive_items
        reason: "Routing hierarchy warnings in legacy blocks - waived per IP vendor approval"
      - name: "AN.R.20mg: 290"
        reason: "Antenna ratio violations in test structures - waived per design review"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (keep exemption object names consistent)
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean DRC clean check as Type 1 (no pattern_items), plus waiver classification:
- Parse all DRC reports and extract all violations
- Match violations against waive_items by rule name and count
- Classify violations:
  - **Unwaived:** Violations not in waive_items → ERROR
  - **Waived:** Violations matching waive_items → INFO with [WAIVER] tag
  - **Unused waivers:** waive_items not matching any violation → WARN with [WAIVER] tag
- PASS if all violations are waived (total unwaived = 0)
- FAIL if any unwaived violations exist

**Sample Output:**
```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - RH_TN.WARN.1: 300 violations - DRC violation waived per design approval: Routing hierarchy warnings in legacy blocks - waived per IP vendor approval [WAIVER]
  - AN.R.20mg: 290 violations - DRC violation waived per design approval: Antenna ratio violations in test structures - waived per design review [WAIVER]
  - Summary: Total DRC violations: 590 (all waived)
WARN01 (Unused Waivers):
  (none - all waivers matched violations)
```

**Sample Output (with unwaived violations):**
```
Status: FAIL
Reason: DRC violations found in reports - design requires fixes
ERROR01 (Unwaived):
  - EFP.VIA13.R.1.1: 41 violations - DRC violations found in reports - design requires fixes
INFO01 (Waived):
  - RH_TN.WARN.1: 300 violations - DRC violation waived per design approval: Routing hierarchy warnings in legacy blocks - waived per IP vendor approval [WAIVER]
  - Summary: Total DRC violations: 341 (41 unwaived, 300 waived)
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 12.0_PHYSICAL_VERIFICATION_CHECK --checkers IMP-12-0-0-11 --force

# Run individual tests
python IMP-12-0-0-11.py
```

---

## Notes

### Multi-Report Aggregation
- The checker supports processing multiple DRC reports simultaneously (both Calibre and Pegasus)
- Violations are aggregated across all reports
- Total violation count is the sum of all violations from all reports
- DRC is only clean when ALL reports show zero violations (or all violations are waived)

### Report Format Differences
- **Calibre:** Uses `TOTAL Result Count = X (Y)` format, where X is the violation count
- **Pegasus:** Uses `Total Result X (Y)` format, where X is the violation count
- Both formats have a secondary count in parentheses which is ignored per user requirements

### Waiver Format
- Waivers must specify both rule name and violation count: `"RuleName: Count"`
- Example: `"RH_TN.WARN.1: 300"` waives exactly 300 violations of rule RH_TN.WARN.1
- Partial waivers are not supported (must waive exact count)
- Unused waivers are reported as warnings to help maintain waiver list accuracy

### Confidence Level Reporting
- When using waivers.value=0 (forced PASS mode), include confidence level in waive_items comments
- Example: `"Confidence Level: 95% - floorplan stable, only minor routing adjustments expected"`
- This helps track design stability when DRC violations are temporarily accepted

### Known Limitations
- Runtime warnings (ACUTE angles, SKEW edges) in Calibre reports are geometry flags, not DRC violations
- These warnings are informational and do not affect DRC clean status
- The checker focuses on actual DRC rule violations (RULECHECK entries)