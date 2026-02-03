# Template Behavior Tests

## Overview

This directory contains test suites for validating OutputBuilderTemplate behavior, ensuring API v2.0 compliance, and preventing regressions.

## Test Structure

```
tests/
├── test_output_builder_template.py   # Main template behavior tests
├── test_metadata_preservation.py     # Metadata handling tests (future)
├── test_severity_control.py          # Severity logic tests (future)
├── test_waiver_support.py            # Waiver functionality tests (future)
└── README.md                          # This file
```

## Test Categories

### 1. Metadata Preservation
Tests Dict format metadata (line_number, file_path) preservation through template methods.

**Key Tests**:
- `test_dict_format_preserves_metadata` - Verify Dict metadata preserved
- `test_list_format_auto_conversion` - Verify List→Dict conversion
- `test_missing_items_dict_format` - Verify missing_items supports Dict
- `test_waived_items_dict_format` - Verify waived_items supports Dict

### 2. Severity Control
Tests severity level control and is_pass calculation logic.

**Key Tests**:
- `test_extra_severity_fail` - Verify extra_severity=FAIL forces FAIL
- `test_extra_severity_warn` - Verify extra_severity=WARN allows PASS
- `test_missing_severity_default_fail` - Verify missing_items default FAIL

### 3. Tag Display Logic
Tests tag display ([WAIVER], [WAIVED_INFO], [WAIVED_AS_INFO]) in reason vs name.

**Key Tests**:
- `test_waiver_tag_in_reason` - Verify tags in reason, not name
- `test_waived_info_tag_waiver_zero` - Verify [WAIVED_INFO] in waiver=0
- `test_no_tag_duplication_in_groups` - Verify no duplicate tags

### 4. Waiver Support
Tests waiver=0 auto-conversion and waiver handling.

**Key Tests**:
- `test_waiver_zero_converts_fail_to_info` - Verify FAIL→INFO conversion
- `test_normal_mode_fail_stays_fail` - Verify normal mode FAIL
- `test_waive_items_display` - Verify waive_items display

### 5. Backward Compatibility
Tests v1.x List parameter compatibility.

**Key Tests**:
- `test_list_parameters_still_work` - Verify List[str] still works
- `test_mixed_dict_list_parameters` - Verify Dict+List mixing

### 6. Complete Output
Tests `build_complete_output()` one-step solution.

**Key Tests**:
- `test_complete_output_builds_all_components` - Verify all components built
- `test_complete_output_with_extra_items` - Verify extra_items handling
- `test_complete_output_custom_descriptions` - Verify custom descriptions

### 7. Edge Cases
Tests error handling and edge cases.

**Key Tests**:
- `test_empty_items` - Verify empty dict handling
- `test_none_items` - Verify None handling
- `test_metadata_missing_fields` - Verify incomplete metadata handling

## Running Tests

### Prerequisites

```bash
pip install pytest pytest-cov
```

### Run All Tests

```bash
cd Tool/AutoGenChecker
python -m pytest tests/ -v
```

### Run Specific Test Class

```bash
python -m pytest tests/test_output_builder_template.py::TestMetadataPreservation -v
```

### Run with Coverage

```bash
python -m pytest tests/ --cov=prompt_templates --cov=context_collectors --cov-report=html
```

### Run Single Test

```bash
python -m pytest tests/test_output_builder_template.py::TestSeverityControl::test_extra_severity_fail -v
```

## Test Output

Successful run should show:

```
tests/test_output_builder_template.py::TestMetadataPreservation::test_dict_format_preserves_metadata PASSED
tests/test_output_builder_template.py::TestMetadataPreservation::test_list_format_auto_conversion PASSED
tests/test_output_builder_template.py::TestSeverityControl::test_extra_severity_fail PASSED
...
========================= 25 passed in 2.34s =========================
```

## Adding New Tests

### Test Template

```python
class TestNewFeature:
    """Test description."""
    
    def test_specific_behavior(self):
        """Test specific behavior description."""
        checker = MockChecker()
        
        # Setup
        test_data = {...}
        
        # Execute
        result = checker.method(test_data)
        
        # Assert
        assert result.expected_property == expected_value
```

### Guidelines

1. **One concept per test** - Keep tests focused
2. **Clear names** - Use descriptive test method names
3. **AAA pattern** - Arrange, Act, Assert
4. **Mock external deps** - Use MockChecker for isolation
5. **Test edge cases** - Include boundary conditions
6. **Document intent** - Add docstrings explaining why

## Continuous Integration

Tests should run on:
- Pre-commit hooks
- Pull request validation
- Nightly builds
- Release validation

## Test Coverage Goals

- **Target**: 80% coverage for template code
- **Critical paths**: 100% coverage for API v2.0 methods
- **Edge cases**: All error paths tested

## Known Issues

None currently.

## Future Tests

Planned test suites:

1. **test_file_analysis.py** - FileAnalysisCollector tests
2. **test_code_generation.py** - Prompt generation tests
3. **test_integration.py** - End-to-end checker generation tests
4. **test_performance.py** - Performance benchmarks

## Contributing

When adding new template features:

1. Write tests FIRST (TDD)
2. Ensure tests pass before committing
3. Update this README with new test categories
4. Maintain ≥80% coverage

## Support

For questions:
- Check test output for detailed failure messages
- Review test docstrings for expected behavior
- Contact: yyin@cadence.com

**Last Updated**: December 16, 2025  
**Test Suite Version**: 1.0.0
