# IMP-16-0-0-01: Confirm add TAG information to PHY.(TC/Controller don't need IPTAG)

## Overview

**Check ID:** IMP-16-0-0-01  
**Description:** Confirm add TAG information to PHY.(TC/Controller don't need IPTAG)  
**Category:** IP Tag Verification  
**Input Files:** 
- `${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/phy_iptag.prod` - Golden IPTAG definition file
- `${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/cdn_hs_phy_top.csv` - IP_checker verification report

This checker validates that PHY GDS files contain correct IP tag information by comparing the golden IPTAG from the product definition file against the actual IPTAG extracted from the GDS file. The check ensures proper IP tagging for PHY components (TC/Controller components do not require IPTAG and are excluded from this check).

---

## Check Logic

### Input Parsing

**File 1: phy_iptag.prod (Golden IPTAG Definition)**

Parse the product definition file to extract the golden IPTAG string:
1. Read lines sequentially, skipping comments (lines starting with `#`), `END` marker, and empty lines
2. Extract the first non-whitespace token from each valid line
3. Join all extracted tokens to form the complete golden IPTAG string

**Key Patterns:**
```python
# Pattern 1: Valid data line (extract first token)
pattern1 = r'^(\S+)\s*//.*$'
# Example: "H       // DDR PHY Architecture. Fixed width [1]"
# Extracts: "H"

# Pattern 2: Skip lines (comments, END marker, empty lines)
pattern2 = r'^\s*#|^\s*END\s*$|^\s*$|^"}}'
# Example: "# Comment line" or "END" or empty line
# Action: Skip these lines

# Pattern 3: Delimiter lines (underscore or dollar sign)
pattern3 = r'^([_$])\s*//.*$'
# Example: "_       // delimiter between phy type and protocol names"
# Extracts: "_"
```

**File 2: cdn_hs_phy_top.csv (IP_checker Report)**

Parse the CSV report to extract IPTAG information for PHY instances:
1. Skip the first line (IP_checker tool metadata)
2. Parse CSV header to validate structure
3. For each data row, search for lines containing `,"phy_name","phy_name"` pattern
4. Split the line by comma delimiter
5. Extract the 4th field (index 3) as the check IPTAG

**Key Patterns:**
```python
# Pattern 1: PHY instance line with phy_name pattern
pattern1 = r',"phy_name","phy_name"'
# Example: 'cdn_hs_phy_top.wIPTAG.gds,"Taiwan Semiconductor","phy_name","phy_name",0.096,INSTANCE,"HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R"'
# Action: Extract IPTAG from this line

# Pattern 2: CSV field extraction (4th field = IPTAG)
# Split by comma, get field at index 3
# Example fields: [gds_file, vendor, product, version, metric, instance, instance_tag]
# Field 3 (0-indexed) = version/IPTAG field
```

### Detection Logic

1. **Parse Golden IPTAG** from `phy_iptag.prod`:
   - Read file line by line
   - Skip comment lines (`#`), `END` marker, `"}}` lines, and empty lines
   - Extract first token from each valid line
   - Concatenate all tokens to form golden IPTAG string
   - Example: `HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R`

2. **Parse Check IPTAG** from `cdn_hs_phy_top.csv`:
   - Skip first line (tool metadata)
   - Search for lines containing `,"phy_name","phy_name"` pattern
   - Split line by comma delimiter
   - Extract 4th field (index 3) as check IPTAG
   - Remove surrounding quotes if present

3. **Compare IPTAGs**:
   - If golden IPTAG == check IPTAG → PASS
   - If golden IPTAG != check IPTAG → FAIL
   - If either IPTAG is missing or cannot be parsed → FAIL

4. **Output Results**:
   - PASS: Display matched IPTAG in INFO01
   - FAIL: Display mismatch details in ERROR01 (golden vs actual)

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

**Rationale:** This checker validates the status (correctness) of IPTAG information. It compares the golden IPTAG definition against the actual IPTAG found in the GDS file. The check focuses on whether the IPTAG matches the expected value (status correct) rather than whether certain items exist. Only the PHY IPTAG is checked (pattern matched), and the result depends on whether it matches the golden reference (status validation).

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
item_desc = "Confirm add TAG information to PHY.(TC/Controller don't need IPTAG)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "PHY IPTAG found and validated in GDS file"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "PHY IPTAG matched golden reference"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "PHY IPTAG found in GDS and matches golden definition"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "PHY IPTAG matched and validated against golden reference"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "PHY IPTAG not found or validation failed"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "PHY IPTAG mismatch or not satisfied"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "PHY IPTAG not found in GDS or does not match golden definition"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "PHY IPTAG not satisfied - mismatch between golden and actual IPTAG"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "PHY IPTAG mismatch waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "PHY IPTAG mismatch waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused IPTAG waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding IPTAG mismatch found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "PHY IPTAG: [iptag_string] (Golden: [golden_iptag], Actual: [check_iptag])"
  Example: "PHY IPTAG: HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R (Golden: HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R, Actual: HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R)"

ERROR01 (Violation/Fail items):
  Format: "IPTAG MISMATCH: Golden=[golden_iptag], Actual=[check_iptag]"
  Example: "IPTAG MISMATCH: Golden=HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R, Actual=HPCFSC_D5D4_T3G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-16-0-0-01:
  description: "Confirm add TAG information to PHY.(TC/Controller don't need IPTAG)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/phy_iptag.prod"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/cdn_hs_phy_top.csv"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs custom boolean validation of PHY IPTAG.
Parses golden IPTAG from .prod file and actual IPTAG from .csv file.
PASS if golden IPTAG matches actual IPTAG.
FAIL if IPTAGs mismatch or cannot be parsed.

**Sample Output (PASS):**
```
Status: PASS
Reason: PHY IPTAG found in GDS and matches golden definition
INFO01:
  - PHY IPTAG: HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R (Golden: HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R, Actual: HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: PHY IPTAG not found in GDS or does not match golden definition
ERROR01:
  - IPTAG MISMATCH: Golden=HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R, Actual=HPCFSC_D5D4_T3G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-16-0-0-01:
  description: "Confirm add TAG information to PHY.(TC/Controller don't need IPTAG)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/phy_iptag.prod"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/cdn_hs_phy_top.csv"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: IPTAG validation is informational only for this release"
      - "Note: IPTAG mismatches are expected during development phase and do not block tapeout"
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
  - "Explanation: IPTAG validation is informational only for this release"
  - "Note: IPTAG mismatches are expected during development phase and do not block tapeout"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - IPTAG MISMATCH: Golden=HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R, Actual=HPCFSC_D5D4_T3G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-16-0-0-01:
  description: "Confirm add TAG information to PHY.(TC/Controller don't need IPTAG)"
  requirements:
    value: 1
    pattern_items:
      - "HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/phy_iptag.prod"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/cdn_hs_phy_top.csv"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 searches for expected IPTAG pattern in input files.
Validates that the actual IPTAG from GDS matches the pattern_items (expected IPTAG).
PASS if actual IPTAG matches the expected pattern (missing_items empty).
FAIL if IPTAG mismatch detected (missing_items contains expected IPTAG).

**Sample Output (PASS):**
```
Status: PASS
Reason: PHY IPTAG matched and validated against golden reference
INFO01:
  - PHY IPTAG: HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R (Matched)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-16-0-0-01:
  description: "Confirm add TAG information to PHY.(TC/Controller don't need IPTAG)"
  requirements:
    value: 0
    pattern_items:
      - "HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/phy_iptag.prod"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/cdn_hs_phy_top.csv"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: IPTAG pattern check is informational only for this design"
      - "Note: Pattern mismatches are expected during IP integration and do not require immediate fixes"
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
  - "Explanation: IPTAG pattern check is informational only for this design"
  - "Note: Pattern mismatches are expected during IP integration and do not require immediate fixes"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - IPTAG MISMATCH: Expected=HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R, Actual=HPCFSC_D5D4_T3G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-16-0-0-01:
  description: "Confirm add TAG information to PHY.(TC/Controller don't need IPTAG)"
  requirements:
    value: 1
    pattern_items:
      - "HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/phy_iptag.prod"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/cdn_hs_phy_top.csv"
  waivers:
    value: 2
    waive_items:
      - name: "IPTAG MISMATCH: Golden=HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R, Actual=HPCFSC_D5D4_T3G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R"
        reason: "Waived - using T3G process node for this design variant per architecture team approval"
      - name: "IPTAG MISMATCH: Golden=HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R, Actual=HPCFSC_L4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R"
        reason: "Waived - LPDDR4 protocol variant approved for low-power configuration"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Match found IPTAG mismatches against waive_items
- Unwaived mismatches → ERROR (need fix)
- Waived mismatches → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all IPTAG mismatches are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - IPTAG MISMATCH: Golden=HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R, Actual=HPCFSC_D5D4_T3G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R [WAIVER]
WARN01 (Unused Waivers):
  - IPTAG MISMATCH: Golden=HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R, Actual=HPCFSC_L4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R: Waiver not matched - no corresponding IPTAG mismatch found
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-16-0-0-01:
  description: "Confirm add TAG information to PHY.(TC/Controller don't need IPTAG)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/phy_iptag.prod"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/16.0/cdn_hs_phy_top.csv"
  waivers:
    value: 2
    waive_items:
      - name: "IPTAG MISMATCH: Golden=HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R, Actual=HPCFSC_D5D4_T3G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R"
        reason: "Waived - using T3G process node for this design variant per architecture team approval"
      - name: "IPTAG MISMATCH: Golden=HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R, Actual=HPCFSC_L4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R"
        reason: "Waived - LPDDR4 protocol variant approved for low-power configuration"
```

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (no pattern_items), plus waiver classification:
- Match IPTAG mismatches against waive_items
- Unwaived mismatches → ERROR
- Waived mismatches → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS if all IPTAG mismatches are waived.

**Sample Output:**
```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - IPTAG MISMATCH: Golden=HPCFSC_D5D4_T5G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R, Actual=HPCFSC_D5D4_T3G$CTIME$17M1X1Xb1Xe1Ya1Yb5Y2Yy2Yx2R [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 16.0_IPTAG_CHECK --checkers IMP-16-0-0-01 --force

# Run individual tests
python IMP-16-0-0-01.py
```

---

## Notes

**File Format Requirements:**
- `phy_iptag.prod`: Must follow structured format with single-character codes, delimiters (_,$), protocol codes, process name, and configuration string
- `cdn_hs_phy_top.csv`: Must contain `,"phy_name","phy_name"` pattern for PHY instances with IPTAG in 4th field

**Limitations:**
- Only validates PHY components (TC/Controller excluded as per requirement)
- Assumes specific CSV format from IP_checker tool
- IPTAG comparison is case-sensitive and exact match required

**Known Issues:**
- If .prod file is malformed (missing delimiters, wrong field order), golden IPTAG parsing may fail
- CSV parsing assumes comma-separated format; quoted fields with embedded commas may cause issues
- Multiple PHY instances in CSV will only validate the first match found