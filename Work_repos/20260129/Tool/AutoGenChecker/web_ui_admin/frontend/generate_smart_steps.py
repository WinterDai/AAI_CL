"""Utility to create smart step components for Steps 2, 4-9"""

STEP_TEMPLATE = """
import {{ useState }} from 'react'
import Card from '@/components/common/Card'
import Button from '@/components/common/Button'
import {{ useGenerationStore }} from '@/store/generationStore'

export default function Step{step_num}{step_name}({{ itemId }}) {{
  const generated{content_var} = useGenerationStore((s) => s.generated{content_var})
  const stepStates = useGenerationStore((s) => s.stepStates)
  const setGenerated{content_var} = useGenerationStore((s) => s.setGenerated{content_var})
  const setStepState = useGenerationStore((s) => s.setStepState)
  const setStatus = useGenerationStore((s) => s.setStatus)
  
  const [hints, setHints] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)

  const mock{content_var} = `{mock_content}`

  const handleStartGeneration = async () => {{
    setIsGenerating(true)
    setStatus('running')
    setStepState({step_num}, 'running')
    
    try {{
      const response = await fetch('http://localhost:8000/api/generation/start', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{
          item_id: itemId,
          step: {step_num},
          hints: hints
        }})
      }})
      
      if (response.ok) {{
        const data = await response.json()
        setGenerated{content_var}(data.{api_key} || mock{content_var})
        setStepState({step_num}, 'completed')
        setStatus('idle')
      }} else {{
        throw new Error('Generation failed')
      }}
    }} catch (error) {{
      console.error('Generation error:', error)
      setGenerated{content_var}(mock{content_var})
      setStepState({step_num}, 'completed')
      setStatus('idle')
    }} finally {{
      setIsGenerating(false)
    }}
  }}
  
  const handleReGenerate = () => {{
    if (window.confirm('This will replace existing content. Continue?')) {{
      setGenerated{content_var}('')
      handleStartGeneration()
    }}
  }}
  
  const handleEdit = () => {{
    // TODO: Implement edit functionality
    alert('Edit functionality coming soon!')
  }}

  const stepStatus = stepStates[{step_num}] || 'idle'
  const isCompleted = stepStatus === 'completed' || generated{content_var}
  const displayContent = generated{content_var} || mock{content_var}

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">
          Step {step_num}: {step_title}
        </h1>
        <p className="mt-1 text-base text-gray-600">
          {step_description}
        </p>
      </div>

      {/* Hints Input */}
      <Card>
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Generation Hints (Optional)</h2>
          <textarea
            value={{hints}}
            onChange={{(e) => setHints(e.target.value)}}
            placeholder="Enter any specific requirements or hints for generation..."
            className="w-full px-4 py-3 text-base border border-gray-300 rounded-lg"
            rows={{4}}
            disabled={{isGenerating}}
          />
        </div>
      </Card>

      {/* Generated Content */}
      <Card>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Generated {content_label}</h2>
            <div className="flex items-center space-x-2">
              {{isCompleted ? (
                <>
                  <Button variant="secondary" onClick={{handleEdit}} disabled={{isGenerating}}>
                    ✏️ Edit
                  </Button>
                  <Button onClick={{handleReGenerate}} disabled={{isGenerating}}>
                    🔄 Re-generate
                  </Button>
                </>
              ) : (
                <Button onClick={{handleStartGeneration}} disabled={{isGenerating}}>
                  {{isGenerating ? '⏳ Generating...' : '🚀 Start Generation'}}
                </Button>
              )}}
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-6 overflow-auto max-h-96">
            {{displayContent ? (
              <pre className="text-base text-gray-900 whitespace-pre-wrap font-mono">
                {{displayContent}}
              </pre>
            ) : (
              <p className="text-base text-gray-500 text-center py-8">
                No content generated yet. Click "Start Generation" to begin.
              </p>
            )}}
          </div>
        </div>
      </Card>

      {{/* Generation Log */}}
      {{isGenerating && (
        <Card>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-gray-900">Generation Progress</h3>
            <div className="space-y-1 text-base text-gray-600">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                <span>Generating {content_label}...</span>
              </div>
            </div>
          </div>
        </Card>
      )}}
    </div>
  )
}}
"""

# Step definitions
STEPS = [
    {
        "step_num": 2,
        "step_name": "FileAnalysis",
        "step_title": "File Analysis",
        "step_description": "Analyzing input files and extracting patterns",
        "content_var": "FileAnalysis",
        "content_label": "File Analysis",
        "api_key": "analysis",
        "mock_content": "# File Analysis\\n\\nAnalyzing input files...\\n- timing.rpt: 1234 lines\\n- sta.log: 456 lines"
    },
    {
        "step_num": 4,
        "step_name": "CodeGen",
        "step_title": "Code Generation",
        "step_description": "Generating checker implementation code",
        "content_var": "Code",
        "content_label": "Code",
        "api_key": "code",
        "mock_content": "# Generated Code\\n\\nimport re\\n\\nclass Checker:\\n    def __init__(self):\\n        pass\\n\\n    def run(self):\\n        return 'PASS'"
    },
    # Add more steps as needed
]

# Generate components
if __name__ == "__main__":
    for step in STEPS:
        code = STEP_TEMPLATE.format(**step)
        filename = f"Step{step['step_num']}{step['step_name']}.jsx"
        print(f"\\n{'='*60}")
        print(f"Generated: {filename}")
        print('='*60)
        print(code)
