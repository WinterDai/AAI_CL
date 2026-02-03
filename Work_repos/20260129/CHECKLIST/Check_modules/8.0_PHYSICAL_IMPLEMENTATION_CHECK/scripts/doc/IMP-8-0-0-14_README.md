# IMP-8-0-0-14: Confirm no VT mixing on clock tree for all modes. For some instances has clock attribute but used as data, please list that into Waiver list.

## Overview

**Check ID:** IMP-8-0-0-14  
**Description:** Confirm no VT mixing on clock tree for all modes. For some instances has clock attribute but used as data, please list that into Waiver list.  
**Category:** Physical Implementation - Clock Tree Quality  
**Input Files:** 
- `${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/clock_cells_with_cell_type.txt`
- `${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-14.rpt`

This checker validates that all clock trees use a consistent threshold voltage (VT) type across all cells within each clock domain. VT mixing (e.g., mixing LVT, SVT, ULVT cells in the same clock tree) can cause skew and timing issues. The checker analyzes clock tree structure reports and cell-to-instance mappings to detect VT inconsistencies. Certain cells with clock attributes but used in data paths (e.g., generator inputs, clock dividers) are identified as waiver candidates since they legitimately may have different VT types.

---

## Check Logic

### Input Parsing

**File 1: clock_cells_with_cell_type.txt**
- Format: Instance-to-cell mapping showing clock tree cells with VT types
- Each line: `instance_path : cell_name`
- Cell name contains VT suffix (LVT/ULVT/SVT/HVT/RVT)

**File 2: IMP-8-0-0-14.rpt**
- Format: Hierarchical clock tree structure report
- Contains multiple clock domains with level-by-level breakdown
- Includes cell types, VT variants, and special markers (generator input, generated clock tree)

**Key Patterns:**

```python
# Pattern 1: Clock tree header - identifies clock domain
pattern_clock_tree = r'^(Generated )?[Cc]lock tree ([^:]+):'
# Example: "Clock tree clk_ctlr_phase_0_1dto4:"

# Pattern 2: Instance to cell mapping with VT extraction
pattern_instance_cell = r'^([^:]+)\s*:\s*(\S+)$'
# Example: "cdn_hs_phy/inst_adrctl_slice_core/.../RC_CGIC_INST : CKLNQD4BWP300H8P64PDULVT"

# Pattern 3: VT type extraction from cell name suffix
pattern_vt_type = r'(LVT|ULVT|SVT|HVT|RVT)(?:\s|$)'
# Example: "CKLNQD4BWP300H8P64PDULVT" -> extracts "ULVT"

# Pattern 4: Cell instance with VT in tree report
pattern_cell_in_tree = r'\(([A-Z0-9]+BWP[0-9]+[A-Z0-9]+PD(UL)?(LVT|SVT|SLVT|ULVT|HVT))\)'
# Example: "\\_ (L2) clk4x_I1CLK_IOBUF/I -> ZN (DCCKND8BWP300H8P64PDULVT)"

# Pattern 5: Generator input marker (waiver candidate)
pattern_generator_input = r'\(generator input\)'
# Example: "...hic_dnt_out_reg/CP (DFRPQD4BWP300H8P64PDULVT) (generator input)"

# Pattern 6: Generated clock tree marker (waiver candidate)
pattern_generated_clock = r'\(generated clock tree ([^)]+)\)'
# Example: "(generated clock tree clk_phy_db2_opcg_phase_0_1dto4)"

# Pattern 7: Clock gate cell identification
pattern_clock_gate = r'^(CKLNQD|CKLN|CKG|CLKG)'
# Example: "CKLNQD4BWP300H8P64PDULVT"

# Pattern 8: Clock buffer/inverter identification
pattern_clock_buffer = r'^(DCCKND|DCCK|CKBD|CKND)'
# Example: "DCCKND8BWP300H8P64PDULVT"

# Pattern 9: Instance path extraction for waiver reporting
pattern_instance_path = r'\(L\d+\)\s+([^/\s]+(?:/[^/\s]+)*)/([A-Z]+)\s+\(([A-Z0-9]+)\)'
# Example: "\\_ (L6) inst_slice_clk_gen/.../hic_dnt_out_reg/CP (DFRPQD4BWP300H8P64PDULVT)"
```

### Detection Logic

**Step 1: Parse clock_cells_with_cell_type.txt**
- Extract instance_path and cell_name from each line
- Extract VT type from cell_name using regex (LVT, ULVT, SVT, HVT, RVT)
- Build dictionary: `{instance_path: (cell_name, vt_type)}`

**Step 2: Parse IMP-8-0-0-14.rpt**
- Track current clock tree context using state machine
- For each clock tree section:
  - Extract all cell instances with VT types
  - Identify generator inputs and generated clock markers
  - Build per-tree VT distribution: `{clock_tree: {vt_type: count}}`

**Step 3: Aggregate VT statistics per clock tree**
- Combine data from both files
- Calculate VT distribution for each clock domain
- Identify dominant VT (most common VT type in each tree)

**Step 4: Detect VT mixing violations**
- For each clock tree:
  - If only one VT type present → PASS (clean)
  - If multiple VT types present → Check for waivers:
    - Cells marked as "(generator input)" → Waiver candidate
    - Cells in "(generated clock tree)" → Waiver candidate
    - Clock gates with different VT → Waiver candidate (may be used in data path)
    - Clock buffers/inverters with different VT → Violation (strict requirement)

**Step 5: Classify results**
- **INFO01 (Clean trees)**: Clock trees with single VT type
- **ERROR01 (Violations)**: Clock trees with VT mixing (non-waiverable cells)
- **WAIVER candidates**: Cells with clock attribute but used as data (generator inputs, clock dividers)

**Algorithm:**
1. Parse all lines from both input files
2. Extract VT type from each cell_name using regex
3. Group cells by clock tree name
4. Calculate VT distribution per clock tree
5. Identify dominant VT (mode) for each tree
6. For each cell with non-dominant VT:
   - Check if marked as generator input → Waiver list
   - Check if in generated clock tree → Waiver list
   - Check if clock gate → Waiver candidate
   - Otherwise → Violation (ERROR01)
7. Generate summary statistics and violation reports

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

**Rationale:** This checker validates the VT consistency status of specific clock trees. The pattern_items represent clock trees to check for VT mixing. Only clock trees listed in pattern_items are analyzed - if a tree has VT mixing, it appears in missing_items (status wrong); if clean, it appears in found_items (status correct). Clock trees not in pattern_items are ignored, making this a status check rather than existence check.

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
item_desc = "Confirm no VT mixing on clock tree for all modes. For some instances has clock attribute but used as data, please list that into Waiver list."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "All clock trees have consistent VT types (no mixing detected)"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All specified clock trees validated with consistent VT types"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "No VT mixing found in any clock tree across all modes"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All specified clock trees matched and validated with single VT type per tree"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "VT mixing detected in one or more clock trees"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "VT consistency requirement not satisfied for specified clock trees"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Clock trees with multiple VT types detected (mixing violations found)"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "VT consistency pattern not satisfied - multiple VT types found in specified clock trees"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Clock cells with clock attribute but used as data (waived VT mixing)"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Clock-attributed cell used in data path - VT mixing acceptable per design requirements"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries (no matching VT mixing violations found)"
unused_waiver_reason = "Waiver not matched - specified instance not found or has no VT mixing violation"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "[clock_tree_name]: VT={vt_type}, Total cells={count}, Status=CLEAN"
  Example: "clk_ctlr_phase_0_1dto4: VT=ULVT, Total cells=245, Status=CLEAN"

ERROR01 (Violation/Fail items):
  Format: "[clock_tree_name]: VT_MIXING detected - VT types: {LVT: count, ULVT: count, ...}"
  Example: "clk_phy_db2_opcg_phase_0_1dto4: VT_MIXING detected - VT types: {ULVT: 180, LVT: 15, SVT: 3}"

WAIVER (Generator inputs/data path usage):
  Format: "[instance_path]: Cell={cell_name}, VT={vt_type}, Reason: {marker}"
  Example: "inst_slice_clk_gen/inst_superset_clk_div/LOOP_0__inst_clk4x_div_opcg/inst_ao/inst_clk_div/hic_dnt_out_reg: Cell=DFRPQD4BWP300H8P64PDULVT, VT=ULVT, Reason: generator input"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-14:
  description: "Confirm no VT mixing on clock tree for all modes. For some instances has clock attribute but used as data, please list that into Waiver list."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/clock_cells_with_cell_type.txt"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-14.rpt"
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
Reason: No VT mixing found in any clock tree across all modes
INFO01:
  - clk_ctlr_phase_0_1dto4: VT=ULVT, Total cells=245, Status=CLEAN
  - clk_phy_db2_opcg_phase_0_1dto4: VT=ULVT, Total cells=198, Status=CLEAN
  - clk4x: VT=ULVT, Total cells=87, Status=CLEAN
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Clock trees with multiple VT types detected (mixing violations found)
ERROR01:
  - clk_ctlr_phase_0_1dto4: VT_MIXING detected - VT types: {ULVT: 230, LVT: 15}
  - clk_phy_db2_opcg_phase_0_1dto4: VT_MIXING detected - VT types: {ULVT: 180, SVT: 18}
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-14:
  description: "Confirm no VT mixing on clock tree for all modes. For some instances has clock attribute but used as data, please list that into Waiver list."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/clock_cells_with_cell_type.txt"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-14.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: VT mixing check is informational only for this design phase"
      - "Note: Clock tree VT optimization will be performed in final implementation stage"
      - "Rationale: Early design exploration allows mixed VT for power/performance trade-off analysis"
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
  - "Explanation: VT mixing check is informational only for this design phase"
  - "Note: Clock tree VT optimization will be performed in final implementation stage"
  - "Rationale: Early design exploration allows mixed VT for power/performance trade-off analysis"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - clk_ctlr_phase_0_1dto4: VT_MIXING detected - VT types: {ULVT: 230, LVT: 15} [WAIVED_AS_INFO]
  - clk_phy_db2_opcg_phase_0_1dto4: VT_MIXING detected - VT types: {ULVT: 180, SVT: 18} [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-14:
  description: "Confirm no VT mixing on clock tree for all modes. For some instances has clock attribute but used as data, please list that into Waiver list."
  requirements:
    value: 3
    pattern_items:
      - "clk_ctlr_phase_0_1dto4"
      - "clk_phy_db2_opcg_phase_0_1dto4"
      - "clk4x"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/clock_cells_with_cell_type.txt"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-14.rpt"
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
Reason: All specified clock trees matched and validated with single VT type per tree
INFO01:
  - clk_ctlr_phase_0_1dto4: VT=ULVT, Total cells=245, Status=CLEAN
  - clk_phy_db2_opcg_phase_0_1dto4: VT=ULVT, Total cells=198, Status=CLEAN
  - clk4x: VT=ULVT, Total cells=87, Status=CLEAN
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-14:
  description: "Confirm no VT mixing on clock tree for all modes. For some instances has clock attribute but used as data, please list that into Waiver list."
  requirements:
    value: 0
    pattern_items:
      - "clk_ctlr_phase_0_1dto4"
      - "clk_phy_db2_opcg_phase_0_1dto4"
      - "clk4x"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/clock_cells_with_cell_type.txt"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-14.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: VT mixing check is informational for specified clock trees during design exploration"
      - "Note: These clock trees are under active optimization and VT mixing is expected"
      - "Rationale: Final VT consistency will be enforced in tape-out checklist"
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
  - "Explanation: VT mixing check is informational for specified clock trees during design exploration"
  - "Note: These clock trees are under active optimization and VT mixing is expected"
  - "Rationale: Final VT consistency will be enforced in tape-out checklist"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - clk_ctlr_phase_0_1dto4: VT_MIXING detected - VT types: {ULVT: 230, LVT: 15} [WAIVED_AS_INFO]
  - clk_phy_db2_opcg_phase_0_1dto4: VT_MIXING detected - VT types: {ULVT: 180, SVT: 18} [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-14:
  description: "Confirm no VT mixing on clock tree for all modes. For some instances has clock attribute but used as data, please list that into Waiver list."
  requirements:
    value: 3
    pattern_items:
      - "clk_ctlr_phase_0_1dto4"
      - "clk_phy_db2_opcg_phase_0_1dto4"
      - "clk4x"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/clock_cells_with_cell_type.txt"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-14.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "inst_slice_clk_gen/inst_superset_clk_div/LOOP_0__inst_clk4x_div_opcg/inst_ao/inst_clk_div/hic_dnt_out_reg"
        reason: "Waived - generator input cell, clock attribute but used as data path"
      - name: "cdn_hs_phy/inst_adrctl_slice_core/inst_acm_slice_num_0/inst_acs_ctrl_top/inst_acs_dcc/CDN_1ACH_LP_CLKG_RC_CG_HIER_INST0/RC_CGIC_INST"
        reason: "Waived - clock gate used in data path per design review, VT=LVT acceptable"
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
  - inst_slice_clk_gen/inst_superset_clk_div/LOOP_0__inst_clk4x_div_opcg/inst_ao/inst_clk_div/hic_dnt_out_reg: Cell=DFRPQD4BWP300H8P64PDULVT, VT=ULVT, Reason: generator input [WAIVER]
  - cdn_hs_phy/inst_adrctl_slice_core/inst_acm_slice_num_0/inst_acs_ctrl_top/inst_acs_dcc/CDN_1ACH_LP_CLKG_RC_CG_HIER_INST0/RC_CGIC_INST: Cell=CKLNQD4BWP300H8P64PDLVT, VT=LVT, Reason: clock gate in data path [WAIVER]
WARN01 (Unused Waivers):
  - (none - all waivers matched)
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-14:
  description: "Confirm no VT mixing on clock tree for all modes. For some instances has clock attribute but used as data, please list that into Waiver list."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/clock_cells_with_cell_type.txt"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-14.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "inst_slice_clk_gen/inst_superset_clk_div/LOOP_0__inst_clk4x_div_opcg/inst_ao/inst_clk_div/hic_dnt_out_reg"
        reason: "Waived - generator input cell, clock attribute but used as data path"
      - name: "cdn_hs_phy/inst_adrctl_slice_core/inst_acm_slice_num_0/inst_acs_ctrl_top/inst_acs_dcc/CDN_1ACH_LP_CLKG_RC_CG_HIER_INST0/RC_CGIC_INST"
        reason: "Waived - clock gate used in data path per design review, VT=LVT acceptable"
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
  - inst_slice_clk_gen/inst_superset_clk_div/LOOP_0__inst_clk4x_div_opcg/inst_ao/inst_clk_div/hic_dnt_out_reg: Cell=DFRPQD4BWP300H8P64PDULVT, VT=ULVT, Reason: generator input [WAIVER]
  - cdn_hs_phy/inst_adrctl_slice_core/inst_acm_slice_num_0/inst_acs_ctrl_top/inst_acs_dcc/CDN_1ACH_LP_CLKG_RC_CG_HIER_INST0/RC_CGIC_INST: Cell=CKLNQD4BWP300H8P64PDLVT, VT=LVT, Reason: clock gate in data path [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 8.0_PHYSICAL_IMPLEMENTATION_CHECK --checkers IMP-8-0-0-14 --force

# Run individual tests
python IMP-8-0-0-14.py
```

---

## Notes

**VT Type Extraction:**
- VT types are extracted from cell name suffixes using regex pattern `(LVT|ULVT|SVT|HVT|RVT)`
- Common patterns: `PDULVT` → ULVT, `PDLVT` → LVT, `PDSVT` → SVT
- Cell names without recognizable VT suffix generate warnings and are skipped

**Waiver Candidates:**
- Cells marked with `(generator input)` in tree report
- Cells in `(generated clock tree ...)` sections
- Clock gates (CKLNQD, CKLN, CKG, CLKG prefix) may legitimately have different VT if used in data path
- Clock buffers/inverters (DCCKND, DCCK, CKBD, CKND) are less likely to be waiverable

**Edge Cases:**
- Empty files or no valid entries → Report INFO: No clock cells found
- Clock trees with Total FF: 0 → Report as INFO with no VT data
- Multiple VT variants (LVT, ULVT, SLVT) → Treat as distinct types
- Nested generated clocks → Track parent-child relationships for waiver context
- Truncated paths with "... (N sinks omitted)" → Count visible cells only

**Limitations:**
- VT extraction relies on standard cell naming conventions (BWP library format)
- Non-standard cell names may not be parsed correctly
- Hierarchical path depth analysis assumes "/" as separator
- Multi-file aggregation combines statistics across all input files