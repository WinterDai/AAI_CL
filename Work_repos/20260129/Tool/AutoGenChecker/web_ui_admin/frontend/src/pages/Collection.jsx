/**
 * Collection - 管理员回收页面
 * 
 * 用于从开发者处回收完成的 checker 文件
 * 支持预览、选择和批量回收
 */
import { useEffect, useState } from 'react'
import { useWorkflowStore } from '@/store/workflowStore'
import Card from '@/components/common/Card'
import Button from '@/components/common/Button'

export default function Collection() {
  const { 
    currentDeveloper,
    developers,
    collectionPreview,
    collectionResults,
    isCollecting,
    fetchDevelopers,
    fetchCollectionPreview,
    collectItems,
    clearCollectionResults
  } = useWorkflowStore()
  
  const [selectedDeveloper, setSelectedDeveloper] = useState('')
  const [selectedItems, setSelectedItems] = useState([])
  const [filterComplete, setFilterComplete] = useState(true)

  // 初始加载开发者列表
  useEffect(() => {
    fetchDevelopers()
  }, [fetchDevelopers])

  // 当选择开发者变更时加载预览
  useEffect(() => {
    const developer = selectedDeveloper || currentDeveloper
    if (developer) {
      fetchCollectionPreview(developer)
      setSelectedItems([])
    }
  }, [selectedDeveloper, currentDeveloper, fetchCollectionPreview])

  // 清除结果
  useEffect(() => {
    return () => clearCollectionResults()
  }, [clearCollectionResults])

  const activeDeveloper = selectedDeveloper || currentDeveloper

  const handleCollect = async () => {
    if (selectedItems.length === 0 || !activeDeveloper) return
    
    const items = selectedItems.map(itemId => {
      const item = collectionPreview?.items?.find(i => i.item_id === itemId)
      return { module: item.module, item_id: item.item_id }
    })
    await collectItems(items, activeDeveloper)
  }

  const toggleItem = (itemId) => {
    setSelectedItems(prev =>
      prev.includes(itemId)
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    )
  }

  const selectAllComplete = () => {
    const completeItems = collectionPreview?.items
      ?.filter(i => i.is_complete)
      .map(i => i.item_id) || []
    setSelectedItems(completeItems)
  }

  const clearSelection = () => {
    setSelectedItems([])
  }

  // 过滤显示的项目
  const displayItems = collectionPreview?.items?.filter(item => 
    filterComplete ? item.is_complete : true
  ) || []

  // 按模块分组
  const itemsByModule = displayItems.reduce((acc, item) => {
    if (!acc[item.module]) {
      acc[item.module] = []
    }
    acc[item.module].push(item)
    return acc
  }, {})

  return (
    <div className="min-h-full bg-gray-50">
      <div className="w-full px-6 py-8 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Collection</h1>
            <p className="mt-1 text-sm text-gray-600">
              Collect completed checker files from developers
            </p>
          </div>
          <div className="flex items-center gap-4">
            <select
              value={selectedDeveloper}
              onChange={(e) => setSelectedDeveloper(e.target.value)}
              className="text-sm border border-gray-300 rounded-lg px-4 py-2 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary min-w-[180px]"
            >
              <option value="">
                {currentDeveloper ? `Current: ${currentDeveloper.replace(/_/g, ' ')}` : 'Select Developer'}
              </option>
              {developers.map(dev => (
                <option key={dev} value={dev}>{dev.replace(/_/g, ' ')}</option>
              ))}
            </select>
            <Button 
              variant="secondary" 
              onClick={() => activeDeveloper && fetchCollectionPreview(activeDeveloper)}
            >
              Refresh
            </Button>
          </div>
        </div>

        {/* No Developer Selected */}
        {!activeDeveloper && (
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
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" 
                />
              </svg>
              <p className="text-gray-500">Please select a developer to view collectable items</p>
            </div>
          </Card>
        )}

        {activeDeveloper && (
          <>
            {/* Summary Stats */}
            {collectionPreview?.summary && (
              <Card>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-8">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-gray-900">{collectionPreview.summary.total}</div>
                      <div className="text-sm text-gray-500 mt-1">Total Items</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-green-600">{collectionPreview.summary.complete}</div>
                      <div className="text-sm text-gray-500 mt-1">Complete</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-yellow-600">{collectionPreview.summary.incomplete}</div>
                      <div className="text-sm text-gray-500 mt-1">Incomplete</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={filterComplete}
                        onChange={(e) => setFilterComplete(e.target.checked)}
                        className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
                      />
                      Show complete only
                    </label>
                    <div className="h-6 w-px bg-gray-200" />
                    <Button variant="secondary" size="sm" onClick={selectAllComplete}>
                      Select All Complete
                    </Button>
                    <Button variant="secondary" size="sm" onClick={clearSelection} disabled={selectedItems.length === 0}>
                      Clear
                    </Button>
                    <Button 
                      onClick={handleCollect}
                      disabled={isCollecting || selectedItems.length === 0}
                      isLoading={isCollecting}
                    >
                      Collect ({selectedItems.length})
                    </Button>
                  </div>
                </div>
              </Card>
            )}

            {/* Items Table */}
            <Card className="p-0 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200">
                      <th className="px-4 py-3 text-left w-12">
                        <input
                          type="checkbox"
                          onChange={(e) => {
                            if (e.target.checked) {
                              const completeIds = displayItems.filter(i => i.is_complete).map(i => i.item_id)
                              setSelectedItems(completeIds)
                            } else {
                              setSelectedItems([])
                            }
                          }}
                          checked={selectedItems.length > 0 && selectedItems.length === displayItems.filter(i => i.is_complete).length}
                          className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
                        />
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Item ID</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Module</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">YAML</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Checker</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">README</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {displayItems.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="px-4 py-10 text-center text-gray-500">
                          No items found
                        </td>
                      </tr>
                    ) : (
                      displayItems.map(item => (
                        <tr 
                          key={item.item_id} 
                          className={`hover:bg-gray-50 transition-colors ${
                            selectedItems.includes(item.item_id) ? 'bg-primary/5' : ''
                          }`}
                        >
                          <td className="px-4 py-3">
                            <input
                              type="checkbox"
                              checked={selectedItems.includes(item.item_id)}
                              onChange={() => toggleItem(item.item_id)}
                              disabled={!item.is_complete}
                              className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
                            />
                          </td>
                          <td className="px-4 py-3">
                            <span className="font-mono text-sm text-gray-900">{item.item_id}</span>
                          </td>
                          <td className="px-4 py-3">
                            <span className="text-sm text-gray-600">{item.module}</span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            {item.has_yaml ? (
                              <span className="text-green-500">✓</span>
                            ) : (
                              <span className="text-gray-300">–</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-center">
                            {item.has_checker ? (
                              <span className="text-green-500">✓</span>
                            ) : (
                              <span className="text-gray-300">–</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-center">
                            {item.has_readme ? (
                              <span className="text-green-500">✓</span>
                            ) : (
                              <span className="text-gray-300">–</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-center">
                            {item.is_complete ? (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                                Complete
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                                Incomplete
                              </span>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </Card>

            {/* Collection Results */}
            {collectionResults && (
              <Card>
                <h2 className="text-lg font-medium text-gray-900 mb-4">Collection Results</h2>
                
                <div className="space-y-3">
                  {/* Success */}
                  {collectionResults.results?.success?.length > 0 && (
                    <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                      <div className="flex items-center gap-2 text-green-700 font-medium mb-2">
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        Success ({collectionResults.results.success.length})
                      </div>
                      <p className="text-sm text-green-600">
                        {collectionResults.results.success.join(', ')}
                      </p>
                    </div>
                  )}
                  
                  {/* Incomplete */}
                  {collectionResults.results?.incomplete?.length > 0 && (
                    <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <div className="flex items-center gap-2 text-yellow-700 font-medium mb-2">
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                        Incomplete ({collectionResults.results.incomplete.length})
                      </div>
                      <p className="text-sm text-yellow-600">
                        {collectionResults.results.incomplete.map(i => i.item_id).join(', ')}
                      </p>
                    </div>
                  )}
                  
                  {/* Failed */}
                  {collectionResults.results?.failed?.length > 0 && (
                    <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                      <div className="flex items-center gap-2 text-red-700 font-medium mb-2">
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                        Failed ({collectionResults.results.failed.length})
                      </div>
                      <p className="text-sm text-red-600">
                        {collectionResults.results.failed.map(i => i.item_id).join(', ')}
                      </p>
                    </div>
                  )}

                  {/* Summary */}
                  {collectionResults.summary && (
                    <div className="pt-3 border-t border-gray-200 text-sm text-gray-600">
                      Collected {collectionResults.summary.success} of {collectionResults.summary.total} items
                    </div>
                  )}
                </div>
              </Card>
            )}
          </>
        )}
      </div>
    </div>
  )
}
