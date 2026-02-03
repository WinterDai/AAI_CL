# IMP-2-0-0-06: Confirm latest LVS rule deck(s) was used? List LVS rule deck name in Comments. eg: DFM_LVS_RC_PEGASUS_N3P_1p17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2R_ALRDL.1.0a

## Overview

**Check ID:** IMP-2-0-0-06  
**Description:** Confirm latest LVS rule deck(s) was used? List LVS rule deck name in Comments. eg: DFM_LVS_RC_PEGASUS_N3P_1p17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2R_ALRDL.1.0a  
**Category:** TECHFILE_AND_RULE_DECK_CHECK  
**Input Files:** ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\LVS_pvl.log

This checker validates that the correct LVS rule deck version is used in the Pegasus LVS flow. It extracts the rule deck path from the LVS PVL log file, parses the rule deck file to obtain document name and version information, and compares against expected values. The checker ensures design verification uses approved rule deck versions and provides traceability by listing the actual rule deck name in comments.

---

## Check Logic

### Input Parsing

**Step 1: Extract Rule Deck Path from LVS Log**
Parse `LVS_pvl.log` to find the include statement containing the DFM_LVS rule deck path.

**Key Patterns:**
```python
# Pattern 1: Extract LVS rule deck absolute path from include statement
pattern_rule_path = r'include\s+"([^"]+DFM_LVS[^"]+)"'
# Example: include "C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2b"
# Extracts: Full absolute path to rule deck file
```

**Step 2: Parse Rule Deck File for Document and Version**
Using the extracted `rule_path`, parse the rule deck file to extract metadata.

```python
# Pattern 2: Extract document name from rule deck file
pattern_document = r'COMMAND FILE DOCUMENT:\s*(.+)'
# Example: COMMAND FILE DOCUMENT: T-N05-CL-LS-007-N1
# Extracts: current_doc = "T-N05-CL-LS-007-N1"

# Pattern 3: Extract version from rule deck file
pattern_version = r'COMMAND FILE VERSION:\s*(.+)'
# Example: COMMAND FILE VERSION: 1.2b
# Extracts: current_ver = "1.2b"
```

**Parsing Strategy:**
1. Read LVS_pvl.log line by line to find include statement with "*DFM_LVS*" pattern
2. Extract absolute path and store in `rule_path` variable
3. Open rule deck file at `rule_path` (already absolute, no path resolution needed)
4. Parse rule deck file to extract `current_doc` from "COMMAND FILE DOCUMENT:" line
5. Parse rule deck file to extract `current_ver` from "COMMAND FILE VERSION:" line
6. Store all three values (`rule_path`, `current_doc`, `current_ver`) for validation

**Edge Cases:**
- Multiple include statements: Extract all DFM_LVS rule decks
- Windows vs Unix path separators: Handle both backslash and forward slash
- Missing include statement: Report as FAIL
- Rule deck file not found at extracted path: Report as FAIL
- Missing COMMAND FILE metadata in rule deck: Report as FAIL

### Detection Logic

**Type 1/4 (Boolean Check - No pattern_items):**
- If `rule_path`, `current_doc`, `current_ver` are all successfully extracted and have non-empty values → **PASS**
- If any of `rule_path`, `current_doc`, `current_ver` cannot be extracted or are empty → **FAIL**
- Output format: `ruledeck_path (current_document, current_version)`

**Type 2/3 (Value Check - With pattern_items):**
- Store `pattern_items[0]` into `latest_doc` (expected document name)
- Store `pattern_items[1]` into `latest_ver` (expected version)
- Compare extracted values:
  - If `current_doc` == `latest_doc` AND `current_ver` == `latest_ver` → **PASS**
  - If `current_doc` != `latest_doc` OR `current_ver` != `latest_ver` → **FAIL**
- Output format: `ruledeck_path (current_document, current_version), Expect (latest_document, latest_version)`

**Validation Logic:**
1. Extract rule deck path from LVS log
2. Verify rule deck file exists at extracted path
3. Parse rule deck file for COMMAND FILE metadata
4. For Type 1/4: Verify all three values exist
5. For Type 2/3: Compare current values against expected pattern_items
6. Generate output with appropriate format based on check type

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

**Rationale:** This checker validates that the LVS rule deck document and version match expected values (pattern_items). The checker extracts current document/version from the rule deck file and compares against the expected document/version specified in pattern_items. Only the matched rule deck is output with its validation status (correct or incorrect version). This is a status validation check, not an existence check of multiple items.

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
item_desc = "Confirm latest LVS rule deck(s) was used? List LVS rule deck name in Comments. eg: DFM_LVS_RC_PEGASUS_N3P_1p17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2R_ALRDL.1.0a"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "LVS rule deck information found and extracted successfully"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "LVS rule deck version matched expected version"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Rule deck path, document name, and version found in LVS log and rule deck file"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Rule deck document and version matched expected values and validated successfully"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "LVS rule deck information not found or incomplete"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "LVS rule deck version does not match expected version"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Rule deck path, document name, or version not found in LVS log or rule deck file"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Rule deck document or version does not match expected values - version mismatch detected"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "LVS rule deck version mismatch waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Rule deck version mismatch waived per project approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused rule deck waiver entry"
unused_waiver_reason = "Waiver entry not matched - no corresponding rule deck version mismatch found"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [item_name]: [found_reason]"
  Example: "- DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2b (T-N05-CL-LS-007-N1, 1.2b): Rule deck document and version matched expected values and validated successfully"

ERROR01 (Violation/Fail items):
  Format: "- [item_name]: [missing_reason]"
  Example: "- DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.0a (T-N05-CL-LS-007-N1, 1.0a), Expect (T-N05-CL-LS-007-N1, 1.2b): Rule deck document or version does not match expected values - version mismatch detected"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-06:
  description: "Confirm latest LVS rule deck(s) was used? List LVS rule deck name in Comments. eg: DFM_LVS_RC_PEGASUS_N3P_1p17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2R_ALRDL.1.0a"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\LVS_pvl.log
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs boolean validation that LVS rule deck information can be extracted.
PASS if rule_path, current_doc, and current_ver are all found and non-empty.
FAIL if any required information is missing or cannot be extracted.

**Sample Output (PASS):**
```
Status: PASS
Reason: Rule deck path, document name, and version found in LVS log and rule deck file

Log format (CheckList.rpt):
INFO01:
  - DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2b (T-N05-CL-LS-007-N1, 1.2b)

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2b (T-N05-CL-LS-007-N1, 1.2b). In line 15, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\logs\2.0\LVS_pvl.log: Rule deck path, document name, and version found in LVS log and rule deck file
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Rule deck path, document name, or version not found in LVS log or rule deck file

Log format (CheckList.rpt):
ERROR01:
  - LVS rule deck information incomplete

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: LVS rule deck information incomplete. In line 0, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\logs\2.0\LVS_pvl.log: Rule deck path, document name, or version not found in LVS log or rule deck file
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-2-0-0-06:
  description: "Confirm latest LVS rule deck(s) was used? List LVS rule deck name in Comments. eg: DFM_LVS_RC_PEGASUS_N3P_1p17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2R_ALRDL.1.0a"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\LVS_pvl.log
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: LVS rule deck check is informational only for this project phase"
      - "Note: Rule deck version tracking required but mismatches do not block signoff"
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
  - "Explanation: LVS rule deck check is informational only for this project phase"
  - "Note: Rule deck version tracking required but mismatches do not block signoff"
INFO02:
  - LVS rule deck information incomplete

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: LVS rule deck check is informational only for this project phase. [WAIVED_INFO]
2: Info: LVS rule deck information incomplete. In line 0, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\logs\2.0\LVS_pvl.log: Rule deck path, document name, or version not found in LVS log or rule deck file [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-06:
  description: "Confirm latest LVS rule deck(s) was used? List LVS rule deck name in Comments. eg: DFM_LVS_RC_PEGASUS_N3P_1p17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2R_ALRDL.1.0a"
  requirements:
    value: 2
    pattern_items:
      - "T-N05-CL-LS-007-N1"  # Expected document name
      - "1.2b"                # Expected version
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\LVS_pvl.log
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- pattern_items[0]: Expected COMMAND FILE DOCUMENT value (e.g., "T-N05-CL-LS-007-N1")
- pattern_items[1]: Expected COMMAND FILE VERSION value (e.g., "1.2b")
- These are the golden values that current_doc and current_ver must match
- Extract from rule deck file metadata, not from rule deck filename

**Check Behavior:**
Type 2 validates that extracted rule deck document and version match expected values.
PASS if current_doc == pattern_items[0] AND current_ver == pattern_items[1].
FAIL if either document or version does not match expected values.

**Sample Output (PASS):**
```
Status: PASS
Reason: Rule deck document and version matched expected values and validated successfully

Log format (CheckList.rpt):
INFO01:
  - DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2b (T-N05-CL-LS-007-N1, 1.2b)

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2b (T-N05-CL-LS-007-N1, 1.2b). In line 15, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\logs\2.0\LVS_pvl.log: Rule deck document and version matched expected values and validated successfully
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-2-0-0-06:
  description: "Confirm latest LVS rule deck(s) was used? List LVS rule deck name in Comments. eg: DFM_LVS_RC_PEGASUS_N3P_1p17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2R_ALRDL.1.0a"
  requirements:
    value: 2
    pattern_items:
      - "T-N05-CL-LS-007-N1"
      - "1.2b"
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\LVS_pvl.log
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Rule deck version check is informational during development phase"
      - "Note: Version 1.0a is acceptable for this milestone - upgrade to 1.2b planned for next release"
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
  - "Explanation: Rule deck version check is informational during development phase"
  - "Note: Version 1.0a is acceptable for this milestone - upgrade to 1.2b planned for next release"
INFO02:
  - DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.0a (T-N05-CL-LS-007-N1, 1.0a), Expect (T-N05-CL-LS-007-N1, 1.2b)

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: Rule deck version check is informational during development phase. [WAIVED_INFO]
2: Info: DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.0a (T-N05-CL-LS-007-N1, 1.0a), Expect (T-N05-CL-LS-007-N1, 1.2b). In line 15, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\logs\2.0\LVS_pvl.log: Rule deck document or version does not match expected values - version mismatch detected [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-06:
  description: "Confirm latest LVS rule deck(s) was used? List LVS rule deck name in Comments. eg: DFM_LVS_RC_PEGASUS_N3P_1p17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2R_ALRDL.1.0a"
  requirements:
    value: 2
    pattern_items:
      - "T-N05-CL-LS-007-N1"  # Expected document name (golden value)
      - "1.2b"                # Expected version (golden value)
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\LVS_pvl.log
  waivers:
    value: 1
    waive_items:
      - name: "DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2b"  # Rule deck name to exempt
        reason: "This version can be accepted for this project"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern validation logic as Type 2, plus waiver classification:
- Extract rule deck document and version, compare against pattern_items
- If mismatch found, check if rule deck name matches waive_items
- Unwaived mismatches → ERROR (need fix)
- Waived mismatches → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all version mismatches are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived

Log format (CheckList.rpt):
INFO01:
  - DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2b (T-N05-CL-LS-007-N1, 1.2b)

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2b (T-N05-CL-LS-007-N1, 1.2b). In line 15, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\logs\2.0\LVS_pvl.log: Rule deck version mismatch waived per project approval: This version can be accepted for this project [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-06:
  description: "Confirm latest LVS rule deck(s) was used? List LVS rule deck name in Comments. eg: DFM_LVS_RC_PEGASUS_N3P_1p17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2R_ALRDL.1.0a"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\LVS_pvl.log
  waivers:
    value: 1
    waive_items:
      - name: "DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2b"  # ⚠️ MUST match Type 3 waive_items
        reason: "This version can be accepted for this project"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (keep exemption object names consistent)
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (verify rule deck info exists), plus waiver classification:
- Match violations against waive_items
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output:**
```
Status: PASS
Reason: All items waived

Log format (CheckList.rpt):
INFO01:
  - DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2b (T-N05-CL-LS-007-N1, 1.2b)

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2b (T-N05-CL-LS-007-N1, 1.2b). In line 15, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\logs\2.0\LVS_pvl.log: Rule deck version mismatch waived per project approval: This version can be accepted for this project [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 2.0_TECHFILE_AND_RULE_DECK_CHECK --checkers IMP-2-0-0-06 --force

# Run individual tests
python IMP-2-0-0-06.py
```

---

## Notes

**Implementation Notes:**
- The checker must handle both Windows and Unix path separators in include statements
- Rule deck path is already absolute, no path resolution needed
- COMMAND FILE DOCUMENT and VERSION lines must be parsed from the rule deck file itself, not from the log
- Multiple rule decks may be included - extract all DFM_LVS rule decks
- Rule deck filename (e.g., DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2b) is used as the item name in output

**Limitations:**
- Assumes LVS_pvl.log contains include statement with DFM_LVS pattern
- Assumes rule deck file contains COMMAND FILE DOCUMENT and VERSION metadata
- Does not validate rule deck content, only metadata
- Path extraction depends on specific include statement format

**Known Issues:**
- If rule deck file is encrypted or binary, metadata extraction may fail
- Multiple rule decks with different versions may require separate validation
- Waiver matching uses exact rule deck filename - version suffix must match exactly