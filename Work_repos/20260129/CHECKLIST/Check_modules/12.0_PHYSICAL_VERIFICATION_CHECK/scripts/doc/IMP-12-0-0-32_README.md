# IMP-12-0-0-32: Confirm no ERROR message in DFM/FLT log files. (for SEC process, for others fill N/A)

## Overview

**Check ID:** IMP-12-0-0-32  
**Description:** Confirm no ERROR message in DFM/FLT log files. (for SEC process, for others fill N/A)  
**Category:** Physical Verification Quality Check  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log`, `${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log`

This checker validates that Pegasus DFM (Design for Manufacturing) and FLT (Floating) verification runs completed without critical errors. It scans log files for ERROR messages that indicate compilation failures, worker crashes, file system issues, or rule violations. The checker ensures physical verification quality by detecting unrecoverable errors that could compromise layout integrity or manufacturability.

---

## Check Logic

### Input Parsing
Parse Pegasus log files to extract ERROR messages using multiple pattern formats. ERROR messages may appear with different prefixes (`ERROR:`, `[ERROR]`, `Error:`), include worker identification, or contain error codes. The checker normalizes these formats to detect all error conditions regardless of formatting variations.

**Key Patterns (shared across all types):**
```python
# Pattern 1: Standard ERROR prefix (Pegasus FLT format)
pattern1 = r'^ERROR:\s*(.+)$'
# Example: "ERROR: Terminating run, encountered unrecoverable error on Worker 2"

# Pattern 2: Bracketed ERROR format (Pegasus DFM format)
pattern2 = r'^\[?ERROR\]?:?\s*(.+)$'
# Example: "[ERROR] Invalid option."

# Pattern 3: Error with worker context
pattern3 = r'^Error:\s*(.+?)\s*\(Worker\s+(\d+)\)$'
# Example: "Error: Pegasus exception during compilation (Worker 1)"

# Pattern 4: ERROR with error code
pattern4 = r'^ERROR\s*\(([A-Z]+-\d+)\):\s*(.+)$'
# Example: "ERROR (NVN-7090): The difference between the numbers of schematic and layout instances"

# Pattern 5: INPUT ERROR format (cell reference errors)
pattern7 = r'^\[INPUT ERROR\]\s*(.+)$'
# Example: "[INPUT ERROR] Cell pm26 is referenced, but does not exist."

# Pattern 6: Completion status
pattern5 = r'^Pegasus\s+(finished\s+normally|failed|aborted)\.\s+(.+)$'
# Example: "Pegasus finished normally. 2025-12-13 16:12:17"

# Pattern 7: WARNING messages (for context)
pattern6 = r'^WARNING:\s*(.+)$'
# Example: "WARNING: Worker 1 killed by external signal [9]"
```

### Detection Logic
1. Read both input log files (do_pvsFLTwD.log and Pegasus_DFM.log)
2. Scan each line using ERROR pattern regexes (patterns 1-5)
3. Extract ERROR messages and categorize by source:
   - Worker-related errors: Extract worker ID from `(Worker N)` pattern
   - Rule-related errors: Extract error code from `(CODE-NNNN)` pattern
   - Cell reference errors: Extract cell name from `Cell [name] is referenced` pattern
   - Generic errors: Use full error message text
4. For Type 1/4: Count total ERROR occurrences (boolean check)
5. For Type 2/3: Match ERROR messages against pattern_items (value check)
6. For Type 3/4: Apply waiver logic using TWO matching strategies:
   - **Strategy 1 (Preferred):** Match SOURCE identifier (Worker ID, cell name, error code) against waive_items.name using regex
     - Example: `name: "Worker 1$"` matches errors with "(Source: Worker 1)"
     - Example: `name: "NVN-7090"` matches errors with "(Source: NVN-7090)"
   - **Strategy 2 (Fallback):** Match FULL ERROR MESSAGE against waive_items.name using regex if source match fails
     - Example: `name: "Terminating run.*unrecoverable"` matches any error message containing this pattern
     - Example: `name: "Out of.*disk space"` matches disk space errors regardless of worker ID
   - **Important:** Use `$` anchor for exact source matching to avoid partial matches (e.g., "Worker 1$" won't match "Worker 11")
7. Determine PASS/FAIL:
   - Type 1/2: FAIL if any ERROR found
   - Type 3/4: FAIL only if unwaived ERRORs exist

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

**Rationale:** This checker validates ERROR message patterns in log files. When pattern_items are specified (Type 2/3), they represent specific ERROR message patterns to monitor (e.g., "Worker.*killed", "Out of.*disk space"). The checker only reports ERRORs matching these patterns, not all possible errors. This is status_check behavior: only output items matching pattern_items, where "status" means ERROR presence/absence.

---

## Output Descriptions (CRITICAL - Code Generator Uses These!)

This section defines the output strings used by `build_complete_output()` in the checker code.

```python
# Item description for this checker
item_desc = "Confirm no ERROR message in DFM/FLT log files"

# PASS case descriptions - Split by Type semantics (API-026)
found_desc_type1_4 = "No ERROR messages found in Pegasus verification logs"
found_desc_type2_3 = "All monitored ERROR patterns validated (0 errors found)"

# PASS reasons - Split by Type semantics
found_reason_type1_4 = "Pegasus DFM/FLT verification completed without errors"
found_reason_type2_3 = "Monitored ERROR patterns not detected in verification logs"

# FAIL case descriptions
missing_desc_type1_4 = "ERROR messages detected in Pegasus verification logs"
missing_desc_type2_3 = "Monitored ERROR patterns detected in verification logs"

# FAIL reasons
missing_reason_type1_4 = "Pegasus DFM/FLT verification encountered critical errors"
missing_reason_type2_3 = "Monitored ERROR patterns found in verification logs"

# WAIVED case descriptions
waived_desc = "ERROR messages waived per verification team approval"
waived_base_reason = "Pegasus verification errors waived as known issues"

# UNUSED waivers
unused_desc = "Unused ERROR waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding ERROR found in logs"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "No ERROR messages in [log_filename]"
  Example: "No ERROR messages in do_pvsFLTwD.log"

ERROR01 (Violation/Fail items):
  Format: "[error_message] (Source: [worker_id/error_code/file])"
  Example: "Terminating run, encountered unrecoverable error (Source: Worker 2)"
  Example: "Invalid option (Source: Pegasus_DFM.log:line 45)"
  Example: "Out of temporary storage disk space (Source: Worker 11)"
  Example: "Cell pm26 is referenced, but does not exist (Source: pm26)"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-32:
  description: "Confirm no ERROR message in DFM/FLT log files. (for SEC process, for others fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs boolean check for ERROR message presence across all Pegasus log files.
PASS if no ERROR messages found in any log file.
FAIL if any ERROR message detected (regardless of error type or source).

**Sample Output (PASS):**
```
Status: PASS
Reason: Pegasus DFM/FLT verification completed without errors

Log format (item_id.log):
INFO01:
  - No ERROR messages in do_pvsFLTwD.log
  - No ERROR messages in Pegasus_DFM.log

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: No ERROR messages in do_pvsFLTwD.log. In line 0, ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log: Pegasus DFM/FLT verification completed without errors
2: Info: No ERROR messages in Pegasus_DFM.log. In line 0, ${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Pegasus DFM/FLT verification completed without errors
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Pegasus DFM/FLT verification encountered critical errors

Log format (item_id.log):
ERROR01:
  - Terminating run, encountered unrecoverable error (Source: Worker 2)
  - Invalid option (Source: Pegasus_DFM.log:line 45)
  - Out of temporary storage disk space (Source: Worker 11)
  - Cell pm26 is referenced, but does not exist (Source: pm26)

Report format (item_id.rpt):
Fail Occurrence: 4
1: Fail: Terminating run, encountered unrecoverable error (Source: Worker 2). In line 234, ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log: Pegasus DFM/FLT verification encountered critical errors
2: Fail: Invalid option (Source: Pegasus_DFM.log:line 45). In line 45, ${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Pegasus DFM/FLT verification encountered critical errors
3: Fail: Out of temporary storage disk space (Source: Worker 11). In line 156, ${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Pegasus DFM/FLT verification encountered critical errors
4: Fail: Cell pm26 is referenced, but does not exist (Source: pm26). In line 78, ${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Pegasus DFM/FLT verification encountered critical errors
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-32:
  description: "Confirm no ERROR message in DFM/FLT log files. (for SEC process, for others fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode
    waive_items:  # IMPORTANT: Use PLAIN STRING format
      - "Explanation: DFM/FLT verification errors are informational for SEC process"
      - "Note: Non-SEC processes should use N/A or proper waiver configuration"
      - "Rationale: SEC-specific layout rules may trigger expected errors in standard flows"
```

**Sample Output (PASS with violations):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All violations waived as informational

Log format (item_id.log):
INFO01:
  - "Explanation: DFM/FLT verification errors are informational for SEC process"
  - "Note: Non-SEC processes should use N/A or proper waiver configuration"
  - "Rationale: SEC-specific layout rules may trigger expected errors in standard flows"
INFO02:
  - Terminating run, encountered unrecoverable error (Source: Worker 2)
  - Invalid option (Source: Pegasus_DFM.log:line 45)

Report format (item_id.rpt):
Info Occurrence: 5
1: Info: Explanation: DFM/FLT verification errors are informational for SEC process. [WAIVED_INFO]
2: Info: Note: Non-SEC processes should use N/A or proper waiver configuration. [WAIVED_INFO]
3: Info: Rationale: SEC-specific layout rules may trigger expected errors in standard flows. [WAIVED_INFO]
4: Info: Terminating run, encountered unrecoverable error (Source: Worker 2). In line 234, ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log: Pegasus DFM/FLT verification encountered critical errors [WAIVED_AS_INFO]
5: Info: Invalid option (Source: Pegasus_DFM.log:line 45). In line 45, ${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Pegasus DFM/FLT verification encountered critical errors [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-32:
  description: "Confirm no ERROR message in DFM/FLT log files. (for SEC process, for others fill N/A)"
  requirements:
    value: 4
    pattern_items:
      - "Worker.*killed"
      - "Out of.*disk space"
      - "missing_reference exception"
      - "Cell.*is referenced, but does not exist"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Use REGEX PATTERNS to match ERROR message content
- Patterns match against full ERROR message text
- Use `.*` for flexible matching (e.g., "Worker.*killed" matches "Worker 1 killed by external signal")
- Patterns are case-sensitive unless explicitly using `(?i)` flag

**Check Behavior:**
Type 2 searches for specific ERROR message patterns in log files.
PASS if none of the monitored ERROR patterns are found (found_items empty).
FAIL if any monitored ERROR pattern is detected (found_items not empty).
This is a violation check: pattern_items define ERROR patterns to monitor, finding them means FAIL.

**Sample Output (PASS):**
```
Status: PASS
Reason: Monitored ERROR patterns not detected in verification logs

Log format (item_id.log):
INFO01:
  - Worker.*killed (not found)
  - Out of.*disk space (not found)
  - missing_reference exception (not found)
  - Cell.*is referenced, but does not exist (not found)

Report format (item_id.rpt):
Info Occurrence: 4
1: Info: Worker.*killed (not found). In line 0, ${CHECKLIST_ROOT}/IP_project_folder/logs/: Monitored ERROR patterns not detected in verification logs
2: Info: Out of.*disk space (not found). In line 0, ${CHECKLIST_ROOT}/IP_project_folder/logs/: Monitored ERROR patterns not detected in verification logs
3: Info: missing_reference exception (not found). In line 0, ${CHECKLIST_ROOT}/IP_project_folder/logs/: Monitored ERROR patterns not detected in verification logs
4: Info: Cell.*is referenced, but does not exist (not found). In line 0, ${CHECKLIST_ROOT}/IP_project_folder/logs/: Monitored ERROR patterns not detected in verification logs
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Monitored ERROR patterns found in verification logs

Log format (item_id.log):
ERROR01:
  - Worker 1 killed by external signal [9] (matches: Worker.*killed)
  - Out of temporary storage disk space, please check -tmp_dirs setting (matches: Out of.*disk space)
  - Cell pm26 is referenced, but does not exist (matches: Cell.*is referenced, but does not exist)

Report format (item_id.rpt):
Fail Occurrence: 3
1: Fail: Worker 1 killed by external signal [9] (matches: Worker.*killed). In line 123, ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log: Monitored ERROR patterns found in verification logs
2: Fail: Out of temporary storage disk space, please check -tmp_dirs setting (matches: Out of.*disk space). In line 156, ${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Monitored ERROR patterns found in verification logs
3: Fail: Cell pm26 is referenced, but does not exist (matches: Cell.*is referenced, but does not exist). In line 78, ${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Monitored ERROR patterns found in verification logs
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-32:
  description: "Confirm no ERROR message in DFM/FLT log files. (for SEC process, for others fill N/A)"
  requirements:
    value: 0
    pattern_items:
      - "Worker.*killed"
      - "Out of.*disk space"
      - "missing_reference exception"
      - "Cell.*is referenced, but does not exist"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode
    waive_items:  # IMPORTANT: Use PLAIN STRING format
      - "Explanation: Monitored ERROR patterns are informational for SEC process"
      - "Note: Worker crashes and disk space errors are handled by infrastructure team"
      - "Rationale: These errors do not affect final verification results"
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

Log format (item_id.log):
INFO01:
  - "Explanation: Monitored ERROR patterns are informational for SEC process"
  - "Note: Worker crashes and disk space errors are handled by infrastructure team"
  - "Rationale: These errors do not affect final verification results"
INFO02:
  - Worker 1 killed by external signal [9] (matches: Worker.*killed)
  - Out of temporary storage disk space (matches: Out of.*disk space)

Report format (item_id.rpt):
Info Occurrence: 5
1: Info: Explanation: Monitored ERROR patterns are informational for SEC process. [WAIVED_INFO]
2: Info: Note: Worker crashes and disk space errors are handled by infrastructure team. [WAIVED_INFO]
3: Info: Rationale: These errors do not affect final verification results. [WAIVED_INFO]
4: Info: Worker 1 killed by external signal [9] (matches: Worker.*killed). In line 123, ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log: Monitored ERROR patterns found in verification logs [WAIVED_AS_INFO]
5: Info: Out of temporary storage disk space (matches: Out of.*disk space). In line 156, ${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Monitored ERROR patterns found in verification logs [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-32:
  description: "Confirm no ERROR message in DFM/FLT log files. (for SEC process, for others fill N/A)"
  requirements:
    value: 4
    pattern_items:
      - "Worker.*killed"
      - "Out of.*disk space"
      - "missing_reference exception"
      - "Cell.*is referenced, but does not exist"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log"
  waivers:
    value: 3
    waive_items:
      - name: "Worker 1$"  # Worker ID to exempt (use $ for exact match to avoid matching "Worker 11")
        reason: "Waived - Worker 1 crash is known infrastructure issue (ticket #12345)"
      - name: "Worker 11$"  # Worker ID to exempt (use $ for exact match)
        reason: "Waived - Worker 11 disk space handled by storage team"
      - name: "pm26"  # Cell name to exempt
        reason: "Waived - Cell pm26 reference error is expected in SEC flow"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:
- pattern_items = ERROR MESSAGE PATTERNS to match (regex patterns like "Worker.*killed")
- waive_items.name = Supports TWO matching strategies:
  - **Strategy 1 (Preferred):** SOURCE OBJECT patterns (Worker IDs, cell names, error codes)
    - Use regex anchors for precise matching: "Worker 1$" (exact), "Worker.*" (any worker)
  - **Strategy 2 (Fallback):** FULL ERROR MESSAGE patterns (matches complete error text)
    - Used when source matching fails: "Terminating run.*unrecoverable"
- **Important:** Add `$` anchor to prevent partial matches ("Worker 1$" won't match "Worker 11")
- waive_items.name = ERROR SOURCE OBJECTS to exempt (Worker IDs, cell names, error codes)
- Example: pattern "Worker.*killed" matches error, waive by worker ID "Worker 1", NOT by pattern text
- waive_items.name uses REGEX PATTERNS to match error source objects extracted from ERROR messages

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
1. Search for ERROR messages matching pattern_items (regex patterns)
2. Extract source objects from matched ERRORs:
   - Worker ID from "(Worker N)" pattern
   - Cell name from "cell \"name\"" pattern or "Cell name is referenced" pattern
   - Error code from "(CODE-NNNN)" pattern
3. Match waivers using TWO strategies (tries in order):
   - **Strategy 1:** Match SOURCE object against waive_items.name (preferred)
   - **Strategy 2:** Match FULL ERROR MESSAGE against waive_items.name (fallback)
4. Classify as:
   - Unwaived items → ERROR (need fix)
   - Waived items → INFO with [WAIVER] tag (approved)
   - Unused waivers → WARN with [WAIVER] tag
PASS if all found_items (violations) are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived

Log format (item_id.log):
INFO01:
  - Worker 1 killed by external signal [9] (Source: Worker 1)
  - Out of temporary storage disk space (Source: Worker 11)
  - Cell pm26 is referenced, but does not exist (Source: pm26)
WARN01:
  - Worker 2 (unused waiver)

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: Worker 1 killed by external signal [9] (Source: Worker 1). In line 123, ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log: Pegasus verification errors waived as known issues: Waived - Worker 1 crash is known infrastructure issue (ticket #12345) [WAIVER]
2: Info: Out of temporary storage disk space (Source: Worker 11). In line 156, ${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Pegasus verification errors waived as known issues: Waived - Worker 11 disk space handled by storage team [WAIVER]
3: Info: Cell pm26 is referenced, but does not exist (Source: pm26). In line 78, ${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Pegasus verification errors waived as known issues: Waived - Cell pm26 reference error is expected in SEC flow [WAIVER]
Warn Occurrence: 1
1: Warn: Worker 2 (unused waiver). In line 0, ${CHECKLIST_ROOT}/IP_project_folder/logs/: Waiver not matched - no corresponding ERROR found in logs: Waived - Worker 2 issue resolved [WAIVER]
```

**Sample Output (with unwaived items - FAIL):**
```
Status: FAIL
Reason: Monitored ERROR patterns found in verification logs

Log format (item_id.log):
ERROR01:
  - missing_reference exception for cell "pm30" (Source: pm30)
INFO01:
  - Worker 1 killed by external signal [9] (Source: Worker 1)
  - Cell pm26 is referenced, but does not exist (Source: pm26)

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: missing_reference exception for cell "pm30" (Source: pm30). In line 89, ${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Monitored ERROR patterns found in verification logs
Info Occurrence: 2
1: Info: Worker 1 killed by external signal [9] (Source: Worker 1). In line 123, ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log: Pegasus verification errors waived as known issues: Waived - Worker 1 crash is known infrastructure issue (ticket #12345) [WAIVER]
2: Info: Cell pm26 is referenced, but does not exist (Source: pm26). In line 78, ${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Pegasus verification errors waived as known issues: Waived - Cell pm26 reference error is expected in SEC flow [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-32:
  description: "Confirm no ERROR message in DFM/FLT log files. (for SEC process, for others fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log"
  waivers:
    value: 3
    waive_items:
      - name: "Worker 1$"  # ⚠️ MUST match Type 3 waive_items (use $ for exact match)
        reason: "Waived - Worker 1 crash is known infrastructure issue (ticket #12345)"
      - name: "Worker 11$"  # ⚠️ MUST match Type 3 waive_items (use $ for exact match)
        reason: "Waived - Worker 11 disk space handled by storage team"
      - name: "pm26"  # ⚠️ MUST match Type 3 waive_items
        reason: "Waived - Cell pm26 reference error is expected in SEC flow"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (keep exemption object names consistent)
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (no pattern_items - checks ALL errors), plus waiver classification:
1. Scan for ANY ERROR message in log files (no pattern filtering)
2. Extract source objects from all ERRORs (Worker ID, cell name, error code)
3. Match waivers using TWO strategies (tries in order):
   - **Strategy 1:** Match SOURCE object against waive_items.name using regex (preferred)
   - **Strategy 2:** Match FULL ERROR MESSAGE against waive_items.name (fallback)
4. Classify as:
   - Unwaived violations → ERROR
   - Waived violations → INFO with [WAIVER] tag
   - Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output (PASS - all waived):**
```
Status: PASS
Reason: All items waived

Log format (item_id.log):
INFO01:
  - Worker 1 killed by external signal [9] (Source: Worker 1)
  - Out of temporary storage disk space (Source: Worker 11)
  - Cell pm26 is referenced, but does not exist (Source: pm26)
WARN01:
  - Worker 2 (unused waiver)

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: Worker 1 killed by external signal [9] (Source: Worker 1). In line 123, ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log: Pegasus verification errors waived as known issues: Waived - Worker 1 crash is known infrastructure issue (ticket #12345) [WAIVER]
2: Info: Out of temporary storage disk space (Source: Worker 11). In line 156, ${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Pegasus verification errors waived as known issues: Waived - Worker 11 disk space handled by storage team [WAIVER]
3: Info: Cell pm26 is referenced, but does not exist (Source: pm26). In line 78, ${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Pegasus verification errors waived as known issues: Waived - Cell pm26 reference error is expected in SEC flow [WAIVER]
Warn Occurrence: 1
1: Warn: Worker 2 (unused waiver). In line 0, ${CHECKLIST_ROOT}/IP_project_folder/logs/: Waiver not matched - no corresponding ERROR found in logs: Waived - Worker 2 issue resolved [WAIVER]
```

**Sample Output (FAIL - unwaived errors exist):**
```
Status: FAIL
Reason: Pegasus DFM/FLT verification encountered critical errors

Log format (item_id.log):
ERROR01:
  - Terminating run, encountered unrecoverable error (Source: Worker 2)
  - Invalid option (Source: Pegasus_DFM.log:line 45)
INFO01:
  - Worker 1 killed by external signal [9] (Source: Worker 1)
  - Cell pm26 is referenced, but does not exist (Source: pm26)

Report format (item_id.rpt):
Fail Occurrence: 2
1: Fail: Terminating run, encountered unrecoverable error (Source: Worker 2). In line 234, ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log: Pegasus DFM/FLT verification encountered critical errors
2: Fail: Invalid option (Source: Pegasus_DFM.log:line 45). In line 45, ${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Pegasus DFM/FLT verification encountered critical errors
Info Occurrence: 2
1: Info: Worker 1 killed by external signal [9] (Source: Worker 1). In line 123, ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log: Pegasus verification errors waived as known issues: Waived - Worker 1 crash is known infrastructure issue (ticket #12345) [WAIVER]
2: Info: Cell pm26 is referenced, but does not exist (Source: pm26). In line 78, ${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Pegasus verification errors waived as known issues: Waived - Cell pm26 reference error is expected in SEC flow [WAIVER]