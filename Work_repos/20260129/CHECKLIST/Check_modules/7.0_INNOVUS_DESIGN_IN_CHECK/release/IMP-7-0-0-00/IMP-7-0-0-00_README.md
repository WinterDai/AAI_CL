# IMP-7-0-0-00: Block name (e.g: cdn_hs_phy_data_slice)

## Overview

**Check ID:** IMP-7-0-0-00  
**Description:** Block name (e.g: cdn_hs_phy_data_slice)  
**Category:** Design Information Verification  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt`

This checker validates the presence and format of block name identifiers in implementation reports. It ensures that block names are properly defined and follow expected naming conventions, catching missing or malformed block identifiers that could indicate design setup issues.

---

## Check Logic

### Input Parsing
Parse implementation report files to extract block name information and validate naming structure.

**Key Patterns (shared across all types):**
```python
# Pattern 1: Extract block name identifier
pattern1 = r'^Block name:\s*(.+)$'
# Example: "Block name: CDN_104H_cdn_hs_phy_data_slice_EW"

# Pattern 2: Extract block prefix component for validation
pattern2 = r'^Block name:\s*(\w+)_.*$'
# Example: "Block name: CDN_104H_cdn_hs_phy_data_slice_EW"

# Pattern 3: Extract core block type component for classification
pattern3 = r'^Block name:\s*.*_(cdn_hs_phy_data_slice)_.*$'
# Example: "Block name: CDN_104H_cdn_hs_phy_data_slice_EW"
```

### Detection Logic
1. Read implementation report file
2. Search for "Block name:" entries using regex patterns
3. Extract and validate block name format and structure
4. Check if required block identifier exists and follows naming conventions
5. Determine PASS/FAIL based on block name presence and validity

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `existence_check`

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

**Selected Mode for this checker:** `existence_check`

**Rationale:** This checker validates the existence of block name entries in implementation reports, ensuring required block identifiers are present and properly formatted.

---

## Output Descriptions (CRITICAL - Code Generator Uses These!)

This section defines the output strings used by `build_complete_output()` in the checker code.

```python
# Item description for this checker
item_desc = "Block name (e.g: cdn_hs_phy_data_slice)"

# PASS case descriptions - Split by Type semantics (API-026)
found_desc_type1_4 = "Block name found in implementation report"
found_desc_type2_3 = "Required block name pattern matched (2/2)"

# PASS reasons - Split by Type semantics
found_reason_type1_4 = "Block name entry found and validated in implementation report"
found_reason_type2_3 = "Required block name pattern matched and validated in report"

# FAIL case descriptions
missing_desc_type1_4 = "Block name not found in implementation report"
missing_desc_type2_3 = "Expected block name pattern not satisfied (1/2 missing)"

# FAIL reasons
missing_reason_type1_4 = "Block name entry not found or invalid format in implementation report"
missing_reason_type2_3 = "Expected block name pattern not satisfied or missing from report"

# WAIVED case descriptions
waived_desc = "Block name check waived"
waived_base_reason = "Block name verification waived per design team approval"

# UNUSED waivers
unused_desc = "Unused block name waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding block name issue found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "CDN_104H_cdn_hs_phy_data_slice_EW"
  Example: "CDN_104H_cdn_hs_phy_data_slice_EW"

ERROR01 (Violation/Fail items):
  Format: "cdn_hs_phy_data_slice"
  Example: "cdn_hs_phy_data_slice"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-7-0-0-00:
  description: "Block name (e.g: cdn_hs_phy_data_slice)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt"
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
Reason: Block name entry found and validated in implementation report

Log format (item_id.log):
INFO01:
  - CDN_104H_cdn_hs_phy_data_slice_EW

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: CDN_104H_cdn_hs_phy_data_slice_EW. In line 1, IMP-7-0-0-00.rpt: Block name entry found and validated in implementation report
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Block name entry not found or invalid format in implementation report

Log format (item_id.log):
ERROR01:
  - Block name

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: Block name. In line 1, IMP-7-0-0-00.rpt: Block name entry not found or invalid format in implementation report
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-7-0-0-00:
  description: "Block name (e.g: cdn_hs_phy_data_slice)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode
    waive_items:  # IMPORTANT: Use PLAIN STRING format
      - "Explanation: Block name validation is informational only for this design phase"
      - "Note: Missing block names are acceptable during early implementation stages"
```

**Sample Output (PASS with violations):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All violations waived as informational

Log format (item_id.log):
INFO01:
  - "Explanation: Block name validation is informational only for this design phase"
  - "Note: Missing block names are acceptable during early implementation stages"
INFO02:
  - Block name

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: Block name validation is informational only for this design phase. [WAIVED_INFO]
2: Info: Block name. In line 1, IMP-7-0-0-00.rpt: Block name entry not found or invalid format in implementation report [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-7-0-0-00:
  description: "Block name (e.g: cdn_hs_phy_data_slice)"
  requirements:
    value: 2
    pattern_items:
      - "cdn_hs_phy_data_slice"
      - "CDN_104H"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt"
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
Reason: Required block name pattern matched and validated in report

Log format (item_id.log):
INFO01:
  - CDN_104H_cdn_hs_phy_data_slice_EW

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: CDN_104H_cdn_hs_phy_data_slice_EW. In line 1, IMP-7-0-0-00.rpt: Required block name pattern matched and validated in report
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-7-0-0-00:
  description: "Block name (e.g: cdn_hs_phy_data_slice)"
  requirements:
    value: 0
    pattern_items:
      - "cdn_hs_phy_data_slice"
      - "CDN_104H"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode
    waive_items:  # IMPORTANT: Use PLAIN STRING format
      - "Explanation: Block name pattern check is informational only"
      - "Note: Pattern mismatches are acceptable for legacy designs"
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
  - "Explanation: Block name pattern check is informational only"
INFO02:
  - cdn_hs_phy_data_slice

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: Block name pattern check is informational only. [WAIVED_INFO]
2: Info: cdn_hs_phy_data_slice. In line 1, IMP-7-0-0-00.rpt: Expected block name pattern not satisfied or missing from report [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-7-0-0-00:
  description: "Block name (e.g: cdn_hs_phy_data_slice)"
  requirements:
    value: 2
    pattern_items:
      - "cdn_hs_phy_data_slice"
      - "CDN_104H"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "CDN_104H_cdn_hs_phy_data_slice_EW"
        reason: "Waived - Legacy block name format approved by design team"
      - name: "legacy_block"
        reason: "Waived - Old naming convention still in use"
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
  - CDN_104H_cdn_hs_phy_data_slice_EW
WARN01:
  - legacy_block

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: CDN_104H_cdn_hs_phy_data_slice_EW. In line 1, IMP-7-0-0-00.rpt: Block name verification waived per design team approval: Waived - Legacy block name format approved by design team [WAIVER]
Warn Occurrence: 1
1: Warn: legacy_block. In line 1, IMP-7-0-0-00.rpt: Waiver not matched - no corresponding block name issue found: Waived - Old naming convention still in use [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-7-0-0-00:
  description: "Block name (e.g: cdn_hs_phy_data_slice)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "CDN_104H_cdn_hs_phy_data_slice_EW"
        reason: "Waived - Legacy block name format approved by design team"
      - name: "legacy_block"
        reason: "Waived - Old naming convention still in use"
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
  - CDN_104H_cdn_hs_phy_data_slice_EW
WARN01:
  - legacy_block

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: CDN_104H_cdn_hs_phy_data_slice_EW. In line 1, IMP-7-0-0-00.rpt: Block name verification waived per design team approval: Waived - Legacy block name format approved by design team [WAIVER]
Warn Occurrence: 1
1: Warn: legacy_block. In line 1, IMP-7-0-0-00.rpt: Waiver not matched - no corresponding block name issue found: Waived - Old naming convention still in use [WAIVER]
```