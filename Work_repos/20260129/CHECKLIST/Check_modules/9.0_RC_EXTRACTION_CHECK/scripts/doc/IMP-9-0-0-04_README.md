# IMP-9-0-0-04: Confirm no physically open nets in QRC imcomplete net report.

## Overview

**Check ID:** IMP-9-0-0-04  
**Description:** Confirm no physically open nets in QRC imcomplete net report.  
**Category:** RC Extraction Quality Check  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/*.incompletenets`

This checker validates the QRC (Quantus RC Extraction) incomplete nets report to ensure no physically open nets exist in the design. Incomplete nets can be categorized into two types:
1. **Acceptable**: Single-pin nets connected to physical wire (typically unused outputs or test points)
2. **Errors**: Physically open nets indicating routing failures or connectivity issues

The checker parses all `.incompletenets` files, classifies each incomplete net, and reports only physically open nets as errors while providing statistics on acceptable single-pin nets.

---

## Check Logic

### Input Parsing

The checker processes QRC incomplete nets reports with a state-machine approach, tracking net names and their connection status descriptions.

**Key Patterns:**
```python
# Pattern 1: Net name declaration line
pattern_net = r'^NET:\s+(.+)$'
# Example: "NET: inst_data_path_top/inst_data_byte_macro/inst_bit_macro_dqs/inst_x4_rddqs/inst_rddqs_input_macro/inst_rddqs_base_slv_dly_macro/inst_rddqs_base_slv_dly_update/UNCONNECTED331"

# Pattern 2: Single-pin physical wire connection (acceptable case)
pattern_acceptable = r'^-\s+only one pin\s*:\s*(\w+)\s+is connected to a physical wire\s*$'
# Example: "- only one pin : COX is connected to a physical wire "

# Pattern 3: Other incomplete net reasons (potential errors)
pattern_reason = r'^-\s+(.+)$'
# Example: "- net has no physical connections"

# Pattern 4: UNCONNECTED net naming pattern (often intentional)
pattern_unconnected = r'/UNCONNECTED\d+$'
# Example: "/UNCONNECTED331"
```

### Detection Logic

1. **Line-by-line parsing with state tracking**:
   - When `NET:` line encountered → store net name in `current_net`
   - When `-` line encountered → store reason in `current_reason`
   - Process (net, reason) pair before moving to next NET

2. **Classification logic**:
   - If reason matches "only one pin : [PIN] is connected to a physical wire" → classify as ACCEPTABLE
   - Otherwise → classify as PHYSICALLY_OPEN (error)

3. **Aggregation across files**:
   - Sum total incomplete nets from all corner reports
   - Collect all physically open nets (errors)
   - Count acceptable single-pin nets

4. **Pass/Fail determination**:
   - **PASS**: No physically open nets found (only acceptable single-pin nets)
   - **FAIL**: One or more physically open nets detected

5. **Edge cases**:
   - Empty file → Report 0 incomplete nets, PASS
   - Missing reason line after NET → Flag as malformed error
   - Multiple reason lines per net → Take first reason only
   - File with only acceptable single-pin nets → PASS with INFO statistics

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

**Rationale:** This checker validates the status of incomplete nets found in QRC reports. It examines all incomplete nets and classifies them by connection status (acceptable single-pin vs. physically open). Only physically open nets (wrong status) are reported as errors, while acceptable single-pin nets are shown as INFO. This is a status validation check, not an existence check.

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
item_desc = "Confirm no physically open nets in QRC imcomplete net report."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "No physically open nets found in QRC extraction reports"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All incomplete nets are acceptable single-pin connections"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "No physically open nets found - all incomplete nets are acceptable single-pin connections to physical wire"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All incomplete nets matched acceptable pattern (single-pin connected to physical wire) - no physically open nets detected"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Physically open nets detected in QRC extraction"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Incomplete nets with unacceptable connection status found"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Physically open nets found - routing connectivity failures detected in QRC extraction"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Incomplete nets do not satisfy acceptable connection pattern - physically open nets require routing fixes"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Physically open nets waived per design approval"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Physically open net waived - approved by design team as intentional or non-critical"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries for physically open nets"
unused_waiver_reason = "Waiver not matched - no corresponding physically open net found in QRC reports"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "Total incomplete nets: {count} ({single_pin_count} acceptable single-pin, {open_count} physically open)"
  Example: "Total incomplete nets: 245 (245 acceptable single-pin, 0 physically open)"

ERROR01 (Violation/Fail items):
  Format: "Physically open net: {net_name} - {reason}"
  Example: "Physically open net: inst_data_path_top/inst_data_byte_macro/FE_OFN11025_param_phy_rdlvl_rd4_mux_control_2 - net has no physical connections"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-9-0-0-04:
  description: "Confirm no physically open nets in QRC imcomplete net report."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/*.incompletenets"
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
Reason: No physically open nets found - all incomplete nets are acceptable single-pin connections to physical wire
INFO01:
  - Total incomplete nets: 245 (245 acceptable single-pin, 0 physically open)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Physically open nets found - routing connectivity failures detected in QRC extraction
ERROR01:
  - Physically open net: inst_data_path_top/inst_data_byte_macro/FE_OFN11025_param_phy_rdlvl_rd4_mux_control_2 - net has no physical connections
  - Physically open net: inst_data_path_top/inst_control_macro/debug_signal_unrouted - only one pin but not connected to physical wire
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-9-0-0-04:
  description: "Confirm no physically open nets in QRC imcomplete net report."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/*.incompletenets"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Physically open nets are informational only during early design stages"
      - "Note: Open nets on debug signals are expected and will be fixed in final tapeout"
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
  - "Explanation: Physically open nets are informational only during early design stages"
  - "Note: Open nets on debug signals are expected and will be fixed in final tapeout"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - Physically open net: inst_data_path_top/inst_data_byte_macro/FE_OFN11025_param_phy_rdlvl_rd4_mux_control_2 - net has no physical connections [WAIVED_AS_INFO]
  - Physically open net: inst_data_path_top/inst_control_macro/debug_signal_unrouted - only one pin but not connected to physical wire [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-9-0-0-04:
  description: "Confirm no physically open nets in QRC imcomplete net report."
  requirements:
    value: 2
    pattern_items:
      - "inst_data_path_top/inst_data_byte_macro/FE_OFN11025_param_phy_rdlvl_rd4_mux_control_2"
      - "inst_data_path_top/inst_control_macro/debug_signal_unrouted"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/*.incompletenets"
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
Reason: All incomplete nets matched acceptable pattern (single-pin connected to physical wire) - no physically open nets detected
INFO01:
  - Total incomplete nets: 245 (245 acceptable single-pin, 0 physically open)
  - Pattern check: 0/2 physically open nets found
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-9-0-0-04:
  description: "Confirm no physically open nets in QRC imcomplete net report."
  requirements:
    value: 2
    pattern_items:
      - "inst_data_path_top/inst_data_byte_macro/FE_OFN11025_param_phy_rdlvl_rd4_mux_control_2"
      - "inst_data_path_top/inst_control_macro/debug_signal_unrouted"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/*.incompletenets"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: These specific nets are informational only - known debug signals"
      - "Note: Pattern mismatches on debug nets are expected and do not require fixes"
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
  - "Explanation: These specific nets are informational only - known debug signals"
  - "Note: Pattern mismatches on debug nets are expected and do not require fixes"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - Physically open net: inst_data_path_top/inst_data_byte_macro/FE_OFN11025_param_phy_rdlvl_rd4_mux_control_2 - net has no physical connections [WAIVED_AS_INFO]
  - Physically open net: inst_data_path_top/inst_control_macro/debug_signal_unrouted - only one pin but not connected to physical wire [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-9-0-0-04:
  description: "Confirm no physically open nets in QRC imcomplete net report."
  requirements:
    value: 2
    pattern_items:
      - "inst_data_path_top/inst_data_byte_macro/FE_OFN11025_param_phy_rdlvl_rd4_mux_control_2"
      - "inst_data_path_top/inst_control_macro/debug_signal_unrouted"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/*.incompletenets"
  waivers:
    value: 2
    waive_items:
      - name: "inst_data_path_top/inst_data_byte_macro/FE_OFN11025_param_phy_rdlvl_rd4_mux_control_2"
        reason: "Waived - debug signal intentionally left unconnected per design review"
      - name: "inst_data_path_top/inst_control_macro/debug_signal_unrouted"
        reason: "Waived - test point for probe access, no functional impact"
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
  - Physically open net: inst_data_path_top/inst_data_byte_macro/FE_OFN11025_param_phy_rdlvl_rd4_mux_control_2 - net has no physical connections [WAIVER]
  - Physically open net: inst_data_path_top/inst_control_macro/debug_signal_unrouted - only one pin but not connected to physical wire [WAIVER]
WARN01 (Unused Waivers):
  - (none - all waivers matched)
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-9-0-0-04:
  description: "Confirm no physically open nets in QRC imcomplete net report."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/*.incompletenets"
  waivers:
    value: 2
    waive_items:
      - name: "inst_data_path_top/inst_data_byte_macro/FE_OFN11025_param_phy_rdlvl_rd4_mux_control_2"
        reason: "Waived - debug signal intentionally left unconnected per design review"
      - name: "inst_data_path_top/inst_control_macro/debug_signal_unrouted"
        reason: "Waived - test point for probe access, no functional impact"
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
  - Physically open net: inst_data_path_top/inst_data_byte_macro/FE_OFN11025_param_phy_rdlvl_rd4_mux_control_2 - net has no physical connections [WAIVER]
  - Physically open net: inst_data_path_top/inst_control_macro/debug_signal_unrouted - only one pin but not connected to physical wire [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 9.0_RC_EXTRACTION_CHECK --checkers IMP-9-0-0-04 --force

# Run individual tests
python IMP-9-0-0-04.py
```

---

## Notes

- **Acceptable incomplete nets**: Single-pin nets connected to physical wire are common and expected (unused cell outputs, test points, tie-off cells). These are reported in INFO01 for tracking but do not cause check failure.

- **Physically open nets**: Nets with no physical connections or incomplete routing indicate design errors and must be fixed. These trigger ERROR01 and check failure.

- **UNCONNECTED naming pattern**: Nets with names ending in `/UNCONNECTED###` are often intentionally unconnected (synthesis artifacts). The checker still validates their connection status - if they're single-pin connected to physical wire, they're acceptable.

- **Multi-file aggregation**: The checker processes all `.incompletenets` files from different extraction corners and aggregates results. A net appearing in multiple corners is counted once.

- **State machine parsing**: The parser maintains state to associate each net name with its connection status description. Malformed files (missing reason lines) are flagged as errors.

- **Performance**: For designs with thousands of incomplete nets, the checker efficiently filters acceptable cases and reports only actionable errors.