# IMP-8-0-0-05: Confirm the power switches connection is correct . (for non-PSO, please fill N/A)

## Overview

**Check ID:** IMP-8-0-0-05  
**Description:** Confirm the power switches connection is correct . (for non-PSO, please fill N/A)  
**Category:** Physical Implementation - Power Switch Verification  
**Input Files:** 
- `${CHECKLIST_ROOT}\IP_project_folder\logs\8.0\do_fv.log`
- `${CHECKLIST_ROOT}\IP_project_folder\reports\8.0\check_power_switch_connection.pass.rpt`

This checker verifies power switch connections using two complementary methods:
1. **Formal Verification (LEC)**: Analyzes `do_fv.log` to confirm Logic Equivalence Checking succeeded
2. **Database Verification**: Analyzes connectivity report to confirm no connection problems or warnings

The checker performs a dual-validation approach where BOTH checks must pass for overall PASS status. For non-PSO (Power Shut-Off) designs, this check should report N/A.

---

## Check Logic

### Input Parsing

**Step 1: Parse Formal Verification Log (`do_fv.log`)**

Search for LEC success pattern indicating formal verification passed:

```python
# Pattern 1: LEC Success Indicator
pattern_lec_success = r'SUCCEEDED!'
# Example: "// LEC verification SUCCEEDED!"
# Extraction: Boolean flag - indicates formal verification passed
```

**Step 2: Parse Connectivity Report (`check_power_switch_connection.pass.rpt`)**

Search for summary section indicating no connectivity problems:

```python
# Pattern 2: Summary Section Boundary
pattern_summary_start = r'^Begin Summary\s*$'
pattern_summary_end = r'^End Summary\s*$'
# Example: "Begin Summary"
# Extraction: Marks summary section for parsing

# Pattern 3: No Problems Indicator (CRITICAL)
pattern_no_problems = r'^\s*Found no problems or warnings\.\s*$'
# Example: "    Found no problems or warnings."
# Extraction: Boolean flag - indicates connectivity verification passed
```

### Detection Logic

**Type 1/4 Boolean Check Logic:**

This is a dual-validation boolean check with NO pattern_items required:

1. **Parse do_fv.log**:
   - Search entire file for pattern `SUCCEEDED!`
   - If matched: Store match info (line content, line number, source file)
   - Set flag: `lec_passed = True`

2. **Parse connectivity report**:
   - Locate "Begin Summary" section
   - Search within summary for pattern `Found no problems or warnings.`
   - If matched: Store match info (line content, line number, source file)
   - Set flag: `db_check_passed = True`

3. **Determine PASS/FAIL**:
   - **PASS Condition**: `lec_passed == True AND db_check_passed == True`
   - **FAIL Condition**: `lec_passed == False OR db_check_passed == False`

4. **Edge Cases**:
   - Non-PSO design: If neither file contains PSO-related content, report N/A
   - Missing files: Treat as FAIL
   - Incomplete logs: If summary section missing, treat as FAIL

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `status_check`

**Selected Mode for this checker:** N/A (Type 1/4 - Boolean check, no pattern_items)

**Rationale:** This is a Type 1 boolean check that validates power switch connections through dual verification (LEC + database check). No pattern matching is required - the checker performs custom validation logic to determine if both verification methods passed. The check returns a simple PASS/FAIL based on whether both `SUCCEEDED!` and `Found no problems or warnings.` patterns are found.

---

## Output Descriptions (CRITICAL - Code Generator Uses These!)

This section defines the output strings used by `build_complete_output()` in the checker code.

```python
# ⚠️ CRITICAL: Description & Reason parameter usage by Type (API-026)
# Both DESC and REASON constants are split by Type for semantic clarity:
#   Type 1/4 (Boolean): Use DESC_TYPE1_4 & REASON_TYPE1_4 (emphasize "found/not found")
#   Type 2/3 (Pattern): Use DESC_TYPE2_3 & REASON_TYPE2_3 (emphasize "matched/satisfied")

# Item description for this checker
item_desc = "Confirm the power switches connection is correct . (for non-PSO, please fill N/A)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "Power switch connection verification passed - both LEC and database checks succeeded"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "Power switch connection patterns validated successfully"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Power Switch Connection is CORRECT based on db check and LEC result."
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Power switch connection requirements matched and validated"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Power switch connection verification failed - LEC or database check did not pass"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Power switch connection patterns not satisfied"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Power Switch Connection is WRONG based on db check and LEC result."
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Power switch connection requirements not satisfied or missing"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Power switch connection issues waived per design approval"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Power switch connection issue waived - approved by design team for non-critical path"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries for power switch connection check"
unused_waiver_reason = "Waiver entry not matched - no corresponding power switch connection issue found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "Power Switch Connection is CORRECT based on db check and LEC result."
  Example: "LEC verification: SUCCEEDED! | Database check: Found no problems or warnings."

ERROR01 (Violation/Fail items):
  Format: "[CHECK_TYPE]: [failure_details]"
  Example: "LEC verification: FAILED - pattern 'SUCCEEDED!' not found in do_fv.log"
  Example: "Database check: FAILED - problems found in connectivity report"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-05:
  description: "Confirm the power switches connection is correct . (for non-PSO, please fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\8.0\\do_fv.log"
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\8.0\\check_power_switch_connection.pass.rpt"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs dual boolean validation:
1. Searches `do_fv.log` for pattern `SUCCEEDED!` (LEC verification)
2. Searches connectivity report for pattern `Found no problems or warnings.` (database check)
3. PASS if BOTH patterns found, FAIL if either pattern missing

**Sample Output (PASS):**
```
Status: PASS
Reason: Power Switch Connection is CORRECT based on db check and LEC result.
INFO01:
  - LEC verification: SUCCEEDED! (found in do_fv.log)
  - Database check: Found no problems or warnings. (found in check_power_switch_connection.pass.rpt)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Power Switch Connection is WRONG based on db check and LEC result.
ERROR01:
  - LEC verification: Pattern 'SUCCEEDED!' not found in do_fv.log
  - Database check: Summary section missing or problems detected in connectivity report
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-05:
  description: "Confirm the power switches connection is correct . (for non-PSO, please fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\8.0\\do_fv.log"
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\8.0\\check_power_switch_connection.pass.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Power switch connection check is informational only for this design phase"
      - "Note: LEC verification failures are expected during early integration and do not block signoff"
```

**CRITICAL Behavior (waivers.value=0):**
- NOTE: Type 1 has NO waiver logic. waive=0 is forced PASS mode only
- IMPORTANT: waive_items uses PLAIN STRINGS (NOT name/reason dict like Type 3/4!)
- waive_items serves as COMMENT ONLY (no matching/filtering logic)
- waive_items content printed as INFO with [WAIVED_INFO] tag
- ALL violations force converted: FAIL→PASS, displayed as INFO with [WAIVED_AS_INFO] tag
- Check ALWAYS returns PASS (violations shown as INFO for tracking)
- Used when: Check is informational only, connection issues expected/acceptable during development

**Sample Output (PASS with violations):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All violations waived as informational
INFO01 ([WAIVED_INFO] - waive_items as comment):
  - "Explanation: Power switch connection check is informational only for this design phase"
  - "Note: LEC verification failures are expected during early integration and do not block signoff"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - LEC verification: Pattern 'SUCCEEDED!' not found in do_fv.log [WAIVED_AS_INFO]
  - Database check: Problems detected in connectivity report [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-05:
  description: "Confirm the power switches connection is correct . (for non-PSO, please fill N/A)"
  requirements:
    value: 2
    pattern_items:
      - "SUCCEEDED!"
      - "Found no problems or warnings."
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\8.0\\do_fv.log"
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\8.0\\check_power_switch_connection.pass.rpt"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 searches for specific success patterns in input files.
- Pattern 1: `SUCCEEDED!` in do_fv.log (LEC verification)
- Pattern 2: `Found no problems or warnings.` in connectivity report (database check)
- PASS if both patterns found (missing_items empty)
- FAIL if any pattern not found (missing_items not empty)

**Sample Output (PASS):**
```
Status: PASS
Reason: Power switch connection requirements matched and validated
INFO01:
  - SUCCEEDED! (found in do_fv.log, line 1234)
  - Found no problems or warnings. (found in check_power_switch_connection.pass.rpt, line 56)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-05:
  description: "Confirm the power switches connection is correct . (for non-PSO, please fill N/A)"
  requirements:
    value: 2
    pattern_items:
      - "SUCCEEDED!"
      - "Found no problems or warnings."
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\8.0\\do_fv.log"
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\8.0\\check_power_switch_connection.pass.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Power switch verification is informational during early design phase"
      - "Note: Pattern mismatches are expected before final power grid implementation"
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
  - "Explanation: Power switch verification is informational during early design phase"
  - "Note: Pattern mismatches are expected before final power grid implementation"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - Pattern 'SUCCEEDED!' not found in do_fv.log [WAIVED_AS_INFO]
  - Pattern 'Found no problems or warnings.' not found in connectivity report [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-05:
  description: "Confirm the power switches connection is correct . (for non-PSO, please fill N/A)"
  requirements:
    value: 2
    pattern_items:
      - "SUCCEEDED!"
      - "Found no problems or warnings."
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\8.0\\do_fv.log"
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\8.0\\check_power_switch_connection.pass.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "SUCCEEDED!"
        reason: "LEC verification waived - formal verification not required for this design iteration"
      - name: "Found no problems or warnings."
        reason: "Database check waived - known connectivity issues approved by design team"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Search for patterns in input files
- Match found violations against waive_items
- Unwaived violations → ERROR (need fix)
- Waived violations → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - Pattern 'SUCCEEDED!' not found in do_fv.log [WAIVER]
    Reason: LEC verification waived - formal verification not required for this design iteration
  - Pattern 'Found no problems or warnings.' not found in connectivity report [WAIVER]
    Reason: Database check waived - known connectivity issues approved by design team
WARN01 (Unused Waivers):
  (none - all waivers matched)
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-05:
  description: "Confirm the power switches connection is correct . (for non-PSO, please fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\8.0\\do_fv.log"
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\8.0\\check_power_switch_connection.pass.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "SUCCEEDED!"
        reason: "LEC verification waived - formal verification not required for this design iteration"
      - name: "Found no problems or warnings."
        reason: "Database check waived - known connectivity issues approved by design team"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (dual verification), plus waiver classification:
- Perform LEC and database checks
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
  - LEC verification failed: Pattern 'SUCCEEDED!' not found [WAIVER]
    Reason: LEC verification waived - formal verification not required for this design iteration
  - Database check failed: Pattern 'Found no problems or warnings.' not found [WAIVER]
    Reason: Database check waived - known connectivity issues approved by design team
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 8.0_PHYSICAL_IMPLEMENTATION_CHECK --checkers IMP-8-0-0-05 --force

# Run individual tests
python IMP-8-0-0-05.py
```

---

## Notes

**Design Intent:**
- This checker implements a dual-validation approach for power switch connections
- Both LEC (formal verification) and database connectivity checks must pass
- Designed to catch power switch connection errors early in the implementation flow

**Limitations:**
- For non-PSO designs, this check may not be applicable (should report N/A)
- Requires both input files to be present and complete
- LEC log must contain clear success/failure indicators
- Connectivity report must have properly formatted summary section

**Known Issues:**
- If LEC run is incomplete, `SUCCEEDED!` pattern may not appear even if no errors occurred
- Connectivity report format may vary between tool versions
- Summary section parsing assumes specific format ("Begin Summary" / "End Summary")

**Edge Cases:**
- **Non-PSO Design**: If neither file contains PSO-related content, checker should detect and report N/A
- **Missing Files**: Treat as FAIL rather than error to ensure visibility
- **Incomplete Logs**: If LEC run was interrupted, treat as FAIL
- **Empty Summary**: If connectivity report has no summary section, treat as FAIL