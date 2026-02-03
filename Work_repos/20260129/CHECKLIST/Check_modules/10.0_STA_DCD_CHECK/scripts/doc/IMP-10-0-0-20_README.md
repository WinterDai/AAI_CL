# IMP-10-0-0-20: Confirm no ERROR message in the STA log files or the ERROR messages can be waived.

## Overview

**Check ID:** IMP-10-0-0-20  
**Description:** Confirm no ERROR message in the STA log files or the ERROR messages can be waived.  
**Category:** Static Timing Analysis (STA)  
**Input Files:** ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_1.log, ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_2.log

### Purpose

This checker validates that Cadence Tempus Static Timing Analysis (STA) runs completed without critical errors. It parses STA log files to detect ERROR messages, counts total errors/warnings, and determines PASS/FAIL status based on whether errors are present and waivable. This is a critical sign-off check ensuring timing analysis completed successfully without tool failures or data integrity issues.

### Functional Description

**What is being checked?**
The checker extracts and analyzes ERROR messages from Tempus STA log files by:
- Parsing inline ERROR messages with format `**ERROR: (CODE): message`
- Extracting error counts from the "Message Summary" section
- Identifying error codes, messages, file locations, and line numbers
- Cross-referencing detected errors against waiver lists
- Aggregating results across multiple log files

**Why is this check important for VLSI design?**
STA tool errors indicate fundamental problems that invalidate timing analysis results:
- **Data Integrity**: Errors in library loading (TECHLIB-*) or constraint parsing (TCLCMD-*) mean timing data is incomplete or incorrect
- **Sign-off Blocker**: Any unwaived ERROR prevents timing sign-off and tapeout
- **Root Cause Analysis**: Error codes and locations enable quick debugging of setup issues
- **Quality Gate**: Ensures STA environment (libraries, constraints, SPEF) is properly configured before analyzing timing results

---

## Check Logic

### Input Parsing

The checker parses Tempus log files using multiple patterns to capture errors from different sections (inline messages and summary tables).

**Key Patterns:**
```python
# Pattern 1: Inline ERROR messages with error codes
pattern_error_inline = r'\*\*ERROR:\s*\(([A-Z0-9-]+)\):\s*(.+?)(?:\(File\s+(.+?),\s+Line\s+(\d+)\))?$'
# Example: "**ERROR: (SPEF-123): Net 'clk_net' has invalid capacitance (File /path/to/file.spef, Line 456)"
# Captures: error_code, message_text, file_path (optional), line_number (optional)

# Pattern 2: WARNING messages (for context and filtering)
pattern_warn_inline = r'\*\*WARN:\s*\(([A-Z0-9-]+)\):\s*(.+?)(?:\(File\s+(.+?),\s+Line\s+(\d+)\))?$'
# Example: "**WARN: (TECHLIB-1320):	The user-defined attribute 'related_spice_node' is not present..."
# Captures: warning_code, message_text, file_path (optional), line_number (optional)

# Pattern 3: Summary table entries with counts
pattern_summary_entry = r'^(WARNING|ERROR)\s+([A-Z0-9-]+)\s+(\d+)\s+(.+)$'
# Example: "ERROR     TECHLIB-302       2032  No function defined for cell '%s'. The c..."
# Captures: severity, error_code, count, truncated_message

# Pattern 4: Final message summary line
pattern_message_summary = r'\*\*\*\s+Message Summary:\s+(\d+)\s+warning\(s\),\s+(\d+)\s+error\(s\)'
# Example: "*** Message Summary: 2344 warning(s), 0 error(s)"
# Captures: total_warnings, total_errors

# Pattern 5: Generic ERROR fallback (non-standard format)
pattern_error_generic = r'^ERROR[:\s]+(.+)$'
# Example: "ERROR: Timing analysis failed due to missing constraints"
# Captures: full_error_message
```

### Detection Logic

1. **Multi-file Aggregation**:
   - Iterate through all input log files (tempus_1.log, tempus_2.log, etc.)
   - Combine error counts and create unified error list with source file identification

2. **Line-by-line Parsing with State Tracking**:
   - **State 1 (INITIAL)**: Scan for inline ERROR/WARN messages and summary section header
   - **State 2 (IN_SUMMARY)**: Parse summary table rows when inside "Summary of all messages" section
   - **State 3 (COMPLETED)**: Extract final counts from "Message Summary" line

3. **Error Extraction**:
   - Apply `pattern_error_inline` to capture detailed ERROR messages with codes and locations
   - Apply `pattern_summary_entry` to extract ERROR rows from summary table
   - Apply `pattern_error_generic` as fallback for non-standard ERROR formats
   - Store: error_code, message_text, file_path, line_number, log_file_name, log_line_number

4. **Validation**:
   - Compare inline error count vs. summary table count to ensure completeness
   - If `pattern_message_summary` shows 0 errors → PASS (no errors detected)
   - If errors > 0 → check against waiver list

5. **Waiver Matching** (Type 3/4):
   - Match error codes or full error messages against `waive_items[].name`
   - Matched errors → INFO01 with `[WAIVER]` tag
   - Unmatched errors → ERROR01 (FAIL)
   - Unused waiver entries → WARN01

6. **Edge Cases**:
   - Empty log file → ERROR (STA did not run)
   - Missing "Message Summary" line → count errors manually from inline messages
   - Truncated log → report partial results with warning
   - Multi-line error messages → concatenate continuation lines

---

## Output Descriptions (CRITICAL - Code Generator Will Use These!)

This section defines the output strings used by `build_complete_output()` in the checker code.

**⚠️ CRITICAL RULE: These descriptions MUST be used IDENTICALLY across ALL Type 1/2/3/4!**
- Same checker = Same descriptions, regardless of which Type is detected at runtime
- Code generator should define these as CLASS CONSTANTS and reuse them in all _execute_typeN() methods

```python
# ⚠️ CRITICAL: These descriptions MUST be used IDENTICALLY across ALL Type 1/2/3/4!
# Define as class constants, then use self.FOUND_DESC, self.MISSING_DESC, etc.

# Item description for this checker
item_desc = "Confirm no ERROR message in the STA log files or the ERROR messages can be waived."

# PASS case - clean items (used in ALL Types)
found_desc = "STA log files with no errors"
found_reason = "All STA log files completed without errors"

# FAIL case - violations (used in ALL Types)
missing_desc = "ERROR messages detected in STA log files"
missing_reason = "STA log contains unwaived ERROR messages"

# WAIVED case (Type 3/4) - waived items
waived_desc = "Waived ERROR messages in STA log files"
waived_base_reason = "ERROR message waived per design approval"

# UNUSED waivers (Type 3/4) - unused waiver entries
unused_desc = "Unused waiver entries for STA errors"
unused_waiver_reason = "Waiver entry did not match any detected ERROR"
```

**Code Generator Pattern:**
```python
class CheckerName(BaseChecker, OutputBuilderMixin, WaiverHandlerMixin):
    # Define ONCE at class level - MUST be same across all Types!
    FOUND_DESC = "STA log files with no errors"
    MISSING_DESC = "ERROR messages detected in STA log files"
    WAIVED_DESC = "Waived ERROR messages in STA log files"
    FOUND_REASON = "All STA log files completed without errors"
    MISSING_REASON = "STA log contains unwaived ERROR messages"
    WAIVED_BASE_REASON = "ERROR message waived per design approval"
    
    def _execute_type1(self):
        return self.build_complete_output(
            found_desc=self.FOUND_DESC,      # Use constant
            missing_desc=self.MISSING_DESC,  # Use constant
            ...
        )
    
    def _execute_type4(self):
        return self.build_complete_output(
            found_desc=self.FOUND_DESC,      # SAME as Type 1
            missing_desc=self.MISSING_DESC,  # SAME as Type 1
            waived_desc=self.WAIVED_DESC,    # Additional for Type 4
            ...
        )
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "[log_filename]: Message Summary: [X] warning(s), 0 error(s)"
  Example: "tempus_1.log: Message Summary: 2344 warning(s), 0 error(s)"

ERROR01 (Violation/Fail items):
  Format: "[log_filename] - [ERROR_CODE](Occurence: 出现次数): [message_text] [Log Line: [log_line_number]]"
  Note: 每个ERROR_CODE只需要打出来一个
  
  Example: "tempus_1.log - TECHLIB-302(Occurence: 2032): No function defined for cell 'BUFX2' [Log Line: 567]"
  Example: "tempus_2.log - IMPDBTCL-321(Occurence: 1): Invalid timing constraint detected [Log Line: 89]"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-10-0-0-20:
  description: "Confirm no ERROR message in the STA log files or the ERROR messages can be waived."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_1.log
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_2.log
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs a global boolean check across all STA log files without waiver support:
- Parse all log files and aggregate error counts
- If total errors = 0 → **PASS** (all logs clean)
- If total errors > 0 → **FAIL** (any error blocks sign-off)
- No waiver matching performed

**Sample Output (PASS):**
```
Status: PASS
Reason: All STA log files completed without errors
INFO01:Waived ERROR messages in STA log files
  - tempus_1.log: Message Summary: 2344 warning(s), 0 error(s)
  - tempus_2.log: Message Summary: 2309 warning(s), 0 error(s)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: STA log contains unwaived ERROR messages
ERROR01:
  - tempus_1.log - TECHLIB-302(Occurence: 2032): No function defined for cell 'INVX1'. The cell will be treated as a black box. [Log Line: 234]
  - tempus_1.log - SPEF-456(Occurence: 1): Invalid net capacitance value for net 'clk_div/net_123' [Log Line: 891]
  - tempus_2.log - TCLCMD-789(Occurence: 3): Constraint conflict detected for clock 'sys_clk' [Log Line: 156]
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-10-0-0-20:
  description: "Confirm no ERROR message in the STA log files or the ERROR messages can be waived."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_1.log
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_2.log
  waivers:
    value: 0        # Forces PASS: all violations → INFO
    waive_items:    # REQUIRED: Must provide explanation
      - "Pre-implementation phase - library setup errors expected during initial bring-up"
```

**Special Behavior (waivers.value=0):**
⚠️ **CRITICAL**: When `waivers.value=0`, `waive_items` MUST have content:
- `waive_items` strings → INFO with `[WAIVED_INFO]` suffix (shows reason for forced PASS)
- ALL detected ERROR messages → INFO with `[WAIVED_AS_INFO]` suffix (forced conversion)
- Result: **Always PASS** (informational check mode)

**Sample Output:**
```
Status: PASS (forced)
Reason: 
INFO01:
  - Pre-implementation phase - library setup errors expected during initial bring-up [WAIVED_INFO]
  - tempus_1.log - TECHLIB-302(Occurence: 2032): No function defined for cell 'INVX1'. The cell will be treated as a black box. [Log Line: 234] [WAIVED_AS_INFO]
  - tempus_2.log - TCLCMD-789(Occurence: 3): Constraint conflict detected for clock 'sys_clk' [Log Line: 156] [WAIVED_AS_INFO]
```

---

## Type 2: Value comparison

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-10-0-0-20:
  description: "Confirm no ERROR message in the STA log files or the ERROR messages can be waived."
  requirements:
    value: 2  # MUST equal the number of pattern_items (2 log files below)
    pattern_items:
      - "tempus_1.log: Message Summary: 2344 warning(s), 0 error(s)"
      - "tempus_2.log: Message Summary: 2309 warning(s), 0 error(s)"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_1.log
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_2.log
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 validates that the number of clean log files (0 errors) matches the expected count:
- Parse all log files and identify those with 0 errors
- Count clean log files
- If count == requirements.value → **PASS**
- If count < requirements.value → **FAIL** (some logs have errors)
- `pattern_items` lists expected clean log summaries for reference

**Sample Output (PASS):**
```
Status: PASS
Reason: All STA log files completed without errors
INFO01:
  - tempus_1.log: Message Summary: 2344 warning(s), 0 error(s)
  - tempus_2.log: Message Summary: 2309 warning(s), 0 error(s)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-10-0-0-20:
  description: "Confirm no ERROR message in the STA log files or the ERROR messages can be waived."
  requirements:
    value: 2
    pattern_items:
      - "tempus_1.log"
      - "tempus_2.log"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_1.log
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_2.log
  waivers:
    value: 0        # Forces PASS: all violations → INFO
    waive_items:    # REQUIRED: Must provide explanation
      - "Debug mode - STA errors are informational only during development"
```

**Special Behavior (waivers.value=0):**
⚠️ **CRITICAL**: `waive_items` MUST have content:
- `waive_items` strings → INFO with `[WAIVED_INFO]` suffix
- ALL violations/missing items → INFO with `[WAIVED_AS_INFO]` suffix
- Result: **Always PASS**

---

## Type 3: Value Check with Waivers

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-10-0-0-20:
  description: "Confirm no ERROR message in the STA log files or the ERROR messages can be waived."
  requirements:
    value: 2  # MUST equal the number of pattern_items (2 log files below)
    pattern_items:
      - "tempus_1.log"
      - "tempus_2.log"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_1.log
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_2.log
  waivers:
    value: 2  # Number of waiver entries (separate from requirements.value)
    waive_items:
      - name: "tempus_1.log - TECHLIB-302"
        reason: "Black box modeling approved for analog macro cells per design spec v2.3"
      - name: "tempus_2.log - IMPDBTCL-321"
        reason: "Legacy attribute usage - migration planned for next release"
```

**Check Behavior:**
Type 3 validates clean log count with waiver support:
- Parse all log files and extract ERROR messages
- Match detected errors against `waive_items[].name` (exact match or substring match on error code + message)
- Matched errors → INFO01 with `[WAIVER]` tag (do not count as violations)
- Count remaining clean logs (0 errors after waiving)
- If clean_count == requirements.value → **PASS**
- If clean_count < requirements.value → **FAIL** (unwaived errors remain)
- Unused waiver entries → WARN01

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - tempus_1.log - TECHLIB-302(Occurence: 2032): No function defined for cell 'INVX1'. The cell will be treated as a black box. [Log Line: 234]:Black box modeling approved for analog macro cells per design spec v2.3[WAIVER]
  - tempus_2.log - IMPDBTCL-321(Occurence: 1): The attribute 'si_delay_enable' still works but will be deprecated [Log Line: 89]:Legacy attribute usage - migration planned for next release[WAIVER]
WARN01 (Unused Waivers):
  - (none)
```

---

## Type 4: Boolean Check with Waivers

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-10-0-0-20:
  description: "Confirm no ERROR message in the STA log files or the ERROR messages can be waived."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_1.log
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_2.log
  waivers:
    value: 1
    waive_items:
      - name: "tempus_1.log - TECHLIB-302"
        reason: "Black box modeling approved for analog macro cells per design spec v2.3"
```

**Check Behavior:**
Type 4 performs global boolean check with waiver support:
- Parse all log files and extract all ERROR messages
- Match detected errors against `waive_items[].name`
- Matched errors → INFO01 with `[WAIVER]` tag
- Unmatched errors → ERROR01 (FAIL)
- If all errors waived → **PASS**
- If any unwaived errors remain → **FAIL**

**Sample Output:**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - tempus_1.log - TECHLIB-302(Occurence: 2032): No function defined for cell 'INVX1'. The cell will be treated as a black box. [Log Line: 234]: Black box modeling approved for analog macro cells per design spec v2.3[WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 10.0_STA_DCD_CHECK --checkers IMP-10-0-0-20 --force

# Run individual tests
python IMP-10-0-0-20.py
```

---

## Notes

**Common Waivable Error Codes:**
- `TECHLIB-302`: Missing function definition for cells (black box modeling)
- `TECHLIB-1320`: Missing user-defined attributes (non-critical for basic STA)
- `IMPDBTCL-321`: Deprecated attribute warnings (legacy compatibility)
- `TCLCMD-1681`: Auto-recovery messages (tool handled internally)

**Non-Waivable Critical Errors:**
- `SPEF-*`: Parasitic data corruption (invalidates timing)
- `TCLCMD-*` (constraint conflicts): Timing constraints are inconsistent
- Library loading failures: Missing or corrupted timing libraries

**Limitations:**
- Multi-line error messages must be on consecutive lines (no blank lines in between)
- Error code extraction assumes standard Cadence format `**ERROR: (CODE):`
- Waiver matching uses substring matching - ensure waiver names are specific enough to avoid false matches

**Known Issues:**
- Truncated log files (incomplete runs) may show 0 errors incorrectly - checker warns if "Ending" message is missing
- Some errors may appear only in summary table, not as inline messages - checker cross-validates both sources