# IMP-16-0-0-06: Confirm you followed the below document about IPTAG creation. If you have further question, please check with Tobing. HSPHY/HPPHY/DFPHY/GDDR/HBM: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/_layouts/15/Doc.aspx?sourcedoc=%7B26DAB946-483A-415F-AC0C-C195C0838506%7D&file=IP%20Number%20Format%20-%20DDR%20PHY.docx&wdLOR=cF5835961-1465-461D-BAFD-3F0590F6A7F9&action=default&mobileredirect=true SERDES: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/IP_Numbers/IP%20Number%20Format%20-%20SerDes.docx?d=wf015c37bca9b4d3d951589cf616333fe&csf=1&web=1

## Overview

**Check ID:** IMP-16-0-0-06  
**Description:** Confirm you followed the below document about IPTAG creation. If you have further question, please check with Tobing. HSPHY/HPPHY/DFPHY/GDDR/HBM: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/_layouts/15/Doc.aspx?sourcedoc=%7B26DAB946-483A-415F-AC0C-C195C0838506%7D&file=IP%20Number%20Format%20-%20DDR%20PHY.docx&wdLOR=cF5835961-1465-461D-BAFD-3F0590F6A7F9&action=default&mobileredirect=true SERDES: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/IP_Numbers/IP%20Number%20Format%20-%20SerDes.docx?d=wf015c37bca9b4d3d951589cf616333fe&csf=1&web=1  
**Category:** IPTAG Validation  
**Input Files:** ${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/phy_iptag.prod

This checker validates the IPTAG (IP Tag Product Name) configuration file for DDR PHY designs. It verifies that all fields in the phy_iptag.prod file conform to the IP Number Format standards defined in the Cadence SharePoint documentation. The checker ensures proper field formatting, validates field values against allowed codes, checks delimiter placement, and confirms that the IPTAG structure follows the required format for DDR PHY, SERDES, and related IP types.

---

## Check Logic

### Input Parsing

The checker parses the phy_iptag.prod file line-by-line to extract field definitions and validate against format requirements. Each line contains a field value followed by a comment describing the field's purpose, format constraints, and valid codes.

**Key Patterns:**

```python
# Pattern 1: Field definition with inline comment
field_pattern = r'^([A-Z0-9_$]+)\s*//\s*(.+)$'
# Example: "H       // DDR PHY Architecture. Fixed width [1], 1 character descriptive code. Codes: H = HS PHY L = LP PHY U = UT PHY P = Phase PHY (obsolete)"

# Pattern 2: Fixed width field specification
fixed_width_pattern = r'Fixed width \[(\d+)\]'
# Example: "Fixed width [1]" extracts "1"

# Pattern 3: Valid code enumeration
valid_codes_pattern = r'Codes?:\s*([A-Z]\s*=\s*[^,]+(?:,\s*[A-Z]\s*=\s*[^,]+)*)'
# Example: "Codes: H = HS PHY L = LP PHY U = UT PHY" extracts the full code list

# Pattern 4: Delimiter fields
delimiter_pattern = r'^([_$])\s*//\s*(.+delimiter.+)$'
# Example: "_       // delimiter between protocol names and process name"

# Pattern 5: Variable width fields
variable_width_pattern = r'^([A-Z0-9]+)\s*//\s*.*(Variable width|variable width).*$'
# Example: "D5D4    // Protocol Code, the DDR protocol(s) supported by the design at the PHY level. Variable width"

# Pattern 6: CTIME format validation
ctime_pattern = r'^C\d{12}$'
# Example: "C202401151430" (C + YYYYMMDDhhmm)
```

### Detection Logic

1. **File Existence Check**: Verify phy_iptag.prod file exists at the specified path
2. **Line-by-Line Parsing**:
   - Skip comment lines starting with '#'
   - Extract field value (before //) and description (after //)
   - Build ordered list of fields maintaining sequence
3. **Field Validation**:
   - Parse field descriptions to extract: fixed width constraints, valid codes, field type
   - Validate field values against extracted constraints
   - Check fixed width fields match specified length
   - Verify field values are in allowed code lists
4. **Delimiter Validation**:
   - Check delimiter sequence: underscore (_) between major sections
   - Verify dollar sign ($) appears before configuration string
   - Ensure delimiters are in correct positions
5. **Special Field Validation**:
   - CTIME format: Must be 'C' followed by 12 digits (YYYYMMDDhhmm)
   - Protocol codes: Validate order (DDR highest to lowest, then LPDDR)
   - Configuration string: Verify format after final $ delimiter
6. **End Marker Check**: Confirm file ends with 'End' marker
7. **Overall Compliance**: Report PASS if all fields meet the rule requirements

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

**Rationale:** This checker validates the IPTAG configuration file against format rules. The user hint states "parser phy_iptag.prod is met the rule", indicating this is a status check to verify the file meets formatting requirements. The checker validates field formats, codes, delimiters, and overall structure compliance rather than checking for existence of specific items.

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
item_desc = "Confirm you followed the below document about IPTAG creation. If you have further question, please check with Tobing. HSPHY/HPPHY/DFPHY/GDDR/HBM: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/_layouts/15/Doc.aspx?sourcedoc=%7B26DAB946-483A-415F-AC0C-C195C0838506%7D&file=IP%20Number%20Format%20-%20DDR%20PHY.docx&wdLOR=cF5835961-1465-461D-BAFD-3F0590F6A7F9&action=default&mobileredirect=true SERDES: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/IP_Numbers/IP%20Number%20Format%20-%20SerDes.docx?d=wf015c37bca9b4d3d951589cf616333fe&csf=1&web=1"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "IPTAG configuration file found and validated"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "IPTAG configuration meets all format requirements"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "IPTAG configuration file found and all fields validated successfully"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All IPTAG fields matched required format rules and validated successfully"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "IPTAG configuration file not found or validation failed"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "IPTAG configuration has format violations"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "IPTAG configuration file not found or contains invalid fields"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "IPTAG format requirements not satisfied - field validation failed"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "IPTAG format violations waived per design approval"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "IPTAG format violation waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused IPTAG waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding IPTAG format violation found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "[field_name]: [value] (valid) - [description]"
  Example: "PHY Architecture: H (valid) - HS PHY"
  Example: "Protocol Code: D5D4 (valid) - DDR5/DDR4 support"
  Example: "Process Name: T5G (valid) - TSMC 5nm process"

ERROR01 (Violation/Fail items):
  Format: "[field_name]: [error_type] - Expected: [expected_format], Found: [actual_value]"
  Example: "Protocol Code: Invalid delimiter - Expected: '_' after protocol codes, Found: missing delimiter"
  Example: "PHY Architecture: Invalid code - Expected: H|L|U|P, Found: X"
  Example: "CTIME: Invalid format - Expected: C + 12 digits (YYYYMMDDhhmm), Found: C20240115"
  Example: "Fixed Width Violation: Field 'IO Vendor' - Expected: 1 character, Found: 2 characters (AB)"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-16-0-0-06:
  description: "Confirm you followed the below document about IPTAG creation. If you have further question, please check with Tobing. HSPHY/HPPHY/DFPHY/GDDR/HBM: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/_layouts/15/Doc.aspx?sourcedoc=%7B26DAB946-483A-415F-AC0C-C195C0838506%7D&file=IP%20Number%20Format%20-%20DDR%20PHY.docx&wdLOR=cF5835961-1465-461D-BAFD-3F0590F6A7F9&action=default&mobileredirect=true SERDES: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/IP_Numbers/IP%20Number%20Format%20-%20SerDes.docx?d=wf015c37bca9b4d3d951589cf616333fe&csf=1&web=1"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/phy_iptag.prod
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
Reason: IPTAG configuration file found and all fields validated successfully
INFO01:
  - PHY Architecture: H (valid) - HS PHY
  - IP Type: P (valid) - PHY IP
  - IO Vendor: C (valid) - Cadence IO
  - Protocol Code: D5D4 (valid) - DDR5/DDR4 support
  - Process Name: T5G (valid) - TSMC 5nm process
  - CTIME: C202401151430 (valid) - Creation timestamp
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: IPTAG configuration file not found or contains invalid fields
ERROR01:
  - PHY Architecture: Invalid code - Expected: H|L|U|P, Found: X
  - Protocol Code: Invalid delimiter - Expected: '_' after protocol codes, Found: missing delimiter
  - CTIME: Invalid format - Expected: C + 12 digits (YYYYMMDDhhmm), Found: C20240115
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-16-0-0-06:
  description: "Confirm you followed the below document about IPTAG creation. If you have further question, please check with Tobing. HSPHY/HPPHY/DFPHY/GDDR/HBM: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/_layouts/15/Doc.aspx?sourcedoc=%7B26DAB946-483A-415F-AC0C-C195C0838506%7D&file=IP%20Number%20Format%20-%20DDR%20PHY.docx&wdLOR=cF5835961-1465-461D-BAFD-3F0590F6A7F9&action=default&mobileredirect=true SERDES: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/IP_Numbers/IP%20Number%20Format%20-%20SerDes.docx?d=wf015c37bca9b4d3d951589cf616333fe&csf=1&web=1"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/phy_iptag.prod
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: IPTAG format validation is informational only during early development phase"
      - "Note: Format violations are expected in pre-release builds and will be fixed before tape-out"
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
  - "Explanation: IPTAG format validation is informational only during early development phase"
  - "Note: Format violations are expected in pre-release builds and will be fixed before tape-out"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - PHY Architecture: Invalid code - Expected: H|L|U|P, Found: X [WAIVED_AS_INFO]
  - Protocol Code: Invalid delimiter - Expected: '_' after protocol codes, Found: missing delimiter [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-16-0-0-06:
  description: "Confirm you followed the below document about IPTAG creation. If you have further question, please check with Tobing. HSPHY/HPPHY/DFPHY/GDDR/HBM: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/_layouts/15/Doc.aspx?sourcedoc=%7B26DAB946-483A-415F-AC0C-C195C0838506%7D&file=IP%20Number%20Format%20-%20DDR%20PHY.docx&wdLOR=cF5835961-1465-461D-BAFD-3F0590F6A7F9&action=default&mobileredirect=true SERDES: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/IP_Numbers/IP%20Number%20Format%20-%20SerDes.docx?d=wf015c37bca9b4d3d951589cf616333fe&csf=1&web=1"
  requirements:
    value: 3
    pattern_items:
      - "PHY Architecture"
      - "Protocol Code"
      - "Process Name"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/phy_iptag.prod
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS/FAIL depends on check purpose:
- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)

**Sample Output (PASS):**
```
Status: PASS
Reason: All IPTAG fields matched required format rules and validated successfully
INFO01:
  - PHY Architecture: H (valid) - HS PHY
  - Protocol Code: D5D4 (valid) - DDR5/DDR4 support
  - Process Name: T5G (valid) - TSMC 5nm process
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-16-0-0-06:
  description: "Confirm you followed the below document about IPTAG creation. If you have further question, please check with Tobing. HSPHY/HPPHY/DFPHY/GDDR/HBM: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/_layouts/15/Doc.aspx?sourcedoc=%7B26DAB946-483A-415F-AC0C-C195C0838506%7D&file=IP%20Number%20Format%20-%20DDR%20PHY.docx&wdLOR=cF5835961-1465-461D-BAFD-3F0590F6A7F9&action=default&mobileredirect=true SERDES: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/IP_Numbers/IP%20Number%20Format%20-%20SerDes.docx?d=wf015c37bca9b4d3d951589cf616333fe&csf=1&web=1"
  requirements:
    value: 0
    pattern_items:
      - "PHY Architecture"
      - "Protocol Code"
      - "Process Name"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/phy_iptag.prod
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: IPTAG field validation is informational during development - format mismatches are expected"
      - "Note: Field format violations will be resolved before final release per IPTAG documentation requirements"
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
  - "Explanation: IPTAG field validation is informational during development - format mismatches are expected"
  - "Note: Field format violations will be resolved before final release per IPTAG documentation requirements"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - PHY Architecture: Invalid code - Expected: H|L|U|P, Found: X [WAIVED_AS_INFO]
  - Protocol Code: Invalid delimiter - Expected: '_' after protocol codes, Found: missing delimiter [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-16-0-0-06:
  description: "Confirm you followed the below document about IPTAG creation. If you have further question, please check with Tobing. HSPHY/HPPHY/DFPHY/GDDR/HBM: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/_layouts/15/Doc.aspx?sourcedoc=%7B26DAB946-483A-415F-AC0C-C195C0838506%7D&file=IP%20Number%20Format%20-%20DDR%20PHY.docx&wdLOR=cF5835961-1465-461D-BAFD-3F0590F6A7F9&action=default&mobileredirect=true SERDES: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/IP_Numbers/IP%20Number%20Format%20-%20SerDes.docx?d=wf015c37bca9b4d3d951589cf616333fe&csf=1&web=1"
  requirements:
    value: 3
    pattern_items:
      - "PHY Architecture"
      - "Protocol Code"
      - "Process Name"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/phy_iptag.prod
  waivers:
    value: 2
    waive_items:
      - name: "PHY Architecture: Invalid code - Expected: H|L|U|P, Found: X"
        reason: "Waived - experimental PHY architecture code 'X' approved for internal testing builds"
      - name: "Protocol Code: Invalid delimiter - Expected: '_' after protocol codes, Found: missing delimiter"
        reason: "Waived - legacy IPTAG format used for backward compatibility with existing tools"
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
INFO01 (Waived):
  - PHY Architecture: Invalid code - Expected: H|L|U|P, Found: X [WAIVER]
  - Protocol Code: Invalid delimiter - Expected: '_' after protocol codes, Found: missing delimiter [WAIVER]
WARN01 (Unused Waivers):
  - (none - all waivers matched)
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-16-0-0-06:
  description: "Confirm you followed the below document about IPTAG creation. If you have further question, please check with Tobing. HSPHY/HPPHY/DFPHY/GDDR/HBM: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/_layouts/15/Doc.aspx?sourcedoc=%7B26DAB946-483A-415F-AC0C-C195C0838506%7D&file=IP%20Number%20Format%20-%20DDR%20PHY.docx&wdLOR=cF5835961-1465-461D-BAFD-3F0590F6A7F9&action=default&mobileredirect=true SERDES: https://cadence.sharepoint.com/:w:/r/sites/IPGroup/DesignIP/Quality/IP_Numbers/IP%20Number%20Format%20-%20SerDes.docx?d=wf015c37bca9b4d3d951589cf616333fe&csf=1&web=1"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/phy_iptag.prod
  waivers:
    value: 2
    waive_items:
      - name: "PHY Architecture: Invalid code - Expected: H|L|U|P, Found: X"
        reason: "Waived - experimental PHY architecture code 'X' approved for internal testing builds"
      - name: "Protocol Code: Invalid delimiter - Expected: '_' after protocol codes, Found: missing delimiter"
        reason: "Waived - legacy IPTAG format used for backward compatibility with existing tools"
```

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
  - PHY Architecture: Invalid code - Expected: H|L|U|P, Found: X [WAIVER]
  - Protocol Code: Invalid delimiter - Expected: '_' after protocol codes, Found: missing delimiter [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 16.0_IPTAG_CHECK --checkers IMP-16-0-0-06 --force

# Run individual tests
python IMP-16-0-0-06.py
```

---

## Notes

- The checker validates IPTAG configuration against Cadence SharePoint documentation standards for DDR PHY and SERDES IP types
- Field validation includes: fixed width constraints, valid code enumeration, delimiter placement, and special format requirements (CTIME)
- Protocol codes must be ordered correctly: DDR protocols from highest to lowest version, followed by LPDDR protocols
- The 'End' marker is required at the end of the configuration file
- CTIME format must be 'C' followed by exactly 12 digits representing YYYYMMDDhhmm timestamp
- Delimiter validation ensures proper structure: underscore (_) between sections, dollar sign ($) before configuration string
- The checker supports both DDR PHY (HSPHY/HPPHY/DFPHY/GDDR/HBM) and SERDES IP number formats as documented in the respective SharePoint links