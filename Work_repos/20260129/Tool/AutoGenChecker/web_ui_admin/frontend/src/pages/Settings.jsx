import { useState, useEffect } from 'react'
import { useSettingsStore } from '@/store/settingsStore'
import Card from '@/components/common/Card'
import Button from '@/components/common/Button'

export default function Settings() {
  const settings = useSettingsStore((s) => s.settings)
  const updateSettings = useSettingsStore((s) => s.updateSettings)

  const [localSettings, setLocalSettings] = useState({
    // LLM Configuration
    llmProvider: settings?.llmProvider || 'jedai',
    llmModel: settings?.llmModel || 'claude-sonnet-4',
    
    // Generation Settings
    autoSave: settings?.autoSave !== undefined ? settings.autoSave : true,
    maxRetryAttempts: settings?.maxRetryAttempts || 3,
    
    // UI Settings
    darkMode: settings?.darkMode || false,
  })

  const [testStatus, setTestStatus] = useState(null) // null, 'testing', 'success', 'error'
  const [testMessage, setTestMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  
  // Load settings from backend on mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const response = await fetch('/api/settings/')
        if (response.ok) {
          const data = await response.json()
          const backendSettings = {
            llmProvider: data.llm_provider || 'jedai',
            llmModel: data.llm_model || 'claude-sonnet-4',
            autoSave: data.auto_save !== undefined ? data.auto_save : true,
            maxRetryAttempts: data.max_retry_attempts || 3,
            darkMode: data.dark_mode || false,
          }
          setLocalSettings(backendSettings)
          updateSettings(backendSettings)
        }
      } catch (error) {
        console.log('Using local settings, backend not available')
      }
    }
    loadSettings()
  }, [])
  
  // Sync when store settings change
  useEffect(() => {
    if (settings) {
      setLocalSettings({
        llmProvider: settings.llmProvider || 'jedai',
        llmModel: settings.llmModel || 'claude-sonnet-4',
        autoSave: settings.autoSave !== undefined ? settings.autoSave : true,
        maxRetryAttempts: settings.maxRetryAttempts || 3,
        darkMode: settings.darkMode || false,
      })
    }
  }, [settings])

  const handleSave = async () => {
    setIsLoading(true)
    try {
      // Update local store
      updateSettings(localSettings)
      
      // Sync to backend API (convert camelCase to snake_case for Python)
      const response = await fetch('/api/settings/', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          llm_provider: localSettings.llmProvider,
          llm_model: localSettings.llmModel,
          temperature: 0.7,  // Fixed default
          max_tokens: 4096,  // Fixed default
          max_retry_attempts: localSettings.maxRetryAttempts,
          auto_save: localSettings.autoSave,
          auto_test: false,  // Removed from UI
          dark_mode: localSettings.darkMode,
        })
      })
      
      if (response.ok) {
        alert('Settings saved successfully!')
      } else {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to save')
      }
    } catch (error) {
      alert('Failed to save settings: ' + error.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleReset = () => {
    setLocalSettings({
      llmProvider: 'jedai',
      llmModel: 'claude-sonnet-4',
      autoSave: true,
      maxRetryAttempts: 3,
      darkMode: false,
    })
  }

  const handleTestConnection = async () => {
    setTestStatus('testing')
    setTestMessage('Testing JEDAI connection...')
    
    try {
      const response = await fetch('/api/settings/test-llm-connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: localSettings.llmProvider,
          model: localSettings.llmModel
        })
      })
      
      const result = await response.json()
      
      if (result.success) {
        setTestStatus('success')
        setTestMessage(`✓ Connection successful! Model: ${result.model}`)
      } else {
        setTestStatus('error')
        setTestMessage(`✗ Connection failed: ${result.error}`)
      }
    } catch (error) {
      setTestStatus('error')
      setTestMessage(`✗ Test failed: ${error.message}`)
    }
  }

  // Model options based on provider - JEDAI has 37 models grouped by family
  const getModelOptions = () => {
    switch (localSettings.llmProvider) {
      case 'jedai':
        return [
          // Claude models (Recommended for code generation)
          { value: 'claude-sonnet-4', label: 'Claude Sonnet 4', group: 'Claude' },
          { value: 'claude-sonnet-4-5', label: 'Claude Sonnet 4.5', group: 'Claude' },
          { value: 'claude-opus-4', label: 'Claude Opus 4', group: 'Claude' },
          { value: 'claude-opus-4-1', label: 'Claude Opus 4.1', group: 'Claude' },
          { value: 'claude-haiku-4-5', label: 'Claude Haiku 4.5 (Fast)', group: 'Claude' },
          { value: 'claude-3-7-sonnet', label: 'Claude 3.7 Sonnet', group: 'Claude' },
          { value: 'claude-3-5-sonnet', label: 'Claude 3.5 Sonnet', group: 'Claude' },
          { value: 'claude-3-opus', label: 'Claude 3 Opus', group: 'Claude' },
          
          // Gemini models
          { value: 'gemini-2-5-pro', label: 'Gemini 2.5 Pro', group: 'Gemini' },
          { value: 'gemini-2-5-flash', label: 'Gemini 2.5 Flash', group: 'Gemini' },
          { value: 'gemini-2-5-flash-lite', label: 'Gemini 2.5 Flash Lite', group: 'Gemini' },
          { value: 'gemini-1-5-pro', label: 'Gemini 1.5 Pro', group: 'Gemini' },
          
          // Azure OpenAI models
          { value: 'azure-gpt-5-2', label: 'Azure GPT-5.2', group: 'Azure OpenAI' },
          { value: 'azure-gpt-5', label: 'Azure GPT-5', group: 'Azure OpenAI' },
          { value: 'azure-gpt-5-mini', label: 'Azure GPT-5 Mini', group: 'Azure OpenAI' },
          { value: 'azure-gpt-4o', label: 'Azure GPT-4o', group: 'Azure OpenAI' },
          { value: 'azure-o4-mini', label: 'Azure o4-mini', group: 'Azure OpenAI' },
          { value: 'azure-gpt-4-turbo', label: 'Azure GPT-4 Turbo', group: 'Azure OpenAI' },
          { value: 'azure-gpt-4-vision', label: 'Azure GPT-4 Vision', group: 'Azure OpenAI' },
          
          // DeepSeek models
          { value: 'deepseek-r1', label: 'DeepSeek R1', group: 'DeepSeek' },
          { value: 'deepseek-v3-1', label: 'DeepSeek V3.1', group: 'DeepSeek' },
          
          // Meta Llama models
          { value: 'meta-llama-4-maverick-17b', label: 'Llama 4 Maverick 17B', group: 'Meta Llama' },
          { value: 'meta-llama-4-scout-17b', label: 'Llama 4 Scout 17B', group: 'Meta Llama' },
          { value: 'meta-llama-3-3-70b-instruct', label: 'Llama 3.3 70B', group: 'Meta Llama' },
          { value: 'meta-llama-3-1-405b-instruct', label: 'Llama 3.1 405B', group: 'Meta Llama' },
          { value: 'meta-llama-3-1-70b-instruct', label: 'Llama 3.1 70B', group: 'Meta Llama' },
          { value: 'meta-llama-3-1-8b-instruct', label: 'Llama 3.1 8B', group: 'Meta Llama' },
          
          // Qwen models
          { value: 'qwen3-coder-480b', label: 'Qwen3 Coder 480B', group: 'Qwen' },
          { value: 'qwen3-235b-instruct', label: 'Qwen3 235B Instruct', group: 'Qwen' },
          
          // On-Premise models
          { value: 'onprem-gpt-oss-120b', label: 'GPT OSS 120B', group: 'On-Premise' },
          { value: 'onprem-gpt-oss-120b-sj', label: 'GPT OSS 120B (SJ)', group: 'On-Premise' },
          { value: 'onprem-gpt-oss-70b', label: 'GPT OSS 70B', group: 'On-Premise' },
          { value: 'onprem-gpt-oss-20b', label: 'GPT OSS 20B', group: 'On-Premise' },
          { value: 'onprem-llama-3-3-chat', label: 'Llama 3.3 Chat', group: 'On-Premise' },
          { value: 'onprem-llama-3-1-chat', label: 'Llama 3.1 Chat', group: 'On-Premise' },
          { value: 'onprem-llama-3-3-nemotron-49b', label: 'Llama 3.3 Nemotron 49B', group: 'On-Premise' },
          { value: 'onprem-qwen3-32b', label: 'Qwen3 32B', group: 'On-Premise' },
        ]
      case 'openai':
        return [
          { value: 'gpt-4-turbo', label: 'GPT-4 Turbo', group: 'OpenAI' },
          { value: 'gpt-4', label: 'GPT-4', group: 'OpenAI' },
          { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo', group: 'OpenAI' },
        ]
      case 'anthropic':
        return [
          { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet', group: 'Anthropic' },
          { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus', group: 'Anthropic' },
        ]
      default:
        return [{ value: localSettings.llmModel, label: localSettings.llmModel, group: 'Other' }]
    }
  }

  // Group models by family for select optgroup
  const getGroupedModelOptions = () => {
    const options = getModelOptions()
    const groups = {}
    options.forEach(opt => {
      if (!groups[opt.group]) groups[opt.group] = []
      groups[opt.group].push(opt)
    })
    return groups
  }

  return (
    <div className="min-h-full bg-gray-50">
      <div className="w-full px-6 py-8 space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Settings</h1>
            <p className="mt-1 text-sm text-gray-600">
              Configure LLM provider, model selection, and generation settings
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="secondary" onClick={handleReset} disabled={isLoading}>
              Reset to Defaults
            </Button>
            <Button onClick={handleSave} disabled={isLoading}>
              {isLoading ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </div>

        {/* Test Status Message - Full Width */}
        {testMessage && (
          <div className={`px-4 py-2.5 rounded-lg text-sm ${
            testStatus === 'success' ? 'bg-green-50 text-green-700 border border-green-200' :
            testStatus === 'error' ? 'bg-red-50 text-red-700 border border-red-200' :
            'bg-blue-50 text-blue-700 border border-blue-200'
          }`}>
            {testMessage}
          </div>
        )}

        {/* Stats Row - Quick Overview */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <div className="text-center">
              <div className="text-xs text-gray-500 mb-1">Provider</div>
              <div className="text-lg font-semibold text-blue-600 uppercase">{localSettings.llmProvider}</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-xs text-gray-500 mb-1">Model</div>
              <div className="text-sm font-semibold text-gray-900 truncate">{
                getModelOptions().find(m => m.value === localSettings.llmModel)?.label || localSettings.llmModel
              }</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-xs text-gray-500 mb-1">Max Retries</div>
              <div className="text-lg font-semibold text-gray-900">{localSettings.maxRetryAttempts}</div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-xs text-gray-500 mb-1">Auto-save</div>
              <div className={`text-lg font-semibold ${localSettings.autoSave ? 'text-green-600' : 'text-gray-400'}`}>
                {localSettings.autoSave ? 'ON' : 'OFF'}
              </div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <div className="text-xs text-gray-500 mb-1">Status</div>
              <div className={`text-lg font-semibold ${
                testStatus === 'success' ? 'text-green-600' : 
                testStatus === 'error' ? 'text-red-600' : 'text-blue-600'
              }`}>
                {testStatus === 'success' ? '✓ Ready' : testStatus === 'error' ? '✗ Error' : '● Ready'}
              </div>
            </div>
          </Card>
        </div>

        {/* Main Content - 2x2 Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Card 1 - LLM Configuration (Top Left) */}
          <Card>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">LLM Configuration</h2>
                <Button 
                  variant="secondary" 
                  size="sm"
                  onClick={handleTestConnection}
                  disabled={testStatus === 'testing'}
                >
                  {testStatus === 'testing' ? 'Testing...' : 'Test Connection'}
                </Button>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Provider</label>
                <select
                  value={localSettings.llmProvider}
                  onChange={(e) => setLocalSettings({ 
                    ...localSettings, 
                    llmProvider: e.target.value,
                    llmModel: e.target.value === 'jedai' ? 'claude-sonnet-4' : 
                              e.target.value === 'anthropic' ? 'claude-3-5-sonnet-20241022' : 'gpt-4-turbo'
                  })}
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  <option value="jedai">JEDAI (Cadence Internal - 37 Models)</option>
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Model</label>
                <select
                  value={localSettings.llmModel}
                  onChange={(e) => setLocalSettings({ ...localSettings, llmModel: e.target.value })}
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  {Object.entries(getGroupedModelOptions()).map(([group, options]) => (
                    <optgroup key={group} label={`── ${group} ──`}>
                      {options.map(option => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
              </div>

              {/* Model Family Stats - only for JEDAI */}
              {localSettings.llmProvider === 'jedai' && (
                <div className="pt-3 border-t border-gray-100">
                  <div className="text-xs font-medium text-gray-500 mb-2">Model Families ({getModelOptions().length} total)</div>
                  <div className="flex flex-wrap gap-1.5">
                    {[
                      { name: 'Claude', count: 8, color: 'bg-orange-100 text-orange-700' },
                      { name: 'Gemini', count: 4, color: 'bg-blue-100 text-blue-700' },
                      { name: 'Azure', count: 7, color: 'bg-green-100 text-green-700' },
                      { name: 'DeepSeek', count: 2, color: 'bg-purple-100 text-purple-700' },
                      { name: 'Llama', count: 6, color: 'bg-indigo-100 text-indigo-700' },
                      { name: 'Qwen', count: 2, color: 'bg-pink-100 text-pink-700' },
                      { name: 'On-Prem', count: 8, color: 'bg-gray-100 text-gray-700' },
                    ].map(family => (
                      <span key={family.name} className={`px-2 py-0.5 rounded text-xs font-medium ${family.color}`}>
                        {family.name}:{family.count}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Card>

          {/* Card 2 - Quick Reference (Top Right) */}
          <Card>
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-gray-900">Quick Reference</h2>
              
              <div>
                <div className="text-sm font-medium text-gray-700 mb-2">📌 Recommended Models</div>
                <div className="space-y-1.5 text-xs text-gray-600">
                  <div className="flex items-center gap-2">
                    <span className="w-20 font-medium text-gray-900">Code Gen:</span>
                    <span className="px-2 py-0.5 bg-orange-100 text-orange-700 rounded">Claude Sonnet 4</span>
                    <span className="text-gray-400">balanced speed & quality</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-20 font-medium text-gray-900">Fast Tasks:</span>
                    <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded">Gemini 2.0 Flash</span>
                    <span className="text-gray-400">quick responses</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-20 font-medium text-gray-900">Complex:</span>
                    <span className="px-2 py-0.5 bg-orange-100 text-orange-700 rounded">Claude Opus 4</span>
                    <span className="text-gray-400">highest quality</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-20 font-medium text-gray-900">Budget:</span>
                    <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded">DeepSeek V3</span>
                    <span className="text-gray-400">cost effective</span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-gray-100">
                <div className="text-sm font-medium text-gray-700 mb-2">🔐 JEDAI Authentication</div>
                <ul className="space-y-1 text-xs text-gray-600">
                  <li>• Username auto-detected from system login</li>
                  <li>• Password prompted when LLM call is made</li>
                  <li>• Environment (DPC/Non-DPC) auto-detected</li>
                </ul>
              </div>

              <div className="pt-3 border-t border-gray-100">
                <div className="text-sm font-medium text-gray-700 mb-2">💡 Tips</div>
                <ul className="space-y-1 text-xs text-gray-600">
                  <li>• Always <strong>Test Connection</strong> before running generation tasks</li>
                  <li>• Use <strong>3 retries</strong> for complex code generation</li>
                </ul>
              </div>
            </div>
          </Card>

          {/* Card 3 - Generation Settings (Bottom Left) */}
          <Card>
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-gray-900">Generation Settings</h2>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Max Retry Attempts</label>
                <select
                  value={localSettings.maxRetryAttempts}
                  onChange={(e) => setLocalSettings({ ...localSettings, maxRetryAttempts: parseInt(e.target.value) })}
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  <option value={1}>1 - No retry</option>
                  <option value={2}>2 attempts</option>
                  <option value={3}>3 attempts (Default)</option>
                  <option value={5}>5 attempts</option>
                </select>
                <p className="mt-1.5 text-xs text-gray-500">Retry when code generation fails syntax validation</p>
              </div>

              <div className="pt-3 border-t border-gray-100">
                <div className="text-sm font-medium text-gray-700 mb-3">Options</div>
                <div className="space-y-3">
                  {/* Auto-save Toggle */}
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <div className="text-sm font-medium text-gray-900">Auto-save Progress</div>
                      <div className="text-xs text-gray-500">Save state after each generation step</div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setLocalSettings({ ...localSettings, autoSave: !localSettings.autoSave })}
                      className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                        localSettings.autoSave ? 'bg-blue-600' : 'bg-gray-200'
                      }`}
                    >
                      <span className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                        localSettings.autoSave ? 'translate-x-5' : 'translate-x-0'
                      }`} />
                    </button>
                  </div>

                  {/* Dark Mode Toggle */}
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg opacity-50">
                    <div>
                      <div className="text-sm font-medium text-gray-900">Dark Mode</div>
                      <div className="text-xs text-gray-500">Coming soon</div>
                    </div>
                    <button type="button" disabled className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-not-allowed rounded-full border-2 border-transparent bg-gray-200">
                      <span className="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 translate-x-0" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Card 4 - Current Configuration (Bottom Right) */}
          <Card>
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-gray-900">Current Configuration</h2>
              
              <div className="bg-gray-900 rounded-lg p-4 font-mono text-xs">
                <div className="text-gray-400 mb-2"># Active Settings</div>
                <div className="space-y-1">
                  <div><span className="text-purple-400">provider</span><span className="text-gray-500">: </span><span className="text-green-400">"{localSettings.llmProvider}"</span></div>
                  <div><span className="text-purple-400">model</span><span className="text-gray-500">: </span><span className="text-green-400">"{localSettings.llmModel}"</span></div>
                  <div><span className="text-purple-400">max_retries</span><span className="text-gray-500">: </span><span className="text-yellow-400">{localSettings.maxRetryAttempts}</span></div>
                  <div><span className="text-purple-400">auto_save</span><span className="text-gray-500">: </span><span className="text-blue-400">{localSettings.autoSave ? 'true' : 'false'}</span></div>
                </div>
              </div>

              <div className="pt-3 border-t border-gray-100">
                <p className="text-xs text-gray-500 mb-3">
                  These settings will be applied to all new code generation tasks.
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-50 text-green-700 rounded text-xs">
                    <span>✓</span> Settings loaded
                  </span>
                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">
                    <span>↻</span> Syncs on Save
                  </span>
                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-50 text-purple-700 rounded text-xs">
                    <span>💾</span> localStorage
                  </span>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
