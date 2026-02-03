# IMP-7-0-0-00: Block name (e.g: cdn_hs_phy_data_slice)

## Overview

**Check ID:** IMP-7-0-0-00  
**Description:** Block name (e.g: cdn_hs_phy_data_slice)  
**Category:** Implementation Design-In Check  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt`

This checker validates the block name header in the Innovus implementation report. It extracts and verifies the block name from the report file to ensure proper block identification for implementation milestone IMP-7-0-0-00. The checker confirms that the block name is present and properly formatted in the report header.

---

## Check Logic

### Input Parsing

The checker parses the implementation report file to extract the block name from the header section.

**Key Patterns:**
```python
# Pattern 1: Block name header extraction
pattern1 = r'^Block\s+name:\s*([A-Za-z0-9_]+)\s*(?:#.*)?$'
# Example: "Block name: CDN_104H_cdn_hs_phy_data_slice_EW  # Limit to 10KB"

# Pattern 2: Section headers for report structure
pattern2 = r'^={3,}\s*(.+?)\s*={3,}$|^-{3,}\s*(.+?)\s*-{3,}$'
# Example: "========== Implementation Summary =========="

# Pattern 3: Metric summary lines (if present)
pattern3 = r'^\s*([A-Za-z\s]+)\s*:\s*([0-9.]+)\s*([a-zA-Zμ²³%]+)?\s*$'
# Example: "Total Area        : 1234.567 um²"
```

### Detection Logic

1. **Read Report File**: Open and read the IMP-7-0-0-00.rpt file
2. **Extract Block Name**: Search for the "Block name:" header pattern in the first few lines
3. **Validate Format**: Verify the block name matches expected naming conventions (alphanumeric + underscores)
4. **Report Results**:
   - **PASS**: Block name found and properly formatted
   - **FAIL**: Block name missing, malformed, or file unreadable

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
item_desc = "Block name (e.g: cdn_hs_phy_data_slice)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "Block name found in implementation report"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "Block name pattern matched in report header"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Block name successfully extracted from report header"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Block name pattern matched and validated in report"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Block name not found in implementation report"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Block name pattern not satisfied in report header"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Block name header missing or malformed in report file"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Block name pattern not satisfied or missing from report"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Block name validation waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Block name check waived per implementation team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries for block name check"
unused_waiver_reason = "Waiver not matched - no corresponding block name issue found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "Block: {block_name} | Report: {report_file}"
  Example: "Block: CDN_104H_cdn_hs_phy_data_slice_EW | Report: IMP-7-0-0-00.rpt"

ERROR01 (Violation/Fail items):
  Format: "ERROR: {error_type} - {details}"
  Example: "ERROR: Block name header missing from report file IMP-7-0-0-00.rpt"
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
Reason: Block name successfully extracted from report header
INFO01:
  - Block: CDN_104H_cdn_hs_phy_data_slice_EW | Report: IMP-7-0-0-00.rpt
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Block name header missing or malformed in report file
ERROR01:
  - ERROR: Block name header missing from report file IMP-7-0-0-00.rpt
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
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Block name validation is informational only for early implementation milestones"
      - "Note: Missing block names are expected in preliminary reports and do not block design progress"
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
  - "Explanation: Block name validation is informational only for early implementation milestones"
  - "Note: Missing block names are expected in preliminary reports and do not block design progress"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - ERROR: Block name header missing from report file IMP-7-0-0-00.rpt [WAIVED_AS_INFO]
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
      - "CDN_104H_cdn_hs_phy_data_slice_EW"
      - "CDN_104H_cdn_hs_phy_ctrl_slice_NS"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt"
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
Reason: Block name pattern matched and validated in report
INFO01:
  - Block: CDN_104H_cdn_hs_phy_data_slice_EW | Report: IMP-7-0-0-00.rpt
  - Block: CDN_104H_cdn_hs_phy_ctrl_slice_NS | Report: IMP-7-0-0-00.rpt
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-7-0-0-00:
  description: "Block name (e.g: cdn_hs_phy_data_slice)"
  requirements:
    value: 0
    pattern_items:
      - "CDN_104H_cdn_hs_phy_data_slice_EW"
      - "CDN_104H_cdn_hs_phy_ctrl_slice_NS"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Block name pattern check is informational only during development phase"
      - "Note: Pattern mismatches are expected when testing alternative naming conventions"
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
  - "Explanation: Block name pattern check is informational only during development phase"
  - "Note: Pattern mismatches are expected when testing alternative naming conventions"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - ERROR: Block name 'CDN_104H_cdn_hs_phy_ctrl_slice_NS' not found in report [WAIVED_AS_INFO]
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
      - "CDN_104H_cdn_hs_phy_data_slice_EW"
      - "CDN_104H_cdn_hs_phy_ctrl_slice_NS"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "CDN_104H_cdn_hs_phy_data_slice_EW"
        reason: "Waived - legacy block name retained for backward compatibility"
      - name: "CDN_104H_cdn_hs_phy_ctrl_slice_NS"
        reason: "Waived - alternative naming convention approved by design team"
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
  - Block: CDN_104H_cdn_hs_phy_data_slice_EW | Waived - legacy block name retained for backward compatibility [WAIVER]
  - Block: CDN_104H_cdn_hs_phy_ctrl_slice_NS | Waived - alternative naming convention approved by design team [WAIVER]
WARN01 (Unused Waivers):
  - (none)
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
        reason: "Waived - legacy block name retained for backward compatibility"
      - name: "CDN_104H_cdn_hs_phy_ctrl_slice_NS"
        reason: "Waived - alternative naming convention approved by design team"
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
  - Block: CDN_104H_cdn_hs_phy_data_slice_EW | Waived - legacy block name retained for backward compatibility [WAIVER]
  - Block: CDN_104H_cdn_hs_phy_ctrl_slice_NS | Waived - alternative naming convention approved by design team [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 7.0_INNOVUS_DESIGN_IN_CHECK --checkers IMP-7-0-0-00 --force

# Run individual tests
python IMP-7-0-0-00.py
```

---

## Notes

- **File Format**: The checker expects the block name to appear in the first 50 lines of the report file with the format "Block name: <name>"
- **Naming Convention**: Block names should follow the pattern: `[PREFIX]_[VERSION]_[module_name]_[SUFFIX]` (e.g., CDN_104H_cdn_hs_phy_data_slice_EW)
- **Truncation Handling**: The report may contain a comment "# Limit to 10KB" indicating file truncation - the checker handles this gracefully
- **Multiple Reports**: If checking multiple milestone reports, each report should contain its own block name header
- **Case Sensitivity**: Block name matching is case-sensitive
- **Known Limitations**: 
  - Cannot validate block name correctness against design database (only checks presence/format)
  - Does not verify block name consistency across multiple reports
  - Assumes UTF-8 encoding for report files