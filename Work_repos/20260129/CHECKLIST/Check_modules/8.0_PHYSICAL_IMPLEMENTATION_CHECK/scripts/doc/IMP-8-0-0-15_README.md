# IMP-8-0-0-15: Confirm clock tree VT requirements were met.

## Overview

**Check ID:** IMP-8-0-0-15  
**Description:** Confirm clock tree VT requirements were met.  
**Category:** Physical Implementation - Clock Tree Synthesis Verification  
**Input Files:** 
- `${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/clock_cells_with_cell_type.txt`
- `${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-14.rpt`

This checker verifies that all clock tree cells (clock gates, buffers, inverters, and flip-flops) meet the required threshold voltage (VT) specifications. It parses clock tree reports and cell lists to extract VT types (ULVT, LVT, SVT, HVT) from cell names and validates them against design requirements. The checker aggregates statistics across all clock domains and reports violations where cells use incorrect VT types.

---

## Check Logic

### Input Parsing

**File 1: clock_cells_with_cell_type.txt**
- Format: Line-by-line list of clock cells with hierarchical paths and cell types
- Pattern: `instance_path : CELL_TYPE`
- Extract VT type from cell name suffix (ULVT, LVT, SVT, HVT)

**File 2: IMP-8-0-0-14.rpt**
- Format: Hierarchical clock tree report with cell instances and fanout levels
- Contains clock tree headers, cell instances with VT types, and flip-flop endpoints
- Extract clock tree name, cell instances, VT types, and hierarchy levels

**Key Patterns:**
```python
# Pattern 1: Clock cell instance with cell type (clock_cells_with_cell_type.txt)
pattern1 = r'^([^:]+)\s*:\s*(\S+)\s*$'
# Example: "cdn_hs_phy/inst_adrctl_slice_core/.../RC_CGIC_INST : CKLNQD4BWP300H8P64PDULVT"

# Pattern 2: VT classification - ULVT (Ultra Low VT)
pattern2 = r'(ULVT)(?:\s|$)'
# Example: "CKLNQD4BWP300H8P64PDULVT"

# Pattern 3: VT classification - LVT (Low VT, excluding ULVT)
pattern3 = r'(?<!U)(LVT)(?:\s|$)'
# Example: "CKLNQD4BWP300H8P64PDLVT"

# Pattern 4: VT classification - SVT/RVT (Standard VT)
pattern4 = r'(SVT|RVT)(?:\s|$)'
# Example: "DCCKND8BWP300H8P64PDSVT"

# Pattern 5: VT classification - HVT (High VT)
pattern5 = r'(HVT)(?:\s|$)'
# Example: "DCCKND8BWP300H8P64PDHVT"

# Pattern 6: Clock tree header (IMP-8-0-0-14.rpt)
pattern6 = r'^(Generated )?[Cc]lock tree ([^:]+):'
# Example: "Clock tree clk_ctlr_phase_0_1dto4:"

# Pattern 7: Cell instance with VT type and level (IMP-8-0-0-14.rpt)
pattern7 = r'\(L(\d+)\)\s+([^/\s]+)/([A-Z]+)\s*->\s*([A-Z]+)\s*\(([A-Z0-9]+BWP[^)]+PD(ULVT|LVT|RVT|SLVT|HVT))\)'
# Example: "   \_ (L2) clk4x_I1CLK_IOBUF/I -> ZN (DCCKND8BWP300H8P64PDULVT)"

# Pattern 8: CTS-generated cell instance (IMP-8-0-0-14.rpt)
pattern8 = r'\(L(\d+)\)\s+(CTS_[^/\s]+)/([A-Z]+)\s*->\s*([A-Z]+)\s*\(([A-Z0-9]+BWP[^)]+PD(ULVT|LVT|RVT|SLVT|HVT))\)'
# Example: "       \_ (L8) CTS_ccl_a_inv_01377/I -> ZN (DCCKND6BWP300H8P64PDULVT)"

# Pattern 9: Flip-flop endpoint with VT type (IMP-8-0-0-14.rpt)
pattern9 = r'\(L(\d+)\)\s+([^/\s]+)/CP\s*\(([A-Z0-9]+BWP[^)]+PD(ULVT|LVT|RVT|SLVT|HVT))\)'
# Example: "                       \_ (L6) inst_slice_clk_gen/.../hic_dnt_out_reg/CP (DFRPQD4BWP300H8P64PDULVT)"
```

### Detection Logic

1. **Parse Input Files:**
   - Read both input files line-by-line
   - For clock_cells_with_cell_type.txt: Extract instance path and cell type
   - For IMP-8-0-0-14.rpt: Track current clock tree context and extract cell instances with levels

2. **Extract VT Types:**
   - Apply VT classification patterns to cell names
   - Categorize each cell as ULVT, LVT, SVT/RVT, HVT, or UNKNOWN
   - Track cell function (clock gate, buffer/inverter, flip-flop)

3. **Aggregate Statistics:**
   - Count total cells per clock tree
   - Count cells by VT type (ULVT, LVT, SVT, HVT)
   - Calculate percentages for each VT type

4. **Validate Against Requirements:**
   - Compare detected VT types against required VT types (from config or command-line args)
   - Typical requirement: All clock tree cells must be LVT or ULVT (no SVT/HVT allowed)
   - Flag violations where cells use incorrect VT types

5. **Report Results:**
   - INFO01: Summary statistics (total cells, VT breakdown, percentages)
   - ERROR01: Violations with instance path, cell type, detected VT, required VT, and hierarchy level

6. **Edge Cases:**
   - Empty lines or comments: Skip
   - Duplicate instance paths: Count each occurrence or flag as error
   - Cell types without clear VT suffix: Flag as UNKNOWN VT
   - Missing colon delimiter: Skip with warning
   - Whitespace variations: Handle with flexible regex

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

**Rationale:** This checker validates VT requirements for clock tree cells. The pattern_items represent specific clock trees or cell instances to check. The checker examines each matched item's VT status (ULVT/LVT/SVT/HVT) and reports violations only for items that match the pattern but have incorrect VT types. Cells not in pattern_items are not reported, making this a status check rather than an existence check.

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
item_desc = "Confirm clock tree VT requirements were met."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "All clock tree cells found with correct VT types"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All clock tree VT requirements satisfied"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "All clock tree cells found with correct VT types (ULVT/LVT as required)"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All clock tree VT requirements matched and validated (100% ULVT/LVT compliance)"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Clock tree cells with incorrect VT types found"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Clock tree VT requirements not satisfied (violations detected)"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Clock tree cells with incorrect VT types found (SVT/HVT detected, ULVT/LVT required)"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Clock tree VT requirements not satisfied (cells with incorrect VT types detected)"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Clock tree VT violations waived per design approval"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Clock tree VT violation waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused clock tree VT waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding VT violation found in clock tree"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "[clock_tree_name]: [total_cells] cells analyzed, [ulvt_count] ULVT ([ulvt_pct]%), [lvt_count] LVT ([lvt_pct]%), [svt_count] SVT ([svt_pct]%), [hvt_count] HVT ([hvt_pct]%)"
  Example: "clk_ctlr_phase_0_1dto4: 45 cells analyzed, 42 ULVT (93.3%), 3 LVT (6.7%), 0 SVT (0.0%), 0 HVT (0.0%)"

ERROR01 (Violation/Fail items):
  Format: "[clock_tree_name]: [instance_path] has [actual_vt], expected [required_vt] (Level [level]) - Cell: [cell_type]"
  Example: "clk_ctlr_phase_0_1dto4: CTS_ccl_a_inv_01377 has SVT, expected ULVT/LVT (Level 8) - Cell: DCCKND6BWP300H8P64PDSVT"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-15:
  description: "Confirm clock tree VT requirements were met."
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
Reason: All clock tree cells found with correct VT types (ULVT/LVT as required)
INFO01:
  - clk_ctlr_phase_0_1dto4: 45 cells analyzed, 42 ULVT (93.3%), 3 LVT (6.7%), 0 SVT (0.0%), 0 HVT (0.0%)
  - clk_sys_main: 128 cells analyzed, 120 ULVT (93.8%), 8 LVT (6.2%), 0 SVT (0.0%), 0 HVT (0.0%)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Clock tree cells with incorrect VT types found (SVT/HVT detected, ULVT/LVT required)
ERROR01:
  - clk_ctlr_phase_0_1dto4: CTS_ccl_a_inv_01377 has SVT, expected ULVT/LVT (Level 8) - Cell: DCCKND6BWP300H8P64PDSVT
  - clk_sys_main: cdn_hs_phy/inst_adrctl_slice_core/.../RC_CGIC_INST has HVT, expected ULVT/LVT (Level 2) - Cell: CKLNQD4BWP300H8P64PDHVT
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-15:
  description: "Confirm clock tree VT requirements were met."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/clock_cells_with_cell_type.txt"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-14.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Clock tree VT violations are informational only for this design revision"
      - "Note: SVT/HVT cells in non-critical clock paths are acceptable per design team agreement"
      - "Rationale: VT optimization will be performed in final implementation phase"
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
  - "Explanation: Clock tree VT violations are informational only for this design revision"
  - "Note: SVT/HVT cells in non-critical clock paths are acceptable per design team agreement"
  - "Rationale: VT optimization will be performed in final implementation phase"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - clk_ctlr_phase_0_1dto4: CTS_ccl_a_inv_01377 has SVT, expected ULVT/LVT (Level 8) - Cell: DCCKND6BWP300H8P64PDSVT [WAIVED_AS_INFO]
  - clk_sys_main: cdn_hs_phy/inst_adrctl_slice_core/.../RC_CGIC_INST has HVT, expected ULVT/LVT (Level 2) - Cell: CKLNQD4BWP300H8P64PDHVT [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-15:
  description: "Confirm clock tree VT requirements were met."
  requirements:
    value: 2
    pattern_items:
      - "clk_ctlr_phase_0_1dto4"
      - "clk_sys_main"
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
Reason: All clock tree VT requirements matched and validated (100% ULVT/LVT compliance)
INFO01:
  - clk_ctlr_phase_0_1dto4: 45 cells analyzed, 42 ULVT (93.3%), 3 LVT (6.7%), 0 SVT (0.0%), 0 HVT (0.0%)
  - clk_sys_main: 128 cells analyzed, 120 ULVT (93.8%), 8 LVT (6.2%), 0 SVT (0.0%), 0 HVT (0.0%)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-15:
  description: "Confirm clock tree VT requirements were met."
  requirements:
    value: 0
    pattern_items:
      - "clk_ctlr_phase_0_1dto4"
      - "clk_sys_main"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/clock_cells_with_cell_type.txt"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-14.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Clock tree VT check is informational only for early design stages"
      - "Note: VT violations in specified clock trees are expected during initial CTS"
      - "Rationale: Final VT optimization will be performed after timing closure"
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
  - "Explanation: Clock tree VT check is informational only for early design stages"
  - "Note: VT violations in specified clock trees are expected during initial CTS"
  - "Rationale: Final VT optimization will be performed after timing closure"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - clk_ctlr_phase_0_1dto4: CTS_ccl_a_inv_01377 has SVT, expected ULVT/LVT (Level 8) - Cell: DCCKND6BWP300H8P64PDSVT [WAIVED_AS_INFO]
  - clk_sys_main: cdn_hs_phy/inst_adrctl_slice_core/.../RC_CGIC_INST has HVT, expected ULVT/LVT (Level 2) - Cell: CKLNQD4BWP300H8P64PDHVT [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-15:
  description: "Confirm clock tree VT requirements were met."
  requirements:
    value: 2
    pattern_items:
      - "clk_ctlr_phase_0_1dto4"
      - "clk_sys_main"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/clock_cells_with_cell_type.txt"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-14.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "clk_ctlr_phase_0_1dto4"
        reason: "Waived per design review - non-critical debug clock path, SVT acceptable for power optimization"
      - name: "clk_sys_main"
        reason: "Waived - low-frequency clock gate, HVT used for leakage reduction per power team approval"
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
  - clk_ctlr_phase_0_1dto4: CTS_ccl_a_inv_01377 has SVT, expected ULVT/LVT (Level 8) - Cell: DCCKND6BWP300H8P64PDSVT [WAIVER]
  - clk_sys_main: cdn_hs_phy/inst_adrctl_slice_core/.../RC_CGIC_INST has HVT, expected ULVT/LVT (Level 2) - Cell: CKLNQD4BWP300H8P64PDHVT [WAIVER]
WARN01 (Unused Waivers):
  - (none)
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-15:
  description: "Confirm clock tree VT requirements were met."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/clock_cells_with_cell_type.txt"
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-14.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "clk_ctlr_phase_0_1dto4"
        reason: "Waived per design review - non-critical debug clock path, SVT acceptable for power optimization"
      - name: "clk_sys_main"
        reason: "Waived - low-frequency clock gate, HVT used for leakage reduction per power team approval"
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
  - clk_ctlr_phase_0_1dto4: CTS_ccl_a_inv_01377 has SVT, expected ULVT/LVT (Level 8) - Cell: DCCKND6BWP300H8P64PDSVT [WAIVER]
  - clk_sys_main: cdn_hs_phy/inst_adrctl_slice_core/.../RC_CGIC_INST has HVT, expected ULVT/LVT (Level 2) - Cell: CKLNQD4BWP300H8P64PDHVT [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 8.0_PHYSICAL_IMPLEMENTATION_CHECK --checkers IMP-8-0-0-15 --force

# Run individual tests
python IMP-8-0-0-15.py
```

---

## Notes

**VT Type Extraction:**
- VT types are extracted from cell name suffixes using regex patterns
- Common VT types: ULVT (Ultra Low VT), LVT (Low VT), SVT/RVT (Standard VT), HVT (High VT)
- Cell names follow naming convention: `<base_name>BWP<tech><VT_type>`
- Example: `DCCKND8BWP300H8P64PDULVT` → VT type is ULVT

**VT Requirements:**
- Typical requirement: All clock tree cells must use ULVT or LVT for performance
- SVT/HVT cells in clock tree may cause timing violations or excessive skew
- Requirements may vary by clock domain (e.g., high-speed vs. low-power clocks)
- VT requirements should be specified in design constraints or configuration

**Cell Function Classification:**
- Clock gates: CKLNQ, CLKG, CG_HIER, RC_CGIC patterns
- CTS buffers/inverters: CTS_ccl_, CTS_cci_, DCCKND, DCCKBF patterns
- Flip-flops: Identified by /CP pin in hierarchical path

**Edge Cases:**
- Cells without clear VT suffix are flagged as UNKNOWN VT
- Duplicate instance paths may indicate netlist issues
- Empty clock trees (Total FF: 0) are skipped
- Whitespace variations around delimiters are handled by flexible regex

**Limitations:**
- VT requirements must be configured externally (not auto-detected)
- Cell naming conventions must follow standard library patterns
- Multi-file aggregation assumes consistent clock tree naming across files
- Waiver matching requires exact string match (including whitespace)