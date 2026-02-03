# IMP-12-0-0-10: Confirm turn-off the VIRTUAL_CONNECT in LVS setting.

## Overview

**Check ID:** IMP-12-0-0-10  
**Description:** Confirm turn-off the VIRTUAL_CONNECT in LVS setting.  
**Category:** Physical Verification - LVS Configuration Check  
**Input Files:** 
- `${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_LVS_pvl.log` (Pegasus LVS log)
- `${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_LVS_sourceme` (Calibre LVS command file)

This checker validates that VIRTUAL_CONNECT is disabled in LVS (Layout vs Schematic) verification settings. Virtual connection allows automatic connection of nets with the same name across hierarchy boundaries, which can mask real connectivity issues. This check ensures proper LVS verification by confirming VIRTUAL_CONNECT is turned off.

The checker supports both Pegasus and Calibre LVS tools:
- **Pegasus**: Checks for `VIRTUAL_CONNECT` setting in `.pvl` log files (option format: `-COLON NO`)
- **Calibre**: Checks for `VIRTUAL CONNECT COLON` setting in `sourceme` command files (option format: `COLON YES/NO`)

User only needs to specify one file - either Pegasus or Calibre format is acceptable.

---

## Check Logic

### Input Parsing

**File Type 1: Pegasus LVS Log (`do_pvs_LVS_pvl.log`)**
- Parse Pegasus LVS verification log file
- Search for VIRTUAL_CONNECT setting in rule file parsing section
- Extract setting state (specifically `-COLON NO` for disabled state)
- Verify setting is disabled (`-COLON NO`)

**File Type 2: Calibre LVS Command File (`do_cmd_3star_LVS_sourceme`)**
- Parse Calibre LVS command/rule file
- Search for `VIRTUAL CONNECT COLON` directive
- Extract setting value (YES/NO)
- Verify setting is NO (disabled)

**Key Patterns:**

```python
# Pattern 1: Pegasus VIRTUAL_CONNECT setting (case-insensitive)
pegasus_pattern = r'^\s*VIRTUAL_CONNECT\s+-COLON\s+(NO)\s*;?\s*$'
# Example: "VIRTUAL_CONNECT -COLON NO;"
# Extraction: Group 1 captures the setting state (NO for disabled)

# Pattern 2: Calibre VIRTUAL CONNECT COLON setting
calibre_pattern = r'^\s*VIRTUAL\s+CONNECT\s+COLON\s+(YES|NO)\s*$'
# Example: "VIRTUAL CONNECT COLON NO"
# Extraction: Group 1 captures YES or NO value

# Pattern 3: Alternative Pegasus command format
pegasus_alt_pattern = r'^\s*lvs_virtual_connect\s+-colon\s+no\s*$'
# Example: "lvs_virtual_connect -colon no"
# Extraction: Group 1 captures the setting state

# Pattern 4: Commented lines (should be ignored)
comment_pattern = r'^\s*(#|//).*VIRTUAL'
# Example: "# VIRTUAL_CONNECT -COLON NO"
# These lines should NOT be counted as active settings
```

### Detection Logic

**Step 1: File Type Detection**
- Check file extension and content to determine if Pegasus (.pvl log) or Calibre (sourceme)
- Apply appropriate parsing pattern based on tool type

**Step 2: VIRTUAL_CONNECT Search**
- Read file line by line
- Skip comment lines (starting with `#` or `//`)
- Search for VIRTUAL_CONNECT or VIRTUAL CONNECT COLON keywords
- Extract setting value when found
- Track line number for reporting

**Step 3: Setting Validation**
- **Pegasus**: Verify setting is `-COLON NO` (disabled state)
- **Calibre**: Verify setting is NO (disabled state)
- If multiple VIRTUAL_CONNECT statements exist, use the last occurrence
- If VIRTUAL_CONNECT not found, report as potential issue (may default to ON)

**Step 4: Result Classification**
- **PASS**: VIRTUAL_CONNECT is explicitly disabled (`-COLON NO` for Pegasus, `NO` for Calibre)
- **FAIL**: VIRTUAL_CONNECT is enabled or not found in file
- Report file path, setting value, and line number for traceability

**Edge Cases:**
- VIRTUAL_CONNECT not mentioned at all (may default to ON - should fail)
- Multiple VIRTUAL_CONNECT statements (last one wins)
- VIRTUAL_CONNECT in comments (should ignore)
- Case variations (VIRTUAL_CONNECT vs virtual_connect - handle case-insensitive)
- Setting in included files vs main file (check main file only)
- Whitespace variations between keywords

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

**Rationale:** This checker validates the STATUS of VIRTUAL_CONNECT setting (enabled vs disabled). The pattern_items represent the expected disabled state ("VIRTUAL_CONNECT -COLON NO" for Pegasus or "VIRTUAL CONNECT COLON NO" for Calibre). The checker searches for VIRTUAL_CONNECT configuration and validates its status is disabled. Only the matched VIRTUAL_CONNECT setting is output with its status validation result.

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
item_desc = "Confirm turn-off the VIRTUAL_CONNECT in LVS setting."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "VIRTUAL_CONNECT setting found and verified as disabled"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "VIRTUAL_CONNECT setting matched expected disabled state (-COLON NO)"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "VIRTUAL_CONNECT is disabled (-COLON NO for Pegasus, NO for Calibre) in LVS configuration"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "VIRTUAL_CONNECT setting matched and validated as disabled (-COLON NO for Pegasus, NO for Calibre)"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "VIRTUAL_CONNECT setting not found or enabled in LVS configuration"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "VIRTUAL_CONNECT setting not satisfied - expected disabled state (-COLON NO)"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "VIRTUAL_CONNECT is enabled or not found in LVS configuration file"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "VIRTUAL_CONNECT setting not satisfied - found enabled or missing from configuration"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "VIRTUAL_CONNECT enabled state waived per design team approval"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "VIRTUAL_CONNECT enabled state waived - approved exception for this design"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused VIRTUAL_CONNECT waiver entries"
unused_waiver_reason = "Waiver not matched - VIRTUAL_CONNECT setting not found or already disabled"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "[Tool] VIRTUAL_CONNECT is [STATE] (line [LINE_NUMBER])"
  Example: "Pegasus VIRTUAL_CONNECT -COLON NO (line 88)"
  Example: "Calibre VIRTUAL CONNECT COLON NO (line 88)"

ERROR01 (Violation/Fail items):
  Format: "[Tool] VIRTUAL_CONNECT is [STATE] (should be -COLON NO/NO) (line [LINE_NUMBER])"
  Example: "Pegasus VIRTUAL_CONNECT is enabled (should be -COLON NO) (line 88)"
  Example: "Calibre VIRTUAL CONNECT COLON YES (should be NO) (line 88)"
  Example: "VIRTUAL_CONNECT setting not found in file (may default to ON)"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-10:
  description: "Confirm turn-off the VIRTUAL_CONNECT in LVS setting."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_LVS_pvl.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_LVS_sourceme"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs boolean validation of VIRTUAL_CONNECT setting.
- Searches for VIRTUAL_CONNECT configuration in either Pegasus or Calibre LVS files
- Validates setting is disabled (`-COLON NO` for Pegasus, `NO` for Calibre)
- PASS if VIRTUAL_CONNECT is explicitly disabled
- FAIL if VIRTUAL_CONNECT is enabled or not found

**Sample Output (PASS):**
```
Status: PASS
Reason: VIRTUAL_CONNECT is disabled (-COLON NO for Pegasus, NO for Calibre) in LVS configuration
INFO01:
  - Calibre VIRTUAL CONNECT COLON NO (line 88)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: VIRTUAL_CONNECT is enabled or not found in LVS configuration file
ERROR01:
  - Calibre VIRTUAL CONNECT COLON YES (should be NO) (line 88)
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-10:
  description: "Confirm turn-off the VIRTUAL_CONNECT in LVS setting."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_LVS_pvl.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_LVS_sourceme"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: VIRTUAL_CONNECT enabled is acceptable for this design because hierarchical LVS is required"
      - "Note: Design team has verified connectivity manually and approved VIRTUAL_CONNECT usage"
```

**CRITICAL Behavior (waivers.value=0):**
- NOTE: Type 1 has NO waiver logic. waive=0 is forced PASS mode only
- IMPORTANT: waive_items uses PLAIN STRINGS (NOT name/reason dict like Type 3/4!)
- waive_items serves as COMMENT ONLY (no matching/filtering logic)
- waive_items content printed as INFO with [WAIVED_INFO] tag
- ALL violations force converted: FAIL→PASS, displayed as INFO with [WAIVED_AS_INFO] tag
- Check ALWAYS returns PASS (violations shown as INFO for tracking)
- Used when: VIRTUAL_CONNECT enabled is acceptable for specific design requirements

**Sample Output (PASS with violations):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All violations waived as informational
INFO01 ([WAIVED_INFO] - waive_items as comment):
  - "Explanation: VIRTUAL_CONNECT enabled is acceptable for this design because hierarchical LVS is required"
  - "Note: Design team has verified connectivity manually and approved VIRTUAL_CONNECT usage"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - Calibre VIRTUAL CONNECT COLON YES (should be NO) (line 88) [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-10:
  description: "Confirm turn-off the VIRTUAL_CONNECT in LVS setting."
  requirements:
    value: 2
    pattern_items:
      - "VIRTUAL_CONNECT -COLON NO"  # Pegasus disabled state
      - "VIRTUAL CONNECT COLON NO"   # Calibre disabled state
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_LVS_pvl.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_LVS_sourceme"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Description says "turn-off the VIRTUAL_CONNECT" → Extract STATUS VALUES
- pattern_items represent the expected DISABLED states for both tools
- "VIRTUAL_CONNECT -COLON NO" = Pegasus disabled state
- "VIRTUAL CONNECT COLON NO" = Calibre disabled state
- These are the golden values the checker validates against

**Check Behavior:**
Type 2 searches for VIRTUAL_CONNECT setting and validates against expected disabled states.
- Extracts VIRTUAL_CONNECT configuration from LVS files
- Compares against pattern_items (expected disabled states)
- PASS if found setting matches pattern_items (disabled state)
- FAIL if setting doesn't match (enabled state) or not found

**Sample Output (PASS):**
```
Status: PASS
Reason: VIRTUAL_CONNECT setting matched and validated as disabled (-COLON NO for Pegasus, NO for Calibre)
INFO01:
  - Calibre VIRTUAL CONNECT COLON NO (line 88)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-10:
  description: "Confirm turn-off the VIRTUAL_CONNECT in LVS setting."
  requirements:
    value: 2
    pattern_items:
      - "VIRTUAL_CONNECT -COLON NO"
      - "VIRTUAL CONNECT COLON NO"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_LVS_pvl.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_LVS_sourceme"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: VIRTUAL_CONNECT enabled is acceptable for hierarchical LVS verification"
      - "Note: Design uses consistent naming convention across hierarchy, VIRTUAL_CONNECT safe to enable"
```

**CRITICAL Behavior (waivers.value=0):**
- NOTE: Type 2 has NO waiver logic. waive=0 is forced PASS mode only
- IMPORTANT: waive_items uses PLAIN STRINGS (NOT name/reason dict like Type 3/4!)
- waive_items serves as COMMENT ONLY (no matching/filtering logic)
- waive_items content printed as INFO with [WAIVED_INFO] tag
- ALL errors/mismatches force converted: ERROR→PASS, displayed as INFO with [WAIVED_AS_INFO] tag
- Check ALWAYS returns PASS (errors shown as INFO for tracking)
- Used when: Pattern check is informational, enabled state is acceptable

**Sample Output (PASS with mismatches):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All mismatches waived as informational
INFO01 ([WAIVED_INFO] - waive_items as comment):
  - "Explanation: VIRTUAL_CONNECT enabled is acceptable for hierarchical LVS verification"
  - "Note: Design uses consistent naming convention across hierarchy, VIRTUAL_CONNECT safe to enable"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - Calibre VIRTUAL CONNECT COLON YES (should be NO) (line 88) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-10:
  description: "Confirm turn-off the VIRTUAL_CONNECT in LVS setting."
  requirements:
    value: 2
    pattern_items:
      - "VIRTUAL_CONNECT -COLON NO"  # Pegasus disabled state
      - "VIRTUAL CONNECT COLON NO"   # Calibre disabled state
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_LVS_pvl.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_LVS_sourceme"
  waivers:
    value: 2
    waive_items:
      - name: "VIRTUAL_CONNECT enabled"
        reason: "Waived - hierarchical LVS requires VIRTUAL_CONNECT for this legacy design"
      - name: "VIRTUAL CONNECT COLON YES"
        reason: "Waived - Calibre LVS approved to use VIRTUAL_CONNECT per design review"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:
- BOTH must be at SAME semantic level as description!
- Description says "turn-off the VIRTUAL_CONNECT" → STATUS VALUES
- pattern_items: Expected disabled states ("VIRTUAL_CONNECT -COLON NO", "VIRTUAL CONNECT COLON NO")
- waive_items.name: Actual enabled states found in files ("VIRTUAL_CONNECT enabled", "VIRTUAL CONNECT COLON YES")
- waive_items.name represents the violations being waived (enabled states)

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Search for VIRTUAL_CONNECT setting in LVS files
- Validate against pattern_items (expected disabled states)
- If enabled state found, match against waive_items
- Unwaived enabled states → ERROR (need fix)
- Waived enabled states → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all enabled states (violations) are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - Calibre VIRTUAL CONNECT COLON YES (should be NO) (line 88) [WAIVER]
WARN01 (Unused Waivers):
  - VIRTUAL_CONNECT enabled: Waiver not matched - VIRTUAL_CONNECT setting not found or already disabled
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-10:
  description: "Confirm turn-off the VIRTUAL_CONNECT in LVS setting."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_LVS_pvl.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_LVS_sourceme"
  waivers:
    value: 2
    waive_items:
      - name: "VIRTUAL_CONNECT enabled"
        reason: "Waived - hierarchical LVS requires VIRTUAL_CONNECT for this legacy design"
      - name: "VIRTUAL CONNECT COLON YES"
        reason: "Waived - Calibre LVS approved to use VIRTUAL_CONNECT per design review"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (no pattern_items), plus waiver classification:
- Validate VIRTUAL_CONNECT is disabled in LVS configuration
- If enabled state found, match violations against waive_items
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output:**
```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - Calibre VIRTUAL CONNECT COLON YES (should be NO) (line 88) [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 12.0_PHYSICAL_VERIFICATION_CHECK --checkers IMP-12-0-0-10 --force

# Run individual tests
python IMP-12-0-0-10.py
```

---

## Notes

**Tool-Specific Behavior:**
- **Pegasus LVS**: Uses `VIRTUAL_CONNECT -COLON NO` format with semicolon terminator (e.g., `VIRTUAL_CONNECT -COLON NO;`)
- **Calibre LVS**: Uses `VIRTUAL CONNECT COLON` directive without leading dash (e.g., `VIRTUAL CONNECT COLON NO`)
- User only needs to provide one file type - checker auto-detects tool format

**Default Behavior:**
- If VIRTUAL_CONNECT setting is not explicitly specified in the file, it may default to ON (enabled)
- Checker treats missing VIRTUAL_CONNECT as FAIL to ensure explicit configuration

**Multiple Statements:**
- If multiple VIRTUAL_CONNECT statements exist in the file, the last occurrence takes precedence
- Checker reports the final effective setting

**Comment Handling:**
- Lines starting with `#` or `//` are treated as comments and ignored
- VIRTUAL_CONNECT in comments does not count as active configuration

**Case Sensitivity:**
- Checker performs case-insensitive matching for VIRTUAL_CONNECT keywords
- Handles variations like `virtual_connect`, `VIRTUAL_CONNECT`, `Virtual_Connect`

**Included Files:**
- Checker only validates the main LVS file provided
- Does not recursively check included files referenced by `include` directives
- Assumes VIRTUAL_CONNECT setting is in the main rule file

**Known Limitations:**
- Does not validate VIRTUAL_CONNECT settings in included rule files
- Does not check for conditional VIRTUAL_CONNECT settings (e.g., within `#ifdef` blocks)
- Assumes standard Pegasus/Calibre syntax - custom rule file formats may not be detected