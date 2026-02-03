# IMP-2-0-0-02: Confirm latest DRC rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_054_PATCH.11_2a.encrypt

## Overview

**Check ID:** IMP-2-0-0-02  
**Description:** Confirm latest DRC rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_054_PATCH.11_2a.encrypt  
**Category:** DRC Rule Deck Verification  
**Input Files:** ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log

This checker validates that the correct DRC rule deck document and version are used during physical verification. It extracts the rule deck path from the DRC log file, parses the rule deck file to obtain document name and version information, and compares against expected values to ensure compliance with design requirements.

---

## Check Logic

### Input Parsing

**Phase 1: Extract Rule Deck Path from DRC Log**

Parse `DRC_pvl.log` to extract the absolute rule deck path from include statements:

**Key Patterns:**
```python
# Pattern 1: Extract rule deck path from include statement
include_pattern = r'^\s*include\s+"([^"]+)"'
# Example: 'include "/path/to/rule_deck/PLN3ELO_17M_014.11_2a.encrypt"'
# Extraction: Captures absolute path between quotes → stored as `rule_path`
```

**Phase 2: Parse Rule Deck File for Document and Version**

Parse the `rule_path` file to extract document name and version:

**Key Patterns:**
```python
# Pattern 2: Extract document name and version from rule deck header
doc_version_pattern = r'DRC\s+COMMAND\s+FILE\s+DOCUMENT:\s*(.+?)\s+VER\s+(.+?)(?:\s|$)'
# Example: "DRC COMMAND FILE DOCUMENT: T-N05-CL-DR-014-N1 VER 014.11_2a"
# Extraction: 
#   - Group 1: current_document = "T-N05-CL-DR-014-N1"
#   - Group 2: current_version = "014.11_2a"
```

**Storage Requirements:**
- `rule_path`: Absolute path to rule deck file (extracted from DRC_pvl.log)
- `current_doc`: Document name from rule deck header (e.g., "T-N05-CL-DR-014-N1")
- `current_ver`: Version identifier from rule deck header (e.g., "014.11_2a")

### Detection Logic

**Type 1/4 (Boolean Check - No pattern_items):**
1. Attempt to extract `rule_path` from DRC_pvl.log using include pattern
2. If `rule_path` found, parse the rule deck file for document/version
3. Validate all three values exist and are non-empty:
   - `rule_path` is not None and not empty
   - `current_doc` is not None and not empty
   - `current_ver` is not None and not empty
4. **PASS**: All values successfully extracted and non-empty
5. **FAIL**: Any value missing or extraction failed

**Type 2/3 (Value Check - With pattern_items):**
1. Perform same extraction as Type 1/4 to obtain `rule_path`, `current_doc`, `current_ver`
2. Extract expected values from pattern_items:
   - `pattern_items[0]` → `latest_doc` (expected document name)
   - `pattern_items[1]` → `latest_ver` (expected version)
3. Compare extracted values against expected:
   - Document match: `current_doc` == `latest_doc`
   - Version match: `current_ver` == `latest_ver`
4. **PASS**: Both document and version match expected values
5. **FAIL**: Either document or version does not match (or extraction failed)

**Output Format:**
- **Type 1/4 PASS**: `ruledeck_path (current_document, current_version)`
  - Example: `/path/to/PLN3ELO_17M_014.11_2a.encrypt (T-N05-CL-DR-014-N1, 014.11_2a)`
- **Type 2/3 PASS**: `ruledeck_path (current_document, current_version), Expect (latest_document, latest_version)`
  - Example: `/path/to/PLN3ELO_17M_014.11_2a.encrypt (T-N05-CL-DR-014-N1, 014.11_2a), Expect (T-N05-CL-DR-014-N1, 014.11_2a)`
- **Type 2/3 FAIL**: Same format showing mismatch between current and expected

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

**Rationale:** This checker validates that the DRC rule deck document and version match expected values (pattern_items). The pattern_items define the "golden" document name and version that should be used. The checker extracts actual values from files and compares them against these expected values. Only the matched items (document/version pair) are output, with status indicating whether they match the expected configuration. This is a status validation check, not an existence check.

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
item_desc = "Confirm latest DRC rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_054_PATCH.11_2a.encrypt"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "DRC rule deck document and version information found in rule deck file"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "DRC rule deck document and version matched expected values"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Rule deck path, document name, and version successfully extracted from DRC log and rule deck file"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Current rule deck document and version matched expected configuration and validated successfully"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "DRC rule deck document or version information not found or extraction failed"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "DRC rule deck document or version does not match expected values"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Failed to extract rule deck path from DRC log, or document/version not found in rule deck file header"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Current rule deck document or version does not satisfy expected configuration - version mismatch detected"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "DRC rule deck version mismatch waived per project approval"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Rule deck version difference waived - alternative version approved for this project"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused rule deck waiver entry"
unused_waiver_reason = "Waiver entry not matched - specified rule deck version not found in actual usage"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [item_name]: [found_reason]"
  Example: "- /path/to/PLN3ELO_17M_014.11_2a.encrypt (T-N05-CL-DR-014-N1, 014.11_2a): Current rule deck document and version matched expected configuration and validated successfully"

ERROR01 (Violation/Fail items):
  Format: "- [item_name]: [missing_reason]"
  Example: "- /path/to/PLN3ELO_17M_014.10_1a.encrypt (T-N05-CL-DR-014-N1, 014.10_1a): Current rule deck document or version does not satisfy expected configuration - version mismatch detected"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-02:
  description: "Confirm latest DRC rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_054_PATCH.11_2a.encrypt"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log
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
Reason: Rule deck path, document name, and version successfully extracted from DRC log and rule deck file

Log format (CheckList.rpt):
INFO01:
  - /apps/ssg_tools/production/pegasus/rule_decks/PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_2a.encrypt (T-N05-CL-DR-014-N1, 014.11_2a)

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: /apps/ssg_tools/production/pegasus/rule_decks/PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_2a.encrypt (T-N05-CL-DR-014-N1, 014.11_2a). In line 1, DRC_pvl.log: Rule deck path, document name, and version successfully extracted from DRC log and rule deck file
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Failed to extract rule deck path from DRC log, or document/version not found in rule deck file header

Log format (CheckList.rpt):
ERROR01:
  - DRC rule deck information extraction failed

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: DRC rule deck information extraction failed. In line 1, DRC_pvl.log: Failed to extract rule deck path from DRC log, or document/version not found in rule deck file header
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-2-0-0-02:
  description: "Confirm latest DRC rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_054_PATCH.11_2a.encrypt"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - rule deck version tracking for reference"
      - "Note: Version mismatches are acceptable during development phase and do not block signoff"
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
  - "Note: Version mismatches are acceptable during development phase and do not block signoff"
INFO02:
  - DRC rule deck information extraction failed

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: This check is informational only - rule deck version tracking for reference. [WAIVED_INFO]
2: Info: DRC rule deck information extraction failed. In line 1, DRC_pvl.log: Failed to extract rule deck path from DRC log, or document/version not found in rule deck file header [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-02:
  description: "Confirm latest DRC rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_054_PATCH.11_2a.encrypt"
  requirements:
    value: 2
    pattern_items:
      - "T-N05-CL-DR-014-N1"  # Expected document name
      - "014.11_2a"           # Expected version
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- If description contains "version": Use VERSION IDENTIFIERS ONLY (e.g., "22.11-s119_1")
  ❌ DO NOT use paths: "innovus/221/22.11-s119_1"
  ❌ DO NOT use filenames: "libtech.lef"
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
Reason: Current rule deck document and version matched expected configuration and validated successfully

Log format (CheckList.rpt):
INFO01:
  - /apps/ssg_tools/production/pegasus/rule_decks/PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_2a.encrypt (T-N05-CL-DR-014-N1, 014.11_2a), Expect (T-N05-CL-DR-014-N1, 014.11_2a)

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: /apps/ssg_tools/production/pegasus/rule_decks/PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_2a.encrypt (T-N05-CL-DR-014-N1, 014.11_2a), Expect (T-N05-CL-DR-014-N1, 014.11_2a). In line 1, DRC_pvl.log: Current rule deck document and version matched expected configuration and validated successfully
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-2-0-0-02:
  description: "Confirm latest DRC rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_054_PATCH.11_2a.encrypt"
  requirements:
    value: 2
    pattern_items:
      - "T-N05-CL-DR-014-N1"
      - "014.11_2a"
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Rule deck version check is informational - tracking for audit purposes only"
      - "Note: Version mismatches are expected during development and do not require immediate correction"
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
  - "Explanation: Rule deck version check is informational - tracking for audit purposes only"
  - "Note: Version mismatches are expected during development and do not require immediate correction"
INFO02:
  - /apps/ssg_tools/production/pegasus/rule_decks/PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.10_1a.encrypt (T-N05-CL-DR-014-N1, 014.10_1a), Expect (T-N05-CL-DR-014-N1, 014.11_2a)

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: Rule deck version check is informational - tracking for audit purposes only. [WAIVED_INFO]
2: Info: /apps/ssg_tools/production/pegasus/rule_decks/PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.10_1a.encrypt (T-N05-CL-DR-014-N1, 014.10_1a), Expect (T-N05-CL-DR-014-N1, 014.11_2a). In line 1, DRC_pvl.log: Current rule deck document or version does not satisfy expected configuration - version mismatch detected [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-02:
  description: "Confirm latest DRC rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_054_PATCH.11_2a.encrypt"
  requirements:
    value: 2
    pattern_items:
      - "T-N05-CL-DR-014-N1"  # ⚠️ GOLDEN VALUE - Expected document name
      - "014.11_2a"           # ⚠️ GOLDEN VALUE - Expected version
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log
  waivers:
    value: 2
    waive_items:
      - name: "PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014.13_1a.encrypt"  # ⚠️ EXEMPTION - Rule deck filename to exempt
        reason: "This version can be accepted for this project - approved for legacy compatibility"
      - name: "PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.10_1a.encrypt"
        reason: "Older version waived - acceptable for pre-tapeout validation phase"
```

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

Log format (CheckList.rpt):
INFO01:
  - PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014.13_1a.encrypt (T-N05-CL-DR-014-N1, 014.13_1a)
WARN01:
  - PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.10_1a.encrypt

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014.13_1a.encrypt (T-N05-CL-DR-014-N1, 014.13_1a). In line 1, DRC_pvl.log: Rule deck version difference waived - alternative version approved for this project: This version can be accepted for this project - approved for legacy compatibility [WAIVER]
Warn Occurrence: 1
1: Warn: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.10_1a.encrypt. In line 1, DRC_pvl.log: Waiver entry not matched - specified rule deck version not found in actual usage: Older version waived - acceptable for pre-tapeout validation phase [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-02:
  description: "Confirm latest DRC rule deck(s) was used? List DRC rule deck name in Comments. eg: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_2a.encrypt PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_054_PATCH.11_2a.encrypt"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log
  waivers:
    value: 2
    waive_items:
      - name: "PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014.13_1a.encrypt"  # ⚠️ MUST match Type 3 waive_items
        reason: "This version can be accepted for this project - approved for legacy compatibility"
      - name: "PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.10_1a.encrypt"
        reason: "Older version waived - acceptable for pre-tapeout validation phase"
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

Log format (CheckList.rpt):
INFO01:
  - PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014.13_1a.encrypt (T-N05-CL-DR-014-N1, 014.13_1a)
WARN01:
  - PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.10_1a.encrypt

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014.13_1a.encrypt (T-N05-CL-DR-014-N1, 014.13_1a). In line 1, DRC_pvl.log: Rule deck version difference waived - alternative version approved for this project: This version can be accepted for this project - approved for legacy compatibility [WAIVER]
Warn Occurrence: 1
1: Warn: PLN3ELO_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.10_1a.encrypt. In line 1, DRC_pvl.log: Waiver entry not matched - specified rule deck version not found in actual usage: Older version waived - acceptable for pre-tapeout validation phase [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 2.0_TECHFILE_AND_RULE_DECK_CHECK --checkers IMP-2-0-0-02 --force

# Run individual tests
python IMP-2-0-0-02.py
```

---

## Notes

**Implementation Notes:**
1. The checker must parse two files sequentially:
   - First: Extract `rule_path` from DRC_pvl.log using include pattern
   - Second: Parse the extracted `rule_path` file for document/version header

2. Error handling is critical:
   - If include statement not found in DRC_pvl.log → FAIL
   - If rule_path file does not exist → FAIL
   - If document/version header not found in rule deck → FAIL
   - All three values (rule_path, current_doc, current_ver) must be non-empty

3. Pattern matching considerations:
   - Include statement may have varying whitespace
   - Document/version line format is fixed: "DRC COMMAND FILE DOCUMENT: <doc> VER <ver>"
   - Version format may include dots, underscores, alphanumeric characters (e.g., "014.11_2a")

4. Type 2/3 comparison logic:
   - Exact string match required for both document and version
   - Case-sensitive comparison
   - No partial matching or wildcards

5. Output format requirements:
   - Type 1/4: Show only current values in parentheses
   - Type 2/3: Show both current and expected values for comparison
   - Format: `path (doc, ver)` or `path (doc, ver), Expect (expected_doc, expected_ver)`

**Known Limitations:**
- Assumes single include statement in DRC_pvl.log (does not handle multiple rule decks)
- Requires exact format for document/version header line
- No support for encrypted rule deck parsing (relies on header being readable)