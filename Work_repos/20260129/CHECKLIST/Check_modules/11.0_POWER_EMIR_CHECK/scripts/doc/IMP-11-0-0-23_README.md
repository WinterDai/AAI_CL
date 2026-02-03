# IMP-11-0-0-23: Confirm all Warning message in power analysis log files can be waived.

## Overview

**Check ID:** IMP-11-0-0-23  
**Description:** Confirm all Warning message in power analysis log files can be waived.  
**Category:** Power Analysis Validation  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv`, `${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup_static.logv`, `${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_tt_0p75v_85c_typical_typical_setup_dynamic.logv`, `${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/noerror.logv`

This checker validates that all warning messages found in Cadence Voltus power analysis log files (.logv) are either in the approved waiver list or can be safely ignored. It ensures power integrity analysis warnings are properly tracked and approved, preventing unreviewed warnings from blocking design signoff.

---

## Check Logic

### Input Parsing

The checker parses Cadence Voltus power analysis log files (.logv) to extract all warning messages with their codes, messages, file paths, and line numbers.

**Key Patterns:**

```python
# Pattern 1: Cadence formatted warnings with code in parentheses
pattern1 = r'\*\*WARN:\s*\(([A-Z_]+-\d+)\):\s*(.+)'
# Example: "**WARN: (IMPLF-378):\tThe spacing for cell edge type 'NW_0D5' and 'NW_0D5' is already defined."

# Pattern 2: Standard WARNING messages without ** prefix
pattern2 = r'WARNING\s+\(([A-Z_]+-\d+)\):\s*(.+)'
# Example: "WARNING (LEFPARS-2001): No VERSION statement found, using the default value 5.8."

# Pattern 3: Timestamp prefix for line number tracking
pattern3 = r'^\[(\d{2}/\d{2})\s+(\d{2}:\d{2}:\d{2})\s+\d+s\]\s*(.+)'
# Example: "[01/09 09:23:00     21s] **WARN: (IMPLF-378):\tThe spacing for cell edge type..."

# Pattern 4: Multi-line warning continuation detection
pattern4 = r'^\[\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2}\s+\d+s\]\s+(?!\*\*WARN|WARNING|\*\*ERROR|ERROR|<CMD>)(.+)'
# Example: "[01/09 09:23:00     21s] If it's defined multiple times for the same pair of types, only the last one"
```

### Detection Logic

1. **Iterate through each .logv file** in the input file list
2. **Parse line-by-line** with state machine for multi-line message handling:
   - Extract timestamp prefix to identify log entry boundaries
   - Match against warning patterns (Pattern 1 or Pattern 2)
   - Extract warning code (e.g., "IMPLF-378", "LEFPARS-2001")
   - Extract initial warning message text
   - Track current line number for reporting
3. **Handle multi-line warnings**:
   - Continue reading subsequent lines without warning/error/command prefix
   - Append continuation lines to current warning message
   - Finalize warning when new pattern detected or file ends
4. **Aggregate warnings** across all files:
   - Store each warning with: code, full message, file path, line number
   - Group by warning code for statistics
5. **Compare against waiver list**:
   - Match warning codes against waive_items (e.g., "IMPLF-378")
   - Classify as waived or unwaived
6. **Report results**:
   - PASS if all warnings are in waiver list
   - FAIL if any unwaived warnings exist, printing complete warning details

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

**Rationale:** This checker validates that all warnings found in log files are in the approved waiver list. The pattern_items represent warning codes to check waiver status. Only warnings matching pattern_items are validated - other warnings are ignored. This is a status check (waived vs unwaived), not an existence check.

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
item_desc = "Confirm all Warning message in power analysis log files can be waived."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "All warnings found in waiver list"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All warnings matched waiver list"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "All warnings found in approved waiver list"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All warning codes matched and validated against waiver list"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Unwaived warnings found in power analysis logs"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Warning codes not satisfied by waiver list"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Warning not found in approved waiver list - requires review"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Warning code not satisfied by waiver list - requires approval"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Waived power analysis warnings"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Warning waived per approved waiver list"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding warning found in logs"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [warning_code]: [found_reason]"
  Example: "- IMPLF-378: Warning waived per approved waiver list: LEF spacing redefinition is expected"

ERROR01 (Violation/Fail items):
  Format: "- [warning_code] [full_message] (file: [filepath], line: [line_number]): [missing_reason]"
  Example: "- LEFPARS-2001 No VERSION statement found, using the default value 5.8 (file: `func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv`, line: 248): Warning code not satisfied by waiver list - requires approval"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-23:
  description: "Confirm all Warning message in power analysis log files can be waived."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_tt_0p75v_85c_typical_typical_setup_dynamic.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/noerror.logv"
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
Reason: All warnings found in approved waiver list

Log format (CheckList.rpt):
INFO01:
  - No unwaived warnings found

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: No unwaived warnings found. In line 0, N/A: All warnings found in approved waiver list
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Warning not found in approved waiver list - requires review

Log format (CheckList.rpt):
ERROR01:
  - LEFPARS-2001 No VERSION statement found, using the default value 5.8 (file: `func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv`, line: 248)

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: LEFPARS-2001. In line 248, `func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv`: No VERSION statement found, using the default value 5.8 - Warning not found in approved waiver list - requires review
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-23:
  description: "Confirm all Warning message in power analysis log files can be waived."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_tt_0p75v_85c_typical_typical_setup_dynamic.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/noerror.logv"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Power analysis warnings are informational only during early design phase"
      - "Note: IMPLF-378 warnings are expected due to LEF library merge process"
      - "Note: LEFPARS-2001 warnings are benign - tool uses default LEF version"
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
  - "Explanation: Power analysis warnings are informational only during early design phase"
  - "Note: IMPLF-378 warnings are expected due to LEF library merge process"
  - "Note: LEFPARS-2001 warnings are benign - tool uses default LEF version"
INFO02:
  - LEFPARS-2001 No VERSION statement found (file: `func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv`, line: 248)

Report format (item_id.rpt):
Info Occurrence: 4
1: Info: Explanation: Power analysis warnings are informational only during early design phase. [WAIVED_INFO]
2: Info: Note: IMPLF-378 warnings are expected due to LEF library merge process. [WAIVED_INFO]
3: Info: Note: LEFPARS-2001 warnings are benign - tool uses default LEF version. [WAIVED_INFO]
4: Info: LEFPARS-2001. In line 248, `func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv`: No VERSION statement found, using the default value 5.8 - Warning not found in approved waiver list - requires review [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-23:
  description: "Confirm all Warning message in power analysis log files can be waived."
  requirements:
    value: 2
    pattern_items:
      - "IMPLF-378"
      - "LEFPARS-2001"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_tt_0p75v_85c_typical_typical_setup_dynamic.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/noerror.logv"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- If description contains "version": Use VERSION IDENTIFIERS ONLY (e.g., "22.11-s119_1")
  ❌ DO NOT use paths: "innovus/221/22.11-s119_1"
  ❌ DO NOT use filenames: "libtech.lef"
- If description contains "filename"/"name": Use COMPLETE FILENAMES (e.g., "design.v")
- If description contains "status": Use STATUS VALUES (e.g., "Loaded", "Skipped")

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS/FAIL depends on check purpose:
- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)

**Sample Output (PASS):**
```
Status: PASS
Reason: All warning codes matched and validated against waiver list

Log format (CheckList.rpt):
INFO01:
  - IMPLF-378
  - LEFPARS-2001

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: IMPLF-378. In line 67, `func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv`: All warning codes matched and validated against waiver list
2: Info: LEFPARS-2001. In line 248, `func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv`: All warning codes matched and validated against waiver list
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-23:
  description: "Confirm all Warning message in power analysis log files can be waived."
  requirements:
    value: 2
    pattern_items:
      - "IMPLF-378"
      - "LEFPARS-2001"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_tt_0p75v_85c_typical_typical_setup_dynamic.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/noerror.logv"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Warning code validation is informational during development phase"
      - "Note: IMPLF-378 warnings are expected due to multi-library LEF merge"
      - "Note: LEFPARS-2001 warnings are benign - default LEF version is acceptable"
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
  - "Explanation: Warning code validation is informational during development phase"
  - "Note: IMPLF-378 warnings are expected due to multi-library LEF merge"
  - "Note: LEFPARS-2001 warnings are benign - default LEF version is acceptable"
INFO02:
  - TMPDIR-1001

Report format (item_id.rpt):
Info Occurrence: 4
1: Info: Explanation: Warning code validation is informational during development phase. [WAIVED_INFO]
2: Info: Note: IMPLF-378 warnings are expected due to multi-library LEF merge. [WAIVED_INFO]
3: Info: Note: LEFPARS-2001 warnings are benign - default LEF version is acceptable. [WAIVED_INFO]
4: Info: TMPDIR-1001. In line 15, `func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv`: The environment variable TMPDIR is not set - Warning code not satisfied by waiver list - requires approval [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-23:
  description: "Confirm all Warning message in power analysis log files can be waived."
  requirements:
    value: 2
    pattern_items:
      - "IMPLF-378"
      - "LEFPARS-2001"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_tt_0p75v_85c_typical_typical_setup_dynamic.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/noerror.logv"
  waivers:
    value: 1
    waive_items:
      - name: "IMPLF-378"
        reason: "LEF spacing redefinition is expected when merging multiple technology libraries"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Match found_items against waive_items
- Unwaived items → ERROR (need fix)
- Waived items → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all found_items (violations) are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived

Log format (CheckList.rpt):
INFO01:
  - IMPLF-378
  - LEFPARS-2001

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: IMPLF-378. In line 67, func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv: Warning waived per approved waiver list: LEF spacing redefinition is expected when merging multiple technology libraries [WAIVER]
2: Info: LEFPARS-2001. In line 248, func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv: Warning waived per approved waiver list: Missing VERSION statement is benign - tool uses default LEF version 5.8 [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-23:
  description: "Confirm all Warning message in power analysis log files can be waived."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup_static.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/func_func_tt_0p75v_85c_typical_typical_setup_dynamic.logv"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/noerror.logv"
  waivers:
    value: 2
    waive_items:
      - name: "IMPLF-378"
        reason: "LEF spacing redefinition is expected when merging multiple technology libraries"
      - name: "LEFPARS-2001"
        reason: "Missing VERSION statement is benign - tool uses default LEF version 5.8"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (keep exemption object names consistent)
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

Log format (CheckList.rpt):
INFO01:
  - IMPLF-378
  - LEFPARS-2001

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: IMPLF-378. In line 67, func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv: Warning waived per approved waiver list: LEF spacing redefinition is expected when merging multiple technology libraries [WAIVER]
2: Info: LEFPARS-2001. In line 248, func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static.logv: Warning waived per approved waiver list: Missing VERSION statement is benign - tool uses default LEF version 5.8 [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 11.0_POWER_EMIR_CHECK --checkers IMP-11-0-0-23 --force

# Run individual tests
python IMP-11-0-0-23.py
```

---

## Notes

**Common Warning Codes in Voltus Power Analysis:**
- **IMPLF-378**: LEF spacing redefinition - occurs when merging multiple technology libraries with overlapping definitions
- **LEFPARS-2001**: Missing VERSION statement in LEF file - tool uses default version 5.8
- **TMPDIR-1001**: Environment variable TMPDIR not set - informational only

**Multi-line Warning Handling:**
The checker properly assembles multi-line warning messages by:
1. Detecting timestamp prefix to identify message boundaries
2. Accumulating continuation lines without warning/error/command prefix
3. Finalizing complete message when next pattern detected

**File Coverage:**
The checker processes all .logv files in the input list, aggregating warnings across multiple power analysis runs (different corners, modes, etc.).

**Waiver Best Practices:**
- Use specific warning codes (e.g., "IMPLF-378") rather than generic descriptions
- Provide clear reason explaining why warning is acceptable
- Review waiver list periodically to remove obsolete entries
- Track unused waivers (WARN01) to identify outdated waiver entries