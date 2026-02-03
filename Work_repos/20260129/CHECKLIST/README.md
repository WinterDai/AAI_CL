# CHECKLIST - VLSI Design Verification Automation Framework

A Python-based automated verification framework for standardized checks across VLSI design stages (synthesis, physical implementation, timing analysis, etc.).

## 🎯 Project Overview

CHECKLIST is a modular automation framework that executes standardized design checks at various stages of the VLSI design flow. The framework features a unified BaseChecker architecture with automatic type detection, supporting four distinct checker types with sophisticated waiver management.

## 📋 Table of Contents

- [Recent Updates](#recent-updates)
- [Architecture](#architecture)
- [Checker Types](#checker-types)
- [Quick Start](#quick-start)
- [Directory Structure](#directory-structure)
- [Development Guide](#development-guide)
- [Configuration](#configuration)
- [Contributing](#contributing)

---

## 🚀 Recent Updates

### Latest Updates

#### December 15, 2025 - Path Portability Architecture ⭐

**${CHECKLIST_ROOT} Variable System** - Fully Git-friendly configuration

- 2-Phase workflow (placeholder → merge, variables preserved)
- Runtime variable expansion in base_checker.py
- 48/69 items files using portable paths
- Cross-platform compatible (Windows/Linux)

#### December 11, 2025 - Template Library v1.1.0

**Template Library v1.1.0 Enhancements**

- Added `normalize_command()` utility for consistent text normalization
- Enhanced waiver matching with normalizer callback support
- Fixed log deduplication bug
- IMP-10-0-0-02: 738 → 697 lines (-5.6% via template reuse)

#### December 9, 2025 - Checker Template Library ⭐

**3 Reusable Mixins** (`Check_modules/common/checker_templates/`)

- InputFileParserMixin: 7 parsing patterns (953 lines)
- WaiverHandlerMixin: 8 waiver patterns (637 lines)
- OutputBuilderMixin: 6 output formatters (773 lines)
- **Benefits**: 41-70% code reduction, 100% automatic waiver=0 handling

**Other December 2025 Updates:**

- Regression testing framework with snapshot-based validation
- YAML format optimization for Windows paths (single quotes)
- Migrated 13.0 POST_PD_EQUIVALENCE_CHECK (8 checkers)
- Created 6.0 POST_SYNTHESIS_LEC_CHECK module
- Waiver tag rules standardization ([WAIVER], [WAIVED_AS_INFO], [WAIVED_INFO])

---

## 🏗️ Architecture

### Core Components

```
CHECKLIST/
├── Check_modules/
│   ├── common/                          # Framework core
│   │   ├── base_checker.py              # Unified BaseChecker class
│   │   ├── output_formatter.py          # Log/Report formatting
│   │   ├── check_flowtool.py            # Execution engine
│   │   ├── write_summary_yaml.py        # YAML summary generator
│   │   └── parse_interface.py           # DATA_INTERFACE distribution
│   │
│   ├── 1.0_LIBRARY_CHECK/               # Library verification
│   ├── 5.0_SYNTHESIS_CHECK/             # Synthesis verification
│   ├── 6.0_POST_SYNTHESIS_LEC_CHECK/    # Post-synthesis LEC ⭐ NEW
│   ├── 10.0_STA_DCD_CHECK/              # Static timing analysis
│   ├── 13.0_POST_PD_EQUIVALENCE_CHECK/  # Post-PD LEC ⭐ MIGRATED
│   └── [other modules]/
│
├── Data_interface/
│   └── outputs/
│       └── DATA_INTERFACE.yaml          # Global data paths
│
├── IP_project_folder/
│   ├── reports/                         # Design tool outputs
│   └── logs/
│
└── Work/
    ├── Results/                         # Aggregated results
    └── Reports/                         # HTML visualizations
```

### BaseChecker Architecture

All checkers inherit from a unified base class:

```python
class BaseChecker(ABC):
    def __init__(self, check_module: str, item_id: str, item_desc: str)
    def init_checker(self, script_path: Path) -> None
    def detect_checker_type(self, custom_requirements=None) -> int  # 1/2/3/4
  
    @abstractmethod
    def execute_check(self) -> CheckResult
  
    def run(self) -> None  # Main entry point
```

**Key Features:**

- Automatic type detection (Type 1/2/3/4)
- Unified configuration loading
- Standardized output formatting
- ConfigurationError exception handling
- Cross-module configuration references

---

## 🔍 Checker Types

The framework supports four checker types with automatic detection based on configuration:

### Type Detection Logic

```python
# BaseChecker.detect_checker_type() automatically determines:

if requirements.value > 0 AND pattern_items AND waivers.value > 0:
    → Type 3: Value comparison WITH waiver logic
  
elif requirements.value > 0 AND pattern_items:
    → Type 2: Value comparison, NO waiver
  
elif waivers.value > 0:
    → Type 4: Boolean WITH waiver logic
  
else:
    → Type 1: Boolean check, NO waiver
```

**⚠️ Configuration Guidelines (Updated Dec 2025):**


| Type       | requirements.value | pattern_items | waivers.value | waive_items     | Description                            |
| ---------- | ------------------ | ------------- | ------------- | --------------- | -------------------------------------- |
| **Type 1** | `N/A`              | `[]`          | `N/A` or `0`  | `[]` or `[...]` | Boolean check; waiver=0 forces PASS    |
| **Type 2** | `>0` or `N/A`      | `[...]`       | `N/A` or `0`  | `[]` or `[...]` | Value comparison; waiver=0 forces PASS |
| **Type 3** | `>0` or `N/A`      | `[...]`       | `>0`          | `[...]`         | Value comparison with normal waiver    |
| **Type 4** | `N/A`              | `[]`          | `>0`          | `[...]`         | Boolean check with normal waiver       |

**Important Notes:**

- **All types now support `value = N/A`** (flexible configuration)
- **Recommended**: For Type 2/3, set `requirements.value = len(pattern_items)`
- **Recommended**: For Type 3/4 with `value > 0`, set `waivers.value = len(waive_items)`
- **Type 1/2**: When `waivers.value = 0`, enables forced-PASS mode (all failures → INFO)
- **Runtime Validation**: Checkers validate consistency and warn on mismatches

### Waiver Tag Rules ⭐ NEW


| waivers.value | Checker Type | Waived Violations        | Unused Waivers   | waive_items Config    | Result                       |
| ------------- | ------------ | ------------------------ | ---------------- | --------------------- | ---------------------------- |
| **> 0**       | Type 3/4     | INFO +`[WAIVER]`         | WARN +`[WAIVER]` | -                     | Based on unwaived violations |
| **= 0**       | Type 1/2     | INFO +`[WAIVED_AS_INFO]` | -                | INFO +`[WAIVED_INFO]` | Forced PASS                  |
| **= N/A**     | Type 1/2     | FAIL (normal)            | -                | -                     | Based on actual result       |

**Tag Meanings:**

- **`[WAIVER]`**: Normal approved waiver (waivers.value > 0)
- **`[WAIVED_AS_INFO]`**: Forced waiver on detected violations (waivers.value = 0)
- **`[WAIVED_INFO]`**: Forced waiver configuration items (waivers.value = 0)

**Examples:**

```yaml
# Type 2 - Recommended (value matches count)
requirements:
  value: 2                     # ✅ Equals pattern_items count
  pattern_items:
    - "CLOCK_A"
    - "CLOCK_B"

# Type 2 - Also Valid (value = N/A)
requirements:
  value: N/A                   # ✅ Also supported
  pattern_items:
    - "CLOCK_A"
    - "CLOCK_B"

# Type 2 - Forced PASS mode (waiver=0)
requirements:
  value: 0
  pattern_items:
    - "FORBIDDEN_CELL"
waivers:
  value: 0                     # Forces PASS, all FAIL → INFO
  waive_items:
    - "debug_item"

# Type 3 - Normal waiver mode
requirements:
  value: 1
  pattern_items:
    - "FORBIDDEN_CELL"
waivers:
  value: 2                     # Normal waiver (value > 0)
  waive_items:
    - name: "ITEM_X"
      reason: "Approved"
    - name: "ITEM_Y"
      reason: "Legacy"
```

### Type 1: Boolean Check

**Use Case**: Simple yes/no verification (library exists, file present)

**Configuration (Normal Mode):**

```yaml
requirements:
  value: N/A
  pattern_items: []
waivers:
  value: N/A
  waive_items: []
```

**Configuration (Forced PASS Mode - waiver=0):**

```yaml
requirements:
  value: N/A
  pattern_items: []
waivers:
  value: 0                    # Forces PASS
  waive_items:
    - "debug_item"
```

**Example**: IMP-5-0-0-00 (Library Model Check)

---

### Type 2: Value Check

**Use Case**: Search for specific patterns in input files (violations to avoid, or requirements to meet)

**Configuration (Normal Mode):**

```yaml
requirements:
  value: 2                    # Number of patterns (for config validation)
  pattern_items:              # Patterns to search
    - "*nldm*"
    - "*quick*"
waivers:
  value: N/A
```

**Configuration (Forced PASS Mode - waiver=0):**

```yaml
requirements:
  value: 0
  pattern_items:
    - "*nldm*"
waivers:
  value: 0                    # Forces PASS
  waive_items:
    - "debug_item"
```

**Logic:**

1. Search pattern_items in input files
2. Classify results:
   - `found_items`: Patterns found in files
   - `missing_items`: Patterns not found
3. **PASS/FAIL depends on check purpose**:
   - **Violation Check**: PASS if found_items empty (no violations)
   - **Requirement Check**: PASS if missing_items empty (all requirements met)
4. **Config Validation**: Check `len(pattern_items) == requirements.value` (warns if mismatch, doesn't affect PASS/FAIL)
5. Forced mode (waiver=0): Always PASS, violations → INFO with `[WAIVED_AS_INFO]`

**Example**: IMP-1-0-0-02 (Don't Use Cell Check - Violation Check)

---

### Type 3: Value Check with Waiver Logic

**Use Case**: Search patterns with approved exceptions (same search logic as Type 2, plus waiver support)

**Configuration:**

```yaml
requirements:
  value: 1
  pattern_items:
    - "*nldm*"
waivers:
  value: 2                    # Must be > 0
  waive_items:
    - name: "ItemA"
      reason: "Approved by architect - Ticket#12345"
    - name: "ItemB"
      reason: "Legacy requirement - Q2 fix planned"
```

**Logic:**

1. **Same as Type 2**: Search pattern_items in input files
2. **Additional waiver classification**:
   - Match found_items against waive_items
   - **Unwaived items** → ERROR (need fix)
   - **Waived items** → INFO with `[WAIVER]` tag (approved)
   - **Unused waivers** → WARN with `[WAIVER]` tag (configured but not used)
3. **PASS/FAIL** (depends on check purpose):
   - **Violation Check**: PASS if all found_items are waived
   - **Requirement Check**: PASS if all missing_items are waived or found
4. **Config Validation**: Same as Type 2
5. All waive-related outputs use `[WAIVER]` suffix (since waivers.value > 0)

**Output Example (PASS):**

```
PASS
Value: 2 (all waived)

INFO01: Waived violations and unmatched patterns (good)
  - ItemA: Approved by architect - Ticket#12345[WAIVER]
  - ItemB: Legacy requirement - Q2 fix planned[WAIVER]
  - *quick*: Not found (good)
```

**Output Example (WARN - Unused Waiver):**

```
PASS
Value: 1 (all waived)

INFO01: Waived violations
  - ItemA: Approved[WAIVER]

WARN01: Unused waivers
  - ItemB: Configured but not found[WAIVER]
```

---

### Type 4: Boolean Check with Waiver Logic

**Use Case**: Boolean check with exceptions (same as Type 1, plus waiver support)

**Configuration:**

```yaml
requirements:
  value: N/A
  pattern_items: []
waivers:
  value: 1                    # Must be > 0
  waive_items:
    - name: "ItemA"
      reason: "Approved exception"
```

**Logic:**

1. **Same as Type 1**: Execute custom boolean check (no pattern_items)
2. **Additional waiver classification**:
   - Match violations against waive_items
   - **Unwaived violations** → ERROR
   - **Waived violations** → INFO with `[WAIVER]` tag
   - **Unused waivers** → WARN with `[WAIVER]` tag
3. **PASS/FAIL**: PASS if all violations are waived
4. All waive-related outputs use `[WAIVER]` suffix (since waivers.value > 0)

**Example**: IMP-5-0-0-10 (Synthesis Don't Use Cell with waivers)

---

## 🚦 Quick Start

**Prerequisites:** Python 3.8+, PyYAML, openpyxl

### Recommended: Work Directory Execution

```powershell
cd Work

# Run single checker
.\run.ps1 -check_module "10.0_STA_DCD_CHECK" -check_item "IMP-10-0-0-00"

# Run entire module
.\run.ps1 -check_module "10.0_STA_DCD_CHECK"

# Full regression test
.\run.ps1 -run_all -parallel_level 8

# Development mode (skip distribution)
.\run.ps1 -check_item "IMP-10-0-0-00" -skip_distribution -verbose
```

**Detailed Guide:** [Work Directory Guide](doc/WORK_DIRECTORY_GUIDE.md)

---

## 📁 Output Files

```
Check_modules/13.0_POST_PD_EQUIVALENCE_CHECK/
├── logs/
│   └── IMP-13-0-0-00.log              # Grouped format
├── reports/
│   └── IMP-13-0-0-00.rpt              # Detailed list
├── outputs/
│   ├── 13.0_POST_PD_EQUIVALENCE_CHECK.yaml  # Module summary
│   └── .cache/                         # Result cache
└── Results/
    └── 13.0_POST_PD_EQUIVALENCE_CHECK.xlsx  # Excel report
```

---

## 📚 Development Guide

### Creating a New Checker

**Step 1: Create Checker Script**

> **💡 PRIORITY:** Before implementing from scratch, check the **Checker Template Library** at `Check_modules/common/checker_templates/`. The template mixins can reduce code by 40-70% and ensure consistency.
>
> **Available Templates:**
>
> - **InputFileParserMixin**: 7 parsing patterns (simple patterns, file references, sections, command blocks, etc.)
> - **WaiverHandlerMixin**: 8 waiver handling patterns with unified tag rules
> - **OutputBuilderMixin**: 6 output formatting patterns for Type 1-4 checkers
>
> **See:** `checker_templates/README.md` for detailed usage guide with 30+ examples

**Example: Using Template Mixins**

```python
# Check_modules/X.0_MODULE/scripts/checker/IMP-X-0-0-YY.py

from pathlib import Path
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
_CHECK_MODULES_DIR = _SCRIPT_DIR.parents[2]
_COMMON_DIR = _CHECK_MODULES_DIR / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from base_checker import BaseChecker, CheckResult, ConfigurationError
from checker_templates.input_file_parser_template import InputFileParserMixin
from checker_templates.waiver_handler_template import WaiverHandlerMixin
from checker_templates.output_builder_template import OutputBuilderMixin

class MyChecker(BaseChecker, InputFileParserMixin, WaiverHandlerMixin, OutputBuilderMixin):
    """Check for specific patterns in log files"""
  
    def __init__(self):
        super().__init__(
            check_module="X.0_MODULE",
            item_id="IMP-X-0-0-YY",
            item_desc="Check description"
        )
        self._metadata = {}
  
    def execute_check(self) -> CheckResult:
        """Execute the check using template mixins"""
      
        # 1. Validate input files
        try:
            valid_files, missing_files = self.validate_input_files()
        except ConfigurationError as e:
            return e.result
      
        # 2. Auto-detect checker type
        checker_type = self.detect_checker_type()
      
        # 3. Parse using template pattern (InputFileParserMixin)
        patterns = {
            'in2out': r'_(in2out)_|timing_in2out',
            'in2reg': r'_(in2reg)_|timing_in2reg',
        }
        found_items = self.parse_log_with_patterns(
            log_file=valid_files[0],
            patterns=patterns
        )
      
        # 4. Apply waivers using template (WaiverHandlerMixin)
        waived_items, non_waived = self.apply_waivers_to_dict(
            items=found_items,
            waiver_key='name'
        )
      
        # 5. Build output using template (OutputBuilderMixin)
        return self.build_type3_output(
            items=non_waived,
            requirement_value=len(patterns),
            waived_items=waived_items,
            summary_message="Path groups found",
            item_formatter=lambda k, v: f"{k}: {v['count']} occurrences"
        )

if __name__ == "__main__":
    checker = MyChecker()
    result = checker.run()
    sys.exit(0 if result.status == "pass" else 1)
```

**Note:** For traditional implementation without templates, refer to existing checkers in the codebase or see detailed examples in `doc/DEVELOPER_TASK_PROMPTS.md`.

**Step 2: Create Configuration File**

```yaml
# Check_modules/X.0_MODULE/inputs/items/IMP-X-0-0-YY.yaml

description: "Your check description"

requirements:
  value: 0                    # N/A, 0, or >0 (flexible)
  pattern_items:              # For Type 2/3
    - "*pattern1*"
    - "^pattern2.*"

input_files: path/to/input.rpt

waivers:
  value: N/A                  # N/A, 0 (forced PASS), or >0 (normal waiver)
  waive_items:
    - name: "ItemName"
      reason: "Approval reason"
```

**Step 3: Test the Checker**

```powershell
# Option 1: Run single checker (Standard Execution)
python ..\Check_modules\common\check_flowtool.py -root .. -stage Initial `
    -check_module X.0_MODULE -check_item IMP-X-0-0-YY

# Option 2: Create Regression Snapshot (Recommended for Development)
# Captures baseline output for automated regression testing
python Check_modules\common\regression_testing\create_all_snapshots.py `
    --modules X.0_MODULE --checkers IMP-X-0-0-YY --force

# Option 3: Verify Against Baseline (After Code Changes)
# Automatically compares current output with baseline snapshot
python Check_modules\common\regression_testing\verify_all_snapshots.py `
    --modules X.0_MODULE --checkers IMP-X-0-0-YY --show-diff

# Check output
cat ..\Check_modules\X.0_MODULE\logs\IMP-X-0-0-YY.log
cat ..\Check_modules\X.0_MODULE\reports\IMP-X-0-0-YY.rpt
```

**Regression Testing Workflow:**

```powershell
# 1. Create baseline BEFORE code changes
python common\regression_testing\create_all_snapshots.py --modules X.0_MODULE

# 2. Make code changes (e.g., migrate to template mixins)

# 3. Verify output matches baseline
python common\regression_testing\verify_all_snapshots.py --modules X.0_MODULE

# 4. If changes are intentional, update baseline
python common\regression_testing\verify_all_snapshots.py --modules X.0_MODULE --update-failed

# 5. Run all module tests before commit
python common\regression_testing\verify_all_snapshots.py
```

### Type-Specific Implementation Templates

See `Development_prompt.md` for detailed implementation examples of all four types.

---

## ⚙️ Configuration

### $ {CHECKLIST_ROOT} Variable System ⭐ NEW (Dec 15, 2025)

**Design Philosophy**: Keep configuration files Git-friendly with portable paths

**2-Phase Workflow**:

```
Phase 1: Placeholder Generation
  CheckList_Index.yaml (346 checkers)
        ↓
  DATA_INTERFACE.template.yaml (with ${CHECKLIST_ROOT} variables)

Phase 2: Items Merge
  Check_modules/*/inputs/items/*.yaml (developer-written)
        ↓
  Merged into template.yaml (preserves ${CHECKLIST_ROOT} variables)

Phase 3: (Deprecated)
  ~~Resolve ${CHECKLIST_ROOT} → Absolute paths~~
```

**Variable Expansion**:

- **Disk files**: Use `${CHECKLIST_ROOT}` for portability
- **Runtime**: Automatically expand to absolute paths in memory
- **Location**: `base_checker.py` and `parse_interface.py` handle expansion

**Configuration Example:**

```yaml
# items/IMP-10-0-0-02.yaml
description: Confirm clock uncertainty setting
requirements:
  value: N/A
  pattern_items: []
input_files:
- ${CHECKLIST_ROOT}/IP_project_folder/reports/constr.rpt  # Portable!
waivers:
  value: 2
  waive_items:
  - name: set_clock_uncertainty 0.01 -hold
    reason: Pre-implementation phase
```

---

## 📊 Output Formats

### Log File (Grouped Format)

```
PASS:IMP-13-0-0-00:Confirm conformal constraints have been peer reviewed?
IMP-13-0-0-00-WARN01: Conformal constraints requiring peer review:
  Severity: Warn Occurrence: 3
  - Command: add_pin_constraints 0 {cmnda_scanmode} -golden
  - Command: add_pin_constraints 0 {cmnda_scanen} -golden
  - Command: add_pin_constraints 0 {cmnda_scanen_cg} -golden
```

### Report File (Detailed List)

```
PASS:IMP-13-0-0-00:Confirm conformal constraints have been peer reviewed?
Warn Occurrence: 3
1: Warn: Command: add_pin_constraints 0 {cmnda_scanmode} -golden. In line 42, conformal.log: Constraint found
2: Warn: Command: add_pin_constraints 0 {cmnda_scanen} -golden. In line 43, conformal.log: Constraint found
3: Warn: Command: add_pin_constraints 0 {cmnda_scanen_cg} -golden. In line 44, conformal.log: Constraint found
```

### Summary YAML

```yaml
IMP-13-0-0-00:
  executed: true
  status: pass
  description: "Confirm conformal constraints have been peer reviewed?"
  warnings:
    - index: 1
      detail: Conformal constraints requiring peer review
      source_line: 42
      source_file: conformal.log
      reason: Constraint found
```

### Excel Report

Generated from summary YAML with color-coded status indicators.

---

## 🛠️ Troubleshooting

### Common Issues

**1. Empty input_files**

**Problem**: Checker reports "No input files configured"

**Solution**:

```powershell
# Delete cache and re-run DATA_INTERFACE distribution
Remove-Item Check_modules\*\inputs\.cache\*.json -Force
python ..\Check_modules\common\check_flowtool.py -root .. -stage Initial
```

**2. ConfigurationError not raised**

**Problem**: Empty input files don't trigger ConfigurationError

**Solution**: Ensure `validate_input_files()` is called WITHOUT `raise_on_empty=False` parameter

**3. YAML parsing error with Windows paths**

**Problem**: `expected <block end>, but found '<scalar>'` at Windows path

**Solution**: This is fixed in latest version - update `write_summary_yaml.py`

**4. Method not found: detect_check_type**

**Problem**: AttributeError on method call

**Solution**: Use correct method name: `detect_checker_type()` (not `detect_check_type()`)

---

## 🤝 Contributing

### Development Workflow

1. **Create Feature Branch**

   ```bash
   git checkout -b feature/new-checker
   ```
2. **Implement Checker Using Templates** ⭐ RECOMMENDED

   ```python
   # Use template mixins for 40-70% code reduction
   from checker_templates.input_file_parser_template import InputFileParserMixin
   from checker_templates.waiver_handler_template import WaiverHandlerMixin
   from checker_templates.output_builder_template import OutputBuilderMixin

   class MyChecker(BaseChecker, InputFileParserMixin, WaiverHandlerMixin, OutputBuilderMixin):
       # See checker_templates/README.md for usage examples
   ```
3. **Test with Regression Framework**

   ```powershell
   # Create baseline snapshot
   python common\regression_testing\create_all_snapshots.py --modules X.0_MODULE --force

   # Make code changes...

   # Verify against baseline
   python common\regression_testing\verify_all_snapshots.py --modules X.0_MODULE --show-diff

   # Update baseline if changes are intentional
   python common\regression_testing\verify_all_snapshots.py --modules X.0_MODULE --update-failed
   ```
4. **Update Documentation**

   - Update `Development_prompt.md` if adding new patterns
   - Document any special parsing logic in checker's README
   - Add examples to `checker_templates/EXAMPLES.md` if creating new template patterns
5. **Commit and Push**

   ```bash
   git add .
   git commit -m "feat: Add MODULE_NAME checker with template mixins (XX% code reduction)"
   git push origin feature/new-checker
   ```

### Code Standards

- **Naming**: Use descriptive class names ending with `Checker`
- **Error Handling**: Always use try-except for file operations
- **Metadata**: Store line numbers and file paths for all items
- **Type Safety**: Use type hints for all methods
- **Documentation**: Include docstrings for all public methods

---

## 📖 Documentation

### Core Documentation

- **README.md** (this file) - Project overview, architecture, and quick start
- **Development_prompt.md** - Comprehensive development reference with Type 1-4 implementation examples

### Template Library Documentation

- **checker_templates/README.md** - Complete template usage guide with 30+ examples
  - 7 input parsing patterns + 1 utility method (normalize_command)
  - 8 waiver handling patterns with unified tag rules
  - 6 output formatting patterns for Type 1-4 checkers
- **checker_templates/EXAMPLES.md** - Real-world migration examples
  - IMP-10-0-0-10: 684→402 lines (-41.2%)
  - IMP-10-0-0-02: 738→697 lines (-5.6%, v1.1.0)
- **checker_templates/TASK_COMPLETION.md** - Template migration task tracking and version history

### Regression Testing Documentation

- **regression_testing/README.md** - Complete regression testing workflow guide
  - Snapshot creation and verification
  - Batch operations for entire modules
  - Migration workflow (baseline → migrate → verify → update)
  - Auto-discovery and smart diffing

### Developer Guides

- **doc/DEVELOPER_TASK_PROMPTS.md** - AI-assisted development guide
  - Emphasizes template library priority
  - Step-by-step checker implementation workflow
  - Regression testing integration
- **doc/DEVELOPER_WORKFLOW_DIAGRAM.md** - Visual workflow diagram
  - Simplified testing steps using snapshot tool
  - Template-first development approach
- **doc/OUTPUT_FORMATTER_GUIDE.md** - Output formatting best practices
- **doc/WORK_DISPATCHER_GUIDE.md** - Work assignment system guide

### Example Checkers

- **IMP-10-0-0-10** (`Check_modules/10.0_STA_DCD_CHECK/scripts/checker/IMP-10-0-0-10.py`)
  - Showcase of template migration (41% code reduction)
  - Uses all 3 mixins: InputFileParser, WaiverHandler, OutputBuilder
- **IMP-13-0-0-XX** (`Check_modules/13.0_POST_PD_EQUIVALENCE_CHECK/scripts/checker/`)
  - 8 checkers with BaseChecker pattern
- **IMP-6-0-0-XX** (`Check_modules/6.0_POST_SYNTHESIS_LEC_CHECK/scripts/checker/`)
  - 8 checkers for post-synthesis LEC verification

---

## 📜 License

Internal Cadence Design Systems project.

---

## 👥 Authors

- **Yu Yin** (yuyin@global.cadence.com) - Architecture migration and framework development

---

## 🔗 Related Resources

### Core Framework

- **BaseChecker API**: `Check_modules/common/base_checker.py` - Base class for all checkers
- **Output Formatter**: `Check_modules/common/output_formatter.py` - Result formatting utilities
- **Execution Engine**: `Check_modules/common/check_flowtool.py` - Main execution driver

### Template Library

- **Input Parser**: `Check_modules/common/checker_templates/input_file_parser_template.py`
  - 953 lines, 7 parsing patterns + 1 utility method (v1.1.0)
  - normalize_command() for consistent text normalization
- **Waiver Handler**: `Check_modules/common/checker_templates/waiver_handler_template.py`
  - 637 lines, 8 waiver patterns (v1.1.0)
  - Enhanced match_waiver_entry() with normalizer support
- **Output Builder**: `Check_modules/common/checker_templates/output_builder_template.py`
  - 773 lines, 6 output patterns (v1.1.0)
  - Fixed log deduplication bug

### Testing & Automation

- **Snapshot Manager**: `Check_modules/common/regression_testing/snapshot_manager.py`
  - Core snapshot management engine
- **Batch Creator**: `Check_modules/common/regression_testing/create_all_snapshots.py`
  - Automated snapshot creation for all checkers
- **Batch Verifier**: `Check_modules/common/regression_testing/verify_all_snapshots.py`
  - Automated regression verification

### Productivity Tools

- **Checker Generator**: `Check_modules/common/checker_generator.py` - Generate new checker skeleton
- **Work Dispatcher**: `Check_modules/common/work_dispatcher.py` - Work assignment automation

---

**Last Updated**: December 15, 2025
