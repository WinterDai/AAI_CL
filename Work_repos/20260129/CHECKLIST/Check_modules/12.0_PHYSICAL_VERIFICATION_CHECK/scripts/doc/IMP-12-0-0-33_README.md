# IMP-12-0-0-33: Confirm all Warning message in DFM/FLT log files can be waived. (for SEC process, for others fill N/A)

## Overview

**Check ID:** IMP-12-0-0-33
**Description:** Confirm all Warning message in DFM/FLT log files can be waived. (for SEC process, for others fill N/A)
**Category:** Physical Verification Quality Check
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log`, `${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log`

This checker validates that Pegasus DFM/FLT verification logs contain no WARNING messages. The primary goal is to ensure a clean verification run without warnings. If warnings exist, the checker (with waiver configuration) can verify that all warnings have been explicitly approved for waiver. This is parallel to IMP-12-0-0-32 which checks ERROR messages - both ensure clean verification logs or properly waived issues.

---

## Check Logic

### Input Parsing

Parse Pegasus DFM and FLT verification log files to extract all WARNING messages and their source identifiers. Similar to ERROR checking (IMP-12-0-0-32), this checker identifies warning sources (worker IDs, warning codes, affected cells) to enable precise waiver matching.

**Key Patterns (shared across all types):**

```python
# Pattern 1: Standard WARNING messages
pattern_warning = r'^WARNING:\s*(.+)$'
# Example: "WARNING: Worker 1 killed by external signal [9]"

# Pattern 2: Multi-line WARNING blocks with identifiers
pattern_warning_code = r'^WARNING:\s*([A-Z0-9-]+)\s*$'
# Example: "WARNING: GDR-00003"

# Pattern 3: [WARN] tagged messages
pattern_warn_tag = r'^\[WARN\]\s*(.+)$'
# Example: "[WARN] same label "x" for multiple nets, it is assigned to net x"

# Pattern 4: Capitalized Warning messages
pattern_warning_cap = r'^Warning:\s*(.+)$'
# Example: "Warning: Encountered problems with Worker 1, attempting recovery..."

```

### Detection Logic

1. Read both input log files (do_pvsFLTwD.log and Pegasus_DFM.log)
2. Scan each line using WARNING pattern regexes (patterns 1-4)
3. Extract warning messages and categorize by source:
   - Worker-related warning: Extract worker ID from `(Worker N)` pattern
   - Rule-related warnings: Extract warning code from `(CODE-NNNN)` pattern
   - Generic warnings: Use full warning message text
4. For Type 1/4: Count total WARNING occurrences (boolean check)
5. For Type 2/3: Match WARNING messages against pattern_items (value check)
6. For Type 3/4: Apply waiver logic using TWO matching strategies:
   - **Strategy 1 (Preferred):** Match SOURCE identifier (Worker ID, cell name, warning code) against waive_items.name using regex
     - Example: `name: "Worker 1$"` matches warnings with "(Source: Worker 1)"
     - Example: `name: "GDR-0003"` matches warnings with "(Source: GDR-0003)"
   - **Strategy 2 (Fallback):** Match FULL WARNING MESSAGE against waive_items.name using regex if source match fails
     - Example: `name: "same label.*multiple nets"` matches any warning message containing this pattern
     - Example: `name: "Out of.*disk space"` matches disk space warnings regardless of worker ID
   - **Important:** Use `$` anchor for exact source matching to avoid partial matches (e.g., "Worker 1$" won't match "Worker 11")
7. Determine PASS/FAIL:
   - Type 1/2: FAIL if any WARNING found
   - Type 3/4: FAIL only if unwaived WARNINGs exist

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

**Rationale:** This checker validates warning message patterns in log files. When pattern_items are specified (Type 2/3), they represent specific warning message patterns to monitor (e.g., "Worker.*killed", "Out of.*disk space"). The checker only reports warnings matching these patterns, not all possible warnings. This is status_check behavior: only output items matching pattern_items, where "status" means warnings presence/absence.

---

## Output Descriptions (CRITICAL - Code Generator Uses These!)

This section defines the output strings used by `build_complete_output()` in the checker code.

```python
# Item description for this checker
item_desc = "Confirm all Warning message in DFM/FLT log files can be waived. (for SEC process, for others fill N/A)"

# PASS case descriptions - Split by Type semantics (API-026)
found_desc_type1_4 = "No WARNING messages found in Pegasus verification logs"
found_desc_type2_3 = "All monitored WARNING patterns validated (0 warnings found)"

# PASS reasons - Split by Type semantics
found_reason_type1_4 = "Pegasus DFM/FLT verification completed without warnings"
found_reason_type2_3 = "Monitored WARNING patterns not detected in verification logs"

# FAIL case descriptions
missing_desc_type1_4 = "WARNING messages detected in Pegasus verification logs"
missing_desc_type2_3 = "Monitored WARNING patterns detected in verification logs"

# FAIL reasons
missing_reason_type1_4 = "Pegasus DFM/FLT verification encountered warnings"
missing_reason_type2_3 = "Monitored WARNING patterns found in verification logs"

# WAIVED case descriptions
waived_desc = "WARNING messages waived per verification team approval"
waived_base_reason = "Pegasus verification warnings waived as known issues"

# UNUSED waivers
unused_desc = "Unused warning waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding WARNING found in logs"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "No WARNING messages in [log_filename]"
  Example: "No WARNING messages in do_pvsFLTwD.log"
  Note: Only displayed when Type 2/3 with patterns not found

ERROR01 (Violation/Fail items):
  Format: "[warning_message] (Source: [worker_id/warning_code/file])"
  Example: "Worker 1 killed by external signal [9] (Source: Worker 1)"
  Example: "same label \"x\" for multiple nets (Source: GDR-00003)"
  Example: "Invalid option (Source: do_pvsFLTwD.log:line 281)"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-12-0-0-33:
  description: "Confirm all Warning message in DFM/FLT log files can be waived. (for SEC process, for others fill N/A)"
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
Type 1: Boolean check without waiver support.

Verifies no WARNING messages exist in Pegasus DFM/FLT log files.
PASS if no WARNING messages found in any log file.
FAIL if any WARNING message detected (regardless of warning type or source).

**Sample Output (PASS):**

```
Status: PASS
Reason: Pegasus DFM/FLT verification completed without warnings

Log format (item_id.log):
INFO01:
  - No WARNING messages in do_pvsFLTwD.log
  - No WARNING messages in Pegasus_DFM.log

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: No WARNING messages in do_pvsFLTwD.log. In line 0, ${CHECKLIST_ROOT}/IP_project_folder/logs/: Pegasus DFM/FLT verification completed without warnings
2: Info: No WARNING messages in Pegasus_DFM.log. In line 0, ${CHECKLIST_ROOT}/IP_project_folder/logs/: Pegasus DFM/FLT verification completed without warnings
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: Pegasus DFM/FLT verification encountered warnings

Log format (item_id.log):
ERROR01:
  - Worker 1 killed by external signal [9] (Source: Worker 1)
  - same label "x" for multiple nets (Source: GDR-00003)
  - Invalid option (Source: do_pvsFLTwD.log:line 281)

Report format (item_id.rpt):
Fail Occurrence: 3
1: Fail: Worker 1 killed by external signal [9] (Source: Worker 1). In line 245, C:\${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log: Pegasus DFM/FLT verification encountered warnings
2: Fail: same label "x" for multiple nets (Source: GDR-00003). In line 312, C:\${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Pegasus DFM/FLT verification encountered warnings
3: Fail: Invalid option (Source: do_pvsFLTwD.log:line 281). In line 281, C:\${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log: Pegasus DFM/FLT verification encountered warnings
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-12-0-0-33:
  description: "Confirm all Warning message in DFM/FLT log files can be waived. (for SEC process, for others fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode
    waive_items:  # IMPORTANT: Use PLAIN STRING format
      - "Explanation: DFM/FLT warnings are informational for SEC process review"
      - "Note: All warnings reviewed and documented by physical verification team"
```

**CRITICAL Behavior (waivers.value=0):**

- waive_items content printed as INFO with [WAIVED_INFO] tag
- ALL warnings force converted: ERROR→INFO with [WAIVED_AS_INFO] tag
- Check ALWAYS returns PASS (warnings shown as INFO for tracking)

**Sample Output (PASS with violations):**

```
Status: PASS  # Always PASS when waivers.value=0
Reason: All violations waived as informational

Log format (item_id.log):
INFO01:
  - "Explanation: DFM/FLT warnings are informational for SEC process review"
  - "Note: All warnings reviewed and documented by physical verification team"
INFO02:
  - Worker 1 killed by external signal [9] (Source: Worker 1)
  - same label "x" for multiple nets (Source: GDR-00003)

Report format (item_id.rpt):
Info Occurrence: 4
1: Info: Explanation: DFM/FLT warnings are informational for SEC process review. [WAIVED_INFO]
2: Info: Note: All warnings reviewed and documented by physical verification team. [WAIVED_INFO]
3: Info: Worker 1 killed by external signal [9] (Source: Worker 1). In line 245, C:\${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log: Pegasus DFM/FLT verification encountered warnings [WAIVED_AS_INFO]
4: Info: same label "x" for multiple nets (Source: GDR-00003). In line 312, C:\${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Pegasus DFM/FLT verification encountered warnings [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-12-0-0-33:
  description: "Confirm all Warning message in DFM/FLT log files can be waived. (for SEC process, for others fill N/A)"
  requirements:
    value: 4
    pattern_items:
      - "Worker.*killed"
      - "Out of.*disk space"
      - "same label.*multiple nets"
      - "GDR-[0-9]+"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:

- pattern_items = WARNING MESSAGE PATTERNS to monitor (regex patterns like "Worker.*killed")
- Use regex for flexible matching: "Worker.*killed" matches various worker failure messages

**Check Behavior:**
Type 2: Pattern/value check without waiver support.

Searches for WARNING messages matching pattern_items in Pegasus DFM/FLT log files.
This is a violation check: finding monitored WARNING patterns means FAIL.
PASS if none of the monitored patterns are found (clean logs).
FAIL if any monitored WARNING pattern is detected.

**Sample Output (PASS):**

```
Status: PASS
Reason: Monitored WARNING patterns not detected in verification logs

Log format (item_id.log):
INFO01:
  - Worker.*killed (not found)
  - Out of.*disk space (not found)
  - same label.*multiple nets (not found)
  - GDR-[0-9]+ (not found)

Report format (item_id.rpt):
Info Occurrence: 4
1: Info: Worker.*killed (not found). In line 0, ${CHECKLIST_ROOT}/IP_project_folder/logs/: Monitored WARNING patterns not detected in verification logs
2: Info: Out of.*disk space (not found). In line 0, ${CHECKLIST_ROOT}/IP_project_folder/logs/: Monitored WARNING patterns not detected in verification logs
3: Info: same label.*multiple nets (not found). In line 0, ${CHECKLIST_ROOT}/IP_project_folder/logs/: Monitored WARNING patterns not detected in verification logs
4: Info: GDR-[0-9]+ (not found). In line 0, ${CHECKLIST_ROOT}/IP_project_folder/logs/: Monitored WARNING patterns not detected in verification logs
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: Monitored WARNING patterns found in verification logs

Log format (item_id.log):
ERROR01:
  - Worker 1 killed by external signal [9] (matches: Worker.*killed)
  - Out of temporary storage disk space (matches: Out of.*disk space)
  - same label "x" for multiple nets (matches: same label.*multiple nets)

Report format (item_id.rpt):
Fail Occurrence: 3
1: Fail: Worker 1 killed by external signal [9] (matches: Worker.*killed). In line 245, C:\${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log: Monitored WARNING patterns found in verification logs
2: Fail: Out of temporary storage disk space (matches: Out of.*disk space). In line 178, C:\${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log: Monitored WARNING patterns found in verification logs
3: Fail: same label "x" for multiple nets (matches: same label.*multiple nets). In line 312, C:\${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Monitored WARNING patterns found in verification logs
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-12-0-0-33:
  description: "Confirm all Warning message in DFM/FLT log files can be waived. (for SEC process, for others fill N/A)"
  requirements:
    value: 4
    pattern_items:
      - "Worker.*killed"
      - "Out of.*disk space"
      - "same label.*multiple nets"
      - "GDR-[0-9]+"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode
    waive_items:  # IMPORTANT: Use PLAIN STRING format
      - "Explanation: DFM/FLT warning pattern check is informational only"
      - "Note: Pattern mismatches reviewed and acceptable for SEC process"
```

**CRITICAL Behavior (waivers.value=0):**

- waive_items content printed as INFO with [WAIVED_INFO] tag
- ALL warnings force converted: ERROR→INFO with [WAIVED_AS_INFO] tag
- Check ALWAYS returns PASS (warnings shown as INFO for tracking)

**Sample Output (PASS with warnings):**

```
Status: PASS  # Always PASS when waivers.value=0
Reason: All violations waived as informational

Log format (item_id.log):
INFO01:
  - "Explanation: DFM/FLT warning pattern check is informational only"
  - "Note: Pattern mismatches reviewed and acceptable for SEC process"
INFO02:
  - Worker 1 killed by external signal [9] (matches: Worker.*killed)
  - same label "x" for multiple nets (matches: same label.*multiple nets)

Report format (item_id.rpt):
Info Occurrence: 4
1: Info: Explanation: DFM/FLT warning pattern check is informational only. [WAIVED_INFO]
2: Info: Note: Pattern mismatches reviewed and acceptable for SEC process. [WAIVED_INFO]
3: Info: Worker 1 killed by external signal [9] (matches: Worker.*killed). In line 245, C:\${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log: Monitored WARNING patterns found in verification logs [WAIVED_AS_INFO]
4: Info: same label "x" for multiple nets (matches: same label.*multiple nets). In line 312, C:\${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Monitored WARNING patterns found in verification logs [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-12-0-0-33:
  description: "Confirm all Warning message in DFM/FLT log files can be waived. (for SEC process, for others fill N/A)"
  requirements:
    value: 4
    pattern_items:
      - "Worker.*killed"
      - "Out of.*disk space"
      - "same label.*multiple nets"
      - "GDR-[0-9]+"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log"
  waivers:
    value: 3
    waive_items:
      - name: "Worker 1$"  # Exact match Worker ID using regex anchor
        reason: "Waived - Known LSF resource issue on compute node"
      - name: "Worker 11$"  # Another worker ID (anchor prevents matching Worker 1)
        reason: "Waived - Transient network failure during verification"
      - name: "GDR-00003"  # Exact error code match
        reason: "Waived - Known label conflict in legacy design"
```

🛑 CRITICAL: Dual Waiver Matching Strategy

This checker supports TWO types of waiver matching (tried in order):

1. **Source Object Matching (PREFERRED):**

   - Extracts source identifier from warning: "Worker 1 killed" (Source: Worker 1)
   - Matches waive_items.name against source: "Worker 1$" matches source "Worker 1"
   - Use regex anchors for precision: "Worker 1$" won't match "Worker 11"
2. **Full Error Message Regex (FALLBACK):**

   - If source matching fails, matches waive_items.name against complete error message
   - Supports complex patterns: "Terminating run.*unrecoverable" matches full message text
   - Use when source extraction not available or pattern-based waiving needed

Recommended Approach:

- Use source matching when possible (cleaner, more maintainable)
- Use message regex for special cases (complex patterns, no clear source)
- Use $ anchors for exact matches to prevent partial matching issues

**Check Behavior:**
Type 3: Pattern/value check with waiver support.

Searches for WARNING messages matching pattern_items, then applies waiver logic:

- Matches found warnings against waive_items (using dual matching strategy)
- Unwaived warnings → ERROR (need fix)
- Waived warnings → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
  PASS if all found warnings are waived.

**Sample Output (with waived items):**

```
Status: PASS
Reason: All violations waived

Log format (item_id.log):
INFO01:
  - Worker 1 killed by external signal [9] (Source: Worker 1)
  - same label "x" for multiple nets (Source: GDR-00003)
WARN01:
  - Worker 11 (Source: Worker 11)

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Worker 1 killed by external signal [9] (Source: Worker 1). In line 245, C:\${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log: Pegasus verification warnings waived as known issues: Waived - Known LSF resource issue on compute node [WAIVER]
2: Info: same label "x" for multiple nets (Source: GDR-00003). In line 312, C:\${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Pegasus verification warnings waived as known issues: Waived - Known label conflict in legacy design [WAIVER]
Warn Occurrence: 1
1: Warn: Worker 11 (Source: Worker 11). In line 0, item_data.yaml: WARNING found in logs: Waived - Transient network failure during verification [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-12-0-0-33:
  description: "Confirm all Warning message in DFM/FLT log files can be waived. (for SEC process, for others fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log"
  waivers:
    value: 3
    waive_items:
      - name: "Worker 1$"
        reason: "Waived - Known LSF resource issue on compute node"
      - name: "Worker 11$"
        reason: "Waived - Transient network failure during verification"
      - name: "GDR-00003"
        reason: "Waived - Known label conflict in legacy design"
```

⚠️ CRITICAL: Type 4 waive_items format identical to Type 3!

- Same dual waiver matching strategy (source matching + full message regex)
- Same regex anchor recommendations (use $ for exact matches)
- Same waiver reason format

**Check Behavior:**
Type 4: Boolean check with waiver support.

Detects ANY WARNING message (no pattern filtering), then applies waiver logic:

- Matches found warnings against waive_items (using dual matching strategy)
- Unwaived warnings → ERROR
- Waived warnings → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
  PASS if all warnings are waived.

**Sample Output:**

```
Status: PASS
Reason: All items waived

Log format (item_id.log):
INFO01:
  - Worker 1 killed by external signal [9] (Source: Worker 1)
  - same label "x" for multiple nets (Source: GDR-00003)
WARN01:
  - Worker 11 (Source: Worker 11)

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Worker 1 killed by external signal [9] (Source: Worker 1). In line 245, C:\${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvsFLTwD.log: Pegasus verification warnings waived as known issues: Waived - Known LSF resource issue on compute node [WAIVER]
2: Info: same label "x" for multiple nets (Source: GDR-00003). In line 312, C:\${CHECKLIST_ROOT}/IP_project_folder/logs/Pegasus_DFM.log: Pegasus verification warnings waived as known issues: Waived - Known label conflict in legacy design [WAIVER]
Warn Occurrence: 1
1: Warn: Worker 11 (Source: Worker 11). In line 0, item_data.yaml: WARNING found in logs: Waived - Transient network failure during verification [WAIVER]
```
