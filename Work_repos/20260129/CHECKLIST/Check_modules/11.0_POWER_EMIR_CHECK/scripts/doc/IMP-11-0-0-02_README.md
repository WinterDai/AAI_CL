# IMP-11-0-0-02: Confirm EMIR signoff criteria follows addendum or SOW, otherwise follow internal spec (design rule with IP specific margin)

## Overview

**Check ID:** IMP-11-0-0-02  
**Description:** Confirm EMIR signoff criteria follows addendum or SOW, otherwise follow internal spec (design rule with IP specific margin)  
**Category:** POWER_EMIR_CHECK  
**Input Files:** TBD

This checker validates that the EMIR (Electromigration and IR Drop) signoff criteria used in the design meet the requirements specified in the project addendum or Statement of Work (SOW). If no specific criteria are defined in these documents, the checker verifies compliance with internal specifications, including design rules with IP-specific margins. The checker examines key EMIR parameters including EM temperature, EM lifetime, static IR drop targets, and dynamic IR drop targets to ensure they meet the required thresholds for signoff.

---

## Check Logic

### Input Parsing
Parse EMIR signoff report files or configuration files to extract the following key parameters:
- EM_TEMPERATURE: Electromigration analysis temperature (in °C)
- EM_LIFETIME: Electromigration lifetime requirement (in hours)
- STATIC_IR_TARGET: Static IR drop target percentage
- DYNAMIC_IR_TARGET: Dynamic IR drop target percentage

**Key Patterns:**
```python
# Pattern 1: EM Temperature extraction
pattern_em_temp = r'EM[_\s]*TEMPERATURE[:\s]*(\d+)'
# Example: "EM_TEMPERATURE: 105" or "EM TEMPERATURE = 105"

# Pattern 2: EM Lifetime extraction
pattern_em_lifetime = r'EM[_\s]*LIFETIME[:\s]*(\d+)'
# Example: "EM_LIFETIME: 87600" or "EM LIFETIME = 87600 hours"

# Pattern 3: Static IR target extraction
pattern_static_ir = r'STATIC[_\s]*IR[_\s]*TARGET[:\s]*(\d+)%?'
# Example: "STATIC_IR_TARGET: 3%" or "STATIC IR TARGET = 3"

# Pattern 4: Dynamic IR target extraction
pattern_dynamic_ir = r'DYNAMIC[_\s]*IR[_\s]*TARGET[:\s]*(\d+)%?'
# Example: "DYNAMIC_IR_TARGET: 15%" or "DYNAMIC IR TARGET = 15"
```

### Detection Logic
1. Parse input files to extract EMIR signoff criteria values
2. Compare extracted values against required pattern_items:
   - EM_TEMPERATURE should match required temperature (e.g., 105°C)
   - EM_LIFETIME should match required lifetime (e.g., 87600 hours = 10 years)
   - STATIC_IR_TARGET should match required percentage (e.g., 3%)
   - DYNAMIC_IR_TARGET should match required percentage (e.g., 15%)
3. For each pattern_item (required criterion):
   - If matching value found in input → Add to found_items
   - If not found or value mismatch → Add to missing_items
4. Report PASS if all required criteria are found and match specifications
5. Report FAIL if any required criteria are missing or do not match

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `existence_check`

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

**Selected Mode for this checker:** `existence_check`

**Rationale:** This checker validates that required EMIR signoff criteria exist in the design configuration. The pattern_items represent mandatory EMIR parameters (EM_TEMPERATURE, EM_LIFETIME, STATIC_IR_TARGET, DYNAMIC_IR_TARGET) that MUST be present and match the specified values. The checker performs an existence check to ensure all required criteria are configured correctly according to addendum/SOW or internal specifications.

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
item_desc = "Confirm EMIR signoff criteria follows addendum or SOW, otherwise follow internal spec (design rule with IP specific margin)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "EMIR signoff criteria found in configuration"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "EMIR signoff criteria matched required specifications"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "All required EMIR signoff criteria found in design configuration"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All EMIR signoff criteria matched and validated against requirements (EM_TEMPERATURE=105°C, EM_LIFETIME=87600hrs, STATIC_IR=3%, DYNAMIC_IR=15%)"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Required EMIR signoff criteria not found in configuration"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "EMIR signoff criteria not satisfied or missing from configuration"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Required EMIR signoff criteria not found in design configuration files"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "EMIR signoff criteria not satisfied - missing or incorrect values for required parameters"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Waived EMIR signoff criteria deviations"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "EMIR signoff criteria deviation waived per project-specific requirements"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused EMIR criteria waiver entries"
unused_waiver_reason = "Waiver entry not matched - no corresponding EMIR criteria deviation found in configuration"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [item_name]: [found_reason]"
  Example: "- EM_TEMPERATURE=105: All EMIR signoff criteria matched and validated against requirements"

ERROR01 (Violation/Fail items):
  Format: "- [item_name]: [missing_reason]"
  Example: "- STATIC_IR_TARGET=3%: EMIR signoff criteria not satisfied - missing or incorrect values for required parameters"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-02:
  description: "Confirm EMIR signoff criteria follows addendum or SOW, otherwise follow internal spec (design rule with IP specific margin)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "emir_signoff_report.rpt"
    - "emir_config.cfg"
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
Reason: All required EMIR signoff criteria found in design configuration

Log format (CheckList.rpt):
INFO01:
  - EMIR_SIGNOFF_CRITERIA_VALID

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: EMIR_SIGNOFF_CRITERIA_VALID. In line 1, emir_config.cfg: All required EMIR signoff criteria found in design configuration
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Required EMIR signoff criteria not found in design configuration files

Log format (CheckList.rpt):
ERROR01:
  - EMIR_SIGNOFF_CRITERIA_MISSING

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: EMIR_SIGNOFF_CRITERIA_MISSING. In line 1, emir_config.cfg: Required EMIR signoff criteria not found in design configuration files
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-02:
  description: "Confirm EMIR signoff criteria follows addendum or SOW, otherwise follow internal spec (design rule with IP specific margin)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "emir_signoff_report.rpt"
    - "emir_config.cfg"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: EMIR criteria check is informational only for early design phases"
      - "Note: Final EMIR signoff criteria will be validated during tape-out review"
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
  - "Explanation: EMIR criteria check is informational only for early design phases"
  - "Note: Final EMIR signoff criteria will be validated during tape-out review"
INFO02:
  - EMIR_SIGNOFF_CRITERIA_MISSING

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: EMIR criteria check is informational only for early design phases. [WAIVED_INFO]
2: Info: EMIR_SIGNOFF_CRITERIA_MISSING. In line 1, emir_config.cfg: Required EMIR signoff criteria not found in design configuration files [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-02:
  description: "Confirm EMIR signoff criteria follows addendum or SOW, otherwise follow internal spec (design rule with IP specific margin)"
  requirements:
    value: 4
    pattern_items:
      - "EM_TEMPERATURE=105"
      - "EM_LIFETIME=87600"
      - "STATIC_IR_TARGET=3%"
      - "DYNAMIC_IR_TARGET=15%"
  input_files:
    - "emir_signoff_report.rpt"
    - "emir_config.cfg"
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
Reason: All EMIR signoff criteria matched and validated against requirements (EM_TEMPERATURE=105°C, EM_LIFETIME=87600hrs, STATIC_IR=3%, DYNAMIC_IR=15%)

Log format (CheckList.rpt):
INFO01:
  - EM_TEMPERATURE=105
  - EM_LIFETIME=87600
  - STATIC_IR_TARGET=3%
  - DYNAMIC_IR_TARGET=15%

Report format (item_id.rpt):
Info Occurrence: 4
1: Info: EM_TEMPERATURE=105. In line 15, emir_config.cfg: All EMIR signoff criteria matched and validated against requirements
2: Info: EM_LIFETIME=87600. In line 16, emir_config.cfg: All EMIR signoff criteria matched and validated against requirements
3: Info: STATIC_IR_TARGET=3%. In line 20, emir_config.cfg: All EMIR signoff criteria matched and validated against requirements
4: Info: DYNAMIC_IR_TARGET=15%. In line 21, emir_config.cfg: All EMIR signoff criteria matched and validated against requirements
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-02:
  description: "Confirm EMIR signoff criteria follows addendum or SOW, otherwise follow internal spec (design rule with IP specific margin)"
  requirements:
    value: 4
    pattern_items:
      - "EM_TEMPERATURE=105"
      - "EM_LIFETIME=87600"
      - "STATIC_IR_TARGET=3%"
      - "DYNAMIC_IR_TARGET=15%"
  input_files:
    - "emir_signoff_report.rpt"
    - "emir_config.cfg"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: EMIR criteria deviations are acceptable for pre-silicon validation phase"
      - "Note: Relaxed criteria approved by design team for early power analysis"
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
  - "Explanation: EMIR criteria deviations are acceptable for pre-silicon validation phase"
  - "Note: Relaxed criteria approved by design team for early power analysis"
INFO02:
  - STATIC_IR_TARGET=3%
  - DYNAMIC_IR_TARGET=15%

Report format (item_id.rpt):
Info Occurrence: 4
1: Info: Explanation: EMIR criteria deviations are acceptable for pre-silicon validation phase. [WAIVED_INFO]
2: Info: Note: Relaxed criteria approved by design team for early power analysis. [WAIVED_INFO]
3: Info: STATIC_IR_TARGET=3%. In line 20, emir_config.cfg: EMIR signoff criteria not satisfied - missing or incorrect values for required parameters [WAIVED_AS_INFO]
4: Info: DYNAMIC_IR_TARGET=15%. In line 21, emir_config.cfg: EMIR signoff criteria not satisfied - missing or incorrect values for required parameters [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-02:
  description: "Confirm EMIR signoff criteria follows addendum or SOW, otherwise follow internal spec (design rule with IP specific margin)"
  requirements:
    value: 4
    pattern_items:
      - "EM_TEMPERATURE=105"
      - "EM_LIFETIME=87600"
      - "STATIC_IR_TARGET=3%"
      - "DYNAMIC_IR_TARGET=15%"
  input_files:
    - "emir_signoff_report.rpt"
    - "emir_config.cfg"
  waivers:
    value: 2
    waive_items:
      - name: "STATIC_IR_TARGET=5%"
        reason: "Waived per addendum - 5% static IR acceptable for low-power domains"
      - name: "DYNAMIC_IR_TARGET=20%"
        reason: "Waived per SOW - 20% dynamic IR acceptable for test mode operation"
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

Log format (CheckList.rpt):
INFO01:
  - STATIC_IR_TARGET=5%
  - DYNAMIC_IR_TARGET=20%
WARN01:
  - (none - all waivers used)

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: STATIC_IR_TARGET=5%. In line 20, emir_config.cfg: EMIR signoff criteria deviation waived per project-specific requirements: Waived per addendum - 5% static IR acceptable for low-power domains [WAIVER]
2: Info: DYNAMIC_IR_TARGET=20%. In line 21, emir_config.cfg: EMIR signoff criteria deviation waived per project-specific requirements: Waived per SOW - 20% dynamic IR acceptable for test mode operation [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-02:
  description: "Confirm EMIR signoff criteria follows addendum or SOW, otherwise follow internal spec (design rule with IP specific margin)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "emir_signoff_report.rpt"
    - "emir_config.cfg"
  waivers:
    value: 2
    waive_items:
      - name: "STATIC_IR_TARGET=5%"
        reason: "Waived per addendum - 5% static IR acceptable for low-power domains"
      - name: "DYNAMIC_IR_TARGET=20%"
        reason: "Waived per SOW - 20% dynamic IR acceptable for test mode operation"
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

Log format (CheckList.rpt):
INFO01:
  - STATIC_IR_TARGET=5%
  - DYNAMIC_IR_TARGET=20%
WARN01:
  - (none - all waivers used)

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: STATIC_IR_TARGET=5%. In line 20, emir_config.cfg: EMIR signoff criteria deviation waived per project-specific requirements: Waived per addendum - 5% static IR acceptable for low-power domains [WAIVER]
2: Info: DYNAMIC_IR_TARGET=20%. In line 21, emir_config.cfg: EMIR signoff criteria deviation waived per project-specific requirements: Waived per SOW - 20% dynamic IR acceptable for test mode operation [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 11.0_POWER_EMIR_CHECK --checkers IMP-11-0-0-02 --force

# Run individual tests
python IMP-11-0-0-02.py
```

---

## Notes

- **EMIR Signoff Criteria Priority**: The checker follows this priority order:
  1. Project-specific addendum requirements (highest priority)
  2. Statement of Work (SOW) specifications
  3. Internal design rules with IP-specific margins (fallback)

- **Parameter Definitions**:
  - **EM_TEMPERATURE**: Temperature used for electromigration analysis (typically 105°C for worst-case)
  - **EM_LIFETIME**: Required electromigration lifetime in hours (87600 hours = 10 years)
  - **STATIC_IR_TARGET**: Maximum allowable static IR drop percentage (typically 3%)
  - **DYNAMIC_IR_TARGET**: Maximum allowable dynamic IR drop percentage (typically 15%)

- **Waiver Use Cases**: Waivers may be granted for:
  - Low-power domains with relaxed IR drop requirements
  - Test mode operations where higher IR drop is acceptable
  - Specific IP blocks with vendor-approved alternative criteria
  - Early design phases where final criteria are not yet finalized

- **Input File Formats**: The checker supports multiple input formats:
  - EMIR signoff reports (`.rpt`)
  - EMIR configuration files (`.cfg`)
  - Power analysis summary files
  - Custom EMIR specification documents

- **Known Limitations**:
  - Checker assumes EMIR criteria are explicitly stated in input files
  - Does not perform actual EMIR analysis, only validates criteria configuration
  - Waiver logic requires exact string matching for criterion names