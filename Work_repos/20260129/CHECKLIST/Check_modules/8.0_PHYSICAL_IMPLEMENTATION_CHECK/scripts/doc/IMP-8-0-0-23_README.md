# IMP-8-0-0-23: confirm no unplaced cells in design.

## Overview

**Check ID:** IMP-8-0-0-23  
**Description:** confirm no unplaced cells in design.  
**Category:** Physical Implementation - Placement Verification  
**Input Files:** 
- `IMP-8-0-0-23_case0.rpt` - Placement status report containing unplaced cell information

This checker verifies that all cells in the design have been successfully placed during the physical implementation stage. The report uses a special indicator `0x0` to signify that no unplaced cells exist (PASS condition). If unplaced cells are present, the report lists their hierarchical paths (FAIL condition). This is a critical check to ensure placement completeness before proceeding to routing stages.

---

## Check Logic

### Input Parsing

The checker parses the placement report to detect either:
1. **PASS indicator**: The special marker `0x0` (signifies no unplaced cells)
2. **FAIL indicators**: Hierarchical cell instance paths (signifies unplaced cells exist)

**Key Patterns:**

```python
# Pattern 1: Special '0x0' indicator - PASS condition (no unplaced cells)
pattern_0x0 = r'^\s*0x0\s*$'
# Example: "0x0"

# Pattern 2: Hierarchical cell paths - FAIL condition (unplaced cells detected)
pattern_hierarchy = r'([^\s/]+(?:/[^\s/]+)+)'
# Example: "top/cpu_core/alu/adder_cell"
# Example: "design/block_a/subblock_b/cell_xyz"

# Pattern 3: Simple cell names without hierarchy (fallback)
pattern_simple = r'\S+'
# Example: "unplaced_cell_name"
```

### Detection Logic

**Step 1: Initialize tracking variables**
- `unplaced_cells = []` - List to store unplaced cell instances
- `has_0x0_indicator = False` - Flag for PASS condition

**Step 2: Parse report line-by-line**
- Check each line for the `0x0` pattern first (highest priority)
- If `0x0` found: Set `has_0x0_indicator = True` and skip remaining lines
- If not `0x0`: Check for hierarchical paths using pattern_hierarchy
- Extract cell instance names from hierarchical paths

**Step 3: Extract cell information**
- For hierarchical paths: Extract full path and cell instance name (last component)
- For simple names: Extract cell name directly
- Add each unplaced cell to the `unplaced_cells` list

**Step 4: Determine PASS/FAIL**
- **PASS**: `has_0x0_indicator == True` AND `len(unplaced_cells) == 0`
- **FAIL**: `has_0x0_indicator == False` OR `len(unplaced_cells) > 0`

**Step 5: Generate output**
- **PASS**: Print "PASS" with confirmation message
- **FAIL**: Print "FAIL" with list of all unplaced cell instance names

**Edge Cases:**
- Empty file: Treat as invalid report (FAIL)
- File with only whitespace: Same as empty file
- Mixed format (both 0x0 and cell paths): Prioritize 0x0, log inconsistency warning
- Very large files: Stream processing, provide count summary

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `status_check`

**Selected Mode for this checker:** `status_check`

**Rationale:** This checker validates the placement status of cells in the design. The `0x0` indicator represents a status value (no unplaced cells), and any cell paths found represent items with incorrect status (unplaced). This is a status verification check rather than an existence check, as we're validating that cells have the correct placement status (placed vs. unplaced). The checker only reports cells that have the wrong status (unplaced), not all cells in the design.

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
item_desc = "confirm no unplaced cells in design."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "No unplaced cells found in design"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All cells successfully placed - 0x0 indicator matched"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "0x0 indicator found - no unplaced cells detected in design"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Placement status validated - 0x0 indicator matched, all cells placed successfully"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Unplaced cells detected in design"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Placement incomplete - unplaced cells found in design"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Unplaced cell instance detected - placement incomplete"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Cell placement status not satisfied - instance remains unplaced"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Waived unplaced cells (approved exceptions)"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Unplaced cell waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries for unplaced cells"
unused_waiver_reason = "Waiver not matched - no corresponding unplaced cell found in report"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [cell_instance_path]: [found_reason]"
  Example: "- 0x0: Placement status validated - 0x0 indicator matched, all cells placed successfully"

ERROR01 (Violation/Fail items):
  Format: "- [cell_instance_path]: [missing_reason]"
  Example: "- top/cpu_core/alu/adder_cell: Cell placement status not satisfied - instance remains unplaced"
  Example: "- design/block_a/subblock_b/cell_xyz: Cell placement status not satisfied - instance remains unplaced"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-23:
  description: "confirm no unplaced cells in design."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "reports/8.0/IMP-8-0-0-23/IMP-8-0-0-23_case0.rpt"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs a boolean validation of placement completeness. The checker parses the report to detect the `0x0` indicator (PASS) or unplaced cell paths (FAIL). PASS if `0x0` is found and no unplaced cells exist; FAIL if unplaced cells are detected.

**Sample Output (PASS):**
```
Status: PASS
Reason: 0x0 indicator found - no unplaced cells detected in design
INFO01:
  - 0x0: 0x0 indicator found - no unplaced cells detected in design
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Unplaced cell instance detected - placement incomplete
ERROR01:
  - top/cpu_core/alu/adder_cell: Unplaced cell instance detected - placement incomplete
  - design/block_a/subblock_b/cell_xyz: Unplaced cell instance detected - placement incomplete
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-23:
  description: "confirm no unplaced cells in design."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "reports/8.0/IMP-8-0-0-23/IMP-8-0-0-23_case0.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Unplaced cells are acceptable during early placement exploration phase"
      - "Note: This check is informational only - unplaced cells will be resolved in incremental placement"
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
  - "Explanation: Unplaced cells are acceptable during early placement exploration phase"
  - "Note: This check is informational only - unplaced cells will be resolved in incremental placement"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - top/cpu_core/alu/adder_cell: Unplaced cell instance detected - placement incomplete [WAIVED_AS_INFO]
  - design/block_a/subblock_b/cell_xyz: Unplaced cell instance detected - placement incomplete [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-23:
  description: "confirm no unplaced cells in design."
  requirements:
    value: 1
    pattern_items:
      - "0x0"  # Expected indicator for no unplaced cells (PASS condition)
  input_files:
    - "reports/8.0/IMP-8-0-0-23/IMP-8-0-0-23_case0.rpt"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Description: "confirm no unplaced cells in design" → Check for PLACEMENT STATUS indicator
- pattern_items contains the expected status value: `"0x0"` (no unplaced cells indicator)
- This is a status validation check, not a cell name check
- ✅ CORRECT: `"0x0"` (status indicator)
- ❌ WRONG: Cell instance names (those are violations, not expected patterns)

**Check Behavior:**
Type 2 searches for the `0x0` pattern in the input report. This is a violation check where:
- **PASS**: `found_items` is empty (no unplaced cells, `0x0` indicator present)
- **FAIL**: `found_items` contains unplaced cell paths (violations detected)

The checker validates placement status by checking if the report contains the `0x0` indicator (PASS) or unplaced cell paths (FAIL).

**Sample Output (PASS):**
```
Status: PASS
Reason: Placement status validated - 0x0 indicator matched, all cells placed successfully
INFO01:
  - 0x0: Placement status validated - 0x0 indicator matched, all cells placed successfully
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Cell placement status not satisfied - instance remains unplaced
ERROR01:
  - top/cpu_core/alu/adder_cell: Cell placement status not satisfied - instance remains unplaced
  - design/block_a/subblock_b/cell_xyz: Cell placement status not satisfied - instance remains unplaced
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-23:
  description: "confirm no unplaced cells in design."
  requirements:
    value: 1
    pattern_items:
      - "0x0"
  input_files:
    - "reports/8.0/IMP-8-0-0-23/IMP-8-0-0-23_case0.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Unplaced cells are acceptable during incremental placement optimization"
      - "Note: Pattern mismatches are expected in early design stages and do not require immediate fixes"
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
  - "Explanation: Unplaced cells are acceptable during incremental placement optimization"
  - "Note: Pattern mismatches are expected in early design stages and do not require immediate fixes"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - top/cpu_core/alu/adder_cell: Cell placement status not satisfied - instance remains unplaced [WAIVED_AS_INFO]
  - design/block_a/subblock_b/cell_xyz: Cell placement status not satisfied - instance remains unplaced [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-23:
  description: "confirm no unplaced cells in design."
  requirements:
    value: 1
    pattern_items:
      - "0x0"  # Expected indicator for no unplaced cells
  input_files:
    - "reports/8.0/IMP-8-0-0-23/IMP-8-0-0-23_case0.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "top/cpu_core/alu/adder_cell"
        reason: "Waived - spare cell intentionally left unplaced for ECO purposes"
      - name: "design/memory_ctrl/buffer_inst/flop_23"
        reason: "Waived - debug cell excluded from placement per design team approval"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2 (check for `0x0` indicator), plus waiver classification:
- Match unplaced cell paths (found_items) against waive_items
- Unwaived cells → ERROR (need fix)
- Waived cells → INFO with [WAIVER] tag (approved exceptions)
- Unused waivers → WARN with [WAIVER] tag
PASS if all unplaced cells are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - top/cpu_core/alu/adder_cell: Unplaced cell waived per design team approval: Waived - spare cell intentionally left unplaced for ECO purposes [WAIVER]
WARN01 (Unused Waivers):
  - design/memory_ctrl/buffer_inst/flop_23: Waiver not matched - no corresponding unplaced cell found in report: Waived - debug cell excluded from placement per design team approval [WAIVER]
```

**Sample Output (with unwaived violations):**
```
Status: FAIL
Reason: Cell placement status not satisfied - instance remains unplaced
ERROR01:
  - design/block_a/subblock_b/cell_xyz: Cell placement status not satisfied - instance remains unplaced
INFO01 (Waived):
  - top/cpu_core/alu/adder_cell: Unplaced cell waived per design team approval: Waived - spare cell intentionally left unplaced for ECO purposes [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-23:
  description: "confirm no unplaced cells in design."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "reports/8.0/IMP-8-0-0-23/IMP-8-0-0-23_case0.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "top/cpu_core/alu/adder_cell"
        reason: "Waived - spare cell intentionally left unplaced for ECO purposes"
      - name: "design/memory_ctrl/buffer_inst/flop_23"
        reason: "Waived - debug cell excluded from placement per design team approval"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (cell instance paths)
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (parse for `0x0` or unplaced cells), plus waiver classification:
- Match unplaced cell violations against waive_items
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output:**
```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - top/cpu_core/alu/adder_cell: Unplaced cell waived per design team approval: Waived - spare cell intentionally left unplaced for ECO purposes [WAIVER]
WARN01 (Unused Waivers):
  - design/memory_ctrl/buffer_inst/flop_23: Waiver not matched - no corresponding unplaced cell found in report: Waived - debug cell excluded from placement per design team approval [WAIVER]
```

**Sample Output (with unwaived violations):**
```
Status: FAIL
Reason: Unplaced cell instance detected - placement incomplete
ERROR01:
  - design/block_a/subblock_b/cell_xyz: Unplaced cell instance detected - placement incomplete
INFO01 (Waived):
  - top/cpu_core/alu/adder_cell: Unplaced cell waived per design team approval: Waived - spare cell intentionally left unplaced for ECO purposes [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 8.0_PHYSICAL_IMPLEMENTATION_CHECK --checkers IMP-8-0-0-23 --force

# Run individual tests
python IMP-8-0-0-23.py
```

---

## Notes

**Special Indicator Handling:**
- The `0x0` value is a special indicator meaning "no unplaced cells found"
- `0x0` is NOT a cell instance name and should not be included in pattern_items for violation tracking
- If the report contains only `0x0`, all subsequent YAML configurations should have empty pattern_items

**Output Behavior:**
- **PASS**: Print "PASS" when `0x0` indicator is found
- **FAIL**: Print "FAIL" and list all unplaced cell instance names (hierarchical paths)

**Edge Cases:**
- Empty report files are treated as invalid (FAIL condition)
- Mixed format reports (both `0x0` and cell paths) prioritize the `0x0` indicator but log inconsistency warnings
- Very large reports with thousands of unplaced cells use streaming processing with count summaries

**Waiver Semantics:**
- For Type 3/4: waive_items.name contains cell instance paths (object identifiers to exempt)
- pattern_items contains status indicators (`"0x0"`), NOT cell names
- Waiver matching: Compare unplaced cell paths against waive_items.name for exemption