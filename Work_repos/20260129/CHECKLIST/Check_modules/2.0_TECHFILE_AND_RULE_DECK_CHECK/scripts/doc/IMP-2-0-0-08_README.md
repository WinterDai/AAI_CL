# IMP-2-0-0-08: Confirm latest BUMP rule deck(s) was used? List BUMP rule deck name in Comments. eg: PN3_CU_ROUND_BUMP_ON_PAD_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_003.10a

## Overview

**Check ID:** IMP-2-0-0-08  
**Description:** Confirm latest BUMP rule deck(s) was used? List BUMP rule deck name in Comments. eg: PN3_CU_ROUND_BUMP_ON_PAD_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_003.10a  
**Category:** TECHFILE_AND_RULE_DECK_CHECK  
**Input Files:** ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\BUMP_pvl.log

This checker validates that the correct BUMP DRC rule deck version was used during physical verification. It extracts the rule deck path from the BUMP_pvl.log file, parses the rule deck document name and version from the rule deck file itself, and compares against expected values. The checker ensures design compliance with the latest approved BUMP rule deck specifications.

---

## Check Logic

### Input Parsing

**Step 1: Parse BUMP DRC Log File (BUMP_pvl.log)**

Extract the rule deck path from the include statement in the log file. The path is stored as an absolute path that can be directly used for parsing the rule deck file.

**Key Patterns:**

```python
# Pattern 1: Extract BUMP rule deck path from include statement
pattern_include = r'include\s+"([^"]+)"'
# Example: include "C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PN5_CU_BUMP_030.10_1a"
# Extraction: Group 1 = Full absolute path to rule deck file
```

**Step 2: Parse Rule Deck File**

Using the extracted `rule_path`, parse the rule deck file to extract document name and version.

```python
# Pattern 2: Extract document name and version from rule deck header
pattern_doc_ver = r'DRC\s+COMMAND\s+FILE\s+DOCUMENT:\s*(\S+)\s+VER\s+(\S+)'
# Example: DRC COMMAND FILE DOCUMENT: T-000-BP-DR-030-N1 VER 1.0_1a
# Extraction: Group 1 = current_doc (T-000-BP-DR-030-N1)
#            Group 2 = current_ver (1.0_1a)
```

**Parsing Strategy:**
1. Read BUMP_pvl.log line by line to find the include statement
2. Extract the absolute rule deck path (stored as `rule_path`)
3. Open the rule deck file at `rule_path`
4. Search for the "DRC COMMAND FILE DOCUMENT" line
5. Extract `current_doc` (document name before "VER")
6. Extract `current_ver` (version after "VER")
7. Store all three values: `rule_path`, `current_doc`, `current_ver`

**Edge Cases:**
- Multiple include statements: Take the first BUMP-specific one (contains path ending with rule deck name)
- Windows vs Linux path separators: Handle both backslash and forward slash
- Missing include statement: Flag as FAIL (no rule deck found)
- Missing DRC COMMAND FILE DOCUMENT line: Flag as FAIL (cannot extract version)
- Commented out include lines: Ignore lines starting with # or //

### Detection Logic

**Type 1/4 (Boolean Check - No pattern_items):**

1. Check if `rule_path` was successfully extracted from BUMP_pvl.log
2. Check if `current_doc` was successfully extracted from rule deck file
3. Check if `current_ver` was successfully extracted from rule deck file
4. **PASS Condition:** All three values (`rule_path`, `current_doc`, `current_ver`) exist and are non-empty
5. **FAIL Condition:** Any of the three values cannot be extracted or is empty

**Type 2/3 (Value Check - With pattern_items):**

1. Extract `rule_path`, `current_doc`, `current_ver` as in Type 1/4
2. Store `pattern_items[0]` into `latest_doc` (expected document name)
3. Store `pattern_items[1]` into `latest_ver` (expected version)
4. **PASS Condition:** `current_doc` == `latest_doc` AND `current_ver` == `latest_ver`
5. **FAIL Condition:** `current_doc` != `latest_doc` OR `current_ver` != `latest_ver`

**Validation Steps:**
- Verify rule deck path is accessible (file exists)
- Confirm document name matches expected pattern format (e.g., T-000-BP-DR-XXX-N#)
- Validate version format (e.g., #.#_#a)
- For Type 2/3: Exact string match between current and expected values

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

**Rationale:** This checker validates that the BUMP rule deck document and version match expected values (pattern_items). The checker extracts the current document/version from files and compares against the expected document/version specified in pattern_items. Only the matched rule deck is output - if the document/version matches, it's a PASS (found_items); if it doesn't match, it's a FAIL (missing_items). This is a status validation check, not an existence check.

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
item_desc = "Confirm latest BUMP rule deck(s) was used? List BUMP rule deck name in Comments. eg: PN3_CU_ROUND_BUMP_ON_PAD_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_003.10a"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "BUMP rule deck information found and extracted successfully"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "BUMP rule deck version matched expected specification"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Rule deck path, document name, and version successfully extracted from BUMP_pvl.log and rule deck file"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Current rule deck document and version matched expected values - using approved BUMP rule deck"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "BUMP rule deck information not found or incomplete"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "BUMP rule deck version does not match expected specification"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Failed to extract rule deck path, document name, or version from input files - verify BUMP_pvl.log contains valid include statement and rule deck file is accessible"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Current rule deck document or version does not match expected values - incorrect BUMP rule deck version in use"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "BUMP rule deck version mismatch waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "BUMP rule deck version mismatch waived per project approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused BUMP rule deck waiver entry"
unused_waiver_reason = "Waiver entry not matched - no corresponding rule deck version mismatch found"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [rule_deck_path] ([current_document], [current_version])"
  Example: "- C:\...\ruledeck\2.0\PN5_CU_BUMP_030.10_1a (T-000-BP-DR-030-N1, 1.0_1a)"

ERROR01 (Violation/Fail items):
  Format: "- [rule_deck_path] ([current_document], [current_version]): Expected ([latest_document], [latest_version])"
  Example: "- C:\...\ruledeck\2.0\PN5_CU_BUMP_030.10_1a (T-000-BP-DR-030-N1, 1.0_1a): Expected (T-000-BP-DR-030-N1, 2.0_1a)"
```

Note: For Type 1/4 (no pattern_items), only the current values are displayed. For Type 2/3 (with pattern_items), both current and expected values are shown in FAIL cases.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-08:
  description: "Confirm latest BUMP rule deck(s) was used? List BUMP rule deck name in Comments. eg: PN3_CU_ROUND_BUMP_ON_PAD_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_003.10a"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\BUMP_pvl.log
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs boolean validation that BUMP rule deck information can be extracted. Checks if rule_path, current_doc, and current_ver are all successfully parsed from input files. PASS if all three values exist and are non-empty; FAIL if any value is missing or cannot be extracted.

**Sample Output (PASS):**
```
Status: PASS
Reason: Rule deck path, document name, and version successfully extracted from BUMP_pvl.log and rule deck file

Log format (CheckList.rpt):
INFO01:
  - C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PN5_CU_BUMP_030.10_1a (T-000-BP-DR-030-N1, 1.0_1a)

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: PN5_CU_BUMP_030.10_1a. In line 1, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PN5_CU_BUMP_030.10_1a: Rule deck path, document name, and version successfully extracted from BUMP_pvl.log and rule deck file
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Failed to extract rule deck path, document name, or version from input files - verify BUMP_pvl.log contains valid include statement and rule deck file is accessible

Log format (CheckList.rpt):
ERROR01:
  - BUMP rule deck information missing

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: BUMP_pvl.log. In line 0, ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\BUMP_pvl.log: Failed to extract rule deck path, document name, or version from input files - verify BUMP_pvl.log contains valid include statement and rule deck file is accessible
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-2-0-0-08:
  description: "Confirm latest BUMP rule deck(s) was used? List BUMP rule deck name in Comments. eg: PN3_CU_ROUND_BUMP_ON_PAD_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_003.10a"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\BUMP_pvl.log
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: BUMP rule deck extraction is informational only for this project phase"
      - "Note: Rule deck version validation will be enforced in final signoff"
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
  - "Explanation: BUMP rule deck extraction is informational only for this project phase"
  - "Note: Rule deck version validation will be enforced in final signoff"
INFO02:
  - BUMP rule deck information missing

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Waiver Comment. [WAIVED_INFO]: Explanation: BUMP rule deck extraction is informational only for this project phase
2: Info: BUMP_pvl.log. In line 0, ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\BUMP_pvl.log: Failed to extract rule deck path, document name, or version from input files - verify BUMP_pvl.log contains valid include statement and rule deck file is accessible [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-08:
  description: "Confirm latest BUMP rule deck(s) was used? List BUMP rule deck name in Comments. eg: PN3_CU_ROUND_BUMP_ON_PAD_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_003.10a"
  requirements:
    value: 2
    pattern_items:
      - "T-000-BP-DR-030-N1"  # Expected document name
      - "1.0_1a"              # Expected version
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\BUMP_pvl.log
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- pattern_items[0] = Expected BUMP rule deck DOCUMENT NAME (e.g., "T-000-BP-DR-030-N1")
- pattern_items[1] = Expected BUMP rule deck VERSION (e.g., "1.0_1a")
- These are the golden values extracted from the "DRC COMMAND FILE DOCUMENT" line
- NOT the full rule deck filename (e.g., NOT "PN5_CU_BUMP_030.10_1a")
- Match the semantic level: document identifier + version identifier

**Check Behavior:**
Type 2 extracts current_doc and current_ver from files, then compares against pattern_items (latest_doc and latest_ver). PASS if current values match expected values exactly; FAIL if there's any mismatch. This validates that the correct approved BUMP rule deck version is in use.

**Sample Output (PASS):**
```
Status: PASS
Reason: Current rule deck document and version matched expected values - using approved BUMP rule deck

Log format (CheckList.rpt):
INFO01:
  - C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PN5_CU_BUMP_030.10_1a (T-000-BP-DR-030-N1, 1.0_1a)

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: PN5_CU_BUMP_030.10_1a. In line 1, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PN5_CU_BUMP_030.10_1a: Current rule deck document and version matched expected values - using approved BUMP rule deck
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Current rule deck document or version does not match expected values - incorrect BUMP rule deck version in use

Log format (CheckList.rpt):
ERROR01:
  - C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PN5_CU_BUMP_030.10_1a (T-000-BP-DR-030-N1, 0.9_1a): Expected (T-000-BP-DR-030-N1, 1.0_1a)

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: PN5_CU_BUMP_030.10_1a. In line 1, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PN5_CU_BUMP_030.10_1a: Current rule deck document or version does not match expected values - incorrect BUMP rule deck version in use. Expected: (T-000-BP-DR-030-N1, 1.0_1a), Found: (T-000-BP-DR-030-N1, 0.9_1a)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-2-0-0-08:
  description: "Confirm latest BUMP rule deck(s) was used? List BUMP rule deck name in Comments. eg: PN3_CU_ROUND_BUMP_ON_PAD_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_003.10a"
  requirements:
    value: 2
    pattern_items:
      - "T-000-BP-DR-030-N1"
      - "1.0_1a"
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\BUMP_pvl.log
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: BUMP rule deck version check is informational during development phase"
      - "Note: Older rule deck versions are acceptable for early design iterations"
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
  - "Explanation: BUMP rule deck version check is informational during development phase"
  - "Note: Older rule deck versions are acceptable for early design iterations"
INFO02:
  - C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PN5_CU_BUMP_030.10_1a (T-000-BP-DR-030-N1, 0.9_1a): Expected (T-000-BP-DR-030-N1, 1.0_1a)

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Waiver Comment. [WAIVED_INFO]: Explanation: BUMP rule deck version check is informational during development phase
2: Info: PN5_CU_BUMP_030.10_1a. In line 1, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PN5_CU_BUMP_030.10_1a: Current rule deck document or version does not match expected values - incorrect BUMP rule deck version in use. Expected: (T-000-BP-DR-030-N1, 1.0_1a), Found: (T-000-BP-DR-030-N1, 0.9_1a) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-08:
  description: "Confirm latest BUMP rule deck(s) was used? List BUMP rule deck name in Comments. eg: PN3_CU_ROUND_BUMP_ON_PAD_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_003.10a"
  requirements:
    value: 2
    pattern_items:
      - "T-000-BP-DR-030-N1"  # Expected document name (GOLDEN VALUE)
      - "1.0_1a"              # Expected version (GOLDEN VALUE)
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\BUMP_pvl.log
  waivers:
    value: 2
    waive_items:
      - name: "PN5_CU_BUMP_030.10_1a"  # Rule deck NAME to exempt (EXEMPTION OBJECT)
        reason: "This version can be accepted for this project"
      - name: "PN5_CU_BUMP_029.05_1b"  # Another rule deck NAME to exempt
        reason: "Legacy version approved for backward compatibility testing"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support. Extracts current_doc and current_ver, compares against pattern_items. If mismatch found, checks if the rule deck name is in waive_items. Unwaived mismatches → ERROR; Waived mismatches → INFO with [WAIVER] tag; Unused waivers → WARN with [WAIVER] tag. PASS if all mismatches are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived

Log format (CheckList.rpt):
INFO01:
  - PN5_CU_BUMP_030.10_1a (T-000-BP-DR-030-N1, 0.9_1a): Expected (T-000-BP-DR-030-N1, 1.0_1a)
WARN01:
  - PN5_CU_BUMP_029.05_1b

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: PN5_CU_BUMP_030.10_1a. In line 1, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PN5_CU_BUMP_030.10_1a: BUMP rule deck version mismatch waived per project approval: This version can be accepted for this project [WAIVER]
Warn Occurrence: 1
1: Warn: PN5_CU_BUMP_029.05_1b. In line 0, waiver_config: Waiver entry not matched - no corresponding rule deck version mismatch found: Legacy version approved for backward compatibility testing [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-08:
  description: "Confirm latest BUMP rule deck(s) was used? List BUMP rule deck name in Comments. eg: PN3_CU_ROUND_BUMP_ON_PAD_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_003.10a"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\BUMP_pvl.log
  waivers:
    value: 2
    waive_items:
      - name: "PN5_CU_BUMP_030.10_1a"  # ⚠️ MUST match Type 3 waive_items
        reason: "This version can be accepted for this project"
      - name: "PN5_CU_BUMP_029.05_1b"  # ⚠️ MUST match Type 3 waive_items
        reason: "Legacy version approved for backward compatibility testing"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (keep exemption object names consistent)
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support. Performs boolean check (extraction validation) without pattern_items. If extraction fails, checks if the rule deck name is in waive_items. Unwaived failures → ERROR; Waived failures → INFO with [WAIVER] tag; Unused waivers → WARN with [WAIVER] tag. PASS if all failures are waived.

**Sample Output:**
```
Status: PASS
Reason: All items waived

Log format (CheckList.rpt):
INFO01:
  - PN5_CU_BUMP_030.10_1a
WARN01:
  - PN5_CU_BUMP_029.05_1b

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: PN5_CU_BUMP_030.10_1a. In line 1, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PN5_CU_BUMP_030.10_1a: BUMP rule deck version mismatch waived per project approval: This version can be accepted for this project [WAIVER]
Warn Occurrence: 1
1: Warn: PN5_CU_BUMP_029.05_1b. In line 0, waiver_config: Waiver entry not matched - no corresponding rule deck version mismatch found: Legacy version approved for backward compatibility testing [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 2.0_TECHFILE_AND_RULE_DECK_CHECK --checkers IMP-2-0-0-08 --force

# Run individual tests
python IMP-2-0-0-08.py
```

---

## Notes

**Implementation Notes:**
- The checker performs two-stage parsing: first extracts rule deck path from log, then parses the rule deck file itself
- Rule deck path is stored as absolute path and can be directly used for file access
- Document name and version extraction relies on specific format: "DRC COMMAND FILE DOCUMENT: <doc> VER <ver>"
- For Type 2/3, pattern_items[0] is the expected document name, pattern_items[1] is the expected version
- Waiver matching (Type 3/4) uses the rule deck filename (e.g., "PN5_CU_BUMP_030.10_1a") as the exemption object name

**Known Limitations:**
- Assumes single BUMP rule deck per log file (takes first include statement)
- Requires exact format match for "DRC COMMAND FILE DOCUMENT" line
- Case-sensitive string matching for document and version comparison
- Does not validate rule deck content beyond document/version extraction

**Edge Cases:**
- If BUMP_pvl.log contains multiple include statements, only the first is processed
- If rule deck file is inaccessible, checker will FAIL with appropriate error message
- Empty or malformed rule deck files will result in extraction failure
- Waiver matching is based on rule deck filename, not full path