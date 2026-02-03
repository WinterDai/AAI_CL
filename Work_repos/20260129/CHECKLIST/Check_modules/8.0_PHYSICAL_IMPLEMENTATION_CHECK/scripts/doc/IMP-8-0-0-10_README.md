# IMP-8-0-0-10: Confirm you placed the discrete synchronizer flops close to each other (distance <= 10um) for process without dedicated 2/3 stage synchronizer library cell like TSMC. Make sure "no buffering on the Q->D path between sync flops" for the sync_regs falling under same hierarchy. Please fine tune clock tree for hold fixing. Please don't change the VT of synchronizer flops. (Check the Note. Fill N/A for library has 2/3 stages dedicated library cell)

## Overview

**Check ID:** IMP-8-0-0-10  
**Description:** Confirm you placed the discrete synchronizer flops close to each other (distance <= 10um) for process without dedicated 2/3 stage synchronizer library cell like TSMC. Make sure "no buffering on the Q->D path between sync flops" for the sync_regs falling under same hierarchy. Please fine tune clock tree for hold fixing. Please don't change the VT of synchronizer flops. (Check the Note. Fill N/A for library has 2/3 stages dedicated library cell)  
**Category:** Physical Implementation - Synchronizer Placement Verification  
**Input Files:** 
- `${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-10.rpt`

This checker validates physical placement of discrete synchronizer flip-flops to ensure proper CDC (Clock Domain Crossing) functionality. It verifies two critical requirements:
1. **Distance Constraint**: Consecutive synchronizer stages (Q->D pin pairs) must be placed within 10um of each other to minimize metastability propagation delay
2. **No Buffering**: The Q->D path between synchronizer flops in the same hierarchy must be direct with no intermediate buffers/inverters/muxes to prevent hold violations and maintain synchronizer integrity

The checker parses placement reports containing synchronizer group information with pin coordinates and calculates Euclidean distances between consecutive stages (e.g., hic_dnt_sync_reg0/Q -> hic_dnt_sync_reg1/D). Violations are flagged when distance exceeds 10um or when non-register cells are detected in the synchronizer chain.

---

## Check Logic

### Input Parsing
The checker parses synchronizer placement reports organized by groups. Each group contains pin entries with hierarchical paths and physical coordinates (x, y) in microns.

**Key Patterns:**
```python
# Pattern 1: Group header identifying synchronizer group number
pattern_group = r'^Group(\d+):'
# Example: "Group0:"

# Pattern 2: D pin entry with hierarchical path and coordinates
pattern_d_pin = r'PinName:\s+(.+?)/(hic_dnt_sync_reg\d+)/D\s*;\s*cellPT:\s*\{([\d.]+)\s+([\d.]+)\}'
# Example: "    PinName: inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_0__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_dff_out/hic_dnt_sync_reg1/D ; cellPT: {522.88 464.8}"

# Pattern 3: Q pin entry with hierarchical path and coordinates
pattern_q_pin = r'PinName:\s+(.+?)/(hic_dnt_sync_reg\d+)/Q\s*;\s*cellPT:\s*\{([\d.]+)\s+([\d.]+)\}'
# Example: "    PinName: inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_0__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_dff_out/hic_dnt_sync_reg0/Q ; cellPT: {523.328 465.15}"

# Pattern 4: Non-register cell (buffer/mux/inverter) indicating buffering violation
pattern_buffer = r'PinName:\s+(.+?)/(hic_dnt_(?:mux|buf|inv)[^/]*)/[A-Z]'
# Example: "    PinName: inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_0__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_mux2/hic_dnt_mux2/I0 ; cellPT: {521.472 467.48}"

# Pattern 5: Generic pin entry (fallback for comprehensive parsing)
pattern_generic = r'PinName:\s+([^;]+)\s*;\s*cellPT:\s*\{([\d.]+)\s+([\d.]+)\}'
# Example: "    PinName: inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_0__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_dff_out/hic_dnt_sync_reg2/Q ; cellPT: {521.984 466.95}"
```

### Detection Logic

**Step 1: File Parsing with State Machine**
- Iterate line-by-line through report file(s)
- Track current group number using pattern_group
- Accumulate all pin entries within each group until next group header or EOF
- Extract hierarchy path, register name, pin type (D/Q), and coordinates (x, y)

**Step 2: Pin Pair Matching**
- Within each group, match Q->D pin pairs by register naming convention
  - Stage 0->1: hic_dnt_sync_reg0/Q -> hic_dnt_sync_reg1/D
  - Stage 1->2: hic_dnt_sync_reg1/Q -> hic_dnt_sync_reg2/D
  - Stage 2->3: hic_dnt_sync_reg2/Q -> hic_dnt_sync_reg3/D
- Extract common synchronizer hierarchy path (parent path before register instance)

**Step 3: Distance Calculation**
- For each Q->D pair, calculate Euclidean distance:
  ```
  distance = sqrt((x_D - x_Q)^2 + (y_D - y_Q)^2)
  ```
- Threshold: 10.0 um
- Flag violation if distance > 10.0 um

**Step 4: Buffering Detection**
- Scan all pins within the synchronizer hierarchy path
- Detect non-register cells using pattern_buffer (hic_dnt_mux*, hic_dnt_buf*, hic_dnt_inv*)
- Flag violation if buffer/mux/inverter found between sync stages

**Step 5: Violation Reporting**
- Compliant groups: Report in INFO01 with distance and stage information
- Distance violations: Report in ERROR01 with actual distance and threshold
- Buffering violations: Report in ERROR01 with buffer cell name and hierarchy
- Summary: Total groups analyzed, compliant count, violation count

**Edge Cases:**
- Empty file or no groups: Return INFO01 with "0 groups analyzed"
- Unpaired pins (D without Q or vice versa): Report as WARNING for incomplete group
- Missing cellPT coordinates: Skip distance check, report data error in WARNING
- Multiple files: Aggregate all groups across files into single report

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

**Rationale:** This checker validates the placement status of synchronizer groups. The pattern_items represent specific synchronizer hierarchies to check. The checker examines each matched synchronizer group and reports whether it meets placement requirements (distance ≤10um, no buffering). Only synchronizer groups matching the pattern_items are analyzed and reported - other synchronizers in the file are ignored. PASS means all matched groups are compliant; FAIL means some matched groups violate distance or buffering constraints.

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
item_desc = "Synchronizer flop placement verification (distance ≤10um, no Q->D buffering)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "All synchronizer groups found with compliant placement"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All synchronizer groups matched and placement requirements satisfied"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "All synchronizer groups found with distance ≤10um and no buffering violations"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All synchronizer groups matched pattern and satisfied placement constraints (distance ≤10um, no Q->D buffering)"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Synchronizer placement violations found (distance >10um or buffering detected)"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Synchronizer groups matched but placement requirements not satisfied (distance >10um or buffering detected)"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Synchronizer placement violations found: distance >10um or buffering on Q->D path"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Synchronizer groups matched but placement constraints not satisfied: distance >10um or buffering violations detected"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Synchronizer placement violations waived per design approval"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Synchronizer placement violation waived per design team approval (distance or buffering exception granted)"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused synchronizer placement waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding synchronizer violation found in placement report"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "[hierarchy_path] Group N: Stage regX->regY distance=X.XXum (compliant)"
  Example: "inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_0__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_dff_out Group 0: Stage reg0->reg1 distance=0.58um (compliant)"

ERROR01 (Violation/Fail items):
  Format: "[hierarchy_path] Group N: VIOLATION - Distance=X.XXum (>10um threshold) | Stage: regX->regY"
          "[hierarchy_path] Group N: VIOLATION - Buffering detected: cell_name on Q->D path"
  Example: "inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_0__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_dff_out Group 0: VIOLATION - Distance=12.45um (>10um threshold) | Stage: reg0->reg1"
           "inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_0__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_mux2 Group 1: VIOLATION - Buffering detected: hic_dnt_mux2 on Q->D path"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-10:
  description: "Confirm you placed the discrete synchronizer flops close to each other (distance <= 10um) for process without dedicated 2/3 stage synchronizer library cell like TSMC. Make sure "no buffering on the Q->D path between sync flops" for the sync_regs falling under same hierarchy. Please fine tune clock tree for hold fixing. Please don't change the VT of synchronizer flops. (Check the Note. Fill N/A for library has 2/3 stages dedicated library cell)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-10.rpt"
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
Reason: All synchronizer groups found with distance ≤10um and no buffering violations
INFO01:
  - inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_0__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_dff_out Group 0: Stage reg0->reg1 distance=0.58um (compliant)
  - inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_0__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_dff_out Group 0: Stage reg1->reg2 distance=1.23um (compliant)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Synchronizer placement violations found: distance >10um or buffering on Q->D path
ERROR01:
  - inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_0__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_dff_out Group 0: VIOLATION - Distance=12.45um (>10um threshold) | Stage: reg0->reg1
  - inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_1__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_mux2 Group 1: VIOLATION - Buffering detected: hic_dnt_mux2 on Q->D path
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-10:
  description: "Confirm you placed the discrete synchronizer flops close to each other (distance <= 10um) for process without dedicated 2/3 stage synchronizer library cell like TSMC. Make sure "no buffering on the Q->D path between sync flops" for the sync_regs falling under same hierarchy. Please fine tune clock tree for hold fixing. Please don't change the VT of synchronizer flops. (Check the Note. Fill N/A for library has 2/3 stages dedicated library cell)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-10.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Synchronizer placement violations are informational only for this design revision"
      - "Note: Distance violations are expected in low-density regions and will be addressed in final placement optimization"
      - "Justification: Buffering on Q->D path is acceptable for non-critical CDC paths per design review"
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
  - "Explanation: Synchronizer placement violations are informational only for this design revision"
  - "Note: Distance violations are expected in low-density regions and will be addressed in final placement optimization"
  - "Justification: Buffering on Q->D path is acceptable for non-critical CDC paths per design review"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_0__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_dff_out Group 0: VIOLATION - Distance=12.45um (>10um threshold) | Stage: reg0->reg1 [WAIVED_AS_INFO]
  - inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_1__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_mux2 Group 1: VIOLATION - Buffering detected: hic_dnt_mux2 on Q->D path [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-10:
  description: "Confirm you placed the discrete synchronizer flops close to each other (distance <= 10um) for process without dedicated 2/3 stage synchronizer library cell like TSMC. Make sure "no buffering on the Q->D path between sync flops" for the sync_regs falling under same hierarchy. Please fine tune clock tree for hold fixing. Please don't change the VT of synchronizer flops. (Check the Note. Fill N/A for library has 2/3 stages dedicated library cell)"
  requirements:
    value: 2
    pattern_items:
      - "inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_0__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_dff_out"
      - "inst_data_path_top/inst_data_byte_macro/RD_CLK_GEN_0__inst_rd_slice_clk_gen/inst_rd_bit_clk_gen/inst_rst_n_clk2x_sync/inst_hic_dff_out"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-10.rpt"
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
Reason: All synchronizer groups matched pattern and satisfied placement constraints (distance ≤10um, no Q->D buffering)
INFO01:
  - inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_0__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_dff_out Group 0: Stage reg0->reg1 distance=0.58um (compliant)
  - inst_data_path_top/inst_data_byte_macro/RD_CLK_GEN_0__inst_rd_slice_clk_gen/inst_rd_bit_clk_gen/inst_rst_n_clk2x_sync/inst_hic_dff_out Group 1: Stage reg0->reg1 distance=1.23um (compliant)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-10:
  description: "Confirm you placed the discrete synchronizer flops close to each other (distance <= 10um) for process without dedicated 2/3 stage synchronizer library cell like TSMC. Make sure "no buffering on the Q->D path between sync flops" for the sync_regs falling under same hierarchy. Please fine tune clock tree for hold fixing. Please don't change the VT of synchronizer flops. (Check the Note. Fill N/A for library has 2/3 stages dedicated library cell)"
  requirements:
    value: 2
    pattern_items:
      - "inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_0__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_dff_out"
      - "inst_data_path_top/inst_data_byte_macro/RD_CLK_GEN_0__inst_rd_slice_clk_gen/inst_rd_bit_clk_gen/inst_rst_n_clk2x_sync/inst_hic_dff_out"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-10.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Synchronizer placement check is informational only for early design stages"
      - "Note: Pattern mismatches are expected during incremental placement and do not require immediate fixes"
      - "Justification: Distance violations will be resolved during final placement optimization phase"
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
  - "Explanation: Synchronizer placement check is informational only for early design stages"
  - "Note: Pattern mismatches are expected during incremental placement and do not require immediate fixes"
  - "Justification: Distance violations will be resolved during final placement optimization phase"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_0__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_dff_out Group 0: VIOLATION - Distance=12.45um (>10um threshold) | Stage: reg0->reg1 [WAIVED_AS_INFO]
  - inst_data_path_top/inst_data_byte_macro/RD_CLK_GEN_0__inst_rd_slice_clk_gen/inst_rd_bit_clk_gen/inst_rst_n_clk2x_sync/inst_hic_dff_out Group 1: VIOLATION - Buffering detected: hic_dnt_mux2 on Q->D path [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-10:
  description: "Confirm you placed the discrete synchronizer flops close to each other (distance <= 10um) for process without dedicated 2/3 stage synchronizer library cell like TSMC. Make sure "no buffering on the Q->D path between sync flops" for the sync_regs falling under same hierarchy. Please fine tune clock tree for hold fixing. Please don't change the VT of synchronizer flops. (Check the Note. Fill N/A for library has 2/3 stages dedicated library cell)"
  requirements:
    value: 2
    pattern_items:
      - "inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_0__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_dff_out"
      - "inst_data_path_top/inst_data_byte_macro/RD_CLK_GEN_0__inst_rd_slice_clk_gen/inst_rd_bit_clk_gen/inst_rst_n_clk2x_sync/inst_hic_dff_out"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-10.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_0__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_dff_out"
        reason: "Waived per design review - low-density region constraint, timing analysis confirms acceptable metastability window"
      - name: "inst_data_path_top/inst_data_byte_macro/RD_CLK_GEN_0__inst_rd_slice_clk_gen/inst_rd_bit_clk_gen/inst_rst_n_clk2x_sync/inst_hic_dff_out"
        reason: "Waived - mux required for test mode switching, CDC functionality verified by simulation"
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
  - inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_0__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_dff_out Group 0: VIOLATION - Distance=12.45um (>10um threshold) | Stage: reg0->reg1 [WAIVER]
  - inst_data_path_top/inst_data_byte_macro/RD_CLK_GEN_0__inst_rd_slice_clk_gen/inst_rd_bit_clk_gen/inst_rst_n_clk2x_sync/inst_hic_dff_out Group 1: VIOLATION - Buffering detected: hic_dnt_mux2 on Q->D path [WAIVER]
WARN01 (Unused Waivers):
  - (none)
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-10:
  description: "Confirm you placed the discrete synchronizer flops close to each other (distance <= 10um) for process without dedicated 2/3 stage synchronizer library cell like TSMC. Make sure \"no buffering on the Q->D path between sync flops\" for the sync_regs falling under same hierarchy. Please fine tune clock tree for hold fixing. Please don't change the VT of synchronizer flops. (Check the Note. Fill N/A for library has 2/3 stages dedicated library cell)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-10.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_0__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_dff_out"
        reason: "Waived per design review - low-density region constraint, timing analysis confirms acceptable metastability window"
      - name: "inst_data_path_top/inst_data_byte_macro/RD_CLK_GEN_0__inst_rd_slice_clk_gen/inst_rd_bit_clk_gen/inst_rst_n_clk2x_sync/inst_hic_dff_out"
        reason: "Waived - mux required for test mode switching, CDC functionality verified by simulation"
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
  - inst_data_path_top/inst_data_byte_macro/WR_CLK_GEN_0__inst_wr_slice_clk_gen/inst_wr_bit_clk_gen/inst_rst_n_clk4x_sync/inst_hic_dff_out Group 0: VIOLATION - Distance=12.45um (>10um threshold) | Stage: reg0->reg1 [WAIVER]
  - inst_data_path_top/inst_data_byte_macro/RD_CLK_GEN_0__inst_rd_slice_clk_gen/inst_rd_bit_clk_gen/inst_rst_n_clk2x_sync/inst_hic_dff_out Group 1: VIOLATION - Buffering detected: hic_dnt_mux2 on Q->D path [WAIVER]
WARN01 (Unused Waivers):
  - (none)
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 8.0_PHYSICAL_IMPLEMENTATION_CHECK --checkers IMP-8-0-0-10 --force

# Run individual tests
python IMP-8-0-0-10.py
```

---

## Notes

- **Distance Threshold**: 10um is the default threshold for synchronizer flop placement. This can be customized via pattern_items if needed.
- **Buffering Detection**: The checker detects any non-register cells (buffers, muxes, inverters) in the Q->D path between synchronizer stages.
- **Hierarchy Matching**: Synchronizer groups are identified by their common hierarchy path. Only flops within the same hierarchy are considered a synchronizer chain.
- **N/A for Dedicated Cells**: If the library provides dedicated 2/3 stage synchronizer cells (like TSMC), fill N/A as this check is not applicable.
- **VT Consistency**: The checker assumes VT (threshold voltage) consistency is verified separately. This check focuses on placement distance and buffering only.
- **Multi-stage Support**: The checker supports 2-stage, 3-stage, and higher synchronizer chains by analyzing consecutive reg0->reg1, reg1->reg2, etc. pairs