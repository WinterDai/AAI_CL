# IMP-8-0-0-03: Confirm routing blockages are created around the block edges.

## Overview

**Check ID:** IMP-8-0-0-03  
**Description:** Confirm routing blockages are created around the block edges.  
**Category:** Physical Implementation Verification  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-03.rpt`

This checker validates that routing blockages are properly placed around all four edges (left, right, top, bottom) of the die boundary. It parses the die box coordinates and routing blockage definitions to ensure complete edge coverage on all metal layers. Missing or misaligned edge blockages can lead to routing violations and DRC errors at the chip boundary.

---

## Check Logic

### Input Parsing
The checker parses a routing blockage report containing:
1. **Die box definition**: Extracts boundary coordinates `{llx lly urx ury}`
2. **Routing blockages**: Extracts layer name and box coordinates for each blockage
3. **Edge classification**: Determines which edge (left/right/top/bottom) each blockage covers based on proximity to die boundaries

**Key Patterns:**
```python
# Pattern 1: Die box definition
die_box_pattern = r'Block die boxes:\s*\{\{([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\}\}'
# Example: "Block die boxes: {{0.0 0.0 752.0 535.8}}"

# Pattern 2: Routing blockage with layer and coordinates
blockage_pattern = r'Routing Blockage:\s*Layer\s+(M\d+);\s*Box\s*\{\{([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\}\}'
# Example: "Routing Blockage: Layer M15; Box {{751.7 0.0 752.0 535.8}}"

# Pattern 3: Left edge blockage (llx near 0.0)
left_edge_pattern = r'Routing Blockage:\s*Layer\s+(M\d+);\s*Box\s*\{\{(0\.0|0\.\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\}\}'
# Example: "Routing Blockage: Layer M15; Box {{0.0 0.0 0.3 535.8}}"

# Pattern 4: Right edge blockage (urx near die max)
right_edge_pattern = r'Routing Blockage:\s*Layer\s+(M\d+);\s*Box\s*\{\{([\d.]+)\s+([\d.]+)\s+(75[12]\.\d+)\s+([\d.]+)\}\}'
# Example: "Routing Blockage: Layer M15; Box {{751.7 0.0 752.0 535.8}}"

# Pattern 5: Top/Bottom edge blockage (horizontal strips)
horiz_edge_pattern = r'Routing Blockage:\s*Layer\s+(M\d+);\s*Box\s*\{\{([\d.]+)\s+(0\.0|0\.\d+|53[45]\.\d+)\s+([\d.]+)\s+([\d.]+)\}\}'
# Example: "Routing Blockage: Layer M15; Box {{0.3 0.0 751.7 0.3}}"
```

### Detection Logic
1. **Extract die box**: Parse die boundary coordinates (llx, lly, urx, ury) from the report
2. **Extract all blockages**: Collect all routing blockage definitions with layer and coordinates
3. **Classify by edge**: For each blockage, determine edge proximity using tolerance (±0.5 units):
   - Left edge: `blockage.llx <= die.llx + 0.5`
   - Right edge: `blockage.urx >= die.urx - 0.5`
   - Bottom edge: `blockage.lly <= die.lly + 0.5`
   - Top edge: `blockage.ury >= die.ury - 0.5`
4. **Group by layer**: Count blockages per metal layer
5. **Validate coverage**: Check that all four edges have blockages on expected layers
6. **Report results**:
   - **PASS**: All edges have proper blockage coverage
   - **FAIL**: Missing edge blockages or blockages not aligned to die edges

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
item_desc = "Confirm routing blockages are created around the block edges."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "All edge routing blockages found and properly aligned to die boundaries"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All required edge blockage patterns matched and validated"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "All four edges (left, right, top, bottom) have routing blockages on all metal layers"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All edge blockage patterns matched: left/right/top/bottom edges validated on all layers"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Edge routing blockages not found or misaligned"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Required edge blockage patterns not satisfied"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Missing edge blockages or blockages not aligned to die boundaries"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Edge blockage patterns not satisfied: missing coverage on one or more edges"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Edge blockage violations waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Edge blockage violation waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused edge blockage waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding edge blockage violation found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "Layer <layer_name>: <count> blockages | Edge: <edge_type> (<count> blockages)"
  Example: "Layer M15: 4 blockages | Edge: left (1), right (1), top (1), bottom (1)"
  Example: "Die box: {{0.0 0.0 752.0 535.8}} | Total blockages: 16 (4 layers × 4 edges)"

ERROR01 (Violation/Fail items):
  Format: "ERROR: <edge_name> edge missing blockages on layer <layer> | Blockage at (<coords>) not aligned to die edge"
  Example: "ERROR: Left edge missing blockages on layer M12"
  Example: "ERROR: Blockage at (10.5, 0.0, 15.0, 535.8) not aligned to any die edge (tolerance=0.5)"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-03:
  description: "Confirm routing blockages are created around the block edges."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-03.rpt"
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
Reason: All four edges (left, right, top, bottom) have routing blockages on all metal layers
INFO01:
  - Die box: {{0.0 0.0 752.0 535.8}} | Total blockages: 16 (4 layers × 4 edges)
  - Layer M15: 4 blockages | Edge: left (1), right (1), top (1), bottom (1)
  - Layer M14: 4 blockages | Edge: left (1), right (1), top (1), bottom (1)
  - Layer M13: 4 blockages | Edge: left (1), right (1), top (1), bottom (1)
  - Layer M12: 4 blockages | Edge: left (1), right (1), top (1), bottom (1)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Missing edge blockages or blockages not aligned to die boundaries
ERROR01:
  - ERROR: Left edge missing blockages on layer M12
  - ERROR: Top edge missing blockages on layer M13
  - ERROR: Blockage at (10.5, 0.0, 15.0, 535.8) not aligned to any die edge (tolerance=0.5)
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-03:
  description: "Confirm routing blockages are created around the block edges."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-03.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Edge blockages are informational only for this design stage"
      - "Note: Missing blockages on lower metal layers are expected during floorplan phase"
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
  - "Explanation: Edge blockages are informational only for this design stage"
  - "Note: Missing blockages on lower metal layers are expected during floorplan phase"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - ERROR: Left edge missing blockages on layer M12 [WAIVED_AS_INFO]
  - ERROR: Top edge missing blockages on layer M13 [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-03:
  description: "Confirm routing blockages are created around the block edges."
  requirements:
    value: 4
    pattern_items:
      - "Layer M15; Box {{0.0 0.0 0.3 535.8}}"
      - "Layer M15; Box {{751.7 0.0 752.0 535.8}}"
      - "Layer M15; Box {{0.3 0.0 751.7 0.3}}"
      - "Layer M15; Box {{0.3 535.5 751.7 535.8}}"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-03.rpt"
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
Reason: All edge blockage patterns matched: left/right/top/bottom edges validated on all layers
INFO01:
  - Layer M15; Box {{0.0 0.0 0.3 535.8}} (left edge)
  - Layer M15; Box {{751.7 0.0 752.0 535.8}} (right edge)
  - Layer M15; Box {{0.3 0.0 751.7 0.3}} (bottom edge)
  - Layer M15; Box {{0.3 535.5 751.7 535.8}} (top edge)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-03:
  description: "Confirm routing blockages are created around the block edges."
  requirements:
    value: 4
    pattern_items:
      - "Layer M15; Box {{0.0 0.0 0.3 535.8}}"
      - "Layer M15; Box {{751.7 0.0 752.0 535.8}}"
      - "Layer M15; Box {{0.3 0.0 751.7 0.3}}"
      - "Layer M15; Box {{0.3 535.5 751.7 535.8}}"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-03.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Edge blockage pattern check is informational only during early design phase"
      - "Note: Pattern mismatches on specific layers are expected and will be resolved in final implementation"
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
  - "Explanation: Edge blockage pattern check is informational only during early design phase"
  - "Note: Pattern mismatches on specific layers are expected and will be resolved in final implementation"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - Layer M15; Box {{0.3 0.0 751.7 0.3}} (bottom edge) - MISSING [WAIVED_AS_INFO]
  - Layer M15; Box {{0.3 535.5 751.7 535.8}} (top edge) - MISSING [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-03:
  description: "Confirm routing blockages are created around the block edges."
  requirements:
    value: 4
    pattern_items:
      - "Layer M15; Box {{0.0 0.0 0.3 535.8}}"
      - "Layer M15; Box {{751.7 0.0 752.0 535.8}}"
      - "Layer M15; Box {{0.3 0.0 751.7 0.3}}"
      - "Layer M15; Box {{0.3 535.5 751.7 535.8}}"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-03.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "Layer M12; Box {{0.0 0.0 0.3 535.8}}"
        reason: "Waived - M12 left edge blockage conflicts with power strap routing per design review"
      - name: "Layer M13; Box {{0.3 535.5 751.7 535.8}}"
        reason: "Waived - M13 top edge blockage not required for this block per integration team approval"
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
  - Layer M12; Box {{0.0 0.0 0.3 535.8}} [WAIVER] - Waived - M12 left edge blockage conflicts with power strap routing per design review
  - Layer M13; Box {{0.3 535.5 751.7 535.8}} [WAIVER] - Waived - M13 top edge blockage not required for this block per integration team approval
WARN01 (Unused Waivers):
  - Layer M14; Box {{751.7 0.0 752.0 535.8}}: Waiver not matched - no corresponding edge blockage violation found
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-03:
  description: "Confirm routing blockages are created around the block edges."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-03.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "Layer M12; Box {{0.0 0.0 0.3 535.8}}"
        reason: "Waived - M12 left edge blockage conflicts with power strap routing per design review"
      - name: "Layer M13; Box {{0.3 535.5 751.7 535.8}}"
        reason: "Waived - M13 top edge blockage not required for this block per integration team approval"
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
  - Layer M12; Box {{0.0 0.0 0.3 535.8}} [WAIVER] - Waived - M12 left edge blockage conflicts with power strap routing per design review
  - Layer M13; Box {{0.3 535.5 751.7 535.8}} [WAIVER] - Waived - M13 top edge blockage not required for this block per integration team approval
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 8.0_PHYSICAL_IMPLEMENTATION_CHECK --checkers IMP-8-0-0-03 --force

# Run individual tests
python IMP-8-0-0-03.py
```

---

## Notes

- **Edge tolerance**: Uses ±0.5 unit tolerance for edge alignment detection to account for minor coordinate variations
- **Multi-layer validation**: Checks all metal layers (M12-M15 typical) for complete edge coverage
- **Die box requirement**: Report must contain valid die box definition; missing die box triggers immediate FAIL
- **Internal blockages**: Blockages not aligned to any edge are ignored for edge coverage validation but may be reported as warnings
- **Overlapping blockages**: Multiple blockages on the same edge/layer are counted separately and do not cause errors
- **Known limitations**: 
  - Does not validate blockage width/thickness (only presence and alignment)
  - Does not check for gaps in edge coverage (assumes continuous blockage if edge-aligned)
  - Tolerance value (0.5) is hardcoded and may need adjustment for different technologies