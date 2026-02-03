# IMP-2-0-0-04: Confirm latest Antenna rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_ANT.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_SHDMIM_ANT.11_2a.encrypt

## Overview

**Check ID:** IMP-2-0-0-04  
**Description:** Confirm latest Antenna rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_ANT.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_SHDMIM_ANT.11_2a.encrypt  
**Category:** TECHFILE_AND_RULE_DECK_CHECK  
**Input Files:** ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\ANT_pvl.log

This checker validates that the correct version of Antenna DRC rule deck was used during physical verification. It parses the ANT PVL log file to extract the rule deck path and version information, then compares against expected document and version identifiers to ensure compliance with project requirements.

---

## Check Logic

### Input Parsing

**Step 1: Parse ANT_pvl.log for Rule Deck Path**

Extract the absolute rule deck path from include statements in the ANT log file:

**Key Patterns:**
```python
# Pattern 1: Rule deck include statement - extracts absolute path
pattern_include = r'include\s+"([^"]+)"'
# Example: include "C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt"
# Extracts: Full absolute path to rule deck file
```

**Step 2: Parse Rule Deck File for Document and Version**

Parse the extracted rule deck file to extract document name and version:

```python
# Pattern 2: DRC command file document header - extracts document and version
pattern_document = r'DRC\s+COMMAND\s+FILE\s+DOCUMENT:\s*(\S+)\s+VER\s+(\S+)'
# Example: DRC COMMAND FILE DOCUMENT: T-N05-CL-DR-014-N1 VER 014.13_1a
# Extracts: 
#   Group 1 (current_doc): T-N05-CL-DR-014-N1
#   Group 2 (current_ver): 014.13_1a
```

**Parsing Strategy:**
1. Line-by-line sequential parsing of ANT_pvl.log
2. Extract `rule_path` from include statement (absolute path)
3. Open and parse the rule deck file at `rule_path`
4. Extract `current_doc` and `current_ver` from DRC COMMAND FILE DOCUMENT line
5. Store all three values: `rule_path`, `current_doc`, `current_ver`

**Edge Cases:**
- Multiple include statements: Capture all rule deck files
- Windows path format with backslashes
- Encrypted rule deck files (.encrypt extension)
- Missing or malformed DRC COMMAND FILE DOCUMENT header
- Rule deck file not found at extracted path

### Detection Logic

**Type 1/4 (Boolean Check - No pattern_items):**
- If `rule_path`, `current_doc`, `current_ver` can be extracted and all have values → **PASS**
- If any of `rule_path`, `current_doc`, `current_ver` cannot be extracted or is empty → **FAIL**
- Output format: `ruledeck_path (current_document, current_version)`

**Type 2/3 (Value Check - With pattern_items):**
- Store `pattern_items[0]` into `latest_doc`
- Store `pattern_items[1]` into `latest_ver`
- If `current_doc` == `latest_doc` AND `current_ver` == `latest_ver` → **PASS**
- If `current_doc` != `latest_doc` OR `current_ver` != `latest_ver` → **FAIL**
- Output format (PASS): `ruledeck_path (current_document, current_version), Expect (latest_document, latest_version)`
- Output format (FAIL): `ruledeck_path (current_document, current_version), Expect (latest_document, latest_version)`

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

**Rationale:** This checker validates that the extracted rule deck document and version match the expected values defined in pattern_items. It checks the STATUS of the rule deck version (whether it matches the latest required version), not just whether a rule deck exists. Only the rule deck specified in the log is checked against the expected document/version pattern.

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
item_desc = "Confirm latest Antenna rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_ANT.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_SHDMIM_ANT.11_2a.encrypt"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "Antenna rule deck information found in ANT log"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "Antenna rule deck version matched expected version"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Rule deck path, document name, and version successfully extracted from ANT log"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Rule deck document and version matched expected values and validated"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Antenna rule deck information not found or incomplete in ANT log"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Antenna rule deck version does not match expected version"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Rule deck path, document name, or version not found in ANT log or rule deck file"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Rule deck document or version does not match expected pattern - version mismatch detected"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Antenna rule deck version mismatch waived"

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
  Example: "- PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt (T-N05-CL-DR-014-N1, 014.13_1a): Rule deck document and version matched expected values and validated"

ERROR01 (Violation/Fail items):
  Format: "- [item_name]: [missing_reason]"
  Example: "- PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt (T-N05-CL-DR-014-N1, 014.11_2a), Expect (T-N05-CL-DR-014-N1, 014.13_1a): Rule deck document or version does not match expected pattern - version mismatch detected"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-04:
  description: "Confirm latest Antenna rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_ANT.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_SHDMIM_ANT.11_2a.encrypt"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\ANT_pvl.log"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs boolean validation that rule deck information can be extracted from the ANT log.
PASS if `rule_path`, `current_doc`, and `current_ver` are all successfully extracted.
FAIL if any of these values cannot be extracted or are empty.

**Sample Output (PASS):**
```
Status: PASS
Reason: Rule deck path, document name, and version successfully extracted from ANT log

Log format (CheckList.rpt):
INFO01:
  - PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt (T-N05-CL-DR-014-N1, 014.13_1a)

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt (T-N05-CL-DR-014-N1, 014.13_1a). In line 45, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\logs\2.0\ANT_pvl.log: Rule deck path, document name, and version successfully extracted from ANT log
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Rule deck path, document name, or version not found in ANT log or rule deck file

Log format (CheckList.rpt):
ERROR01:
  - ANT_pvl.log

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: ANT_pvl.log. In line 0, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\logs\2.0\ANT_pvl.log: Rule deck path, document name, or version not found in ANT log or rule deck file
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-2-0-0-04:
  description: "Confirm latest Antenna rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_ANT.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_SHDMIM_ANT.11_2a.encrypt"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\ANT_pvl.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - rule deck version tracking for reference"
      - "Note: Version mismatches are acceptable during development phase"
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
  - "Explanation: This check is informational only - rule deck version tracking for reference"
  - "Note: Version mismatches are acceptable during development phase"
INFO02:
  - ANT_pvl.log

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: This check is informational only - rule deck version tracking for reference. [WAIVED_INFO]
2: Info: ANT_pvl.log. In line 0, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\logs\2.0\ANT_pvl.log: Rule deck path, document name, or version not found in ANT log or rule deck file [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-04:
  description: "Confirm latest Antenna rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_ANT.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_SHDMIM_ANT.11_2a.encrypt"
  requirements:
    value: 2
    pattern_items:
      - "T-N05-CL-DR-014-N1"  # Expected document identifier
      - "014.13_1a"            # Expected version identifier
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\ANT_pvl.log"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- pattern_items[0] = Expected document identifier (e.g., "T-N05-CL-DR-014-N1")
- pattern_items[1] = Expected version identifier (e.g., "014.13_1a")
- These are the "golden values" that current_doc and current_ver must match
- Extract from DRC COMMAND FILE DOCUMENT header in rule deck file

**Check Behavior:**
Type 2 compares extracted rule deck document and version against expected pattern_items.
PASS if `current_doc` == `pattern_items[0]` AND `current_ver` == `pattern_items[1]`.
FAIL if document or version does not match expected values.

**Sample Output (PASS):**
```
Status: PASS
Reason: Rule deck document and version matched expected values and validated

Log format (CheckList.rpt):
INFO01:
  - PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt (T-N05-CL-DR-014-N1, 014.13_1a), Expect (T-N05-CL-DR-014-N1, 014.13_1a)

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt (T-N05-CL-DR-014-N1, 014.13_1a), Expect (T-N05-CL-DR-014-N1, 014.13_1a). In line 45, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\logs\2.0\ANT_pvl.log: Rule deck document and version matched expected values and validated
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Rule deck document or version does not match expected pattern - version mismatch detected

Log format (CheckList.rpt):
ERROR01:
  - PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt (T-N05-CL-DR-014-N1, 014.11_2a), Expect (T-N05-CL-DR-014-N1, 014.13_1a)

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt (T-N05-CL-DR-014-N1, 014.11_2a), Expect (T-N05-CL-DR-014-N1, 014.13_1a). In line 45, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\logs\2.0\ANT_pvl.log: Rule deck document or version does not match expected pattern - version mismatch detected
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-2-0-0-04:
  description: "Confirm latest Antenna rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_ANT.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_SHDMIM_ANT.11_2a.encrypt"
  requirements:
    value: 2
    pattern_items:
      - "T-N05-CL-DR-014-N1"
      - "014.13_1a"
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\ANT_pvl.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Rule deck version check is informational - older versions acceptable during development"
      - "Note: Version 014.11_2a is approved for use in this project phase"
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
  - "Explanation: Rule deck version check is informational - older versions acceptable during development"
  - "Note: Version 014.11_2a is approved for use in this project phase"
INFO02:
  - PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt (T-N05-CL-DR-014-N1, 014.11_2a), Expect (T-N05-CL-DR-014-N1, 014.13_1a)

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: Rule deck version check is informational - older versions acceptable during development. [WAIVED_INFO]
2: Info: PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt (T-N05-CL-DR-014-N1, 014.11_2a), Expect (T-N05-CL-DR-014-N1, 014.13_1a). In line 45, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\logs\2.0\ANT_pvl.log: Rule deck document or version does not match expected pattern - version mismatch detected [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-04:
  description: "Confirm latest Antenna rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_ANT.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_SHDMIM_ANT.11_2a.encrypt"
  requirements:
    value: 2
    pattern_items:
      - "T-N05-CL-DR-014-N1"  # ⚠️ GOLDEN VALUE - Expected document
      - "014.13_1a"            # ⚠️ GOLDEN VALUE - Expected version
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\ANT_pvl.log"
  waivers:
    value: 2
    waive_items:
      - name: "PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt"  # ⚠️ EXEMPTION - Rule deck filename to exempt
        reason: "This version can be accepted for this project"
      - name: "PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.11_2a.encrypt"
        reason: "Legacy version approved for backward compatibility testing"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern comparison logic as Type 2, plus waiver classification:
- Compare extracted document/version against pattern_items
- If mismatch found, check if rule deck filename is in waive_items
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
  - PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt (T-N05-CL-DR-014-N1, 014.11_2a), Expect (T-N05-CL-DR-014-N1, 014.13_1a)
WARN01:
  - PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.11_2a.encrypt

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt (T-N05-CL-DR-014-N1, 014.11_2a), Expect (T-N05-CL-DR-014-N1, 014.13_1a). In line 45, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\logs\2.0\ANT_pvl.log: Rule deck version mismatch waived per project approval: This version can be accepted for this project [WAIVER]
Warn Occurrence: 1
1: Warn: PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.11_2a.encrypt. In line 0, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\logs\2.0\ANT_pvl.log: Waiver entry not matched - no corresponding rule deck version mismatch found: Legacy version approved for backward compatibility testing [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-04:
  description: "Confirm latest Antenna rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_ANT.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014_SHDMIM_ANT.11_2a.encrypt"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\ANT_pvl.log"
  waivers:
    value: 2
    waive_items:
      - name: "PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt"  # ⚠️ MUST match Type 3 waive_items
        reason: "This version can be accepted for this project"
      - name: "PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.11_2a.encrypt"
        reason: "Legacy version approved for backward compatibility testing"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (keep exemption object names consistent)
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (extraction validation), plus waiver classification:
- Check if rule deck information can be extracted
- If extraction fails, check if rule deck filename is in waive_items
- Unwaived failures → ERROR
- Waived failures → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS if all extraction failures are waived.

**Sample Output:**
```
Status: PASS
Reason: All items waived

Log format (CheckList.rpt):
INFO01:
  - PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt
WARN01:
  - PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.11_2a.encrypt

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt. In line 45, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\logs\2.0\ANT_pvl.log: Rule deck version mismatch waived per project approval: This version can be accepted for this project [WAIVER]
Warn Occurrence: 1
1: Warn: PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.11_2a.encrypt. In line 0, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\logs\2.0\ANT_pvl.log: Waiver entry not matched - no corresponding rule deck version mismatch found: Legacy version approved for backward compatibility testing [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 2.0_TECHFILE_AND_RULE_DECK_CHECK --checkers IMP-2-0-0-04 --force

# Run individual tests
python IMP-2-0-0-04.py
```

---

## Notes

**Implementation Notes:**
1. The rule deck path extracted from ANT_pvl.log is an absolute Windows path - use it directly for file parsing
2. Rule deck files may be encrypted (.encrypt extension) - ensure parser handles encrypted file format
3. Multiple rule decks may be included - process all include statements found in the log
4. DRC COMMAND FILE DOCUMENT header format is fixed - parse exactly as specified in user hints
5. For Type 2/3: pattern_items[0] is document identifier, pattern_items[1] is version identifier
6. For Type 3/4: waive_items.name should be the rule deck filename (not full path)

**Known Limitations:**
- Assumes DRC COMMAND FILE DOCUMENT header exists in rule deck file
- Requires exact format match for document/version extraction
- Does not validate rule deck content beyond header information
- Waiver matching is based on filename only, not full path

**Edge Cases:**
- Missing include statement in ANT log → Type 1/4 FAIL
- Malformed DRC COMMAND FILE DOCUMENT header → Type 1/4 FAIL
- Multiple rule decks with different versions → Check each separately
- Encrypted rule deck file cannot be opened → Type 1/4 FAIL