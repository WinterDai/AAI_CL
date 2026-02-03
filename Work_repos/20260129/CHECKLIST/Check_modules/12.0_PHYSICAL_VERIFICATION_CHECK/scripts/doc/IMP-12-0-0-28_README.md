# IMP-12-0-0-28: Confirm ARC check result is clean. (For BRCM project only, for others fill N/A)

## Overview

**Check ID:** IMP-12-0-0-28  
**Description:** Confirm ARC check result is clean. (For BRCM project only, for others fill N/A)  
**Category:** Physical Verification - ARC (Antenna Rule Check)  
**Input Files:** 
- `${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_ARC.rep` (Calibre ARC report)
- Additional Pegasus ARC reports (optional, user-specified)

This checker validates that all ARC (Antenna Rule Check) violations are resolved across one or more ARC reports. It supports both Calibre and Pegasus report formats, aggregates violations across all reports, and provides waiver support for approved exceptions. The checker is specifically designed for BRCM projects but can be adapted for other flows.

---

## Check Logic

### Input Parsing

The checker supports two ARC report formats:

**Format 1: Calibre ARC Report**
```python
# Pattern 1: Individual ARC rule violations (Calibre format)
calibre_rule_pattern = r'^RULECHECK\s+(\S+)\s+\.+\s+TOTAL\s+Result\s+Count\s*=\s*(\d+)\s*\(\d+\)'
# Example: "RULECHECK ARC_probepad_enclosure_by_chip_edge .................................... TOTAL Result Count = 37 (37)"
# Group 1: ARC rule name (e.g., "ARC_probepad_enclosure_by_chip_edge")
# Group 2: Violation count (e.g., "37") - first number is actual count, (37) is ignored

# Pattern 2: Total DRC violations summary (Calibre format)
calibre_total_pattern = r'^TOTAL\s+DRC\s+Results\s+Generated:\s+(\d+)\s*\(\d+\)'
# Example: "TOTAL DRC Results Generated:     16819 (49568208)"
# Group 1: Total violation count (e.g., "16819") - first number is total, (49568208) is ignored
```

**Format 2: Pegasus ARC Report**
```python
# Pattern 3: Individual ARC rule violations (Pegasus format)
pegasus_rule_pattern = r'^RULECHECK\s+(\S+)\s+\.+\s+Total\s+Result\s+(\d+)\s*\(\s*\d+\s*\)'
# Example: "RULECHECK ARC_probepad_enclosure_by_chip_edge .................................... Total Result          4 (         4)"
# Group 1: ARC rule name (e.g., "ARC_probepad_enclosure_by_chip_edge")
# Group 2: Violation count (e.g., "4") - first number is actual count, (4) is ignored

# Pattern 4: Total DRC violations summary (Pegasus format)
pegasus_total_pattern = r'^Total\s+DRC\s+Results\s*:\s*(\d+)\s*\(\d+\)'
# Example: "Total DRC Results                 : 258 (43252)"
# Group 1: Total violation count (e.g., "258") - first number is total, (43252) is ignored
```

### Detection Logic

**Step 1: Parse All ARC Reports**
- Iterate through all user-specified ARC report files
- Detect report format (Calibre vs Pegasus) based on pattern matching
- Extract individual ARC rule violations with counts
- Extract total violation count from summary section

**Step 2: Aggregate Violations Across Reports**
- Combine violations from all reports by ARC rule name
- Sum violation counts for duplicate rule names across reports
- Calculate total ARC violations across all reports

**Step 3: ARC Clean Determination**
- **PASS Criteria**: Total violation count = 0 across ALL reports
- **FAIL Criteria**: Any report has violations (total count > 0)

**Step 4: Violation Reporting**
- For each ARC rule with violations:
  - Output: `ARC_rule_name: violation_count violations`
- Generate summary statistics:
  - Total unique ARC rules violated
  - Total violation count across all reports
  - Per-report breakdown (if multiple reports)

**Step 5: Waiver Processing (Type 3/4)**
- Match violated ARC rule names against `waive_items`
- Classify violations:
  - **Unwaived**: ARC rules with violations not in waive_items → ERROR
  - **Waived**: ARC rules with violations in waive_items → INFO with [WAIVER] tag
  - **Unused waivers**: waive_items not matching any violations → WARN with [WAIVER] tag

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

**Rationale:** This checker validates ARC violation status (clean vs violations). The `pattern_items` represent specific ARC rule names to monitor. The checker only reports on ARC rules that have violations (matched items with wrong status = violations found). ARC rules not in `pattern_items` are still checked but not individually reported unless they have violations. This is a status check because we're validating "violation count = 0" status for each ARC rule.

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
item_desc = "Confirm ARC check result is clean. (For BRCM project only, for others fill N/A)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "ARC check clean - no violations found in all reports"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "ARC check clean - all monitored rules satisfied (0 violations)"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "All ARC reports show 0 violations (TOTAL DRC Results = 0)"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All monitored ARC rules satisfied with 0 violations across all reports"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "ARC violations detected in reports"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "ARC violations found - monitored rules not satisfied"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "ARC violations found - total violation count > 0"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "ARC rule violations not satisfied - violation count > 0"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Waived ARC violations (approved exceptions)"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "ARC violation waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused ARC waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding ARC violation found in reports"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [ARC_rule_name]: 0 violations (clean)"
  Example: "- ARC_metal_density_check: 0 violations (clean)"

ERROR01 (Violation/Fail items):
  Format: "- [ARC_rule_name]: [count] violations"
  Example: "- ARC_probepad_enclosure_by_chip_edge: 37 violations"

Summary Statistics:
  Format: "Total ARC violations: [total_count] across [rule_count] rules in [report_count] reports"
  Example: "Total ARC violations: 16819 across 15 rules in 2 reports"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-28:
  description: "Confirm ARC check result is clean. (For BRCM project only, for others fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_ARC.rep"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs boolean ARC clean check across all reports.
- Parse all ARC reports (Calibre and/or Pegasus format)
- Aggregate total violation count across all reports
- PASS if total violations = 0 across ALL reports
- FAIL if any report has violations (total count > 0)
- Output summary statistics with per-rule breakdown

**Sample Output (PASS):**
```
Status: PASS
Reason: All ARC reports show 0 violations (TOTAL DRC Results = 0)
INFO01:
  - Summary: ARC check clean - 0 violations across all reports
  - Calibre_ARC.rep: TOTAL DRC Results = 0 (0)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: ARC violations found - total violation count > 0
ERROR01:
  - ARC_probepad_enclosure_by_chip_edge: 37 violations
  - ARC_metal_density_min: 15 violations
  - ARC_via_enclosure: 8 violations
  - Summary: Total ARC violations: 60 across 3 rules in 1 report (Calibre_ARC.rep)
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-28:
  description: "Confirm ARC check result is clean. (For BRCM project only, for others fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_ARC.rep"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: ARC violations are informational only for this BRCM project phase"
      - "Note: Violations will be addressed in final tapeout verification"
      - "Approved by: Design team lead - tracking violations for trend analysis"
```

**CRITICAL Behavior (waivers.value=0):**
- NOTE: Type 1 has NO waiver logic. waive=0 is forced PASS mode only
- IMPORTANT: waive_items uses PLAIN STRINGS (NOT name/reason dict like Type 3/4!)
- waive_items serves as COMMENT ONLY (no matching/filtering logic)
- waive_items content printed as INFO with [WAIVED_INFO] tag
- ALL violations force converted: FAIL→PASS, displayed as INFO with [WAIVED_AS_INFO] tag
- Check ALWAYS returns PASS (violations shown as INFO for tracking)
- Used when: ARC check is informational only, violations expected/acceptable during development

**Sample Output (PASS with violations):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All violations waived as informational
INFO01 ([WAIVED_INFO] - waive_items as comment):
  - "Explanation: ARC violations are informational only for this BRCM project phase"
  - "Note: Violations will be addressed in final tapeout verification"
  - "Approved by: Design team lead - tracking violations for trend analysis"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - ARC_probepad_enclosure_by_chip_edge: 37 violations [WAIVED_AS_INFO]
  - ARC_metal_density_min: 15 violations [WAIVED_AS_INFO]
  - Summary: Total ARC violations: 52 (tracked as informational) [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-28:
  description: "Confirm ARC check result is clean. (For BRCM project only, for others fill N/A)"
  requirements:
    value: 3  # ⚠️ CRITICAL: MUST equal len(pattern_items)
    pattern_items:
      - "ARC_probepad_enclosure_by_chip_edge"  # Monitor specific ARC rule
      - "ARC_metal_density_min"                # Monitor metal density rule
      - "ARC_via_enclosure"                    # Monitor via enclosure rule
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_ARC.rep"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- pattern_items contain ARC RULE NAMES to monitor (not full violation descriptions)
- Extract rule names from RULECHECK lines in reports
- Use exact rule name format as it appears in reports (case-sensitive)
- Example: "ARC_probepad_enclosure_by_chip_edge" (NOT "probepad enclosure" or "ARC violation")

**Check Behavior:**
Type 2 monitors specific ARC rules listed in pattern_items.
- Parse all ARC reports and extract violations
- Filter violations to only those matching pattern_items (monitored rules)
- PASS if all monitored rules have 0 violations
- FAIL if any monitored rule has violations > 0
- Non-monitored rules (not in pattern_items) are checked but not individually reported

**Sample Output (PASS):**
```
Status: PASS
Reason: All monitored ARC rules satisfied with 0 violations across all reports
INFO01:
  - ARC_probepad_enclosure_by_chip_edge: 0 violations (clean)
  - ARC_metal_density_min: 0 violations (clean)
  - ARC_via_enclosure: 0 violations (clean)
  - Summary: All 3 monitored ARC rules clean
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: ARC rule violations not satisfied - violation count > 0
ERROR01:
  - ARC_probepad_enclosure_by_chip_edge: 37 violations
  - ARC_metal_density_min: 15 violations
INFO01:
  - ARC_via_enclosure: 0 violations (clean)
ERROR_SUMMARY:
  - Summary: 2 of 3 monitored ARC rules have violations (total: 52 violations)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-28:
  description: "Confirm ARC check result is clean. (For BRCM project only, for others fill N/A)"
  requirements:
    value: 3
    pattern_items:
      - "ARC_probepad_enclosure_by_chip_edge"
      - "ARC_metal_density_min"
      - "ARC_via_enclosure"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_ARC.rep"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Monitored ARC rules are informational only during development phase"
      - "Note: Violations in these rules are expected and will be fixed before tapeout"
      - "Tracking: Design team is monitoring violation trends for process improvement"
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
  - "Explanation: Monitored ARC rules are informational only during development phase"
  - "Note: Violations in these rules are expected and will be fixed before tapeout"
  - "Tracking: Design team is monitoring violation trends for process improvement"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - ARC_probepad_enclosure_by_chip_edge: 37 violations [WAIVED_AS_INFO]
  - ARC_metal_density_min: 15 violations [WAIVED_AS_INFO]
  - ARC_via_enclosure: 0 violations (clean) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-28:
  description: "Confirm ARC check result is clean. (For BRCM project only, for others fill N/A)"
  requirements:
    value: 3  # ⚠️ CRITICAL: MUST equal len(pattern_items)
    pattern_items:
      - "ARC_probepad_enclosure_by_chip_edge"  # ⚠️ GOLDEN VALUE - Expected clean status
      - "ARC_metal_density_min"                # ⚠️ GOLDEN VALUE - Expected clean status
      - "ARC_via_enclosure"                    # ⚠️ GOLDEN VALUE - Expected clean status
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_ARC.rep"
  waivers:
    value: 2
    waive_items:
      - name: "ARC_probepad_enclosure_by_chip_edge"  # ⚠️ EXEMPTION - ARC rule name to exempt
        reason: "Waived per BRCM design review - probe pad placement constrained by package"
      - name: "ARC_metal_density_min"                # ⚠️ EXEMPTION - ARC rule name to exempt
        reason: "Waived - metal density acceptable for this process corner per foundry approval"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Parse ARC reports and extract violations for monitored rules (pattern_items)
- Match violated ARC rule names against waive_items
- Classify violations:
  - **Unwaived items** → ERROR (need fix)
  - **Waived items** → INFO with [WAIVER] tag (approved)
  - **Unused waivers** → WARN with [WAIVER] tag
- PASS if all violations in monitored rules are waived

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - ARC_probepad_enclosure_by_chip_edge: 37 violations - ARC violation waived per design team approval: Waived per BRCM design review - probe pad placement constrained by package [WAIVER]
  - ARC_metal_density_min: 15 violations - ARC violation waived per design team approval: Waived - metal density acceptable for this process corner per foundry approval [WAIVER]
INFO02 (Clean):
  - ARC_via_enclosure: 0 violations (clean)
WARN01 (Unused Waivers):
  (None - all waivers matched violations)
```

**Sample Output (with unwaived violations):**
```
Status: FAIL
Reason: Unwaived ARC violations found
ERROR01 (Unwaived):
  - ARC_via_enclosure: 8 violations - ARC rule violations not satisfied - violation count > 0
INFO01 (Waived):
  - ARC_probepad_enclosure_by_chip_edge: 37 violations - ARC violation waived per design team approval: Waived per BRCM design review - probe pad placement constrained by package [WAIVER]
WARN01 (Unused Waivers):
  - ARC_metal_density_min: Waiver not matched - no corresponding ARC violation found in reports: Waived - metal density acceptable for this process corner per foundry approval [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-28:
  description: "Confirm ARC check result is clean. (For BRCM project only, for others fill N/A)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/pv/Calibre_ARC.rep"
  waivers:
    value: 2
    waive_items:
      - name: "ARC_probepad_enclosure_by_chip_edge"  # ⚠️ MUST match Type 3 waive_items
        reason: "Waived per BRCM design review - probe pad placement constrained by package"
      - name: "ARC_metal_density_min"                # ⚠️ MUST match Type 3 waive_items
        reason: "Waived - metal density acceptable for this process corner per foundry approval"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (ARC rule names to exempt)
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (no pattern_items - checks ALL ARC rules), plus waiver classification:
- Parse all ARC reports and extract ALL violations (not filtered by pattern_items)
- Match violated ARC rule names against waive_items
- Classify violations:
  - **Unwaived violations** → ERROR
  - **Waived violations** → INFO with [WAIVER] tag
  - **Unused waivers** → WARN with [WAIVER] tag
- PASS if all violations are waived

**Sample Output:**
```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - ARC_probepad_enclosure_by_chip_edge: 37 violations - ARC violation waived per design team approval: Waived per BRCM design review - probe pad placement constrained by package [WAIVER]
  - ARC_metal_density_min: 15 violations - ARC violation waived per design team approval: Waived - metal density acceptable for this process corner per foundry approval [WAIVER]
WARN01 (Unused Waivers):
  (None - all waivers matched violations)
```

**Sample Output (with unwaived violations):**
```
Status: FAIL
Reason: Unwaived ARC violations found
ERROR01 (Unwaived):
  - ARC_via_enclosure: 8 violations - ARC violations found - total violation count > 0
  - ARC_antenna_ratio: 3 violations - ARC violations found - total violation count > 0
INFO01 (Waived):
  - ARC_probepad_enclosure_by_chip_edge: 37 violations - ARC violation waived per design team approval: Waived per BRCM design review - probe pad placement constrained by package [WAIVER]
WARN01 (Unused Waivers):
  - ARC_metal_density_min: Waiver not matched - no corresponding ARC violation found in reports: Waived - metal density acceptable for this process corner per foundry approval [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 12.0_PHYSICAL_VERIFICATION_CHECK --checkers IMP-12-0-0-28 --force

# Run individual tests
python IMP-12-0-0-28.py
```

---

## Notes

### Multi-Report Support
- Checker supports 1 or more ARC reports (Calibre and/or Pegasus format)
- Violations are aggregated across all reports by ARC rule name
- Total violation count is sum across all reports
- ARC clean requires ALL reports to show 0 violations

### Report Format Detection
- Calibre format: `RULECHECK ... TOTAL Result Count = X (Y)`
- Pegasus format: `RULECHECK ... Total Result X (Y)`
- Checker auto-detects format based on pattern matching
- Mixed formats supported (e.g., Calibre + Pegasus reports in same check)

### Violation Count Parsing
- First number is actual violation count (used for checks)
- Number in parentheses is ignored (may represent unique violations or other metrics)
- Example: `37 (37)` → use `37` as violation count

### Summary Statistics
- Total violations: Sum of all ARC rule violations across all reports
- Per-rule breakdown: Individual violation counts for each ARC rule
- Per-report breakdown: Violations grouped by source report (if multiple reports)

### Waiver Matching Logic (Type 3/4)
- Waivers match on ARC rule name (exact string match, case-sensitive)
- One waiver can cover multiple violations of the same ARC rule
- Unused waivers indicate potential configuration errors or resolved violations

### Known Limitations
- Checker does not parse individual violation locations (only counts)
- Detailed violation analysis requires manual review of ARC reports
- Waiver reasons are informational only (not validated against approval database)

### BRCM Project Specifics
- This checker is designed for BRCM project flows
- For non-BRCM projects, fill "N/A" in requirements or skip this check
- BRCM-specific ARC rules may have different naming conventions