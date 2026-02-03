/**
 * Dispatch - 管理员分发工作空间页面
 * 
 * 用于创建开发者工作目录并分配模块/任务
 */
import { useState, useEffect } from 'react'
import { useWorkflowStore } from '@/store/workflowStore'
import { useModulesStore } from '@/store/modulesStore'
import Card from '@/components/common/Card'
import Button from '@/components/common/Button'

export default function Dispatch() {
  const { 
    developers, 
    fetchDevelopers, 
    createWorkspace, 
    dispatchStatus,
    isDispatching,
    clearDispatchStatus 
  } = useWorkflowStore()
  
  const { modules, fetchModules, isLoading: loadingModules } = useModulesStore()
  
  const [selectedDeveloper, setSelectedDeveloper] = useState('')
  const [newDeveloperName, setNewDeveloperName] = useState('')
  const [selectedModules, setSelectedModules] = useState([])

  // 初始加载
  useEffect(() => {
    fetchDevelopers()
    fetchModules()
  }, [fetchDevelopers, fetchModules])

  // 清除结果
  useEffect(() => {
    return () => clearDispatchStatus()
  }, [clearDispatchStatus])

  const handleCreateWorkspace = async () => {
    const developerName = newDeveloperName.trim() || selectedDeveloper
    if (!developerName || selectedModules.length === 0) {
      alert('Please enter developer name and select at least one module')
      return
    }

    await createWorkspace({
      developer_name: developerName.replace(/\s+/g, '_'),
      modules: selectedModules,
      include_reference: true
    })
  }

  const toggleModule = (moduleName) => {
    setSelectedModules(prev => 
      prev.includes(moduleName)
        ? prev.filter(m => m !== moduleName)
        : [...prev, moduleName]
    )
  }

  const selectAllModules = () => {
    if (selectedModules.length === modules.length) {
      setSelectedModules([])
    } else {
      setSelectedModules(modules.map(m => m.name))
    }
  }

  const totalItems = selectedModules.reduce((sum, moduleName) => {
    const module = modules.find(m => m.name === moduleName)
    return sum + (module?.item_count || 0)
  }, 0)

  return (
    <div className="min-h-full bg-gray-50">
      <div className="w-full px-6 py-8 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Dispatch Workspace</h1>
          <p className="mt-1 text-sm text-gray-600">
            Create developer workspaces and assign modules for checker development
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Configuration */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <h2 className="text-lg font-medium text-gray-900 mb-4">Developer</h2>
              
              {/* Existing Developer Selection */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Existing Developer
                </label>
                <select
                  value={selectedDeveloper}
                  onChange={(e) => {
                    setSelectedDeveloper(e.target.value)
                    if (e.target.value) setNewDeveloperName('')
                  }}
                  className="w-full border border-gray-300 rounded-lg px-4 py-2.5 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                >
                  <option value="">-- Select existing developer --</option>
                  {developers.map(dev => (
                    <option key={dev} value={dev}>{dev.replace(/_/g, ' ')}</option>
                  ))}
                </select>
              </div>

              {/* New Developer Input */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Or Enter New Developer Name
                </label>
                <input
                  type="text"
                  value={newDeveloperName}
                  onChange={(e) => {
                    setNewDeveloperName(e.target.value)
                    if (e.target.value) setSelectedDeveloper('')
                  }}
                  placeholder="e.g., John Smith"
                  className="w-full border border-gray-300 rounded-lg px-4 py-2.5 bg-white text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
              </div>
            </Card>

            <Card>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-medium text-gray-900">
                  Modules ({selectedModules.length} selected)
                </h2>
                <Button 
                  variant="secondary" 
                  size="sm"
                  onClick={selectAllModules}
                >
                  {selectedModules.length === modules.length ? 'Deselect All' : 'Select All'}
                </Button>
              </div>

              {loadingModules ? (
                <div className="text-center py-8">
                  <div className="inline-block animate-spin rounded-full h-6 w-6 border-2 border-primary border-t-transparent"></div>
                  <p className="mt-2 text-sm text-gray-500">Loading modules...</p>
                </div>
              ) : (
                <div className="max-h-80 overflow-y-auto border border-gray-200 rounded-lg divide-y divide-gray-100">
                  {modules.map(module => (
                    <label 
                      key={module.name}
                      className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={selectedModules.includes(module.name)}
                        onChange={() => toggleModule(module.name)}
                        className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
                      />
                      <span className="flex-1 text-sm text-gray-900">{module.name}</span>
                      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                        {module.item_count} items
                      </span>
                    </label>
                  ))}
                </div>
              )}
            </Card>
          </div>

          {/* Right: Summary and Action */}
          <div className="space-y-6">
            <Card>
              <h2 className="text-lg font-medium text-gray-900 mb-4">Summary</h2>
              
              <div className="space-y-4">
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                  <span className="text-sm text-gray-600">Developer</span>
                  <span className="text-sm font-medium text-gray-900">
                    {newDeveloperName.trim() || selectedDeveloper || 'Not selected'}
                  </span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                  <span className="text-sm text-gray-600">Modules</span>
                  <span className="text-sm font-medium text-gray-900">
                    {selectedModules.length}
                  </span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                  <span className="text-sm text-gray-600">Total Items</span>
                  <span className="text-sm font-medium text-primary">
                    {totalItems}
                  </span>
                </div>
              </div>

              <Button 
                className="w-full mt-6"
                onClick={handleCreateWorkspace}
                disabled={isDispatching || (!selectedDeveloper && !newDeveloperName.trim()) || selectedModules.length === 0}
                isLoading={isDispatching}
              >
                Create Workspace
              </Button>
            </Card>

            {/* Result */}
            {dispatchStatus && (
              <Card className={dispatchStatus.status === 'success' ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
                <h2 className="text-lg font-medium text-gray-900 mb-3">Result</h2>
                
                {dispatchStatus.status === 'success' ? (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-green-700">
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <span className="font-medium">Workspace Created</span>
                    </div>
                    <p className="text-sm text-gray-600">{dispatchStatus.message}</p>
                    {dispatchStatus.workspace_path && (
                      <div className="mt-2 p-2 bg-white rounded border border-green-200">
                        <p className="text-xs text-gray-500 mb-1">Path:</p>
                        <p className="text-xs font-mono text-gray-700 break-all">
                          {dispatchStatus.workspace_path}
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex items-start gap-2 text-red-700">
                    <svg className="w-5 h-5 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                    <div>
                      <span className="font-medium">Error</span>
                      <p className="text-sm mt-1">{dispatchStatus.error}</p>
                    </div>
                  </div>
                )}
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
