# IMP-8-0-0-02: Confirm all ports status are Fixed.

## Overview

**Check ID:** IMP-8-0-0-02  
**Description:** Confirm all ports status are Fixed.  
**Category:** Physical Implementation - Port Placement Verification  
**Input Files:** Port placement status report (*.rpt)

This checker validates that all ports in the design have been properly fixed in their placement locations. It parses port placement status reports to identify ports with incorrect placement status (placed or unplaced) and ensures all ports have achieved the required "fixed" status before proceeding with physical implementation.

---

## Check Logic

### Input Parsing
The checker parses port placement status reports with the following format:
- Standard ports: `Port: <port_name> ; Pstatus: <status>`
- Bus notation ports: `Port: {<port_name[index]>} ; Pstatus: <status>`

Port status values:
- `fixed` - Port placement is locked (correct state)
- `placed` - Port is placed but not locked (violation)
- `unplaced` - Port has no placement (violation)

**Key Patterns:**
```python
# Pattern 1: Standard port with simple name
pattern1 = r'^Port:\s*([^;{]+?)\s*;\s*Pstatus:\s*(\w+)\s*$'
# Example: "Port: pad_mem_dqs_p ; Pstatus: fixed"

# Pattern 2: Bus notation port with curly braces and index
pattern2 = r'^Port:\s*\{([^}]+)\}\s*;\s*Pstatus:\s*(\w+)\s*$'
# Example: "Port: {pad_mem_data[7]} ; Pstatus: fixed"

# Pattern 3: Generic fallback pattern for any port format
pattern3 = r'Port:\s*(.+?)\s*;\s*Pstatus:\s*(\S+)'
# Example: "Port: clk4x ; Pstatus: fixed"

# Pattern 4: Non-fixed status detection (for violations)
pattern4 = r'^Port:\s*(.+?)\s*;\s*Pstatus:\s*(?!fixed)(\w+)\s*$'
# Example: "Port: test_port ; Pstatus: placed"
```

### Detection Logic
1. Parse each line of the report file to extract port name and placement status
2. Handle both standard port names and bus notation with curly braces
3. Classify ports by status:
   - `fixed` → Clean (no action needed)
   - `placed` → Violation (port not locked)
   - `unplaced` → Violation (port not placed)
4. Collect all ports with non-fixed status as violations
5. Report violations with port name and actual status
6. PASS if all ports have `fixed` status
7. FAIL if any ports have `placed` or `unplaced` status

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

**Rationale:** This checker validates the placement status of ports. When pattern_items are specified (Type 2/3), they represent specific port names to monitor. The checker only reports on those specified ports - if a port is in pattern_items and has correct status (fixed), it goes to found_items; if it has wrong status (placed/unplaced), it goes to missing_items. Ports not in pattern_items are ignored. This is status validation, not existence checking.

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
item_desc = "Confirm all ports status are Fixed."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "All ports have fixed placement status"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All specified ports have fixed placement status"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Port placement is locked and ready for implementation"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Port placement status validated as fixed"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Ports with non-fixed placement status detected"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Specified ports have incorrect placement status"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Port placement status is not fixed (placed or unplaced)"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Port placement status does not satisfy fixed requirement"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Ports with waived placement status violations"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Port placement status violation waived per design requirements"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused port placement waiver entries"
unused_waiver_reason = "Waiver entry not matched - no corresponding port violation found"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [port_name]: Port placement status validated as fixed"
  Example: "- pad_mem_dqs_p: Port placement status validated as fixed"

ERROR01 (Violation/Fail items):
  Format: "- [port_name]: Port placement status is not fixed (Pstatus: [actual_status])"
  Example: "- test_port: Port placement status is not fixed (Pstatus: placed)"
  Example: "- debug_port: Port placement status is not fixed (Pstatus: unplaced)"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-02:
  description: "Confirm all ports status are Fixed."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "reports/8.0/IMP-8-0-0-02/port_placement_status.rpt"
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
Reason: All ports have fixed placement status
INFO01:
  - Total ports: 450, Fixed: 450, Placed: 0, Unplaced: 0: Port placement is locked and ready for implementation
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Ports with non-fixed placement status detected
ERROR01:
  - test_port: Port placement status is not fixed (Pstatus: placed)
  - debug_signal: Port placement status is not fixed (Pstatus: unplaced)
  - scan_port: Port placement status is not fixed (Pstatus: placed)
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-02:
  description: "Confirm all ports status are Fixed."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "reports/8.0/IMP-8-0-0-02/port_placement_status.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Port placement violations are informational during early floorplanning stages"
      - "Note: Non-fixed ports are expected during iterative placement optimization"
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
  - "Explanation: Port placement violations are informational during early floorplanning stages"
  - "Note: Non-fixed ports are expected during iterative placement optimization"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - test_port: Port placement status is not fixed (Pstatus: placed) [WAIVED_AS_INFO]
  - debug_signal: Port placement status is not fixed (Pstatus: unplaced) [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-02:
  description: "Confirm all ports status are Fixed."
  requirements:
    value: 3
    pattern_items:
      - "pad_mem_dqs_p"
      - "pad_mem_data[7]"
      - "clk4x"
  input_files:
    - "reports/8.0/IMP-8-0-0-02/port_placement_status.rpt"
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

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS/FAIL depends on check purpose:
- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)

**Sample Output (PASS):**
```
Status: PASS
Reason: All specified ports have fixed placement status
INFO01:
  - pad_mem_dqs_p: Port placement status validated as fixed
  - pad_mem_data[7]: Port placement status validated as fixed
  - clk4x: Port placement status validated as fixed
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-02:
  description: "Confirm all ports status are Fixed."
  requirements:
    value: 3
    pattern_items:
      - "pad_mem_dqs_p"
      - "pad_mem_data[7]"
      - "clk4x"
  input_files:
    - "reports/8.0/IMP-8-0-0-02/port_placement_status.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Monitoring specific critical ports for placement status tracking"
      - "Note: Non-fixed status on these ports is acceptable during floorplan iterations"
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
  - "Explanation: Monitoring specific critical ports for placement status tracking"
  - "Note: Non-fixed status on these ports is acceptable during floorplan iterations"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - pad_mem_data[7]: Port placement status is not fixed (Pstatus: placed) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-02:
  description: "Confirm all ports status are Fixed."
  requirements:
    value: 3
    pattern_items:
      - "pad_mem_dqs_p"
      - "pad_mem_data[7]"
      - "clk4x"
  input_files:
    - "reports/8.0/IMP-8-0-0-02/port_placement_status.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "test_mode_port"
        reason: "Test mode port - placement deferred to post-layout optimization"
      - name: "debug_scan_chain[0]"
        reason: "Debug port - non-critical path, placement flexibility allowed"
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
  - test_mode_port: Port placement status violation waived per design requirements: Test mode port - placement deferred to post-layout optimization [WAIVER]
  - debug_scan_chain[0]: Port placement status violation waived per design requirements: Debug port - non-critical path, placement flexibility allowed [WAIVER]
WARN01 (Unused Waivers):
  - optional_io_port: Waiver entry not matched - no corresponding port violation found: Optional I/O port waiver not used [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-02:
  description: "Confirm all ports status are Fixed."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "reports/8.0/IMP-8-0-0-02/port_placement_status.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "test_mode_port"
        reason: "Test mode port - placement deferred to post-layout optimization"
      - name: "debug_scan_chain[0]"
        reason: "Debug port - non-critical path, placement flexibility allowed"
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
INFO01 (Waived):
  - test_mode_port: Port placement status violation waived per design requirements: Test mode port - placement deferred to post-layout optimization [WAIVER]
  - debug_scan_chain[0]: Port placement status violation waived per design requirements: Debug port - non-critical path, placement flexibility allowed [WAIVER]
WARN01 (Unused Waivers):
  - optional_io_port: Waiver entry not matched - no corresponding port violation found: Optional I/O port waiver not used [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 8.0_PHYSICAL_IMPLEMENTATION_CHECK --checkers IMP-8-0-0-02 --force

# Run individual tests
python IMP-8-0-0-02.py
```

---

## Notes

**Port Status Definitions:**
- `fixed`: Port placement is locked and cannot be moved by optimization tools (required state)
- `placed`: Port has been placed but is not locked, may be moved during optimization (violation)
- `unplaced`: Port has no physical placement assigned (violation)

**Parsing Considerations:**
- Supports both standard port names and bus notation with curly braces `{port[index]}`
- Handles variable whitespace in report format
- Case-insensitive status comparison (fixed/Fixed/FIXED all accepted)
- Each port occurrence counted separately (handles duplicate port names if present)

**Common Use Cases:**
- Pre-implementation verification: Ensure all ports are locked before starting placement/routing
- Post-floorplan check: Validate port placement completion after floorplanning stage
- Incremental verification: Monitor port status during iterative placement optimization

**Limitations:**
- Assumes report format follows standard "Port: <name> ; Pstatus: <status>" structure
- Does not validate port placement coordinates or physical locations
- Does not check port orientation or layer assignment