# IMP-8-0-0-12: Confirm no inputs are tied directly to the power rails (VDD/VSS) by using Tiehigh/Tielow cells(check the Note)

## Overview

**Check ID:** IMP-8-0-0-12  
**Description:** Confirm no inputs are tied directly to the power rails (VDD/VSS) by using Tiehigh/Tielow cells(check the Note)  
**Category:** Physical Implementation - Tie Cell Verification  
**Input Files:** 
- Cadence Innovus verifyTieCell report (`.rpt`)

This checker validates that all inputs requiring tie-high or tie-low connections use proper Tiehigh/Tielow buffer cells instead of being directly connected to power rails (VDD/VSS). Direct connections to power rails can cause reliability issues, increased power consumption, and potential design rule violations. The checker parses Innovus verifyTieCell reports to identify violations where pins are tied directly to power rails without proper tie cells.

---

## Check Logic

### Input Parsing

The checker parses Cadence Innovus verifyTieCell reports to extract tie cell violations. Each violation indicates an input pin that is directly connected to a power rail without using a proper Tiehigh/Tielow cell.

**Key Patterns:**

```python
# Pattern 1: Individual tie cell violation with coordinates and instance/pin information
pattern1 = r'Tie cell violation at \(([\d.]+),\s*([\d.]+)\)\s*\(([\d.]+),\s*([\d.]+)\)\s*for pin (\S+) of instance (.+)\.'
# Example: "Tie cell violation at (158.688, 29.867) (158.689, 29.869) for pin PAD1_HV_IN_XTC of instance inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_7."
# Extracts: x1=158.688, y1=29.867, x2=158.689, y2=29.869, pin=PAD1_HV_IN_XTC, instance=inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_7

# Pattern 2: Violation type count in summary section
pattern2 = r'Number of (\w+)\s+viol\(s\):\s*(\d+)'
# Example: "Number of connection  viol(s): 20"
# Extracts: violation_type=connection, count=20

# Pattern 3: Total violations count
pattern3 = r'(\d+)\s+total\s+(?:info|viol)\(s\)\s+created\.'
# Example: "20 total info(s) created."
# Extracts: total_count=20

# Pattern 4: Design name from header
pattern4 = r'#\s*Design:\s+(\S+)'
# Example: "#  Design:            CDN_104H_cdn_hs_phy_data_slice_EW"
# Extracts: design_name=CDN_104H_cdn_hs_phy_data_slice_EW
```

### Detection Logic

1. **Parse Report Header**: Extract design name and metadata from report header
2. **Identify Violation Sections**: Detect violation category sections (e.g., "Connection Viol:")
3. **Extract Individual Violations**: For each violation line:
   - Parse coordinates (x1, y1, x2, y2)
   - Extract pin name (e.g., PAD1_HV_IN_XTC)
   - Extract instance path (e.g., inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_7)
   - Construct full instance pin name: `{instance_path}/{pin_name}`
4. **Parse Summary Statistics**: Extract total violation count and validate against parsed violations
5. **Match Against Requirements**: Compare violations against `pattern_items` (if Type 2/3)
6. **Apply Waivers**: Match violations against `waive_items` to classify as waived/unwaived (if Type 3/4)
7. **Determine PASS/FAIL**:
   - **PASS**: No tie cell violations found (or all violations waived in Type 3/4)
   - **FAIL**: Tie cell violations exist (unwaived violations in Type 3/4)

**Edge Cases:**
- Empty report (0 violations): Return PASS with INFO01 showing clean design
- Missing summary section: Use count of parsed violations as fallback
- Multiple violation types: Track each type separately (connection, setup, etc.)
- Malformed coordinates: Skip line and log parsing error
- Very long instance paths: Preserve full hierarchy without truncation
- Instance pin name format: Combine instance path and pin name as `{instance}/{pin}` (e.g., `inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_7/PAD1_HV_IN_XTC`)

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

**Rationale:** This checker validates tie cell violations (status check). The `pattern_items` represent specific instance pins that are expected to have violations or are being monitored. The checker reports violations found in the input file, and only outputs items that match the pattern_items (if specified). This is a status check because we're verifying whether specific pins have tie cell violations, not checking for the existence of configuration items.

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
item_desc = "Confirm no inputs are tied directly to the power rails (VDD/VSS) by using Tiehigh/Tielow cells(check the Note)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "No tie cell violations found in design"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All monitored instance pins have no tie cell violations"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "No tie cell violations found - all inputs use proper Tiehigh/Tielow cells"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All monitored instance pins validated - no tie cell violations matched"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Tie cell violations detected in design"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Tie cell violations found for monitored instance pins"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Tie cell violations detected - inputs tied directly to power rails without proper Tiehigh/Tielow cells"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Monitored instance pins have tie cell violations - inputs tied directly to power rails"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Tie cell violations waived per design approval"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Tie cell violation waived - approved exception for specific design requirements"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries - no matching violations found"
unused_waiver_reason = "Waiver entry not matched - corresponding tie cell violation not found in report"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "Design: {design_name} - No tie cell violations"
  Example: "Design: CDN_104H_cdn_hs_phy_data_slice_EW - No tie cell violations"

ERROR01 (Violation/Fail items):
  Format: "{instance_path}/{pin_name} | Location: ({x1}, {y1})"
  Example: "inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_7/PAD1_HV_IN_XTC | Location: (158.688, 29.867)"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-12:
  description: "Confirm no inputs are tied directly to the power rails (VDD/VSS) by using Tiehigh/Tielow cells(check the Note)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "reports/8.0/IMP-8-0-0-12/IMP-8-0-0-12_case0.rpt"
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
Reason: No tie cell violations found - all inputs use proper Tiehigh/Tielow cells
INFO01:
  - Design: CDN_104H_cdn_hs_phy_data_slice_EW - No tie cell violations
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Tie cell violations detected - inputs tied directly to power rails without proper Tiehigh/Tielow cells
ERROR01:
  - inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_7/PAD1_HV_IN_XTC | Location: (158.688, 29.867)
  - inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_6/PAD1_HV_IN_XTC | Location: (158.688, 30.123)
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-12:
  description: "Confirm no inputs are tied directly to the power rails (VDD/VSS) by using Tiehigh/Tielow cells(check the Note)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "reports/8.0/IMP-8-0-0-12/IMP-8-0-0-12_case0.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Tie cell violations are informational only for this design phase"
      - "Note: Direct power rail connections are acceptable for PAD cells in this technology"
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
  - "Explanation: Tie cell violations are informational only for this design phase"
  - "Note: Direct power rail connections are acceptable for PAD cells in this technology"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_7/PAD1_HV_IN_XTC | Location: (158.688, 29.867) [WAIVED_AS_INFO]
  - inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_6/PAD1_HV_IN_XTC | Location: (158.688, 30.123) [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-12:
  description: "Confirm no inputs are tied directly to the power rails (VDD/VSS) by using Tiehigh/Tielow cells(check the Note)"
  requirements:
    value: 2
    pattern_items:
      - "inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_7/PAD1_HV_IN_XTC"
      - "inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_6/PAD1_HV_IN_XTC"
  input_files:
    - "reports/8.0/IMP-8-0-0-12/IMP-8-0-0-12_case0.rpt"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- pattern_items represent specific instance pins to monitor for tie cell violations
- Use complete instance pin names: `{instance_path}/{pin_name}`
- Example: `inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_7/PAD1_HV_IN_XTC`
- These are the exact identifiers extracted from the report violation lines

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS/FAIL depends on check purpose:
- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)

**Sample Output (PASS):**
```
Status: PASS
Reason: All monitored instance pins validated - no tie cell violations matched
INFO01:
  - Design: CDN_104H_cdn_hs_phy_data_slice_EW - Monitored pins clean (0/2 violations)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-12:
  description: "Confirm no inputs are tied directly to the power rails (VDD/VSS) by using Tiehigh/Tielow cells(check the Note)"
  requirements:
    value: 2
    pattern_items:
      - "inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_7/PAD1_HV_IN_XTC"
      - "inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_6/PAD1_HV_IN_XTC"
  input_files:
    - "reports/8.0/IMP-8-0-0-12/IMP-8-0-0-12_case0.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Monitored pins are informational only - violations expected for PAD cells"
      - "Note: Direct power rail connections are acceptable for these specific instances"
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
  - "Explanation: Monitored pins are informational only - violations expected for PAD cells"
  - "Note: Direct power rail connections are acceptable for these specific instances"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_7/PAD1_HV_IN_XTC | Location: (158.688, 29.867) [WAIVED_AS_INFO]
  - inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_6/PAD1_HV_IN_XTC | Location: (158.688, 30.123) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-12:
  description: "Confirm no inputs are tied directly to the power rails (VDD/VSS) by using Tiehigh/Tielow cells(check the Note)"
  requirements:
    value: 2
    pattern_items:
      - "inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_7/PAD1_HV_IN_XTC"
      - "inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_6/PAD1_HV_IN_XTC"
  input_files:
    - "reports/8.0/IMP-8-0-0-12/IMP-8-0-0-12_case0.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_7/PAD1_HV_IN_XTC"
        reason: "Waived - PAD cell design allows direct power rail connection per technology spec"
      - name: "inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_6/PAD1_HV_IN_XTC"
        reason: "Waived - Approved exception for HV input pad in this design"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:
- BOTH must be at SAME semantic level as description!
- pattern_items: Complete instance pin names (e.g., `inst_path/pin_name`)
- waive_items.name: SAME format as pattern_items (complete instance pin names)
- Example: If pattern_items = ["inst_data_path_top/.../data_pad_7/PAD1_HV_IN_XTC"], then waive_items.name = "inst_data_path_top/.../data_pad_7/PAD1_HV_IN_XTC"

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
  - inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_7/PAD1_HV_IN_XTC | Location: (158.688, 29.867) [WAIVER]
  - inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_6/PAD1_HV_IN_XTC | Location: (158.688, 30.123) [WAIVER]
WARN01 (Unused Waivers):
  (none - all waivers matched)
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-12:
  description: "Confirm no inputs are tied directly to the power rails (VDD/VSS) by using Tiehigh/Tielow cells(check the Note)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "reports/8.0/IMP-8-0-0-12/IMP-8-0-0-12_case0.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_7/PAD1_HV_IN_XTC"
        reason: "Waived - PAD cell design allows direct power rail connection per technology spec"
      - name: "inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_6/PAD1_HV_IN_XTC"
        reason: "Waived - Approved exception for HV input pad in this design"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3
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
INFO01 (Waived):
  - inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_7/PAD1_HV_IN_XTC | Location: (158.688, 29.867) [WAIVER]
  - inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_6/PAD1_HV_IN_XTC | Location: (158.688, 30.123) [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 8.0_PHYSICAL_IMPLEMENTATION_CHECK --checkers IMP-8-0-0-12 --force

# Run individual tests
python IMP-8-0-0-12.py
```

---

## Notes

**Important Considerations:**

1. **Instance Pin Name Format**: The checker constructs full instance pin names by combining the instance path and pin name from the report (e.g., `inst_data_path_top/inst_data_byte_macro/cdn_hs_phy_data_asic_pads/data_pad_7/PAD1_HV_IN_XTC`). This format is used for both pattern matching and waiver matching.

2. **Violation Types**: The report may contain different violation types (connection, setup, etc.). The checker aggregates all types and reports them uniformly.

3. **Coordinate Information**: Physical coordinates (x1, y1, x2, y2) are extracted for each violation and displayed in the output for debugging purposes.

4. **Design Name**: The design name is extracted from the report header and included in summary messages.

5. **PAD Cell Exceptions**: In some technologies, PAD cells may legitimately require direct power rail connections. Use Type 3/4 waivers to document approved exceptions.

6. **Empty Reports**: If the report contains 0 violations, the checker returns PASS with an informational message indicating a clean design.

7. **Validation**: The checker validates that the number of parsed violations matches the summary count in the report to ensure complete parsing.

**Known Limitations:**

- The checker assumes the Innovus verifyTieCell report format remains consistent across tool versions
- Very long instance paths are preserved without truncation, which may affect display formatting
- Malformed violation lines (e.g., missing coordinates) are skipped with a warning