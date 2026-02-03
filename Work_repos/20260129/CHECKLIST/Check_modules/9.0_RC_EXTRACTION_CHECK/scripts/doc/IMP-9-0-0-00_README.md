# IMP-9-0-0-00: Confirm SPEF extaction includes dummy metal gds.

## Overview

**Check ID:** IMP-9-0-0-00  
**Description:** Confirm SPEF extaction includes dummy metal gds.  
**Category:** RC Extraction Verification  
**Input Files:** 
- `${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrcrcworst_CCworst_T_125c.log`
- `${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrccbest_CCbest_125c.log`

This checker validates that Cadence Quantus QRC parasitic extraction includes dummy metal (metal fill) GDS layers in SPEF generation. Metal fill layers are critical for accurate parasitic extraction as they represent floating/grounded metal shapes added for density compliance. The checker verifies that:

1. The extraction setup contains `input_db -type metal_fill` configuration with a valid GDS file reference
2. The metal fill GDS file path points to a BEOL (Back-End-Of-Line) GDS file (typically `*BEOL.gds`)
3. No error messages indicate missing metal fill data (e.g., "does NOT contain MetalFill data")

Without metal fill inclusion, extracted parasitics may be inaccurate, leading to timing/SI analysis errors in signoff.

---

## Check Logic

### Input Parsing

The checker parses Quantus QRC extraction log files to verify metal fill configuration. Each log file represents one extraction corner/scenario (e.g., RC worst, CC best).

**Key Patterns:**

```python
# Pattern 1: Metal fill GDS input configuration (UPDATED - supports newline after =)
# CRITICAL: Must handle both single-line and cross-line formats
pattern1 = r'input_db\s+-type\s+metal_fill\s+.*?-gds_file\s*=\s*\n?\s*"([^"]+)"'
# Single-line format:
# input_db -type metal_fill -gds_file = "/path/to/BEOL.gds"
# Cross-line format (IMPORTANT - path on next line):
# input_db -type metal_fill -gds_file =
# "/projects/yunbao_N6_80bits_EW_PHY_OD_6400/work/.../BEOL/BEOL.gds"
# Extracts: GDS file path (group 1)

# Pattern 2: Metal fill type configuration
pattern2 = r'^metal_fill\s+.*?-type\s+"([^"]+)"'
# Example:
# metal_fill \
#     -type "FLOATING"
# Extracts: Metal fill type (group 1) - FLOATING, GROUNDED, or NONE

# Pattern 2b: Alternative metal fill enable flag (NEW)
# CRITICAL: Some logs use enable_metal_fill_effects instead of metal_fill -type
pattern2b = r'enable_metal_fill_effects\s*=\s*"(true)"'
# Example:
# INFO (EXTGRMP-143) : Option enable_metal_fill_effects = "true"
# Extracts: "true" value indicating metal fill is enabled
# NOTE: This is equivalent to metal_fill -type "FLOATING" or "GROUNDED"

# Pattern 3: Error messages related to metal fill
pattern3 = r'^(?:ERROR|\*\*ERROR).*?(?:metal_fill|MetalFill|gds_file|BEOL).*$'
# Example:
# ERROR (EXTGDS-123): GDS file processing error
# Extracts: Error messages indicating metal fill issues

# Pattern 4: Warning messages about metal fill processing
pattern4 = r'^(?:WARNING|\*\*WARNING).*?(?:metal_fill|gds|density).*$'
# Example:
# WARNING (EXTGRMP-635) : The option extraction_setup -density_bounding_box is ignored.
# Extracts: Warnings that may affect metal fill extraction

# Pattern 5: Missing MetalFill data message (standalone message without ERROR/WARN keyword)
pattern5 = r'does NOT contain MetalFill data'
# Example:
# GDS file "/path/to/BEOL.gds" does NOT contain MetalFill data
# Extracts: Standalone message indicating metal fill data is missing from GDS file
```

### Detection Logic

**Step 1: Read QRC extraction log file**
- Parse entire log file (typically < 50MB)
- Identify "Command File Options" section (starts with `INFO (EXTQRCXLOG-103)`)

**Step 2: Search for metal fill configuration**
- Use multi-line regex to find `input_db -type metal_fill` block
- Extract GDS file path from `-gds_file` parameter
- Verify path contains "BEOL" substring (indicates Back-End-Of-Line metal fill GDS)

**Step 3: Verify metal fill type**
- Search for `metal_fill -type` configuration OR `enable_metal_fill_effects = "true"`
- Extract processing mode:
  - `metal_fill -type "FLOATING"` or `"GROUNDED"` = metal fill included (PASS)
  - `enable_metal_fill_effects = "true"` = metal fill enabled (PASS)
  - `metal_fill -type "NONE"` or missing = metal fill excluded (FAIL)
- CRITICAL: Valid metal fill types are FLOATING, GROUNDED, or ENABLED
  - ENABLED indicates metal fill is active via enable_metal_fill_effects flag

**Step 4: Scan for error/warning messages**
- Search for ERROR/WARNING messages containing keywords: metal_fill, MetalFill, gds_file, BEOL
- Search for standalone message "does NOT contain MetalFill data" (IMPORTANT: This is a standalone message without ERROR or WARN prefix)
- Standalone message "does NOT contain MetalFill data" → FAIL (indicates GDS file lacks metal fill layers)
- ERROR messages related to metal_fill/gds_file → FAIL
- Warnings (e.g., density_bounding_box ignored) → Report but may not fail

**Step 5: Build corner-to-file mapping for error reporting**
- CRITICAL: Store mapping of corner_name → log_file_path
- This enables detailed error messages with full file paths
- Example: `corner_file_map = {'do_qrccbest_CCbest_125c': 'C:\...\logs\9.0\do_qrccbest_CCbest_125c.log'}`
- Used in missing_items to show: "do_qrccbest_CCbest_125c.log: ... In C:\...\logs\9.0\do_qrccbest_CCbest_125c.log"

**Step 6: Aggregate results across all log files**
- Check each extraction corner/scenario log
- Report PASS if ALL logs have valid metal fill configuration
- Report FAIL if ANY log is missing metal fill or has errors

**Edge Cases:**
- Multi-line commands with backslash continuation (need to concatenate lines)
- Cross-line GDS path: `-gds_file =` on one line, path on next line (CRITICAL - must handle!)
- Missing `metal_fill` section entirely (indicates dummy metal NOT included)
- `metal_fill -type "NONE"` (explicitly excludes dummy metal)
- `enable_metal_fill_effects = "true"` as alternative to `metal_fill -type`
- Empty GDS path: `-gds_file = ""` (indicates no metal fill GDS)
- Relative vs absolute GDS file paths (both valid)
- Multiple `input_db -type metal_fill` blocks for different layers (all should be checked)
- Truncated log files (extraction crashed early - treat as FAIL)
- Standalone "does NOT contain MetalFill data" message without ERROR/WARN prefix

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `existence_check`

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

**Selected Mode for this checker:** `existence_check`

**Rationale:** This checker validates that required metal fill configuration elements EXIST in QRC extraction logs. The `pattern_items` represent mandatory configuration components (metal fill GDS file reference, metal fill type setting) that MUST be present in the extraction setup. The checker searches for these configuration patterns and reports which ones are found vs. missing. This is a classic existence check - verifying that all required setup elements are configured, not checking the status of existing items.

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
item_desc = "Confirm SPEF extraction includes dummy metal GDS"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
# IMPORTANT: Remove "all corners" - each log represents ONE corner
found_desc_type1_4 = "QRC extraction completed with metal fill GDS configuration found"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "Metal fill GDS configuration matched and validated in extraction corner logs"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
# IMPORTANT: Remove "all corners" - refer to single corner context
found_reason_type1_4 = "Metal fill GDS file found in extraction corner configuration with valid BEOL path"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Metal fill configuration pattern matched with FLOATING/GROUNDED type and valid GDS path"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "QRC extraction missing metal fill GDS configuration or contains errors"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Expected metal fill GDS configuration not satisfied or missing in extraction corner logs"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
# IMPORTANT: Use "this corner" instead of "one or more corners"
missing_reason_type1_4 = "Metal fill GDS configuration not found or contains critical errors (missing MetalFill data) in this corner"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Expected metal fill pattern not satisfied: missing input_db configuration or type is NONE in this corner"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Metal fill configuration issues waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Metal fill GDS configuration issue waived per extraction team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused metal fill waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding metal fill configuration issue found in extraction logs"
```

### INFO01/ERROR01 Display Format

🛑 CRITICAL OUTPUT FORMAT REQUIREMENTS:
1. ALL items MUST use `corner_name.log:` prefix (note the .log suffix!)
2. Missing items MUST include full file path: "In C:\...\logs\9.0\corner_name.log"
3. Corner references removed: NO "all corners" or "one or more corners" in text

```
INFO01 (Clean/Pass items):
  Format: "[corner_name].log: Metal fill GDS = [gds_path]. In line [N], [full_file_path]: [reason]"
  Example: "do_qrcrcworst_CCworst_T_125c.log: Metal fill GDS = /projects/.../BEOL/BEOL.gds. In line 338, C:\Users\...\logs\9.0\do_qrcrcworst_CCworst_T_125c.log: Metal fill GDS file found in extraction corner configuration with valid BEOL path"
  
  IMPORTANT: Note the .log suffix after corner name!

ERROR01 (Violation/Fail items):
  Format: "[corner_name].log: [ERROR_TYPE]. In [full_file_path]: [reason]"
  Example: "do_qrccbest_CCbest_125c.log: Metal fill configuration missing or incomplete. In C:\Users\...\logs\9.0\do_qrccbest_CCbest_125c.log: Metal fill GDS configuration not found or contains critical errors"
  
  CRITICAL: Must include full file path with "In [path]:" for traceability!
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-9-0-0-00:
  description: "Confirm SPEF extaction includes dummy metal gds."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrcrcworst_CCworst_T_125c.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrccbest_CCbest_125c.log"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs custom boolean validation - checks if metal fill GDS configuration exists in ALL QRC extraction logs. The checker parses each log file to verify:
1. `input_db -type metal_fill` with valid `-gds_file` path exists
2. GDS file path contains "BEOL" substring
3. No error messages about missing MetalFill data
4. No standalone "does NOT contain MetalFill data" message

PASS if all logs have valid metal fill configuration.
FAIL if any log is missing metal fill or has errors.

**Sample Output (PASS):**
```
Status: PASS
Reason: Metal fill GDS file found in extraction corner configuration with valid BEOL path
INFO01:
  - do_qrcrcworst_CCworst_T_125c.log: Metal fill GDS = /projects/byd_A3_N4P_32bits_LPDDR5_phy/work/.../BEOL/BEOL.gds. In line 338, C:\Users\...\logs\9.0\do_qrcrcworst_CCworst_T_125c.log: Metal fill GDS file found in extraction corner configuration with valid BEOL path
  - do_qrccbest_CCbest_m40c.log: Metal fill GDS = /projects/yunbao_N6_80bits_EW_PHY/.../BEOL/BEOL.gds. In line 3, C:\Users\...\logs\9.0\do_qrccbest_CCbest_m40c.log: Metal fill GDS file found in extraction corner configuration with valid BEOL path
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Metal fill GDS configuration not found or contains critical errors (missing MetalFill data) in this corner
ERROR01:
  - do_qrccbest_CCbest_125c.log: Metal fill configuration missing or incomplete. In C:\Users\...\logs\9.0\do_qrccbest_CCbest_125c.log: Metal fill GDS configuration not found or contains critical errors (missing MetalFill data) in this corner
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-9-0-0-00:
  description: "Confirm SPEF extaction includes dummy metal gds."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrcrcworst_CCworst_T_125c.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrccbest_CCbest_125c.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Metal fill GDS check is informational only for post-synthesis extraction"
      - "Note: Dummy metal not required for early timing analysis - will be added in final signoff extraction"
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
  - "Explanation: Metal fill GDS check is informational only for post-synthesis extraction"
  - "Note: Dummy metal not required for early timing analysis - will be added in final signoff extraction"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - do_qrccbest_CCbest_125c.log: MISSING_METAL_FILL - input_db -type metal_fill not found in extraction setup [WAIVED_AS_INFO]
  - do_qrcrcworst_CCworst_T_125c.log: MISSING_METALFILL_DATA - GDS file does NOT contain MetalFill data [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-9-0-0-00:
  description: "Confirm SPEF extaction includes dummy metal gds."
  requirements:
    value: 2
    pattern_items:
      - "do_qrcrcworst_CCworst_T_125c.log"
      - "do_qrccbest_CCbest_125c.log"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrcrcworst_CCworst_T_125c.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrccbest_CCbest_125c.log"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Pattern items represent the extraction log files that MUST contain valid metal fill configuration
- Each pattern_item is a log filename (not full path, just the filename)
- Checker searches each log file for metal fill GDS configuration
- PASS if all pattern_items (log files) have valid metal fill setup
- FAIL if any pattern_item (log file) is missing metal fill configuration

**Check Behavior:**
Type 2 searches for metal fill configuration in each log file specified in pattern_items.
- found_items: Log files with valid metal fill GDS configuration
- missing_items: Log files missing metal fill configuration or with errors
- PASS if missing_items is empty (all required logs have metal fill)
- FAIL if missing_items is not empty (some logs missing metal fill)

**Sample Output (PASS):**
```
Status: PASS
Reason: Metal fill configuration pattern matched with FLOATING/GROUNDED type and valid GDS path
INFO01:
  - do_qrcrcworst_CCworst_T_125c.log: Metal fill GDS = /projects/.../BEOL/BEOL.gds. In line 338, C:\Users\...\logs\9.0\do_qrcrcworst_CCworst_T_125c.log: Metal fill configuration pattern matched with FLOATING/GROUNDED type and valid GDS path
  - do_qrccbest_CCbest_m40c.log: Metal fill GDS = /projects/.../BEOL/BEOL.gds. In line 3, C:\Users\...\logs\9.0\do_qrccbest_CCbest_m40c.log: Metal fill configuration pattern matched with FLOATING/GROUNDED type and valid GDS path
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-9-0-0-00:
  description: "Confirm SPEF extaction includes dummy metal gds."
  requirements:
    value: 2
    pattern_items:
      - "do_qrcrcworst_CCworst_T_125c.log"
      - "do_qrccbest_CCbest_125c.log"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrcrcworst_CCworst_T_125c.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrccbest_CCbest_125c.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Metal fill check is informational for early extraction runs"
      - "Note: Missing metal fill in RC worst corner is acceptable for pre-layout analysis"
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
  - "Explanation: Metal fill check is informational for early extraction runs"
  - "Note: Missing metal fill in RC worst corner is acceptable for pre-layout analysis"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - do_qrccbest_CCbest_125c.log: MISSING_METAL_FILL - input_db -type metal_fill not found in extraction setup [WAIVED_AS_INFO]
  - do_qrcrcworst_CCworst_T_125c.log: MISSING_METALFILL_DATA - GDS file does NOT contain MetalFill data [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-9-0-0-00:
  description: "Confirm SPEF extaction includes dummy metal gds."
  requirements:
    value: 2
    pattern_items:
      - "do_qrcrcworst_CCworst_T_125c.log"
      - "do_qrccbest_CCbest_125c.log"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrcrcworst_CCworst_T_125c.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrccbest_CCbest_125c.log"
  waivers:
    value: 2
    waive_items:
      - name: "do_qrccbest_CCbest_125c.log"
        reason: "Waived - CC best corner uses simplified extraction without metal fill per design team approval"
      - name: "do_qrcrcworst_CCworst_T_125c.log"
        reason: "Waived - RC worst corner metal fill GDS path updated in next extraction run"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:
- BOTH must be at SAME semantic level as description!
- Description focuses on "SPEF extraction" and "dummy metal gds" (log file level check)
- pattern_items: Log filenames that should have metal fill configuration
- waive_items.name: Log filenames where missing metal fill is waived
- Both use the SAME format: just the log filename (e.g., "do_qrcrcworst_CCworst_T_125c.log")

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Search each log file in pattern_items for metal fill configuration
- Match missing/error items against waive_items
- Unwaived missing items → ERROR (need fix)
- Waived missing items → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all missing items are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - do_qrccbest_CCbest_125c.log: MISSING_METAL_FILL - input_db -type metal_fill not found [WAIVER]
WARN01 (Unused Waivers):
  - do_qrcrcworst_CCworst_T_125c.log: Waiver not matched - no corresponding metal fill configuration issue found in extraction logs
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-9-0-0-00:
  description: "Confirm SPEF extaction includes dummy metal gds."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrcrcworst_CCworst_T_125c.log"
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/do_qrccbest_CCbest_125c.log"
  waivers:
    value: 2
    waive_items:
      - name: "do_qrccbest_CCbest_125c.log"
        reason: "Waived - CC best corner uses simplified extraction without metal fill per design team approval"
      - name: "do_qrcrcworst_CCworst_T_125c.log"
        reason: "Waived - RC worst corner metal fill GDS path updated in next extraction run"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (log filenames)
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (no pattern_items), plus waiver classification:
- Check all input log files for metal fill configuration
- Match violations (missing metal fill) against waive_items
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output:**
```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - do_qrccbest_CCbest_125c.log: MISSING_METAL_FILL - input_db -type metal_fill not found [WAIVER]
WARN01 (Unused Waivers):
  - do_qrcrcworst_CCworst_T_125c.log: Waiver not matched - no corresponding metal fill configuration issue found in extraction logs
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 9.0_RC_EXTRACTION_CHECK --checkers IMP-9-0-0-00 --force

# Run individual tests
python IMP-9-0-0-00.py
```

---

## Notes

**Important Considerations:**

1. **Cross-line GDS Path Format (CRITICAL!)**: QRC extraction log may show GDS file path on the NEXT line after `=`:
   ```
   input_db -type metal_fill -gds_file =
   "/projects/yunbao_N6_80bits_EW_PHY/.../BEOL/BEOL.gds"
   ```
   The regex pattern MUST include `\n?` to handle newline after `=`.

2. **Multi-line Command Parsing**: QRC extraction commands use backslash continuation across multiple lines. The checker must concatenate these lines before pattern matching.

3. **BEOL GDS File Requirement**: The metal fill GDS file should contain "BEOL" in its path (e.g., `/path/to/BEOL/BEOL.gds`). This indicates it's the Back-End-Of-Line metal fill layer set.

4. **Metal Fill Type Detection (TWO Methods!)**: 
   - Method 1: `metal_fill -type "FLOATING"` or `"GROUNDED"` 
   - Method 2: `enable_metal_fill_effects = "true"` 
   - If type is "NONE" or both methods missing, dummy metal is NOT included
   - Valid types: FLOATING, GROUNDED, or ENABLED (ENABLED = enable_metal_fill_effects)

5. **Empty GDS Path Detection**: Some logs may have `input_db -type metal_fill -gds_file = ""` (empty string). This indicates metal fill is configured but NO GDS file is specified (should FAIL).

6. **Corner-to-File Mapping (NEW!)**: The checker MUST build and store a `corner_file_map` dictionary:
   ```python
   corner_file_map = {
       'do_qrccbest_CCbest_125c': 'C:\\Users\\...\\logs\\9.0\\do_qrccbest_CCbest_125c.log',
       'do_qrcrcworst_CCworst_T_125c': 'C:\\Users\\...\\logs\\9.0\\do_qrcrcworst_CCworst_T_125c.log'
   }
   ```
   This mapping is used to include full file paths in missing_items error messages.

7. **Standalone Error Message Detection**: The checker specifically looks for the standalone message "does NOT contain MetalFill data" which appears in the log WITHOUT an "ERROR" or "WARNING" keyword prefix. This indicates the GDS file was specified but doesn't contain the expected metal fill layers.

8. **Output Format Consistency (CRITICAL!)**: ALL output items (found_items, missing_items, waived_items) MUST use `corner_name.log:` prefix format:
   ```python
   # CORRECT:
   found_items[f"{corner}.log: Metal fill GDS = {gds_path}"] = {...}
   missing_items.append(f"{corner}.log: Metal fill configuration missing. In {file_path}")
   
   # WRONG (missing .log suffix):
   found_items[f"{corner}: Metal fill GDS = {gds_path}"] = {...}  # ❌
   ```

9. **Corner Reference Terminology**: Remove ALL references to "all corners" or "one or more corners" in output text. Each log file represents ONE corner, so use singular forms:
   - Use: "in extraction corner configuration" or "in this corner"
   - Avoid: "in all extraction corner configurations" or "in one or more corners"

10. **Multiple Extraction Corners**: Typically there are multiple QRC extraction runs (RC worst, CC best, etc.). Each should include metal fill for consistent parasitic extraction.

11. **Compressed Input Files**: Input DEF files may be compressed (`.def.gz`). This is normal and not an error.

12. **Warnings vs Errors**: Some warnings (e.g., `density_bounding_box is ignored`) are informational and don't indicate metal fill is missing. Only critical errors should cause FAIL.

**Known Limitations:**

- The checker assumes metal fill GDS files follow the naming convention `*BEOL.gds`. Non-standard naming may require checker updates.
- Relative GDS paths are accepted but may be harder to validate for existence.
- The checker does not verify the actual contents of the GDS file, only that it's referenced in the extraction setup.