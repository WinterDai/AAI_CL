import { useState, useEffect } from 'react'
import Card from '@/components/common/Card'
import Button from '@/components/common/Button'
import { useGenerationStore } from '@/store/generationStore'
import { useSettingsStore } from '@/store/settingsStore'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'

export default function Step3README({ itemId }) {
  const generatedReadme = useGenerationStore((s) => s.generatedReadme)
  const setGeneratedReadme = useGenerationStore((s) => s.setGeneratedReadme)
  const stepStates = useGenerationStore((s) => s.stepStates)
  const setStepState = useGenerationStore((s) => s.setStepState)
  const setStatus = useGenerationStore((s) => s.setStatus)
  const setHintsHistory = useGenerationStore((s) => s.setHintsHistory)
  
  // Get data from project
  const project = useGenerationStore((s) => s.project)
  const yamlConfig = useGenerationStore((s) => s.yamlConfig || s.project.yamlConfig)
  const fileAnalysis = useGenerationStore((s) => s.fileAnalysis)
  const setFileAnalysis = useGenerationStore((s) => s.setFileAnalysis)
  
  // Get module and item from locked project
  const selectedModule = project.module
  const selectedItem = project.itemId
  
  // Get Step3 generation state from store (persists across navigation)
  const step3IsGenerating = useGenerationStore((s) => s.step3IsGenerating)
  const setStep3IsGenerating = useGenerationStore((s) => s.setStep3IsGenerating)
  const step3GenerationLogs = useGenerationStore((s) => s.step3GenerationLogs)
  const setStep3GenerationLogs = useGenerationStore((s) => s.setStep3GenerationLogs)
  const addStep3Log = useGenerationStore((s) => s.addStep3Log)
  
  // Use store state for generation status (local aliases for compatibility)
  const isGenerating = step3IsGenerating
  const setIsGenerating = setStep3IsGenerating
  // Ensure generationLogs is always an array (handle corrupted persist state)
  const generationLogs = Array.isArray(step3GenerationLogs) ? step3GenerationLogs : []
  
  // Get LLM settings
  const settings = useSettingsStore((s) => s.settings)
  
  const [hints, setHints] = useState('')
  const [hintsHistory, setHintsHistoryLocal] = useState([])
  const [loadCount, setLoadCount] = useState(0)  // Track number of loads for numbering
  const [hintsLoaded, setHintsLoaded] = useState(false)
  const [hintsModified, setHintsModified] = useState(false)  // Track if hints were manually edited
  const [showHistory, setShowHistory] = useState(false)
  const [hintsMode, setHintsMode] = useState('use') // 'use' | 'hints_only' | 'no_hints'
  const [viewMode, setViewMode] = useState('rendered') // 'rendered' or 'raw'
  
  // Add log entry helper (uses store action)
  const addLog = (message, level = 'info') => {
    addStep3Log(message, level)
  }

  // Sync local hintsHistory to global store for LeftSidebar
  const syncHintsToStore = (history) => {
    setHintsHistoryLocal(history)
    setHintsHistory(history)  // Sync to global store
  }

  // Load existing README on mount (for resume functionality)
  const [readmeStatus, setReadmeStatus] = useState({ isTemplate: false, modifiedTime: null })
  const [isEditing, setIsEditing] = useState(false)
  const [editContent, setEditContent] = useState('')
  const [readmeLoaded, setReadmeLoaded] = useState(false)  // Prevent duplicate loading
  
  useEffect(() => {
    const loadExistingReadme = async () => {
      if (!selectedModule || !selectedItem) return
      // Skip if generation is in progress
      if (step3IsGenerating) return
      // Skip if already loaded in this session
      if (readmeLoaded) return
      // Skip if already have content in store (from current session generation)
      if (generatedReadme) {
        setReadmeLoaded(true)
        return
      }
      
      try {
        const response = await fetch('http://localhost:8000/api/step3/load-readme', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            module: selectedModule,
            item_id: selectedItem
          })
        })
        
        if (response.ok) {
          const data = await response.json()
          if (data.exists) {
            setGeneratedReadme(data.readme)
            // Check if it's a template (contains TODO:)
            const isTemplate = data.readme.includes('TODO:')
            setReadmeStatus({
              isTemplate,
              modifiedTime: data.modified_time,
              path: data.path
            })
            if (isTemplate) {
              addLog(`Loaded README template (contains TODO sections)`, 'info')
            } else {
              addLog(`Loaded existing README from ${data.modified_time}`, 'info')
            }
            console.log(`📂 Loaded README: template=${isTemplate}, modified=${data.modified_time}`)
          }
        }
        setReadmeLoaded(true)  // Mark as loaded regardless of result
      } catch (error) {
        console.error('Failed to load README:', error)
        setReadmeLoaded(true)  // Mark as loaded even on error to prevent retries
      }
    }
    
    loadExistingReadme()
  }, [selectedModule, selectedItem])

  // Load Step2 fileAnalysis if not in store but Step2 is completed
  useEffect(() => {
    const loadStep2Data = async () => {
      if (!selectedModule || !selectedItem) return
      // Skip if already have fileAnalysis in store
      if (fileAnalysis && fileAnalysis.length > 0) return
      // Check if Step2 is completed
      if (stepStates[2] !== 'completed') return
      
      try {
        const response = await fetch('http://localhost:8000/api/step2/load-file-analysis', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            module: selectedModule,
            item_id: selectedItem
          })
        })
        
        if (response.ok) {
          const data = await response.json()
          if (data.exists && data.file_analysis) {
            setFileAnalysis(data.file_analysis)
            addLog(`Loaded Step2 file analysis (${data.file_count} files)`, 'info')
            console.log(`📂 Loaded Step2 analysis: ${data.file_count} files`)
          }
        }
      } catch (error) {
        console.error('Failed to load Step2 analysis:', error)
      }
    }
    
    loadStep2Data()
  }, [selectedModule, selectedItem, stepStates])
  
  // Load hints history on mount or when module/item changes
  useEffect(() => {
    const loadHints = async () => {
      if (!selectedModule || !selectedItem) return
      
      try {
        const response = await fetch('http://localhost:8000/api/step3/load-hints', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            module: selectedModule,
            item_id: selectedItem
          })
        })
        
        if (response.ok) {
          const data = await response.json()
          if (data.has_hints) {
            syncHintsToStore(data.history || [])
            // Auto-load latest hints if available and not already set
            if (data.latest && !hints) {
              setHints(data.latest)
              setLoadCount(1)
              console.log(`Loaded ${data.count} hints version(s) for ${selectedItem}`)
            }
            setHintsLoaded(true)
          }
        }
      } catch (error) {
        console.error('Failed to load hints:', error)
      }
    }
    
    loadHints()
  }, [selectedModule, selectedItem])

  // Handle hint action buttons
  const handleHintAction = (action) => {
    switch (action) {
      case 'U': // Use - Use current hints in text box for README generation
        setHintsMode('use')
        if (hints.trim()) {
          addLog('Mode: Use current hints for generation', 'info')
        } else {
          addLog('Mode: Use (no hints entered yet)', 'info')
        }
        break
        
      case 'H': // Hints Only - Use only hints, skip file analysis context
        setHintsMode('hints_only')
        addLog('Mode: Hints Only - Will use only hints for generation', 'info')
        break
        
      case 'N': // No Hints - Clear hints and reset count
        setHints('')
        setLoadCount(0)
        setHintsModified(false)
        setHintsMode('no_hints')
        addLog('Hints cleared', 'info')
        break
        
      case 'S': // Show - Toggle history panel
        setShowHistory(!showHistory)
        break
    }
  }

  // Load specific hints version from history (append mode with numbering)
  const loadHintsVersion = (version) => {
    const newCount = loadCount + 1
    // Append with numbered separator
    if (hints.trim()) {
      setHints(prev => `${prev}\n\n${newCount}) ${version.hints}`)
    } else {
      setHints(`1) ${version.hints}`)
    }
    setLoadCount(newCount)
    setHintsModified(false)  // Loading is not a modification
    setHintsMode('use')
    addLog(`Loaded hints #${newCount} from ${version.timestamp}`, 'info')
  }
  
  const handleStartGeneration = async () => {
    // Debug: Log all prerequisites
    console.log('[Step3] handleStartGeneration called')
    console.log('[Step3] selectedModule:', selectedModule)
    console.log('[Step3] selectedItem:', selectedItem)
    console.log('[Step3] yamlConfig:', yamlConfig)
    console.log('[Step3] fileAnalysis:', fileAnalysis?.length || 0, 'files')
    
    // Validate prerequisites
    if (!yamlConfig) {
      alert('Please complete Step 1 (Configuration) first')
      return
    }
    
    if (!fileAnalysis || fileAnalysis.length === 0) {
      alert('Please complete Step 2 (File Analysis) first')
      return
    }
    
    setIsGenerating(true)
    setStatus('running')
    setStepState(3, 'running')
    setStep3GenerationLogs([])  // Clear previous logs using store action
    
    // Use setTimeout to ensure logs are added after state is cleared
    setTimeout(() => {
      addLog('Starting README generation...', 'info')
      addLog(`   Module: ${selectedModule}`, 'info')
      addLog(`   Item: ${selectedItem}`, 'info')
      addLog(`   LLM: ${settings.llmProvider || 'jedai'} - ${settings.llmModel || 'claude-sonnet-4-5'}`, 'info')
      addLog(`   Hints Mode: ${hintsMode}`, 'info')
    }, 0)
    
    console.log('[Step3] Starting README generation with LLM...')
    console.log('[Step3]    Module:', selectedModule)
    console.log('[Step3]    Item:', selectedItem)
    console.log('[Step3]    Input files:', yamlConfig.input_files?.length || 0)
    console.log('[Step3]    File analysis:', fileAnalysis.length)
    console.log('[Step3]    Hints mode:', hintsMode)
    
    try {
      console.log('[Step3] About to send fetch request...')
      addLog('Sending request to backend...', 'info')
      
      // Prepare request based on hints mode
      const requestBody = {
        module: selectedModule,
        item_id: selectedItem,
        item_name: yamlConfig.item_name || selectedItem,
        description: yamlConfig.description || '',
        input_files: yamlConfig.input_files || [],
        file_analysis: hintsMode === 'hints_only' ? [] : fileAnalysis, // Skip file analysis if hints_only
        llm_provider: settings.llmProvider || 'jedai',
        llm_model: settings.llmModel || 'claude-sonnet-4-5',
        hints: hintsMode === 'no_hints' ? '' : hints,
        hints_mode: hintsMode
      }
      
      console.log('[Step3] Request body prepared:', JSON.stringify(requestBody).substring(0, 200) + '...')
      
      const response = await fetch('http://localhost:8000/api/step3/generate-readme', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      })
      
      console.log('[Step3] Response received, status:', response.status)
      
      if (response.ok) {
        addLog('LLM generating README...', 'info')
        const data = await response.json()
        console.log('[Step3] README generated:', data.message)
        addLog(`${data.message}`, 'success')
        setGeneratedReadme(data.readme)
        setStepState(3, 'completed')
        setStatus('idle')
        
        // Reload hints history to include newly saved hints (sync to store)
        if (hints) {
          const hintsResponse = await fetch('http://localhost:8000/api/step3/load-hints', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              module: selectedModule,
              item_id: selectedItem
            })
          })
          if (hintsResponse.ok) {
            const hintsData = await hintsResponse.json()
            if (hintsData.has_hints) {
              syncHintsToStore(hintsData.history || [])
            }
          }
        }
      } else {
        const error = await response.json()
        throw new Error(error.detail || 'Generation failed')
      }
    } catch (error) {
      console.error('README generation error:', error)
      addLog(`Error: ${error.message}`, 'error')
      alert(`README generation failed: ${error.message}`)
      setStepState(3, 'idle')
      setStatus('idle')
    } finally {
      setIsGenerating(false)
    }
  }
  
  const handleReGenerate = () => {
    if (window.confirm('This will replace existing README content. Continue?')) {
      setGeneratedReadme('')
      handleStartGeneration()
    }
  }
  
  // Edit functionality
  const handleEdit = () => {
    setEditContent(generatedReadme || '')
    setIsEditing(true)
  }
  
  const handleSaveEdit = async () => {
    try {
      // Save to backend
      const response = await fetch('http://localhost:8000/api/step3/save-readme', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          module: selectedModule,
          item_id: selectedItem,
          content: editContent
        })
      })
      
      if (response.ok) {
        setGeneratedReadme(editContent)
        setIsEditing(false)
        addLog('README saved successfully', 'success')
        // Update template status
        const isTemplate = editContent.includes('TODO:')
        setReadmeStatus(prev => ({ ...prev, isTemplate, modifiedTime: new Date().toLocaleString() }))
      } else {
        throw new Error('Failed to save README')
      }
    } catch (error) {
      console.error('Save error:', error)
      addLog(`Save failed: ${error.message}`, 'error')
    }
  }
  
  const handleCancelEdit = () => {
    setIsEditing(false)
    setEditContent('')
  }

  const stepStatus = stepStates[3] || 'idle'
  const isCompleted = stepStatus === 'completed' || generatedReadme
  // Don't show mock data - only show actual generated content
  const displayContent = generatedReadme
  
  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-base font-semibold text-gray-900">
            Step 3: README Generation
          </h1>
          <div className="mt-1 flex items-center gap-2">
            <span className="text-xs text-gray-600">
              {isGenerating ? '⏳ AI is generating documentation...' : 'AI-powered checker documentation generation'}
            </span>
            {readmeStatus.isTemplate && displayContent && (
              <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                Template (contains TODO)
              </span>
            )}
            {!readmeStatus.isTemplate && displayContent && (
              <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                Generated
              </span>
            )}
            {readmeStatus.modifiedTime && (
              <span className="text-xs text-gray-500">
                Modified: {readmeStatus.modifiedTime}
              </span>
            )}
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {isEditing ? (
            <>
              <Button variant="secondary" size="xs" onClick={handleCancelEdit}>
                Cancel
              </Button>
              <Button size="xs" onClick={handleSaveEdit}>
                💾 Save
              </Button>
            </>
          ) : isCompleted && !isGenerating ? (
            <>
              <Button variant="secondary" size="xs" onClick={handleEdit}>
                ✏️ Edit
              </Button>
              <Button size="xs" onClick={handleReGenerate}>
                🔄 Re-generate
              </Button>
            </>
          ) : (
            <Button 
              onClick={handleStartGeneration} 
              disabled={isGenerating}
              size="xs"
            >
              {isGenerating ? '⏳ Generating...' : '🚀 Start Generation'}
            </Button>
          )}
        </div>
      </div>

      {/* Hints Input */}
      <Card>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold text-gray-900">
                Additional Hints
              </h2>
              {hintsHistory.length > 0 && (
                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                  {hintsHistory.length} version{hintsHistory.length > 1 ? 's' : ''} saved
                </span>
              )}
              {hintsModified && hints.trim() && (
                <span className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs rounded-full">
                  Modified (will save on generate)
                </span>
              )}
              {hintsMode !== 'use' && (
                <span className={`px-2 py-0.5 text-xs rounded-full ${
                  hintsMode === 'hints_only' ? 'bg-orange-100 text-orange-700' : 'bg-gray-100 text-gray-600'
                }`}>
                  {hintsMode === 'hints_only' ? 'Hints Only Mode' : 'No Hints Mode'}
                </span>
              )}
            </div>
            <div className="flex items-center space-x-1">
              <Button
                size="xs"
                variant={hintsMode === 'use' ? 'primary' : 'secondary'}
                onClick={() => handleHintAction('U')}
                title="Use current hints in text box for README generation"
              >
                [U] Use
              </Button>
              <Button
                size="xs"
                variant={hintsMode === 'hints_only' ? 'primary' : 'secondary'}
                onClick={() => handleHintAction('H')}
                title="Use only hints, skip file analysis context"
              >
                [H] Hints Only
              </Button>
              <Button
                size="xs"
                variant={hintsMode === 'no_hints' ? 'primary' : 'secondary'}
                onClick={() => handleHintAction('N')}
                title="Clear hints and generate without them"
              >
                [N] No Hints
              </Button>
              <Button
                size="xs"
                variant={showHistory ? 'primary' : 'secondary'}
                onClick={() => handleHintAction('S')}
                title="Show hints history (click to load specific version)"
              >
                [S] Show {hintsHistory.length > 0 ? `(${hintsHistory.length})` : ''}
              </Button>
            </div>
          </div>

          <textarea
            value={hints}
            onChange={(e) => {
              setHints(e.target.value)
              setHintsModified(true)  // Mark as modified on manual edit
            }}
            placeholder="Enter additional hints for AI to generate better README...&#10;&#10;Example:&#10;- Check purpose: Verify timing constraints&#10;- Key patterns to look for: setup/hold violations&#10;- Expected output format: table with violation details"
            className="w-full h-28 px-3 py-2 text-xs border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none font-mono"
            disabled={hintsMode === 'no_hints'}
          />

          {/* Hints History Panel */}
          {showHistory && (
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <div className="bg-gray-50 px-3 py-2 border-b border-gray-200">
                <h3 className="text-sm font-medium text-gray-700">Hints History</h3>
              </div>
              <div className="max-h-48 overflow-auto">
                {hintsHistory.length > 0 ? (
                  <div className="divide-y divide-gray-100">
                    {[...hintsHistory].reverse().map((version, index) => (
                      <div 
                        key={index}
                        className="px-3 py-2 hover:bg-gray-50 cursor-pointer group"
                        onClick={() => loadHintsVersion(version)}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-500">{version.timestamp}</span>
                          <div className="flex items-center space-x-2">
                            <button 
                              className="text-xs text-blue-600 hover:text-blue-700"
                              onClick={(e) => {
                                e.stopPropagation()
                                loadHintsVersion(version)
                              }}
                            >
                              Load
                            </button>
                            <button 
                              className="text-xs text-red-500 hover:text-red-700 opacity-0 group-hover:opacity-100 transition-opacity"
                              onClick={async (e) => {
                                e.stopPropagation()
                                if (window.confirm(`Delete hints from ${version.timestamp}?`)) {
                                  try {
                                    const response = await fetch('http://localhost:8000/api/step3/delete-hints', {
                                      method: 'POST',
                                      headers: { 'Content-Type': 'application/json' },
                                      body: JSON.stringify({
                                        module: selectedModule || '',
                                        item_id: selectedItem || '',
                                        timestamp: version.timestamp
                                      })
                                    })
                                    if (response.ok) {
                                      // Reload hints history
                                      const hintsResponse = await fetch('http://localhost:8000/api/step3/load-hints', {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({
                                          module: selectedModule || '',
                                          item_id: selectedItem || ''
                                        })
                                      })
                                      if (hintsResponse.ok) {
                                        const data = await hintsResponse.json()
                                        syncHintsToStore(data.history || [])
                                      }
                                    }
                                  } catch (err) {
                                    console.error('Failed to delete hints:', err)
                                  }
                                }
                              }}
                            >
                              🗑️
                            </button>
                          </div>
                        </div>
                        <p className="text-xs text-gray-700 mt-1 line-clamp-2">
                          {version.hints.substring(0, 150)}{version.hints.length > 150 ? '...' : ''}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="px-3 py-5 text-center text-xs text-gray-500">
                    No hints history yet. Hints will be saved when you generate a README.
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-600">
              {hintsMode === 'hints_only' 
                ? 'Will generate using only hints (no file analysis)'
                : hintsMode === 'no_hints'
                ? 'Will generate without hints'
                : 'Hints will be combined with file analysis for generation'}
            </span>
            {hints && (
              <span className="text-gray-500">
                {hints.length} characters
              </span>
            )}
          </div>
        </div>
      </Card>

      {/* Generated README */}
      <Card>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-900">
              Generated README.md
            </h2>
            <div className="flex items-center space-x-3">
              {displayContent && (
                <div className="flex items-center space-x-1.5 bg-gray-100 rounded-lg p-1">
                  <button
                    onClick={() => setViewMode('rendered')}
                    className={`px-2.5 py-1 text-xs rounded transition-colors ${
                      viewMode === 'rendered'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    📄 Rendered
                  </button>
                  <button
                    onClick={() => setViewMode('raw')}
                    className={`px-2.5 py-1 text-xs rounded transition-colors ${
                      viewMode === 'raw'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    📝 Raw
                  </button>
                </div>
              )}
              {isGenerating && (
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-gray-600">
                    AI generating...
                  </span>
                  <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                </div>
              )}
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-4 max-h-[520px] overflow-auto custom-scrollbar">
            {isEditing ? (
              // Edit mode - show textarea
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="w-full h-[420px] font-mono text-xs text-gray-900 border border-gray-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
                placeholder="Edit README content..."
              />
            ) : displayContent ? (
              viewMode === 'rendered' ? (
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      code({node, inline, className, children, ...props}) {
                        const match = /language-(\w+)/.exec(className || '')
                        return !inline && match ? (
                          <SyntaxHighlighter
                            style={{
                              'pre[class*="language-"]': {
                                background: '#f8fafc',
                                border: '1px solid #e2e8f0',
                                borderRadius: '0.375rem',
                                padding: '0.5rem',
                                fontSize: '0.75rem',
                                lineHeight: '1.4',
                                overflow: 'auto',
                              },
                              'code[class*="language-"]': {
                                color: '#334155',
                                fontFamily: 'inherit',
                              },
                              'comment': { color: '#64748b' },
                              'punctuation': { color: '#64748b' },
                              'property': { color: '#0369a1' },
                              'string': { color: '#059669' },
                              'keyword': { color: '#7c3aed' },
                              'function': { color: '#0284c7' },
                              'number': { color: '#d97706' },
                              'operator': { color: '#475569' },
                              'class-name': { color: '#0891b2' },
                              'tag': { color: '#dc2626' },
                              'attr-name': { color: '#0369a1' },
                              'attr-value': { color: '#059669' },
                            }}
                            language={match[1]}
                            PreTag="div"
                            customStyle={{ fontFamily: 'inherit' }}
                            {...props}
                          >
                            {String(children).replace(/\n$/, '')}
                          </SyntaxHighlighter>
                        ) : (
                          <code className="px-1 py-0.5 bg-gray-100 text-gray-700 rounded text-xs" {...props}>
                            {children}
                          </code>
                        )
                      },
                      h1: ({children}) => <h1 className="text-base font-bold mt-4 mb-3 text-gray-900">{children}</h1>,
                      h2: ({children}) => <h2 className="text-sm font-semibold mt-3 mb-2 text-gray-800 border-b pb-1">{children}</h2>,
                      h3: ({children}) => <h3 className="text-xs font-semibold mt-2 mb-1 text-gray-700">{children}</h3>,
                      p: ({children}) => <p className="mb-2 text-xs text-gray-700 leading-relaxed">{children}</p>,
                      ul: ({children}) => <ul className="list-disc pl-5 mb-2 space-y-0.5 text-xs">{children}</ul>,
                      ol: ({children}) => <ol className="list-decimal pl-5 mb-2 space-y-0.5 text-xs">{children}</ol>,
                      li: ({children}) => <li className="text-xs text-gray-700">{children}</li>,
                      strong: ({children}) => <strong className="font-semibold text-gray-900">{children}</strong>,
                      blockquote: ({children}) => <blockquote className="border-l-3 border-gray-300 pl-3 italic text-xs text-gray-600 my-2">{children}</blockquote>,
                      table: ({children}) => <div className="overflow-x-auto my-2"><table className="min-w-full border border-gray-300 text-xs">{children}</table></div>,
                      th: ({children}) => <th className="border border-gray-300 px-2 py-1 bg-gray-100 font-semibold text-left text-xs">{children}</th>,
                      td: ({children}) => <td className="border border-gray-300 px-2 py-1 text-xs">{children}</td>,
                    }}
                  >
                    {displayContent}
                  </ReactMarkdown>
                </div>
              ) : (
                <pre className="text-xs text-gray-900 whitespace-pre-wrap font-mono">
                  {displayContent}
                </pre>
              )
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p className="text-xs mb-2">No README generated yet</p>
                <p className="text-[11px]">Click "Start Generation" to begin</p>
              </div>
            )}
          </div>

          {displayContent && (
            <div className="flex items-center space-x-2">
              <Button variant="secondary" size="xs" onClick={() => navigator.clipboard.writeText(displayContent)}>
                📋 Copy
              </Button>
              <Button variant="secondary" size="xs">
                💾 Save
              </Button>
            </div>
          )}
        </div>
      </Card>

      {/* Generation Log */}
      <Card>
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-gray-900">
            Generation Log
          </h2>
          
          <div className="space-y-2 text-xs max-h-[200px] overflow-auto">
            {generationLogs.length > 0 ? (
              generationLogs.map((log, index) => (
                <div key={index} className="flex items-start space-x-2">
                  <span className="text-gray-500 text-sm">[{log.timestamp}]</span>
                  <span className={
                    log.level === 'error' ? 'text-red-600' :
                    log.level === 'success' ? 'text-green-600' :
                    'text-gray-900'
                  }>
                    {log.message}
                  </span>
                </div>
              ))
            ) : (
              <div className="text-gray-500 text-center py-4">
                No generation logs yet. Click "Start Generation" to begin.
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  )
}
