# IMP-12-0-0-30: Confirm DFM check result is clean. (for SEC process, for others fill N/A)

## Overview

**Check ID:** IMP-12-0-0-30  
**Description:** Confirm DFM check result is clean. (for SEC process, for others fill N/A)  
**Category:** Physical Verification  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_DFM.sum`

This checker validates that all DFM (Design for Manufacturing) rule checks in the Pegasus DFM summary report have zero violations. It parses the DFM summary file to extract individual rule violation counts and ensures all rules pass cleanly. This is critical for SEC process designs to meet manufacturing requirements and prevent yield issues.

---

## Check Logic

### Input Parsing
Parse the Pegasus DFM summary report to extract individual DFM rule check results. Each rule line contains the rule name and total violation count.

**Key Patterns (shared across all types):**
```python
# Pattern 1: DFM rule check result line with violation count
pattern1 = r'RULECHECK\s+(\S+)\s+\.+\s+Total Result\s+(\d+)\s+\(\s*(\d+)\)'
# Example: "RULECHECK PM_M2_C_3 .................................... Total Result        579 (       579)"
# Captures: rule_name="PM_M2_C_3", total_violations="579"
```

### Detection Logic
1. Read the Pegasus DFM summary file (Pegasus_DFM.sum)
2. Search for all RULECHECK lines using the pattern above
3. Extract rule names and their violation counts
4. Identify rules with non-zero violations (violations > 0)
5. Determine PASS/FAIL:
   - PASS: All DFM rules have 0 violations
   - FAIL: One or more DFM rules have violations > 0

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

**Rationale:** This checker validates the status (violation count = 0) of all DFM rules found in the report. It checks whether each rule has clean status (zero violations). Rules with violations are reported as failures.

---

## Output Descriptions (CRITICAL - Code Generator Uses These!)

This section defines the output strings used by `build_complete_output()` in the checker code.

```python
# Item description for this checker
item_desc = "Confirm DFM check result is clean. (for SEC process, for others fill N/A)"

# PASS case descriptions - Split by Type semantics (API-026)
found_desc_type1_4 = "All DFM rules passed with zero violations"
found_desc_type2_3 = "All DFM rules clean (0 violations)"

# PASS reasons - Split by Type semantics
found_reason_type1_4 = "All DFM rule checks in Pegasus_DFM.sum report have zero violations"
found_reason_type2_3 = "All DFM rule checks validated with zero violations in Pegasus_DFM.sum"

# FAIL case descriptions
missing_desc_type1_4 = "DFM violations detected in Pegasus report"
missing_desc_type2_3 = "DFM rule violations found (rules with non-zero violations)"

# FAIL reasons
missing_reason_type1_4 = "One or more DFM rules have violations in Pegasus_DFM.sum report"
missing_reason_type2_3 = "DFM rule check failed with violations in Pegasus_DFM.sum"

# WAIVED case descriptions
waived_desc = "DFM rule violations waived"
waived_base_reason = "DFM rule violations waived per design team approval"

# UNUSED waivers
unused_desc = "Unused DFM rule waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding DFM rule violation found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "DFM rule: [rule_name] - 0 violations"
  Example: "DFM rule: PM_M2_C_3 - 0 violations"

ERROR01 (Violation/Fail items):
  Format: "DFM rule: [rule_name] - [count] violations"
  Example: "DFM rule: PM_M2_C_3 - 579 violations"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-30:
  description: "Confirm DFM check result is clean. (for SEC process, for others fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_DFM.sum"
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
Reason: All DFM rule checks in Pegasus_DFM.sum report have zero violations

Log format (item_id.log):
INFO01:
  - DFM rule: PM_M2_C_3 - 0 violations
  - DFM rule: PM_M3_C_1 - 0 violations

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: DFM rule: PM_M2_C_3 - 0 violations. In line 45, Pegasus_DFM.sum: All DFM rule checks in Pegasus_DFM.sum report have zero violations
2: Info: DFM rule: PM_M3_C_1 - 0 violations. In line 67, Pegasus_DFM.sum: All DFM rule checks in Pegasus_DFM.sum report have zero violations
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: One or more DFM rules have violations in Pegasus_DFM.sum report

Log format (item_id.log):
ERROR01:
  - DFM rule: PM_M2_C_3 - 579 violations
  - DFM rule: PM_M5_C_2 - 123 violations

Report format (item_id.rpt):
Fail Occurrence: 2
1: Fail: DFM rule: PM_M2_C_3 - 579 violations. In line 45, Pegasus_DFM.sum: One or more DFM rules have violations in Pegasus_DFM.sum report
2: Fail: DFM rule: PM_M5_C_2 - 123 violations. In line 89, Pegasus_DFM.sum: One or more DFM rules have violations in Pegasus_DFM.sum report
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-30:
  description: "Confirm DFM check result is clean. (for SEC process, for others fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_DFM.sum"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode
    waive_items:  # IMPORTANT: Use PLAIN STRING format
      - "Explanation: DFM violations are informational for non-SEC process designs"
      - "Note: DFM checks are optional for this design phase"
```

**Sample Output (PASS with violations):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All violations waived as informational

Log format (item_id.log):
INFO01:
  - "Explanation: DFM violations are informational for non-SEC process designs"
  - "Note: DFM checks are optional for this design phase"
INFO02:
  - DFM rule: PM_M2_C_3 - 579 violations
  - DFM rule: PM_M5_C_2 - 123 violations

Report format (item_id.rpt):
Info Occurrence: 4
1: Info: Explanation: DFM violations are informational for non-SEC process designs. [WAIVED_INFO]
2: Info: Note: DFM checks are optional for this design phase. [WAIVED_INFO]
3: Info: DFM rule: PM_M2_C_3 - 579 violations. In line 45, Pegasus_DFM.sum: One or more DFM rules have violations in Pegasus_DFM.sum report [WAIVED_AS_INFO]
4: Info: DFM rule: PM_M5_C_2 - 123 violations. In line 89, Pegasus_DFM.sum: One or more DFM rules have violations in Pegasus_DFM.sum report [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-30:
  description: "Confirm DFM check result is clean. (for SEC process, for others fill N/A)"
  requirements:
    value: 3
    pattern_items:
      - "PM_M2_C_3"
      - "PM_M3_C_1"
      - "PM_M5_C_2"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_DFM.sum"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- If description contains "version": Use VERSION IDENTIFIERS ONLY (e.g., "22.11-s119_1")
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
Reason: All DFM rule checks validated with zero violations in Pegasus_DFM.sum

Log format (item_id.log):
INFO01:
  - DFM rule: PM_M2_C_3 - 0 violations
  - DFM rule: PM_M3_C_1 - 0 violations
  - DFM rule: PM_M5_C_2 - 0 violations

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: DFM rule: PM_M2_C_3 - 0 violations. In line 45, Pegasus_DFM.sum: All DFM rule checks validated with zero violations in Pegasus_DFM.sum
2: Info: DFM rule: PM_M3_C_1 - 0 violations. In line 67, Pegasus_DFM.sum: All DFM rule checks validated with zero violations in Pegasus_DFM.sum
3: Info: DFM rule: PM_M5_C_2 - 0 violations. In line 89, Pegasus_DFM.sum: All DFM rule checks validated with zero violations in Pegasus_DFM.sum
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-30:
  description: "Confirm DFM check result is clean. (for SEC process, for others fill N/A)"
  requirements:
    value: 0
    pattern_items:
      - "PM_M2_C_3"
      - "PM_M3_C_1"
      - "PM_M5_C_2"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_DFM.sum"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode
    waive_items:  # IMPORTANT: Use PLAIN STRING format
      - "Explanation: DFM violations are informational for non-SEC process designs"
      - "Note: Specific DFM rules may have acceptable violations in early design stages"
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
  - "Explanation: DFM violations are informational for non-SEC process designs"
  - "Note: Specific DFM rules may have acceptable violations in early design stages"
INFO02:
  - DFM rule: PM_M2_C_3 - 579 violations
  - DFM rule: PM_M5_C_2 - 123 violations

Report format (item_id.rpt):
Info Occurrence: 4
1: Info: Explanation: DFM violations are informational for non-SEC process designs. [WAIVED_INFO]
2: Info: Note: Specific DFM rules may have acceptable violations in early design stages. [WAIVED_INFO]
3: Info: DFM rule: PM_M2_C_3 - 579 violations. In line 45, Pegasus_DFM.sum: DFM rule check failed with violations in Pegasus_DFM.sum [WAIVED_AS_INFO]
4: Info: DFM rule: PM_M5_C_2 - 123 violations. In line 89, Pegasus_DFM.sum: DFM rule check failed with violations in Pegasus_DFM.sum [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-30:
  description: "Confirm DFM check result is clean. (for SEC process, for others fill N/A)"
  requirements:
    value: 3
    pattern_items:
      - "PM_M2_C_3"
      - "PM_M3_C_1"
      - "PM_M5_C_2"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_DFM.sum"
  waivers:
    value: 2
    waive_items:
      - name: "PM_M2_C_3"  # Object NAME to exempt, NOT pattern value
        reason: "Waived - Known issue in legacy IP block, acceptable for this design"
      - name: "PM_M5_C_2"
        reason: "Waived - Manufacturing team approved deviation for this metal layer"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:
- BOTH must be at SAME semantic level as description!
- pattern_items = VALUES to match (versions, status, conditions)
- waive_items.name = OBJECT NAMES to exempt (libraries, modules, views, files)

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

Log format (item_id.log):
INFO01:
  - DFM rule: PM_M2_C_3 - 579 violations
  - DFM rule: PM_M5_C_2 - 123 violations
WARN01:
  - (No unused waivers in this example)

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: DFM rule: PM_M2_C_3 - 579 violations. In line 45, Pegasus_DFM.sum: DFM rule violations waived per design team approval: Waived - Known issue in legacy IP block, acceptable for this design [WAIVER]
2: Info: DFM rule: PM_M5_C_2 - 123 violations. In line 89, Pegasus_DFM.sum: DFM rule violations waived per design team approval: Waived - Manufacturing team approved deviation for this metal layer [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-30:
  description: "Confirm DFM check result is clean. (for SEC process, for others fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_DFM.sum"
  waivers:
    value: 2
    waive_items:
      - name: "PM_M2_C_3"  # ⚠️ MUST match Type 3 waive_items
        reason: "Waived - Known issue in legacy IP block, acceptable for this design"
      - name: "PM_M5_C_2"
        reason: "Waived - Manufacturing team approved deviation for this metal layer"
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

Log format (item_id.log):
INFO01:
  - DFM rule: PM_M2_C_3 - 579 violations
  - DFM rule: PM_M5_C_2 - 123 violations
WARN01:
  - (No unused waivers in this example)

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: DFM rule: PM_M2_C_3 - 579 violations. In line 45, Pegasus_DFM.sum: DFM rule violations waived per design team approval: Waived - Known issue in legacy IP block, acceptable for this design [WAIVER]
2: Info: DFM rule: PM_M5_C_2 - 123 violations. In line 89, Pegasus_DFM.sum: DFM rule violations waived per design team approval: Waived - Manufacturing team approved deviation for this metal layer [WAIVER]
```