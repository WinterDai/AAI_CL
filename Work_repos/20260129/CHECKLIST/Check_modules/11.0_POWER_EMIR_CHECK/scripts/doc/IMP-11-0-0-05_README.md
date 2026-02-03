# IMP-11-0-0-05: Confirm generate all the power library with detail view correctly.

## Overview

**Check ID:** IMP-11-0-0-05  
**Description:** Confirm generate all the power library with detail view correctly.  
**Category:** Power Library Generation Verification  
**Input Files:** ${CHECKLIST_ROOT}/IP_project_folder/logs/*LibGen.log

This checker validates that power libraries for macros are generated with proper GDS detail views. It scans Voltus LibGen log files to extract `set_pg_library_mode` commands, filters for macro cell types, and reports all GDS files specified for user verification. The checker does not perform PASS/FAIL validation but provides a comprehensive report of GDS files used in power library generation for manual review.

---

## Check Logic

### Input Parsing

The checker processes Voltus LibGen log files containing power library generation commands.

**Key Patterns:**

```python
# Pattern 1: Extract celltype from set_pg_library_mode command
pattern_celltype = r'set_pg_library_mode\s+-celltype\s+(\S+)'
# Example: "<CMD> set_pg_library_mode -celltype macros -ground_pins {VSS 0.000} ..."
# Extracts: "macros", "techonly", "stdcells"

# Pattern 2: Extract GDS files list from -gds_files parameter (handles both formats)
pattern_gds_files_braces = r'-gds_files\s+\{([^}]*)\}'  # Format: -gds_files {file1 file2}
pattern_gds_files_no_braces = r'-gds_files\s+([^-\n]+?)(?=\s+-|\s*$)'  # Format: -gds_files file1
# Example 1: "-gds_files {/path/to/design.gds /path/to/macro.gds}" → list of files
# Example 2: "-gds_files /path/to/design.gds" → single file
# Example 3: "-gds_files {}" → empty (skip)

```

### Detection Logic

**Step 1: File Discovery**
- Scan `${CHECKLIST_ROOT}/IP_project_folder/logs/` for files matching `*LibGen.log` pattern
- Use filename stem (without .LibGen.log extension) as library identifier

**Step 2: Command Extraction**
- For each log file, search for `set_pg_library_mode` commands
- Extract celltype parameter using Pattern 1

**Step 3: Filtering and Reporting Logic**
- Extract GDS files list using Pattern 2 (handles both braced and non-braced formats)
- **Informational Check**: Report ALL libraries with their GDS file status
  - Libraries with GDS files: Report full GDS file path(s)
  - Libraries without GDS files: Report "No GDS files (-gds_files empty or not specified)"
- Include celltype in report for context (macros, stdcells, techonly)
- No filtering - all libraries are reported for user verification

**Step 4: Report Generation**
- Report all libraries found in *LibGen.log files
- For each library, display:
  - Library name (from filename)
  - GDS file configuration status
  - Celltype (macros/stdcells/techonly)
  - Line number where configuration was found
- Output format: Informational report for user manual verification

**Step 5: Status Determination**
- This checker ALWAYS returns PASS status
- Purpose is informational reporting only
- User must manually verify the GDS files configuration is correct
- All libraries reported as INFO items for user review

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `status_check`

**Selected Mode for this checker:** `status_check`

**Rationale:** This checker extracts and reports GDS files from macro power library configurations. It does not validate against a predefined list of expected files (not `existence_check`). Instead, it filters library configurations by celltype and GDS file presence, then reports the found items for user verification. The checker uses `status_check` mode to output only the GDS files that match the filtering criteria (celltype=macros AND gds_files not empty), without performing PASS/FAIL validation.

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
item_desc = "Confirm generate all the power library with detail view correctly."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "Power library GDS files found in LibGen logs"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "Macro power library with GDS detail view validated"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "GDS file found in macro power library configuration"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Macro library configuration matched with GDS detail view"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "No GDS files found for macro power libraries"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Macro power library missing GDS detail view"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "GDS file not found in macro power library configuration"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Macro library configuration missing GDS detail view or filtered out"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "GDS file requirement waived for specific macro libraries"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Macro power library GDS requirement waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries for macro GDS files"
unused_waiver_reason = "Waiver not matched - no corresponding macro library found without GDS files"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [corner_name]: [gds_file_path]"
  Example: "- gpio_ffgnp_0p825v_125c_cbest_CCbest_T: /process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/gds/tphn05_12gpio.gds"

ERROR01 (Violation/Fail items):
  Format: "- [corner_name]: [missing_reason]"
  Example: "- gpio_ffgnp_0p825v_125c_cbest_CCbest_T: Macro library configuration missing GDS detail view or filtered out"
```

Note: Since this checker is informational only (no PASS/FAIL), all valid GDS files are reported in INFO01. ERROR01 would only appear if parsing errors occur or if the checker logic is extended to validate against expected files.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-05:
  description: "Confirm generate all the power library with detail view correctly."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*LibGen.log"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 is an informational-only check that reports all power library GDS file configurations found in LibGen log files. The checker scans all *LibGen.log files, extracts celltype and GDS file information, and reports all libraries with their configuration status. This check ALWAYS returns PASS - all output is informational for user verification.

**Sample Output (PASS - Informational):**
```
Status: PASS
Reason: Power library GDS files found in LibGen logs (informational report)

Log format (CheckList.rpt):
INFO01:
  - gpio_ffgnp_0p825v_125c_cbest_CCbest_T: No GDS files (-gds_files empty or not specified) (celltype=macros)
  - sram_ffgnp_0p825v_125c_cbest_CCbest_T: GDS file configuration found: /process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/GDSII/ts1n05mblvta16384x39m16qwbzhodcp.gds (celltype=macros)
  - stdcell_ffgnp_0p825v_125c_cbest_CCbest_T: No GDS files (-gds_files empty or not specified) (celltype=stdcells)
  - tech_ffgnp_0p825v_125c_cbest_CCbest_T: No GDS files (-gds_files empty or not specified) (celltype=techonly)

Report format (item_id.rpt):
Info Occurrence: 4
1: Info: gpio_ffgnp_0p825v_125c_cbest_CCbest_T. In line 26, gpio_ffgnp_0p825v_125c_cbest_CCbest_T.LibGen.log: No GDS files (-gds_files empty or not specified) (celltype=macros)
2: Info: sram_ffgnp_0p825v_125c_cbest_CCbest_T. In line 26, sram_ffgnp_0p825v_125c_cbest_CCbest_T.LibGen.log: GDS file configuration found: /process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/GDSII/ts1n05mblvta16384x39m16qwbzhodcp.gds (celltype=macros)
3: Info: stdcell_ffgnp_0p825v_125c_cbest_CCbest_T: No GDS files (-gds_files empty or not specified) (celltype=stdcells)
4: Info: tech_ffgnp_0p825v_125c_cbest_CCbest_T: No GDS files (-gds_files empty or not specified) (celltype=techonly)
```

Note: This checker is informational only and does not produce FAIL status. All libraries are reported as INFO items.

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: Macro power libraries. In line N/A, ${CHECKLIST_ROOT}/IP_project_folder/logs/: GDS file not found in macro power library configuration
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-05:
  description: "Confirm generate all the power library with detail view correctly."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*LibGen.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - GDS files are reported for manual verification"
      - "Note: Missing GDS files for macro libraries are acceptable during early development phases"
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
  - "Explanation: This check is informational only - GDS files are reported for manual verification"
  - "Note: Missing GDS files for macro libraries are acceptable during early development phases"
INFO02:
  - No macro libraries with GDS detail views found

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Waiver comment. [WAIVED_INFO]: Explanation: This check is informational only - GDS files are reported for manual verification
2: Info: Macro power libraries. In line N/A, ${CHECKLIST_ROOT}/IP_project_folder/logs/: GDS file not found in macro power library configuration [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-05:
  description: "Confirm generate all the power library with detail view correctly."
  requirements:
    value: 2
    pattern_items:
      - "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/gds/tphn05_12gpio.gds"
      - "/projects/TC70_LPDDR6_N5P/libs/gds/custom_macro.gds"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*LibGen.log"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Description says "confirm generate all the power library with detail view correctly"
- Semantic level: GDS FILE PATHS (complete paths to GDS files)
- ✅ Use complete GDS file paths as they appear in `-gds_files` parameter
- ❌ DO NOT use just filenames: "tphn05_12gpio.gds"
- ❌ DO NOT use directory paths: "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/gds/"

**Check Behavior:**
Type 2 searches for expected GDS file paths in macro power library configurations. The checker extracts GDS files from `set_pg_library_mode -celltype macros` commands and compares against pattern_items. PASS if all expected GDS files are found in at least one macro library configuration; FAIL if any expected GDS file is missing.

**Sample Output (PASS):**
```
Status: PASS
Reason: Macro power library with GDS detail view validated

Log format (CheckList.rpt):
INFO01:
  - /process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/gds/tphn05_12gpio.gds
  - /projects/TC70_LPDDR6_N5P/libs/gds/custom_macro.gds

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: /process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/gds/tphn05_12gpio.gds. In line 15, gpio_ffgnp_0p825v_125c_cbest_CCbest_T.LibGen.log: Macro library configuration matched with GDS detail view
2: Info: /projects/TC70_LPDDR6_N5P/libs/gds/custom_macro.gds. In line 15, gpio_ffgnp_0p825v_m40c_cworst_CCworst_T.LibGen.log: Macro library configuration matched with GDS detail view
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-05:
  description: "Confirm generate all the power library with detail view correctly."
  requirements:
    value: 2
    pattern_items:
      - "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/gds/tphn05_12gpio.gds"
      - "/projects/TC70_LPDDR6_N5P/libs/gds/custom_macro.gds"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*LibGen.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: GDS file verification is informational - missing files acceptable during library development"
      - "Note: Some macro libraries may use abstract views instead of GDS detail views"
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
  - "Explanation: GDS file verification is informational - missing files acceptable during library development"
  - "Note: Some macro libraries may use abstract views instead of GDS detail views"
INFO02:
  - /projects/TC70_LPDDR6_N5P/libs/gds/custom_macro.gds

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Waiver comment. [WAIVED_INFO]: Explanation: GDS file verification is informational - missing files acceptable during library development
2: Info: /projects/TC70_LPDDR6_N5P/libs/gds/custom_macro.gds. In line N/A, ${CHECKLIST_ROOT}/IP_project_folder/logs/: Macro library configuration missing GDS detail view or filtered out [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-05:
  description: "Confirm generate all the power library with detail view correctly."
  requirements:
    value: 2
    pattern_items:
      - "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/gds/tphn05_12gpio.gds"
      - "/projects/TC70_LPDDR6_N5P/libs/gds/custom_macro.gds"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*LibGen.log"
  waivers:
    value: 2
    waive_items:
      - name: "gpio_ffgnp_0p825v_125c_cbest_CCbest_T"
        reason: "Waived - using abstract view for this corner per design team approval"
      - name: "gpio_ffgnp_0p825v_m40c_cworst_CCworst_T"
        reason: "Waived - GDS detail view not required for worst-case corner analysis"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same GDS file path search logic as Type 2, plus waiver classification:
- Match found library corners (missing GDS files) against waive_items by corner name
- Unwaived corners → ERROR (need GDS files added)
- Waived corners → INFO with [WAIVER] tag (approved to skip GDS)
- Unused waivers → WARN with [WAIVER] tag
PASS if all corners missing GDS files are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived

Log format (CheckList.rpt):
INFO01:
  - gpio_ffgnp_0p825v_125c_cbest_CCbest_T
WARN01:
  - gpio_ffgnp_0p825v_m40c_cworst_CCworst_T

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: gpio_ffgnp_0p825v_125c_cbest_CCbest_T. In line 15, gpio_ffgnp_0p825v_125c_cbest_CCbest_T.LibGen.log: Macro power library GDS requirement waived per design team approval: Waived - using abstract view for this corner per design team approval [WAIVER]
Warn Occurrence: 1
1: Warn: gpio_ffgnp_0p825v_m40c_cworst_CCworst_T. In line N/A, waivers: Waiver not matched - no corresponding macro library found without GDS files: Waived - GDS detail view not required for worst-case corner analysis [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-05:
  description: "Confirm generate all the power library with detail view correctly."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*LibGen.log"
  waivers:
    value: 2
    waive_items:
      - name: "gpio_ffgnp_0p825v_125c_cbest_CCbest_T"
        reason: "Waived - using abstract view for this corner per design team approval"
      - name: "gpio_ffgnp_0p825v_m40c_cworst_CCworst_T"
        reason: "Waived - GDS detail view not required for worst-case corner analysis"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (corner names: "gpio_ffgnp_0p825v_125c_cbest_CCbest_T")
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (scans for macro libraries with/without GDS files), plus waiver classification:
- Match violations (corners missing GDS) against waive_items by corner name
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
  - gpio_ffgnp_0p825v_125c_cbest_CCbest_T
WARN01:
  - gpio_ffgnp_0p825v_m40c_cworst_CCworst_T

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: gpio_ffgnp_0p825v_125c_cbest_CCbest_T. In line 15, gpio_ffgnp_0p825v_125c_cbest_CCbest_T.LibGen.log: Macro power library GDS requirement waived per design team approval: Waived - using abstract view for this corner per design team approval [WAIVER]
Warn Occurrence: 1
1: Warn: gpio_ffgnp_0p825v_m40c_cworst_CCworst_T. In line N/A, waivers: Waiver not matched - no corresponding macro library found without GDS files: Waived - GDS detail view not required for worst-case corner analysis [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 11.0_POWER_EMIR_CHECK --checkers IMP-11-0-0-05 --force

# Run individual tests
python IMP-11-0-0-05.py
```

---

## Notes

**Important Considerations:**

1. **Filtering Logic**: The checker implements specific filtering per USER HINTS:
   - Skips files with `celltype` = "techonly" or "stdcells"
   - For `celltype` = "macros", skips if `-gds_files {}` (empty)
   - Only reports GDS files from macro libraries with non-empty GDS lists

2. **No PASS/FAIL Validation**: This checker is informational only. It does not determine PASS or FAIL status based on the presence or absence of GDS files. The output is intended for manual verification by the user.

3. **Corner Identification**: Library corners are identified from log filenames using the pattern:
   `{corner_name}.LibGen.log`

4. **GDS File Paths**: The checker extracts complete file paths from the `-gds_files` parameter. Multiple GDS files may be specified for a single library corner (space-separated within braces).

5. **Sorting**: All GDS file paths are sorted alphabetically before reporting to facilitate manual review and comparison.

6. **Use Cases**:
   - **Type 1/4**: Verify that at least one macro library has GDS detail views
   - **Type 2/3**: Validate specific expected GDS files are present in configurations
   - **waivers.value=0**: Use for informational reporting during development phases
   - **waivers.value>0**: Use to exempt specific corners from GDS requirements

7. **Limitations**:
   - Does not validate GDS file existence on filesystem
   - Does not check GDS file content or format
   - Does not verify GDS layermap consistency
   - Relies on correct command syntax in LibGen logs