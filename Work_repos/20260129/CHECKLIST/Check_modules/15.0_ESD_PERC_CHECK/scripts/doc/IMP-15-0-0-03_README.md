# IMP-15-0-0-03: Confirm there is no issue about ESD PERC check if PERC check is needed.

## Overview

**Check ID:** IMP-15-0-0-03  
**Description:** Confirm there is no issue about ESD PERC check if PERC check is needed.  
**Category:** ESD Verification  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/prec*.rep`

This checker validates PERC (Parasitic Extraction Rule Check) verification reports to ensure ESD (Electrostatic Discharge) protection rules are properly verified. It parses PERC report files to detect CHECK status (PASSED/FAILED), counts verified cells, and identifies any violations or failures in the ESD PERC verification process.

---

## Check Logic

### Input Parsing
Parse PERC report files (`.rep`) to extract:
1. Overall CHECK status (PASSED/FAILED) from verification results section
2. Cell verification details (cell names and placement counts)
3. LVS filter configurations
4. Any error or violation messages

**Key Patterns:**
```python
# Pattern 1: Check PASSED status indicator
pattern1 = r'#\s+CHECK\(s\)\s+PASSED\s+#'
# Example: "                          #           CHECK(s) PASSED          #"

# Pattern 2: Check FAILED status indicator
pattern2 = r'#\s+CHECK\(s\)\s+FAILED\s+#'
# Example: "                          #           CHECK(s) FAILED          #"

# Pattern 3: Cell name and placement count
pattern3 = r'CELL NAME:\s+(\S+)\s+\((\d+)\s+placements?\)'
# Example: "CELL NAME:         AIOI21ARD1BWP143M169H3P48CPDLVTLL (10 placements)  # Limit to 10KB"

# Pattern 4: LVS filter configuration
pattern4 = r'LVS FILTER\s+(\S+)\s+(OPEN|SHORT|\S+)'
# Example: "   LVS FILTER  ppode_ulvt_mac  OPEN"

# Pattern 5: Error or violation messages
pattern5 = r'(ERROR|VIOLATION|FAIL):\s*(.+)'
# Example: "ERROR: ESD protection missing on cell XYZ"
```

### Detection Logic
1. **Aggregate all PERC report files** matching pattern `prec*.rep`
2. **Parse each file line-by-line** with state tracking:
   - Track if currently in "CELL VERIFICATION RESULTS" section
   - Accumulate CHECK status indicators (PASSED/FAILED)
   - Count verified cells from "CELL NAME:" entries
   - Collect any ERROR/VIOLATION messages
3. **Determine overall status**:
   - PASS: At least one "CHECK(s) PASSED" found AND no "CHECK(s) FAILED" found
   - FAIL: Any "CHECK(s) FAILED" found OR no CHECK status found OR empty file
4. **Build output**:
   - INFO01: Summary of PERC check status with cell count for PASS cases
   - ERROR01: Specific PERC violations or failures with cell/error details

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `status_check`

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

**Selected Mode for this checker:** `status_check`

**Rationale:** This checker validates the status of PERC verification results. When pattern_items specifies filenames, the checker searches for those specific files and determines if they pass the PERC check. The checker only reports on files that are explicitly mentioned in pattern_items, not on all available files. The focus is on verifying that specified files have the correct status (PASSED), making this a status validation rather than an existence check.

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
item_desc = "Confirm there is no issue about ESD PERC check if PERC check is needed."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "ESD PERC check completed successfully - all checks found and passed"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "ESD PERC check status validated - all required checks matched and passed"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "PERC CHECK(s) PASSED status found in verification reports - no failures detected"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All PERC check patterns matched and satisfied - CHECK(s) PASSED status validated"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "ESD PERC check failed - CHECK(s) PASSED status not found or failures detected"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "ESD PERC check validation failed - required CHECK(s) PASSED pattern not satisfied"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "PERC CHECK(s) FAILED found or CHECK(s) PASSED status not found in verification reports"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "PERC check status pattern not satisfied - CHECK(s) FAILED detected or PASSED status missing"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "ESD PERC check failures waived per design team approval"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "PERC check failure waived - approved exception for specific cells or verification issues"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused PERC check waiver entries"
unused_waiver_reason = "Waiver entry not matched - no corresponding PERC check failure found in reports"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "PERC Check: PASSED | File: <filename>"
  Example: "PERC Check: PASSED | File: prec_esd_verification.rep"

ERROR01 (Violation/Fail items):
  Format: "PERC Check: FAILED | File: <filename>"
  Example: "PERC Check: FAILED | File: prec_esd_verification.rep"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-15-0-0-03:
  description: "Confirm there is no issue about ESD PERC check if PERC check is needed."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/prec*.rep
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs custom boolean checks (file exists? config valid?).
PASS/FAIL based on checker's own validation logic.

**Sample Output (PASS):**
```
Status: PASS
Reason: PERC CHECK(s) PASSED status found in verification reports - no failures detected
INFO01:
  - PERC Check: PASSED | File: prec_esd_verification.rep
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: PERC CHECK(s) FAILED found or CHECK(s) PASSED status not found in verification reports
ERROR01:
  - PERC Check: FAILED | File: prec_esd_verification.rep
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-15-0-0-03:
  description: "Confirm there is no issue about ESD PERC check if PERC check is needed."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/prec*.rep
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: PERC check is informational only for this design phase - ESD verification will be completed in final tapeout"
      - "Note: PERC failures are expected during early development and do not block design progress"
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
  - "Explanation: PERC check is informational only for this design phase - ESD verification will be completed in final tapeout"
  - "Note: PERC failures are expected during early development and do not block design progress"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - PERC Check: FAILED | File: prec_esd_verification.rep [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-15-0-0-03:
  description: "Confirm there is no issue about ESD PERC check if PERC check is needed."
  requirements:
    value: 2
    pattern_items:
      - "prec_esd_verification.rep"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/prec*.rep
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 searches pattern_items in input files.
When pattern_items specifies filenames, the checker:
- Searches for each specified filename in the input files
- Checks if the file passes the PERC check (CHECK(s) PASSED status)
- found_items: Files that are found AND pass the check
- missing_items: Files that are found BUT fail the check, OR files not found
PASS if all specified files are found and pass the check.

**Sample Output (PASS):**
```
Status: PASS
Reason: All PERC check patterns matched and satisfied - CHECK(s) PASSED status validated
INFO01:
  - PERC Check: PASSED | File: prec_esd_verification.rep
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: PERC check status pattern not satisfied - CHECK(s) FAILED detected or PASSED status missing
ERROR01:
  - PERC Check: FAILED | File: prec_esd_verification.rep
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-15-0-0-03:
  description: "Confirm there is no issue about ESD PERC check if PERC check is needed."
  requirements:
    value: 0
    pattern_items:
      - "prec_esd_verification.rep"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/prec*.rep
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: PERC pattern check is informational only - specific cell/filter verification not required at this stage"
      - "Note: Pattern mismatches are expected during incremental design updates and do not require immediate fixes"
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
  - "Explanation: PERC pattern check is informational only - specific cell/filter verification not required at this stage"
  - "Note: Pattern mismatches are expected during incremental design updates and do not require immediate fixes"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - PERC Check: FAILED | File: prec_esd_verification.rep [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-15-0-0-03:
  description: "Confirm there is no issue about ESD PERC check if PERC check is needed."
  requirements:
    value: 2
    pattern_items:
      - "prec_esd_verification.rep"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/prec*.rep
  waivers:
    value: 2
    waive_items:
      - filename: "prec_esd_verification.rep"
        reason: "Waived - legacy cell with known ESD protection issue, approved by design team for non-critical paths"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
When pattern_items specifies filenames, the checker:
- Searches for each specified filename in the input files
- Checks if the file passes the PERC check (CHECK(s) PASSED status)
- found_items: Files that fail the check (violations)
- Match found_items (failed files) against waive_items by filename
- Unwaived items → ERROR (need fix)
- Waived items → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all failed files are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - prec_esd_verification.rep [WAIVER]: Waived - legacy cell with known ESD protection issue, approved by design team for non-critical paths
WARN01 (Unused Waivers):
  - (none)
```

**Sample Output (with unwaived violations):**
```
Status: FAIL
Reason: PERC check status pattern not satisfied - CHECK(s) FAILED detected or PASSED status missing
ERROR01:
  - PERC Check: FAILED | File: prec_esd_verification.rep
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-15-0-0-03:
  description: "Confirm there is no issue about ESD PERC check if PERC check is needed."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/15.0/prec*.rep
  waivers:
    value: 2
    waive_items:
      - name: "prec_esd_verification.rep"
        reason: "Waived - legacy cell with known ESD protection issue, approved by design team for non-critical paths"
```

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (no pattern_items), plus waiver classification:
- Match violations against waive_items by filename
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output:**
```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - prec_esd_verification.rep [WAIVER]: Waived - legacy cell with known ESD protection issue, approved by design team for non-critical paths
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 15.0_ESD_PERC_CHECK --checkers IMP-15-0-0-03 --force

# Run individual tests
python IMP-15-0-0-03.py
```

---

## Notes

- **Multi-file aggregation**: The checker processes all files matching `prec*.rep` pattern and aggregates results to determine overall PASS/FAIL status
- **State tracking**: Parser tracks whether currently in "CELL VERIFICATION RESULTS" section to properly extract cell verification data
- **Edge cases handled**:
  - Empty files → reported as ERROR (PERC check not run)
  - Missing CHECK status section → reported as ERROR (incomplete report)
  - Multiple CHECK sections → all results aggregated
  - Mixed PASS/FAIL across cells → reported as overall FAIL
- **LVS filter information**: LVS filter configurations (e.g., "ppode_ulvt_mac OPEN") are extracted for context but do not directly affect PASS/FAIL status
- **Cell placement counts**: The number of placements per cell is tracked for informational purposes in the output
- **CHECK status priority**: The presence of any "CHECK(s) FAILED" indicator overrides any "CHECK(s) PASSED" indicators, resulting in overall FAIL status
- **Type 2/3 filename matching**: When pattern_items specifies filenames, the checker searches for those specific files and checks their PERC status. Only files listed in pattern_items are checked. In Type 3, waive_items with matching filenames will waive the corresponding failed files.