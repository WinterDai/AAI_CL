# IMP-8-0-0-04: Confirm buffers are attached for all ports and are set as fixed.

## Overview

**Check ID:** IMP-8-0-0-04  
**Description:** Confirm buffers are attached for all ports and are set as fixed.  
**Category:** Physical Implementation - Port Buffer Connectivity  
**Input Files:** C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-04\IMP-8-0-0-04.rpt

This checker validates that all design ports (excluding bidirectional ports and ports with null connections) have proper buffer/inverter cells attached and that these buffer cells are placed with "fixed" status. The check ensures clock and signal integrity by verifying that port drivers use approved buffer types (INV, BUF, CKND, CKBD, CKBMVPMZ, CKNMVPMZ, DCCK) and are locked in place to prevent placement optimization from moving them.

---

## Check Logic

### Input Parsing

The input file is a custom port-buffer connectivity report with the following format:
```
Port: {port_name}; Direction: {input|output|bidi}; Port_Pt: {x y}; Port_connected_cell_name: {cell_name(s)}; Port_connected_cell_pt: {x y}; Port_connected_cell_pStatus: {fixed|unfixed};
```

**Key Patterns:**

```python
# Pattern 1: Extract complete port entry with all fields
complete_line_pattern = r'Port:\s*\{?([^;}]+)\}?;\s*Direction:\s*(\w+);.*?Port_connected_cell_name:\s*([^;]+);.*?Port_connected_cell_pStatus:\s*([^;]+);'
# Example: "Port: clk4x; Direction: input; Port_Pt: {752.0 285.008}; Port_connected_cell_name: DCCKND8BWP300H8P64PDULVT; Port_connected_cell_pt: {748.544 284.312}; Port_connected_cell_pStatus: fixed;"
# Captures: Group 1=port_name, Group 2=direction, Group 3=cell_name(s), Group 4=placement_status(es)

# Pattern 2: Extract port name (handles bus notation with braces)
port_name_pattern = r'Port:\s*\{?([^;}]+)\}?;'
# Example: "Port: {pad_mem_data[7]};" → Captures "pad_mem_data[7]"

# Pattern 3: Extract port direction
direction_pattern = r'Direction:\s*(\w+);'
# Example: "Direction: input;" → Captures "input"

# Pattern 4: Extract connected buffer/IO cell name(s)
cell_name_pattern = r'Port_connected_cell_name:\s*([^;]+);'
# Example: "Port_connected_cell_name: DCCKND8BWP300H8P64PDULVT;" → Captures "DCCKND8BWP300H8P64PDULVT"
# Example: "Port_connected_cell_name: cdns_ddr_fb_txrx_h cdns_ddr_vref_dfe_h;" → Captures "cdns_ddr_fb_txrx_h cdns_ddr_vref_dfe_h"

# Pattern 5: Extract placement status(es)
status_pattern = r'Port_connected_cell_pStatus:\s*([^;]+);'
# Example: "Port_connected_cell_pStatus: fixed;" → Captures "fixed"
# Example: "Port_connected_cell_pStatus: fixed fixed unfixed;" → Captures "fixed fixed unfixed"

# Pattern 6: Approved buffer cell prefixes
approved_buffer_prefixes = ['INV', 'BUF', 'CKND', 'CKBD', 'CKBMVPMZ', 'CKNMVPMZ', 'DCCK']
```

### Detection Logic

**Step 1: Filter Ports**
- Parse each line using the complete line pattern
- **Exclude** ports with `Direction: bidi` (bidirectional ports are not checked)
- **Exclude** ports with `Port_connected_cell_name: 0x0` (null connections are not checked)

**Step 2: Validate Buffer Type**
For remaining ports:
- Extract `Port_connected_cell_name` value(s) (may be space-separated list)
- Check if **any** cell name starts with approved prefixes: `INV`, `BUF`, `CKND`, `CKBD`, `CKBMVPMZ`, `CKNMVPMZ`, `DCCK`
- If **no** approved buffer found → **FAIL** with violation type `missing_buffer`
- If approved buffer found → proceed to Step 3

**Step 3: Validate Placement Status**
For ports with approved buffers:
- Extract `Port_connected_cell_pStatus` value(s) (may be space-separated list)
- Check if **all** status values are `fixed`
- If **any** status is not `fixed` → **FAIL** with violation type `unfixed_buffer`
- If **all** statuses are `fixed` → **PASS**

**Overall PASS Condition:**
- All ports (after filtering) have at least one approved buffer type **AND**
- All buffer cells are placed with `fixed` status

**Overall FAIL Conditions:**
- **FAIL Type 1 (missing_buffer):** Port has no approved buffer attached
- **FAIL Type 2 (unfixed_buffer):** Port has approved buffer but placement status is not `fixed`

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `status_check`

**Selected Mode for this checker:** `status_check`

**Rationale:** This checker validates the **status** of port buffer connectivity and placement. The `pattern_items` represent specific ports to check (when provided), and the checker reports whether each port's buffer attachment and placement status are correct. This is a status validation check, not an existence check - we're verifying that ports meet buffer and placement requirements, not just checking if certain items exist in the file.

---

## Output Descriptions (CRITICAL - Code Generator Uses These!)

This section defines the output strings used by `build_complete_output()` in the checker code.

```python
# ⚠️ CRITICAL: Description & Reason parameter usage by Type (API-026)
# Both DESC and REASON constants are split by Type for semantic clarity:
#   Type 1/4 (Boolean): Use DESC_TYPE1_4 & REASON_TYPE1_4 (emphasize "found/not found")
#   Type 2/3 (Pattern): Use DESC_TYPE2_3 & REASON_TYPE2_3 (emphasize "matched/satisfied")

# Item description for this checker
item_desc = "Confirm buffers are attached for all ports and are set as fixed."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "All ports have approved buffers attached and fixed"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "Port buffer requirements satisfied"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "All ports have approved buffer types (INV/BUF/CKND/CKBD/CKBMVPMZ/CKNMVPMZ/DCCK) attached and placement status is fixed"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Port has approved buffer attached and placement status is fixed"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Ports with missing or unfixed buffers found"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Port buffer requirements not satisfied"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Port buffer validation failed - missing approved buffer or unfixed placement"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Port drive not buffered with approved cell type or buffer placement not fixed"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Waived port buffer violations"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Port buffer requirement waived per design approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused port buffer waiver entries"
unused_waiver_reason = "Waiver entry not matched - no corresponding port buffer violation found"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [port_name]: [found_reason]"
  Example: "- clk4x: Port has approved buffer attached and placement status is fixed"

ERROR01 (Violation/Fail items):
  Format: "- [port_name]: [missing_reason]"
  Example: "- test_port: Port drive not buffered - connected cell 'cdns_ddr_se_txrx_h' does not start with approved prefix (INV/BUF/CKND/CKBD/CKBMVPMZ/CKNMVPMZ/DCCK)"
  Example: "- debug_clk: Port buffer not fixed - placement status is 'unfixed' (expected 'fixed')"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-04:
  description: "Confirm buffers are attached for all ports and are set as fixed."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-04\IMP-8-0-0-04.rpt
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs custom boolean validation - checks all ports (excluding bidi and 0x0) for approved buffer attachment and fixed placement status. PASS if all ports meet requirements, FAIL if any port has missing buffer or unfixed placement.

**Sample Output (PASS):**
```
Status: PASS
Reason: All ports have approved buffer types (INV/BUF/CKND/CKBD/CKBMVPMZ/CKNMVPMZ/DCCK) attached and placement status is fixed

Log format (CheckList.rpt):
INFO01:
  - clk4x
  - rst_n
  - scan_en

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: clk4x. In line 15, IMP-8-0-0-04.rpt: All ports have approved buffer types (INV/BUF/CKND/CKBD/CKBMVPMZ/CKNMVPMZ/DCCK) attached and placement status is fixed
2: Info: rst_n. In line 16, IMP-8-0-0-04.rpt: All ports have approved buffer types (INV/BUF/CKND/CKBD/CKBMVPMZ/CKNMVPMZ/DCCK) attached and placement status is fixed
3: Info: scan_en. In line 17, IMP-8-0-0-04.rpt: All ports have approved buffer types (INV/BUF/CKND/CKBD/CKBMVPMZ/CKNMVPMZ/DCCK) attached and placement status is fixed
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Port buffer validation failed - missing approved buffer or unfixed placement

Log format (CheckList.rpt):
ERROR01:
  - test_port
  - debug_clk

Report format (item_id.rpt):
Fail Occurrence: 2
1: Fail: test_port. In line 25, IMP-8-0-0-04.rpt: Port drive not buffered - connected cell 'cdns_ddr_se_txrx_h' does not start with approved prefix (INV/BUF/CKND/CKBD/CKBMVPMZ/CKNMVPMZ/DCCK)
2: Fail: debug_clk. In line 30, IMP-8-0-0-04.rpt: Port buffer not fixed - placement status is 'unfixed' (expected 'fixed')
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-04:
  description: "Confirm buffers are attached for all ports and are set as fixed."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-04\IMP-8-0-0-04.rpt
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Port buffer violations are informational only during early design stages"
      - "Note: Some test ports intentionally use non-standard buffers for debug purposes"
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

Log format (CheckList.rpt):
INFO01:
  - "Explanation: Port buffer violations are informational only during early design stages"
  - "Note: Some test ports intentionally use non-standard buffers for debug purposes"
INFO02:
  - test_port
  - debug_clk

Report format (item_id.rpt):
Info Occurrence: 4
1: Info: Explanation: Port buffer violations are informational only during early design stages. [WAIVED_INFO]
2: Info: Note: Some test ports intentionally use non-standard buffers for debug purposes. [WAIVED_INFO]
3: Info: test_port. In line 25, IMP-8-0-0-04.rpt: Port drive not buffered - connected cell 'cdns_ddr_se_txrx_h' does not start with approved prefix (INV/BUF/CKND/CKBD/CKBMVPMZ/CKNMVPMZ/DCCK) [WAIVED_AS_INFO]
4: Info: debug_clk. In line 30, IMP-8-0-0-04.rpt: Port buffer not fixed - placement status is 'unfixed' (expected 'fixed') [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-04:
  description: "Confirm buffers are attached for all ports and are set as fixed."
  requirements:
    value: 3
    pattern_items:
      - "clk4x"
      - "rst_n"
      - "scan_en"
  input_files:
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-04\IMP-8-0-0-04.rpt
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Description says "Confirm buffers are attached for all ports" → Use PORT NAMES
- Extract specific port names from the report that need buffer validation
- Pattern items are port identifiers to check (e.g., "clk4x", "rst_n", "scan_en")
- NOT buffer cell names or status values

**Check Behavior:**
Type 2 searches pattern_items (port names) in input files and validates their buffer attachment and placement status.
PASS if all pattern_items have approved buffers attached and fixed placement.
FAIL if any pattern_item has missing buffer or unfixed placement.

**Sample Output (PASS):**
```
Status: PASS
Reason: Port buffer requirements satisfied

Log format (CheckList.rpt):
INFO01:
  - clk4x
  - rst_n
  - scan_en

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: clk4x. In line 15, IMP-8-0-0-04.rpt: Port has approved buffer attached and placement status is fixed
2: Info: rst_n. In line 16, IMP-8-0-0-04.rpt: Port has approved buffer attached and placement status is fixed
3: Info: scan_en. In line 17, IMP-8-0-0-04.rpt: Port has approved buffer attached and placement status is fixed
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-04:
  description: "Confirm buffers are attached for all ports and are set as fixed."
  requirements:
    value: 3
    pattern_items:
      - "clk4x"
      - "rst_n"
      - "test_port"
  input_files:
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-04\IMP-8-0-0-04.rpt
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Port buffer check is informational during floorplan stage"
      - "Note: Test ports may use non-standard buffers for debug access"
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

Log format (CheckList.rpt):
INFO01:
  - "Explanation: Port buffer check is informational during floorplan stage"
  - "Note: Test ports may use non-standard buffers for debug access"
INFO02:
  - test_port

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: Explanation: Port buffer check is informational during floorplan stage. [WAIVED_INFO]
2: Info: Note: Test ports may use non-standard buffers for debug access. [WAIVED_INFO]
3: Info: test_port. In line 25, IMP-8-0-0-04.rpt: Port drive not buffered - connected cell 'cdns_ddr_se_txrx_h' does not start with approved prefix (INV/BUF/CKND/CKBD/CKBMVPMZ/CKNMVPMZ/DCCK) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-04:
  description: "Confirm buffers are attached for all ports and are set as fixed."
  requirements:
    value: 3
    pattern_items:
      - "clk4x"
      - "rst_n"
      - "scan_en"
  input_files:
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-04\IMP-8-0-0-04.rpt
  waivers:
    value: 2
    waive_items:
      - name: "test_port"
        reason: "Test port uses custom IO cell per design specification - approved by design team"
      - name: "debug_clk"
        reason: "Debug clock buffer intentionally unfixed for placement optimization - approved for non-critical path"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2 (validate port buffer requirements), plus waiver classification:
- Match found violations (ports with missing/unfixed buffers) against waive_items
- Unwaived violations → ERROR (need fix)
- Waived violations → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived

Log format (CheckList.rpt):
INFO01:
  - test_port
  - debug_clk
WARN01:
  - unused_port_waiver

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: test_port. In line 25, IMP-8-0-0-04.rpt: Port buffer requirement waived per design approval: Test port uses custom IO cell per design specification - approved by design team [WAIVER]
2: Info: debug_clk. In line 30, IMP-8-0-0-04.rpt: Port buffer requirement waived per design approval: Debug clock buffer intentionally unfixed for placement optimization - approved for non-critical path [WAIVER]
Warn Occurrence: 1
1: Warn: unused_port_waiver. In line [N], IMP-8-0-0-04.rpt: Waiver entry not matched - no corresponding port buffer violation found: [waiver reason] [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-04:
  description: "Confirm buffers are attached for all ports and are set as fixed."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-04\IMP-8-0-0-04.rpt
  waivers:
    value: 2
    waive_items:
      - name: "test_port"
        reason: "Test port uses custom IO cell per design specification - approved by design team"
      - name: "debug_clk"
        reason: "Debug clock buffer intentionally unfixed for placement optimization - approved for non-critical path"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (port names with violations)
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (validate all ports for buffer requirements), plus waiver classification:
- Match violations against waive_items
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output:**
```
Status: PASS
Reason: All items waived

Log format (CheckList.rpt):
INFO01:
  - test_port
  - debug_clk
WARN01:
  - unused_port_waiver

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: test_port. In line 25, IMP-8-0-0-04.rpt: Port buffer requirement waived per design approval: Test port uses custom IO cell per design specification - approved by design team [WAIVER]
2: Info: debug_clk. In line 30, IMP-8-0-0-04.rpt: Port buffer requirement waived per design approval: Debug clock buffer intentionally unfixed for placement optimization - approved for non-critical path [WAIVER]
Warn Occurrence: 1
1: Warn: unused_port_waiver. In line [N], IMP-8-0-0-04.rpt: Waiver entry not matched - no corresponding port buffer violation found: [waiver reason] [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 8.0_PHYSICAL_IMPLEMENTATION_CHECK --checkers IMP-8-0-0-04 --force

# Run individual tests
python IMP-8-0-0-04.py
```

---

## Notes

**Filtering Rules:**
- Bidirectional ports (`Direction: bidi`) are excluded from validation as they use different connectivity rules
- Ports with null connections (`Port_connected_cell_name: 0x0`) are excluded as they represent unconnected ports

**Approved Buffer Prefixes:**
The checker validates against these standard cell prefixes:
- `INV` - Inverters
- `BUF` - Buffers
- `CKND` - Clock NAND-based buffers
- `CKBD` - Clock buffer drivers
- `CKBMVPMZ` - Clock buffer with multi-VT PMVZ variant
- `CKNMVPMZ` - Clock NAND with multi-VT PMVZ variant
- `DCCK` - Dual-clock buffers

**Violation Types:**
- `missing_buffer`: Port has no buffer cell attached, or attached cell does not start with approved prefix
- `unfixed_buffer`: Port has approved buffer attached but placement status is not "fixed"

**Multi-Cell Handling:**
Some ports may have multiple cells attached (space-separated in `Port_connected_cell_name`). The checker validates:
- At least ONE cell must have an approved prefix (OR logic for buffer type)
- ALL cells must have "fixed" status (AND logic for placement)

**Known Limitations:**
- The checker assumes the input file format is consistent with the pattern shown in examples
- Cell name matching is prefix-based only (does not validate full cell library membership)
- Does not validate buffer drive strength or electrical characteristics