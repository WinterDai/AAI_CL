# IMP-16-0-0-05: Confirm remove the FIRM PHY slices IPTAG if FIRM PHY slices are reused in Hard PHY project.

## Overview

**Check ID:** IMP-16-0-0-05  
**Description:** Confirm remove the FIRM PHY slices IPTAG if FIRM PHY slices are reused in Hard PHY project.  
**Category:** IP Tag Verification  
**Input Files:** 
- `${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/cdn_hs_phy_top.csv`

This checker verifies that FIRM PHY slice instances (Cadence IP blocks like cdn_hs_phy_top, cdns_ddr_atb_h) have their IPTAGs properly removed when reused in Hard PHY projects. The check is conditional on IMP-16-0-0-04 status - only executes if IMP-16-0-0-04 passes. It parses the IP_checker CSV report to identify Cadence FIRM PHY instances and validates that their instance IPTAG matches the block IPTAG (indicating proper IPTAG removal).

---

## Check Logic

### Input Parsing

The checker parses the IP_checker CSV report containing GDS instance information with vendor, product, version, metric, and IPTAG data.

**Key Patterns:**
```python
# Pattern 1: CSV header validation
header_pattern = r'^GDS\s*,\s*Vendor\s*,\s*Product\s*,\s*Version\s*,\s*Metric\s*,\s*Instance\s*,\s*Instance_tag'
# Example: "GDS                 ,Vendor    ,Product   ,Version   ,Metric    ,Instance  ,Instance_tag"

# Pattern 2: Cadence FIRM PHY slice instances
cadence_pattern = r'^([^,]+\.gds),\s*"Cadence Design Systems, Inc\."\s*,\s*([^,]+)\s*,\s*"([^"]+)"\s*,\s*([0-9.]+)\s*,\s*([^,]+)\s*,\s*"([^"]+)"'
# Example: 'cdn_hs_phy_top.wIPTAG.gds,"Cadence Design Systems, Inc.",HPCFSC_D5D4_T5G$C202209262108$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R,"R100",0.0,cdn_hs_phy_top,"cdn_hs_phy_top"'

# Pattern 3: FIRM PHY product family identification
firm_phy_pattern = r'(HPCFSC_|DDR\d+_|cdn_hs_phy_|cdns_ddr_)'
# Example: "HPCFSC_D5D4_T5G", "DDR500_T5G", "cdn_hs_phy_top", "cdns_ddr_atb_h"

# Pattern 4: TSMC instances (for statistics)
tsmc_pattern = r'^([^,]+\.gds),\s*"Taiwan Semiconductor Manufacturing Corp\."\s*,\s*([^,]+)\s*,\s*"([^"]+)"\s*,\s*([0-9.]+)\s*,\s*([^,]+)\s*,\s*"([^"]+)"'
# Example: 'cdn_hs_phy_top.wIPTAG.gds,"Taiwan Semiconductor Manufacturing Corp.",tcbn05_bwph280l6p57cnod_base_lvt,"110a",0.096,AIOI21KAD1BWP280H6P57CNODLVT,"AIOI21KAD1BWP280H6P57CNODLVT"'
```

### Detection Logic

1. **Prerequisite Check**: Verify IMP-16-0-0-04 status
   - If IMP-16-0-0-04 == "yes": Proceed with IPTAG validation
   - If IMP-16-0-0-04 != "yes": Return NA (check not applicable)

2. **CSV Parsing**:
   - Skip metadata header lines (IP_checker tool info)
   - Locate CSV header line starting with "GDS"
   - Parse data rows using csv.DictReader

3. **Instance Categorization**:
   - Separate instances by vendor (Cadence vs TSMC)
   - Filter Cadence instances matching FIRM PHY patterns (HPCFSC_, DDR\d+_, cdn_hs_phy_, cdns_ddr_)
   - Collect statistics for INFO01 display

4. **IPTAG Validation** (per user hint: "if phy iptag == block iptag then yes else Error"):
   - For each Cadence FIRM PHY instance:
     - Extract instance name (column: Instance)
     - Extract instance_tag (column: Instance_tag)
     - Compare: if instance == instance_tag → PASS (IPTAG properly removed)
     - Compare: if instance != instance_tag → FAIL (IPTAG mismatch - ERROR)

5. **Result Classification**:
   - **PASS items (INFO01)**: Cadence FIRM PHY instances where instance == instance_tag
   - **FAIL items (ERROR01)**: Cadence FIRM PHY instances where instance != instance_tag
   - **Overall PASS**: All Cadence FIRM PHY instances have matching IPTAGs
   - **Overall FAIL**: Any Cadence FIRM PHY instance has mismatched IPTAG

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

**Rationale:** This checker validates the IPTAG removal status for specific Cadence FIRM PHY instances. The pattern_items (when configured) represent specific instances to check, and the checker validates whether their IPTAG status is correct (instance == instance_tag). Only instances matching the pattern_items are validated and reported - other instances in the CSV are ignored. This is a status validation check, not an existence check.

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
item_desc = "Confirm remove the FIRM PHY slices IPTAG if FIRM PHY slices are reused in Hard PHY project."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "All Cadence FIRM PHY instances found with correct IPTAG removal"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All specified FIRM PHY instances matched with correct IPTAG status"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "All Cadence FIRM PHY slice instances found with instance IPTAG matching block IPTAG (proper IPTAG removal confirmed)"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All specified FIRM PHY instances matched and validated with correct IPTAG removal status (instance == instance_tag)"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "FIRM PHY instances found with IPTAG mismatch (IPTAG not properly removed)"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Specified FIRM PHY instances not satisfied - IPTAG mismatch detected"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "FIRM PHY slice instances found where instance IPTAG does not match block IPTAG (IPTAG removal incomplete)"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Specified FIRM PHY instances not satisfied - instance IPTAG does not match block IPTAG (validation failed)"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "FIRM PHY IPTAG mismatches waived per design approval"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "FIRM PHY IPTAG mismatch waived - approved exception for Hard PHY project reuse"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused IPTAG waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding IPTAG mismatch found for this instance"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "[instance_name] Product: {product} Version: {version} | IPTAG: {instance_tag} (Vendor: {vendor})"
  Example: "cdn_hs_phy_top Product: HPCFSC_D5D4_T5G$C202209262108$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R Version: R100 | IPTAG: cdn_hs_phy_top (Vendor: Cadence Design Systems, Inc.)"

ERROR01 (Violation/Fail items):
  Format: "[instance_name] IPTAG MISMATCH: instance={instance} but instance_tag={instance_tag} | Product: {product} Version: {version} (Vendor: {vendor})"
  Example: "cdn_hs_phy_top IPTAG MISMATCH: instance=cdn_hs_phy_top but instance_tag=cdn_hs_phy_top_v2 | Product: HPCFSC_D5D4_T5G Version: R100 (Vendor: Cadence Design Systems, Inc.)"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-16-0-0-05:
  description: "Confirm remove the FIRM PHY slices IPTAG if FIRM PHY slices are reused in Hard PHY project."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/cdn_hs_phy_top.csv
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
Reason: All Cadence FIRM PHY slice instances found with instance IPTAG matching block IPTAG (proper IPTAG removal confirmed)
INFO01:
  - cdn_hs_phy_top Product: HPCFSC_D5D4_T5G$C202209262108$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R Version: R100 | IPTAG: cdn_hs_phy_top (Vendor: Cadence Design Systems, Inc.)
  - cdns_ddr_atb_h Product: DDR500_T5G Version: R100 | IPTAG: cdns_ddr_atb_h (Vendor: Cadence Design Systems, Inc.)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: FIRM PHY slice instances found where instance IPTAG does not match block IPTAG (IPTAG removal incomplete)
ERROR01:
  - cdn_hs_phy_top IPTAG MISMATCH: instance=cdn_hs_phy_top but instance_tag=cdn_hs_phy_top_old | Product: HPCFSC_D5D4_T5G Version: R100 (Vendor: Cadence Design Systems, Inc.)
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-16-0-0-05:
  description: "Confirm remove the FIRM PHY slices IPTAG if FIRM PHY slices are reused in Hard PHY project."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/cdn_hs_phy_top.csv
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: IPTAG validation is informational only for this Hard PHY project phase"
      - "Note: IPTAG mismatches are expected during integration and will be resolved in final release"
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
  - "Explanation: IPTAG validation is informational only for this Hard PHY project phase"
  - "Note: IPTAG mismatches are expected during integration and will be resolved in final release"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - cdn_hs_phy_top IPTAG MISMATCH: instance=cdn_hs_phy_top but instance_tag=cdn_hs_phy_top_old | Product: HPCFSC_D5D4_T5G Version: R100 (Vendor: Cadence Design Systems, Inc.) [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-16-0-0-05:
  description: "Confirm remove the FIRM PHY slices IPTAG if FIRM PHY slices are reused in Hard PHY project."
  requirements:
    value: 2
    pattern_items:
      - "cdn_hs_phy_top"
      - "cdns_ddr_atb_h"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/cdn_hs_phy_top.csv
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
Reason: All specified FIRM PHY instances matched and validated with correct IPTAG removal status (instance == instance_tag)
INFO01:
  - cdn_hs_phy_top Product: HPCFSC_D5D4_T5G$C202209262108$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R Version: R100 | IPTAG: cdn_hs_phy_top (Vendor: Cadence Design Systems, Inc.)
  - cdns_ddr_atb_h Product: DDR500_T5G Version: R100 | IPTAG: cdns_ddr_atb_h (Vendor: Cadence Design Systems, Inc.)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-16-0-0-05:
  description: "Confirm remove the FIRM PHY slices IPTAG if FIRM PHY slices are reused in Hard PHY project."
  requirements:
    value: 2
    pattern_items:
      - "cdn_hs_phy_top"
      - "cdns_ddr_atb_h"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/cdn_hs_phy_top.csv
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: IPTAG pattern validation is informational only during Hard PHY integration phase"
      - "Note: Pattern mismatches for specified instances are expected and will be corrected in final tape-out"
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
  - "Explanation: IPTAG pattern validation is informational only during Hard PHY integration phase"
  - "Note: Pattern mismatches for specified instances are expected and will be corrected in final tape-out"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - cdn_hs_phy_top IPTAG MISMATCH: instance=cdn_hs_phy_top but instance_tag=cdn_hs_phy_top_v1 | Product: HPCFSC_D5D4_T5G Version: R100 (Vendor: Cadence Design Systems, Inc.) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-16-0-0-05:
  description: "Confirm remove the FIRM PHY slices IPTAG if FIRM PHY slices are reused in Hard PHY project."
  requirements:
    value: 2
    pattern_items:
      - "cdn_hs_phy_top"
      - "cdns_ddr_atb_h"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/cdn_hs_phy_top.csv
  waivers:
    value: 2
    waive_items:
      - name: "cdn_hs_phy_top"
        reason: "Waived - legacy IPTAG retained per IP team approval for backward compatibility"
      - name: "cdns_ddr_atb_h"
        reason: "Waived - IPTAG mismatch approved for debug version during integration phase"
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
  - cdn_hs_phy_top IPTAG MISMATCH: instance=cdn_hs_phy_top but instance_tag=cdn_hs_phy_top_legacy | Product: HPCFSC_D5D4_T5G Version: R100 (Vendor: Cadence Design Systems, Inc.) [WAIVER]
  - cdns_ddr_atb_h IPTAG MISMATCH: instance=cdns_ddr_atb_h but instance_tag=cdns_ddr_atb_h_debug | Product: DDR500_T5G Version: R100 (Vendor: Cadence Design Systems, Inc.) [WAIVER]
WARN01 (Unused Waivers):
  - (none - all waivers matched)
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-16-0-0-05:
  description: "Confirm remove the FIRM PHY slices IPTAG if FIRM PHY slices are reused in Hard PHY project."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/cdn_hs_phy_top.csv
  waivers:
    value: 2
    waive_items:
      - name: "cdn_hs_phy_top"
        reason: "Waived - legacy IPTAG retained per IP team approval for backward compatibility"
      - name: "cdns_ddr_atb_h"
        reason: "Waived - IPTAG mismatch approved for debug version during integration phase"
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
  - cdn_hs_phy_top IPTAG MISMATCH: instance=cdn_hs_phy_top but instance_tag=cdn_hs_phy_top_legacy | Product: HPCFSC_D5D4_T5G Version: R100 (Vendor: Cadence Design Systems, Inc.) [WAIVER]
  - cdns_ddr_atb_h IPTAG MISMATCH: instance=cdns_ddr_atb_h but instance_tag=cdns_ddr_atb_h_debug | Product: DDR500_T5G Version: R100 (Vendor: Cadence Design Systems, Inc.) [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 16.0_IPTAG_CHECK --checkers IMP-16-0-0-05 --force

# Run individual tests
python IMP-16-0-0-05.py
```

---

## Notes

- **Prerequisite Dependency**: This check only executes if IMP-16-0-0-04 returns "yes". If IMP-16-0-0-04 is not "yes", this check returns NA (not applicable).
- **IPTAG Validation Logic**: Per user hint, the check validates "if phy iptag == block iptag then yes else Error". This translates to comparing the Instance column with the Instance_tag column in the CSV.
- **FIRM PHY Pattern Matching**: The checker identifies FIRM PHY slices using product name patterns: HPCFSC_, DDR\d+_, cdn_hs_phy_, cdns_ddr_. Only Cadence vendor instances matching these patterns are validated.
- **CSV Format**: The IP_checker CSV report contains metadata header lines before the actual CSV data. The checker must skip these lines and locate the header starting with "GDS".
- **Vendor Filtering**: Only "Cadence Design Systems, Inc." instances are checked for IPTAG removal. TSMC instances are counted for statistics but not validated.
- **Empty CSV Handling**: If the CSV contains only headers with no data rows, the checker reports INFO01 with zero instance counts and returns PASS (no violations found).
- **GDS Filename**: The GDS column typically shows filenames like "cdn_hs_phy_top.wIPTAG.gds" indicating IPTAG presence in the layout file.