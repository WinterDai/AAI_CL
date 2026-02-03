# IMP-11-0-0-06: Confirm use the proper spice model and spice netlist to generate the PGV views.(check the Note)

## Overview

**Check ID:** IMP-11-0-0-06  
**Description:** Confirm use the proper spice model and spice netlist to generate the PGV views.(check the Note)  
**Category:** Power Grid Verification (PGV) Library Generation  
**Input Files:** ${CHECKLIST_ROOT}/IP_project_folder/logs/*LibGen.log

This checker validates that the correct SPICE models and SPICE netlists are used during PGV (Power Grid View) library generation in Voltus LibGen. It extracts and reports the SPICE configuration from `set_pg_library_mode` commands for user verification. The checker filters by celltype (macros/stdcells) and skips techonly cells, then collects all SPICE model and netlist paths for manual review.

**Note:** This is an informational checker with no PASS/FAIL criteria. It provides a sorted report of all SPICE configurations for user double-checking.

---

## Check Logic

### Input Parsing

The checker processes Voltus LibGen log files (`*LibGen.log`) to extract SPICE configuration from `set_pg_library_mode` commands.

**Key Patterns:**

```python
# Pattern 1: Extract celltype from set_pg_library_mode command
celltype_pattern = r'set_pg_library_mode\s+-celltype\s+(\S+)'
# Example: "<CMD> set_pg_library_mode -celltype macros -ground_pins {VSS 0.000} ..."
# Extracted: "macros" or "stdcells" or "techonly"

# Pattern 2: Extract SPICE models path (only if celltype is macros/stdcells)
spice_models_pattern = r'-spice_models\s+(\S+)'
# Example: "... -spice_models /process/tsmcN5/data/g/PDK/tsmc5g.a.13/models/spectre_v1d2_2p5/ir_em.scs ..."
# Extracted: "/process/tsmcN5/data/g/PDK/tsmc5g.a.13/models/spectre_v1d2_2p5/ir_em.scs"

# Pattern 3: Extract SPICE subckts paths (only if celltype is macros/stdcells)
spice_subckts_pattern = r'-spice_subckts\s+\{([^}]+)\}'
# Example: "... -spice_subckts {/process/tsmcN5/data/g/PEGASUS/LVS/current/source.added /process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/lpe_spice/tphn05_12gpio_lpe_cworst_CCworst_T.spi} ..."
# Extracted: "/process/tsmcN5/data/g/PEGASUS/LVS/current/source.added /process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/lpe_spice/tphn05_12gpio_lpe_cworst_CCworst_T.spi"
# Post-processing: Split by whitespace to get individual paths
```

### Detection Logic


1. **Filter by celltype (Pattern 1):**
   - If celltype is "techonly" → Skip this file and continue to next
   - If celltype is "macros" or "stdcells" → Proceed to extract SPICE configuration

2. **Extract SPICE configuration (Patterns 2 & 3):**
   - Extract spice_models path using Pattern 2
   - Extract spice_subckts paths using Pattern 3 (split multiple paths by whitespace)
   - Store with corner name and line number for traceability

3. **Collect and sort results:**
   - Aggregate all spice_models and spice_subckts paths across all files
   - Sort alphabetically for easy review
   - No validation or comparison against expected values

4. **Report for user verification:**
   - Display all collected SPICE configurations
   - User manually verifies correctness based on design requirements
   - No automatic PASS/FAIL determination

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `status_check`

**Selected Mode for this checker:** `status_check`

**Rationale:** This checker extracts SPICE configuration items (models and netlists) from LibGen logs and reports them for user verification. It uses `status_check` mode because:
- The checker identifies specific SPICE configuration items in the logs
- Each item's presence and path are reported for manual validation
- No automatic PASS/FAIL criteria - user must verify correctness
- Items are matched and displayed with their configuration details

However, since there are no predefined pattern_items (no golden reference), this checker operates in informational mode where all found items are reported as INFO for user review.

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
item_desc = "Confirm use the proper spice model and spice netlist to generate the PGV views.(check the Note)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "SPICE configuration found in LibGen logs"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "SPICE configuration extracted for verification"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "SPICE model and netlist paths found in set_pg_library_mode command"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "SPICE configuration extracted and reported for user verification"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "SPICE configuration not found in LibGen logs"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "SPICE configuration missing or incomplete"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "set_pg_library_mode command not found or missing SPICE parameters"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "SPICE model or netlist path not found in set_pg_library_mode command"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "SPICE configuration reported as informational"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "SPICE configuration waived - informational check only"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries for SPICE configuration"
unused_waiver_reason = "Waiver not matched - no corresponding SPICE configuration issue found"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [corner_name] SPICE Model: [model_path], SPICE Netlist: [netlist_path]"
  Example: "- ffgnp_0p825v_125c_cbest_CCbest_T: SPICE Model: /process/tsmcN5/data/g/PDK/tsmc5g.a.13/models/spectre_v1d2_2p5/ir_em.scs, SPICE Netlist: /process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/lpe_spice/tphn05_12gpio_lpe_cworst_CCworst_T.spi"

ERROR01 (Violation/Fail items):
  Format: "- [corner_name]: [missing_reason]"
  Example: "- ffgnp_0p825v_125c_cbest_CCbest_T: SPICE model or netlist path not found in set_pg_library_mode command"
```

Note: Since this is an informational checker with no PASS/FAIL criteria, all extracted configurations are reported as INFO01 for user verification. ERROR01 is only used if parsing fails or required patterns are not found in the log files.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-06:
  description: "Confirm use the proper spice model and spice netlist to generate the PGV views.(check the Note)"
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
Type 1 performs custom boolean checks to verify SPICE configuration exists in LibGen logs.
- Searches for `set_pg_library_mode` commands with celltype macros/stdcells
- Extracts SPICE models and netlists paths
- Reports all findings as INFO (no PASS/FAIL validation)
- User manually verifies correctness of extracted paths

**Sample Output (PASS):**
```
Status: PASS
Reason: SPICE model and netlist paths found in set_pg_library_mode command

Log format (CheckList.rpt):
INFO01:
  - ffgnp_0p825v_125c_cbest_CCbest_T: SPICE Model: /process/tsmcN5/data/g/PDK/tsmc5g.a.13/models/spectre_v1d2_2p5/ir_em.scs, SPICE Netlist: /process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/lpe_spice/tphn05_12gpio_lpe_cworst_CCworst_T.spi
  - rcss_0p675v_125c_cworst_CCworst_T: SPICE Model: /process/tsmcN5/data/g/PDK/tsmc5g.a.13/models/spectre_v1d2_2p5/ir_em.scs, SPICE Netlist: /process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/lpe_spice/tphn05_12gpio_lpe_cworst_CCworst_T.spi

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: ffgnp_0p825v_125c_cbest_CCbest_T. In line 45, gpio_ffgnp_0p825v_125c_cbest_CCbest_T.LibGen.log: SPICE configuration extracted and reported for user verification
2: Info: rcss_0p675v_125c_cworst_CCworst_T. In line 52, gpio_rcss_0p675v_125c_cworst_CCworst_T.LibGen.log: SPICE configuration extracted and reported for user verification
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: set_pg_library_mode command not found or missing SPICE parameters

Log format (CheckList.rpt):
ERROR01:
  - ffgnp_0p825v_125c_cbest_CCbest_T: Missing SPICE configuration

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: ffgnp_0p825v_125c_cbest_CCbest_T. In line 0, gpio_ffgnp_0p825v_125c_cbest_CCbest_T.LibGen.log: SPICE model or netlist path not found in set_pg_library_mode command
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-06:
  description: "Confirm use the proper spice model and spice netlist to generate the PGV views.(check the Note)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*LibGen.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - no automatic validation performed"
      - "Note: User must manually verify SPICE model and netlist paths match design requirements"
      - "Action: Review extracted paths and confirm they point to correct process corner files"
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
  - "Explanation: This check is informational only - no automatic validation performed"
  - "Note: User must manually verify SPICE model and netlist paths match design requirements"
  - "Action: Review extracted paths and confirm they point to correct process corner files"
INFO02:
  - ffgnp_0p825v_125c_cbest_CCbest_T: SPICE Model: /process/tsmcN5/data/g/PDK/tsmc5g.a.13/models/spectre_v1d2_2p5/ir_em.scs, SPICE Netlist: /process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/lpe_spice/tphn05_12gpio_lpe_cworst_CCworst_T.spi

Report format (item_id.rpt):
Info Occurrence: 4
1: Info: Explanation: This check is informational only - no automatic validation performed. [WAIVED_INFO]
2: Info: Note: User must manually verify SPICE model and netlist paths match design requirements. [WAIVED_INFO]
3: Info: Action: Review extracted paths and confirm they point to correct process corner files. [WAIVED_INFO]
4: Info: ffgnp_0p825v_125c_cbest_CCbest_T. In line 45, gpio_ffgnp_0p825v_125c_cbest_CCbest_T.LibGen.log: SPICE configuration extracted and reported for user verification [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-06:
  description: "Confirm use the proper spice model and spice netlist to generate the PGV views.(check the Note)"
  requirements:
    value: 2  # ⚠️ CRITICAL: MUST equal len(pattern_items)
    pattern_items:
      - "/process/tsmcN5/data/g/PDK/tsmc5g.a.13/models/spectre_v1d2_2p5/ir_em.scs"  # Expected SPICE model path
      - "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/lpe_spice/tphn05_12gpio_lpe_cworst_CCworst_T.spi"  # Expected SPICE netlist path
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*LibGen.log"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Description requires "spice model and spice netlist" paths
- Use COMPLETE FILE PATHS as they appear in set_pg_library_mode command
- Pattern items represent expected/golden SPICE configuration paths
- Checker validates that extracted paths match these expected values

**Check Behavior:**
Type 2 searches pattern_items (expected SPICE paths) in LibGen log files.
- Extracts actual SPICE model and netlist paths from set_pg_library_mode commands
- Compares extracted paths against pattern_items (golden values)
- PASS if all pattern_items found (all expected paths are used)
- FAIL if any pattern_items missing (some expected paths not found)

**Sample Output (PASS):**
```
Status: PASS
Reason: SPICE configuration extracted and reported for user verification

Log format (CheckList.rpt):
INFO01:
  - /process/tsmcN5/data/g/PDK/tsmc5g.a.13/models/spectre_v1d2_2p5/ir_em.scs
  - /process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/lpe_spice/tphn05_12gpio_lpe_cworst_CCworst_T.spi

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: /process/tsmcN5/data/g/PDK/tsmc5g.a.13/models/spectre_v1d2_2p5/ir_em.scs. In line 45, gpio_ffgnp_0p825v_125c_cbest_CCbest_T.LibGen.log: SPICE configuration extracted and reported for user verification
2: Info: /process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/lpe_spice/tphn05_12gpio_lpe_cworst_CCworst_T.spi. In line 45, gpio_ffgnp_0p825v_125c_cbest_CCbest_T.LibGen.log: SPICE configuration extracted and reported for user verification
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-06:
  description: "Confirm use the proper spice model and spice netlist to generate the PGV views.(check the Note)"
  requirements:
    value: 2
    pattern_items:
      - "/process/tsmcN5/data/g/PDK/tsmc5g.a.13/models/spectre_v1d2_2p5/ir_em.scs"
      - "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/lpe_spice/tphn05_12gpio_lpe_cworst_CCworst_T.spi"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*LibGen.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: SPICE path validation is informational - paths extracted for manual review"
      - "Note: Different SPICE models/netlists may be used for different process corners"
      - "Action: Verify extracted paths match your design's process corner requirements"
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
  - "Explanation: SPICE path validation is informational - paths extracted for manual review"
  - "Note: Different SPICE models/netlists may be used for different process corners"
  - "Action: Verify extracted paths match your design's process corner requirements"
INFO02:
  - /process/tsmcN5/data/g/PDK/tsmc5g.a.13/models/spectre_v1d2_2p5/ir_em.scs
  - /process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/lpe_spice/tphn05_12gpio_lpe_cbest_CCbest_T.spi

Report format (item_id.rpt):
Info Occurrence: 5
1: Info: Explanation: SPICE path validation is informational - paths extracted for manual review. [WAIVED_INFO]
2: Info: Note: Different SPICE models/netlists may be used for different process corners. [WAIVED_INFO]
3: Info: Action: Verify extracted paths match your design's process corner requirements. [WAIVED_INFO]
4: Info: /process/tsmcN5/data/g/PDK/tsmc5g.a.13/models/spectre_v1d2_2p5/ir_em.scs. In line 45, gpio_ffgnp_0p825v_125c_cbest_CCbest_T.LibGen.log: SPICE configuration extracted and reported for user verification [WAIVED_AS_INFO]
5: Info: /process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/lpe_spice/tphn05_12gpio_lpe_cbest_CCbest_T.spi. In line 45, gpio_ffgnp_0p825v_125c_cbest_CCbest_T.LibGen.log: SPICE configuration extracted and reported for user verification [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-06:
  description: "Confirm use the proper spice model and spice netlist to generate the PGV views.(check the Note)"
  requirements:
    value: 2  # ⚠️ CRITICAL: MUST equal len(pattern_items)
    pattern_items:
      - "/process/tsmcN5/data/g/PDK/tsmc5g.a.13/models/spectre_v1d2_2p5/ir_em.scs"  # GOLDEN VALUE: Expected SPICE model path
      - "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/lpe_spice/tphn05_12gpio_lpe_cworst_CCworst_T.spi"  # GOLDEN VALUE: Expected SPICE netlist path
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*LibGen.log"
  waivers:
    value: 2
    waive_items:
      - name: "ffgnp_0p825v_125c_cbest_CCbest_T"  # EXEMPTION: Corner name using alternative SPICE files
        reason: "Waived - using alternative SPICE model for fast corner per design team approval"
      - name: "rcss_0p675v_m40c_cworst_CCworst_T"  # EXEMPTION: Corner name using legacy SPICE netlist
        reason: "Waived - legacy SPICE netlist approved for low voltage corner"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Extract SPICE paths from LibGen logs (identified by corner name)
- Compare extracted paths against pattern_items (golden SPICE paths)
- If path doesn't match golden value → check if corner name is in waive_items
- Match: found_item['name'] (corner name) == waive_item['name']
- Unwaived mismatches → ERROR (need fix)
- Waived mismatches → INFO with [WAIVER] tag (approved exception)
- Unused waivers → WARN with [WAIVER] tag
- PASS if all mismatches are waived

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived

Log format (CheckList.rpt):
INFO01:
  - ffgnp_0p825v_125c_cbest_CCbest_T
  - rcss_0p675v_m40c_cworst_CCworst_T
WARN01:
  - unused_corner_waiver

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: ffgnp_0p825v_125c_cbest_CCbest_T. In line 45, gpio_ffgnp_0p825v_125c_cbest_CCbest_T.LibGen.log: SPICE configuration waived - informational check only: Waived - using alternative SPICE model for fast corner per design team approval [WAIVER]
2: Info: rcss_0p675v_m40c_cworst_CCworst_T. In line 52, gpio_rcss_0p675v_m40c_cworst_CCworst_T.LibGen.log: SPICE configuration waived - informational check only: Waived - legacy SPICE netlist approved for low voltage corner [WAIVER]
Warn Occurrence: 1
1: Warn: unused_corner_waiver. In line 0, N/A: Waiver not matched - no corresponding SPICE configuration issue found: [waiver reason from config] [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-06:
  description: "Confirm use the proper spice model and spice netlist to generate the PGV views.(check the Note)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/*LibGen.log"
  waivers:
    value: 2
    waive_items:
      - name: "ffgnp_0p825v_125c_cbest_CCbest_T"  # ⚠️ MUST match Type 3 waive_items
        reason: "Waived - using alternative SPICE model for fast corner per design team approval"
      - name: "rcss_0p675v_m40c_cworst_CCworst_T"  # ⚠️ MUST match Type 3 waive_items
        reason: "Waived - legacy SPICE netlist approved for low voltage corner"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (corner names with SPICE issues)
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (extract SPICE configs, no pattern validation), plus waiver classification:
- Extract SPICE configurations from all LibGen logs
- Identify corners with missing or incomplete SPICE settings
- Match violations (corner names) against waive_items
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
- PASS if all violations are waived

**Sample Output:**
```
Status: PASS
Reason: All items waived

Log format (CheckList.rpt):
INFO01:
  - ffgnp_0p825v_125c_cbest_CCbest_T
  - rcss_0p675v_m40c_cworst_CCworst_T
WARN01:
  - unused_corner_waiver

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: ffgnp_0p825v_125c_cbest_CCbest_T. In line 45, gpio_ffgnp_0p825v_125c_cbest_CCbest_T.LibGen.log: SPICE configuration waived - informational check only: Waived - using alternative SPICE model for fast corner per design team approval [WAIVER]
2: Info: rcss_0p675v_m40c_cworst_CCworst_T. In line 52, gpio_rcss_0p675v_m40c_cworst_CCworst_T.LibGen.log: SPICE configuration waived - informational check only: Waived - legacy SPICE netlist approved for low voltage corner [WAIVER]
Warn Occurrence: 1
1: Warn: unused_corner_waiver. In line 0, N/A: Waiver not matched - no corresponding SPICE configuration issue found: [waiver reason from config] [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 11.0_POWER_EMIR_CHECK --checkers IMP-11-0-0-06 --force

# Run individual tests
python IMP-11-0-0-06.py
```

---

## Notes

**Important Considerations:**

1. **Informational Check:** This checker has no automatic PASS/FAIL validation. It extracts and reports SPICE configurations for manual user verification.

2. **Celltype Filtering:** Only processes `set_pg_library_mode` commands with celltype "macros" or "stdcells". Commands with celltype "techonly" are skipped.

3. **Multiple SPICE Netlists:** The `-spice_subckts` parameter can contain multiple paths separated by whitespace. All paths are extracted and reported individually.

4. **Corner Identification:** Corner information is extracted from the LibGen log filename to provide context for each SPICE configuration.

5. **Sorted Output:** All SPICE model and netlist paths are sorted alphabetically in the final report for easier review.

6. **Manual Verification Required:** Users must manually verify that:
   - SPICE model paths point to correct process corner models
   - SPICE netlist paths match the design's RC corner requirements
   - Temperature settings align with corner specifications
   - All required corners have proper SPICE configurations

7. **No Golden Reference:** Unlike typical Type 2/3 checks, this checker does not validate against predefined golden values. It simply extracts and reports what is configured in the LibGen commands.

8. **Traceability:** Each reported item includes line number and filename for easy traceability back to the source LibGen log.