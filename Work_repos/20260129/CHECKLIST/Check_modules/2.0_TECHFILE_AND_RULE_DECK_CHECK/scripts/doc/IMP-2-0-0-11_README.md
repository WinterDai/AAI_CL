# IMP-2-0-0-11: List BEOL dummy rule deck name. eg: Dummy_BEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a

## Overview

**Check ID:** IMP-2-0-0-11**Description:** List BEOL dummy rule deck name. eg: Dummy_BEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a**Category:** TECHFILE_AND_RULE_DECK_CHECK**Input Files:**

- `${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\BEOL_pvl.log`

This checker extracts and validates the BEOL (Back-End-Of-Line) dummy fill rule deck name from Pegasus PVL log files. The rule deck name identifies the specific technology node, version, and metal stack configuration used for dummy metal fill operations during physical verification.

---

## Check Logic

### Input Parsing

Parse the Pegasus PVL log file to extract the BEOL dummy rule deck path from `include` statements. The absolute path contains the rule deck filename which serves as the version identifier.

**Key Patterns:**

```python
# Pattern 1: Extract BEOL dummy rule deck name from include statement
pattern1 = r'include\s+"[^"]*/(Dummy_BEOL_Pegasus_[^"]+)"'
# Example: include "/projects/TC73_DDR5_12800_N5P/libs/ruledeck/PEGASUS/DMY/Dummy_BEOL_Pegasus_5nm_014.13_1a.M16"
# Captures: Dummy_BEOL_Pegasus_5nm_014.13_1a.M16
```

**Parsing Strategy:**

1. Open `BEOL_pvl.log` file
2. Scan line-by-line for `include` statements
3. Extract the absolute rule deck path between double quotes
4. Parse the filename component (after last `/` or `\`) as `beol_rule`
5. The `beol_rule` is already an absolute identifier (complete filename)

### Detection Logic

**Type 1/4 (No pattern_items):**

- If `beol_rule` can be successfully extracted and value exists → **PASS**
- Output the extracted `beol_rule` name
- No comparison against golden values needed

**Type 2/3 (With pattern_items):**

- Store `pattern_items[0]` into `golden_beol` (expected rule deck name)
- Compare extracted `beol_rule` against `golden_beol`:
  - If `beol_rule` == `golden_beol` → **PASS**
  - If `beol_rule` != `golden_beol` → **FAIL**
- Output format includes expected value for transparency

**Edge Cases:**

- Multiple include statements: Take first `Dummy_BEOL_Pegasus` match
- Empty or truncated log file: Return ERROR (rule deck not found)
- Different technology nodes (3nm, 5nm, etc.): Pattern captures any node
- Different metal stack configurations (M16, M17, etc.): Pattern captures any stack

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `existence_check`

**Selected Mode for this checker:** `existence_check`

**Rationale:** This checker validates that the BEOL dummy rule deck name exists in the log file and optionally matches the expected golden value. The pattern_items represent the expected rule deck name that SHOULD EXIST in the input file. For Type 1/4, we verify existence only. For Type 2/3, we verify the extracted name matches the expected pattern_items value.

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
item_desc = "List BEOL dummy rule deck name. eg: Dummy_BEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "BEOL dummy rule deck name found in PVL log"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "BEOL dummy rule deck name matched expected pattern"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "BEOL dummy rule deck name successfully extracted from include statement"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "BEOL dummy rule deck name matched and validated against expected golden value"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "BEOL dummy rule deck name not found in PVL log"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "BEOL dummy rule deck name does not match expected pattern"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "BEOL dummy rule deck name not found in include statements or log file is empty"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "BEOL dummy rule deck name does not match expected golden value or pattern not satisfied"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "BEOL dummy rule deck name mismatch waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "BEOL dummy rule deck name mismatch waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries for BEOL rule deck check"
unused_waiver_reason = "Waiver not matched - no corresponding BEOL rule deck mismatch found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "Dummy_BEOL_Pegasus_<tech_node>_<version>_<variant>.<metal_stack>"
  Example: "Dummy_BEOL_Pegasus_5nm_014.13_1a.M16"

ERROR01 (Violation/Fail items):
  Format: "ERROR: BEOL dummy rule deck name not found in log file" (Type 1/4)
          "ERROR: Expected '<golden_beol>' but found '<beol_rule>'" (Type 2/3)
  Example: "ERROR: Expected 'Dummy_BEOL_Pegasus_5nm_014.13_1a.M16' but found 'Dummy_BEOL_Pegasus_5nm_014.11_1a.M16'"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-11:
  description: "List BEOL dummy rule deck name. eg: Dummy_BEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\BEOL_pvl.log"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs existence check - validates that BEOL dummy rule deck name can be extracted from the PVL log file.
PASS if rule deck name is found, FAIL if not found or log file is empty.

**Sample Output (PASS):**

```
Status: PASS
Reason: BEOL dummy rule deck name successfully extracted from include statement
INFO01:
  - Dummy_BEOL_Pegasus_5nm_014.13_1a.M16
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: BEOL dummy rule deck name not found in include statements or log file is empty
ERROR01:
  - ERROR: BEOL dummy rule deck name not found in log file
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-2-0-0-11:
  description: "List BEOL dummy rule deck name. eg: Dummy_BEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\BEOL_pvl.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - BEOL rule deck name is extracted for reference"
      - "Note: Missing rule deck name is acceptable for early design stages without dummy fill"
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
  - "Explanation: This check is informational only - BEOL rule deck name is extracted for reference"
  - "Note: Missing rule deck name is acceptable for early design stages without dummy fill"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - ERROR: BEOL dummy rule deck name not found in log file [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-11:
  description: "List BEOL dummy rule deck name. eg: Dummy_BEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a"
  requirements:
    value: 1
    pattern_items:
      - "Dummy_BEOL_Pegasus_5nm_014.13_1a.M16"  # Expected BEOL rule deck name
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\BEOL_pvl.log"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 searches pattern_items in input files and validates the extracted BEOL rule deck name matches the expected golden value.
PASS if extracted `beol_rule` matches `pattern_items[0]` (golden_beol), FAIL if mismatch or not found.

**Sample Output (PASS):**

```
Status: PASS
Reason: BEOL dummy rule deck name matched and validated against expected golden value
INFO01:
  - Dummy_BEOL_Pegasus_5nm_014.13_1a.M16 (Expected: Dummy_BEOL_Pegasus_5nm_014.13_1a.M16)
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: BEOL dummy rule deck name does not match expected golden value or pattern not satisfied
ERROR01:
  - ERROR: Expected 'Dummy_BEOL_Pegasus_5nm_014.13_1a.M16' but found 'Dummy_BEOL_Pegasus_5nm_014.11_1a.M16'
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-2-0-0-11:
  description: "List BEOL dummy rule deck name. eg: Dummy_BEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a"
  requirements:
    value: 1
    pattern_items:
      - "Dummy_BEOL_Pegasus_5nm_014.13_1a.M16"
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\BEOL_pvl.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: BEOL rule deck version mismatch is acceptable for this design phase"
      - "Note: Using legacy rule deck version approved by design team for compatibility"
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
  - "Explanation: BEOL rule deck version mismatch is acceptable for this design phase"
  - "Note: Using legacy rule deck version approved by design team for compatibility"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - ERROR: Expected 'Dummy_BEOL_Pegasus_5nm_014.13_1a.M16' but found 'Dummy_BEOL_Pegasus_5nm_014.11_1a.M16' [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-11:
  description: "List BEOL dummy rule deck name. eg: Dummy_BEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a"
  requirements:
    value: 1
    pattern_items:
      - "Dummy_BEOL_Pegasus_5nm_014.13_1a.M16"  # Expected BEOL rule deck name
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\BEOL_pvl.log"
  waivers:
    value: 2
    waive_items:
      - name: "Dummy_BEOL_Pegasus_5nm_014.11_1a.M16"  # Legacy version waived
        reason: "Waived - legacy BEOL rule deck version approved for this design per team agreement"
      - name: "Dummy_BEOL_Pegasus_5nm_014.12_1a.M16"  # Intermediate version waived
        reason: "Waived - intermediate version used for compatibility with existing tapeout flow"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:

- Match found mismatches against waive_items
- Unwaived mismatches → ERROR (need fix)
- Waived mismatches → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
  PASS if all mismatches are waived.

**Sample Output (with waived items):**

```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - Dummy_BEOL_Pegasus_5nm_014.11_1a.M16 (Expected: Dummy_BEOL_Pegasus_5nm_014.13_1a.M16) [WAIVER]
WARN01 (Unused Waivers):
  - Dummy_BEOL_Pegasus_5nm_014.12_1a.M16: Waiver not matched - no corresponding BEOL rule deck mismatch found
```

**Sample Output (with unwaived violations):**

```
Status: FAIL
Reason: BEOL dummy rule deck name does not match expected golden value or pattern not satisfied
ERROR01:
  - ERROR: Expected 'Dummy_BEOL_Pegasus_5nm_014.13_1a.M16' but found 'Dummy_BEOL_Pegasus_5nm_014.10_1a.M16'
INFO01 (Waived):
  - (none)
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-11:
  description: "List BEOL dummy rule deck name. eg: Dummy_BEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\BEOL_pvl.log"
  waivers:
    value: 2
    waive_items:
      - name: "Dummy_BEOL_Pegasus_5nm_014.11_1a.M16"  # Legacy version waived
        reason: "Waived - legacy BEOL rule deck version approved for this design per team agreement"
      - name: "Dummy_BEOL_Pegasus_5nm_014.12_1a.M16"  # Intermediate version waived
        reason: "Waived - intermediate version used for compatibility with existing tapeout flow"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!

- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3
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
INFO01 (Waived):
  - Dummy_BEOL_Pegasus_5nm_014.11_1a.M16 [WAIVER]
WARN01 (Unused Waivers):
  - Dummy_BEOL_Pegasus_5nm_014.12_1a.M16: Waiver not matched - no corresponding BEOL rule deck mismatch found
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 2.0_TECHFILE_AND_RULE_DECK_CHECK --checkers IMP-2-0-0-11 --force

# Run individual tests
python IMP-2-0-0-11.py
```

---

## Notes

**Technology Node Support:**

- Pattern supports any technology node (3nm, 5nm, 7nm, etc.)
- Captures version numbers in format: `<major>.<minor>_<variant>`
- Metal stack identifier captured (e.g., M16, M17, M11)

**Version Format:**

- Standard format: `Dummy_BEOL_Pegasus_<node>_<version>_<variant>.<metal_stack>`
- Example: `Dummy_BEOL_Pegasus_5nm_014.13_1a.M16`
  - Node: 5nm
  - Version: 014.13
  - Variant: 1a
  - Metal Stack: M16

**Limitations:**

- Only extracts the first matching `Dummy_BEOL_Pegasus` include statement
- Assumes standard Pegasus PVL log format with include statements
- Does not validate rule deck file existence, only extracts the name

**Known Issues:**

- If multiple BEOL rule decks are included, only the first one is reported
- Compressed or encrypted rule deck paths may have different naming conventions
