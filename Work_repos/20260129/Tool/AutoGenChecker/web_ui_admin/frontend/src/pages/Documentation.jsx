import { useState } from 'react'
import Card from '@/components/common/Card'

export default function Documentation() {
  const [activeSection, setActiveSection] = useState('getting-started')

  const sections = [
    { id: 'getting-started', title: 'Getting Started', icon: '🚀' },
    { id: 'workflow', title: '9-Step Workflow', icon: '📋' },
    { id: 'features', title: 'Features', icon: '✨' },
    { id: 'api', title: 'API Reference', icon: '📚' },
    { id: 'faq', title: 'FAQ', icon: '❓' }
  ]

  const content = {
    'getting-started': {
      title: 'Getting Started with AutoGenChecker',
      content: `
## Welcome to AutoGenChecker Web UI

AutoGenChecker is an AI-powered tool that automatically generates checker code for your verification needs.

### Quick Start

1. **Create a New Project**: Click "New Project" from the Dashboard
2. **Configure**: Provide YAML configuration with item ID, module, and input files
3. **Generate**: Follow the 9-step workflow to generate your checker
4. **Deploy**: Download or deploy the generated checker to your project

### Prerequisites

- Python 3.9+
- Node.js 18+
- Access to JEDAI LLM or other configured LLM provider

### Installation

\`\`\`bash
# Backend
cd web_ui/backend
pip install -r requirements.txt
python app.py

# Frontend
cd web_ui/frontend
npm install
npm run dev
\`\`\`
      `
    },
    'workflow': {
      title: '9-Step Workflow Guide',
      content: `
## The 9-Step Checker Generation Workflow

### Step 1: Configuration
Load and validate YAML configuration file containing:
- Item ID
- Module path
- Input file patterns
- Description

### Step 2: File Analysis
AI analyzes input files to:
- Detect file formats
- Extract patterns
- Identify key data structures

### Step 3: README Generation
- Generate documentation
- Add custom hints (optional)
- Actions: [U]se, [H]ints only, [N]o hints, [S]how

### Step 4: README Review
- Review and edit README
- Actions: [K]eep, [E]dit, [A]ppend, [R]egenerate, [Q]uit

### Step 5: Code Implementation
- AI generates checker code
- Monaco editor for code review
- Syntax highlighting and validation

### Step 6: Self Check
- Automated code quality checks
- PEP8 style validation
- Auto-fix capabilities

### Step 7: Testing
- Generate comprehensive tests
- Unit, integration, edge case tests
- Code coverage analysis

### Step 8: Final Review
- Review all components
- Actions: [T]est, [M]anual review, [O]ptimize, [V]alidate, [R]evise, [F]inalize, [Q]uit

### Step 9: Package
- Create deployment package
- Download options
- Deploy to Check_modules
      `
    },
    'features': {
      title: 'Features Overview',
      content: `
## Key Features

### AI-Powered Generation
- Intelligent code generation using advanced LLMs
- Context-aware README and test generation
- Automatic pattern detection

### Interactive Workflow
- Step-by-step guided process
- Real-time progress tracking
- Resume from any step

### Code Quality
- Built-in self-check system
- PEP8 compliance
- Comprehensive test generation
- Code coverage analysis

### Templates
- Reusable checker templates
- Category-based organization
- Usage tracking

### History & Management
- Complete generation history
- Detailed logs and artifacts
- Online viewing of generated files
- Clone and edit past generations

### Customization
- Configurable LLM providers
- Custom hints support
- Flexible project paths
- Auto-save and auto-test options
      `
    },
    'api': {
      title: 'API Reference',
      content: `
## REST API Endpoints

### Generation

\`\`\`http
POST /api/generation/start
Content-Type: application/json

{
  "item_id": "IMP-10-0-0-13",
  "module": "10.0_STA_DCD_CHECK",
  "llm_provider": "jedai",
  "llm_model": "claude-sonnet-4-5"
}
\`\`\`

### Status

\`\`\`http
GET /api/generation/status/{item_id}
\`\`\`

### Progress Stream (SSE)

\`\`\`http
GET /api/generation/stream/progress?item_id={item_id}
\`\`\`

### History

\`\`\`http
GET /api/history
GET /api/history/{item_id}
\`\`\`

### Templates

\`\`\`http
GET /api/templates
POST /api/templates
PUT /api/templates/{id}
DELETE /api/templates/{id}
\`\`\`
      `
    },
    'faq': {
      title: 'Frequently Asked Questions',
      content: `
## FAQ

### How long does generation take?
Typically 3-5 minutes depending on complexity. The UI shows real-time progress.

### Can I resume a failed generation?
Yes, click "Resume" from the History page to continue from the last completed step.

### What LLM providers are supported?
- JEDAI (default)
- OpenAI
- Anthropic
- Local models

### How do I add custom hints?
In Step 3, use the hints textarea and select [U]se or [H]ints only to apply them.

### Can I edit generated code?
Yes, in Step 5 you can edit code directly in the Monaco editor.

### What if tests fail?
Review test results in Step 7, fix issues in Step 5, and re-run tests.

### How do I deploy?
In Step 9, click "Deploy Now" to copy files to your Check_modules directory.

### Can I create custom templates?
Yes, go to Templates page and click "Create New Template".

### Where are files saved?
Generated files are saved in the configured output directory and can be downloaded as ZIP.
      `
    }
  }

  return (
    <div className="min-h-full bg-gray-50">
      <div className="w-full px-6 py-8">
        <div className="flex gap-6">
          {/* Sidebar */}
          <div className="w-64 flex-shrink-0">
            <Card>
              <div className="space-y-1">
                {sections.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={`w-full flex items-center space-x-3 px-4 py-3 text-left rounded-lg transition-colors ${
                      activeSection === section.id
                        ? 'bg-primary text-white'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <span className="text-lg">{section.icon}</span>
                    <span className="text-sm font-medium">{section.title}</span>
                  </button>
                ))}
              </div>
            </Card>
          </div>

          {/* Content */}
          <div className="flex-1">
            <Card>
              <div className="prose prose-sm max-w-none">
                <h1 className="text-2xl font-semibold text-gray-900 mb-6">
                  {content[activeSection].title}
                </h1>
                <div className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                  {content[activeSection].content}
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
