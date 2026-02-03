/**
 * MyTasks - 开发者任务工作台
 * 
 * 显示当前开发者的所有任务，按模块分组
 * 包含进度追踪和一键跳转到 Generator 开发
 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useWorkflowStore } from '@/store/workflowStore'
import Card from '@/components/common/Card'
import Button from '@/components/common/Button'

export default function MyTasks() {
  const navigate = useNavigate()
  const { 
    currentDeveloper, 
    tasks, 
    taskStats, 
    loadingTasks,
    fetchMyTasks 
  } = useWorkflowStore()

  // 查看文件模态框状态
  const [showViewModal, setShowViewModal] = useState(false)
  const [viewingItem, setViewingItem] = useState(null)
  const [viewedFiles, setViewedFiles] = useState({ yaml: null, checker: null, readme: null })
  const [activeFileTab, setActiveFileTab] = useState('yaml')
  const [loadingFiles, setLoadingFiles] = useState(false)

  // 获取任务状态 - 使用 task.status 字符串
  const getItemStatus = (task) => {
    const status = (task.status || '').toLowerCase()
    if (status.includes('complet')) return 'completed'
    if (status.includes('progress') || status.includes('ongoing')) return 'in_progress'
    return 'not_started'
  }

  // 渲染状态时钟图标
  const renderStatusIcon = (status) => {
    const clockIcon = (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    )

    switch (status) {
      case 'completed':
        return <span className="text-green-500">{clockIcon}</span>
      case 'in_progress':
        return <span className="text-yellow-500">{clockIcon}</span>
      case 'not_started':
      default:
        return <span className="text-red-500">{clockIcon}</span>
    }
  }

  // 处理按钮点击
  const handleItemAction = async (module, task) => {
    const status = getItemStatus(task)
    
    if (status === 'completed') {
      // 查看生成的文件
      await handleViewItem(module, task.item_id)
    } else {
      // 跳转到 Generator Step1，并携带 module 和 item
      navigate(`/generate/step1?module=${encodeURIComponent(module)}&item=${encodeURIComponent(task.item_id)}`)
    }
  }

  // 查看已完成的 item 文件
  const handleViewItem = async (module, itemId) => {
    setViewingItem({ module, itemId })
    setShowViewModal(true)
    setLoadingFiles(true)
    setViewedFiles({ yaml: null, checker: null, readme: null })

    try {
      // 并行加载三个文件
      const [yamlRes, checkerRes, readmeRes] = await Promise.allSettled([
        fetch(`http://localhost:8000/api/step1/modules/${encodeURIComponent(module)}/items/${encodeURIComponent(itemId)}`),
        fetch(`http://localhost:8000/api/step7/read-file?path=${encodeURIComponent(`Check_modules/${module}/scripts/checker/${itemId}.py`)}`),
        fetch(`http://localhost:8000/api/step7/read-file?path=${encodeURIComponent(`Check_modules/${module}/scripts/doc/${itemId}_README.md`)}`)
      ])

      const files = {
        yaml: null,
        checker: null,
        readme: null
      }

      // 处理 YAML
      if (yamlRes.status === 'fulfilled' && yamlRes.value.ok) {
        const data = await yamlRes.value.json()
        // step1 API 直接返回数据对象，不是嵌套在 data.data 中
        files.yaml = JSON.stringify(data, null, 2)
      }

      // 处理 Checker
      if (checkerRes.status === 'fulfilled' && checkerRes.value.ok) {
        const data = await checkerRes.value.json()
        if (data.content) {
          files.checker = data.content
        }
      }

      // 处理 README
      if (readmeRes.status === 'fulfilled' && readmeRes.value.ok) {
        const data = await readmeRes.value.json()
        console.log('README API response:', data)
        if (data.status === 'success' && data.content) {
          files.readme = data.content
        } else if (data.status === 'error') {
          console.warn('README not found:', data.error)
        }
      } else {
        console.error('README fetch failed:', readmeRes.status === 'fulfilled' ? readmeRes.value.status : readmeRes.reason)
      }

      setViewedFiles(files)
    } catch (error) {
      console.error('Failed to load item files:', error)
    } finally {
      setLoadingFiles(false)
    }
  }

  // 关闭模态框
  const closeViewModal = () => {
    setShowViewModal(false)
    setViewingItem(null)
    setViewedFiles({ yaml: null, checker: null, readme: null })
    setActiveFileTab('yaml')
  }

  // 智能跳转到 Generator 对应步骤
  const handleEditInGenerator = () => {
    if (!viewingItem) return

    const { module, itemId } = viewingItem
    
    // 根据当前查看的标签页跳转到不同步骤
    let targetPath = ''
    switch (activeFileTab) {
      case 'yaml':
        // YAML配置 → Step 1
        targetPath = `/generate/step1?module=${encodeURIComponent(module)}&item=${encodeURIComponent(itemId)}`
        break
      case 'checker':
        // Checker脚本 → Step 5
        targetPath = `/generate/step5?module=${encodeURIComponent(module)}&item=${encodeURIComponent(itemId)}`
        break
      case 'readme':
        // README → Step 4
        targetPath = `/generate/step4?module=${encodeURIComponent(module)}&item=${encodeURIComponent(itemId)}`
        break
      default:
        targetPath = `/generate/new?module=${encodeURIComponent(module)}&item=${encodeURIComponent(itemId)}`
    }
    
    closeViewModal()
    navigate(targetPath)
  }

  // 当开发者变更时加载任务
  useEffect(() => {
    if (currentDeveloper) {
      fetchMyTasks()
    }
  }, [currentDeveloper, fetchMyTasks])

  // 按模块分组任务
  const tasksByModule = tasks.reduce((acc, task) => {
    if (!acc[task.module]) {
      acc[task.module] = []
    }
    acc[task.module].push(task)
    return acc
  }, {})

  // 未选择开发者提示
  if (!currentDeveloper) {
    return (
      <div className="min-h-full bg-gray-50">
        <div className="w-full px-6 py-8">
          <div className="text-center py-20">
            <svg 
              className="mx-auto w-16 h-16 text-gray-300 mb-4" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={1.5} 
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" 
              />
            </svg>
            <h2 className="text-xl font-medium text-gray-600 mb-2">No Developer Selected</h2>
            <p className="text-gray-500">Please select a developer from the header dropdown</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-full bg-gray-50">
      <div className="w-full px-6 py-8 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">My Tasks</h1>
            <p className="mt-1 text-sm text-gray-600">
              Welcome, <span className="font-medium text-gray-900">{currentDeveloper.replace(/_/g, ' ')}</span>
            </p>
          </div>
          <Button variant="secondary" onClick={fetchMyTasks} disabled={loadingTasks}>
            {loadingTasks ? 'Refreshing...' : 'Refresh'}
          </Button>
        </div>

        {/* Progress Overview */}
        {taskStats && (
          <Card>
            <div className="flex items-center gap-8">
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-600 mb-2">Overall Progress</div>
                <div className="flex items-center gap-4">
                  <div className="flex-1 h-3 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-primary transition-all duration-500 ease-out"
                      style={{ width: `${taskStats.progress_percent}%` }}
                    />
                  </div>
                  <span className="text-lg font-semibold text-gray-900 min-w-[120px] text-right">
                    {taskStats.completed}/{taskStats.total} ({taskStats.progress_percent}%)
                  </span>
                </div>
              </div>
              <div className="flex gap-8 text-center border-l border-gray-200 pl-8">
                <div>
                  <div className="text-2xl font-bold text-green-600">{taskStats.completed}</div>
                  <div className="text-xs text-gray-500 mt-1">Completed</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-primary">{taskStats.in_progress}</div>
                  <div className="text-xs text-gray-500 mt-1">In Progress</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-400">{taskStats.not_started}</div>
                  <div className="text-xs text-gray-500 mt-1">Not Started</div>
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Tasks by Module */}
        {loadingTasks ? (
          <div className="text-center py-10">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-primary border-t-transparent"></div>
            <p className="mt-2 text-gray-500">Loading tasks...</p>
          </div>
        ) : Object.keys(tasksByModule).length === 0 ? (
          <Card>
            <div className="text-center py-10">
              <svg 
                className="mx-auto w-12 h-12 text-gray-300 mb-3" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={1.5} 
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" 
                />
              </svg>
              <p className="text-gray-500">No tasks assigned to you yet</p>
            </div>
          </Card>
        ) : (
          <div className="space-y-4">
            {Object.entries(tasksByModule).map(([module, moduleTasks]) => {
              const completedCount = moduleTasks.filter(t => t.is_complete).length
              const progressPercent = Math.round((completedCount / moduleTasks.length) * 100)
              
              return (
                <Card key={module} className="p-0 overflow-hidden">
                  {/* Module Header */}
                  <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                      <h3 className="text-base font-medium text-gray-900">{module}</h3>
                      <div className="flex items-center gap-3">
                        <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-primary transition-all"
                            style={{ width: `${progressPercent}%` }}
                          />
                        </div>
                        <span className="text-sm text-gray-600">
                          {completedCount}/{moduleTasks.length}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Task List */}
                  <div className="divide-y divide-gray-100">
                    {moduleTasks.map(task => {
                      const status = getItemStatus(task)
                      const buttonText = status === 'completed' ? 'View' : 'Start'
                      
                      return (
                        <div 
                          key={task.item_id}
                          className="px-6 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
                        >
                          <div className="flex items-center gap-4">
                            {/* Status Clock Icon */}
                            {renderStatusIcon(status)}
                            
                            {/* Item ID */}
                            <span className="font-mono text-sm text-gray-900">{task.item_id}</span>
                            
                            {/* File Status Tags */}
                            <div className="flex gap-1.5">
                              {task.has_yaml && (
                                <span className="text-xs px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 font-medium">
                                  YAML
                                </span>
                              )}
                              {task.has_checker && (
                                <span className="text-xs px-1.5 py-0.5 rounded bg-green-100 text-green-700 font-medium">
                                  PY
                                </span>
                              )}
                              {task.has_readme && (
                                <span className="text-xs px-1.5 py-0.5 rounded bg-purple-100 text-purple-700 font-medium">
                                  DOC
                                </span>
                              )}
                            </div>
                          </div>
                          
                          {/* Action Button */}
                          <Button
                            size="sm"
                            variant={status === 'completed' ? "secondary" : "primary"}
                            onClick={() => handleItemAction(module, task)}
                          >
                            {buttonText}
                          </Button>
                        </div>
                      )
                    })}
                  </div>
                </Card>
              )
            })}
          </div>
        )}

        {/* View Files Modal */}
        {showViewModal && viewingItem && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col">
              {/* Modal Header */}
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">{viewingItem.itemId}</h2>
                  <p className="text-sm text-gray-500 mt-1">{viewingItem.module}</p>
                </div>
                <button
                  onClick={closeViewModal}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* File Tabs */}
              <div className="flex border-b border-gray-200 bg-gray-50">
                {[
                  { key: 'yaml', label: '📋 YAML Config', icon: '📋' },
                  { key: 'checker', label: '🐍 Checker Script', icon: '🐍' },
                  { key: 'readme', label: '📖 README', icon: '📖' }
                ].map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => setActiveFileTab(tab.key)}
                    className={`px-6 py-3 font-medium transition-colors ${
                      activeFileTab === tab.key
                        ? 'border-b-2 border-blue-500 text-blue-600 bg-white'
                        : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* File Content */}
              <div className="flex-1 overflow-auto p-6 bg-gray-50">
                {loadingFiles ? (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center">
                      <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent mb-3"></div>
                      <p className="text-gray-600">Loading files...</p>
                    </div>
                  </div>
                ) : viewedFiles[activeFileTab] ? (
                  <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                    <pre className="text-sm p-4 overflow-x-auto">
                      <code className="language-python">{viewedFiles[activeFileTab]}</code>
                    </pre>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center">
                      <svg className="mx-auto w-12 h-12 text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <p className="text-gray-500 mb-1">
                        {activeFileTab === 'yaml' && 'YAML configuration not found'}
                        {activeFileTab === 'checker' && 'Checker script not found'}
                        {activeFileTab === 'readme' && 'README not found'}
                      </p>
                      <p className="text-sm text-gray-400">This file may not have been generated yet</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-end gap-3">
                <Button
                  variant="secondary"
                  onClick={closeViewModal}
                >
                  Close
                </Button>
                <Button
                  onClick={handleEditInGenerator}
                >
                  Edit in Generator
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
