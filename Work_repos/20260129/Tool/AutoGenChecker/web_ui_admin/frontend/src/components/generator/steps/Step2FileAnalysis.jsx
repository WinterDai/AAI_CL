import { useState, useEffect } from 'react'
import Card from '@/components/common/Card'
import StatusBadge from '@/components/common/StatusBadge'
import Button from '@/components/common/Button'
import { useGenerationStore } from '@/store/generationStore'
import { useSettingsStore } from '@/store/settingsStore'

export default function Step2FileAnalysis({ itemId }) {
  // Use store for persistent file analysis state
  const fileAnalysis = useGenerationStore((s) => s.fileAnalysis)
  const setFileAnalysis = useGenerationStore((s) => s.setFileAnalysis)
  
  // Get Step2 analysis state from store (persists across navigation)
  const step2IsAnalyzing = useGenerationStore((s) => s.step2IsAnalyzing)
  const setStep2IsAnalyzing = useGenerationStore((s) => s.setStep2IsAnalyzing)
  
  // Use store state for loading (local alias for compatibility)
  const loading = step2IsAnalyzing
  const setLoading = setStep2IsAnalyzing
  
  const [selectedFile, setSelectedFile] = useState(null)
  const [selectedFileIndex, setSelectedFileIndex] = useState(null)
  const [viewMode, setViewMode] = useState('analysis') // 'analysis' or 'content'
  const [selectedTypeTab, setSelectedTypeTab] = useState('type1') // 'type1', 'type2', 'type3', 'type4'
  
  // File content states
  const [fileContent, setFileContent] = useState('')
  const [loadingContent, setLoadingContent] = useState(false)
  const [contentError, setContentError] = useState(null)
  const [contentTruncated, setContentTruncated] = useState(false)
  const [contentTotalLines, setContentTotalLines] = useState(0)
  const [contentShownLines, setContentShownLines] = useState(0)
  
  // Edit mode states
  const [isEditing, setIsEditing] = useState(false)  // Manual edit mode
  const [isAiEditing, setIsAiEditing] = useState(false)  // AI edit mode
  const [editPatterns, setEditPatterns] = useState('')
  const [editParsingStrategy, setEditParsingStrategy] = useState('')
  const [editSampleData, setEditSampleData] = useState('')
  const [aiRefinePrompt, setAiRefinePrompt] = useState('')
  const [isRefining, setIsRefining] = useState(false)
  
  // Get YAML data from store (loaded in Step1)
  const { project, legacyYamlConfig } = useGenerationStore((s) => ({
    project: s.project,
    legacyYamlConfig: s.yamlConfig || null,
  }))
  const yamlConfig = project?.yamlConfig || legacyYamlConfig
  // Get LLM settings from settings store
  const settings = useSettingsStore((s) => s.settings)

  const fetchFileStats = async (filePath) => {
    try {
      const response = await fetch('http://localhost:8000/api/step2/file-stats', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_path: filePath })
      })
      
      if (response.ok) {
        return await response.json()
      }
    } catch (error) {
      console.error('Failed to fetch file stats:', error)
    }
    return { lines: '?', size: '?', exists: false }
  }

  useEffect(() => {
    // Skip if already have analysis results in store
    if (fileAnalysis && fileAnalysis.length > 0) {
      console.log('✅ Using cached file analysis from store')
      return
    }
    
    if (yamlConfig && yamlConfig.input_files) {
      setLoading(true)
      
      // Analyze real input files from YAML
      const analyzeFiles = async () => {
        const analysis = await Promise.all(
          yamlConfig.input_files.map(async (filePath) => {
            const filename = filePath.split(/[\\/]/).pop() || filePath
            const ext = filename.split('.').pop()?.toLowerCase()
            
            // Determine file type based on extension
            let fileType = 'Unknown'
            if (ext === 'rpt') fileType = 'Report File'
            else if (ext === 'log') fileType = 'Log File'
            else if (ext === 'sdc') fileType = 'SDC Constraints'
            else if (ext === 'tcl') fileType = 'TCL Script'
            else if (ext === 'yaml' || ext === 'yml') fileType = 'YAML Config'
            else if (ext === 'txt') fileType = 'Text File'
            else if (ext === 'spi' || ext === 'sp') fileType = 'SPICE Netlist'
            
            // Fetch real file stats
            const stats = await fetchFileStats(filePath)
            
            return {
              filename: filename,
              fullPath: filePath,
              fileType: fileType,
              lines: stats.lines,
              size: stats.size,
              status: stats.exists ? 'PENDING' : 'NOT_FOUND',
              // Initialize 4 types structure
              type1_boolean_check: {
                outputFormat: '',
                patterns: [],
                parsingStrategy: '',
                sampleData: ''
              },
              type2_value_check: {
                outputFormat: '',
                patterns: [],
                parsingStrategy: '',
                sampleData: ''
              },
              type3_value_with_waiver: {
                outputFormat: '',
                patterns: [],
                parsingStrategy: '',
                sampleData: ''
              },
              type4_boolean_with_waiver: {
                outputFormat: '',
                patterns: [],
                parsingStrategy: '',
                sampleData: ''
              },
              // Backward compatibility fields
              patterns: [],
              sampleData: stats.exists 
                ? `File path: ${filePath}\n\nFile exists. Click 'Analyze' button to analyze with LLM.`
                : `File path: ${filePath}\n\n⚠️ File not found on disk.`,
              parsingStrategy: '',
              outputFormat: '',
              templateRecommendations: []
            }
          })
        )
        
        setFileAnalysis(analysis)
        setLoading(false)
      }
      
      analyzeFiles()
    }
  }, [yamlConfig])

  const analyzeFileWithLLM = async (fileIndex) => {
    const file = fileAnalysis[fileIndex]
    if (!file || file.status === 'NOT_FOUND') return
    
    // Update status to ANALYZING
    const updatedFiles = [...fileAnalysis]
    updatedFiles[fileIndex] = { ...file, status: 'ANALYZING' }
    setFileAnalysis(updatedFiles)
    
    try {
      console.log('🚀 Starting analysis for:', file.filename)
      console.log('   File path:', file.fullPath)
      console.log('   File type:', file.fileType)
      console.log('   LLM Provider:', settings.llmProvider || 'jedai')
      console.log('   LLM Model:', settings.llmModel || 'claude-sonnet-4-5')
      
      const response = await fetch('http://localhost:8000/api/step2/analyze-file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          file_path: file.fullPath,
          file_type: file.fileType,
          llm_provider: settings.llmProvider || 'jedai',
          llm_model: settings.llmModel || 'claude-sonnet-4-5',
          description: yamlConfig?.description || ''
        })
      })
      
      console.log('📡 Response status:', response.status, response.statusText)
      
      if (response.ok) {
        const result = await response.json()
        console.log('✅ Analysis result:', result)
        
        // Map backend response (with 4 types) to frontend structure
        updatedFiles[fileIndex] = {
          ...file,
          status: 'ANALYZED',
          fileType: result.file_type || file.fileType,
          // Store all 4 types
          type1_boolean_check: result.type1_boolean_check || {
            outputFormat: '',
            patterns: [],
            parsingStrategy: '',
            sampleData: ''
          },
          type2_value_check: result.type2_value_check || {
            outputFormat: '',
            patterns: [],
            parsingStrategy: '',
            sampleData: ''
          },
          type3_value_with_waiver: result.type3_value_with_waiver || {
            outputFormat: '',
            patterns: [],
            parsingStrategy: '',
            sampleData: ''
          },
          type4_boolean_with_waiver: result.type4_boolean_with_waiver || {
            outputFormat: '',
            patterns: [],
            parsingStrategy: '',
            sampleData: ''
          },
          templateRecommendations: result.templateRecommendations || result.template_recommendations || [],
          // Backward compatibility: use type1 as default display
          patterns: result.type1_boolean_check?.patterns || result.patterns || [],
          outputFormat: result.type1_boolean_check?.outputFormat || result.output_format || result.outputFormat || '',
          parsingStrategy: result.type1_boolean_check?.parsingStrategy || result.parsing_strategy || result.parsingStrategy || '',
          sampleData: result.type1_boolean_check?.sampleData || result.sample_data || result.sampleData || 'Analysis completed!'
        }
      } else {
        const errorText = await response.text()
        console.error('❌ API Error:', response.status, errorText)
        throw new Error(`API returned ${response.status}: ${errorText}`)
      }
    } catch (error) {
      console.error('❌ Analysis failed:', error)
      console.error('   Error name:', error.name)
      console.error('   Error message:', error.message)
      console.error('   Error stack:', error.stack)
      
      updatedFiles[fileIndex] = {
        ...file,
        status: 'ERROR',
        sampleData: `Analysis failed: ${error.message}\n\nPlease check:\n1. Backend server is running (http://localhost:8000)\n2. File path is correct: ${file.fullPath}\n3. Browser console for details`
      }
    }
    
    // Force state update
    setFileAnalysis([...updatedFiles])
    console.log('✅ File analyzed:', file.filename, 'Status:', updatedFiles[fileIndex].status)
  }

  const analyzeAllFiles = async () => {
    setLoading(true)
    for (let i = 0; i < fileAnalysis.length; i++) {
      if (fileAnalysis[i].status === 'PENDING' || fileAnalysis[i].status === 'ERROR') {
        await analyzeFileWithLLM(i)
      }
    }
    setLoading(false)
  }

  // Only show real data; when empty we render an empty state
  const displayFiles = fileAnalysis

  const handleReanalyze = async () => {
    if (!yamlConfig || !yamlConfig.input_files) {
      alert('请先在Step1加载YAML配置')
      return
    }
    
    setLoading(true)
    
    // Re-analyze files with real stats
    const analysis = await Promise.all(
      yamlConfig.input_files.map(async (filePath) => {
        const filename = filePath.split(/[\\/]/).pop() || filePath
        const ext = filename.split('.').pop()?.toLowerCase()
        
        let fileType = 'Unknown'
        if (ext === 'rpt') fileType = 'Report File'
        else if (ext === 'log') fileType = 'Log File'
        else if (ext === 'sdc') fileType = 'SDC Constraints'
        else if (ext === 'tcl') fileType = 'TCL Script'
        else if (ext === 'yaml' || ext === 'yml') fileType = 'YAML Config'
        else if (ext === 'txt') fileType = 'Text File'
        else if (ext === 'spi' || ext === 'sp') fileType = 'SPICE Netlist'
        
        // Fetch real file stats
        const stats = await fetchFileStats(filePath)
        
        return {
          filename: filename,
          fullPath: filePath,
          fileType: fileType,
          lines: stats.lines,
          size: stats.size,
          status: stats.exists ? 'PENDING' : 'NOT_FOUND',
          // Initialize 4 types structure
          type1_boolean_check: {
            outputFormat: '',
            patterns: [],
            parsingStrategy: '',
            sampleData: ''
          },
          type2_value_check: {
            outputFormat: '',
            patterns: [],
            parsingStrategy: '',
            sampleData: ''
          },
          type3_value_with_waiver: {
            outputFormat: '',
            patterns: [],
            parsingStrategy: '',
            sampleData: ''
          },
          type4_boolean_with_waiver: {
            outputFormat: '',
            patterns: [],
            parsingStrategy: '',
            sampleData: ''
          },
          // Backward compatibility fields
          patterns: [],
          sampleData: stats.exists 
            ? `File path: ${filePath}\n\nFile re-scanned. Click 'Analyze' to run LLM analysis.`
            : `File path: ${filePath}\n\n⚠️ File not found on disk.`,
          parsingStrategy: '',
          outputFormat: '',
          templateRecommendations: []
        }
      })
    )
    
    setFileAnalysis(analysis)
    setLoading(false)
    console.log('✅ Files re-scanned')
  }

  const handleViewAnalysis = (file, index) => {
    // Toggle: if same file is clicked, close it
    if (selectedFile && selectedFileIndex === index && viewMode === 'analysis') {
      setSelectedFile(null)
      setSelectedFileIndex(null)
      setIsEditing(false)
      setIsAiEditing(false)
    } else {
      setSelectedFile(file)
      setSelectedFileIndex(index)
      setViewMode('analysis')
      setIsEditing(false)
      setIsAiEditing(false)
      // Reset to type1 tab when viewing a file
      setSelectedTypeTab('type1')
      // Initialize edit states from type1
      const type1 = file.type1_boolean_check || {}
      setEditPatterns(type1.patterns?.join('\n') || file.patterns?.join('\n') || '')
      setEditParsingStrategy(type1.parsingStrategy || file.parsingStrategy || '')
      setEditSampleData(type1.sampleData || file.sampleData || '')
    }
  }

  const handleViewFile = async (file, index) => {
    setSelectedFile(file)
    setSelectedFileIndex(index)
    setViewMode('content')
    setLoadingContent(true)
    setFileContent('')
    setContentError(null)
    
    try {
      const response = await fetch('http://localhost:8000/api/step2/file-content', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          file_path: file.fullPath,
          max_lines: 500
        })
      })
      
      const data = await response.json()
      
      if (data.success) {
        setFileContent(data.content)
        setContentTruncated(data.truncated)
        setContentTotalLines(data.total_lines)
        setContentShownLines(data.shown_lines)
      } else {
        setContentError(data.error || 'Failed to load file content')
      }
    } catch (err) {
      setContentError(`Error: ${err.message}`)
    } finally {
      setLoadingContent(false)
    }
  }
  
  // Manual edit functionality
  const handleStartEdit = () => {
    setIsEditing(true)
    setIsAiEditing(false)
    // Get data from currently selected type
    const typeDataKeyMap = {
      'type1': 'type1_boolean_check',
      'type2': 'type2_value_check',
      'type3': 'type3_value_with_waiver',
      'type4': 'type4_boolean_with_waiver'
    }
    const typeKey = typeDataKeyMap[selectedTypeTab]
    const currentType = selectedFile?.[typeKey]
    setEditPatterns(currentType?.patterns?.join('\n') || '')
    setEditParsingStrategy(currentType?.parsingStrategy || '')
    setEditOutputFormat(currentType?.outputFormat || '')
    setEditSampleData(currentType?.sampleData || '')
  }
  
  // AI edit functionality
  const handleStartAiEdit = () => {
    setIsAiEditing(true)
    setIsEditing(false)
    setAiRefinePrompt('')
  }
  
  const handleSaveEdit = () => {
    if (selectedFileIndex === null) return
    
    const updatedFiles = [...fileAnalysis]
    const typeDataKeyMap = {
      'type1': 'type1_boolean_check',
      'type2': 'type2_value_check',
      'type3': 'type3_value_with_waiver',
      'type4': 'type4_boolean_with_waiver'
    }
    const typeKey = typeDataKeyMap[selectedTypeTab]
    
    // Update the specific type's data
    updatedFiles[selectedFileIndex] = {
      ...updatedFiles[selectedFileIndex],
      [typeKey]: {
        patterns: editPatterns.split('\n').filter(p => p.trim()),
        parsingStrategy: editParsingStrategy,
        sampleData: editSampleData
      }
    }
    
    // Update backward compatibility fields if editing type1
    if (selectedTypeTab === 'type1') {
      updatedFiles[selectedFileIndex].patterns = editPatterns.split('\n').filter(p => p.trim())
      updatedFiles[selectedFileIndex].parsingStrategy = editParsingStrategy
      updatedFiles[selectedFileIndex].sampleData = editSampleData
    }
    
    setFileAnalysis(updatedFiles)
    setSelectedFile(updatedFiles[selectedFileIndex])
    setIsEditing(false)
  }
  
  const handleCancelEdit = () => {
    const typeDataKeyMap = {
      'type1': 'type1_boolean_check',
      'type2': 'type2_value_check',
      'type3': 'type3_value_with_waiver',
      'type4': 'type4_boolean_with_waiver'
    }
    const typeKey = typeDataKeyMap[selectedTypeTab]
    const currentType = selectedFile?.[typeKey]
    setEditPatterns(currentType?.patterns?.join('\n') || '')
    setEditParsingStrategy(currentType?.parsingStrategy || '')
    setEditSampleData(currentType?.sampleData || '')
    setIsEditing(false)
    setIsAiEditing(false)
    setAiRefinePrompt('')
  }
  
  // AI Refine functionality - refines the entire analysis
  const handleAiRefine = async () => {
    if (!aiRefinePrompt.trim() || selectedFileIndex === null) return
    
    setIsRefining(true)
    try {
      const response = await fetch('http://localhost:8000/api/step2/refine-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_path: selectedFile.fullPath,
          current_analysis: {
            patterns: selectedFile.patterns || [],
            parsing_strategy: selectedFile.parsingStrategy || '',
            output_format: selectedFile.outputFormat || '',
            sample_data: selectedFile.sampleData || ''
          },
          user_feedback: aiRefinePrompt,
          llm_provider: settings.llmProvider || 'jedai',
          llm_model: settings.llmModel || 'claude-sonnet-4-5'
        })
      })
      
      if (response.ok) {
        const result = await response.json()
        // Update the entire analysis with AI refined results
        const updatedFiles = [...fileAnalysis]
        updatedFiles[selectedFileIndex] = {
          ...updatedFiles[selectedFileIndex],
          patterns: result.patterns || selectedFile.patterns,
          parsingStrategy: result.parsing_strategy || selectedFile.parsingStrategy,
          outputFormat: result.output_format || selectedFile.outputFormat,
          sampleData: result.sample_data || selectedFile.sampleData,
          aiRawResponse: (result.ai_raw_response || '') + '\n\n[Refined based on user feedback]'
        }
        setFileAnalysis(updatedFiles)
        setSelectedFile(updatedFiles[selectedFileIndex])
        setAiRefinePrompt('')
        setIsAiEditing(false)  // Close AI edit mode after refinement
        
        alert('Analysis refined successfully!')
      } else {
        throw new Error('AI refinement failed')
      }
    } catch (error) {
      console.error('AI refine error:', error)
      alert(`AI refinement failed: ${error.message}`)
    } finally {
      setIsRefining(false)
    }
  }

  return (
    <div className="p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-sm font-semibold text-gray-900">
            Step 2: Analyzing Input Files
          </h1>
          <p className="mt-1 text-xs text-gray-600">
            {fileAnalysis.length > 0 
              ? `Displaying ${fileAnalysis.length} input files from YAML configuration`
              : 'No files loaded. Please complete Step 1 first.'}
          </p>
        </div>
        <button 
          onClick={handleReanalyze}
          className="px-3 py-1.5 text-xs text-gray-600 hover:text-gray-900 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
        >
          Reanalyze
        </button>
      </div>
      {/* Status Summary Card */}
      {fileAnalysis.length > 0 && (
        <Card className="mb-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-1">
                Analysis Summary
              </h3>
              <div className="flex items-center space-x-4 text-xs">
                <div>
                  <span className="text-gray-600">Total Files:</span>
                  <span className="ml-2 font-semibold text-gray-900">{fileAnalysis.length}</span>
                </div>
                <div>
                  <span className="text-gray-600">Analyzed:</span>
                  <span className="ml-2 font-semibold text-green-600">
                    {fileAnalysis.filter(f => f.status === 'ANALYZED').length}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Analyzing:</span>
                  <span className="ml-2 font-semibold text-blue-600">
                    {fileAnalysis.filter(f => f.status === 'ANALYZING').length}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Pending:</span>
                  <span className="ml-2 font-semibold text-yellow-600">
                    {fileAnalysis.filter(f => f.status === 'PENDING').length}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Not Found:</span>
                  <span className="ml-2 font-semibold text-red-600">
                    {fileAnalysis.filter(f => f.status === 'NOT_FOUND').length}
                  </span>
                </div>
              </div>
            </div>
            <div className="text-right">
              {fileAnalysis.filter(f => f.status === 'PENDING').length > 0 ? (
                <button
                  onClick={analyzeAllFiles}
                  disabled={loading}
                  className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? 'Analyzing...' : 'Analyze All Files'}
                </button>
              ) : (
                <div>
                  <div className="text-xs text-gray-600 mb-1">
                    All files analyzed
                  </div>
                  <div className="text-xs text-gray-500">
                    Click <strong>Continue</strong> at the bottom to proceed to Step 3
                  </div>
                </div>
              )}
            </div>
          </div>
        </Card>
      )}
      {loading && (
        <Card>
          <div className="text-center py-6 text-gray-600 text-sm">
            Loading input files...
          </div>
        </Card>
      )}

      {!loading && displayFiles.length === 0 && (
        <Card>
          <div className="text-center py-6 text-gray-600 text-sm">
            No files loaded. Please complete Step 1 first.
          </div>
        </Card>
      )}

      <div className="space-y-3">
        {displayFiles.map((file, index) => (
          <Card key={index}>
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <h2 className="text-xs font-semibold text-gray-900">
                      {file.filename}
                    </h2>
                    <StatusBadge status={file.status} />
                  </div>
                  <div className="mt-1 text-xs text-gray-500 font-mono">
                    {file.fullPath}
                  </div>
                  <div className="mt-1 grid grid-cols-3 gap-3 text-xs">
                    <div className="col-span-3 flex items-center space-x-4">
                      <div className="flex items-center space-x-1">
                        <span className="text-gray-600">File Type:</span>
                        <span className="text-gray-900">{file.fileType}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <span className="text-gray-600">Lines:</span>
                        <span className="text-gray-900">{file.lines.toLocaleString()}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <span className="text-gray-600">Size:</span>
                        <span className="text-gray-900">{file.size}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-xs font-medium text-gray-900 mb-1.5">
                  Detected Patterns:
                </h3>
                <ul className="space-y-0.5">
                  {file.patterns.map((pattern, idx) => (
                    <li key={idx} className="text-xs text-gray-600 font-mono">
                      • {pattern}
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <h3 className="text-xs font-medium text-gray-900 mb-1.5">
                  Sample Data:
                </h3>
                <div className="bg-gray-50 rounded-lg p-2">
                  <pre className="text-xs text-gray-700 font-mono whitespace-pre-wrap">
                    {file.sampleData}
                  </pre>
                </div>
              </div>

              <div className="flex items-center justify-between space-x-2 pt-2 border-t border-gray-100 mt-2">
                <div className="flex items-center space-x-2">
                  <button 
                    className="px-3 py-1 text-xs text-gray-700 hover:text-gray-900 border border-gray-300 rounded hover:bg-gray-50 transition-colors"
                    onClick={() => handleViewAnalysis(file, index)}
                  >
                    {selectedFile && selectedFileIndex === index && viewMode === 'analysis' ? 'Hide Analysis' : 'View Analysis'}
                  </button>
                  <button 
                    className="px-3 py-1 text-xs text-gray-700 hover:text-gray-900 border border-gray-300 rounded hover:bg-gray-50 transition-colors"
                    onClick={() => handleViewFile(file, index)}
                  >
                    View File
                  </button>
                </div>
                
                {file.status === 'PENDING' && (
                  <button
                    onClick={() => analyzeFileWithLLM(index)}
                    className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                  >
                    Analyze
                  </button>
                )}
                {file.status === 'ANALYZING' && (
                  <button
                    disabled
                    className="px-3 py-1 text-xs bg-gray-400 text-white rounded cursor-not-allowed"
                  >
                    Analyzing...
                  </button>
                )}
                {file.status === 'ANALYZED' && (
                  <button
                    onClick={() => analyzeFileWithLLM(index)}
                    className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                  >
                    Re-analyze
                  </button>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* File Detail View */}
      {selectedFile && (
        <Card className="mt-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-900">
              {viewMode === 'analysis' ? 'File Analysis Details' : 'File Content'}
            </h3>
            <div className="flex items-center space-x-2">
              {viewMode === 'analysis' && selectedFile.status === 'ANALYZED' && (
                <>
                  {!isEditing && !isAiEditing ? (
                    <>
                      <Button variant="secondary" size="sm" onClick={handleStartEdit}>
                        Manual Edit
                      </Button>
                      <Button variant="secondary" size="sm" onClick={handleStartAiEdit}>
                        AI Edit
                      </Button>
                    </>
                  ) : (
                    <>
                      <Button variant="secondary" size="sm" onClick={handleCancelEdit}>
                        Cancel
                      </Button>
                      {isEditing && (
                        <Button size="sm" onClick={handleSaveEdit}>
                          Save
                        </Button>
                      )}
                    </>
                  )}
                </>
              )}
              <button
                onClick={() => { 
                  setSelectedFile(null); 
                  setIsEditing(false); 
                  setIsAiEditing(false);
                }}
                className="text-gray-500 hover:text-gray-700 text-sm"
              >
                ×
              </button>
            </div>
          </div>

          {/* AI Refinement Section - Only show when AI Edit is clicked */}
          {isAiEditing && (
            <div className="mb-3 bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-3">
              <h4 className="text-xs font-medium text-gray-900 mb-1.5">AI-Assisted Refinement</h4>
              <p className="text-xs text-gray-600 mb-2">
                Describe what you want to improve, and AI will refine the entire analysis (patterns, parsing strategy, sample data).
              </p>
              <div className="space-y-2">
                <textarea
                  value={aiRefinePrompt}
                  onChange={(e) => setAiRefinePrompt(e.target.value)}
                  className="w-full h-20 text-xs border border-gray-300 rounded-md p-2.5 focus:outline-none focus:ring-2 focus:ring-purple-500/50 bg-white"
                  placeholder="Example: 'Focus on error patterns only' or 'Improve timing violation detection' or 'Extract more detailed values'"
                />
                <div className="flex justify-end">
                  <Button 
                    onClick={handleAiRefine}
                    disabled={isRefining || !aiRefinePrompt.trim()}
                    size="sm"
                  >
                    {isRefining ? 'Refining...' : 'Refine with AI'}
                  </Button>
                </div>
              </div>
            </div>
          )}

          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="font-medium text-gray-700">File Name:</span>
                <span className="ml-2 text-gray-900 font-mono">{selectedFile.filename}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">File Type:</span>
                <span className="ml-2 text-gray-900">{selectedFile.fileType}</span>
              </div>
              <div className="col-span-2">
                <span className="font-medium text-gray-700">Full Path:</span>
                <div className="mt-1 bg-gray-50 rounded px-3 py-1.5 font-mono text-xs text-gray-700 break-all">
                  {selectedFile.fullPath}
                </div>
              </div>
            </div>

            {viewMode === 'analysis' ? (
              <div className="space-y-3">
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-1.5">Analysis Status:</h4>
                  {selectedFile.status === 'ANALYZED' ? (
                    <div className="inline-flex items-center px-2.5 py-0.5 bg-green-100 text-green-700 rounded-md text-xs font-medium">
                      Analyzed
                    </div>
                  ) : (
                    <StatusBadge status={selectedFile.status} />
                  )}
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-1.5">File Statistics:</h4>
                  <div className="bg-gray-50 rounded-lg p-3 space-y-1.5 text-xs">
                    <div>Lines: <span className="font-mono">{selectedFile.lines}</span></div>
                    <div>Size: <span className="font-mono">{selectedFile.size}</span></div>
                  </div>
                </div>

                {/* Template Type Tabs */}
                {selectedFile.status === 'ANALYZED' && (
                  <div className="border-b border-gray-200">
                    <div className="flex space-x-1 -mb-px">
                      <button
                        onClick={() => setSelectedTypeTab('type1')}
                        className={`px-3 py-1.5 text-xs font-medium rounded-t-lg transition-colors ${
                          selectedTypeTab === 'type1'
                            ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-600'
                            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                        }`}
                      >
                        Type 1: Boolean Check
                      </button>
                      <button
                        onClick={() => setSelectedTypeTab('type2')}
                        className={`px-3 py-1.5 text-xs font-medium rounded-t-lg transition-colors ${
                          selectedTypeTab === 'type2'
                            ? 'bg-green-50 text-green-700 border-b-2 border-green-600'
                            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                        }`}
                      >
                        Type 2: Value Check
                      </button>
                      <button
                        onClick={() => setSelectedTypeTab('type3')}
                        className={`px-3 py-1.5 text-xs font-medium rounded-t-lg transition-colors ${
                          selectedTypeTab === 'type3'
                            ? 'bg-purple-50 text-purple-700 border-b-2 border-purple-600'
                            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                        }`}
                      >
                        Type 3: Value + Waiver
                      </button>
                      <button
                        onClick={() => setSelectedTypeTab('type4')}
                        className={`px-3 py-1.5 text-xs font-medium rounded-t-lg transition-colors ${
                          selectedTypeTab === 'type4'
                            ? 'bg-orange-50 text-orange-700 border-b-2 border-orange-600'
                            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                        }`}
                      >
                        Type 4: Boolean + Waiver
                      </button>
                    </div>
                  </div>
                )}

                {/* Display selected type's analysis */}
                {(() => {
                  // Map tab name to data key
                  const typeDataKeyMap = {
                    'type1': 'type1_boolean_check',
                    'type2': 'type2_value_check',
                    'type3': 'type3_value_with_waiver',
                    'type4': 'type4_boolean_with_waiver'
                  }
                  const typeKey = typeDataKeyMap[selectedTypeTab]
                  const currentTypeData = selectedFile[typeKey] || {}
                  
                  return (
                    <>
                      {/* Output Format moved to Step3 - no longer displayed here */}

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <h4 className="text-sm font-medium text-gray-900">Detected Patterns:</h4>
                    {isEditing && (
                      <span className="text-xs text-gray-500">One pattern per line</span>
                    )}
                    {!isEditing && selectedTypeTab !== 'type1' && (
                      <span className="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded">
                        ✓ Inherited from Type 1
                      </span>
                    )}
                  </div>
                  {isEditing ? (
                    <textarea
                      value={editPatterns}
                      onChange={(e) => setEditPatterns(e.target.value)}
                      className="w-full h-36 text-xs font-mono border border-gray-300 rounded-md p-2.5 focus:outline-none focus:ring-2 focus:ring-primary/50"
                      placeholder="Pattern 1: Description&#10;  Regex: ^pattern$&#10;  Example: sample line"
                    />
                  ) : currentTypeData.patterns && currentTypeData.patterns.length > 0 ? (
                    <div className="space-y-1.5">
                      {currentTypeData.patterns.map((pattern, idx) => (
                        <div key={idx} className="bg-gray-50 border border-gray-200 rounded-lg p-2.5">
                          <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                            {pattern}
                          </pre>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-xs text-gray-500 italic bg-gray-50 rounded-lg p-3">
                      No patterns detected
                    </div>
                  )}
                </div>

                {/* Pattern Items Usage (Type 2/3) */}
                {currentTypeData.patternItemsUsage && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-1.5">
                      📋 Pattern Items Usage
                      <span className="ml-2 text-xs font-normal text-blue-600">(Type 2/3 specific)</span>
                    </h4>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <div className="space-y-1.5 text-xs text-gray-700">
                        {currentTypeData.patternItemsUsage.compared_values && (
                          <div>
                            <span className="font-semibold">Compared Values:</span> {currentTypeData.patternItemsUsage.compared_values}
                          </div>
                        )}
                        {currentTypeData.patternItemsUsage.logic && (
                          <div>
                            <span className="font-semibold">Logic:</span> {currentTypeData.patternItemsUsage.logic}
                          </div>
                        )}
                        {currentTypeData.patternItemsUsage.found_items && (
                          <div>
                            <span className="font-semibold">Found Items:</span> {currentTypeData.patternItemsUsage.found_items}
                          </div>
                        )}
                        {currentTypeData.patternItemsUsage.missing_items && (
                          <div>
                            <span className="font-semibold">Missing Items:</span> {currentTypeData.patternItemsUsage.missing_items}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Waive Items Usage (Type 3/4) */}
                {currentTypeData.waiveItemsUsage && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-1.5">
                      🛡️ Waive Items Usage
                      <span className="ml-2 text-xs font-normal text-purple-600">(Type 3/4 specific)</span>
                    </h4>
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                      <div className="space-y-1.5 text-xs text-gray-700">
                        {currentTypeData.waiveItemsUsage.matched_objects && (
                          <div>
                            <span className="font-semibold">Matched Objects:</span> {currentTypeData.waiveItemsUsage.matched_objects}
                          </div>
                        )}
                        {currentTypeData.waiveItemsUsage.logic && (
                          <div>
                            <span className="font-semibold">Logic:</span> {currentTypeData.waiveItemsUsage.logic}
                          </div>
                        )}
                        {currentTypeData.waiveItemsUsage.waived_items && (
                          <div>
                            <span className="font-semibold">Waived Items:</span> {currentTypeData.waiveItemsUsage.waived_items}
                          </div>
                        )}
                        {currentTypeData.waiveItemsUsage.unwaived_items && (
                          <div>
                            <span className="font-semibold">Unwaived Items:</span> {currentTypeData.waiveItemsUsage.unwaived_items}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-1.5">Parsing Strategy:</h4>
                  {isEditing ? (
                    <textarea
                      value={editParsingStrategy}
                      onChange={(e) => setEditParsingStrategy(e.target.value)}
                      className="w-full h-24 text-xs border border-gray-300 rounded-md p-2.5 focus:outline-none focus:ring-2 focus:ring-primary/50"
                      placeholder="Describe the parsing strategy..."
                    />
                  ) : (
                    <div className="bg-gray-50 border border-gray-200 rounded-md p-3">
                      {currentTypeData.parsingStrategy ? (
                        <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                          {currentTypeData.parsingStrategy}
                        </pre>
                      ) : (
                        <span className="text-xs text-gray-500 italic">No parsing strategy defined</span>
                      )}
                    </div>
                  )}
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-1.5">Sample Data:</h4>
                  {isEditing ? (
                    <textarea
                      value={editSampleData}
                      onChange={(e) => setEditSampleData(e.target.value)}
                      className="w-full h-32 text-xs font-mono border border-gray-300 rounded-md p-2.5 focus:outline-none focus:ring-2 focus:ring-primary/50"
                      placeholder="Sample data from the file..."
                    />
                  ) : (
                    <div className="bg-gray-50 rounded-md p-3">
                      <pre className="text-xs text-gray-700 font-mono whitespace-pre-wrap">
                        {currentTypeData.sampleData}
                      </pre>
                    </div>
                  )}
                </div>
                    </>
                  )
                })()}

                {selectedFile.templateRecommendations && selectedFile.templateRecommendations.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-1.5">Template Recommendations:</h4>
                    <ul className="bg-purple-50 border border-purple-200 rounded-md p-3 space-y-1">
                      {selectedFile.templateRecommendations.map((rec, idx) => (
                        <li key={idx} className="text-xs text-gray-700">• {rec}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {selectedFile.aiRawResponse && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-1.5">AI Raw Response (Debug):</h4>
                    <details className="bg-gray-50 rounded-md p-3">
                      <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-900">
                        Click to expand raw AI response
                      </summary>
                      <pre className="mt-2 text-xs text-gray-600 font-mono whitespace-pre-wrap border-t border-gray-200 pt-2">
                        {selectedFile.aiRawResponse}
                      </pre>
                    </details>
                  </div>
                )}
              </div>
            ) : (
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-1.5">File Content:</h4>
                {loadingContent ? (
                  <div className="bg-gray-50 rounded-md p-6 text-center">
                    <div className="animate-spin w-5 h-5 border-2 border-primary border-t-transparent rounded-full mx-auto mb-2"></div>
                    <span className="text-xs text-gray-600">Loading file content...</span>
                  </div>
                ) : contentError ? (
                  <div className="bg-red-50 border border-red-200 rounded-md p-3">
                    <div className="text-red-700 text-sm font-medium">Error loading file</div>
                    <div className="text-xs text-red-600 mt-1">{contentError}</div>
                  </div>
                ) : (
                  <div className="bg-gray-50 rounded-md p-3">
                    {contentTruncated && (
                      <div className="mb-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
                        File truncated: Showing {contentShownLines} of {contentTotalLines} lines
                      </div>
                    )}
                    <div className="bg-white border border-gray-200 rounded p-2.5 max-h-96 overflow-auto">
                      <pre className="text-xs font-mono text-gray-800 whitespace-pre-wrap">
                        {fileContent || 'No content available'}
                      </pre>
                    </div>
                    <div className="mt-2 text-xs text-gray-600">
                      Tip: Open in editor for better viewing:
                      <code className="ml-2 text-xs bg-gray-100 px-2 py-0.5 rounded text-gray-800">
                        code "{selectedFile.fullPath}"
                      </code>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  )
}
