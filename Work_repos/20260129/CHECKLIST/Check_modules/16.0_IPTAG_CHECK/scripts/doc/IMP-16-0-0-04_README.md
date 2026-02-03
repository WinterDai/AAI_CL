# IMP-16-0-0-04: Confirm update the IPTAG if FIRM PHY slices are reused as FIRM PHY delivery for another project.

## Overview

**Check ID:** IMP-16-0-0-04  
**Description:** Confirm update the IPTAG if FIRM PHY slices are reused as FIRM PHY delivery for another project.  
**Category:** IPTAG Verification  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/cdn_hs_phy_top.csv`

This checker verifies that when FIRM PHY slices are reused for another project, the IPTAG has been properly updated. It parses the IP_checker CSV report to identify both the block-level IPTAG (cdn_hs_phy_top instance) and the PHY-level IPTAG (Cadence FIRM PHY product). The check passes if both IPTAGs exist in the report, indicating proper IPTAG configuration for PHY reuse scenarios.

---

## Check Logic

### Input Parsing
The checker parses the IP_checker CSV report (`cdn_hs_phy_top.csv`) which contains GDS instance information with vendor, product, version, and IPTAG details.

**Key Patterns:**
```python
# Pattern 1: CSV header validation
pattern_header = r'^GDS\s*,Vendor\s*,Product\s*,Version\s*,Metric\s*,Instance\s*,Instance_tag\s*$'
# Example: "GDS                 ,Vendor    ,Product   ,Version   ,Metric    ,Instance  ,Instance_tag"

# Pattern 2: Block-level IPTAG (cdn_hs_phy_top instance)
pattern_block_iptag = r'^[^,]+,"Cadence Design Systems, Inc\.",[^,]+,"R\d+",[^,]+,cdn_hs_phy_top,"([^"]+)"'
# Example: 'cdn_hs_phy_top.wIPTAG.gds,"Cadence Design Systems, Inc.",HPCFSC_D5D4_T5G$C202209262108$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R,"R100",0.0,cdn_hs_phy_top,"cdn_hs_phy_top"'

# Pattern 3: PHY-level IPTAG (Cadence FIRM PHY product with configuration timestamp)
pattern_phy_iptag = r'^[^,]+,"Cadence Design Systems, Inc\.",(HPCFSC_[^,]+),"(R\d+)",[^,]+,cdn_hs_phy_top,"([^"]+)"'
# Example: Product name "HPCFSC_D5D4_T5G$C202209262108$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R" contains configuration and timestamp
```

### Detection Logic
1. **Parse CSV file** using csv.DictReader to extract instance records
2. **Identify block IPTAG**: Search for instance name "cdn_hs_phy_top" with Cadence vendor
3. **Identify PHY IPTAG**: Extract the Product field from the same record (contains FIRM PHY configuration)
4. **Validation**:
   - Block IPTAG exists: Instance_tag field is populated for cdn_hs_phy_top
   - PHY IPTAG exists: Product field contains HPCFSC configuration string
5. **Result determination**:
   - PASS: Both block IPTAG and PHY IPTAG are found
   - FAIL: Either IPTAG is missing

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

**Rationale:** This checker verifies the existence of both block-level and PHY-level IPTAGs in the IP_checker report. The pattern_items represent the two required IPTAG types that must be present when FIRM PHY slices are reused. The check passes when both IPTAGs are found, confirming proper IPTAG update for PHY reuse scenarios.

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
item_desc = "Confirm update the IPTAG if FIRM PHY slices are reused as FIRM PHY delivery for another project."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "Both block IPTAG and PHY IPTAG found in IP_checker report"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "Required IPTAGs matched (2/2): block IPTAG and PHY IPTAG validated"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Both block IPTAG (cdn_hs_phy_top) and PHY IPTAG (FIRM PHY product) found in IP_checker report"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Required IPTAG patterns matched and validated: block IPTAG and PHY IPTAG present"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Required IPTAG not found in IP_checker report"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Expected IPTAG pattern not satisfied (missing block or PHY IPTAG)"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Block IPTAG or PHY IPTAG not found - IPTAG update required for FIRM PHY reuse"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Expected IPTAG pattern not satisfied - block IPTAG or PHY IPTAG missing from report"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "IPTAG verification waived for FIRM PHY reuse"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "IPTAG check waived - PHY reuse approved without IPTAG update per design team"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused IPTAG waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding IPTAG violation found in IP_checker report"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "[IPTAG_TYPE]: [instance_name] | Product: [product_name] | Instance_tag: [tag_value]"
  Example: "Block IPTAG: cdn_hs_phy_top | Product: HPCFSC_D5D4_T5G$C202209262108$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R | Instance_tag: cdn_hs_phy_top"
  Example: "PHY IPTAG: cdn_hs_phy_top | Product: HPCFSC_D5D4_T5G$C202209262108$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R | Version: R100"

ERROR01 (Violation/Fail items):
  Format: "MISSING IPTAG: [iptag_type] not found in IP_checker report"
  Example: "MISSING IPTAG: Block IPTAG (cdn_hs_phy_top instance) not found in cdn_hs_phy_top.csv"
  Example: "MISSING IPTAG: PHY IPTAG (FIRM PHY product configuration) not found in cdn_hs_phy_top.csv"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-16-0-0-04:
  description: "Confirm update the IPTAG if FIRM PHY slices are reused as FIRM PHY delivery for another project."
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
Reason: Both block IPTAG (cdn_hs_phy_top) and PHY IPTAG (FIRM PHY product) found in IP_checker report
INFO01:
  - Block IPTAG: cdn_hs_phy_top | Product: HPCFSC_D5D4_T5G$C202209262108$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R | Instance_tag: cdn_hs_phy_top
  - PHY IPTAG: cdn_hs_phy_top | Product: HPCFSC_D5D4_T5G$C202209262108$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R | Version: R100
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Block IPTAG or PHY IPTAG not found - IPTAG update required for FIRM PHY reuse
ERROR01:
  - MISSING IPTAG: Block IPTAG (cdn_hs_phy_top instance) not found in cdn_hs_phy_top.csv
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-16-0-0-04:
  description: "Confirm update the IPTAG if FIRM PHY slices are reused as FIRM PHY delivery for another project."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/cdn_hs_phy_top.csv
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: IPTAG check is informational only for this project phase"
      - "Note: FIRM PHY reuse without IPTAG update is acceptable during development"
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
  - Explanation: IPTAG check is informational only for this project phase
  - Note: FIRM PHY reuse without IPTAG update is acceptable during development
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - MISSING IPTAG: Block IPTAG (cdn_hs_phy_top instance) not found in cdn_hs_phy_top.csv [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-16-0-0-04:
  description: "Confirm update the IPTAG if FIRM PHY slices are reused as FIRM PHY delivery for another project."
  requirements:
    value: 2
    pattern_items:
      - "Block IPTAG: cdn_hs_phy_top"
      - "PHY IPTAG: HPCFSC_D5D4_T5G"
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
Reason: Required IPTAG patterns matched and validated: block IPTAG and PHY IPTAG present
INFO01:
  - Block IPTAG: cdn_hs_phy_top | Product: HPCFSC_D5D4_T5G$C202209262108$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R | Instance_tag: cdn_hs_phy_top
  - PHY IPTAG: cdn_hs_phy_top | Product: HPCFSC_D5D4_T5G$C202209262108$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R | Version: R100
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-16-0-0-04:
  description: "Confirm update the IPTAG if FIRM PHY slices are reused as FIRM PHY delivery for another project."
  requirements:
    value: 2
    pattern_items:
      - "Block IPTAG: cdn_hs_phy_top"
      - "PHY IPTAG: HPCFSC_D5D4_T5G"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/cdn_hs_phy_top.csv
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: IPTAG pattern check is informational during early development"
      - "Note: Missing IPTAGs are expected when using preliminary PHY builds"
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
  - Explanation: IPTAG pattern check is informational during early development
  - Note: Missing IPTAGs are expected when using preliminary PHY builds
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - MISSING IPTAG: Block IPTAG (cdn_hs_phy_top instance) not found in cdn_hs_phy_top.csv [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-16-0-0-04:
  description: "Confirm update the IPTAG if FIRM PHY slices are reused as FIRM PHY delivery for another project."
  requirements:
    value: 2
    pattern_items:
      - "Block IPTAG: cdn_hs_phy_top"
      - "PHY IPTAG: HPCFSC_D5D4_T5G"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/cdn_hs_phy_top.csv
  waivers:
    value: 2
    waive_items:
      - name: "Block IPTAG: cdn_hs_phy_top | Product: HPCFSC_D5D4_T5G$C202209262108$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R | Instance_tag: cdn_hs_phy_top"
        reason: "Waived - legacy IPTAG approved for backward compatibility with existing PHY builds"
      - name: "PHY IPTAG: cdn_hs_phy_top | Product: HPCFSC_D5D4_T5G$C202209262108$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R | Version: R100"
        reason: "Waived - PHY configuration timestamp acceptable per design team review"
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
  - Block IPTAG: cdn_hs_phy_top | Product: HPCFSC_D5D4_T5G$C202209262108$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R | Instance_tag: cdn_hs_phy_top [WAIVER]
  - PHY IPTAG: cdn_hs_phy_top | Product: HPCFSC_D5D4_T5G$C202209262108$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R | Version: R100 [WAIVER]
WARN01 (Unused Waivers):
  - (none)
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-16-0-0-04:
  description: "Confirm update the IPTAG if FIRM PHY slices are reused as FIRM PHY delivery for another project."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/cdn_hs_phy_top.csv
  waivers:
    value: 2
    waive_items:
      - name: "Block IPTAG: cdn_hs_phy_top | Product: HPCFSC_D5D4_T5G$C202209262108$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R | Instance_tag: cdn_hs_phy_top"
        reason: "Waived - legacy IPTAG approved for backward compatibility with existing PHY builds"
      - name: "PHY IPTAG: cdn_hs_phy_top | Product: HPCFSC_D5D4_T5G$C202209262108$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R | Version: R100"
        reason: "Waived - PHY configuration timestamp acceptable per design team review"
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
  - Block IPTAG: cdn_hs_phy_top | Product: HPCFSC_D5D4_T5G$C202209262108$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R | Instance_tag: cdn_hs_phy_top [WAIVER]
  - PHY IPTAG: cdn_hs_phy_top | Product: HPCFSC_D5D4_T5G$C202209262108$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R | Version: R100 [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 16.0_IPTAG_CHECK --checkers IMP-16-0-0-04 --force

# Run individual tests
python IMP-16-0-0-04.py
```

---

## Notes

- **IPTAG Format**: The PHY IPTAG is embedded in the Product field with format `HPCFSC_<config>$C<timestamp>$<parameters>`
- **Reuse Detection**: When FIRM PHY slices are reused, both the block-level Instance_tag and the PHY-level Product configuration should be updated
- **CSV Parsing**: The checker uses csv.DictReader to handle quoted fields containing commas (e.g., vendor names)
- **Vendor Identification**: Cadence instances are identified by exact match: `"Cadence Design Systems, Inc."`
- **Version Format**: PHY versions follow the pattern `R<number>` (e.g., R100)
- **Known Limitations**: 
  - Checker assumes single cdn_hs_phy_top instance per CSV file
  - Does not validate IPTAG format correctness, only existence
  - Does not cross-check IPTAG consistency across multiple project deliveries