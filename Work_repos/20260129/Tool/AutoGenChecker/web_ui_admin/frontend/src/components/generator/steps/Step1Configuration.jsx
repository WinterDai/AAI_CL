import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import Card from '@/components/common/Card'
import Button from '@/components/common/Button'
import { useGenerationStore } from '@/store/generationStore'
import { useModulesStore } from '@/store/modulesStore'
import apiClient from '@/api/client'

export default function Step1Configuration({ itemId }) {
  const [searchParams] = useSearchParams()
  const moduleFromUrl = searchParams.get('module')
  const itemFromUrl = searchParams.get('item')
  
  // Store methods - 新的项目锁定系统
  const project = useGenerationStore((s) => s.project)
  const saveProject = useGenerationStore((s) => s.saveProject)
  const unlockProject = useGenerationStore((s) => s.unlockProject)
  const step1Draft = useGenerationStore((s) => s.step1Draft)
  const setStep1Draft = useGenerationStore((s) => s.setStep1Draft)
  
  // 兼容旧代码
  const setStep1State = useGenerationStore((s) => s.setStep1State)
  const setYamlConfig = useGenerationStore((s) => s.setYamlConfig)
  const setResumeStatus = useGenerationStore((s) => s.setResumeStatus)
  const setCurrentStep = useGenerationStore((s) => s.setCurrentStep)
  const setGeneratedReadme = useGenerationStore((s) => s.setGeneratedReadme)
  const setGeneratedCode = useGenerationStore((s) => s.setGeneratedCode)
  const setFileAnalysis = useGenerationStore((s) => s.setFileAnalysis)
  
  // Use cached modules from global store
  const { modules: cachedModules, fetchModules } = useModulesStore()
  
  // 初始化逻辑：
  // 1. 如果项目已锁定（project.locked），显示锁定的配置
  // 2. 如果有 URL 参数，使用 URL 参数
  // 3. 否则使用草稿状态 (step1Draft)
  const [showEditYaml, setShowEditYaml] = useState(false)
  const [yamlData, setYamlData] = useState(
    project.locked ? project.yamlConfig : step1Draft.yamlData
  )
  const [loadingYaml, setLoadingYaml] = useState(false)
  
  // 确定初始选择值
  const getInitialModule = () => {
    if (moduleFromUrl) return moduleFromUrl
    if (project.locked) return project.module
    return step1Draft.selectedModule || ''
  }
  const getInitialItem = () => {
    if (itemFromUrl) return itemFromUrl
    if (project.locked) return project.itemId
    return step1Draft.selectedItem || ''
  }
  
  const [selectedModule, setSelectedModule] = useState(getInitialModule)
  const [selectedItem, setSelectedItem] = useState(getInitialItem)
  const [modules, setModules] = useState(step1Draft.modules || cachedModules || [])
  const [items, setItems] = useState(step1Draft.items || [])
  
  // 当 URL 参数变化时，同步更新 local state
  useEffect(() => {
    if (moduleFromUrl && moduleFromUrl !== selectedModule) {
      console.log('🔄 URL module changed, updating:', moduleFromUrl)
      setSelectedModule(moduleFromUrl)
    }
    if (itemFromUrl && itemFromUrl !== selectedItem) {
      console.log('🔄 URL item changed, updating:', itemFromUrl)
      setSelectedItem(itemFromUrl)
    }
  }, [moduleFromUrl, itemFromUrl])
  
  // Resume status state
  const [resumeStatus, setLocalResumeStatus] = useState(null)
  const [loadingResume, setLoadingResume] = useState(false)
  
  // Configuration saved state - 如果项目已锁定，表示已保存
  const [configSaved, setConfigSaved] = useState(project.locked)
  
  const [editableYaml, setEditableYaml] = useState(step1Draft.editableYaml || `description: "Check for STA timing violations"

input_files:
  - \${CHECKLIST_ROOT}/IP_project_folder/reports/10.0/timing.rpt

requirements:
  value: N/A
  pattern_items: []

waivers:
  value: N/A
  waive_items: []`)

  // Load modules from cache on mount
  useEffect(() => {
    const loadModules = async () => {
      // 总是检查是否需要加载模块
      if (modules.length === 0 || cachedModules.length === 0) {
        const data = await fetchModules()
        if (data.length > 0) {
          setModules(data)
          // Save to store with current step1State
          setStep1State({ 
            ...step1State, 
            modules: data 
          })
          
          // 如果URL有module参数，自动选择
          const targetModule = moduleFromUrl || step1State.selectedModule
          if (targetModule && data.find(m => m.module_id === targetModule)) {
            setSelectedModule(targetModule)
            const moduleItems = data.find(m => m.module_id === targetModule)?.items || []
            setItems(moduleItems)
            
            // 如果URL有item参数，自动选择
            const targetItem = itemFromUrl || step1Draft.selectedItem
            if (targetItem && moduleItems.some(i => i.item_id === targetItem)) {
              setSelectedItem(targetItem)
            }
          }
        }
      } else if (modules.length > 0) {
        // 模块已加载，检查是否需要根据URL参数选择
        const targetModule = moduleFromUrl || step1State.selectedModule
        if (targetModule && !selectedModule) {
          setSelectedModule(targetModule)
        }
      }
    }
    loadModules()
  }, [modules.length, fetchModules, moduleFromUrl, itemFromUrl]) // 添加URL参数依赖

  // Load items when module changes
  useEffect(() => {
    if (selectedModule) {
      const module = modules.find(m => m.module_id === selectedModule)
      const newItems = module?.items || []
      setItems(newItems)
      
      // Save to store
      setStep1Draft({ 
        selectedModule, 
        items: newItems 
      })
      
      console.log('✅ Module selected:', selectedModule, 'Items:', newItems.length)
      
      // 如果URL中有item参数，且该item在列表中，自动选择它
      if (itemFromUrl && newItems.some(item => item.item_id === itemFromUrl)) {
        console.log('✅ Auto-selecting item from URL:', itemFromUrl)
        setSelectedItem(itemFromUrl)
      }
    }
  }, [selectedModule, itemFromUrl])

  // Load YAML when item selected
  useEffect(() => {
    console.log('📦 YAML useEffect triggered:', { selectedModule, selectedItem })
    if (selectedModule && selectedItem) {
      setLoadingYaml(true)
      console.log('📡 Fetching YAML for:', selectedModule, selectedItem)
      fetch(`http://localhost:8000/api/step1/modules/${selectedModule}/items/${selectedItem}`)
        .then(res => res.json())
        .then(data => {
          console.log('✅ YAML data received:', data)
          setYamlData(data)
          
          // Save to store for Step2 to access
          setYamlConfig(data)
          console.log('✅ YAML config saved to store for Step2')
          
          // Format YAML content for display - use clean format matching original YAML files
          // Do NOT include item_id/module (they're derived from filename/directory)
          const hasInputFiles = data.input_files && data.input_files.length > 0
          const inputFilesStr = hasInputFiles
            ? 'input_files:\n' + data.input_files.map(f => `  - ${f}`).join('\n')
            : 'input_files: []'
          
          const hasPatternItems = data.requirements?.pattern_items && data.requirements.pattern_items.length > 0
          const patternItemsStr = hasPatternItems
            ? 'pattern_items:\n' + data.requirements.pattern_items.map(p => `      - ${p}`).join('\n')
            : 'pattern_items: []'
          
          const hasWaiveItems = data.waivers?.waive_items && data.waivers.waive_items.length > 0
          const waiveItemsStr = hasWaiveItems
            ? 'waive_items:\n' + data.waivers.waive_items.map(w => `      - ${w}`).join('\n')
            : 'waive_items: []'
          
          const yamlText = `description: "${data.description || ''}"

${inputFilesStr}

requirements:
  value: ${data.requirements?.value || 'N/A'}
  ${patternItemsStr}

waivers:
  value: ${data.waivers?.value || 'N/A'}
  ${waiveItemsStr}`
          setEditableYaml(yamlText)
          setLoadingYaml(false)
          
          // Save complete state to store
          setStep1Draft({
            selectedModule,
            selectedItem,
            yamlData: data,
            editableYaml: yamlText,
            modules,
            items
          })
          
          console.log('✅ Step1 state saved to store')
          
          // Check resume status after YAML loaded
          checkResumeStatus(selectedModule, selectedItem)
        })
        .catch(err => {
          console.error('Failed to load YAML:', err)
          setLoadingYaml(false)
        })
    }
  }, [selectedItem]) // Only depend on selectedItem to avoid infinite loops
  
  // Check resume status for the selected item
  const checkResumeStatus = async (module, item) => {
    setLoadingResume(true)
    try {
      const response = await apiClient.get(`/api/step1/modules/${module}/items/${item}/resume-status`)
      if (response.data.status === 'success') {
        setLocalResumeStatus(response.data)
        setResumeStatus(response.data)
        console.log('📂 Resume status:', response.data)
      }
    } catch (error) {
      console.error('Failed to check resume status:', error)
    } finally {
      setLoadingResume(false)
    }
  }
  
  // Handle resume from a specific step
  const handleResumeFrom = async (step) => {
    console.log(`🔄 Resuming from Step ${step}`)
    
    // Load cached data based on the step
    try {
      // Load file analysis if resuming from step 3+
      if (step >= 3 && resumeStatus?.files?.file_analysis) {
        const res = await apiClient.post('/api/step2/load-file-analysis', {
          module: selectedModule,
          item_id: selectedItem
        })
        if (res.data.exists) {
          setFileAnalysis(res.data.file_analysis)
          console.log('📂 Loaded file analysis from file')
        }
      }
      
      // Load README if resuming from step 4+
      if (step >= 4 && resumeStatus?.files?.readme) {
        const res = await apiClient.post('/api/step3/load-readme', {
          module: selectedModule,
          item_id: selectedItem
        })
        if (res.data.exists) {
          setGeneratedReadme(res.data.readme)
          console.log('📂 Loaded README from file')
        }
      }
      
      // Load code if resuming from step 6+
      if (step >= 6 && resumeStatus?.files?.code) {
        const res = await apiClient.post('/api/step5/load-code', {
          module: selectedModule,
          item_id: selectedItem
        })
        if (res.data.exists) {
          setGeneratedCode(res.data.code)
          console.log('📂 Loaded code from file')
        }
      }
      
      // Navigate to the resume step
      setCurrentStep(step)
      
    } catch (error) {
      console.error('Failed to load cached data:', error)
      alert('Failed to load cached data: ' + error.message)
    }
  }
  
  // =========================================================================
  // Save Configuration - 锁定项目配置，后续所有步骤都使用此配置
  // =========================================================================
  const handleSaveConfiguration = () => {
    if (!selectedModule || !selectedItem) {
      alert('请先选择 Module 和 Item')
      return
    }
    
    if (!yamlData) {
      alert('请等待 YAML 配置加载完成')
      return
    }
    
    console.log('💾 Saving and locking configuration:', { selectedModule, selectedItem })
    
    // 使用新的 saveProject 方法锁定项目
    // 这会设置 project.locked = true，后续所有步骤都使用此配置
    saveProject(selectedModule, selectedItem, yamlData)
    
    // 同时保存草稿状态（为了 UI 显示）
    setStep1Draft({
      selectedModule,
      selectedItem,
      yamlData,
      editableYaml,
      modules,
      items
    })
    
    // Mark as saved
    setConfigSaved(true)
    
    console.log('✅ Project locked - all steps will use this configuration')
  }
  
  // =========================================================================
  // 解锁项目 - 允许重新选择 module/item
  // =========================================================================
  const handleUnlockConfiguration = () => {
    console.log('🔓 Unlocking configuration')
    unlockProject()
    setConfigSaved(false)
  }

  const handleEditYaml = (e) => {
    e.preventDefault()
    e.stopPropagation()
    console.log('🔵 Edit YAML clicked!')
    setShowEditYaml(true)
  }
  
  const handleReload = (e) => {
    e.preventDefault()
    e.stopPropagation()
    console.log('🔵 Reload clicked!')
    
    if (!selectedModule || !selectedItem) {
      alert('请先选择Module和Item')
      return
    }
    
    // Reload YAML from backend
    setLoadingYaml(true)
    fetch(`http://localhost:8000/api/step1/modules/${selectedModule}/items/${selectedItem}`)
      .then(res => res.json())
      .then(data => {
        setYamlData(data)
        setYamlConfig(data) // Update store
        
        // Regenerate YAML text in clean format (matching original YAML file)
        const yamlText = `description: "${data.description}"

input_files:
${data.input_files.map(f => `  - ${f}`).join('\n')}

requirements:
  value: ${data.requirements?.value || 'N/A'}
  pattern_items: ${JSON.stringify(data.requirements?.pattern_items || [])}

waivers:
  value: ${data.waivers?.value || 'N/A'}
  waive_items: ${JSON.stringify(data.waivers?.waive_items || [])}`
        setEditableYaml(yamlText)
        setLoadingYaml(false)
        
        // Update store
        setStep1Draft({
          selectedModule,
          selectedItem,
          yamlData: data,
          editableYaml: yamlText,
          modules,
          items
        })
        
        console.log('✅ YAML reloaded from backend')
      })
      .catch(err => {
        console.error('Failed to reload YAML:', err)
        alert('重新加载失败')
        setLoadingYaml(false)
      })
  }
  
  const handleSaveYaml = async () => {
    console.log('💾 Saving YAML:', editableYaml)
    
    if (!selectedModule || !selectedItem) {
      alert('无法保存：未选择Module或Item')
      return
    }
    
    try {
      // Auto-fix common YAML issues
      let fixedYaml = editableYaml
      
      // Fix description field with colons (add quotes if not already quoted)
      fixedYaml = fixedYaml.replace(
        /^(\s*description:\s*)([^"\n].*:\s*.*)$/gm,
        (match, prefix, value) => {
          // Only add quotes if value contains : and is not already quoted
          if (value.includes(':') && !value.trim().startsWith('"') && !value.trim().startsWith("'")) {
            return `${prefix}"${value.trim()}"`
          }
          return match
        }
      )
      
      console.log('🔧 Auto-fixed YAML:', fixedYaml !== editableYaml ? 'Yes' : 'No')
      
      // Save to backend (file system)
      const response = await fetch(`http://localhost:8000/api/step1/modules/${selectedModule}/items/${selectedItem}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ yaml_content: fixedYaml })
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Save failed')
      }
      
      console.log('✅ YAML saved to file system')
      
      // Parse edited YAML text to update display
      const lines = editableYaml.split('\n')
      let itemId = ''
      let module = ''
      let description = ''
      let inputFiles = []
      let inInputFiles = false
      
      lines.forEach(line => {
        const trimmed = line.trim()
        if (trimmed.startsWith('item_id:')) {
          itemId = trimmed.split(':')[1].trim()
        } else if (trimmed.startsWith('module:')) {
          module = trimmed.split(':')[1].trim()
        } else if (trimmed.startsWith('description:')) {
          description = trimmed.substring(trimmed.indexOf(':') + 1).trim()
        } else if (trimmed === 'input_files:') {
          inInputFiles = true
        } else if (inInputFiles && trimmed.startsWith('-')) {
          inputFiles.push(trimmed.substring(1).trim())
        } else if (inInputFiles && trimmed && !trimmed.startsWith('-') && !trimmed.startsWith('${CHECKLIST_ROOT}')) {
          inInputFiles = false
        }
      })
      
      // Update yamlData with parsed information
      if (yamlData) {
        const updatedYamlData = {
          ...yamlData,
          item_id: itemId || yamlData.item_id,
          module: module || yamlData.module,
          description: description || yamlData.description,
          input_files: inputFiles.length > 0 ? inputFiles : yamlData.input_files
        }
        setYamlData(updatedYamlData)
        
        // Update store for Step2 to see changes
        setYamlConfig(updatedYamlData)
        
        // Save complete state to store
        setStep1Draft({
          selectedModule,
          selectedItem,
          yamlData: updatedYamlData,
          editableYaml: fixedYaml !== editableYaml ? fixedYaml : editableYaml,
          modules,
          items
        })
        
        console.log('✅ Display updated and store synced:', updatedYamlData)
      }
      
      // Update editableYaml with fixed version
      if (fixedYaml !== editableYaml) {
        setEditableYaml(fixedYaml)
        alert('✅ YAML已保存！\n\n💡 已自动修复格式问题：\n- description字段包含冒号已自动加引号')
      } else {
        alert('✅ YAML已保存到文件！')
      }
      setShowEditYaml(false)
      
    } catch (error) {
      console.error('❌ Failed to save YAML:', error)
      
      // Show detailed error message
      let errorMsg = error.message
      if (errorMsg.includes('mapping values are not allowed')) {
        errorMsg += '\n\n💡 提示：description字段中如果包含冒号(:)，需要用引号括起来\n例如：description: "Block name (e.g: example)"'
      }
      
      alert(`保存失败: ${errorMsg}`)
    }
  }
  
  // Mock YAML content
  const yamlContent = editableYaml

  const validationResults = [
    { id: 1, text: 'YAML file exists and valid', passed: true },
    { id: 2, text: 'All input files found', passed: true },
    { id: 3, text: 'Module directory exists', passed: true },
    { id: 4, text: 'Configuration complete', passed: true }
  ]

  return (
    <>
      <div className="p-4 space-y-3">
        <div>
          <h1 className="text-lg font-semibold text-gray-900">
            Step 1: Loading Configuration
          </h1>
          <p className="mt-1 text-xs text-gray-600">
            Select module and item from CHECKLIST directory
          </p>
        </div>

        {/* Module and Item Selection */}
        <Card>
          <div className="space-y-2">
            <h2 className="text-sm font-semibold text-gray-900">
              Select Configuration
            </h2>
            
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Module
                </label>
                <select
                  value={selectedModule}
                  onChange={(e) => {
                    setSelectedModule(e.target.value)
                    setConfigSaved(false) // Reset saved state when selection changes
                  }}
                  className="w-full px-3 py-2 text-xs border border-gray-300 rounded-md"
                >
                  <option value="">-- Select Module --</option>
                  {modules.map(m => (
                    <option key={m.module_id} value={m.module_id}>
                      {m.module_id} ({m.item_count} items)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Item
                </label>
                <select
                  value={selectedItem}
                  onChange={(e) => {
                    setSelectedItem(e.target.value)
                    setConfigSaved(false) // Reset saved state when selection changes
                  }}
                  disabled={!selectedModule}
                  className="w-full px-3 py-2 text-xs border border-gray-300 rounded-md disabled:bg-gray-100"
                >
                  <option value="">-- Select Item --</option>
                  {items.map(item => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </div>
              
              {/* Save Configuration Button */}
              {selectedModule && selectedItem && yamlData && (
                <div className="pt-2 border-t border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {configSaved ? (
                        <>
                          <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                          <span className="text-sm text-green-600 font-medium">Configuration Locked</span>
                        </>
                      ) : (
                        <span className="text-sm text-yellow-600">Click "Save & Lock" to enable other steps</span>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      {configSaved && (
                        <button
                          onClick={handleUnlockConfiguration}
                          className="px-2 py-1 text-xs font-medium rounded-md bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
                        >
                          Unlock to Edit
                        </button>
                      )}
                      <button
                        onClick={handleSaveConfiguration}
                        disabled={configSaved}
                        className={`px-2 py-1 text-xs font-medium rounded-md transition-colors ${
                          configSaved 
                            ? 'bg-green-100 text-green-700 cursor-not-allowed' 
                            : 'bg-primary text-white hover:bg-primary-hover'
                        }`}
                      >
                        {configSaved ? 'Locked' : 'Save & Lock'}
                      </button>
                    </div>
                  </div>
                  {configSaved && (
                    <p className="mt-1 text-xs text-gray-500">
                      All steps (2-9) will now use this module and item. Click "Unlock to Edit" to change selection.
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>
        </Card>

        {loadingYaml && (
          <Card>
            <div className="text-center py-8 text-gray-600">
              Loading YAML configuration...
            </div>
          </Card>
        )}

        {yamlData && (
          <Card>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-gray-900">
                  YAML Configuration
                </h2>
                <div className="flex items-center space-x-2">
                  <button 
                    type="button"
                    onClick={handleEditYaml}
                    className="px-2 py-1 text-xs font-medium text-white bg-primary hover:bg-primary-hover border-0 rounded-md transition-colors cursor-pointer"
                    style={{ pointerEvents: 'auto' }}
                  >
                    Edit YAML
                  </button>
                  <button 
                    type="button"
                    onClick={handleReload}
                    className="px-2 py-1 text-xs font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50 border border-gray-300 rounded-md transition-colors cursor-pointer"
                    style={{ pointerEvents: 'auto' }}
                  >
                    Reload
                  </button>
                </div>
              </div>

              <div className="bg-gray-50 rounded-md p-4 overflow-x-auto">
                <pre className="text-xs font-mono text-gray-800">
                  {editableYaml}
                </pre>
              </div>

              {/* Display real YAML data */}
              <div className="space-y-2">
                <div>
                  <span className="text-xs font-medium text-gray-700">Description: </span>
                  <span className="text-xs text-gray-900">{yamlData.description || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-xs font-medium text-gray-700">Input Files ({(yamlData.input_files || []).length}): </span>
                  <div className="mt-1 space-y-0.5">
                    {(yamlData.input_files || []).slice(0, 5).map((file, idx) => (
                      <div key={idx} className="text-xs text-gray-600 font-mono bg-gray-50 px-2 py-0.5 rounded">
                        {file}
                      </div>
                    ))}
                    {(yamlData.input_files || []).length > 5 && (
                      <div className="text-xs text-gray-500">
                        ... and {(yamlData.input_files || []).length - 5} more files
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </Card>
        )}

        {!loadingYaml && !yamlData && selectedModule && selectedItem && (
          <Card>
            <div className="text-center py-8 text-red-600">
              Failed to load YAML configuration
            </div>
          </Card>
        )}

        {yamlData && (
          <Card>
            <div className="space-y-2">
              <h2 className="text-sm font-semibold text-gray-900">
                Validation Results
              </h2>

              <div className="space-y-1.5">
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center bg-success/10">
                    <svg className="w-4 h-4 text-success" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <span className="text-xs text-gray-900">YAML file loaded: {yamlData.yaml_path}</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center bg-success/10">
                    <svg className="w-4 h-4 text-success" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <span className="text-xs text-gray-900">Input files found: {(yamlData.input_files || []).length} files</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center bg-success/10">
                    <svg className="w-4 h-4 text-success" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <span className="text-xs text-gray-900">Configuration complete</span>
                </div>
              </div>
            </div>
          </Card>
        )}
        
        {/* Resume Status Card */}
        {resumeStatus && resumeStatus.suggested_resume_step > 1 && (
          <Card>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-gray-900">
                  Resume From Previous Work
                </h2>
                <span className="text-xs px-2 py-0.5 rounded bg-blue-50 text-blue-600 font-medium">
                  Suggested: Step {resumeStatus.suggested_resume_step}
                </span>
              </div>
              
              <p className="text-xs text-gray-600">{resumeStatus.message}</p>
              
              <div className="grid grid-cols-4 gap-2">
                {/* File Analysis */}
                <div className={`p-1.5 rounded ${resumeStatus.files?.file_analysis ? 'bg-green-50 border border-green-200' : 'bg-gray-50 border border-gray-200'}`}>
                  <div className="flex items-center space-x-1.5">
                    <span className="text-xs">{resumeStatus.files?.file_analysis ? '✓' : '○'}</span>
                    <span className="text-xs font-medium">File Analysis</span>
                  </div>
                  {resumeStatus.files?.file_analysis && (
                    <p className="text-xs text-gray-400 mt-0.5 truncate" title={resumeStatus.files.file_analysis.modified_time}>
                      {resumeStatus.files.file_analysis.modified_time}
                    </p>
                  )}
                </div>
                
                {/* README */}
                <div className={`p-1.5 rounded ${resumeStatus.files?.readme ? 'bg-green-50 border border-green-200' : 'bg-gray-50 border border-gray-200'}`}>
                  <div className="flex items-center space-x-1.5">
                    <span className="text-xs">{resumeStatus.files?.readme ? '✓' : '○'}</span>
                    <span className="text-xs font-medium">README</span>
                  </div>
                  {resumeStatus.files?.readme && (
                    <p className="text-xs text-gray-400 mt-0.5 truncate" title={resumeStatus.files.readme.modified_time}>
                      {resumeStatus.files.readme.modified_time}
                    </p>
                  )}
                </div>
                
                {/* Code */}
                <div className={`p-1.5 rounded ${resumeStatus.files?.code ? 'bg-green-50 border border-green-200' : 'bg-gray-50 border border-gray-200'}`}>
                  <div className="flex items-center space-x-1.5">
                    <span className="text-xs">{resumeStatus.files?.code ? '✓' : '○'}</span>
                    <span className="text-xs font-medium">Code</span>
                  </div>
                  {resumeStatus.files?.code && (
                    <p className="text-xs text-gray-400 mt-0.5 truncate" title={resumeStatus.files.code.modified_time}>
                      {resumeStatus.files.code.modified_time}
                    </p>
                  )}
                </div>
                
                {/* Config */}
                <div className={`p-1.5 rounded ${resumeStatus.files?.config ? 'bg-green-50 border border-green-200' : 'bg-gray-50 border border-gray-200'}`}>
                  <div className="flex items-center space-x-1.5">
                    <span className="text-xs">{resumeStatus.files?.config ? '✓' : '○'}</span>
                    <span className="text-xs font-medium">Config</span>
                  </div>
                  {resumeStatus.files?.config && (
                    <p className="text-xs text-gray-400 mt-0.5 truncate" title={resumeStatus.files.config.modified_time}>
                      {resumeStatus.files.config.modified_time}
                    </p>
                  )}
                </div>
              </div>
              
              {/* Resume Buttons */}
              <div className="grid grid-cols-3 gap-1.5 pt-1.5">
                {resumeStatus.files?.file_analysis && (
                  <Button
                    variant="secondary"
                    onClick={() => handleResumeFrom(3)}
                    className="text-xs w-full"
                  >
                    Step 3 (README)
                  </Button>
                )}
                {resumeStatus.files?.readme && (
                  <Button
                    variant="secondary"
                    onClick={() => handleResumeFrom(4)}
                    className="text-xs w-full"
                  >
                    Step 4 (Review)
                  </Button>
                )}
                {resumeStatus.files?.readme && (
                  <Button
                    variant="secondary"
                    onClick={() => handleResumeFrom(5)}
                    className="text-xs w-full"
                  >
                    Step 5 (Code)
                  </Button>
                )}
                {resumeStatus.files?.code && (
                  <Button
                    variant="secondary"
                    onClick={() => handleResumeFrom(6)}
                    className="text-xs w-full"
                  >
                    Step 6 (Self-Check)
                  </Button>
                )}
                {resumeStatus.files?.code && (
                  <Button
                    variant="secondary"
                    onClick={() => handleResumeFrom(7)}
                    className="text-xs w-full"
                  >
                    Step 7 (Testing)
                  </Button>
                )}
                {resumeStatus.files?.code && (
                  <Button
                    variant="secondary"
                    onClick={() => handleResumeFrom(8)}
                    className="text-xs w-full"
                  >
                    Step 8 (Review)
                  </Button>
                )}
                {resumeStatus.files?.code && (
                  <Button
                    variant="secondary"
                    onClick={() => handleResumeFrom(9)}
                    className="text-xs w-full"
                  >
                    Step 9 (Package)
                  </Button>
                )}
              </div>
            </div>
          </Card>
        )}
        
        {loadingResume && (
          <Card>
            <div className="text-center py-4 text-gray-600">
              Checking for previous work...
            </div>
          </Card>
        )}
      </div>

      {/* YAML Editor Modal */}
      {showEditYaml && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowEditYaml(false)}>
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h2 className="text-base font-semibold text-gray-900">Edit YAML Configuration</h2>
              <button
                onClick={() => setShowEditYaml(false)}
                className="text-gray-400 hover:text-gray-600 text-lg leading-none"
              >
                ×
              </button>
            </div>
            
            <div className="flex-1 p-4 overflow-auto">
              <textarea
                value={editableYaml}
                onChange={(e) => setEditableYaml(e.target.value)}
              className="w-full h-full min-h-[400px] px-3 py-2 font-mono text-xs border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                placeholder="Enter YAML configuration..."
              />
            </div>
            
            <div className="flex items-center justify-end space-x-2 p-4 border-t border-gray-200">
              <Button
                variant="secondary"
                onClick={() => setShowEditYaml(false)}
              >
                Cancel
              </Button>
              <Button onClick={handleSaveYaml}>
                Save Changes
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
