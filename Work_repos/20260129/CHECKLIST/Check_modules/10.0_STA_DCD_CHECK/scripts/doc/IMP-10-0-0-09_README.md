# IMP-10-0-0-09: Confirm no SPEF annotation issue in STA.

## Overview

**Check ID:** IMP-10-0-0-09  
**Description:** Confirm no SPEF annotation issue in STA.  
**Category:** Static Timing Analysis / SPEF Annotation Validation  
**Input Files:**
- `IP_project_folder/logs/sta_post_route.log` - Main STA log file
- `IP_project_folder/logs/*_sta_post_route.log` - Per-view STA log files (multi-file support)

### Purpose

Validates that all real nets in Static Timing Analysis have complete SPEF (Standard Parasitic Exchange Format) annotation. This checker detects nets that failed parasitic annotation by searching for `Not annotated real net:` entries in STA log files.

**Shell Script Equivalent:**
```bash
grep -i "^Not annotated real net:" sta_post_route.log
# If found → FAIL (list all not-annotated nets with view info)
# If not found → PASS (all nets are annotated)
```

### Functional Description

**What is being checked?**
- **Primary Detection**: Searches for lines starting with `Not annotated real net:` in STA log files
- **View Association**: Extracts view names and associates each not-annotated net with its timing view
- **Multi-file Aggregation**: Processes multiple input log files and aggregates results
- **Display Format**: Reports nets as `[net_name] (view: view_name)` with file path and line number

**Why is this check important for VLSI design?**
- **Timing Accuracy**: Not-annotated nets use estimated parasitics instead of extracted SPEF values, causing inaccurate timing analysis
- **Design Convergence**: Missing SPEF annotation leads to false timing passes/fails and prevents timing closure
- **Sign-off Readiness**: 100% real net annotation is mandatory for tapeout sign-off
- **Multi-corner Validation**: Ensures all timing views (setup/hold, fast/slow corners) have complete annotation

**What problems does it prevent?**
- Silicon failures due to incorrect post-route timing analysis
- RC extraction or SPEF file mapping errors
- View-specific annotation gaps across PVT corners
- Incomplete parasitic data before tape-out

---

## Check Logic

### Detection Logic (Based on Script Implementation)

**Step 1: Parse STA Log Files**
```python
For each input file:
  1. Track current view from "# view: <view_name>" lines
  2. Search for pattern: "^Not annotated real net:\s*(.+)"
  3. When found:
     - Extract net name (strip brackets)
     - Record file path and line number
     - Associate with current view
  4. Aggregate results across all files
```

**Step 2: Extract Data from Logs**

**View Name Extraction:**
- **Pattern**: `^#\s+view:\s+(.+)`
- **Example**: `#   view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup`
- **Purpose**: Associates nets with timing view/corner

**Not-annotated Net Detection:**
- **Pattern**: `^Not annotated real net:\s*(.+)` (case-insensitive)
- **Example**: `Not annotated real net: [u_pcs_top/u_phy_pcs_reg_ctrl/u_pcs_cdb_reg/UNCONNECTED_HIER_Z314]`
- **Extracted Info**: 
  * Net name: `u_pcs_top/u_phy_pcs_reg_ctrl/u_pcs_cdb_reg/UNCONNECTED_HIER_Z314`
  * View: `func_rcss_0p675v_125c_pcss_cmax_pcff3_setup`
  * File: `/path/to/func_rcss_0p675v_125c_pcss_cmax_pcff3_setup_sta_post_route.log`
  * Line: `14`

**Annotation Statistics (Optional, for reference):**
- **Pattern**: `\|\s*Count\s+\|\s+([\d]+)\s+\|\s+([\d]+)\s+\|\s+([\d]+)\s+\|`
- **Table**: Resistor/Capacitor counts from parasitic summary
- **Note**: Extracted but not displayed in output (removed per design)

**Step 3: Apply Check Type Logic**

```
Type 1 (requirements.value=N/A, waivers.value=N/A/0):
  - Global check: scan all views
  - PASS if no "Not annotated real net:" found
  - FAIL if any detected, list all with view info
  - Output: PASS views → INFO01, FAIL nets → ERROR01

Type 2 (requirements.value>0, pattern_items exists, waivers.value=N/A/0):
  - View-specific check: scan only pattern_items views
  - Compare not-annotated count vs requirements.value threshold
  - FAIL if view exceeds threshold
  - Output: PASS views → INFO01, FAIL nets → ERROR01
  - Display detailed net information for failed views

Type 3 (requirements.value>0, pattern_items exists, waivers.value>0):
  - View-specific check with waiver support
  - Support view-level waiver (waive entire view)
  - Support net-level waiver (waive specific nets)
  - Output: PASS views → INFO02, Waived nets → INFO01, FAIL nets → ERROR01

Type 4 (requirements.value=N/A, waivers.value>0):
  - Global check with waiver support
  - Check all views, support view/net-level waivers
  - Output: PASS views → INFO02, Waived nets → INFO01, FAIL nets → ERROR01
```

**Step 4: Waiver Matching (Type 3/4 only)**

**View-level Waiver:**
```yaml
waive_items:
  - func_rcss_0p675v_125c_pcss_cmax_pcff3_setup
# Effect: Waives ALL not-annotated nets in this view
```

**Net-level Waiver:**
```yaml
waive_items:
  - "[u_pcs_top/net_name] (view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup)"
# Effect: Waives specific net in specific view
```

**Waiver Tag Rules:**
- When `waivers.value > 0` (Type 3/4 active waiver):
  * All waived items: suffix `[WAIVER]`
  * Reason field includes waiver justification
- When `waivers.value = 0` (Type 1/2 forced PASS):
  * waive_items: suffix `[WAIVED_INFO]`
  * FAIL items converted to INFO: suffix `[WAIVED_AS_INFO]`

**Step 5: Output Generation**

**DetailItem Format:**
```python
DetailItem(
    severity=Severity.FAIL,  # or INFO for PASS/waived
    name="[net_name] (view: view_name)",
    line_number=14,  # Line in source log file
    file_path="/path/to/log/file.log",
    reason="Not-annotated real net detected"
)
```

**Report Output (.rpt file):**
```
FAIL:IMP-10-0-0-09:Confirm no SPEF annotation issue in STA.
Fail Occurrence: 1
1: Fail: [net_name] (view: view_name). In line 14, filepath: /path/to/log: Not-annotated real net detected
```

**Log Output (.log file):**
```
FAIL:IMP-10-0-0-09:Confirm no SPEF annotation issue in STA.
IMP-10-0-0-09-ERROR01: SPEF annotation issues found in STA:
  Severity: Fail Occurrence: 1
  - [[net_name]] (view: view_name)
```

---

## Auto Type Detection

The checker automatically detects which type to execute based on configuration:

| Type | requirements.value | pattern_items | waivers.value | Behavior |
|------|-------------------|---------------|---------------|----------|
| 1 | N/A | [] (empty) | N/A or 0 | Global check, no waivers |
| 2 | >0 (e.g., 0) | List of views | N/A or 0 | View-specific, no waivers |
| 3 | >0 (e.g., 0) | List of views | >0 (e.g., 1) | View-specific, with waivers |
| 4 | N/A | [] (empty) | >0 (e.g., 1) | Global check, with waivers |

---

## Type 1: Global Check (No Waivers)

### Use Case
Use this configuration to ensure ALL views have complete SPEF annotation without any waivers. This is the strictest check mode suitable for final sign-off validation.

### Configuration Example

```yaml
description: Confirm no SPEF annotation issue in STA.
requirements:
  value: N/A
  pattern_items: []
input_files: 
  - IP_project_folder/logs/sta_post_route.log
waivers:
  value: N/A
  waive_items: []
```

### Expected Behavior
### Configuration Example

```yaml
description: Confirm no SPEF annotation issue in STA.
requirements:
  value: N/A
  pattern_items: []
input_files: 
  - IP_project_folder/logs/sta_post_route.log
  - IP_project_folder/logs/func_rcss_0p675v_125c_pcss_cmax_pcff3_setup_sta_post_route.log
waivers:
  value: N/A
  waive_items: []
```

### Expected Behavior

**PASS Conditions:**
- No `Not annotated real net:` entries found in any log file
- All views have 100% net annotation

**Output Examples:**
```
PASS:IMP-10-0-0-09:Confirm no SPEF annotation issue in STA.
IMP-10-0-0-09-INFO01: No SPEF annotation issue in STA:
  Severity: Info Occurrence: 2
  - All nets are annotated (view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup)
  - All nets are annotated (view: func_rcss_0p675v_m40c_pcss_cmax_pcss3_setup)
```

**FAIL Conditions:**
- Any `Not annotated real net:` entries detected
- Displays net name, view, file path, and line number

**Output Examples:**
```
FAIL:IMP-10-0-0-09:Confirm no SPEF annotation issue in STA.
IMP-10-0-0-09-ERROR01: SPEF annotation issues found in STA:
  Severity: Fail Occurrence: 1
  - [[u_pcs_top/u_phy_pcs_reg_ctrl/u_pcs_cdb_reg/UNCONNECTED_HIER_Z314]] (view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup)
IMP-10-0-0-09-INFO01: No SPEF annotation issue in STA:
  Severity: Info Occurrence: 1
  - All nets are annotated (view: func_rcss_0p675v_m40c_pcss_cmax_pcss3_setup)
```

---

## Type 2: View-Specific Check (No Waivers)

### Use Case
Check specific timing views (from pattern_items) for SPEF annotation issues. Use this when you want to validate particular corners or scenarios without checking all views. Useful for incremental validation or focusing on critical timing scenarios.

### Configuration Example

```yaml
description: Confirm no SPEF annotation issue in STA.
requirements:
  value: 0
  pattern_items:
    - func_rcss_0p675v_125c_pcss_cmax_pcff3_setup
    - func_rcss_0p675v_m40c_pcss_cmax_pcss3_setup
input_files: 
  - IP_project_folder/logs/sta_post_route.log
  - IP_project_folder/logs/func_rcss_0p675v_125c_pcss_cmax_pcff3_setup_sta_post_route.log
waivers:
  value: N/A
  waive_items: []
```

### Expected Behavior

**PASS Conditions:**
- Not-annotated net count for each specified view ≤ requirements.value (0)
- All checked views have complete annotation

**Output Examples:**
```
PASS:IMP-10-0-0-09:Confirm no SPEF annotation issue in STA.
IMP-10-0-0-09-INFO01: No SPEF annotation issue in STA:
  Severity: Info Occurrence: 2
  - All nets are annotated (view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup)
  - All nets are annotated (view: func_rcss_0p675v_m40c_pcss_cmax_pcss3_setup)
```

**FAIL Conditions:**
- Any view in pattern_items has not-annotated nets exceeding requirements.value
- Shows detailed net information for failed views

**Output Examples:**
```
FAIL:IMP-10-0-0-09:Confirm no SPEF annotation issue in STA.
IMP-10-0-0-09-ERROR01: SPEF annotation issues found in STA:
  Severity: Fail Occurrence: 1
  - [[u_pcs_top/u_phy_pcs_reg_ctrl/u_pcs_cdb_reg/UNCONNECTED_HIER_Z314]] (view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup)
IMP-10-0-0-09-INFO01: No SPEF annotation issue in STA:
  Severity: Info Occurrence: 1
  - All nets are annotated (view: func_rcss_0p675v_m40c_pcss_cmax_pcss3_setup)
```

---

## Type 3: View-Specific Check with Waivers

### Use Case
Check specific views while allowing view-level or net-level waivers. Use when certain views or specific nets have known annotation issues that are acceptable (e.g., test modes, debug paths, or views under development).

### Configuration Example

```yaml
description: Confirm no SPEF annotation issue in STA.
requirements:
  value: 0
  pattern_items:
    - func_rcss_0p675v_125c_pcss_cmax_pcff3_setup
    - func_rcss_0p675v_m40c_pcss_cmax_pcss3_setup
input_files: 
  - IP_project_folder/logs/sta_post_route.log
  - IP_project_folder/logs/func_rcss_0p675v_125c_pcss_cmax_pcff3_setup_sta_post_route.log
waivers:
  value: 1
  waive_items:
    - func_rcss_0p675v_125c_pcss_cmax_pcff3_setup  # Waive entire view
```

### Expected Behavior

**Waiver Logic:**
- **View-level waiver**: Specify view name in waive_items → waives ALL not-annotated nets in that view
- **Net-level waiver**: Specify `"[net_name] (view: view_name)"` → waives specific net in specific view
- Waived nets are reported as INFO01, unwaived nets as ERROR01

**PASS Conditions:**
- All not-annotated nets are either in waived views or explicitly waived
- Unwaived net count per view ≤ requirements.value

**Sample Output (PASS - view-level waiver):**
```
PASS:IMP-10-0-0-09:Confirm no SPEF annotation issue in STA.
IMP-10-0-0-09-INFO01: Waived SPEF annotation issues:
  Severity: Info Occurrence: 1
  - [[u_pcs_top/u_phy_pcs_reg_ctrl/u_pcs_cdb_reg/UNCONNECTED_HIER_Z314]] (view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup)
IMP-10-0-0-09-INFO02: No SPEF annotation issue in STA:
  Severity: Info Occurrence: 1
  - All nets are annotated (view: func_rcss_0p675v_m40c_pcss_cmax_pcss3_setup)
```

**FAIL Conditions:**
- Unwaived not-annotated nets exceed threshold
- New nets detected that are not covered by waivers

**Sample Output (FAIL - unwaived nets):**
```
FAIL:IMP-10-0-0-09:Confirm no SPEF annotation issue in STA.
IMP-10-0-0-09-ERROR01: SPEF annotation issues found in STA:
  Severity: Fail Occurrence: 2
  - [[u_pcs_top/new_net_1]] (view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup)
  - [[u_pcs_top/new_net_2]] (view: func_rcss_0p675v_m40c_pcss_cmax_pcss3_setup)
IMP-10-0-0-09-INFO01: Waived SPEF annotation issues:
  Severity: Info Occurrence: 1
  - [[u_pcs_top/u_phy_pcs_reg_ctrl/u_pcs_cdb_reg/UNCONNECTED_HIER_Z314]] (view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup)
```

---

## Type 4: Global Check with Waivers

### Use Case
Global check across all views with waiver support. Use when you want to monitor annotation status across all timing scenarios while allowing temporary exceptions for specific views or nets (e.g., early development stages or known tool limitations).

### Configuration Example

```yaml
description: Confirm no SPEF annotation issue in STA.
requirements:
  value: N/A
  pattern_items: []
input_files: 
  - IP_project_folder/logs/sta_post_route.log
  - IP_project_folder/logs/func_rcss_0p675v_125c_pcss_cmax_pcff3_setup_sta_post_route.log
waivers:
  value: 1
  waive_items:
    - func_rcss_0p675v_125c_pcss_cmax_pcff3_setup  # Waive entire view
```

### Expected Behavior

**Waiver Logic:**
- Same as Type 3: supports both view-level and net-level waivers
- Checks all views (not limited to pattern_items)
- Views with waived nets still appear in INFO02 as PASS

**Sample Output (PASS with waivers):**
```
PASS:IMP-10-0-0-09:Confirm no SPEF annotation issue in STA.
IMP-10-0-0-09-INFO01: Waived SPEF annotation issues:
  Severity: Info Occurrence: 1
  - [u_pcs_top/u_phy_pcs_reg_ctrl/u_pcs_cdb_reg/UNCONNECTED_HIER_Z314] (view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup)
IMP-10-0-0-09-INFO02: No SPEF annotation issue in STA:
  Severity: Info Occurrence: 2
  - All nets are annotated (view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup)
  - All nets are annotated (view: func_rcss_0p675v_m40c_pcss_cmax_pcss3_setup)
```

---

## Testing

### Test Data Preparation

#### Option 1: Use Existing Test Data
```powershell
# Verify the existing STA log files are available
Get-Item IP_project_folder\logs\sta_post_route.log
Get-Item IP_project_folder\logs\*_sta_post_route.log

# Check for not-annotated nets in logs
Select-String -Path IP_project_folder\logs\*_sta_post_route.log -Pattern "^Not annotated real net:"

# View annotation summary sections
Select-String -Path IP_project_folder\logs\sta_post_route.log -Pattern "# Summary of Annotated Parasitics" -Context 0,15
```

#### Option 2: Create Minimal Test Case with PASS
```powershell
# Create a test log with no annotation issues
$passLog = @"
report_annotated_parasitics -list_not_annotated -list_real_net -list_broken_net
<CMD> report_annotated_parasitics -list_not_annotated -list_real_net -list_broken_net
####################################################################
# report_annotated_parasitics: Mon Sep 15 08:05:40 2025
#   view: test_view_setup
#   -list_not_annotated
#   -list_real_net
#   -list_broken_net
####################################################################

# No not-annotated real net.

# Summary of Annotated Parasitics:
+------------------------------------------------------------------------------+
|    Net Type         |    Count   |   Annotated (%)     | Not Annotated (%)   |
+---------------------+------------+---------------------+---------------------+
| total               |     100742 |      60926 60.48%   |      39816 39.52%   |
| real net (complete) |      60913 |      60913 100.00%   |          0  0.00%   |
| real net (broken)   |          2 |          2 100.00%   |          0  0.00%   |
+------------------------------------------------------------------------------+

+-----------------------------------------------------------------+
| Annotated |    Res (MOhm)   |    Cap (pF)     |    XCap (pF)    |
+-----------+-----------------+-----------------+-----------------+
| Count     |       1140000   |       1120938   |        731012   |
| Value     |       83.7013   |       95.1273   |       24.6238   |
+-----------------------------------------------------------------+
"@

# Save test log
$passLog | Out-File -FilePath IP_project_folder\logs\test_pass_sta_post_route.log -Encoding utf8
```

#### Option 3: Create Test Case with Not-annotated Nets (FAIL)
```powershell
# Create a log with not-annotated nets for FAIL testing
$failLog = @"
report_annotated_parasitics -list_not_annotated -list_real_net -list_broken_net
<CMD> report_annotated_parasitics -list_not_annotated -list_real_net -list_broken_net
####################################################################
# report_annotated_parasitics: Mon Sep 15 08:05:40 2025
#   view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup
#   -list_not_annotated
#   -list_real_net
#   -list_broken_net
####################################################################
#
# list syntax: type: net_name [nrCap Cap nrXCap XCap nrRes Res]
# unit: pF, Ohm

Not annotated real net: [u_pcs_top/u_phy_pcs_reg_ctrl/u_pcs_cdb_reg/UNCONNECTED_HIER_Z314]
Not annotated real net: [u_pcs_top/u_debug_logic/test_net_1]

# Summary of Annotated Parasitics:
+------------------------------------------------------------------------------+
|    Net Type         |    Count   |   Annotated (%)     | Not Annotated (%)   |
+---------------------+------------+---------------------+---------------------+
| total               |     100742 |      60924 60.47%   |      39818 39.53%   |
| real net (complete) |      60911 |      60911 100.00%   |          0  0.00%   |
| real net (broken)   |          2 |          0  0.00%   |          2 100.00%   |
+------------------------------------------------------------------------------+
"@

$failLog | Out-File -FilePath IP_project_folder\logs\test_fail_sta_post_route.log -Encoding utf8
```

### Test Commands

#### Type 1: Global Check (No Waivers)
```powershell
# Navigate to checker directory
cd Check_modules\10.0_STA_DCD_CHECK\scripts\checker

# Ensure configuration is Type 1
# Edit inputs/items/IMP-10-0-0-09.yaml:
#   requirements.value: N/A
#   pattern_items: []
#   waivers.value: N/A
#   waive_items: []

# Run checker
python IMP-10-0-0-09.py

# Check exit code (0 = PASS, 1 = FAIL)
echo "Exit code: $LASTEXITCODE"

# View detailed output
Get-Content ..\..\..\logs\IMP-10-0-0-09.log
Get-Content ..\..\..\reports\IMP-10-0-0-09.rpt
```

**Expected PASS Results (all nets annotated):**
```
PASS:IMP-10-0-0-09:Confirm no SPEF annotation issue in STA.
IMP-10-0-0-09-INFO01: No SPEF annotation issue in STA:
  Severity: Info Occurrence: 2
  - All nets are annotated (view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup)
  - All nets are annotated (view: func_rcss_0p675v_m40c_pcss_cmax_pcss3_setup)

Exit code: 0
```

**Expected FAIL Results (with not-annotated nets):**
```
FAIL:IMP-10-0-0-09:Confirm no SPEF annotation issue in STA.
IMP-10-0-0-09-ERROR01: SPEF annotation issues found in STA:
  Severity: Fail Occurrence: 2
  - [[u_pcs_top/u_phy_pcs_reg_ctrl/u_pcs_cdb_reg/UNCONNECTED_HIER_Z314]] (view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup)
  - [[u_pcs_top/u_debug_logic/test_net_1]] (view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup)
IMP-10-0-0-09-INFO01: No SPEF annotation issue in STA:
  Severity: Info Occurrence: 1
  - All nets are annotated (view: func_rcss_0p675v_m40c_pcss_cmax_pcss3_setup)

Exit code: 1
```

#### Type 2: View-Specific Check
```powershell
# Edit inputs/items/IMP-10-0-0-09.yaml for Type 2:
#   requirements.value: 0
#   pattern_items: 
#     - func_rcss_0p675v_125c_pcss_cmax_pcff3_setup
#     - func_rcss_0p675v_m40c_pcss_cmax_pcss3_setup
#   waivers.value: N/A

python IMP-10-0-0-09.py
echo "Exit code: $LASTEXITCODE"
```

**Expected Output (same as Type 1 for these views):**
```
FAIL:IMP-10-0-0-09:Confirm no SPEF annotation issue in STA.
IMP-10-0-0-09-ERROR01: SPEF annotation issues found in STA:
  Severity: Fail Occurrence: 1
  - [[u_pcs_top/u_phy_pcs_reg_ctrl/u_pcs_cdb_reg/UNCONNECTED_HIER_Z314]] (view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup)
IMP-10-0-0-09-INFO01: No SPEF annotation issue in STA:
  Severity: Info Occurrence: 1
  - All nets are annotated (view: func_rcss_0p675v_m40c_pcss_cmax_pcss3_setup)

Exit code: 1
```

#### Type 3: View-Specific with View-Level Waiver
```powershell
# Edit inputs/items/IMP-10-0-0-09.yaml for Type 3:
#   requirements.value: 0
#   pattern_items: 
#     - func_rcss_0p675v_125c_pcss_cmax_pcff3_setup
#     - func_rcss_0p675v_m40c_pcss_cmax_pcss3_setup
#   waivers.value: 1
#   waive_items:
#     - func_rcss_0p675v_125c_pcss_cmax_pcff3_setup

python IMP-10-0-0-09.py
echo "Exit code: $LASTEXITCODE"
```

**Expected Output (PASS with waiver):**
```
PASS:IMP-10-0-0-09:Confirm no SPEF annotation issue in STA.
IMP-10-0-0-09-INFO01: Waived SPEF annotation issues:
  Severity: Info Occurrence: 1
  - [[u_pcs_top/u_phy_pcs_reg_ctrl/u_pcs_cdb_reg/UNCONNECTED_HIER_Z314]] (view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup)
IMP-10-0-0-09-INFO02: No SPEF annotation issue in STA:
  Severity: Info Occurrence: 1
  - All nets are annotated (view: func_rcss_0p675v_m40c_pcss_cmax_pcss3_setup)

Exit code: 0
```

#### Type 4: Global Check with View-Level Waiver
```powershell
# Edit inputs/items/IMP-10-0-0-09.yaml for Type 4:
#   requirements.value: N/A
#   pattern_items: []
#   waivers.value: 1
#   waive_items:
#     - func_rcss_0p675v_125c_pcss_cmax_pcff3_setup

python IMP-10-0-0-09.py
echo "Exit code: $LASTEXITCODE"
```

**Expected Output (PASS with waiver, all views shown):**
```
PASS:IMP-10-0-0-09:Confirm no SPEF annotation issue in STA.
IMP-10-0-0-09-INFO01: Waived SPEF annotation issues:
  Severity: Info Occurrence: 1
  - [u_pcs_top/u_phy_pcs_reg_ctrl/u_pcs_cdb_reg/UNCONNECTED_HIER_Z314] (view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup)
IMP-10-0-0-09-INFO02: No SPEF annotation issue in STA:
  Severity: Info Occurrence: 2
  - All nets are annotated (view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup)
  - All nets are annotated (view: func_rcss_0p675v_m40c_pcss_cmax_pcss3_setup)

Exit code: 0
```

#### Type 2: Value Check (Strict - No Waivers)
```powershell
# Edit configuration file
notepad ..\..\..\inputs\items\IMP-10-0-0-09.yaml

# Set configuration to:
# requirements:
#   value: 0
#   pattern_items:
#     - "SPEF-1169"
# waivers:
#   value: N/A

# Run checker
python IMP-10-0-0-09.py
```

**Expected PASS Results (0 errors):**
```
[PASS] IMP-10-0-0-09: Confirm no SPEF annotation issue in STA

PASS: 0 SPEF-1169 errors (required: 0)
INFO: Real nets 100% annotated
INFO: No broken nets

Exit code: 0
```

**Expected FAIL Results (errors found):**
```
[FAIL] IMP-10-0-0-09: Confirm no SPEF annotation issue in STA

FAIL: 16 SPEF-1169 errors found (required: 0)
  - Line 321133: Invalid value of '$LAYER' in D_NET
  - Line 676113: Invalid value of '$LAYER' in D_NET
  - Line 942871: Invalid value of '$LAYER' in D_NET
  - ... (13 more instances)

Exit code: 1
```

#### Type 3: Value Check with Waivers
```powershell
# Edit configuration
# requirements:
#   value: 50
#   pattern_items:
#     - "SPEF-1169"
# waivers:
#   value: 20
#   waive_items:
#     - "SPEF-1169"

python IMP-10-0-0-09.py
```

**Expected PASS Results (within waiver limit):**
```
[PASS] IMP-10-0-0-09: Confirm no SPEF annotation issue in STA

INFO: 16 SPEF-1169 warnings waived (20 allowed) [WAIVER]
  - All instances within acceptable limit

Summary: 16 waived, 0 failures

Exit code: 0
```

**Expected FAIL Results (exceeds waiver):**
```
[FAIL] IMP-10-0-0-09: Confirm no SPEF annotation issue in STA

INFO: 20 SPEF-1169 warnings waived [WAIVER]
FAIL: 8 SPEF-1169 errors exceed waiver limit
  - Total: 28 warnings
  - Waiver limit: 20
  - Unwaived: 8

Exit code: 1
```

#### Type 4: Boolean with Waivers
```powershell
# Edit configuration
# requirements:
#   value: N/A
# waivers:
#   value: 1
#   waive_items:
#     - "Pre-route phase"

python IMP-10-0-0-09.py
```

**Expected Results (Always PASS):**
```
[PASS] IMP-10-0-0-09: Confirm no SPEF annotation issue in STA

INFO: Check waived [WAIVER]
  Reason: Pre-route phase

INFO: 16 SPEF-1169 warnings detected (waived) [WAIVER]

Exit code: 0
```

### Viewing Results

```powershell
# View summary log (grouped by category)
Get-Content ..\..\..\logs\IMP-10-0-0-09.log

# View detailed report (line-by-line details)
Get-Content ..\..\..\reports\IMP-10-0-0-09.rpt

# View JSON output (machine-readable)
Get-Content ..\..\..\outputs\IMP-10-0-0-09_result.json | ConvertFrom-Json

# Search for specific issues
Select-String -Path ..\..\..\logs\IMP-10-0-0-09.log -Pattern "FAIL|ERROR|WARN"

# Check annotation statistics
Select-String -Path ..\..\..\reports\IMP-10-0-0-09.rpt -Pattern "real net|broken|annotated"
```

---

## Notes

### Understanding Not-annotated Nets

**What causes not-annotated real nets?**
- SPEF file missing net definition
- Netlist mismatch between layout and timing database
- RC extraction tool skipped certain nets
- SPEF-to-design name mapping issues
- Hierarchical design with missing block-level SPEF files

**Net Types (from STA log annotation summary):**
- **real net (complete)**: Must be 100% annotated - these are timing-critical nets
- **real net (broken)**: Should be 0 - indicates corrupted parasitic data
- **1-term: no load**: Expected to be not-annotated - single-pin nets, not timing paths
- **0-term: floating**: Expected to be not-annotated - unconnected nets
- **assign**: Expected to be not-annotated - wire assignments, not real nets

**Note**: Only "real net (complete)" must have 100% annotation. Missing annotation on 0-term, 1-term, or assign nets is expected and acceptable.

### Waiver Strategies

**View-level Waivers (Recommended for Type 3/4):**
```yaml
waive_items:
  - func_rcss_0p675v_125c_pcss_cmax_pcff3_setup  # Waive entire view
```
Use when:
- Entire timing view is under development
- View represents non-critical scenario (e.g., test mode)
- Known extraction issues for specific corner

**Net-level Waivers (Precise control):**
```yaml
waive_items:
  - "[u_pcs_top/debug_net] (view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup)"
```
Use when:
- Specific nets are debug/test-only paths
- Known tool limitation for certain net patterns
- Isolated extraction failures on non-critical nets

### Best Practices

1. **Type 1 (Global, No Waivers)**: 
   - Use for: Final tapeout sign-off validation
   - Ensures: ALL views have 100% annotation
   - When to use: Gate before tape-out, strict quality check

2. **Type 2 (View-specific, No Waivers)**:
   - Use for: Critical corner validation (e.g., setup@slow, hold@fast)
   - Ensures: Specified views are fully annotated
   - When to use: Incremental checks during development

3. **Type 3 (View-specific with Waivers)**:
   - Use for: Production flow with known exceptions
   - Ensures: Critical views pass, allows controlled waivers
   - When to use: Continuous integration, regression testing

4. **Type 4 (Global with Waivers)**:
   - Use for: Early development stages
   - Ensures: Track annotation status without blocking
   - When to use: Pre-route, early floorplan, bring-up phase

### Checker Behavior Details

**Multi-file Processing:**
- Processes all input_files in sequence
- Aggregates not-annotated nets from all files
- Associates each net with its view from log file
- Displays source file path and line number in reports

**View Filtering (Type 1 only):**
- PASS views (no not-annotated nets) → INFO01
- FAIL views (with not-annotated nets) → ERROR01
- Failed views are excluded from INFO section

**Output Format:**
- **Log file**: Grouped by INFO01/ERROR01 with severity and occurrence count
- **Report file**: Line-by-line detail with file path and line number
- **Display**: `[[net_name]] (view: view_name)` format for clarity

### Limitations

- **Log Format Dependency**: Assumes Cadence Innovus/Tempus STA log format
  - Requires `report_annotated_parasitics` command output
  - Needs "# view:" marker for view extraction
  - Other STA tools may need format adaptation

- **Detection Scope**: Only detects explicitly listed not-annotated nets
  - Does not validate SPEF file content directly
  - Cannot detect silent annotation errors (wrong values)
  - Relies on STA tool's annotation reporting

- **View Name Extraction**: Depends on log containing "# view:" lines
  - Per-view log files recommended for accurate view tracking
  - Missing view markers may result in "Unknown" view labels

### Troubleshooting

**Issue: Not-annotated nets detected but SPEF file exists**  
**Root Cause**: Netlist mismatch between layout and timing database  
**Solution**: 
- Verify SPEF was generated from same netlist as timing database
- Check for ECO changes between layout freeze and RC extraction
- Regenerate SPEF after netlist updates

**Issue: All nets in a specific view are not-annotated**  
**Root Cause**: SPEF file not loaded for that view/corner  
**Solution**:
- Check STA script: verify `read_spef` command includes correct corner
- Verify SPEF file path in STA command script
- Check for missing RC corner in extraction flow

**Issue: False negatives - checker reports PASS but timing seems wrong**  
**Root Cause**: Checker only detects missing annotation, not incorrect values  
**Solution**:
- Review annotation statistics in full STA log
- Compare Res/Cap/XCap values against expected ranges
- Use separate checks for parasitic value sanity (not in this checker)

**Issue: View-level waiver not working**  
**Root Cause**: View name mismatch between waive_items and log file  
**Solution**:
- Check exact view name in log: `grep "# view:" sta_post_route.log`
- Ensure view name in waive_items matches exactly (case-sensitive)
- Use net-level waiver as fallback if view name varies

**Issue: Multiple views in same log file causing confusion**  
**Root Cause**: Single log contains multiple `report_annotated_parasitics` runs  
**Solution**:
- Use per-view log files (recommended): `func_*_sta_post_route.log`
- Separate logs ensure accurate view-to-net association
- Configure input_files to list all per-view logs

**Issue: "Unknown" view in output**  
**Root Cause**: Log file missing "# view:" marker before not-annotated net  
**Solution**:
- Ensure STA command uses `-list_not_annotated` flag
- Check log has proper section headers
- Manually add view info to waive_items using actual net names

### Related Checks

This checker focuses solely on not-annotated nets. Consider these complementary checks:

- **SPEF Parsing Errors**: Check for `**ERROR: (SPEF-` messages (separate checker)
- **RC Extraction QA**: Validate parasitic values are in expected ranges
- **Netlist Consistency**: Verify SPEF netlist matches timing database
- **Annotation Coverage**: Track annotation percentage trends over time
description: Confirm no SPEF annotation issue in STA.
requirements:
  value: 50
  pattern_items:
    - "SPEF-1169"
    - "SPEF-0301"
waivers:
  value: 20
  waive_items:
    - "SPEF-1169"
```

### Expected Behavior

**Waiver Logic:**
- `SPEF-1169` errors up to 20 instances are waived (marked as INFO with `[WAIVER]` suffix)
- Remaining errors above 20 instances are flagged as FAIL
- `SPEF-0301` errors are not waived - any instance causes FAIL

**PASS Conditions:**
- Total SPEF-1169 errors ≤ 20 (all waived)
- No SPEF-0301 errors found

**Output Examples:**
```
INFO: 16 SPEF-1169 warnings waived (threshold: 20) [WAIVER]
  - Invalid $LAYER parameter in D_NET line 321133
  - Invalid $LAYER parameter in D_NET line 676113
  - ... (14 more instances)
PASS: No SPEF-0301 errors found
Summary: 16 waived, 0 failures
```

**FAIL Conditions:**
- SPEF-1169 count > 20 (waiver exceeded)
- Any SPEF-0301 errors present

**Output Examples:**
```
INFO: 20 SPEF-1169 warnings waived [WAIVER]
FAIL: 8 SPEF-1169 errors exceed waiver limit (20)
  - Line 4185758: Invalid $LAYER parameter
  - Line 4234921: Invalid $LAYER parameter
  - ... (6 more unwaived)
FAIL: 2 SPEF-0301 errors found (not waived)
Summary: 20 waived, 10 failures
```

---

## Type 4: Boolean Check with Waivers

### Use Case
Allow the entire SPEF annotation check to be temporarily waived during specific project phases (e.g., pre-implementation, early floorplan). Use when SPEF quality issues are expected and acceptable in the current stage.

### Configuration Example

```yaml
description: Confirm no SPEF annotation issue in STA.
requirements:
  value: N/A
  pattern_items: []
input_files: 
  - IP_project_folder/logs/sta_post_route.log
waivers:
  value: 1
  waive_items:
    - "Pre-implementation phase - SPEF quality not critical"
    - "Using preliminary RC extraction"
```

### Expected Behavior

**When waivers.value > 0:**
- All SPEF errors/warnings are reported as INFO with `[WAIVER]` suffix
- Check always returns PASS
- Waiver reasons are documented in output

**Output Examples:**
```
INFO: SPEF check waived [WAIVER]
  Reason: Pre-implementation phase - SPEF quality not critical
INFO: 3 SPEF-0102 errors found [WAIVER]
INFO: 28 SPEF-1169 warnings found [WAIVER]
INFO: 1506 nets missing in SPEF [WAIVER]
PASS: Check waived per project phase
```

**When waivers.value = 0 (Forced PASS Mode):**
- All errors converted to INFO with `[WAIVED_AS_INFO]` suffix
- Waive_items shown as INFO with `[WAIVED_INFO]` suffix
- Always returns PASS (useful for debugging/transition)

**Output Examples:**
```
INFO: Pre-implementation phase - SPEF quality not critical [WAIVED_INFO]
INFO: SPEF-0102 errors found (converted to info) [WAIVED_AS_INFO]
INFO: SPEF-1169 warnings found (converted to info) [WAIVED_AS_INFO]
PASS: All issues waived (waiver=0 mode)
```

---

## Testing

### Test Data Preparation

1. **Create test STA log with SPEF issues:**
```powershell
# Copy example log
cp IP_project_folder/logs/sta_post_route.log IP_project_folder/logs/sta_test.log

# Or create minimal test case
@"
SPEF files for RC Corner test_corner:
Top-level spef file './test.spef.gz'.
Start spef parsing (MEM=1000.00).
**WARN: (SPEF-1169): Invalid value of parameter in D_NET line 100.
**ERROR: (SPEF-0102): Net definition error at line 200.
End spef parsing (MEM=1005.00 CPU=0:00:10.0).
10 nets are missing in SPEF file.
"@ | Out-File IP_project_folder/logs/sta_test.log
```

2. **Update configuration YAML:**
```powershell
# Point to test log
notepad Check_modules/10.0_STA_DCD_CHECK/inputs/items/IMP-10-0-0-09.yaml
```

### Test Commands

#### Type 1: Informational Check
```powershell
# Navigate to checker directory
cd Check_modules/10.0_STA_DCD_CHECK/scripts/checker

# Run checker
python IMP-10-0-0-09.py

# Expected: PASS with INFO about warnings
# Output: ../logs/IMP-10-0-0-09.log
# Report: ../reports/IMP-10-0-0-09.rpt
```

**Expected PASS Results:**
```
[PASS] IMP-10-0-0-09
INFO: 16 SPEF-1169 warnings found
INFO: 1506 nets missing (1-term no load)
INFO: 69572 real nets annotated (100%)
```

**Expected FAIL Results (if errors present):**
```
[FAIL] IMP-10-0-0-09
ERROR: 1 SPEF-0102 error detected
```

#### Type 2: Value Check (Strict)
```powershell
# Edit config to set requirements.value = 0
# Edit config to add pattern_items: ["SPEF-0102", "SPEF-1169"]

python IMP-10-0-0-09.py
```

**Expected PASS Results:**
```
[PASS] IMP-10-0-0-09
PASS: 0 SPEF-0102 errors (required: 0)
PASS: 0 SPEF-1169 errors (required: 0)
```

**Expected FAIL Results:**
```
[FAIL] IMP-10-0-0-09
FAIL: 16 SPEF-1169 errors found (required: 0)
  Line 321133, 676113, ... (16 total)
```

#### Type 3: Value Check with Waivers
```powershell
# Edit config:
# requirements.value = 50
# requirements.pattern_items = ["SPEF-1169"]
# waivers.value = 20
# waivers.waive_items = ["SPEF-1169"]

python IMP-10-0-0-09.py
```

**Expected PASS Results (within waiver limit):**
```
[PASS] IMP-10-0-0-09
INFO: 16 SPEF-1169 warnings waived [WAIVER]
Summary: 16 waived, 0 failures
```

**Expected FAIL Results (exceeds waiver):**
```
[FAIL] IMP-10-0-0-09
INFO: 20 SPEF-1169 warnings waived [WAIVER]
FAIL: 8 SPEF-1169 errors exceed waiver (total: 28, limit: 20)
```

#### Type 4: Boolean with Waivers
```powershell
# Edit config:
# requirements.value = N/A
# waivers.value = 1
# waivers.waive_items = ["Pre-route phase"]

python IMP-10-0-0-09.py
```

**Expected Results (Always PASS):**
```
[PASS] IMP-10-0-0-09
INFO: SPEF check waived [WAIVER]
  Reason: Pre-route phase
INFO: All SPEF issues waived
```

### Viewing Results

```powershell
# View summary log (grouped format)
cat ../logs/IMP-10-0-0-09.log

# View detailed report (line-by-line details)
cat ../reports/IMP-10-0-0-09.rpt

# View JSON output (machine-readable)
cat ../outputs/IMP-10-0-0-09_result.json
```

---

## Notes

### Understanding Not-annotated Nets

**What causes not-annotated real nets?**
- SPEF file missing net definition
- Netlist mismatch between layout and timing database
- RC extraction tool skipped certain nets
- SPEF-to-design name mapping issues
- Hierarchical design with missing block-level SPEF files

**Net Types (from STA log annotation summary):**
- **real net (complete)**: Must be 100% annotated - these are timing-critical nets
- **real net (broken)**: Should be 0 - indicates corrupted parasitic data
- **1-term: no load**: Expected to be not-annotated - single-pin nets, not timing paths
- **0-term: floating**: Expected to be not-annotated - unconnected nets
- **assign**: Expected to be not-annotated - wire assignments, not real nets

**Note**: Only "real net (complete)" must have 100% annotation. Missing annotation on 0-term, 1-term, or assign nets is expected and acceptable.

### Waiver Strategies

**View-level Waivers (Recommended for Type 3/4):**
```yaml
waive_items:
  - func_rcss_0p675v_125c_pcss_cmax_pcff3_setup  # Waive entire view
```
Use when:
- Entire timing view is under development
- View represents non-critical scenario (e.g., test mode)
- Known extraction issues for specific corner

**Net-level Waivers (Precise control):**
```yaml
waive_items:
  - "[u_pcs_top/debug_net] (view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup)"
```
Use when:
- Specific nets are debug/test-only paths
- Known tool limitation for certain net patterns
- Isolated extraction failures on non-critical nets

### Best Practices

1. **Type 1 (Global, No Waivers)**: 
   - Use for: Final tapeout sign-off validation
   - Ensures: ALL views have 100% annotation
   - When to use: Gate before tape-out, strict quality check

2. **Type 2 (View-specific, No Waivers)**:
   - Use for: Critical corner validation (e.g., setup@slow, hold@fast)
   - Ensures: Specified views are fully annotated
   - When to use: Incremental checks during development

3. **Type 3 (View-specific with Waivers)**:
   - Use for: Production flow with known exceptions
   - Ensures: Critical views pass, allows controlled waivers
   - When to use: Continuous integration, regression testing

4. **Type 4 (Global with Waivers)**:
   - Use for: Early development stages
   - Ensures: Track annotation status without blocking
   - When to use: Pre-route, early floorplan, bring-up phase

### Checker Behavior Details

**Multi-file Processing:**
- Processes all input_files in sequence
- Aggregates not-annotated nets from all files
- Associates each net with its view from log file
- Displays source file path and line number in reports

**View Filtering (Type 1 only):**
- PASS views (no not-annotated nets) → INFO01
- FAIL views (with not-annotated nets) → ERROR01
- Failed views are excluded from INFO section

**Output Format:**
- **Log file**: Grouped by INFO01/ERROR01 with severity and occurrence count
- **Report file**: Line-by-line detail with file path and line number
- **Display**: `[[net_name]] (view: view_name)` format for clarity

### Limitations

- **Log Format Dependency**: Assumes Cadence Innovus/Tempus STA log format
  - Requires `report_annotated_parasitics` command output
  - Needs "# view:" marker for view extraction
  - Other STA tools may need format adaptation

- **Detection Scope**: Only detects explicitly listed not-annotated nets
  - Does not validate SPEF file content directly
  - Cannot detect silent annotation errors (wrong values)
  - Relies on STA tool's annotation reporting

- **View Name Extraction**: Depends on log containing "# view:" lines
  - Per-view log files recommended for accurate view tracking
  - Missing view markers may result in "Unknown" view labels

### Troubleshooting

**Issue: Not-annotated nets detected but SPEF file exists**  
**Root Cause**: Netlist mismatch between layout and timing database  
**Solution**: 
- Verify SPEF was generated from same netlist as timing database
- Check for ECO changes between layout freeze and RC extraction
- Regenerate SPEF after netlist updates

**Issue: All nets in a specific view are not-annotated**  
**Root Cause**: SPEF file not loaded for that view/corner  
**Solution**:
- Check STA script: verify `read_spef` command includes correct corner
- Verify SPEF file path in STA command script
- Check for missing RC corner in extraction flow

**Issue: False negatives - checker reports PASS but timing seems wrong**  
**Root Cause**: Checker only detects missing annotation, not incorrect values  
**Solution**:
- Review annotation statistics in full STA log
- Compare Res/Cap/XCap values against expected ranges
- Use separate checks for parasitic value sanity (not in this checker)

**Issue: View-level waiver not working**  
**Root Cause**: View name mismatch between waive_items and log file  
**Solution**:
- Check exact view name in log: `grep "# view:" sta_post_route.log`
- Ensure view name in waive_items matches exactly (case-sensitive)
- Use net-level waiver as fallback if view name varies

**Issue: Multiple views in same log file causing confusion**  
**Root Cause**: Single log contains multiple `report_annotated_parasitics` runs  
**Solution**:
- Use per-view log files (recommended): `func_*_sta_post_route.log`
- Separate logs ensure accurate view-to-net association
- Configure input_files to list all per-view logs

**Issue: "Unknown" view in output**  
**Root Cause**: Log file missing "# view:" marker before not-annotated net  
**Solution**:
- Ensure STA command uses `-list_not_annotated` flag
- Check log has proper section headers
- Manually add view info to waive_items using actual net names

### Related Checks

This checker focuses solely on not-annotated nets. Consider these complementary checks:

- **SPEF Parsing Errors**: Check for `**ERROR: (SPEF-` messages (separate checker)
- **RC Extraction QA**: Validate parasitic values are in expected ranges
- **Netlist Consistency**: Verify SPEF netlist matches timing database
- **Annotation Coverage**: Track annotation percentage trends over time
