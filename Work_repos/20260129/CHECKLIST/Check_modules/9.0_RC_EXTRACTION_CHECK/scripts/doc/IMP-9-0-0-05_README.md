# IMP-9-0-0-05: Confirm proper Quantus version is used for RC extraction(match to or mature than Foundry recommended Quantus version)

## Overview

**Check ID:** IMP-9-0-0-05  
**Description:** Confirm proper Quantus version is used for RC extraction(match to or mature than Foundry recommended Quantus version)  
**Category:** RC Extraction Validation  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/*.spef.gz`

This checker validates that SPEF (Standard Parasitic Exchange Format) files were generated using the correct Cadence Quantus version. It extracts the Quantus version from SPEF file headers, identifies the foundry/technology from the TECH_VERSION or TECH_FILE fields, and compares against foundry-specific minimum version requirements. This ensures RC extraction quality meets foundry recommendations for accurate timing analysis.

---

## Check Logic

### Input Parsing

The checker processes compressed SPEF files (.spef.gz) by parsing the header section (first ~50 lines until *D_NET or *R_NET appears). It extracts version information and technology identifiers to validate tool compliance.

**Key Patterns:**

```python
# Pattern 1: Extract Quantus version from VERSION header
pattern1 = r'^\*VERSION\s+"([0-9]+\.[0-9]+\.[0-9]+(?:-s[0-9]+)?)\s+(.+)"$'
# Example: "*VERSION "22.1.1-s233 Mon Dec 11 23:26:00 PST 2023""
# Group 1: version_number (22.1.1-s233)
# Group 2: build_date_info (Mon Dec 11 23:26:00 PST 2023)

# Pattern 2: Extract extraction date for reporting context
pattern2 = r'^\*DATE\s+"(.+)"$'
# Example: "*DATE "Wed Nov 26 17:35:31 2025""
# Group 1: extraction_date

# Pattern 3: Extract technology version from DESIGN_FLOW
pattern3 = r'\*DESIGN_FLOW.*"TECH_VERSION\s+([^"]+)"'
# Example: "*DESIGN_FLOW "ROUTING_CONFIDENCE 100" "PIN_CAP NONE" "TECH_VERSION cln6_1p15m_1x1xa1ya5y2yy2yx2r_mim_ut-alrdl_rcbest_CCbest""
# Group 1: tech_version string (used to identify foundry)

# Pattern 4: Extract technology file path for foundry identification
pattern4 = r'^//\s*TECH_FILE\s+(.+)$'
# Example: "// TECH_FILE /process/tsmcN6/data/g/QRC/15M1X1Xa1Ya5Y2Yy2Yx2R_UT/fs_v1d0p1a/rcbest/Tech/rcbest_CCbest/qrcTechFile"
# Group 1: tech_file_path (parse for foundry identifier like "tsmcN6" → TSMC N6)

# Pattern 5: Extract design name for context
pattern5 = r'^\*DESIGN\s+"(.+)"$'
# Example: "*DESIGN "CDN_104H_cdn_hs_phy_data_slice_EW""
# Group 1: design_name
```

### Detection Logic

1. **File Processing**: Decompress .spef.gz files using gzip and parse header section line-by-line
2. **Version Extraction**: Search for *VERSION line to extract Quantus version (major.minor.patch-build format)
3. **Foundry Identification**: 
   - Parse TECH_VERSION from *DESIGN_FLOW line, or
   - Parse TECH_FILE comment line to extract foundry identifier (e.g., "tsmcN6" → TSMC_N6)
4. **Version Lookup**: Map foundry identifier to minimum required Quantus version from configuration/lookup table
5. **Version Comparison**: Compare extracted version against required version:
   - Parse version components (major, minor, patch, build)
   - Perform numeric comparison (e.g., 22.1.1-s233 >= 22.1.0-s200)
6. **Result Classification**:
   - **PASS**: Found version >= required version
   - **FAIL**: Found version < required version, or version/foundry info missing
7. **Aggregation**: Report per-file results with file path, found version, required version, and foundry

**Edge Cases Handled**:
- Compressed .gz files (automatic decompression)
- Missing VERSION line (report as error)
- Missing TECH_FILE/TECH_VERSION (cannot determine foundry requirement)
- Non-standard version format (handle with warning)
- Empty or corrupted SPEF files (catch and report)
- Multiple SPEF files with different versions (report each separately)

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

**Rationale:** This checker validates the STATUS of Quantus versions in SPEF files. The pattern_items represent specific Quantus version numbers to check, and the checker outputs only those versions with their compliance status (compliant vs. non-compliant). Versions not in pattern_items are not reported, making this a status validation check rather than an existence check.

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
item_desc = "Confirm proper Quantus version is used for RC extraction(match to or mature than Foundry recommended Quantus version)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "All SPEF files found with compliant Quantus versions"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All Quantus versions matched with compliant status"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "All SPEF files found with Quantus versions meeting or exceeding foundry requirements"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All Quantus versions validated with compliance matching or exceeding foundry requirements"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "SPEF files not found with compliant Quantus versions"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Quantus versions with non-compliant status detected"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "SPEF files not found with required Quantus versions or version information missing"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Quantus versions failed validation - versions below foundry requirements or version information missing"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Quantus versions with waived violations"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Quantus version violation waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries for Quantus version checks"
unused_waiver_reason = "Waiver not matched - no corresponding Quantus version violation found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  If all SPEF files use the same Quantus version and foundry:
    Format: All RC extraction is used Quantus version X.Y.Z-buildID (Foundry: foundry_name)
    Example: All RC extraction is used Quantus version 22.1.1-s233 (Foundry: TSMC_N6)
  
  If SPEF files use different Quantus versions or foundries:
    Format: [Quantus version X.Y.Z-buildID]: file_path (Foundry: foundry_name)
    Example: 
      - Quantus version 22.1.1-s233: IMP-9-0-0-04.spef.gz (Foundry: TSMC_N6)
      - Quantus version 22.1.2-s240: IMP-9-0-0-05.spef.gz (Foundry: TSMC_N5)

ERROR01 (Violation/Fail items):
  Format: [Quantus version X.Y.Z-buildID]: file_path - Found version X.Y.Z-buildID, Required version >=A.B.C-buildXYZ (Foundry: foundry_name)
  Example: Quantus version 21.1.0-s100: IMP-9-0-0-04.spef.gz - Found version 21.1.0-s100, Required version >=22.1.0-s200 (Foundry: TSMC_N6)
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-9-0-0-05:
  description: "Confirm proper Quantus version is used for RC extraction(match to or mature than Foundry recommended Quantus version)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/*.spef.gz"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs custom boolean checks (file exists? config valid?).
PASS/FAIL based on checker's own validation logic.

**Sample Output (PASS - All same version):**
```
Status: PASS
Reason: All SPEF files found with Quantus versions meeting or exceeding foundry requirements
INFO01:
  - All RC extraction is used Quantus version 22.1.1-s233 (Foundry: TSMC_N6)
```

**Sample Output (PASS - Different versions):**
```
Status: PASS
Reason: All SPEF files found with Quantus versions meeting or exceeding foundry requirements
INFO01:
  - Quantus version 22.1.1-s233: IMP-9-0-0-04.spef.gz (Foundry: TSMC_N6)
  - Quantus version 22.1.2-s240: IMP-9-0-0-05.spef.gz (Foundry: TSMC_N5)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: SPEF files not found with required Quantus versions or version information missing
ERROR01:
  - Quantus version 21.1.0-s100: IMP-9-0-0-04.spef.gz - Found version 21.1.0-s100, Required version >=22.1.0-s200 (Foundry: TSMC_N6)
  - VERSION header not found: IMP-9-0-0-06.spef.gz
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-9-0-0-05:
  description: "Confirm proper Quantus version is used for RC extraction(match to or mature than Foundry recommended Quantus version)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/*.spef.gz"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Quantus version check is informational only for legacy designs"
      - "Note: Older Quantus versions are acceptable for this IP block per design team agreement"
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
  - Explanation: Quantus version check is informational only for legacy designs
  - Note: Older Quantus versions are acceptable for this IP block per design team agreement
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - Quantus version 21.1.0-s100: IMP-9-0-0-04.spef.gz - Found version 21.1.0-s100, Required version >=22.1.0-s200 (Foundry: TSMC_N6) [WAIVED_AS_INFO]
  - VERSION header not found: IMP-9-0-0-06.spef.gz [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-9-0-0-05:
  description: "Confirm proper Quantus version is used for RC extraction(match to or mature than Foundry recommended Quantus version)"
  requirements:
    value: 2
    pattern_items:
      - "22.1.1-s233"
      - "22.1.2-s240"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/*.spef.gz"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS/FAIL depends on check purpose:
- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)

**Sample Output (PASS - All same version):**
```
Status: PASS
Reason: All Quantus versions validated with compliance matching or exceeding foundry requirements
INFO01:
  - All RC extraction is used Quantus version 22.1.1-s233 (Foundry: TSMC_N6)
```

**Sample Output (PASS - Different versions):**
```
Status: PASS
Reason: All Quantus versions validated with compliance matching or exceeding foundry requirements
INFO01:
  - Quantus version 22.1.1-s233: IMP-9-0-0-04.spef.gz (Foundry: TSMC_N6)
  - Quantus version 22.1.2-s240: IMP-9-0-0-05.spef.gz (Foundry: TSMC_N5)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-9-0-0-05:
  description: "Confirm proper Quantus version is used for RC extraction(match to or mature than Foundry recommended Quantus version)"
  requirements:
    value: 2
    pattern_items:
      - "22.1.1-s233"
      - "22.1.2-s240"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/*.spef.gz"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Quantus version validation is informational for this design phase"
      - "Note: Version mismatches are expected during early development and do not block signoff"
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
  - Explanation: Quantus version validation is informational for this design phase
  - Note: Version mismatches are expected during early development and do not block signoff
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - Quantus version 21.1.0-s100: IMP-9-0-0-04.spef.gz - Found version 21.1.0-s100, Required version >=22.1.0-s200 (Foundry: TSMC_N6) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-9-0-0-05:
  description: "Confirm proper Quantus version is used for RC extraction(match to or mature than Foundry recommended Quantus version)"
  requirements:
    value: 2
    pattern_items:
      - "22.1.1-s233"
      - "22.1.2-s240"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/*.spef.gz"
  waivers:
    value: 2
    waive_items:
      - name: "21.1.0-s100"
        reason: "Waived - legacy extraction approved by foundry for this design revision"
      - name: "21.1.5-s150"
        reason: "Waived - intermediate version used for debug purposes only, not for final signoff"
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
  - Quantus version 21.1.0-s100: IMP-9-0-0-04.spef.gz - Found version 21.1.0-s100, Required version >=22.1.0-s200 (Foundry: TSMC_N6) [WAIVER]
WARN01 (Unused Waivers):
  - 21.1.5-s150: Waiver not matched - no corresponding Quantus version violation found
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-9-0-0-05:
  description: "Confirm proper Quantus version is used for RC extraction(match to or mature than Foundry recommended Quantus version)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/9.0/*.spef.gz"
  waivers:
    value: 2
    waive_items:
      - name: "21.1.0-s100"
        reason: "Waived - legacy extraction approved by foundry for this design revision"
      - name: "21.1.5-s150"
        reason: "Waived - intermediate version used for debug purposes only, not for final signoff"
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
  - Quantus version 21.1.0-s100: IMP-9-0-0-04.spef.gz - Found version 21.1.0-s100, Required version >=22.1.0-s200 (Foundry: TSMC_N6) [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 9.0_RC_EXTRACTION_CHECK --checkers IMP-9-0-0-05 --force

# Run individual tests
python IMP-9-0-0-05.py
```

---

## Notes

**Foundry Version Mapping:**
The checker requires a configuration mapping foundry/process identifiers to minimum Quantus versions. This can be implemented as:
- JSON/YAML configuration file (recommended for maintainability)
- Hardcoded lookup dictionary in checker code

Example mapping structure:
```python
FOUNDRY_VERSION_MAP = {
    "TSMC_N6": "22.1.0-s200",
    "TSMC_N5": "22.1.1-s233",
    "SAMSUNG_5LPE": "21.1.5-s150",
    "INTEL_10NM": "21.1.0-s100"
}
```

**Version Comparison Logic:**
Version strings follow format: `major.minor.patch-sBUILD`
- Compare major → minor → patch → build numerically
- Example: 22.1.1-s233 > 22.1.0-s200 (patch version higher)
- Example: 22.1.0-s200 > 21.1.5-s300 (major version higher takes precedence)

**Limitations:**
- Requires SPEF files to contain standard VERSION and TECH_VERSION/TECH_FILE headers
- Foundry identification depends on consistent naming in technology file paths
- Version comparison assumes standard Cadence version format (may need adjustment for custom builds)

**Known Issues:**
- Corrupted or incomplete SPEF files may cause parsing errors (handled with try/except)
- Non-standard TECH_VERSION formats may fail foundry identification (fallback to manual specification)
- Very large SPEF files may have performance impact (mitigated by parsing header only)