# AutoGenChecker Web UI - Test Plan

## Test Overview

This document outlines the testing strategy for the AutoGenChecker Web UI.

## Test Categories

### 1. Backend API Tests

#### Generation API (`/api/generation`)
- [ ] **POST /start** - Start new generation
  - Valid item_id and configuration
  - Invalid item_id (error handling)
  - Missing required fields (validation)
  - Concurrent generations
  
- [ ] **GET /status/{item_id}** - Get generation status
  - Active generation
  - Completed generation
  - Non-existent generation (404)
  
- [ ] **GET /stream/progress** - SSE progress stream
  - Connection establishment
  - Real-time updates
  - Connection timeout handling
  - Reconnection logic
  
- [ ] **POST /{item_id}/continue** - Continue to next step
  - Step progression
  - Final step handling
  - Invalid step transitions
  
- [ ] **POST /{item_id}/save** - Save progress
  - Data persistence
  - Concurrent saves
  - Save validation

#### History API (`/api/history`)
- [ ] **GET /** - Get history list
  - Pagination
  - Status filtering
  - Module filtering
  - Date range filtering
  
- [ ] **GET /{item_id}** - Get history detail
  - Complete item data
  - Logs retrieval
  - File content access
  
- [ ] **POST /save** - Save to history
  - Data validation
  - Duplicate handling

#### Templates API (`/api/templates`)
- [ ] **GET /** - List templates
  - All templates
  - Category filtering
  - Search functionality
  
- [ ] **GET /{template_id}** - Get template detail
- [ ] **POST /use** - Use template

#### Settings API (`/api/settings`)
- [ ] **GET /** - Get current settings
- [ ] **POST /** - Update settings
  - LLM configuration
  - Generation preferences
  - Path settings

### 2. Frontend Component Tests

#### Dashboard Page
- [ ] Statistics display (total, in-progress, completed)
- [ ] Recent activity feed
- [ ] Active projects table
- [ ] Navigation to generator
- [ ] Resume in-progress items

#### Generator Page (9-Step Workflow)
- [ ] **Step 1**: Configuration loading and validation
- [ ] **Step 2**: File analysis display
- [ ] **Step 3**: README generation with hints
- [ ] **Step 4**: README review and editing
- [ ] **Step 5**: Code generation with Monaco editor
- [ ] **Step 6**: Self-check and auto-fix
- [ ] **Step 7**: Testing interface
- [ ] **Step 8**: Final review with actions
- [ ] **Step 9**: Package and deployment

- [ ] Left sidebar progress display
- [ ] Bottom action bar (Back/Continue)
- [ ] Progress bar updates
- [ ] Step navigation
- [ ] Data persistence between steps

#### History Page
- [ ] List display with filters
- [ ] Status badge rendering
- [ ] Detail sidebar toggle
- [ ] Tab navigation (6 tabs)
- [ ] Resume functionality
- [ ] Download buttons

#### Templates Page
- [ ] Category tabs
- [ ] Template cards display
- [ ] View/Use buttons
- [ ] Template search

#### Settings Page
- [ ] LLM configuration form
- [ ] Generation settings checkboxes
- [ ] Project paths configuration
- [ ] Save/Reset functionality

#### Documentation Page
- [ ] Section navigation
- [ ] Content display
- [ ] Sidebar scrolling

### 3. Integration Tests

#### End-to-End Workflow
- [ ] **Complete Generation Flow**:
  1. Start from Dashboard
  2. Navigate to Generator
  3. Complete all 9 steps
  4. Save to history
  5. View in History page
  
- [ ] **Resume Flow**:
  1. Start generation
  2. Save progress at step 5
  3. Exit and return
  4. Resume from Dashboard
  5. Continue from step 5
  
- [ ] **Template Usage Flow**:
  1. Browse templates
  2. Select template
  3. Start generation with template
  4. Verify pre-filled configuration

#### API Integration
- [ ] Frontend ↔ Backend communication
- [ ] SSE event handling
- [ ] Error propagation
- [ ] Loading states
- [ ] Retry logic

### 4. Performance Tests

- [ ] **Load Time**:
  - [ ] Initial page load < 2s
  - [ ] Route transitions < 500ms
  - [ ] API response time < 1s
  
- [ ] **Concurrency**:
  - [ ] Multiple simultaneous generations
  - [ ] Multiple SSE connections
  
- [ ] **Memory**:
  - [ ] No memory leaks in long sessions
  - [ ] Efficient state management

### 5. Error Handling Tests

- [ ] Network errors
  - [ ] Connection timeout
  - [ ] Server unavailable
  - [ ] Retry mechanism
  
- [ ] LLM errors
  - [ ] Token limit exceeded
  - [ ] Invalid API credentials
  - [ ] Model unavailable
  
- [ ] Validation errors
  - [ ] Invalid YAML configuration
  - [ ] Missing input files
  - [ ] Invalid item_id format
  
- [ ] User errors
  - [ ] Invalid form input
  - [ ] Navigation away during generation
  - [ ] Browser refresh during generation

### 6. Browser Compatibility Tests

- [ ] Chrome (latest)
- [ ] Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest, if accessible)

### 7. Accessibility Tests

- [ ] Keyboard navigation
- [ ] Screen reader compatibility
- [ ] Color contrast (WCAG AA)
- [ ] Focus indicators

## Manual Test Procedures

### Test 1: Complete Generation (Happy Path)

**Prerequisites**: Backend and frontend running

**Steps**:
1. Open http://localhost:5173
2. Verify Dashboard displays correctly
3. Click "New Generation"
4. Select item: IMP-10-0-0-13
5. Verify configuration loads (Step 1)
6. Click Continue
7. Verify file analysis displays (Step 2)
8. Click Continue through all 9 steps
9. Verify progress bar updates
10. Verify package generation (Step 9)
11. Click "View History"
12. Verify item appears in history

**Expected Result**: Complete generation with all steps passing

### Test 2: SSE Progress Stream

**Prerequisites**: Backend running with SSE endpoint

**Steps**:
1. Start generation via API
2. Open SSE stream in browser dev tools
3. Verify event stream connected
4. Verify progress updates received
5. Verify final completion event

**Expected Result**: Real-time progress updates via SSE

### Test 3: Error Recovery

**Prerequisites**: Backend with intentional error injection

**Steps**:
1. Start generation
2. Trigger error at step 5 (code generation)
3. Verify error message displayed
4. Verify state saved
5. Click "Retry"
6. Verify generation resumes

**Expected Result**: Graceful error handling with retry

## Automated Test Scripts

### Backend API Test Script

```python
# test_backend.py
import pytest
import httpx

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_start_generation():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/generation/start", json={
            "item_id": "IMP-10-0-0-13",
            "module": "10.0_STA_DCD_CHECK",
            "llm_provider": "jedai",
            "llm_model": "gemini-1.5-pro"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert "item_id" in data

# Run: pytest test_backend.py
```

### Frontend Component Test

```javascript
// Dashboard.test.jsx
import { render, screen } from '@testing-library/react';
import Dashboard from './Dashboard';

test('renders dashboard with stats', () => {
  render(<Dashboard />);
  expect(screen.getByText(/Total Generations/i)).toBeInTheDocument();
  expect(screen.getByText(/In Progress/i)).toBeInTheDocument();
});

// Run: npm test
```

## Test Execution Schedule

1. **Unit Tests**: Run on every commit
2. **Integration Tests**: Run before every PR merge
3. **E2E Tests**: Run nightly
4. **Performance Tests**: Run weekly
5. **Manual Tests**: Run before releases

## Test Environment Setup

### Local Development
```bash
# Backend
cd web_ui/backend
pip install -r requirements.txt
pip install pytest httpx pytest-asyncio
python -m pytest tests/

# Frontend
cd web_ui/frontend
npm install
npm test
```

### CI/CD Pipeline
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest
  
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
      - run: npm install
      - run: npm test
```

## Success Criteria

- ✅ All automated tests pass
- ✅ No critical bugs in manual testing
- ✅ Performance metrics met
- ✅ Error handling verified
- ✅ Cross-browser compatibility confirmed
- ✅ Accessibility standards met

## Known Issues / TODO

- [ ] Monaco Editor integration needs real implementation (currently placeholder)
- [ ] Database persistence not implemented (using in-memory storage)
- [ ] Template library needs actual template data
- [ ] Settings persistence needs localStorage implementation
