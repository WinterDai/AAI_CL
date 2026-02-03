# IMP-12-0-0-31: Confirm FLT check result is clean. (for SEC process, for others fill N/A)

## Overview

**Check ID:** IMP-12-0-0-31  
**Description:** Confirm FLT check result is clean. (for SEC process, for others fill N/A)  
**Category:** Physical Verification  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_FLT.sum`

This checker validates that the FLT (Flat Layout Tool) physical verification check results are clean by verifying that all individual rule violations equal zero. It parses the Pegasus FLT summary report to extract violation counts for each rule and ensures no violations exist. The checker is applicable only for SEC process designs; for other processes, this check should be marked as N/A.

---

## Check Logic

### Input Parsing
Parse the Pegasus FLT summary report to extract individual rule violation counts. Each rule entry contains a rule name and total violation count.

**Key Patterns (shared across all types):**
```python
# Pattern 1: Extract rule name and violation count from FLT summary
pattern1 = r'(\S+)\s+\.+\s+Total Result\s+(\d+)\s+\(\s*(\d+)\s*\)'
# Example: "FLTM.Mx.S.1_M1 ............................... Total Result          12 (         0)"
# Captures: rule_name="FLTM.Mx.S.1_M1", total_violations="12", clean_violations="0"
```

### Detection Logic
1. Read the Pegasus FLT summary report file (Pegasus_FLT.sum)
2. Search for rule violation patterns using the regex pattern
3. Extract rule names and their corresponding total violation counts
4. Identify all rules with non-zero violation counts as failures
5. Determine PASS/FAIL: PASS if all rules have 0 violations, FAIL if any rule has violations > 0

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

**Rationale:** This checker validates the status (violation count) of FLT rules. It checks whether each rule has zero violations (clean status). Rules with non-zero violations represent status failures that need to be reported.

---

## Output Descriptions (CRITICAL - Code Generator Uses These!)

This section defines the output strings used by `build_complete_output()` in the checker code.

```python
# Item description for this checker
item_desc = "Confirm FLT check result is clean. (for SEC process, for others fill N/A)"

# PASS case descriptions - Split by Type semantics (API-026)
found_desc_type1_4 = "FLT check result is clean - all rules have 0 violations"
found_desc_type2_3 = "FLT check result is clean - all rules have 0 violations"

# PASS reasons - Split by Type semantics
found_reason_type1_4 = "All FLT rules passed with 0 violations in Pegasus_FLT.sum"
found_reason_type2_3 = "All FLT rules passed with 0 violations in Pegasus_FLT.sum"

# FAIL case descriptions
missing_desc_type1_4 = "FLT check has violations - one or more rules failed"
missing_desc_type2_3 = "FLT check has violations - one or more rules failed"

# FAIL reasons
missing_reason_type1_4 = "FLT rule violations detected in Pegasus_FLT.sum"
missing_reason_type2_3 = "FLT rule violations detected in Pegasus_FLT.sum"

# WAIVED case descriptions
waived_desc = "FLT rule violation waived"
waived_base_reason = "FLT rule violation waived per design team approval"

# UNUSED waivers
unused_desc = "Unused FLT rule waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding FLT rule violation found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "FLT rule: [rule_name] - 0 violations"
  Example: "FLT rule: FLTM.Mx.S.1_M1 - 0 violations"

ERROR01 (Violation/Fail items):
  Format: "FLT rule: [rule_name] - [count] violations"
  Example: "FLT rule: FLTM.Mx.S.1_M1 - 12 violations"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-31:
  description: "Confirm FLT check result is clean. (for SEC process, for others fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_FLT.sum"
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
Reason: All FLT rules passed with 0 violations in Pegasus_FLT.sum

Log format (item_id.log):
INFO01:
  - FLT check result is clean - all rules have 0 violations

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: FLT check result is clean - all rules have 0 violations. In line 1, Pegasus_FLT.sum: All FLT rules passed with 0 violations in Pegasus_FLT.sum
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: FLT rule violations detected in Pegasus_FLT.sum

Log format (item_id.log):
ERROR01:
  - FLT rule: FLTM.Mx.S.1_M1 - 12 violations
  - FLT rule: FLTM.Mx.S.2_M2 - 5 violations

Report format (item_id.rpt):
Fail Occurrence: 2
1: Fail: FLT rule: FLTM.Mx.S.1_M1 - 12 violations. In line 45, Pegasus_FLT.sum: FLT rule violations detected in Pegasus_FLT.sum
2: Fail: FLT rule: FLTM.Mx.S.2_M2 - 5 violations. In line 67, Pegasus_FLT.sum: FLT rule violations detected in Pegasus_FLT.sum
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-31:
  description: "Confirm FLT check result is clean. (for SEC process, for others fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_FLT.sum"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode
    waive_items:  # IMPORTANT: Use PLAIN STRING format
      - "Explanation: FLT violations are informational for non-SEC process designs"
      - "Note: This check is only mandatory for SEC process; other processes can have acceptable violations"
```

**Sample Output (PASS with violations):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All violations waived as informational

Log format (item_id.log):
INFO01:
  - "Explanation: FLT violations are informational for non-SEC process designs"
  - "Note: This check is only mandatory for SEC process; other processes can have acceptable violations"
INFO02:
  - FLT rule: FLTM.Mx.S.1_M1 - 12 violations
  - FLT rule: FLTM.Mx.S.2_M2 - 5 violations

Report format (item_id.rpt):
Info Occurrence: 4
1: Info: Explanation: FLT violations are informational for non-SEC process designs. [WAIVED_INFO]
2: Info: Note: This check is only mandatory for SEC process; other processes can have acceptable violations. [WAIVED_INFO]
3: Info: FLT rule: FLTM.Mx.S.1_M1 - 12 violations. In line 45, Pegasus_FLT.sum: FLT rule violations detected in Pegasus_FLT.sum [WAIVED_AS_INFO]
4: Info: FLT rule: FLTM.Mx.S.2_M2 - 5 violations. In line 67, Pegasus_FLT.sum: FLT rule violations detected in Pegasus_FLT.sum [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-31:
  description: "Confirm FLT check result is clean. (for SEC process, for others fill N/A)"
  requirements:
    value: 3
    pattern_items:
      - "FLTM.Mx.S.1_M1"
      - "FLTM.Mx.S.2_M2"
      - "FLTM.Mx.S.3_M3"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_FLT.sum"
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
Reason: All FLT rules passed with 0 violations in Pegasus_FLT.sum

Log format (item_id.log):
INFO01:
  - FLT rule: FLTM.Mx.S.1_M1 - 0 violations
  - FLT rule: FLTM.Mx.S.2_M2 - 0 violations
  - FLT rule: FLTM.Mx.S.3_M3 - 0 violations

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: FLT rule: FLTM.Mx.S.1_M1 - 0 violations. In line 45, Pegasus_FLT.sum: All FLT rules passed with 0 violations in Pegasus_FLT.sum
2: Info: FLT rule: FLTM.Mx.S.2_M2 - 0 violations. In line 67, Pegasus_FLT.sum: All FLT rules passed with 0 violations in Pegasus_FLT.sum
3: Info: FLT rule: FLTM.Mx.S.3_M3 - 0 violations. In line 89, Pegasus_FLT.sum: All FLT rules passed with 0 violations in Pegasus_FLT.sum
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-31:
  description: "Confirm FLT check result is clean. (for SEC process, for others fill N/A)"
  requirements:
    value: 0
    pattern_items:
      - "FLTM.Mx.S.1_M1"
      - "FLTM.Mx.S.2_M2"
      - "FLTM.Mx.S.3_M3"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_FLT.sum"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode
    waive_items:  # IMPORTANT: Use PLAIN STRING format
      - "Explanation: FLT violations are informational for non-SEC process designs"
      - "Note: Specific rule violations are acceptable for this design configuration"
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
  - "Explanation: FLT violations are informational for non-SEC process designs"
  - "Note: Specific rule violations are acceptable for this design configuration"
INFO02:
  - FLT rule: FLTM.Mx.S.1_M1 - 12 violations
  - FLT rule: FLTM.Mx.S.2_M2 - 5 violations

Report format (item_id.rpt):
Info Occurrence: 4
1: Info: Explanation: FLT violations are informational for non-SEC process designs. [WAIVED_INFO]
2: Info: Note: Specific rule violations are acceptable for this design configuration. [WAIVED_INFO]
3: Info: FLT rule: FLTM.Mx.S.1_M1 - 12 violations. In line 45, Pegasus_FLT.sum: FLT rule violations detected in Pegasus_FLT.sum [WAIVED_AS_INFO]
4: Info: FLT rule: FLTM.Mx.S.2_M2 - 5 violations. In line 67, Pegasus_FLT.sum: FLT rule violations detected in Pegasus_FLT.sum [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-31:
  description: "Confirm FLT check result is clean. (for SEC process, for others fill N/A)"
  requirements:
    value: 3
    pattern_items:
      - "FLTM.Mx.S.1_M1"
      - "FLTM.Mx.S.2_M2"
      - "FLTM.Mx.S.3_M3"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_FLT.sum"
  waivers:
    value: 2
    waive_items:
      - name: "FLTM.Mx.S.1_M1"  # Object NAME to exempt, NOT pattern value
        reason: "Waived - Known issue in legacy IP block, approved by design team"
      - name: "FLTM.Mx.S.2_M2"
        reason: "Waived - False positive due to custom metal stack configuration"
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
  - FLT rule: FLTM.Mx.S.1_M1 - 12 violations
  - FLT rule: FLTM.Mx.S.2_M2 - 5 violations
WARN01:
  - FLTM.Mx.S.4_M4

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: FLT rule: FLTM.Mx.S.1_M1 - 12 violations. In line 45, Pegasus_FLT.sum: FLT rule violation waived per design team approval: Waived - Known issue in legacy IP block, approved by design team [WAIVER]
2: Info: FLT rule: FLTM.Mx.S.2_M2 - 5 violations. In line 67, Pegasus_FLT.sum: FLT rule violation waived per design team approval: Waived - False positive due to custom metal stack configuration [WAIVER]
Warn Occurrence: 1
1: Warn: FLTM.Mx.S.4_M4. In line 0, Pegasus_FLT.sum: Waiver not matched - no corresponding FLT rule violation found: Waived - Obsolete waiver entry [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-31:
  description: "Confirm FLT check result is clean. (for SEC process, for others fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_FLT.sum"
  waivers:
    value: 2
    waive_items:
      - name: "FLTM.Mx.S.1_M1"  # ⚠️ MUST match Type 3 waive_items
        reason: "Waived - Known issue in legacy IP block, approved by design team"
      - name: "FLTM.Mx.S.2_M2"
        reason: "Waived - False positive due to custom metal stack configuration"
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
  - FLT rule: FLTM.Mx.S.1_M1 - 12 violations
  - FLT rule: FLTM.Mx.S.2_M2 - 5 violations
WARN01:
  - FLTM.Mx.S.4_M4

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: FLT rule: FLTM.Mx.S.1_M1 - 12 violations. In line 45, Pegasus_FLT.sum: FLT rule violation waived per design team approval: Waived - Known issue in legacy IP block, approved by design team [WAIVER]
2: Info: FLT rule: FLTM.Mx.S.2_M2 - 5 violations. In line 67, Pegasus_FLT.sum: FLT rule violation waived per design team approval: Waived - False positive due to custom metal stack configuration [WAIVER]
Warn Occurrence: 1
1: Warn: FLTM.Mx.S.4_M4. In line 0, Pegasus_FLT.sum: Waiver not matched - no corresponding FLT rule violation found: Waived - Obsolete waiver entry [WAIVER]
```