# Developer Task Prompts - Generic Template

**Last Updated**: December 11, 2025 (Template Library v1.1.0)

## Overview

This template guides checker development in 4 steps:

- **Step 1**: Update Configuration (2 min)
- **Step 2**: Analyze Input Files & Write README (10 min)
- **Step 3**: Implement Python Code (30-60 min)
- **Step 4**: Test & Verify (10 min)

**Total Time**: ~1 hour per checker

---

## Step 1: Update Configuration

```
Please update the configuration for checker {ITEM_ID}.

File: Check_modules/{MODULE}/inputs/items/{ITEM_ID}.yaml

====================================================================================
BLOCK 1 – Validate Assigned Files (MANDATORY)
====================================================================================
1. Open the YAML and confirm `input_files` point to real project data
2. Resolve relative paths against module directory; avoid placeholders
3. Document missing files or request replacements before proceeding

====================================================================================
BLOCK 2 – Maintain Default Type 1 Settings
====================================================================================
1. Keep `requirements.value: N/A` unless Type 2/3 logic is approved
2. Keep `waivers.value: N/A` for Type 1/2 scenarios
3. Do not invent pattern_items until after Step 2 analysis

====================================================================================
BLOCK 3 – Sanity Checklist Before Moving On
====================================================================================
1. YAML parses with `python -c "import yaml; yaml.safe_load(open('{ITEM_PATH}'))"`
2. Paths resolve on both Windows and Linux agents
3. Comments explain any temporary assumptions (use `# TODO:` tags sparingly)
```

---

## Step 2: Analyze Input Files & Write README

```
Please update the README file for checker {ITEM_ID}.

File: Check_modules/{MODULE}/scripts/doc/{ITEM_ID}_README.md

IMPORTANT: Before writing the README, you MUST first analyze the actual input files to understand the real data format.

====================================================================================
PHASE 1: Analyze Input Files (MANDATORY - Do This First!)
====================================================================================

File Location: Check_modules/{MODULE}/inputs/
Configuration: Check_modules/{MODULE}/inputs/items/{ITEM_ID}.yaml

Analysis Steps:
1. Read Configuration & Identify Files
   - Open {ITEM_ID}.yaml and locate input_files list
   - Note if single file or multiple files (aggregation required?)
   - Find files in IP_project_folder/ or module inputs/
2. Examine Input File Structure
   - Read first 50-100 lines of actual files
   - Identify format: log/report/JSON/CSV/custom
   - Note key sections, headers, delimiters
3. Define Output Format FIRST (determines parsing granularity)
   - INFO01: What to display? (file paths? views? items? counts?)
   - ERROR01: What failures look like? (net names? error codes? violations?)
   - Display format: "[item_name] (view: view_name)" vs "error_code: message"
   - Determines what data must be extracted and associated during parsing
4. Identify Parsing Patterns (based on output requirements)
   - Provide actual regex, e.g. r'\*\*ERROR:\s*\(SPEF-(\d+)\)\s*(.+)'
   - Decide data to extract: error codes, net names, view associations, line numbers
   - Plan multi-file handling: aggregate vs per-file results
   - Note edge cases: empty files, missing sections, format variations
5. Document Real Data Samples (3-5 lines minimum)
   - Sample Line 1: <paste actual content>
   - Sample Line 2: <paste actual content>
   - Sample Line 3: <paste actual content>
   - Pattern: <actual regex>
   - Extraction: <what gets captured>
6. Waiver Tag Rules (for output_formatter.py)
   - waivers.value > 0 (Type 3/4): append "[WAIVER]" suffix in reason field
   - waivers.value = 0 (Type 1/2): append "[WAIVED_AS_INFO]" suffix in reason field
   - Name field NEVER contains tags (used for matching)

Critical Reminders:
- Define output format BEFORE writing parsing logic
- Analyze real files and capture actual samples
- Check for multi-file scenarios (loop through valid_files)
- Do not guess patterns or write README without real data

====================================================================================
PHASE 2: Write README (After Completing Analysis)
====================================================================================

Requirements:
1. Delete all TODO placeholders
2. Fill in Overview
   - Category: [Based on check type]
   - Input Files: All files from {ITEM_ID}.yaml
   - Description: What is validated and why it matters
3. Fill in Check Logic
   - Parsing: HOW data is extracted (patterns, regex, sections)
   - Detection: Step-by-step PASS/FAIL logic
   - Use real examples from Phase 1 analysis
4. Provide 4 Type examples
   - Type 1: Boolean Check
   - Type 2: Value Check
   - Type 3: Value Check with Waiver Logic (Type 2 + waiver support)
   - Type 4: Boolean Check with Waiver Logic (Type 1 + waiver support)
   - Each example covers use case, YAML config, expected behavior, sample output
5. Add Testing section
   - Test data creation steps
   - Commands for each type
   - Expected PASS/FAIL outputs
   - All examples use real patterns from Phase 1 (copy-paste ready)
```

---

## Step 3: Implement Python Code

```
Please implement the checker logic for {ITEM_ID}.

File: Check_modules/{MODULE}/scripts/checker/{ITEM_ID}.py
Task: {DESCRIPTION}

====================================================================================
BLOCK 1 – Template Setup (MANDATORY)
====================================================================================
1. Review `Check_modules/common/checker_templates/README.md` (30+ examples) before coding
2. Import and inherit REQUIRED mixins in this exact order:
       from checker_templates.waiver_handler_template import WaiverHandlerMixin
       from checker_templates.output_builder_template import OutputBuilderMixin
       from checker_templates.input_file_parser_template import InputFileParserMixin  # optional but recommended
3. Class skeleton must inherit from BaseChecker + mixins (InputFileParserMixin first if used)
4. Reference migrations: IMP-10-0-0-10 (all mixins), IMP-10-0-0-02 (template reuse)

====================================================================================
BLOCK 2 – File Header & Auto Type Detection
====================================================================================
1. Update header comment with Purpose/Logic/Auto-Type/Waiver rules (see IMP-10-0-0-09.py)
2. Document logic in 5-8 bullet steps (parse → extract → validate → apply waivers)
3. Include "Refactored: {date} (Using checker_templates)" line
4. Confirm BaseChecker.detect_checker_type() covers all four types as outlined:
       Type 1 → requirements.value N/A, pattern_items [] (empty), waivers N/A/0
       Type 2 → requirements.value > 0, pattern_items [...] (defined), waivers N/A/0
       Type 3 → requirements.value > 0, pattern_items [...] (defined), waivers > 0
       Type 4 → requirements.value N/A, pattern_items [] (empty), waivers > 0
   Note: requirements.value indicates number of patterns for config validation (doesn't affect PASS/FAIL)

====================================================================================
BLOCK 3 – Implement _parse_input_files()
====================================================================================
1. Validate inputs with `self.validate_input_files()`; raise ConfigurationError for missing files
2. Use template helpers (parse_log_with_patterns, parse_section, extract_file_references, normalize_command)
3. Return aggregated dict, e.g.:
       {
          'netlist_files': [...],
          'violations': [...],
          'metadata': {...}
       }
4. Store frequently reused data on `self` (e.g., self._netlist_files) for later type execution
5. Log anomalies or edge cases; avoid silent failures

====================================================================================
BLOCK 4 – Execute Methods by Checker Type
====================================================================================
Type 1 (_execute_type1)
   - Boolean check without pattern_items search
   - Use `build_complete_output(found_items=..., missing_items=...)`
   - PASS/FAIL based on custom checker logic (file exists, config valid, etc.)

Type 2 (_execute_type2)
   - Search pattern_items in input files
   - found_items = patterns found; missing_items = patterns not found
   - PASS/FAIL depends on purpose: Violation Check (found=bad) vs Requirement Check (found=good)
   - Config validation: check len(pattern_items) == requirements.value (warns if mismatch)
   - Pass `extra_items` to `build_complete_output()` for unexpected findings
   - Let template auto-handle waiver=0 conversions

Type 3 (_execute_type3)
   - Same search logic as Type 2: Search pattern_items in input files
   - Additional waiver classification: match found_items against waive_items
   - Use `self.parse_waive_items()` and `self.match_waiver_entry()`
   - Call `build_complete_output(waived_items=..., unwaived_items=..., waive_dict=..., unused_waivers=...)`
   - PASS if all found_items (violations) are waived
   - Append "[WAIVER]" in DetailItem.reason only (never in name)

Type 4 (_execute_type4)
   - Same boolean check as Type 1 (no pattern_items search)
   - Additional waiver classification: match violations against waive_items
   - Convert failures to waived/unwaived using mixin helpers
   - Always pass `has_waiver_value=True` when calling `build_complete_output()`
   - PASS if all violations are waived

Framework APIs & Tips
   - DetailItem(severity, name, line_number, file_path, reason)
   - create_check_result(status, details, summary)
   - Severity.INFO / Severity.ERROR / Severity.WAIVE constants
   - `build_complete_output()` handles descriptions/reasons automatically when parameters provided

Common Pitfalls to Avoid
   - Skipping mandatory mixins (OutputBuilderMixin & WaiverHandlerMixin)
   - Re-implementing output formatting instead of using `build_complete_output()`
   - Manually normalizing commands; use `self.normalize_command()`
   - Adding waiver tags to DetailItem.name (must stay in reason)
   - Forgetting to document unused waivers (pass `unused_waivers` list)
   - Leaving TODO logic from template skeletons

Pre-Commit Checklist for Step 3
   - Pylint/mypy clean run (if configured)
   - All Type methods exercised with sample data (manual or regression test)
   - README logic section updated to match implementation details
```

---

## Step 4: Testing

```
Test checker {ITEM_ID} using the Regression Testing Framework.

Block 1 – Prepare Test Inputs
   - Create PASS and FAIL scenarios (adjust inputs/items/{ITEM_ID}.yaml as needed)
   - Populate input files with realistic data taken from project sources

Block 2 – Quick Sanity Run (local execution)
   - cd Check_modules/{MODULE}/scripts/checker
   - python {ITEM_ID}.py
   - Get-Content ..\logs\{ITEM_ID}.log | Select-Object -First 30
   - Get-Content ..\reports\{ITEM_ID}.rpt

Block 3 – Regression Snapshot Workflow
   - python common/regression_testing/create_all_snapshots.py --modules {MODULE} --checkers {ITEM_ID} --force
   - (Optional) python common/regression_testing/verify_all_snapshots.py --modules {MODULE} --checkers {ITEM_ID}
   - Confirm outputs/{ITEM_ID}.yaml and reports/{ITEM_ID}.rpt are updated

Block 4 – Final Verification & Sign-off
   - Ensure terminal reports "Success Rate: 100.0%"
   - Confirm README Check Logic matches implemented parsing
   - Validate Type 1/2/3/4 examples against actual behavior
   - Document any waivers/tests added for regression tracking

Success Criteria:
   - Snapshots refreshed without diff failures
   - README fully aligned with implementation
   - No crashes, missing parameters, or unaccounted waivers
```

---

## Quick Reference

**Development Workflow Summary:**

```

Step 1: Update Configuration (2 min)
→ Edit {ITEM_ID}.yaml, set input_files paths

Step 2: Analyze & Document (10 min)
→ Phase 1: Analyze real input files (define output format first!)
→ Phase 2: Write README (Overview, Check Logic, 4 Type examples, Testing)

Step 3: Implement Code (30-60 min)
→ Use templates: WaiverHandlerMixin + OutputBuilderMixin
→ Implement: _parse_input_files() + _execute_type1/2/3/4()

Step 4: Test & Verify (10 min)
→ Create test data, run snapshot tool
→ Verify outputs and README accuracy

```

**Files Modified:**
1. `inputs/items/{ITEM_ID}.yaml` - Configuration
2. `scripts/doc/{ITEM_ID}_README.md` - Documentation
3. `scripts/checker/{ITEM_ID}.py` - Implementation

**Completion Checklist:**
- ☐ Configuration updated with correct input_files
- ☐ README complete (no TODOs)
- ☐ All 4 types implemented
- ☐ Test data created
- ☐ Snapshot tests pass
- ☐ README matches implementation

---

## Usage Instructions

**For AI Assistant:**

Replace placeholders:
- `{ITEM_ID}`: e.g., IMP-10-0-0-10
- `{MODULE}`: e.g., 10.0_STA_DCD_CHECK
- `{DESCRIPTION}`: e.g., "Confirm check full path group timing reports"

**For Developers:**

1. Get assignment from `work_dispatcher.py`
2. Copy Step 1-4 prompts, replace placeholders
3. Follow steps sequentially with AI or manually
4. Verify checklist before committing

---

## Example: Complete Workflow for IMP-10-0-0-10

### Step 1: Update Configuration

```

Edit: Check_modules/10.0_STA_DCD_CHECK/inputs/items/IMP-10-0-0-10.yaml

Set input_files:

- "../../IP_project_folder/reports/timing_in2out.rpt"
- "../../IP_project_folder/reports/timing_in2reg.rpt"
- "../../IP_project_folder/reports/timing_reg2out.rpt"
- "../../IP_project_folder/reports/timing_reg2reg.rpt"
- "../../IP_project_folder/reports/timing_default.rpt"
- "../../IP_project_folder/reports/timing_cgdefault.rpt"

```

### Step 2: README (Filled)

```

File: Check_modules/10.0_STA_DCD_CHECK/scripts/doc/IMP-10-0-0-10_README.md

Phase 1: Analyze input files (6 timing reports)
Phase 2: Write README

Requirements:

1. Delete TODO placeholders
2. Overview:
   - Category: Timing Analysis - Path Group Reports
   - Input Files: timing_in2out.rpt, timing_in2reg.rpt, ...
   - Description: Verifies standard timing path group reports exist
3. Check Logic:
   - Parsing: Check reports/ directory for 6 files
   - Detection: PASS if all exist, FAIL if missing
4. Add 4 Type examples
5. Add Testing section

```

### Step 3: Implementation (Filled)

```

File: Check_modules/10.0_STA_DCD_CHECK/scripts/checker/IMP-10-0-0-10.py

Implement:

1. _parse_input_files(): Check 6 timing reports exist
2. _execute_type1/2/3/4(): All 4 types

Use templates: WaiverHandlerMixin + OutputBuilderMixin

```

### Step 4: Testing (Filled)

```

1. Create test reports in inputs/reports/
2. Run: python common/regression_testing/create_all_snapshots.py --modules 10.0_STA_DCD_CHECK --checkers IMP-10-0-0-10 --force
3. Verify snapshot and outputs
4. Verify README accuracy

```

```
