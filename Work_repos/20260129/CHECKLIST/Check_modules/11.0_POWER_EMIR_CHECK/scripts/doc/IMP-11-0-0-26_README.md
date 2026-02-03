# IMP-11-0-0-26: List the VT ratio (without physical cells): EG: TSMCN7/N6:SVT(50%)/LVT(40%)/ULVT(10%) TSMCN5/N4/N3/N2:SVT(50%)/LVTLL(20%)/LVT(20%)/ULVTLL(5%)/ULVT(5%)/ELVT(0%) SEC:RVT(50%)/LVT(40%)/SLVT(10%) INTl_I3/18A:ad(HVT 30%)/ac(SVT 20%)/ab(LVT 30%)/aa(ULVT 20%)

## Overview

**Check ID:** IMP-11-0-0-26  
**Description:** List the VT ratio (without physical cells): EG: TSMCN7/N6:SVT(50%)/LVT(40%)/ULVT(10%) TSMCN5/N4/N3/N2:SVT(50%)/LVTLL(20%)/LVT(20%)/ULVTLL(5%)/ULVT(5%)/ELVT(0%) SEC:RVT(50%)/LVT(40%)/SLVT(10%) INTl_I3/18A:ad(HVT 30%)/ac(SVT 20%)/ab(LVT 30%)/aa(ULVT 20%)  
**Category:** Power/EMIR Analysis  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/vtratio.sum`

This checker extracts VT (Voltage Threshold) ratio distribution from the vtratio.sum report file and formats the output according to process node naming conventions. The checker parses each VT type's percentage and total cell count, then aggregates them into a summary string with percentages rounded to 2 decimal places. The output format varies by process node: TSMC N7/N6 uses SVT/LVT/ULVT, TSMC N5/N4/N3/N2 uses SVT/LVTLL/LVT/ULVTLL/ULVT/ELVT, SEC uses RVT/LVT/SLVT, and Intel I3/18A uses ad(HVT)/ac(SVT)/ab(LVT)/aa(ULVT) naming.

---

## Check Logic

### Input Parsing
The checker parses the vtratio.sum file line-by-line to extract VT type distribution data. Each line contains a VT type identifier, its percentage ratio, and total cell count.

**Key Patterns:**
```python
# Pattern 1: Extract VT type, percentage, and cell count
pattern1 = r'core logic (\w+) ratio is : ([\d.]+)%\s+total number is: (\d+)'
# Example: "core logic CNODSVT ratio is : 46.0147161781%  total number is: 99245"
# Captures: group(1)=CNODSVT, group(2)=46.0147161781, group(3)=99245

# Pattern 2: Detect zero percentage VT types (for validation)
pattern2 = r'core logic (\w+) ratio is : 0\.0%'
# Example: "core logic CNODELVT ratio is : 0.0%  total number is: 0"
# Captures: group(1)=CNODELVT (indicates unused VT type)
```

### Detection Logic
1. **Parse VT Data**: Iterate through each line in vtratio.sum file
   - Use pattern1 to extract VT type name, percentage value, and cell count
   - Store each VT type with its percentage rounded to 2 decimal places
   - Example: "CNODSVT" → 46.01%, "CNODLVTLL" → 25.04%

2. **Process Node Identification**: Infer process node from VT naming convention
   - CNOD* prefix → TSMC N5/N4/N3/N2 (uses LVTLL, ULVTLL, ELVT variants)
   - RVT/LVT/SLVT → SEC process
   - ad/ac/ab/aa → Intel I3/18A process
   - Other SVT/LVT/ULVT → TSMC N7/N6

3. **VT Type Mapping**: Map raw VT names to standard abbreviations
   - CNODSVT → SVT
   - CNODLVTLL → LVTLL
   - CNODLVT → LVT
   - CNODULVTLL → ULVTLL
   - CNODULVT → ULVT
   - CNODELVT → ELVT

4. **Format Output**: Construct summary string in required format
   - Format: `VT_TYPE(percentage%)/VT_TYPE(percentage%)/...`
   - Example: `SVT(46.01%)/LVTLL(25.04%)/LVT(7.35%)/ULVTLL(4.12%)/ULVT(17.48%)/ELVT(0.0%)`
   - Percentages rounded to 2 decimal places with % symbol

5. **Pattern Comparison Logic** (for Type 2/3 with pattern_items):
   - Supports comparison operators in pattern_items:
     * `SVT(50%)` or `SVT(==50%)` - Exact match (SVT must equal 50%)
     * `SVT(>50%)` - Greater than (SVT must be > 50%)
     * `SVT(<50%)` - Less than (SVT must be < 50%)
     * `SVT(>=50%)` - Greater or equal (SVT must be >= 50%)
     * `SVT(<=50%)` - Less or equal (SVT must be <= 50%)
   - Pattern parsing:
     * Extract VT type name: `SVT`, `LVTLL`, etc.
     * Extract operator: `>`, `<`, `>=`, `<=`, `==` (default if omitted)
     * Extract threshold value: `50`, `20`, etc.
   - Comparison tolerance: ±0.01% for equality checks (e.g., 50.00% matches 50.01%)
   - Example patterns:
     * `SVT(>45%)` - PASS if actual SVT is 46.01%, FAIL if 44.99%
     * `LVTLL(<=25%)` - PASS if actual LVTLL is 25.04%, FAIL if 25.50%

6. **Validation Checks**:
   - Verify all expected VT types are present for the detected process node
   - Check that percentage sum is approximately 100% (±0.1% tolerance)
   - Flag zero-percentage VT types as informational (may be valid if unused)

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

**Rationale:** This checker validates VT ratio distribution against expected patterns. The pattern_items represent expected VT type percentages (golden values) that should be matched in the parsed data. The checker only reports on VT types specified in pattern_items, comparing their actual percentages against expected values. VT types not in pattern_items are ignored. This is a status check because we're validating that specific VT types have correct percentage distributions, not just checking if they exist.

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
item_desc = "List the VT ratio (without physical cells): EG: TSMCN7/N6:SVT(50%)/LVT(40%)/ULVT(10%) TSMCN5/N4/N3/N2:SVT(50%)/LVTLL(20%)/LVT(20%)/ULVTLL(5%)/ULVT(5%)/ELVT(0%) SEC:RVT(50%)/LVT(40%)/SLVT(10%) INTl_I3/18A:ad(HVT 30%)/ac(SVT 20%)/ab(LVT 30%)/aa(ULVT 20%)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "VT ratio distribution found in vtratio.sum report"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "VT ratio distribution matched expected pattern"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "VT ratio data successfully extracted from vtratio.sum report"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "VT type percentage matched expected ratio pattern"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "VT ratio data not found in vtratio.sum report"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "VT ratio distribution does not match expected pattern"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "VT ratio data missing or vtratio.sum file not found"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "VT type percentage does not satisfy expected ratio requirement"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "VT ratio deviation waived per design team approval"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "VT ratio mismatch waived - acceptable deviation for this design configuration"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused VT ratio waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding VT ratio deviation found"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [VT_type]: [percentage_ratio]"
  Example: "- SVT(46.01%)/LVTLL(25.04%)/LVT(7.35%)/ULVTLL(4.12%)/ULVT(17.48%)/ELVT(0.0%)"

ERROR01 (Violation/Fail items):
  Format: "- [VT_type]: [actual_percentage] (expected: [expected_percentage])"
  Example: "- SVT: 46.01% (expected: 50.00%) - VT type percentage does not satisfy expected ratio requirement"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-26:
  description: "List the VT ratio (without physical cells): EG: TSMCN7/N6:SVT(50%)/LVT(40%)/ULVT(10%) TSMCN5/N4/N3/N2:SVT(50%)/LVTLL(20%)/LVT(20%)/ULVTLL(5%)/ULVT(5%)/ELVT(0%) SEC:RVT(50%)/LVT(40%)/SLVT(10%) INTl_I3/18A:ad(HVT 30%)/ac(SVT 20%)/ab(LVT 30%)/aa(ULVT 20%)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/vtratio.sum"
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
Reason: VT ratio data successfully extracted from vtratio.sum report
INFO01:
  - VT_Ratio_Summary: SVT(46.01%)/LVTLL(25.04%)/LVT(7.35%)/ULVTLL(4.12%)/ULVT(17.48%)/ELVT(0.0%)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: VT ratio data missing or vtratio.sum file not found
ERROR01:
  - vtratio.sum: VT ratio data missing or vtratio.sum file not found
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-26:
  description: "List the VT ratio (without physical cells): EG: TSMCN7/N6:SVT(50%)/LVT(40%)/ULVT(10%) TSMCN5/N4/N3/N2:SVT(50%)/LVTLL(20%)/LVT(20%)/ULVTLL(5%)/ULVT(5%)/ELVT(0%) SEC:RVT(50%)/LVT(40%)/SLVT(10%) INTl_I3/18A:ad(HVT 30%)/ac(SVT 20%)/ab(LVT 30%)/aa(ULVT 20%)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/vtratio.sum"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: VT ratio check is informational only - reports actual distribution without enforcing specific targets"
      - "Note: VT ratio variations are expected across different design configurations and process corners"
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
  - "Explanation: VT ratio check is informational only - reports actual distribution without enforcing specific targets"
  - "Note: VT ratio variations are expected across different design configurations and process corners"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - VT_Ratio_Summary: SVT(46.01%)/LVTLL(25.04%)/LVT(7.35%)/ULVTLL(4.12%)/ULVT(17.48%)/ELVT(0.0%) [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-26:
  description: "List the VT ratio (without physical cells): EG: TSMCN7/N6:SVT(50%)/LVT(40%)/ULVT(10%) TSMCN5/N4/N3/N2:SVT(50%)/LVTLL(20%)/LVT(20%)/ULVTLL(5%)/ULVT(5%)/ELVT(0%) SEC:RVT(50%)/LVT(40%)/SLVT(10%) INTl_I3/18A:ad(HVT 30%)/ac(SVT 20%)/ab(LVT 30%)/aa(ULVT 20%)"
  requirements:
    value: 6
    pattern_items:
      # COMPARISON OPERATORS SUPPORTED: ==, >, <, >=, <=
      # Format: "VT_TYPE(OPERATOR THRESHOLD%)"
      # If no operator specified, defaults to == (exact match with ±0.01% tolerance)
      - "SVT(>=45%)"     # SVT ratio must be >= 45% (flexible lower bound)
      - "LVTLL(<30%)"    # LVTLL ratio must be < 30% (upper bound constraint)
      - "LVT(20%)"       # LVT ratio must equal 20% (±0.01% tolerance, equivalent to ==20%)
      - "ULVTLL(<=10%)"  # ULVTLL ratio must be <= 10% (upper bound)
      - "ULVT(>3%)"      # ULVT ratio must be > 3% (lower bound)
      - "ELVT(0%)"       # ELVT ratio must equal 0% (exact match)
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/vtratio.sum"
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
- **For VT ratio checks**: Use COMPARISON PATTERN format:
  * Format: `"VT_TYPE(OPERATOR THRESHOLD%)"`
  * Supported operators: `==` (equal), `>` (greater), `<` (less), `>=` (greater/equal), `<=` (less/equal)
  * Default operator: `==` if omitted (e.g., `"SVT(50%)"` = `"SVT(==50%)"`)
  * Examples: `"SVT(>45%)"`, `"LVTLL(<=30%)"`, `"LVT(20%)"`

**Check Behavior:**
Type 2 searches pattern_items in input files and applies comparison logic.
For VT ratio checks:
- Parse each pattern to extract: VT_type, operator, threshold_value
- Compare actual percentage against threshold using specified operator
- found_items: VT types that SATISFY the comparison (e.g., actual SVT 46.01% >= threshold 45%)
- missing_items: VT types that FAIL the comparison (e.g., actual LVTLL 35% NOT < threshold 30%)
PASS/FAIL depends on check purpose:
- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)

**Sample Output (PASS):**
```
Status: PASS
Reason: VT type percentage matched expected ratio pattern
INFO01:
  - VT_Ratio_Summary: ELVT(0.00%)/LVT(7.35%)/LVTLL(25.04%)/SVT(46.01%)/ULVT(17.48%)/ULVTLL(4.12%). In line 1, C:\...\vtratio.sum: VT ratio data successfully extracted from vtratio.sum report
  - SVT: 46.01% satisfies requirement >=45% - VT type percentage matched expected ratio pattern
  - LVTLL: 25.04% satisfies requirement <30% - VT type percentage matched expected ratio pattern
  - LVT: 20.00% satisfies requirement ==20% - VT type percentage matched expected ratio pattern
  - ULVTLL: 4.12% satisfies requirement <=10% - VT type percentage matched expected ratio pattern
  - ULVT: 17.48% satisfies requirement >3% - VT type percentage matched expected ratio pattern
  - ELVT: 0.00% satisfies requirement ==0% - VT type percentage matched expected ratio pattern
```

**Sample Output (FAIL - comparison not satisfied):**
```
Status: FAIL
Reason: VT type percentage does not satisfy expected ratio requirement
INFO01:
  - VT_Ratio_Summary: ELVT(0.00%)/LVT(7.35%)/LVTLL(35.00%)/SVT(46.01%)/ULVT(2.50%)/ULVTLL(4.12%). In line 1, C:\...\vtratio.sum: VT ratio data successfully extracted from vtratio.sum report
ERROR01:
  - LVTLL: 35.00% does NOT satisfy requirement <30% - VT type percentage does not satisfy expected ratio requirement
  - ULVT: 2.50% does NOT satisfy requirement >3% - VT type percentage does not satisfy expected ratio requirement
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-26:
  description: "List the VT ratio (without physical cells): EG: TSMCN7/N6:SVT(50%)/LVT(40%)/ULVT(10%) TSMCN5/N4/N3/N2:SVT(50%)/LVTLL(20%)/LVT(20%)/ULVTLL(5%)/ULVT(5%)/ELVT(0%) SEC:RVT(50%)/LVT(40%)/SLVT(10%) INTl_I3/18A:ad(HVT 30%)/ac(SVT 20%)/ab(LVT 30%)/aa(ULVT 20%)"
  requirements:
    value: 6
    pattern_items:
      - "SVT(50%)"
      - "LVTLL(20%)"
      - "LVT(20%)"
      - "ULVTLL(5%)"
      - "ULVT(5%)"
      - "ELVT(0%)"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/vtratio.sum"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: VT ratio targets are guidelines only - actual ratios depend on design optimization results"
      - "Note: Pattern mismatches are expected when design prioritizes performance over power or vice versa"
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
INFO01:
  - VT_Ratio_Summary: ELVT(0.00%)/LVT(7.35%)/LVTLL(25.04%)/SVT(46.01%)/ULVT(17.48%)/ULVTLL(4.12%). In line 1, C:\...\vtratio.sum: VT ratio data successfully extracted from vtratio.sum report
INFO02 ([WAIVED_INFO] - waive_items as comment):
  - "Explanation: VT ratio targets are guidelines only - actual ratios depend on design optimization results"
  - "Note: Pattern mismatches are expected when design prioritizes performance over power or vice versa"
INFO03 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - SVT: 46.01% (expected: 50%) [WAIVED_AS_INFO]
  - LVTLL: 25.04% (expected: 20%) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-26:
  description: "List the VT ratio (without physical cells): EG: TSMCN7/N6:SVT(50%)/LVT(40%)/ULVT(10%) TSMCN5/N4/N3/N2:SVT(50%)/LVTLL(20%)/LVT(20%)/ULVTLL(5%)/ULVT(5%)/ELVT(0%) SEC:RVT(50%)/LVT(40%)/SLVT(10%) INTl_I3/18A:ad(HVT 30%)/ac(SVT 20%)/ab(LVT 30%)/aa(ULVT 20%)"
  requirements:
    value: 6
    pattern_items:
      # COMPARISON OPERATORS SUPPORTED: ==, >, <, >=, <=
      # Format: "VT_TYPE(OPERATOR THRESHOLD%)"
      - "SVT(>=45%)"     # GOLDEN RULE: SVT ratio must be >= 45%
      - "LVTLL(>30%)"    # GOLDEN RULE: LVTLL ratio must be < 30%
      - "LVT(20%)"       # GOLDEN RULE: LVT ratio must equal 20% (±0.01% tolerance)
      - "ULVTLL(<=10%)"  # GOLDEN RULE: ULVTLL ratio must be <= 10%
      - "ULVT(>3%)"      # GOLDEN RULE: ULVT ratio must be > 3%
      - "ELVT(0%)"       # GOLDEN RULE: ELVT ratio must equal 0%
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/vtratio.sum"
  waivers:
    value: 2
    waive_items:
      - name: "LVTLL"   # EXEMPTION: Waive LVTLL comparison failure (e.g., actual 25% fails >30% requirement)
        reason: "Waived - LVTLL ratio increased to meet timing requirements per design review"
      - name: "ULVT"    # EXEMPTION: Waive ULVT comparison failure (e.g., actual 2.5% fails >3% requirement)
        reason: "Waived - ULVT ratio reduced due to power optimization priorities"
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
INFO01:
  - VT_Ratio_Summary: ELVT(0.00%)/LVT(7.35%)/LVTLL(25.04%)/SVT(46.01%)/ULVT(17.48%)/ULVTLL(4.12%). In line 1, C:\...\vtratio.sum: VT ratio data successfully extracted from vtratio.sum report
INFO02 (Waived):
  - SVT: VT ratio mismatch waived - acceptable deviation for this design configuration: Waived - SVT ratio deviation acceptable for performance-optimized design [WAIVER]
  - LVTLL: VT ratio mismatch waived - acceptable deviation for this design configuration: Waived - LVTLL ratio increased to meet timing requirements per design review [WAIVER]
WARN01 (Unused Waivers):
  - (none - all waivers matched)
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-26:
  description: "List the VT ratio (without physical cells): EG: TSMCN7/N6:SVT(50%)/LVT(40%)/ULVT(10%) TSMCN5/N4/N3/N2:SVT(50%)/LVTLL(20%)/LVT(20%)/ULVTLL(5%)/ULVT(5%)/ELVT(0%) SEC:RVT(50%)/LVT(40%)/SLVT(10%) INTl_I3/18A:ad(HVT 30%)/ac(SVT 20%)/ab(LVT 30%)/aa(ULVT 20%)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/11.0/vtratio.sum"
  waivers:
    value: 2
    waive_items:
      - name: "SVT"     # ✅ SAME object name as Type 3
        reason: "Waived - SVT ratio deviation acceptable for performance-optimized design"
      - name: "LVTLL"   # ✅ SAME object name as Type 3
        reason: "Waived - LVTLL ratio increased to meet timing requirements per design review"
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
INFO01:
  - VT_Ratio_Summary: ELVT(0.00%)/LVT(7.35%)/LVTLL(25.04%)/SVT(46.01%)/ULVT(17.48%)/ULVTLL(4.12%). In line 1, C:\...\vtratio.sum: VT ratio data successfully extracted from vtratio.sum report
INFO02 (Waived):
  - SVT: VT ratio mismatch waived - acceptable deviation for this design configuration: Waived - SVT ratio deviation acceptable for performance-optimized design [WAIVER]
  - LVTLL: VT ratio mismatch waived - acceptable deviation for this design configuration: Waived - LVTLL ratio increased to meet timing requirements per design review [WAIVER]
WARN01 (Unused Waivers):
  - (none - all waivers matched)
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 11.0_POWER_EMIR_CHECK --checkers IMP-11-0-0-26 --force

# Run individual tests
python IMP-11-0-0-26.py
```

---

## Notes

**VT Type Naming Conventions:**
- TSMC N7/N6: SVT (Standard VT), LVT (Low VT), ULVT (Ultra-Low VT)
- TSMC N5/N4/N3/N2: SVT, LVTLL (Low VT Low Leakage), LVT, ULVTLL (Ultra-Low VT Low Leakage), ULVT, ELVT (Extremely Low VT)
- SEC: RVT (Regular VT), LVT, SLVT (Super Low VT)
- Intel I3/18A: ad (HVT - High VT), ac (SVT), ab (LVT), aa (ULVT)

**Percentage Rounding:**
- All percentages are rounded to 2 decimal places
- Example: 46.0147161781% → 46.01%
- Percentage sum should be approximately 100% (±0.1% tolerance acceptable due to rounding)

**Physical Cell Exclusion:**
- The checker excludes physical-only cells (filler, decap, tie cells) from VT ratio calculation
- Only core logic cells are counted in the ratio
- This provides accurate representation of functional cell VT distribution

**Zero Percentage VT Types:**
- VT types with 0.0% ratio are valid if that VT variant is not used in the design
- Example: ELVT often shows 0% as it's rarely used in most designs
- Zero percentages are reported but do not trigger failures

**Validation Checks:**
- File existence: vtratio.sum must exist and be readable
- Data completeness: All expected VT types for the process node should be present
- Percentage sum: Total should be ~100% (allows small rounding errors)
- Cell count validation: Total cell count should match sum of individual VT type counts