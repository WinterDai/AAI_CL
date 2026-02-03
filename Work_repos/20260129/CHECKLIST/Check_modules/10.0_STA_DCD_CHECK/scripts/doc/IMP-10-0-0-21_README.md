# IMP-10-0-0-21: Confirm all Warning message in the STA log files can be waived.

## Overview

**Check ID:** IMP-10-0-0-21
**Description:** Confirm all Warning message in the STA log files can be waived.
**Category:** Static Timing Analysis (STA) Log Validation
**Input Files:** ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_1.log, ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_2.log

### Purpose

This checker validates that all warning messages generated during Cadence Tempus Static Timing Analysis runs are documented and can be waived. It ensures that no unexpected or critical warnings are present in the STA logs that could indicate design quality issues or tool setup problems requiring resolution before sign-off.

### Functional Description

**What is being checked?**
The checker parses Tempus STA log files to extract all warning messages, categorizes them by warning ID and severity, and verifies that each warning type is either acceptable for the design phase or has been explicitly waived with justification. It aggregates warning counts across multiple log files and provides both summary statistics and detailed warning listings for waiver review.

**Why is this check important for VLSI design?**
STA warnings can indicate library issues, constraint problems, or tool configuration errors that may affect timing analysis accuracy. Unreviewed warnings could mask critical timing issues or lead to incorrect sign-off decisions. This check ensures all warnings are consciously reviewed and documented, maintaining design quality and audit traceability for tape-out readiness.

---

## Check Logic

### Input Parsing

The checker parses Tempus log files using a state machine approach to extract warning information from both inline messages and summary tables.

**Key Patterns:**

```python
# Pattern 1: Inline warning messages with file location
pattern_inline_warning = r'^\*\*WARN:\s*\(([A-Z0-9-]+)\):\s*(.+?)(?:\s*\(File\s+(.+?),\s*Line\s+(\d+)\))?$'
# Example: "**WARN: (TECHLIB-1320):	The user-defined attribute 'related_spice_node' is not present in any of the 'ccsn_first_stage' group. This attribute is required for Tempus if SPICE correlation of ROP glitch needs to be performed. The missing attribute does not affect SI delay or glitch analysis. (File /process/intl3/data/stdcell/p765/INTL/lib765_g1i_210h_50pp_seq_hvt_pdk090-r3v0p0-fv/lib/lib765_g1i_210h_50pp_seq_hvt_rcss_0p675v_125c_pcss_cmax_ccslnt.lib.gz, Line 20)"

# Pattern 2: Summary table warning entries
pattern_summary_warning = r'^(WARNING|ERROR)\s+(\S+)\s+(\d+)\s+(.+?)\s*$'
# Example: "WARNING   TECHLIB-302       2032  No function defined for cell '%s'. The c..."

# Pattern 3: Overall message summary totals
pattern_message_summary = r'\*\*\* Message Summary:\s*(\d+)\s+warning\(s\),\s*(\d+)\s+error\(s\)'
# Example: "*** Message Summary: 2309 warning(s), 0 error(s)"

# Pattern 4: Summary section header (state machine trigger)
pattern_summary_header = r'^\*\*\* Summary of all messages that are not suppressed in this session:'
# Example: "*** Summary of all messages that are not suppressed in this session:"

# Pattern 5: Execution statistics
pattern_execution_stats = r'--- Ending "(.+?)"\s+\(totcpu=([^,]+),\s+real=([^,]+),\s+mem=([^)]+)\)'
# Example: "--- Ending "Tempus Timing Solution" (totcpu=0:11:48, real=0:12:40, mem=6206.2M) ---"
```

### Detection Logic

1. **Initialize aggregation structures**: Create dictionaries to track warnings by ID across all log files
2. **Parse each log file sequentially**:
   - Use state machine with states: SEARCHING → IN_SUMMARY → COMPLETE
   - Extract inline warnings during SEARCHING state
   - Enter IN_SUMMARY state when summary header is detected
   - Parse summary table entries for warning counts by ID
   - Extract total counts from message summary line
   - Capture execution statistics for context
3. **Aggregate results across files**:
   - Combine warning counts by message ID
   - Track which files contributed each warning type
   - Calculate total warnings and errors across all logs
4. **Generate output**:
   - INFO01: Summary statistics (total warnings, errors, execution time)
   - ERROR01: Individual warning types with ID, count, and description
5. **Determine pass/fail**:
   - Type 1/2: FAIL if any warnings exist (unless waived)
   - Type 3/4: PASS if all warnings are covered by waiver entries

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
item_desc = "Confirm all Warning message in the STA log files can be waived."

# PASS case - clean items (used in ALL Types)
found_desc = "STA log files with no warnings"
found_reason = "All STA log files are clean with no warnings"

# FAIL case - violations (used in ALL Types)
missing_desc = "STA warnings requiring review"
missing_reason = "STA warnings detected that require waiver review"

# WAIVED case (Type 3/4) - waived items
waived_desc = "Waived STA warnings"
waived_base_reason = "STA warning waived per design review"

# UNUSED waivers (Type 3/4) - unused waiver entries
unused_desc = "Unused STA warning waiver entries"
unused_waiver_reason = "Waiver entry does not match any detected warnings"
```

**Code Generator Pattern:**

```python
class CheckerName(BaseChecker, OutputBuilderMixin, WaiverHandlerMixin):
    # Define ONCE at class level - MUST be same across all Types!
    FOUND_DESC = "STA log files with no warnings"
    MISSING_DESC = "STA warnings requiring review"
    WAIVED_DESC = "Waived STA warnings"
    FOUND_REASON = "All STA log files are clean with no warnings"
    MISSING_REASON = "STA warnings detected that require waiver review"
    WAIVED_BASE_REASON = "STA warning waived per design review"
  
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
  Format: "Log file: [filename] - Total: {warning_count} warnings, {error_count} errors"
  Example: "tempus_1.log - Total: 0 warnings, 0 errors"

ERROR01 (Violation/Fail items):
  Format: "[WARNING_ID] (Count: {count}): {summary_text}"
  Example: "TECHLIB-302 (Count: 2032): No function defined for cell '%s'. The c..."
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-10-0-0-21:
  description: "Confirm all Warning message in the STA log files can be waived."
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
Type 1 performs a global boolean check across all STA log files. It aggregates all warnings from all input files and reports PASS only if zero warnings are detected. Any warnings result in FAIL with detailed ERROR01 listing of each warning type, count, and description. This is the strictest mode requiring completely clean STA runs.

**Sample Output (PASS):**

```
Status: PASS
Reason: All STA log files are clean with no warnings
INFO01:
  - tempus_1.log - Total: 0 warnings, 0 errors
  - tempus_2.log - Total: 0 warnings, 0 errors
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: STA warnings detected that require waiver review
ERROR01:
  - TECHLIB-302 (Count: 2032): No function defined for cell '%s'. The c...
  - TECHLIB-1320 (Count: 276): The user-defined attribute 'related_spice_node' is not present...
  - IMPDBTCL-321 (Count: 1): The attribute '%s' still works but will ...
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-10-0-0-21:
  description: "Confirm all Warning message in the STA log files can be waived."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_1.log
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_2.log
  waivers:
    value: 0        # Forces PASS: all violations → INFO
    waive_items:    # REQUIRED: Must provide explanation
      - "Pre-implementation phase - warnings expected during initial STA runs"
```

**Special Behavior (waivers.value=0):**
⚠️ **CRITICAL**: When `waivers.value=0`, `waive_items` MUST have content:

- `waive_items` strings → INFO with `[WAIVED_INFO]` suffix (shows reason for forced PASS)
- ALL detected violations → INFO with `[WAIVED_AS_INFO]` suffix (forced conversion)
- Result: **Always PASS** (informational check mode)

**Sample Output:**

```
Status: PASS (forced)
Reason: All items converted to informational
INFO01:
  - Pre-implementation phase - warnings expected during initial STA runs [WAIVED_INFO]
  - TECHLIB-302 (Count: 2032): No function defined for cell '%s'. The c... [WAIVED_AS_INFO]
  - TECHLIB-1320 (Count: 276): The user-defined attribute 'related_spice_node' is not present... [WAIVED_AS_INFO]
```

---

## Type 2: Value comparison

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-10-0-0-21:
  description: "Confirm all Warning message in the STA log files can be waived."
  requirements:
    value: 2  # MUST equal the number of pattern_items (2 patterns below)
    pattern_items:
      - "TECHLIB-302"
      - "TECHLIB-1320"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_1.log
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_2.log
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 validates that the exact set of expected warnings (specified in pattern_items) are present in the STA logs. It performs exact matching: PASS if detected warnings match pattern_items exactly (same count and types), FAIL if any extra warnings are found or expected warnings are missing. This mode is used when the warning profile is well-characterized and stable.

**Sample Output (FAIL):**

```
Status: FAIL
Reason: STA warnings detected that require waiver review
ERROR01:
  - TECHLIB-302 (Count: 2032): No function defined for cell '%s'. The c...
  - TECHLIB-1320 (Count: 276): The user-defined attribute 'related_spice_node' is not present...
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-10-0-0-21:
  description: "Confirm all Warning message in the STA log files can be waived."
  requirements:
    value: 2
    pattern_items:
      - "TECHLIB-302"
      - "TECHLIB-1320"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_1.log
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_2.log
  waivers:
    value: 0        # Forces PASS: all violations → INFO
    waive_items:    # REQUIRED: Must provide explanation
      - "Debug mode - all STA warnings are informational only"
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
IMP-10-0-0-21:
  description: "Confirm all Warning message in the STA log files can be waived."
  requirements:
    value: 2  # MUST equal the number of pattern_items (2 patterns below)
    pattern_items:
      - "TECHLIB-302"
      - "TECHLIB-1320"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_1.log
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_2.log
  waivers:
    value: 2  # Number of waiver entries (separate from requirements.value)
    waive_items:
      - name: "TECHLIB-302"
        reason: "Known library limitation - cells are functional primitives without boolean functions"
      - name: "IMPDBTCL-321"
        reason: "Deprecated attribute usage - will be updated in next tool version"
```

**Check Behavior:**
Type 3 combines value comparison with waiver support. It checks if detected warnings match pattern_items, but allows specific warnings to be waived with documented reasons. Warnings matching waiver entries are moved to INFO01 with [WAIVER] tag. PASS if all warnings are either in pattern_items or waived; FAIL if unexpected warnings appear. Unused waiver entries generate WARN01.

**Sample Output (with waived items):**

```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - TECHLIB-302 (Count: 2032): No function defined for cell '%s'. The c... [WAIVER]
  - IMPDBTCL-321 (Count: 1): The attribute '%s' still works but will ... [WAIVER]
WARN01 (Unused Waivers):
  - TECHLIB-1320 (Count: 276): The user-defined attribute 'related_spice_node' is not present...: Waiver entry does not match any detected warnings
```

---

## Type 4: Boolean Check with Waivers

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-10-0-0-21:
  description: "Confirm all Warning message in the STA log files can be waived."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_1.log
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/tempus_2.log
  waivers:
    value: 2
    waive_items:
      - name: "TECHLIB-302"
        reason: "Known library limitation - cells are functional primitives without boolean functions"
      - name: "TECHLIB-1320"
        reason: "SPICE correlation not required for this design - attribute can be safely ignored"
```

**Check Behavior:**
Type 4 performs boolean check (any warnings = potential FAIL) but allows waivers to convert specific warnings to PASS. All detected warnings are checked against waiver entries. Warnings matching waivers move to INFO01 with [WAIVER] tag and documented reason. PASS if all warnings are waived; FAIL if any unwaived warnings remain. This is the most flexible mode for production flows with known acceptable warnings.

**Sample Output:**

```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - TECHLIB-302 (Count: 2032): No function defined for cell '%s'. The c... [WAIVER]
  - TECHLIB-1320 (Count: 276): The user-defined attribute 'related_spice_node' is not present... [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 10.0_STA_DCD_CHECK --checkers IMP-10-0-0-21 --force

# Run individual tests
python IMP-10-0-0-21.py
```

---

## Notes

- **Multi-file aggregation**: Warning counts are summed across all input log files. The same warning ID appearing in multiple files will have combined counts.
- **Truncated logs**: If log files contain the comment "# Limit to 10KB", the checker will flag this as potentially incomplete data.
- **Warning ID matching**: Waiver matching uses exact string comparison including count values. Ensure waiver entries match the exact format output by the checker.
- **Summary section parsing**: The checker prioritizes the summary table section over inline warnings for count accuracy. If summary section is missing, it falls back to inline warning parsing.
- **Tool version tracking**: The checker extracts Tempus version information for context but does not enforce version-specific waiver rules.
- **Edge cases handled**:
  - Empty log files → reported as 0 warnings (PASS for Type 1)
  - Missing summary section → uses inline warning extraction
  - Multi-line warning messages → continuation lines are concatenated
  - Warnings without file location → optional capture groups handle both formats
