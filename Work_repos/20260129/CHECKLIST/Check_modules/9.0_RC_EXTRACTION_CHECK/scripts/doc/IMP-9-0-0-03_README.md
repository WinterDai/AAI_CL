# IMP-9-0-0-03: Confirm no ERROR message in the QRC log files.

## Overview

**Check ID:** IMP-9-0-0-03
**Description:** Confirm no ERROR message in the QRC log files.
**Category:** RC Extraction Validation
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrc*.log`

This checker validates the Cadence Quantus QRC parasitic extraction log files to ensure no ERROR messages were generated during the extraction process. The checker parses QRC log files for ERROR, WARNING, and INFO messages, then verifies that no ERROR-level issues occurred. A clean extraction (no ERRORs) is required for reliable parasitic data used in downstream timing and signal integrity analysis.

---

## Check Logic

### Input Parsing

Parse Cadence Quantus QRC extraction log files to identify ERROR, WARNING, and INFO messages. The log uses a structured format with message codes and descriptions.

**Key Patterns:**

```python
# Pattern 1: ERROR messages from QRC extraction
error_pattern = r'^ERROR\s*\(([A-Z]+-\d+)\)\s*:\s*(.+)$'
# Example: "ERROR (EXTGRMP-123) : Failed to read technology file"

# Pattern 2: WARNING messages from QRC extraction
warning_pattern = r'^WARNING\s*\(([A-Z]+-\d+)\)\s*:\s*(.+)$'
# Example: "WARNING (EXTGRMP-769) : DIVIDECHAR missing in /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_pm_svt_130b/lef/tcbn07_bwph300l8p64pd_pm_svt.lef file, therefore taking default value / for DIVIDECHAR."

# Pattern 3: INFO messages from QRC extraction
info_pattern = r'^INFO\s*\(([A-Z]+-\d+)\)\s*:\s*(.+)$'
# Example: "INFO (EXTGRMP-143) : Option enable_metal_fill_effects = "true""

# Pattern 4: Summary table entries with message counts
summary_pattern = r'^([A-Z]+-\d+)\s+(\d+)\s+(.+)$'
# Example: "EXTGRMP-327       7          The LEF parser reported the following warning :"
```

### Detection Logic

1. **Parse all QRC log files** matching the pattern `do_qrc*.log`
2. **Scan each line** for ERROR, WARNING, and INFO messages using regex patterns
3. **Extract ERROR details**: For each ERROR message, capture:
   - Error code (e.g., EXTGRMP-123)
   - Error message text
   - Line number in log file
4. **Count message types**: Track total counts of INFO, WARNING, and ERROR messages
5. **Group errors by error code**: Aggregate multiple occurrences of the same error code
6. **Determine PASS/FAIL**:
   - PASS: No ERROR messages found (ERROR count = 0)
   - FAIL: One or more ERROR messages found (ERROR count > 0)
7. **Build output**:
   - INFO01: Summary statistics (INFO/WARNING/ERROR counts) if no errors
   - ERROR01: List of unique ERROR codes with occurrence count and first occurrence details

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

**Rationale:** This checker validates the status of QRC extraction by checking for ERROR messages. The check scans all log content (not searching for specific pattern_items), and reports ERROR messages if found. This is a status validation of the extraction process - we're checking whether the extraction completed cleanly (no ERRORs) rather than verifying existence of specific items.

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
item_desc = "Confirm no ERROR message in the QRC log files."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "QRC extraction completed with no ERROR messages found"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "QRC extraction log validated - no ERROR messages detected"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "No ERROR messages found in QRC extraction logs"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "QRC extraction log validated successfully - no ERROR patterns matched"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "ERROR messages found in QRC extraction logs"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "QRC extraction validation failed - ERROR messages detected"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "ERROR messages found in QRC extraction logs - extraction failed"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "QRC extraction validation failed - ERROR patterns detected in logs"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "QRC extraction ERROR messages waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "QRC extraction ERROR waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused QRC ERROR waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding ERROR message found in QRC logs"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "QRC extraction summary: INFO={count}, WARNING={count}, ERROR={count}"
  Example: "QRC extraction summary: INFO=1247, WARNING=23, ERROR=0"

ERROR01 (Violation/Fail items):
  Format: "{error_code} (Occurrence: {total_number}): {error_message} [Line: {line_number}]"
  Example: "EXTGRMP-456 (Occurrence: 3): Failed to read technology file /process/tech.tf [Line: 342]"
  Note: Each unique error code is displayed only once with its total occurrence count and the line number of its first occurrence
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-9-0-0-03:
  description: "Confirm no ERROR message in the QRC log files."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrc*.log"
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
Reason: No ERROR messages found in QRC extraction logs
INFO01:
  - QRC extraction summary: INFO=1247, WARNING=23, ERROR=0
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: ERROR messages found in QRC extraction logs - extraction failed
ERROR01:
  - EXTGRMP-456 (Occurrence: 3): Failed to read technology file /process/tsmcN7/tech/qrc.tf [Line: 342]
  - EXTSNZ-789 (Occurrence: 1): Metal layer M5 not defined in technology file [Line: 1205]
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-9-0-0-03:
  description: "Confirm no ERROR message in the QRC log files."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrc*.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: QRC extraction errors are informational only for this early design phase"
      - "Note: ERROR messages are expected during initial technology file validation and do not block tapeout"
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
  - "Explanation: QRC extraction errors are informational only for this early design phase"
  - "Note: ERROR messages are expected during initial technology file validation and do not block tapeout"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - EXTGRMP-456 (Occurrence: 3): Failed to read technology file /process/tsmcN7/tech/qrc.tf [Line: 342] [WAIVED_AS_INFO]
  - EXTSNZ-789 (Occurrence: 1): Metal layer M5 not defined in technology file [Line: 1205] [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-9-0-0-03:
  description: "Confirm no ERROR message in the QRC log files."
  requirements:
    value: 2
    pattern_items:
      - "EXTGRMP-456"
      - "EXTSNZ-789"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrc*.log"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS/FAIL depends on check purpose:

- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)

**Sample Output (PASS):**

```
Status: PASS
Reason: QRC extraction log validated successfully - no ERROR patterns matched
INFO01:
  - QRC extraction summary: INFO=1247, WARNING=23, ERROR=0
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-9-0-0-03:
  description: "Confirm no ERROR message in the QRC log files."
  requirements:
    value: 0
    pattern_items:
      - "EXTGRMP-456"
      - "EXTSNZ-789"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrc*.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: QRC ERROR pattern check is informational only for debug builds"
      - "Note: Specific ERROR patterns are expected during technology migration and do not require immediate fixes"
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
  - "Explanation: QRC ERROR pattern check is informational only for debug builds"
  - "Note: Specific ERROR patterns are expected during technology migration and do not require immediate fixes"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - EXTGRMP-456 (Occurrence: 3): Failed to read technology file /process/tsmcN7/tech/qrc.tf [Line: 342] [WAIVED_AS_INFO]
  - EXTSNZ-789 (Occurrence: 1): Metal layer M5 not defined in technology file [Line: 1205] [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-9-0-0-03:
  description: "Confirm no ERROR message in the QRC log files."
  requirements:
    value: 2
    pattern_items:
      - "EXTGRMP-456"
      - "EXTSNZ-789"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrc*.log"
  waivers:
    value: 2
    waive_items:
      - name: "EXTGRMP-456"
        reason: "Waived - using alternative technology file per foundry update"
      - name: "EXTSNZ-789"
        reason: "Waived - M5 layer intentionally excluded for this IP block per design spec"
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
INFO01 (Waived):
  - EXTGRMP-456 (Occurrence: 3): Failed to read technology file /process/tsmcN7/tech/qrc.tf [Line: 342] [WAIVER]
  - EXTSNZ-789 (Occurrence: 1): Metal layer M5 not defined in technology file [Line: 1205] [WAIVER]
WARN01 (Unused Waivers):
  - (none - all waivers matched)
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-9-0-0-03:
  description: "Confirm no ERROR message in the QRC log files."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrc*.log"
  waivers:
    value: 2
    waive_items:
      - name: "EXTGRMP-456"
        reason: "Waived - using alternative technology file per foundry update"
      - name: "EXTSNZ-789"
        reason: "Waived - M5 layer intentionally excluded for this IP block per design spec"
```

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
  - EXTGRMP-456 (Occurrence: 3): Failed to read technology file /process/tsmcN7/tech/qrc.tf [Line: 342] [WAIVER]
  - EXTSNZ-789 (Occurrence: 1): Metal layer M5 not defined in technology file [Line: 1205] [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 9.0_RC_EXTRACTION_CHECK --checkers IMP-9-0-0-03 --force

# Run individual tests
python IMP-9-0-0-03.py
```

---

## Notes

- **QRC Message Format**: All messages follow the pattern `TYPE (CODE) : message` where TYPE is INFO/WARNING/ERROR and CODE is a tool-specific identifier (e.g., EXTGRMP-456)
- **Summary Section**: QRC logs include a "Warning message summary" section with aggregated counts - this can be used for validation but primary check focuses on ERROR messages
- **Line Numbers**: ERROR messages are reported with line numbers for easy log navigation and debugging
- **Error Deduplication**: Each unique error code is displayed only once with its total occurrence count to avoid cluttering the output with repeated messages
- **Metal Fill Effects**: Sample logs show INFO messages about metal fill effects being enabled - this is normal operation and not an error
- **LEF Parser Warnings**: Common warnings include DIVIDECHAR missing in LEF files - these are informational and do not indicate extraction failure
- **Technology File Dependencies**: ERROR messages often relate to technology file reading or layer definitions - these are critical and must be resolved for valid extraction
- **Multi-file Support**: Checker supports wildcard pattern `do_qrc*.log` to handle multiple QRC runs in the same directory
