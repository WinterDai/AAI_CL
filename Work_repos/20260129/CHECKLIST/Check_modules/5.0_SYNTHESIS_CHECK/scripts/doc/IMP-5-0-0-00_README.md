# IMP-5-0-0-00: Confirm synthesis is using lib models for timing?

## Overview

**Check ID:** IMP-5-0-0-00  
**Description:** Confirm synthesis is using lib models for timing?  
**Category:** Synthesis Quality Check  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/reports/qor.rpt`

This checker validates that Cadence Genus synthesis is using library timing models (.lib/.ccs format) rather than compiled database models (.db format) for timing analysis. Using .lib models ensures accurate timing characterization with full NLDM/CCS delay calculation support, while .db models are pre-compiled abstractions that may lack timing fidelity. The checker parses the QoR report's "Technology libraries" section to identify all loaded libraries and flags any using .db extensions as violations.

---

## Check Logic

### Input Parsing
Parse the QoR report to extract technology library information from the "Technology libraries:" section. This section lists all timing libraries loaded during synthesis with their model types and versions.

**Key Patterns:**
```python
# Pattern 1: Technology libraries section header with inline first library
pattern1 = r'^\s*Technology libraries:\s+(\S+)\s+(\S+)\s*$'
# Example: "    Technology libraries: tcbn03e_bwp143mh117l3p48cpd_base_elvtssgnp_0p675v_m40c_cworst_CCworst_T_ccs 110"

# Pattern 2: Continuation library lines (indented 26+ spaces)
pattern2 = r'^\s{26,}(\S+)\s+(\S+)\s*$'
# Example: "                          tcbn03e_bwp143mh169l3p48cpd_base_lvtssgnp_0p675v_m40c_cworst_CCworst_T_ccs 110"

# Pattern 3: Library model type detection (valid: _ccs/_nldm/.lib, invalid: .db)
pattern3 = r'_(ccs|nldm|lib)\b|\.lib$|\.db$'
# Example: "tcbn03e_..._ccs" → valid (CCS model), "tcbn03e_base_lvt.db" → invalid (DB model)

# Pattern 4: Library domain context
pattern4 = r'^\s*Library domain:\s+(.+)$'
# Example: "  Library domain:         tcond_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup_ideal_virtual"

# Pattern 5: Section terminator
pattern5 = r'^\s*Operating conditions:|^\s*Interconnect mode:|^\s*Area mode:|^\s*$\n^\s*Timing'
# Example: "  Operating conditions:   ssgnp_0p675v_m40c_cworst_CCworst_T "
```

### Detection Logic
1. **State Machine Parsing**: Iterate through QoR report line-by-line with three states:
   - `SEARCHING`: Look for "Library domain:" or "Technology libraries:" header
   - `IN_DOMAIN`: Capture domain name, transition to library parsing
   - `IN_TECH_LIBS`: Extract library names until section ends

2. **Library Extraction**:
   - Match Pattern 1 to detect section start and capture first library (inline format)
   - Match Pattern 2 to capture continuation libraries (indented format)
   - Store library name, version, and associated domain context

3. **Model Type Classification**:
   - Apply Pattern 3 to each library name
   - Valid models: Contains `_ccs`, `_nldm`, `_lib` suffix or `.lib` extension
   - Invalid models: Contains `.db` extension
   - Extract model type indicator for display

4. **Section Boundary Detection**:
   - Match Pattern 5 to identify end of Technology libraries section
   - Stop parsing to avoid capturing unrelated data

5. **Result Aggregation**:
   - Valid libraries → INFO01 (clean items)
   - Invalid .db libraries → ERROR01 (violations)
   - Track domain context for each library set

6. **Edge Cases**:
   - Empty files: Return empty results via validate_input_files()
   - Missing section: Report "No libraries found" in INFO01
   - Mixed model types: Flag only .db libraries as errors
   - Multiple domains: Associate each library with its domain
   - Version variations: Handle integer (110), decimal (11.0), or missing versions

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

**Rationale:** This checker validates the STATUS of all technology libraries found in the QoR report (whether they use .lib or .db models). It does not check for existence of specific predefined libraries. Instead, it discovers all libraries dynamically from the input file and classifies them by model type. Libraries using .lib/.ccs models have correct status (INFO01), while libraries using .db models have incorrect status (ERROR01). This is a status validation check, not an existence check.

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
item_desc = "Confirm synthesis is using lib models for timing?"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "All technology libraries found using valid .lib timing models"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All technology libraries validated with correct .lib timing models"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "All technology libraries found using .lib/.ccs models (no .db models detected)"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All technology libraries matched expected .lib/.ccs model format and validated successfully"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Invalid .db timing models found in technology libraries"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Technology libraries failed validation - .db models detected instead of .lib models"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Required .lib timing models not found - synthesis using compiled .db models instead"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Technology libraries not satisfied - expected .lib/.ccs models but found .db compiled models"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Waived .db timing model usage"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Library using .db model waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries for .db libraries"
unused_waiver_reason = "Waiver not matched - specified .db library not found in QoR report"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: [library_name] (type: model_type, version: version_number, domain: domain_name)
  Example: tcbn03e_bwp143mh117l3p48cpd_base_elvtssgnp_0p675v_m40c_cworst_CCworst_T_ccs (type: ccs, version: 110, domain: tcond_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup_ideal_virtual)

ERROR01 (Violation/Fail items):
  Format: [library_name] (type: db, version: version_number, domain: domain_name) - INVALID: Using compiled .db model instead of .lib timing model
  Example: tcbn03e_base_lvt.db (type: db, version: 110, domain: tcond_ssgnp_0p675v_m40c) - INVALID: Using compiled .db model instead of .lib timing model
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-5-0-0-00:
  description: "Confirm synthesis is using lib models for timing?"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/qor.rpt
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
Reason: All technology libraries found using .lib/.ccs models (no .db models detected)
INFO01:
  - tcbn03e_bwp143mh117l3p48cpd_base_elvtssgnp_0p675v_m40c_cworst_CCworst_T_ccs (type: ccs, version: 110, domain: tcond_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup_ideal_virtual)
  - tcbn03e_bwp143mh169l3p48cpd_base_lvtssgnp_0p675v_m40c_cworst_CCworst_T_ccs (type: ccs, version: 110, domain: tcond_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup_ideal_virtual)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Required .lib timing models not found - synthesis using compiled .db models instead
ERROR01:
  - tcbn03e_base_lvt.db (type: db, version: 110, domain: tcond_ssgnp_0p675v_m40c) - INVALID: Using compiled .db model instead of .lib timing model
  - tcbn03e_base_ulvt.db (type: db, version: 110, domain: tcond_ssgnp_0p675v_m40c) - INVALID: Using compiled .db model instead of .lib timing model
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-5-0-0-00:
  description: "Confirm synthesis is using lib models for timing?"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/qor.rpt
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only for legacy designs using pre-compiled .db libraries"
      - "Note: .db model usage is expected in early synthesis exploration and does not require immediate fixes"
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
  - "Explanation: This check is informational only for legacy designs using pre-compiled .db libraries"
  - "Note: .db model usage is expected in early synthesis exploration and does not require immediate fixes"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - tcbn03e_base_lvt.db (type: db, version: 110, domain: tcond_ssgnp_0p675v_m40c) - INVALID: Using compiled .db model instead of .lib timing model [WAIVED_AS_INFO]
  - tcbn03e_base_ulvt.db (type: db, version: 110, domain: tcond_ssgnp_0p675v_m40c) - INVALID: Using compiled .db model instead of .lib timing model [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-5-0-0-00:
  description: "Confirm synthesis is using lib models for timing?"
  requirements:
    value: 2
    pattern_items:
      - "tcbn03e_bwp143mh117l3p48cpd_base_elvtssgnp_0p675v_m40c_cworst_CCworst_T_ccs"
      - "tcbn03e_bwp143mh169l3p48cpd_base_lvtssgnp_0p675v_m40c_cworst_CCworst_T_ccs"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/qor.rpt
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
Reason: All technology libraries matched expected .lib/.ccs model format and validated successfully
INFO01:
  - tcbn03e_bwp143mh117l3p48cpd_base_elvtssgnp_0p675v_m40c_cworst_CCworst_T_ccs (type: ccs, version: 110, domain: tcond_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup_ideal_virtual)
  - tcbn03e_bwp143mh169l3p48cpd_base_lvtssgnp_0p675v_m40c_cworst_CCworst_T_ccs (type: ccs, version: 110, domain: tcond_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup_ideal_virtual)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-5-0-0-00:
  description: "Confirm synthesis is using lib models for timing?"
  requirements:
    value: 0
    pattern_items:
      - "tcbn03e_bwp143mh117l3p48cpd_base_elvtssgnp_0p675v_m40c_cworst_CCworst_T_ccs"
      - "tcbn03e_bwp143mh169l3p48cpd_base_lvtssgnp_0p675v_m40c_cworst_CCworst_T_ccs"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/qor.rpt
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - library model type validation not enforced in early design phases"
      - "Note: Pattern mismatches are expected when using alternative library configurations and do not require fixes"
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
  - "Explanation: This check is informational only - library model type validation not enforced in early design phases"
  - "Note: Pattern mismatches are expected when using alternative library configurations and do not require fixes"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - tcbn03e_base_lvt.db (type: db, version: 110, domain: tcond_ssgnp_0p675v_m40c) - INVALID: Using compiled .db model instead of .lib timing model [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-5-0-0-00:
  description: "Confirm synthesis is using lib models for timing?"
  requirements:
    value: 2
    pattern_items:
      - "tcbn03e_bwp143mh117l3p48cpd_base_elvtssgnp_0p675v_m40c_cworst_CCworst_T_ccs"
      - "tcbn03e_bwp143mh169l3p48cpd_base_lvtssgnp_0p675v_m40c_cworst_CCworst_T_ccs"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/qor.rpt
  waivers:
    value: 2
    waive_items:
      - name: "tcbn03e_base_lvt.db"
        reason: "Waived - legacy library using .db model approved for this design per team agreement"
      - name: "tcbn03e_base_ulvt.db"
        reason: "Waived - pre-compiled .db model acceptable for early synthesis exploration phase"
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
  - tcbn03e_base_lvt.db (type: db, version: 110, domain: tcond_ssgnp_0p675v_m40c) - INVALID: Using compiled .db model instead of .lib timing model [WAIVER]
  - tcbn03e_base_ulvt.db (type: db, version: 110, domain: tcond_ssgnp_0p675v_m40c) - INVALID: Using compiled .db model instead of .lib timing model [WAIVER]
WARN01 (Unused Waivers):
  - tcbn03e_base_hvt.db: Waiver not matched - specified .db library not found in QoR report
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-5-0-0-00:
  description: "Confirm synthesis is using lib models for timing?"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/reports/qor.rpt
  waivers:
    value: 2
    waive_items:
      - name: "tcbn03e_base_lvt.db"
        reason: "Waived - legacy library using .db model approved for this design per team agreement"
      - name: "tcbn03e_base_ulvt.db"
        reason: "Waived - pre-compiled .db model acceptable for early synthesis exploration phase"
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
  - tcbn03e_base_lvt.db (type: db, version: 110, domain: tcond_ssgnp_0p675v_m40c) - INVALID: Using compiled .db model instead of .lib timing model [WAIVER]
  - tcbn03e_base_ulvt.db (type: db, version: 110, domain: tcond_ssgnp_0p675v_m40c) - INVALID: Using compiled .db model instead of .lib timing model [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 5.0_SYNTHESIS_CHECK --checkers IMP-5-0-0-00 --force

# Run individual tests
python IMP-5-0-0-00.py
```

---

## Notes

- **Library Model Types**: Valid timing models include CCS (Composite Current Source), NLDM (Non-Linear Delay Model), and standard .lib formats. Compiled .db models are pre-processed abstractions that may lack full timing accuracy.
- **Multi-Domain Support**: QoR reports may contain multiple library domains (setup/hold, different corners). The checker tracks domain context for each library to provide complete traceability.
- **Version Handling**: Library versions may appear as integers (110), decimals (11.0), or be omitted entirely. The checker handles all formats gracefully.
- **Performance**: For large QoR reports with hundreds of libraries, the state machine parser efficiently processes only the Technology libraries section, avoiding unnecessary parsing of timing/area/power data.
- **Edge Case - Mixed Models**: If a design uses both .lib and .db models (e.g., during migration), only the .db libraries are flagged as violations while .lib libraries appear in INFO01.
- **Limitation**: The checker relies on file extension and naming conventions (_ccs, _nldm suffixes). Custom library naming schemes that don't follow standard conventions may require pattern adjustments.