# IMP-9-0-0-07: Confirm all Warning message in QRC log files can be waived.

## Overview

**Check ID:** IMP-9-0-0-07  
**Description:** Confirm all Warning message in QRC log files can be waived.  
**Category:** RC Extraction Quality Check  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrc*.log`

This checker validates that all WARNING messages in Cadence Quantus QRC parasitic extraction log files are acceptable and can be waived. It parses QRC log files to extract all WARNING messages (with codes like EXTGRMP-XXX, EXTSNZ-XXX, LEFPARS-XXX), aggregates them by message code, and verifies that all warnings are either expected or have valid waiver justifications. The checker provides both summary statistics (warning counts by code) and detailed individual warning messages for review.

---

## Check Logic

### Input Parsing

The checker parses Cadence Quantus QRC extraction log files (`do_qrc*.log`) to extract WARNING messages and their summary statistics.

**Key Patterns:**

```python
# Pattern 1: Individual WARNING messages with message codes
warning_pattern = r'WARNING \((EXTGRMP-\d+|EXTSNZ-\d+|LEFPARS-\d+)\)\s*:\s*(.+?)(?=\n(?:WARNING|INFO|\n|$))'
# Example: "WARNING (EXTGRMP-769) : DIVIDECHAR missing in /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_pm_svt_130b/lef/tcbn07_bwph300l8p64pd_pm_svt.lef file, therefore taking default value / for DIVIDECHAR."

# Pattern 2: Warning summary table entries
summary_pattern = r'^(EXTGRMP-\d+|EXTSNZ-\d+|LEFPARS-\d+)\s+(\d+)\s+(.+?)(?=\n(?:-{10,}|[A-Z]|$))'
# Example: "EXTGRMP-327       7          The LEF parser reported the following warning :"

# Pattern 3: File paths mentioned in warnings
filepath_pattern = r'(/[\w/.-]+\.(?:lef|gds|tlef|def))'
# Example: "/process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_pm_svt_130b/lef/tcbn07_bwph300l8p64pd_pm_svt.lef"

# Pattern 4: Warning summary section header
summary_header_pattern = r'Message Code\(ID\)\s+Count\s+Message\s*\n=+\|=+\|=+'
# Example: "Message Code(ID)   Count     Message"
```

### Detection Logic

1. **Parse all QRC log files** matching pattern `do_qrc*.log`
2. **Extract individual WARNING messages**:
   - Capture warning code (EXTGRMP-XXX, EXTSNZ-XXX, LEFPARS-XXX)
   - Capture full warning message text (may span multiple lines)
   - Extract any file paths mentioned in the warning
3. **Parse warning summary table** (if present):
   - Extract message code, count, and brief description
   - Validate that summary counts match individual warning occurrences
4. **Aggregate warnings across all log files**:
   - Group warnings by message code
   - Count occurrences of each warning type
   - Build detailed list with format: `[WARNING_CODE](Occurrence: [total_number]): message_text (file: filepath if available)` - each warning code only displayed once
5. **Generate output**:
   - **INFO01**: Summary statistics showing warning counts by message code
   - **ERROR01**: Individual warning details for waiver verification (one entry per unique warning code)
6. **Determine PASS/FAIL**:
   - **FAIL**: Any warnings exist (unwaived)
   - **PASS**: 
     - **When waivers.value=0**: All warnings automatically waived (one-click waive mode)
     - **When waivers.value>0**: All warnings matched by waive_items using [warning_code] pattern matching

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

**Rationale:** This checker validates the status of WARNING messages found in QRC logs. The pattern_items (if used in Type 2/3) represent specific warning codes or messages to check. Only warnings matching the pattern_items are output and validated. Warnings not in pattern_items are ignored. PASS means all matched warnings have acceptable status (waived or expected), FAIL means some matched warnings require attention.

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
item_desc = "Confirm all Warning message in QRC log files can be waived."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "QRC extraction completed with no WARNING messages found"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "QRC extraction log validated - no WARNING messages detected"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "No WARNING messages found in QRC extraction logs"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "QRC extraction log validated successfully - no WARNING patterns matched"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "WARNING messages found in QRC extraction logs"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "QRC extraction validation failed - WARNING messages detected"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "WARNING messages found in QRC extraction logs - require waiver"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "QRC extraction validation failed - WARNING patterns detected in logs"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "QRC extraction WARNING messages waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "QRC extraction WARNING waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused QRC WARNING waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding WARNING message found in QRC logs"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items - Warning Summary Statistics):
  Format: "Message Code: [CODE] | Count: [N] | [Brief Description]"
  Example: "Message Code: EXTGRMP-769 | Count: 12 | DIVIDECHAR missing in LEF file"

ERROR01 (Violation/Fail items - Individual Warning Details):
  Format: "[WARNING_CODE](Occurrence: [total_number]): [message_text] (file: [filepath])"
  Example: "EXTGRMP-769(Occurrence: 12): DIVIDECHAR missing in /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_pm_svt_130b/lef/tcbn07_bwph300l8p64pd_pm_svt.lef file, therefore taking default value / for DIVIDECHAR. (file: /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_pm_svt_130b/lef/tcbn07_bwph300l8p64pd_pm_svt.lef)"
  
  Note: Each warning code is displayed only once with its total occurrence count
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-9-0-0-07:
  description: "Confirm all Warning message in QRC log files can be waived."
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
PASS if no warnings found. FAIL if any warnings exist.

**Sample Output (PASS - No warnings):**
```
Status: PASS
Reason: No WARNING messages found in QRC extraction logs
INFO01:
  - QRC extraction summary: 0 WARNING messages found
```

**Sample Output (FAIL - Warnings exist):**
```
Status: FAIL
Reason: WARNING messages found in QRC extraction logs - require waiver
ERROR01:
  - [EXTGRMP-769](Occurrence: 12): DIVIDECHAR missing in /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_pm_svt_130b/lef/tcbn07_bwph300l8p64pd_pm_svt.lef file, therefore taking default value / for DIVIDECHAR.
  - [EXTGRMP-728](Occurrence: 9): Different version number exists for tech lef with version 5.8 and macro lef with version 5.6
```

### Type 1 Variant: waivers.value=0 (One-Click Waive Mode)

**Configuration:**
```yaml
IMP-9-0-0-07:
  description: "Confirm all Warning message in QRC log files can be waived."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrc*.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers one-click waive mode (auto-waive all warnings)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: QRC warnings are informational only for this design phase"
      - "Note: LEF version mismatches are expected when using mixed IP libraries from different vendors"
      - "Note: DIVIDECHAR warnings do not impact extraction accuracy for this technology node"
```

**CRITICAL Behavior (waivers.value=0):**
- NOTE: Type 1 one-click waive mode - ALL warnings automatically waived
- IMPORTANT: waive_items uses PLAIN STRINGS (NOT name/reason dict like Type 3/4!)
- waive_items serves as COMMENT ONLY (no matching/filtering logic)
- waive_items content printed as INFO with [WAIVED_INFO] tag
- ALL violations force converted: FAIL→PASS, displayed as INFO with [WAIVED_AS_INFO] tag
- Check ALWAYS returns PASS (violations shown as INFO for tracking)
- Used when: All warnings acceptable, one-click waive without individual matching

**Sample Output (PASS with auto-waived warnings):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All violations waived as informational
INFO01 ([WAIVED_INFO] - waive_items as comment):
  - "Explanation: QRC warnings are informational only for this design phase"
  - "Note: LEF version mismatches are expected when using mixed IP libraries from different vendors"
  - "Note: DIVIDECHAR warnings do not impact extraction accuracy for this technology node"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - EXTGRMP-769(Occurrence: 12): DIVIDECHAR missing in /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_pm_svt_130b/lef/tcbn07_bwph300l8p64pd_pm_svt.lef file [WAIVED_AS_INFO]
  - EXTGRMP-728(Occurrence: 9): Different version number exists for tech lef with version 5.8 and macro lef with version 5.6 [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-9-0-0-07:
  description: "Confirm all Warning message in QRC log files can be waived."
  requirements:
    value: 2
    pattern_items:
      - "EXTGRMP-769"
      - "EXTGRMP-728"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrc*.log"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS if no warnings found. FAIL if any warnings exist.

**Sample Output (PASS - No warnings):**
```
Status: PASS
Reason: QRC extraction log validated successfully - no WARNING patterns matched
INFO01:
  - QRC extraction summary: 0 WARNING messages found
```

**Sample Output (FAIL - Warnings exist):**
```
Status: FAIL
Reason: QRC extraction validation failed - WARNING patterns detected in logs
ERROR01:
  - [EXTGRMP-769](Occurrence: 12): DIVIDECHAR missing in /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_pm_svt_130b/lef/tcbn07_bwph300l8p64pd_pm_svt.lef file, therefore taking default value / for DIVIDECHAR.
  - [EXTGRMP-728](Occurrence: 9): Different version number exists for tech lef with version 5.8 and macro lef with version 5.6
```
```

### Type 2 Variant: waivers.value=0 (One-Click Waive Mode)

**Configuration:**
```yaml
IMP-9-0-0-07:
  description: "Confirm all Warning message in QRC log files can be waived."
  requirements:
    value: 2
    pattern_items:
      - "EXTGRMP-769"
      - "EXTGRMP-728"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrc*.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers one-click waive mode (auto-waive all matched warnings)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: These specific warning codes are informational only for this extraction run"
      - "Note: EXTGRMP-769 (DIVIDECHAR) warnings are expected with legacy LEF files and do not affect results"
      - "Note: EXTGRMP-728 (version mismatch) warnings are acceptable when using mixed vendor libraries"
```

**CRITICAL Behavior (waivers.value=0):**
- NOTE: Type 2 one-click waive mode - ALL matched warnings automatically waived
- IMPORTANT: waive_items uses PLAIN STRINGS (NOT name/reason dict like Type 3/4!)
- waive_items serves as COMMENT ONLY (no matching/filtering logic)
- waive_items content printed as INFO with [WAIVED_INFO] tag
- ALL errors/mismatches force converted: ERROR→PASS, displayed as INFO with [WAIVED_AS_INFO] tag
- Check ALWAYS returns PASS (errors shown as INFO for tracking)
- Used when: All matched pattern warnings acceptable, one-click waive without individual matching

**Sample Output (PASS with auto-waived warnings):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All mismatches waived as informational
INFO01 ([WAIVED_INFO] - waive_items as comment):
  - "Explanation: These specific warning codes are informational only for this extraction run"
  - "Note: EXTGRMP-769 (DIVIDECHAR) warnings are expected with legacy LEF files and do not affect results"
  - "Note: EXTGRMP-728 (version mismatch) warnings are acceptable when using mixed vendor libraries"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - EXTGRMP-769(Occurrence: 12): DIVIDECHAR missing in /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_pm_svt_130b/lef/tcbn07_bwph300l8p64pd_pm_svt.lef file [WAIVED_AS_INFO]
  - EXTGRMP-728(Occurrence: 9): Different version number exists for tech lef with version 5.8 and macro lef with version 5.6 [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-9-0-0-07:
  description: "Confirm all Warning message in QRC log files can be waived."
  requirements:
    value: 2
    pattern_items:
      - "EXTGRMP-769"
      - "EXTGRMP-728"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrc*.log"
  waivers:
    value: 2
    waive_items:
      - name: "EXTGRMP-769"
        reason: "Waived - legacy LEF file format, default DIVIDECHAR value is correct for this library"
      - name: "EXTGRMP-728"
        reason: "Waived - mixed LEF versions approved by foundry, no impact on extraction accuracy"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support using [warning_code] pattern matching.
FAIL if any pattern_items warnings exist. PASS when all matched warnings are waived:
- Match found warnings against waive_items using [warning_code] (e.g., "EXTGRMP-769")
- Unwaived warnings → ERROR (need waiver)
- Waived warnings → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS only if all found warnings are waived.

**Sample Output (PASS - All warnings waived):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - EXTGRMP-769(Occurrence: 12): DIVIDECHAR missing in /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_pm_svt_130b/lef/tcbn07_bwph300l8p64pd_pm_svt.lef file, therefore taking default value / for DIVIDECHAR. [WAIVER]
  - EXTGRMP-728(Occurrence: 9): Different version number exists for tech lef with version 5.8 and macro lef with version 5.6 [WAIVER]
WARN01 (Unused Waivers):
  - (none)
```

**Sample Output (FAIL - Unwaived warnings exist):**
```
Status: FAIL
Reason: Warning patterns not satisfied - warnings detected and require waiver approval
ERROR01 (Unwaived):
  - EXTGRMP-769(Occurrence: 12): DIVIDECHAR missing in /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_pm_svt_130b/lef/tcbn07_bwph300l8p64pd_pm_svt.lef file, therefore taking default value / for DIVIDECHAR.
INFO01 (Waived):
  - EXTGRMP-728(Occurrence: 9): Different version number exists for tech lef with version 5.8 and macro lef with version 5.6 [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-9-0-0-07:
  description: "Confirm all Warning message in QRC log files can be waived."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrc*.log"
  waivers:
    value: 2
    waive_items:
      - name: "EXTGRMP-769"
        reason: "Waived - legacy LEF file format, default DIVIDECHAR value is correct for this library"
      - name: "EXTGRMP-728"
        reason: "Waived - mixed LEF versions approved by foundry, no impact on extraction accuracy"
```

**Check Behavior:**
Type 4 = Type 1 + waiver support using [warning_code] pattern matching.
FAIL if any warnings exist. PASS when all warnings are waived:
- Match violations against waive_items using [warning_code] (e.g., "EXTGRMP-769")
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS only if all violations are waived.

**Sample Output (PASS - All warnings waived):**
```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - EXTGRMP-769(Occurrence: 12): DIVIDECHAR missing in /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_pm_svt_130b/lef/tcbn07_bwph300l8p64pd_pm_svt.lef file, therefore taking default value / for DIVIDECHAR. [WAIVER]
  - EXTGRMP-728(Occurrence: 9): Different version number exists for tech lef with version 5.8 and macro lef with version 5.6 [WAIVER]
```

**Sample Output (FAIL - Unwaived warnings exist):**
```
Status: FAIL
Reason: QRC extraction warnings detected in log files - FAIL until waived
ERROR01 (Unwaived):
  - EXTGRMP-769(Occurrence: 12): DIVIDECHAR missing in /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_pm_svt_130b/lef/tcbn07_bwph300l8p64pd_pm_svt.lef file, therefore taking default value / for DIVIDECHAR.
INFO01 (Waived):
  - EXTGRMP-728(Occurrence: 9): Different version number exists for tech lef with version 5.8 and macro lef with version 5.6 [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 9.0_RC_EXTRACTION_CHECK --checkers IMP-9-0-0-07 --force

# Run individual tests
python IMP-9-0-0-07.py
```

---

## Notes

- **Multi-line Warning Handling**: QRC warnings may span multiple lines. The parser uses lookahead to capture complete warning messages until the next WARNING/INFO marker or blank line.
- **Warning Summary Validation**: The checker cross-validates individual warning counts against the summary table (if present) to ensure completeness.
- **File Path Extraction**: File paths mentioned in warnings are extracted and included in ERROR01 output for easier debugging.
- **Aggregation Across Logs**: When multiple `do_qrc*.log` files exist, warnings are aggregated and deduplicated by message code and content.
- **One Warning Code Per Output**: Each unique warning code is displayed only once in ERROR01 output with its total occurrence count in the format `[WARNING_CODE](Occurrence: [total_number])`.
- **Known Warning Codes**: Common codes include:
  - `EXTGRMP-769`: DIVIDECHAR missing in LEF files
  - `EXTGRMP-728`: LEF version mismatches between tech and macro LEF files
  - `EXTGRMP-327`: LEF parser warnings
  - `EXTGRMP-574`: Unrouted nets detected
  - `EXTSNZ-XXX`: Extraction engine specific warnings
  - `LEFPARS-XXX`: LEF parser specific warnings
- **Waiver Matching Logic**:
  - **waivers.value=0**: One-click waive mode - ALL warnings automatically waived without individual matching
  - **waivers.value>0**: Pattern matching mode - waive_items must contain [warning_code] (e.g., "EXTGRMP-769") to match and waive specific warnings
  - Matching uses warning code only (not full message text) for flexibility
  - Each waive_item can waive all occurrences of that warning code
- **Waiver Best Practices**: 
  - Use warning code (e.g., "EXTGRMP-769") in waiver name for pattern matching
  - Document foundry approval or design team decisions in waiver reasons
  - Review unused waivers to identify outdated waiver entries
  - Use waivers.value=0 for one-click waive when all warnings are acceptable
  - Use waivers.value>0 with specific warning codes for selective waiving