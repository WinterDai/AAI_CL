# IMP-16-0-0-00: Confirm the IPTAG content and format are correct.(check the Note)

## Overview

**Check ID:** IMP-16-0-0-00  
**Description:** Confirm the IPTAG content and format are correct.(check the Note)  
**Category:** IPTAG Configuration Validation  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/phy_iptag.prod`

This checker validates the DDR PHY IP Tag product name configuration file for TSMC IP Tag writer. It verifies that all required fields are present, correctly formatted, and contain valid values according to the IPTAG specification. The checker validates field positions, delimiter placement, allowed code values, and file structure integrity.

---

## Check Logic

### Input Parsing
The checker parses the IPTAG configuration file line-by-line, filtering out comment lines (starting with `#` or `###`) and extracting field values with their positions. Each non-comment line contains a field value followed by a comment describing the field purpose.

**Key Patterns:**
```python
# Pattern 1: Comment lines to skip
comment_pattern = r'^\s*#.*$|^\s*###.*$'
# Example: "### Example DDR IP tag product name input for TSMC IP Tag writer"

# Pattern 2: Field value lines (extract value before comment)
field_pattern = r'^([A-Z0-9_$]+)\s*//'
# Example: "H       // DDR PHY Architecture. Fixed width [1]"
# Example: "D5D4    // Protocol Code, the DDR protocol(s) supported"
# Example: "T5G  // Process Name, identifies the foundry"

# Pattern 3: Delimiter markers
delimiter_pattern = r'^(_|\$)\s*//.*delimiter'
# Example: "_       // delimiter between phy type and protocol names"
# Example: "$       // IP Tag delimiter between product name and configuration name"

# Pattern 4: End marker
end_pattern = r'^End\s*$'
# Example: "End"

# Pattern 5: CTIME placeholder for release date
ctime_pattern = r'^CTIME\s*//.*Release Date Code'
# Example: "CTIME  //Please don't change this item. Release Date Code"
```

### Detection Logic
1. **Filter and Extract**: Remove comment lines and extract field values in order
2. **Field Count Validation**: Verify expected number of fields (13 fields based on specification)
3. **Field Value Validation**: For each field position, validate value against allowed codes:
   - Field 1 (PHY_Architecture): Must be H/L/U/P (single character)
   - Field 2 (IP_Type): Must be P (single character)
   - Field 3 (IO_Type): Must be C (single character)
   - Field 4 (Package): Must be F (single character)
   - Field 5 (PLL_Vendor): Must be S (single character)
   - Field 6 (PHY_Source): Must be C (single character)
   - Field 7 (Delimiter1): Must be _ (underscore)
   - Field 8 (Protocol): Variable width, validate format (e.g., D5D4, D5, D4D3)
   - Field 9 (Delimiter2): Must be _ (underscore)
   - Field 10 (Process): Must be valid process code (e.g., T5G, T7G)
   - Field 11 (Release_Date): Must be CTIME or C followed by 12 digits (YYYYMMDDhhmm)
   - Field 12 (Delimiter3): Must be $ (dollar sign)
   - Field 13 (Configuration): Variable width configuration string
4. **Delimiter Position Validation**: Verify delimiters appear at correct positions (7, 9, 12)
5. **End Marker Validation**: Confirm file terminates with "End" marker
6. **Trailing Content Check**: Warn if content exists after End marker

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

**Rationale:** This checker validates the format and content of IPTAG fields. The pattern_items represent specific field validation rules that must be satisfied. The checker examines each field's status (valid/invalid format, correct/incorrect value) and only outputs items that are validated. Fields with incorrect values or formats are reported as missing_items (validation failed), while correctly formatted fields are reported as found_items (validation passed).

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
item_desc = "Confirm the IPTAG content and format are correct.(check the Note)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "IPTAG configuration file found and validated successfully"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All IPTAG fields validated and format requirements satisfied"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "IPTAG configuration file found with all required fields present"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All IPTAG field formats matched specification and values validated successfully"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "IPTAG configuration file not found or missing required structure"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "IPTAG field validation failed - format or value requirements not satisfied"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "IPTAG configuration file not found or End marker missing"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "IPTAG field validation failed - invalid values or format requirements not satisfied"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "IPTAG validation errors waived per design team approval"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "IPTAG field validation error waived - approved exception for this configuration"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused IPTAG waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding IPTAG validation error found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "[field_name]: [value] (valid)"
  Example: "PHY_Architecture: H (valid)"
  Example: "Protocol: D5D4 (valid)"
  Example: "Process: T5G (valid)"
  Example: "Release_Date: CTIME (valid)"

ERROR01 (Violation/Fail items):
  Format: "[field_name]: Invalid value '[value]' - [error_description] (line: [line_number])"
  Example: "PHY_Architecture: Invalid value 'X' - must be H/L/U/P (line: 4)"
  Example: "Delimiter1: Invalid value '-' - must be underscore '_' (line: 10)"
  Example: "Release_Date: Invalid format 'C20250115' - must be CTIME or C followed by 12 digits (line: 14)"
  Example: "End marker: Missing - file must terminate with 'End' (line: EOF)"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-16-0-0-00:
  description: "Confirm the IPTAG content and format are correct.(check the Note)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/phy_iptag.prod"
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
Reason: IPTAG configuration file found with all required fields present
INFO01:
  - PHY_Architecture: H (valid)
  - IP_Type: P (valid)
  - IO_Type: C (valid)
  - Package: F (valid)
  - PLL_Vendor: S (valid)
  - PHY_Source: C (valid)
  - Delimiter1: _ (valid)
  - Protocol: D5D4 (valid)
  - Delimiter2: _ (valid)
  - Process: T5G (valid)
  - Release_Date: CTIME (valid)
  - Delimiter3: $ (valid)
  - Configuration: 17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R (valid)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: IPTAG configuration file not found or End marker missing
ERROR01:
  - PHY_Architecture: Invalid value 'X' - must be H/L/U/P (line: 4)
  - Delimiter1: Invalid value '-' - must be underscore '_' (line: 10)
  - End marker: Missing - file must terminate with 'End' (line: EOF)
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-16-0-0-00:
  description: "Confirm the IPTAG content and format are correct.(check the Note)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/phy_iptag.prod"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: IPTAG validation is informational during early development phase"
      - "Note: Field format violations are expected in prototype configurations and will be fixed before release"
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
  - "Explanation: IPTAG validation is informational during early development phase"
  - "Note: Field format violations are expected in prototype configurations and will be fixed before release"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - PHY_Architecture: Invalid value 'X' - must be H/L/U/P (line: 4) [WAIVED_AS_INFO]
  - Delimiter1: Invalid value '-' - must be underscore '_' (line: 10) [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-16-0-0-00:
  description: "Confirm the IPTAG content and format are correct.(check the Note)"
  requirements:
    value: 3
    pattern_items:
      - "PHY_Architecture: H (valid)"
      - "Protocol: D5D4 (valid)"
      - "Process: T5G (valid)"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/phy_iptag.prod"
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
Reason: All IPTAG field formats matched specification and values validated successfully
INFO01:
  - PHY_Architecture: H (valid)
  - Protocol: D5D4 (valid)
  - Process: T5G (valid)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-16-0-0-00:
  description: "Confirm the IPTAG content and format are correct.(check the Note)"
  requirements:
    value: 3
    pattern_items:
      - "PHY_Architecture: H (valid)"
      - "Protocol: D5D4 (valid)"
      - "Process: T5G (valid)"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/phy_iptag.prod"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: IPTAG field validation is informational only during integration testing"
      - "Note: Pattern mismatches are expected when using alternative IPTAG formats and do not require fixes"
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
  - "Explanation: IPTAG field validation is informational only during integration testing"
  - "Note: Pattern mismatches are expected when using alternative IPTAG formats and do not require fixes"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - PHY_Architecture: Invalid value 'X' - must be H/L/U/P (line: 4) [WAIVED_AS_INFO]
  - Protocol: Invalid format 'D6' - unsupported protocol code (line: 11) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-16-0-0-00:
  description: "Confirm the IPTAG content and format are correct.(check the Note)"
  requirements:
    value: 3
    pattern_items:
      - "PHY_Architecture: H (valid)"
      - "Protocol: D5D4 (valid)"
      - "Process: T5G (valid)"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/phy_iptag.prod"
  waivers:
    value: 2
    waive_items:
      - name: "PHY_Architecture: Invalid value 'X' - must be H/L/U/P (line: 4)"
        reason: "Waived - experimental PHY architecture code approved for prototype testing"
      - name: "Protocol: Invalid format 'D6' - unsupported protocol code (line: 11)"
        reason: "Waived - DDR6 protocol code pre-approved for future IP development"
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
  - PHY_Architecture: Invalid value 'X' - must be H/L/U/P (line: 4) [WAIVER]
  - Protocol: Invalid format 'D6' - unsupported protocol code (line: 11) [WAIVER]
WARN01 (Unused Waivers):
  - Delimiter1: Invalid value '-' - must be underscore '_' (line: 10): Waiver not matched - no corresponding IPTAG validation error found
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-16-0-0-00:
  description: "Confirm the IPTAG content and format are correct.(check the Note)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/phy_iptag.prod"
  waivers:
    value: 2
    waive_items:
      - name: "PHY_Architecture: Invalid value 'X' - must be H/L/U/P (line: 4)"
        reason: "Waived - experimental PHY architecture code approved for prototype testing"
      - name: "Protocol: Invalid format 'D6' - unsupported protocol code (line: 11)"
        reason: "Waived - DDR6 protocol code pre-approved for future IP development"
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
  - PHY_Architecture: Invalid value 'X' - must be H/L/U/P (line: 4) [WAIVER]
  - Protocol: Invalid format 'D6' - unsupported protocol code (line: 11) [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 16.0_IPTAG_CHECK --checkers IMP-16-0-0-00 --force

# Run individual tests
python IMP-16-0-0-00.py
```

---

## Notes

- The IPTAG file must contain exactly 13 fields in the specified order
- Comment lines (starting with # or ###) are ignored during parsing
- The file must terminate with an "End" marker
- CTIME is a special placeholder for release date that will be replaced during IP tag generation
- Delimiters must appear at specific positions: underscore (_) at positions 7 and 9, dollar sign ($) at position 12
- Field widths are either fixed (single character) or variable (multi-character codes)
- Invalid field values will cause validation failure even if the file structure is correct
- Trailing content after the End marker will generate a warning but not fail the check
- The Protocol field supports multiple DDR protocol combinations (e.g., D5D4, D5, D4D3, L4L3)
- Process codes must match valid foundry process identifiers (e.g., T5G for TSMC 5nm, T7G for TSMC 7nm)