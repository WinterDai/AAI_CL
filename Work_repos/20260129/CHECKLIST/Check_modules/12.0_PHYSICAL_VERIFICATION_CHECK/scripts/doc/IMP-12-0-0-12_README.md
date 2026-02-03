# IMP-12-0-0-12: Confirm the MIM related check is clean. (Need to check and Fill N/A if no MIMCAP inserted or no MIM related layers in PHY or SOC level) - If PHY needs to insert MIMCAP. 1. Need to pay attention to the MIMCAP KOZ rule during MIMCAP insertion after check with customer about the SOC die size, substrate layer number and PHY placement/location in SOC level. 2. Pay attention to the option setting related to MIM DRC check like KOZ_High_subst_layer, SHDMIM_KOZ_AP_SPACE_5um(on/off will impact the checking rule) etc in TSMC rule deck(need to align these settings with customer). -If PHY doesn't insert MIMCAP but SOC level inserts MIMCAP. 1. Need to open SHDMIM switching in DRC rule deck. 2. Need to check with customer whether PHY need to meet SHDMIM_KOZ_AP_SPACE_5um rule (if SOC level this DRC switching setting is ON) in PHY area which falls into SOC KOZ area for TSMC process. 3. May need to insert MIM dummy in PHY level to meet SOC level MIM dummy density rule (you can sync with customer whether PHY MIM dummy is needed and the KOZ information on PHY to make sure there is no dummy added in KOZ area on PHY by adding MIM EXCL layer).

## Overview

**Check ID:** IMP-12-0-0-12  
**Description:** Confirm the MIM related check is clean. (Need to check and Fill N/A if no MIMCAP inserted or no MIM related layers in PHY or SOC level) - If PHY needs to insert MIMCAP. 1. Need to pay attention to the MIMCAP KOZ rule during MIMCAP insertion after check with customer about the SOC die size, substrate layer number and PHY placement/location in SOC level. 2. Pay attention to the option setting related to MIM DRC check like KOZ_High_subst_layer, SHDMIM_KOZ_AP_SPACE_5um(on/off will impact the checking rule) etc in TSMC rule deck(need to align these settings with customer). -If PHY doesn't insert MIMCAP but SOC level inserts MIMCAP. 1. Need to open SHDMIM switching in DRC rule deck. 2. Need to check with customer whether PHY need to meet SHDMIM_KOZ_AP_SPACE_5um rule (if SOC level this DRC switching setting is ON) in PHY area which falls into SOC KOZ area for TSMC process. 3. May need to insert MIM dummy in PHY level to meet SOC level MIM dummy density rule (you can sync with customer whether PHY MIM dummy is needed and the KOZ information on PHY to make sure there is no dummy added in KOZ area on PHY by adding MIM EXCL layer).  
**Category:** Physical Verification - MIM (Metal-Insulator-Metal) Capacitor DRC Check  
**Input Files:** 
- `${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_ANTMIM.rep` (Calibre DRC-H summary report for MIM antenna checks)
- `${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_ANTMIM.rep` (Pegasus DRC summary report for MIM antenna checks)

This checker validates that MIM-related DRC checks are clean by parsing Calibre and/or Pegasus physical verification reports. It extracts MIM rule violations, determines if MIMCAP layers are present in the design, and reports the overall MIM check status. The checker supports three outcomes: CLEAN (no violations), FAIL (violations found), or N/A (no MIMCAP inserted).

---

## Check Logic

### Input Parsing

The checker supports two types of physical verification reports:

**1. Calibre Report Format:**
- Header section: Extract metadata (design name, rule file, execution date, tool version)
- Layer statistics section: Identify MIM-related layers (MPC, BPC, MPC_O, BPC_O, TPCDMY_AP2) and their geometry counts
- Rulecheck results section: Extract MIM rule violations with counts

**2. Pegasus Report Format:**
- Header section: Extract metadata (design name, rule deck path, execution date, tool version)
- Layer statistics section: Identify MIM-related layers (MPC, TPC, BPC, MPC_O, TPC_O, BPC_O, TPCDMY_AP) and their geometry counts
- Rulecheck results section: Extract MIM rule violations with counts

**Key Patterns:**

```python
# Pattern 1: Calibre RULECHECK results
calibre_rulecheck = r'^RULECHECK\s+(MIM\.[A-Z]\.R\.[\d\.]+(?::[A-Z]+)?)\s+\.+\s+TOTAL Result Count\s+=\s+(\d+)\s+\((\d+)\)'
# Example: "RULECHECK MIM.A.R.1.1 ....... TOTAL Result Count = 0 (0)"
# Example: "RULECHECK MIM.A.R.6.1:BPC ... TOTAL Result Count = 0 (0)"

# Pattern 2: Pegasus RULECHECK results (per user hint)
pegasus_rulecheck = r'^RULECHECK\s+([\w\.\:]+)\s+\.+\s+Total Result\s+(\d+)\s+\(\s*(\d+)\)'
# Example: "RULECHECK A.R.18.2:VIA4 ................................ Total Result          0 (         0)"
# Example: "RULECHECK MIM.A.R.1 .................................... Total Result          0 (         0)"

# Pattern 3: Calibre MIM layer statistics
calibre_layer = r'^LAYER\s+((?:MPC|BPC|MPC_O|BPC_O|TPCDMY_AP2))\s+\.+\s+TOTAL Original Geometry Count\s+=\s+(\d+)\s+\((\d+)\)'
# Example: "LAYER MPC .......... TOTAL Original Geometry Count = 0        (0)"
# Example: "LAYER BPC_O ........ TOTAL Original Geometry Count = 0        (0)"

# Pattern 4: Pegasus MIM layer statistics
pegasus_layer = r'^LAYER\s+(MPC|TPC|BPC|MPC_O|TPC_O|BPC_O|TPCDMY_AP)\s+\.+\s+Total Original Geometry:\s+(\d+)\s+\(\s*(\d+)\)'
# Example: "LAYER MPC .................................. Total Original Geometry:        141 (       943)"

# Pattern 5: File metadata extraction (both formats)
metadata = r'^(Layout Primary Cell|Rule File Pathname|Execution Date/Time|Calibre Version|Execute on Date/Time|Pegasus VERSION|Rule Deck Path):\s+(.+)$'
# Example: "Execution Date/Time:       Thu Aug 31 18:15:50 2023"
# Example: "Execute on Date/Time    : 2026-01-06 20:36:18"
```

### Detection Logic

**Step 1: Determine Report Type**
- Detect if report is Calibre (contains "Calibre Version") or Pegasus (contains "Pegasus VERSION")
- Select appropriate regex patterns based on report type

**Step 2: Extract MIM Layer Presence**
- Parse layer statistics section
- Check if any MIM-related layers (MPC, TPC, BPC, etc.) have geometry_count > 0
- If all MIM layers have 0 geometries → Set status to "N/A - No MIMCAP inserted"

**Step 3: Extract MIM Rule Violations**
- Parse rulecheck results section
- For each RULECHECK line matching MIM patterns:
  - Extract rule_name (e.g., "MIM.A.R.1.1", "A.R.18.2:VIA4")
  - Extract violation_count (primary count)
  - If violation_count > 0 → Add to violations list

**Step 4: Determine Overall Status**
- If no MIM layers present (all geometry counts = 0) → Return "N/A"
- If MIM layers present AND all violation_counts = 0 → Return "PASS"
- If any violation_count > 0 → Return "FAIL"

**Step 5: Multi-File Aggregation**
- Process each report file independently
- Aggregate violations across all files
- Overall status = FAIL if ANY file has violations, PASS if all clean, N/A if no MIM in any file

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

**Rationale:** This checker validates the STATUS of MIM DRC rules (clean vs violations). The pattern_items represent specific MIM rules to check, and the checker reports whether each rule has violations (status wrong) or is clean (status correct). Rules not in pattern_items are not reported. This is a status validation check, not an existence check.

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
item_desc = "Confirm the MIM related check is clean. (Need to check and Fill N/A if no MIMCAP inserted or no MIM related layers in PHY or SOC level) - If PHY needs to insert MIMCAP. 1. Need to pay attention to the MIMCAP KOZ rule during MIMCAP insertion after check with customer about the SOC die size, substrate layer number and PHY placement/location in SOC level. 2. Pay attention to the option setting related to MIM DRC check like KOZ_High_subst_layer, SHDMIM_KOZ_AP_SPACE_5um(on/off will impact the checking rule) etc in TSMC rule deck(need to align these settings with customer). -If PHY doesn't insert MIMCAP but SOC level inserts MIMCAP. 1. Need to open SHDMIM switching in DRC rule deck. 2. Need to check with customer whether PHY need to meet SHDMIM_KOZ_AP_SPACE_5um rule (if SOC level this DRC switching setting is ON) in PHY area which falls into SOC KOZ area for TSMC process. 3. May need to insert MIM dummy in PHY level to meet SOC level MIM dummy density rule (you can sync with customer whether PHY MIM dummy is needed and the KOZ information on PHY to make sure there is no dummy added in KOZ area on PHY by adding MIM EXCL layer)."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "All MIM DRC checks are clean - no violations found in physical verification reports"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All specified MIM rules are clean - no violations detected"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "MIM DRC verification complete - all checks passed with 0 violations"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All specified MIM rules validated and satisfied - 0 violations across all checks"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "MIM DRC violations detected in physical verification reports"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "MIM rule violations found - specified rules not satisfied"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "MIM DRC check failed - violations found in one or more reports"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "MIM rule requirements not satisfied - violations detected in specified rules"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "MIM DRC violations waived per design team approval"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "MIM violation waived - approved by physical verification team"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused MIM waiver entries - no corresponding violations found"
unused_waiver_reason = "Waiver entry not matched - specified MIM rule has no violations in current reports"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "[Report_Type] [Rule_Name]: 0 violations (CLEAN)"
  Example: "Calibre MIM.A.R.1.1: 0 violations (CLEAN)"
  Example: "Pegasus A.R.18.2:VIA4: 0 violations (CLEAN)"
  Example: "N/A - No MIMCAP inserted (all MIM layers have 0 geometries)"

ERROR01 (Violation/Fail items):
  Format: "[Report_Type] [Rule_Name]: [violation_count] violations"
  Example: "Calibre MIM.A.R.6.1:BPC: 5 violations"
  Example: "Pegasus MIM.A.R.9.1:MPC: 12 violations"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-12:
  description: "Confirm the MIM related check is clean. (Need to check and Fill N/A if no MIMCAP inserted or no MIM related layers in PHY or SOC level) - If PHY needs to insert MIMCAP. 1. Need to pay attention to the MIMCAP KOZ rule during MIMCAP insertion after check with customer about the SOC die size, substrate layer number and PHY placement/location in SOC level. 2. Pay attention to the option setting related to MIM DRC check like KOZ_High_subst_layer, SHDMIM_KOZ_AP_SPACE_5um(on/off will impact the checking rule) etc in TSMC rule deck(need to align these settings with customer). -If PHY doesn't insert MIMCAP but SOC level inserts MIMCAP. 1. Need to open SHDMIM switching in DRC rule deck. 2. Need to check with customer whether PHY need to meet SHDMIM_KOZ_AP_SPACE_5um rule (if SOC level this DRC switching setting is ON) in PHY area which falls into SOC KOZ area for TSMC process. 3. May need to insert MIM dummy in PHY level to meet SOC level MIM dummy density rule (you can sync with customer whether PHY MIM dummy is needed and the KOZ information on PHY to make sure there is no dummy added in KOZ area on PHY by adding MIM EXCL layer)."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_ANTMIM.rep
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_ANTMIM.rep
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
Reason: MIM DRC verification complete - all checks passed with 0 violations
INFO01:
  - Calibre MIM.A.R.1.1: 0 violations (CLEAN)
  - Calibre MIM.A.R.6.1:BPC: 0 violations (CLEAN)
  - Pegasus MIM.A.R.1: 0 violations (CLEAN)
  - Total MIM checks: 9 | Total violations: 0
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: MIM DRC check failed - violations found in one or more reports
ERROR01:
  - Calibre MIM.A.R.6.1:BPC: 5 violations
  - Pegasus MIM.A.R.9.1:MPC: 12 violations
  - Total MIM checks: 9 | Total violations: 17
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-12:
  description: "Confirm the MIM related check is clean. (Need to check and Fill N/A if no MIMCAP inserted or no MIM related layers in PHY or SOC level) - If PHY needs to insert MIMCAP. 1. Need to pay attention to the MIMCAP KOZ rule during MIMCAP insertion after check with customer about the SOC die size, substrate layer number and PHY placement/location in SOC level. 2. Pay attention to the option setting related to MIM DRC check like KOZ_High_subst_layer, SHDMIM_KOZ_AP_SPACE_5um(on/off will impact the checking rule) etc in TSMC rule deck(need to align these settings with customer). -If PHY doesn't insert MIMCAP but SOC level inserts MIMCAP. 1. Need to open SHDMIM switching in DRC rule deck. 2. Need to check with customer whether PHY need to meet SHDMIM_KOZ_AP_SPACE_5um rule (if SOC level this DRC switching setting is ON) in PHY area which falls into SOC KOZ area for TSMC process. 3. May need to insert MIM dummy in PHY level to meet SOC level MIM dummy density rule (you can sync with customer whether PHY MIM dummy is needed and the KOZ information on PHY to make sure there is no dummy added in KOZ area on PHY by adding MIM EXCL layer)."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_ANTMIM.rep
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_ANTMIM.rep
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: MIM violations are informational only during early design phase"
      - "Note: MIMCAP insertion is optional for this PHY - violations expected if SOC-level MIMCAP used"
      - "Context: Design team confirmed MIM dummy density will be addressed at SOC integration"
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
  - "Explanation: MIM violations are informational only during early design phase"
  - "Note: MIMCAP insertion is optional for this PHY - violations expected if SOC-level MIMCAP used"
  - "Context: Design team confirmed MIM dummy density will be addressed at SOC integration"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - Calibre MIM.A.R.6.1:BPC: 5 violations [WAIVED_AS_INFO]
  - Pegasus MIM.A.R.9.1:MPC: 12 violations [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-12:
  description: "Confirm the MIM related check is clean. (Need to check and Fill N/A if no MIMCAP inserted or no MIM related layers in PHY or SOC level) - If PHY needs to insert MIMCAP. 1. Need to pay attention to the MIMCAP KOZ rule during MIMCAP insertion after check with customer about the SOC die size, substrate layer number and PHY placement/location in SOC level. 2. Pay attention to the option setting related to MIM DRC check like KOZ_High_subst_layer, SHDMIM_KOZ_AP_SPACE_5um(on/off will impact the checking rule) etc in TSMC rule deck(need to align these settings with customer). -If PHY doesn't insert MIMCAP but SOC level inserts MIMCAP. 1. Need to open SHDMIM switching in DRC rule deck. 2. Need to check with customer whether PHY need to meet SHDMIM_KOZ_AP_SPACE_5um rule (if SOC level this DRC switching setting is ON) in PHY area which falls into SOC KOZ area for TSMC process. 3. May need to insert MIM dummy in PHY level to meet SOC level MIM dummy density rule (you can sync with customer whether PHY MIM dummy is needed and the KOZ information on PHY to make sure there is no dummy added in KOZ area on PHY by adding MIM EXCL layer)."
  requirements:
    value: 3
    pattern_items:
      - "MIM.A.R.1.1"
      - "MIM.A.R.6.1:BPC"
      - "A.R.18.2:VIA4"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_ANTMIM.rep
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_ANTMIM.rep
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
Reason: All specified MIM rules validated and satisfied - 0 violations across all checks
INFO01:
  - Calibre MIM.A.R.1.1: 0 violations (CLEAN)
  - Calibre MIM.A.R.6.1:BPC: 0 violations (CLEAN)
  - Pegasus A.R.18.2:VIA4: 0 violations (CLEAN)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-12:
  description: "Confirm the MIM related check is clean. (Need to check and Fill N/A if no MIMCAP inserted or no MIM related layers in PHY or SOC level) - If PHY needs to insert MIMCAP. 1. Need to pay attention to the MIMCAP KOZ rule during MIMCAP insertion after check with customer about the SOC die size, substrate layer number and PHY placement/location in SOC level. 2. Pay attention to the option setting related to MIM DRC check like KOZ_High_subst_layer, SHDMIM_KOZ_AP_SPACE_5um(on/off will impact the checking rule) etc in TSMC rule deck(need to align these settings with customer). -If PHY doesn't insert MIMCAP but SOC level inserts MIMCAP. 1. Need to open SHDMIM switching in DRC rule deck. 2. Need to check with customer whether PHY need to meet SHDMIM_KOZ_AP_SPACE_5um rule (if SOC level this DRC switching setting is ON) in PHY area which falls into SOC KOZ area for TSMC process. 3. May need to insert MIM dummy in PHY level to meet SOC level MIM dummy density rule (you can sync with customer whether PHY MIM dummy is needed and the KOZ information on PHY to make sure there is no dummy added in KOZ area on PHY by adding MIM EXCL layer)."
  requirements:
    value: 3
    pattern_items:
      - "MIM.A.R.1.1"
      - "MIM.A.R.6.1:BPC"
      - "A.R.18.2:VIA4"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_ANTMIM.rep
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_ANTMIM.rep
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: MIM rule violations are informational during pre-tapeout verification"
      - "Note: These specific rules will be addressed during final SOC-level integration"
      - "Context: Customer confirmed MIMCAP KOZ settings will be finalized after die size confirmation"
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
  - "Explanation: MIM rule violations are informational during pre-tapeout verification"
  - "Note: These specific rules will be addressed during final SOC-level integration"
  - "Context: Customer confirmed MIMCAP KOZ settings will be finalized after die size confirmation"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - Calibre MIM.A.R.6.1:BPC: 5 violations [WAIVED_AS_INFO]
  - Pegasus A.R.18.2:VIA4: 3 violations [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-12:
  description: "Confirm the MIM related check is clean. (Need to check and Fill N/A if no MIMCAP inserted or no MIM related layers in PHY or SOC level) - If PHY needs to insert MIMCAP. 1. Need to pay attention to the MIMCAP KOZ rule during MIMCAP insertion after check with customer about the SOC die size, substrate layer number and PHY placement/location in SOC level. 2. Pay attention to the option setting related to MIM DRC check like KOZ_High_subst_layer, SHDMIM_KOZ_AP_SPACE_5um(on/off will impact the checking rule) etc in TSMC rule deck(need to align these settings with customer). -If PHY doesn't insert MIMCAP but SOC level inserts MIMCAP. 1. Need to open SHDMIM switching in DRC rule deck. 2. Need to check with customer whether PHY need to meet SHDMIM_KOZ_AP_SPACE_5um rule (if SOC level this DRC switching setting is ON) in PHY area which falls into SOC KOZ area for TSMC process. 3. May need to insert MIM dummy in PHY level to meet SOC level MIM dummy density rule (you can sync with customer whether PHY MIM dummy is needed and the KOZ information on PHY to make sure there is no dummy added in KOZ area on PHY by adding MIM EXCL layer)."
  requirements:
    value: 3
    pattern_items:
      - "MIM.A.R.1.1"
      - "MIM.A.R.6.1:BPC"
      - "A.R.18.2:VIA4"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_ANTMIM.rep
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_ANTMIM.rep
  waivers:
    value: 2
    waive_items:
      - name: "MIM.A.R.6.1:BPC"
        reason: "Waived - BPC layer violations acceptable per customer agreement for this design phase"
      - name: "A.R.18.2:VIA4"
        reason: "Waived - VIA4 antenna violations will be resolved during SOC-level MIMCAP insertion"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:
- BOTH must be at SAME semantic level as description!
- If description contains "version": 
  ✅ pattern_items: ["22.11-s119_1", "23.10-s200"] (version identifiers)
  ✅ waive_items.name: "22.11-s119_1" (same level as pattern_items)
  ❌ DO NOT mix: pattern_items="innovus/22.11-s119" (path) with waive_items.name="22.11-s119" (version)
- If description contains "filename":
  ✅ pattern_items: ["design.v", "top.v"] (filenames)
  ✅ waive_items.name: "design.v" (same level as pattern_items)

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
  - Calibre MIM.A.R.6.1:BPC: 5 violations [WAIVER]
  - Pegasus A.R.18.2:VIA4: 3 violations [WAIVER]
WARN01 (Unused Waivers):
  - MIM.A.R.1.1: Waiver entry not matched - specified MIM rule has no violations in current reports
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-12:
  description: "Confirm the MIM related check is clean. (Need to check and Fill N/A if no MIMCAP inserted or no MIM related layers in PHY or SOC level) - If PHY needs to insert MIMCAP. 1. Need to pay attention to the MIMCAP KOZ rule during MIMCAP insertion after check with customer about the SOC die size, substrate layer number and PHY placement/location in SOC level. 2. Pay attention to the option setting related to MIM DRC check like KOZ_High_subst_layer, SHDMIM_KOZ_AP_SPACE_5um(on/off will impact the checking rule) etc in TSMC rule deck(need to align these settings with customer). -If PHY doesn't insert MIMCAP but SOC level inserts MIMCAP. 1. Need to open SHDMIM switching in DRC rule deck. 2. Need to check with customer whether PHY need to meet SHDMIM_KOZ_AP_SPACE_5um rule (if SOC level this DRC switching setting is ON) in PHY area which falls into SOC KOZ area for TSMC process. 3. May need to insert MIM dummy in PHY level to meet SOC level MIM dummy density rule (you can sync with customer whether PHY MIM dummy is needed and the KOZ information on PHY to make sure there is no dummy added in KOZ area on PHY by adding MIM EXCL layer)."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_ANTMIM.rep
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Pegasus_ANTMIM.rep
  waivers:
    value: 2
    waive_items:
      - name: "MIM.A.R.6.1:BPC"
        reason: "Waived - BPC layer violations acceptable per customer agreement for this design phase"
      - name: "A.R.18.2:VIA4"
        reason: "Waived - VIA4 antenna violations will be resolved during SOC-level MIMCAP insertion"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3
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
  - Calibre MIM.A.R.6.1:BPC: 5 violations [WAIVER]
  - Pegasus A.R.18.2:VIA4: 3 violations [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 12.0_PHYSICAL_VERIFICATION_CHECK --checkers IMP-12-0-0-12 --force

# Run individual tests
python IMP-12-0-0-12.py
```

---

## Notes

**Special Handling for N/A Status:**
- If all MIM-related layers (MPC, TPC, BPC, MPC_O, TPC_O, BPC_O, TPCDMY_AP, TPCDMY_AP2) have 0 geometries across all reports, the checker returns "N/A - No MIMCAP inserted"
- This distinguishes between "no MIM layers present" (N/A) vs "MIM layers present with 0 violations" (CLEAN)

**Multi-Report Support:**
- Checker processes both Calibre and Pegasus reports in a single run
- Violations are aggregated across all input files
- Overall status is FAIL if ANY report contains violations

**Rule Name Variations:**
- Calibre format: "MIM.A.R.1.1", "MIM.A.R.6.1:BPC"
- Pegasus format: "MIM.A.R.1", "A.R.18.2:VIA4"
- Checker handles both formats and extracts rule names accordingly

**Known Limitations:**
- Checker assumes standard Calibre/Pegasus report formats - custom report formats may require pattern adjustments
- Secondary count in parentheses (e.g., "(0)") is currently ignored but could be used for vertex count validation
- Metadata extraction is optional - checker focuses on violation counts for PASS/FAIL determination