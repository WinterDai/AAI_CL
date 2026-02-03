# Developer Agent Tests

This directory contains unit and integration tests for the Developer Agent.

## Test Files

- `test_unit.py` - Unit tests for individual modules
- `test_integration.py` - Integration tests for workflow and component interactions

## Running Tests

### Run all tests:
```bash
cd developer_agent
python -m pytest tests/ -v
```

### Run unit tests only:
```bash
python -m pytest tests/test_unit.py -v
```

### Run integration tests only:
```bash
python -m pytest tests/test_integration.py -v
```

### Run with coverage:
```bash
python -m pytest tests/ -v --cov=. --cov-report=html
```

### Run without pytest (using unittest):
```bash
python tests/test_unit.py
python tests/test_integration.py
```

## Test Categories

### Unit Tests (test_unit.py)

| Test Class | Coverage |
|------------|----------|
| TestState | AgentState, create_initial_state, generate_item_id |
| TestCache | FileSystemCache save/load/list operations |
| TestTools | File pattern extraction, ItemSpec parsing, log snippet extraction |
| TestValidator | Gate 1/2/3 validation, error source determination |
| TestPrompts | Prompt building and response parsing |
| TestMockLLMClient | Mock client functionality |

### Integration Tests (test_integration.py)

| Test Class | Coverage |
|------------|----------|
| TestEndToEndWorkflow | Full workflow from load_spec to validate |
| TestValidatorIntegration | Complex validation scenarios |
| TestPromptsIntegration | Complete prompt generation cycle |

## Test Fixtures

Tests use temporary directories and files that are cleaned up automatically after each test.
