# IMP-8-0-0-06: Confirm the switch power pin is not in lef . (for non-PSO, please fill N/A)

## Overview

**Check ID:** IMP-8-0-0-06**Description:** Confirm the switch power pin is not in lef . (for non-PSO, please fill N/A)**Category:** Physical Implementation - Power Switch Pin Validation**Input Files:**

- `${CHECKLIST_ROOT}\IP_project_folder\logs\8.0\do_innovusOUTwoD.logv2` (Innovus implementation log)
- `${CHECKLIST_ROOT}\IP_project_folder\reports\8.0\switch_power_layer.rpt` (Switch power layer report)

This checker validates that power switch pins are not written into LEF abstract files for PSO (Power Shut-Off) designs. For PSO designs, switch power pins should remain internal to the design and not be exposed in the LEF interface. The checker compares the PG pin layers specified in the `write_lef_abstract` command against the actual switch power layers reported in the design. For non-PSO designs, the result should be "N/A".

---

## Check Logic

### Input Parsing

**Step 1: Extract LEF PG Pin Layers from Innovus Log**
Search the Innovus log file for the `write_lef_abstract` command with pattern `write_lef_abstract.*OUTwoD.lef`. Extract the metal layer numbers specified after the `-PGpinLayers` option. Store into `lef_pg`.

**CRITICAL: Immediately append ONE dictionary to items when pattern matches**

When `pattern1` matches, **immediately** append the following dictionary to `items` list:

```python
items.append({
    'name': f"LEF_PG_Layers: {' '.join(lef_pg_layers)}",  # Format: "LEF_PG_Layers: 1 2 3"
    'line_number': line_num,  # Line number where pattern matched
    'file_path': str(file_path),  # Full path to Innovus log file
    'lef_pg': lef_pg_layers,  # List of layer numbers
    'type': 'lef_pg'  # Item type identifier
})
```

**Key Patterns:**

```python
# Pattern 1: Extract PG pin layers from write_lef_abstract command
pattern1 = r'write_lef_abstract.*OUTwoD\.lef.*-PGpinLayers\s+\{([^}]+)\}'
# Example: "write_lef_abstract -extractBlockObs dbs/gddr36_ew_cdn_ghs_phy_top.OUTwoD.lef -noCutObs -specifyTopLayer 19 -stripePin -PGpinLayers 19"
# Extracts: "19" → Store as lef_pg list
```

**Step 2: Extract Design Hierarchy from Switch Power Report**
Search the switch power layer report for the `Design Hierarchy:`. Extract the hier name and store into `design_hier`.

**CRITICAL: Immediately append ONE dictionary to items when pattern matches**

When `pattern2` matches, **immediately** append the following dictionary to `items` list:

```python
items.append({
    'name': f"Design_Hierarchy: {design_hier}",  # Format: "Design_Hierarchy: gddr36_ew_cdn_ghs_phy_top"
    'line_number': line_num,  # Line number where pattern matched
    'file_path': str(file_path),  # Full path to switch power report
    'design_hier': design_hier,  # Design hierarchy name
    'type': 'design_hierarchy'  # Item type identifier
})
```

```python
# Pattern 2: Extract design hierarchy
pattern2 = r'^Design Hierarchy:\s*(.+?)\s*$'
# Example: "Design Hierarchy: gddr36_ew_cdn_ghs_phy_top"
# Extracts: "gddr36_ew_cdn_ghs_phy_top" → Store as design_hier
```

**Step 3: Extract Switch Power Net Name**
Search the switch power layer report for the `Switch Power:`. Extract the switch power name and store into  `switch_pg`.

**CRITICAL: Immediately append ONE dictionary to items when pattern matches**

When `pattern3` matches, **immediately** append the following dictionary to `items` list:

```python
items.append({
    'name': f"Switch_Power_Net: {switch_pg}",  # Format: "Switch_Power_Net: VDDG"
    'line_number': line_num,  # Line number where pattern matched
    'file_path': str(file_path),  # Full path to switch power report
    'switch_pg': switch_pg,  # Switch power net name
    'type': 'switch_power_net'  # Item type identifier
})
```

```python
# Pattern 3: Extract switch power net
pattern3 = r'^Switch Power:\s*(.+?)\s*$'
# Example: "Switch Power: VDDG"
# Extracts: "VDDG" → Store as switch_pg
```

**Step 4: Extract Switch Power Layers**
Search the switch power layer report for the `Switch Power Layer:`. Extract the switch power layer list and store into  `switch_pg_layer`.

**CRITICAL: Immediately append ONE dictionary to items when pattern matches**

When `pattern4` matches, **immediately** append the following dictionary to `items` list:

```python
items.append({
    'name': f"Switch_Power_Layers: {' '.join(switch_pg_layer)}",  # Format: "Switch_Power_Layers: 1 2 3 4..."
    'line_number': line_num,  # Line number where pattern matched
    'file_path': str(file_path),  # Full path to switch power report
    'switch_pg_layer': switch_pg_layer,  # List of layer numbers
    'type': 'switch_power_layers'  # Item type identifier
})
```

```python
# Pattern 4: Extract switch power layers (ignore comments after #)
pattern4 = r'^Switch Power Layer:\s*(.+?)(?:\s*#.*)?$'
# Example: "Switch Power Layer: 1 10 11 12 13 14 15 16 17 18 2 3 4 5 6 7 8 9  # Limit to 10KB"
# Extracts: "1 10 11 12 13 14 15 16 17 18 2 3 4 5 6 7 8 9" → Store as switch_pg_layer list
```

**Expected items list structure after parsing:**

After parsing both input files, the `items` list should contain **exactly 4 dictionaries** (assuming all patterns match):

1. `items[0]`: LEF PG layers information (from Innovus log)
2. `items[1]`: Design hierarchy information (from switch power report)
3. `items[2]`: Switch power net information (from switch power report)
4. `items[3]`: Switch power layers information (from switch power report)

**Example items list:**

```python
items = [
    {
        'name': 'LEF_PG_Layers: 19',
        'line_number': 45,
        'file_path': '...\\do_innovusOUTwoD.logv2',
        'lef_pg': ['19'],
        'type': 'lef_pg'
    },
    {
        'name': 'Design_Hierarchy: gddr36_ew_cdn_ghs_phy_top',
        'line_number': 12,
        'file_path': '...\\switch_power_layer.rpt',
        'design_hier': 'gddr36_ew_cdn_ghs_phy_top',
        'type': 'design_hierarchy'
    },
    {
        'name': 'Switch_Power_Net: VDDG',
        'line_number': 15,
        'file_path': '...\\switch_power_layer.rpt',
        'switch_pg': 'VDDG',
        'type': 'switch_power_net'
    },
    {
        'name': 'Switch_Power_Layers: 1 2 3 4 5 6 7 8 9 10',
        'line_number': 18,
        'file_path': '...\\switch_power_layer.rpt',
        'switch_pg_layer': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
        'type': 'switch_power_layers'
    }
]
```

### Detection Logic

**Type 1/4 (No pattern_items):**

- Compare: Check if ANY layer number from `lef_pg` exists in `switch_pg_layer`
- **PASS**: If all `lef_pg` layers do NOT exist in `switch_pg_layer` (no overlap)
- **FAIL**: If one or more `lef_pg` layers exist in `switch_pg_layer` (overlap detected)

**Type 2/3 (With pattern_items - design hierarchy filtering):**

- Compare `design_hier` against `pattern_items` (top_hier)
- **If `design_hier` != `top_hier`**: Force PASS (sub-block level, check not applicable)
- **If `design_hier` == `top_hier`**: Apply same logic as Type 1/4
  - **PASS**: If all `lef_pg` layers do NOT exist in `switch_pg_layer`
  - **FAIL**: If one or more `lef_pg` layers exist in `switch_pg_layer`

**Edge Cases:**

- Non-PSO design: Switch power report contains "N/A" or is empty → Return N/A
- Missing Innovus log: Cannot extract `lef_pg` → Return ERROR
- Missing switch power report: Assume non-PSO → Return N/A
- Empty `lef_pg` list: No PG pins specified → Return PASS
- Empty `switch_pg_layer` list: No switch power layers → Return PASS

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

**Rationale:** The pattern_items represent design hierarchy names to filter which designs should be checked at the top level. The checker validates the STATUS of switch power pin exposure (whether pins are written to LEF or not) for designs matching the pattern. Only designs matching pattern_items are evaluated; other designs are forced to PASS (sub-block level). This is a status validation check, not an existence check.

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
item_desc = "Confirm the switch power pin is not in lef . (for non-PSO, please fill N/A)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "Power Switch Pin would not write out into LEF"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "Power Switch Pin would not write out into LEF (TOP level) OR SUB-BLOCK level"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "No overlap detected between LEF PG pin layers and switch power layers"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Design hierarchy matched and validated: No overlap between LEF PG pin layers and switch power layers, OR design is at sub-block level"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Power Switch Pin would write out into LEF"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Power Switch Pin would write out into LEF (TOP level)"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Overlap detected: LEF PG pin layers contain switch power layers"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Design hierarchy matched but validation failed: LEF PG pin layers contain switch power layers"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Switch power pin in LEF waived for this design hierarchy"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "At this design hierarchy level, switch power pin in LEF can be accepted"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries for design hierarchy"
unused_waiver_reason = "Waiver not matched - no corresponding design hierarchy found or design passed validation"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "Design: [design_hier] | Switch Power: [switch_pg] | LEF PG Layers: [lef_pg] | Switch Layers: [switch_pg_layer] | Status: No Overlap"
  Example: "Design: gddr36_ew_cdn_ghs_phy_top | Switch Power: VDDG | LEF PG Layers: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] | Switch Layers: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18] | Status: No Overlap"

ERROR01 (Violation/Fail items):
  Format: "Design: [design_hier] | Switch Power: [switch_pg] | LEF PG Layers: [lef_pg] | Switch Layers: [switch_pg_layer] | Overlap: [overlapping_layers]"
  Example: "Design: gddr36_ew_cdn_ghs_phy_top | Switch Power: VDDG | LEF PG Layers: [1, 2, 3, 4, 5] | Switch Layers: [1, 2, 3, 4, 5, 6, 7, 8] | Overlap: [1, 2, 3, 4, 5]"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-8-0-0-06:
  description: "Confirm the switch power pin is not in lef . (for non-PSO, please fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\8.0\\do_innovusOUTwoD.logv2"
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\8.0\\switch_power_layer.rpt"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs boolean validation without design hierarchy filtering. It checks all designs regardless of hierarchy level. The checker extracts LEF PG pin layers from the Innovus log and switch power layers from the report, then validates that there is no overlap between these two sets of layers.

**Sample Output (PASS):**

```
Status: PASS
Reason: No overlap detected between LEF PG pin layers and switch power layers
INFO01:
  - Design: gddr36_ew_cdn_ghs_phy_top | Switch Power: VDDG | LEF PG Layers: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] | Switch Layers: [11, 12, 13, 14, 15, 16, 17, 18] | Status: No Overlap
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: Overlap detected: LEF PG pin layers contain switch power layers
ERROR01:
  - Design: gddr36_ew_cdn_ghs_phy_top | Switch Power: VDDG | LEF PG Layers: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] | Switch Layers: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18] | Overlap: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-8-0-0-06:
  description: "Confirm the switch power pin is not in lef . (for non-PSO, please fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\8.0\\do_innovusOUTwoD.logv2"
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\8.0\\switch_power_layer.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only for early design stages where switch power pin exposure in LEF is acceptable"
      - "Note: Violations are expected during block-level integration and do not require immediate fixes"
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
  - "Explanation: This check is informational only for early design stages where switch power pin exposure in LEF is acceptable"
  - "Note: Violations are expected during block-level integration and do not require immediate fixes"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - Design: gddr36_ew_cdn_ghs_phy_top | Switch Power: VDDG | LEF PG Layers: [1, 2, 3, 4, 5] | Switch Layers: [1, 2, 3, 4, 5, 6, 7, 8] | Overlap: [1, 2, 3, 4, 5] [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-8-0-0-06:
  description: "Confirm the switch power pin is not in lef . (for non-PSO, please fill N/A)"
  requirements:
    value: 1
    pattern_items:
      - "gddr36_ew_cdn_ghs_phy_top"  # Top-level design hierarchy name to check
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\8.0\\do_innovusOUTwoD.logv2"
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\8.0\\switch_power_layer.rpt"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:

- pattern_items contains design hierarchy names (top-level design identifiers)
- These are used to filter which designs should be checked at the top level
- If design_hier matches pattern_items: Apply full validation logic
- If design_hier does NOT match pattern_items: Force PASS (sub-block level)

**Check Behavior:**
Type 2 searches for design hierarchy in the switch power report and compares against pattern_items. Only designs matching pattern_items are validated for switch power pin exposure. Designs not matching pattern_items are automatically passed (sub-block level check not applicable).

**Sample Output (PASS - Top level, no overlap):**

```
Status: PASS
Reason: Design hierarchy matched and validated: No overlap between LEF PG pin layers and switch power layers, OR design is at sub-block level
INFO01:
  - Design: gddr36_ew_cdn_ghs_phy_top | Switch Power: VDDG | LEF PG Layers: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] | Switch Layers: [11, 12, 13, 14, 15, 16, 17, 18] | Status: No Overlap (TOP level)
```

**Sample Output (PASS - Sub-block level, forced pass):**

```
Status: PASS
Reason: Design hierarchy matched and validated: No overlap between LEF PG pin layers and switch power layers, OR design is at sub-block level
INFO01:
  - Design: sub_block_module | Switch Power: VDDG | LEF PG Layers: [1, 2, 3, 4, 5] | Switch Layers: [1, 2, 3, 4, 5, 6, 7, 8] | Status: SUB-BLOCK level (check not applicable)
```

**Sample Output (FAIL - Top level, overlap detected):**

```
Status: FAIL
Reason: Design hierarchy matched but validation failed: LEF PG pin layers contain switch power layers
ERROR01:
  - Design: gddr36_ew_cdn_ghs_phy_top | Switch Power: VDDG | LEF PG Layers: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] | Switch Layers: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18] | Overlap: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] (TOP level)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-8-0-0-06:
  description: "Confirm the switch power pin is not in lef . (for non-PSO, please fill N/A)"
  requirements:
    value: 1
    pattern_items:
      - "gddr36_ew_cdn_ghs_phy_top"
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\8.0\\do_innovusOUTwoD.logv2"
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\8.0\\switch_power_layer.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only for top-level designs during early integration phases"
      - "Note: Pattern mismatches are expected when switch power pins are intentionally exposed in LEF for hierarchical power planning"
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
  - "Explanation: This check is informational only for top-level designs during early integration phases"
  - "Note: Pattern mismatches are expected when switch power pins are intentionally exposed in LEF for hierarchical power planning"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - Design: gddr36_ew_cdn_ghs_phy_top | Switch Power: VDDG | LEF PG Layers: [1, 2, 3, 4, 5] | Switch Layers: [1, 2, 3, 4, 5, 6, 7, 8] | Overlap: [1, 2, 3, 4, 5] (TOP level) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-8-0-0-06:
  description: "Confirm the switch power pin is not in lef . (for non-PSO, please fill N/A)"
  requirements:
    value: 1
    pattern_items:
      - "gddr36_ew_cdn_ghs_phy_top"  # Top-level design hierarchy name to check
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\8.0\\do_innovusOUTwoD.logv2"
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\8.0\\switch_power_layer.rpt"
  waivers:
    value: 1
    waive_items:
      - name: "gddr36_ew_cdn_ghs_phy_top"  # Design hierarchy name matching pattern_items
        reason: "At this design hierarchy level, switch power pin in LEF can be accepted."
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:

- BOTH must be at SAME semantic level as description!
- pattern_items contains design hierarchy names (e.g., "gddr36_ew_cdn_ghs_phy_top")
- waive_items.name MUST use the SAME design hierarchy names
- This ensures consistent matching between requirements and waivers

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2 (design hierarchy filtering), plus waiver classification:

- Match violations (designs with overlap) against waive_items
- Unwaived violations → ERROR (need fix)
- Waived violations → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
  PASS if all violations are waived.

**Sample Output (PASS - All violations waived):**

```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - Design: gddr36_ew_cdn_ghs_phy_top | Switch Power: VDDG | LEF PG Layers: [1, 2, 3, 4, 5] | Switch Layers: [1, 2, 3, 4, 5, 6, 7, 8] | Overlap: [1, 2, 3, 4, 5] [WAIVER]
```

**Sample Output (FAIL - Unwaived violations):**

```
Status: FAIL
Reason: Design hierarchy matched but validation failed: LEF PG pin layers contain switch power layers
ERROR01:
  - Design: gddr36_ew_cdn_ghs_phy_top | Switch Power: VDDG | LEF PG Layers: [1, 2, 3, 4, 5] | Switch Layers: [1, 2, 3, 4, 5, 6, 7, 8] | Overlap: [1, 2, 3, 4, 5] (TOP level)
```

**Sample Output (PASS with unused waivers):**

```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - Design: gddr36_ew_cdn_ghs_phy_top | Switch Power: VDDG | LEF PG Layers: [1, 2, 3, 4, 5] | Switch Layers: [1, 2, 3, 4, 5, 6, 7, 8] | Overlap: [1, 2, 3, 4, 5] [WAIVER]
WARN01 (Unused Waivers):
  - another_design_module: Waiver not matched - no corresponding design hierarchy found or design passed validation
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-8-0-0-06:
  description: "Confirm the switch power pin is not in lef . (for non-PSO, please fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\8.0\\do_innovusOUTwoD.logv2"
    - "${CHECKLIST_ROOT}\\IP_project_folder\\reports\\8.0\\switch_power_layer.rpt"
  waivers:
    value: 1
    waive_items:
      - name: "gddr36_ew_cdn_ghs_phy_top"  # SAME as Type 3 waive_items.name
        reason: "At this design hierarchy level, switch power pin in LEF can be accepted."  # SAME as Type 3 reason
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!

- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (no design hierarchy filtering), plus waiver classification:

- Match violations against waive_items (by design hierarchy name)
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
  PASS if all violations are waived.

**Sample Output (PASS - All violations waived):**

```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - Design: gddr36_ew_cdn_ghs_phy_top | Switch Power: VDDG | LEF PG Layers: [1, 2, 3, 4, 5] | Switch Layers: [1, 2, 3, 4, 5, 6, 7, 8] | Overlap: [1, 2, 3, 4, 5] [WAIVER]
```

**Sample Output (FAIL - Unwaived violations):**

```
Status: FAIL
Reason: Overlap detected: LEF PG pin layers contain switch power layers
ERROR01:
  - Design: gddr36_ew_cdn_ghs_phy_top | Switch Power: VDDG | LEF PG Layers: [1, 2, 3, 4, 5] | Switch Layers: [1, 2, 3, 4, 5, 6, 7, 8] | Overlap: [1, 2, 3, 4, 5]
```

**Sample Output (PASS with unused waivers):**

```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - Design: gddr36_ew_cdn_ghs_phy_top | Switch Power: VDDG | LEF PG Layers: [1, 2, 3, 4, 5] | Switch Layers: [1, 2, 3, 4, 5, 6, 7, 8] | Overlap: [1, 2, 3, 4, 5] [WAIVER]
WARN01 (Unused Waivers):
  - another_design_module: Waiver not matched - no corresponding design hierarchy found or design passed validation
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 8.0_PHYSICAL_IMPLEMENTATION_CHECK --checkers IMP-8-0-0-06 --force

# Run individual tests
python IMP-8-0-0-06.py
```

---

## Notes

**PSO Design Detection:**

- For non-PSO designs, the switch power layer report should contain "N/A" or be empty
- The checker should return "N/A" status for non-PSO designs
- PSO designs will have populated switch power layer information

**Layer Number Parsing:**

- Layer numbers are extracted as integers from space-separated lists
- Comments after "#" in the switch power layer report are ignored
- Layer numbers may not be in sequential order (e.g., "1 10 11 12 2 3 4 5")

**Design Hierarchy Filtering (Type 2/3):**

- Type 2/3 use pattern_items to filter top-level designs
- If design_hier does not match pattern_items, the check is forced to PASS (sub-block level)
- This allows different validation rules for top-level vs. sub-block designs

**Waiver Matching (Type 3/4):**

- Waivers are matched by design hierarchy name
- A waived design with overlap will show in INFO01 with [WAIVER] tag
- Unused waivers (no matching design or design passed) show in WARN01

**Known Limitations:**

- Checker assumes single design per switch power report
- Multiple switch power nets in one design are not explicitly handled (uses first match)
- Relative paths in Innovus log are not resolved (assumes absolute paths or same directory)
