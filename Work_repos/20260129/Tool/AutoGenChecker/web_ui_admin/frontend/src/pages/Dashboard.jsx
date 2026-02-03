import { useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Card from '@/components/common/Card'
import Button from '@/components/common/Button'
import StatusBadge from '@/components/common/StatusBadge'
import { useModulesStore } from '@/store/modulesStore'
import { useDashboardStore } from '@/store/dashboardStore'
import { useWorkflowStore } from '@/store/workflowStore'
import { getDashboardExcelSummary } from '@/api/endpoints'

export default function Dashboard() {
  const navigate = useNavigate()
  
  // Use cached modules from global store
  const { modules, isLoading: loadingModules, fetchModules } = useModulesStore()
  
  // Use cached dashboard data from global store
  const { 
    developers, 
    activities, 
    stats,
    loadingDevelopers,
    loadingActivities,
    loadingStats,
    fetchAll: fetchDashboardData,
    refresh: refreshDashboard,
    lastFetched
  } = useDashboardStore()

  // Get current developer from workflow store
  const { currentDeveloper } = useWorkflowStore()
  
  // Excel summary state
  const [excelSummary, setExcelSummary] = useState(null)
  const [loadingExcel, setLoadingExcel] = useState(false)
  
  // Last refresh time - derived from store's lastFetched
  const lastRefresh = lastFetched ? new Date(lastFetched) : new Date()

  // Fetch modules from cache
  useEffect(() => {
    fetchModules()
  }, [fetchModules])

  // Refresh interval setting (in seconds, 0 = disabled) - persisted to localStorage
  const [refreshInterval, setRefreshInterval] = useState(() => {
    const saved = localStorage.getItem('dashboard-refresh-interval')
    return saved !== null ? Number(saved) : 30
  })
  const [isPageVisible, setIsPageVisible] = useState(true)

  // Persist refresh interval to localStorage
  useEffect(() => {
    localStorage.setItem('dashboard-refresh-interval', String(refreshInterval))
  }, [refreshInterval])

  // Track page visibility
  useEffect(() => {
    const handleVisibilityChange = () => {
      setIsPageVisible(document.visibilityState === 'visible')
    }
    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [])

  // Initial load - uses cache if available, respects refreshInterval setting
  useEffect(() => {
    // fetchDashboardData checks cache internally, won't refetch if cache is valid
    fetchDashboardData()
    
    // Fetch Excel summary
    fetchExcelSummary()
  }, [fetchDashboardData])

  // Reload Excel summary when developer changes
  useEffect(() => {
    if (excelSummary) {
      // Force reload to ensure fresh data
      fetchExcelSummary()
    }
  }, [currentDeveloper])

  // Fetch Excel summary
  const fetchExcelSummary = async () => {
    setLoadingExcel(true)
    try {
      const data = await getDashboardExcelSummary()
      console.log('Excel Summary loaded:', {
        developers: data.developers?.length,
        currentDeveloper,
        found: data.developers?.find(d => d.name === currentDeveloper)
      })
      setExcelSummary(data)
    } catch (error) {
      console.error('Failed to fetch Excel summary:', error)
      setExcelSummary(null)
    } finally {
      setLoadingExcel(false)
    }
  }

  // Auto-refresh interval (only if enabled)
  useEffect(() => {
    if (refreshInterval === 0) return // Disabled, no interval
    
    const interval = setInterval(() => {
      if (isPageVisible) {
        refreshDashboard() // Force refresh
      }
    }, refreshInterval * 1000)
    
    return () => clearInterval(interval)
  }, [refreshDashboard, refreshInterval, isPageVisible])

  const handleNewProject = () => {
    navigate('/generate/new')
  }

  // Helper to format time ago
  const formatTimeAgo = (timeStr) => {
    if (!timeStr) return 'Unknown'
    try {
      const date = new Date(timeStr.replace(' ', 'T').substring(0, 19))
      const now = new Date()
      const diffMs = now - date
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)
      
      if (diffMins < 1) return 'Just now'
      if (diffMins < 60) return `${diffMins} min ago`
      if (diffHours < 24) return `${diffHours} hr ago`
      return `${diffDays} days ago`
    } catch {
      return timeStr
    }
  }

  // Get status color for developer
  const getStatusColor = (status) => {
    switch (status) {
      case 'working': return 'bg-green-500'
      case 'active': return 'bg-blue-500'
      default: return 'bg-gray-400'
    }
  }

  // Get status text
  const getStatusText = (status) => {
    switch (status) {
      case 'working': return 'Working'
      case 'active': return 'Active'
      default: return 'Idle'
    }
  }

  // Format branch name for display
  const formatBranch = (branch) => {
    if (!branch) return 'unknown'
    // Format: assignment/zhongyu_sun_20260106 -> zhongyu_sun (20260106)
    if (branch.startsWith('assignment/')) {
      const assignmentPart = branch.replace('assignment/', '')
      const match = assignmentPart.match(/^(.+?)_(\d{8})$/)
      if (match) {
        return `${match[1].replace(/_/g, ' ')} (${match[2]})`
      }
      return assignmentPart
    }
    return branch
  }

  return (
    <div className="min-h-full bg-gray-50">
      <div className="w-full px-6 py-8 space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
            <p className="mt-1 text-sm text-gray-600">
              Overview of checker generation projects and developer status
            </p>
          </div>
          <div className="flex items-center gap-4">
            {/* Refresh Interval Selector */}
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="text-sm border border-gray-300 rounded-md px-2 py-1.5 bg-white text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={0}>Auto-refresh: Off</option>
              <option value={15}>Every 15s</option>
              <option value={30}>Every 30s</option>
              <option value={60}>Every 1min</option>
              <option value={120}>Every 2min</option>
            </select>
            <div className="text-sm text-gray-500">
              {lastRefresh.toLocaleTimeString()}
              {!isPageVisible && <span className="ml-1 text-yellow-600">(paused)</span>}
            </div>
            <Button variant="secondary" onClick={() => {
              refreshDashboard()
              fetchExcelSummary()
            }}>
              Refresh
            </Button>
            <Button onClick={handleNewProject}>
              New Project
            </Button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          {/* Show Excel stats for Admin, Git stats for Developer */}
          {!currentDeveloper ? (
            // Admin View - Excel Statistics
            <>
              <Card>
                <div className="space-y-2">
                  <div className="text-base text-gray-600">Total Modules</div>
                  <div className="text-3xl font-semibold text-gray-900">
                    {loadingExcel ? '...' : excelSummary?.total_modules || 0}
                  </div>
                  <div className="text-xs text-gray-500">From Excel</div>
                </div>
              </Card>

              <Card>
                <div className="space-y-2">
                  <div className="text-base text-gray-600">Total Items</div>
                  <div className="text-3xl font-semibold text-primary">
                    {loadingExcel ? '...' : excelSummary?.total_items || 0}
                  </div>
                  <div className="text-xs text-gray-500">From Excel</div>
                </div>
              </Card>

              <Card>
                <div className="space-y-2">
                  <div className="text-base text-gray-600">Completed</div>
                  <div className="text-3xl font-semibold text-green-600">
                    {loadingExcel ? '...' : excelSummary?.status_distribution?.completed || 0}
                  </div>
                  <div className="text-xs text-gray-500">
                    {excelSummary?.total_items > 0 
                      ? `${Math.round(excelSummary.status_distribution.completed / excelSummary.total_items * 100)}%` 
                      : '0%'}
                  </div>
                </div>
              </Card>

              <Card>
                <div className="space-y-2">
                  <div className="text-base text-gray-600">In Progress</div>
                  <div className="text-3xl font-semibold text-blue-600">
                    {loadingExcel ? '...' : excelSummary?.status_distribution?.in_progress || 0}
                  </div>
                  <div className="text-xs text-gray-500">Active items</div>
                </div>
              </Card>

              <Card>
                <div className="space-y-2">
                  <div className="text-base text-gray-600">Not Started</div>
                  <div className="text-3xl font-semibold text-gray-600">
                    {loadingExcel ? '...' : excelSummary?.status_distribution?.not_started || 0}
                  </div>
                  <div className="text-xs text-gray-500">Pending</div>
                </div>
              </Card>
            </>
          ) : (
            // Developer View - Personal Statistics
            <>
              <Card>
                <div className="space-y-2">
                  <div className="text-base text-gray-600">My Assigned</div>
                  <div className="text-3xl font-semibold text-gray-900">
                    {loadingExcel ? '...' : (
                      excelSummary?.developers?.find(d => d.name === currentDeveloper)?.total_assigned || 0
                    )}
                  </div>
                  <div className="text-xs text-gray-500">Total tasks</div>
                </div>
              </Card>

              <Card>
                <div className="space-y-2">
                  <div className="text-base text-gray-600">Completed</div>
                  <div className="text-3xl font-semibold text-green-600">
                    {loadingExcel ? '...' : (
                      excelSummary?.developers?.find(d => d.name === currentDeveloper)?.completed || 0
                    )}
                  </div>
                  <div className="text-xs text-gray-500">
                    {(() => {
                      const dev = excelSummary?.developers?.find(d => d.name === currentDeveloper)
                      return dev?.completion_rate ? `${dev.completion_rate}%` : '0%'
                    })()}
                  </div>
                </div>
              </Card>

              <Card>
                <div className="space-y-2">
                  <div className="text-base text-gray-600">In Progress</div>
                  <div className="text-3xl font-semibold text-blue-600">
                    {loadingExcel ? '...' : (
                      excelSummary?.developers?.find(d => d.name === currentDeveloper)?.in_progress || 0
                    )}
                  </div>
                  <div className="text-xs text-gray-500">Working on</div>
                </div>
              </Card>

              <Card>
                <div className="space-y-2">
                  <div className="text-base text-gray-600">Not Started</div>
                  <div className="text-3xl font-semibold text-gray-600">
                    {loadingExcel ? '...' : (
                      excelSummary?.developers?.find(d => d.name === currentDeveloper)?.not_started || 0
                    )}
                  </div>
                  <div className="text-xs text-gray-500">Pending</div>
                </div>
              </Card>

              <Card>
                <div className="space-y-2">
                  <div className="text-base text-gray-600">Git Commits</div>
                  <div className="text-3xl font-semibold text-purple-600">
                    {loadingStats ? '...' : stats.total_commits_today}
                  </div>
                  <div className="text-xs text-gray-500">Today</div>
                </div>
              </Card>
            </>
          )}
        </div>

        {/* Team Progress Table - Only show for Admin */}
        {!currentDeveloper && excelSummary?.developers && excelSummary.developers.length > 0 && (
          <Card>
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-gray-900">
                Team Progress ({excelSummary.developers.length} developers)
              </h2>
              
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left text-sm font-semibold text-gray-600 py-3 px-2">Developer</th>
                      <th className="text-center text-sm font-semibold text-gray-600 py-3 px-2">Assigned</th>
                      <th className="text-center text-sm font-semibold text-gray-600 py-3 px-2">Completed</th>
                      <th className="text-center text-sm font-semibold text-gray-600 py-3 px-2">In Progress</th>
                      <th className="text-center text-sm font-semibold text-gray-600 py-3 px-2">Not Started</th>
                      <th className="text-left text-sm font-semibold text-gray-600 py-3 px-2">Progress</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {excelSummary.developers.map((dev) => (
                      <tr key={dev.name} className="hover:bg-gray-50">
                        <td className="py-3 px-2">
                          <div className="font-medium text-gray-900">{dev.name}</div>
                        </td>
                        <td className="py-3 px-2 text-center text-gray-900 font-medium">
                          {dev.total_assigned}
                        </td>
                        <td className="py-3 px-2 text-center">
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            {dev.completed}
                          </span>
                        </td>
                        <td className="py-3 px-2 text-center">
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {dev.in_progress}
                          </span>
                        </td>
                        <td className="py-3 px-2 text-center">
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            {dev.not_started}
                          </span>
                        </td>
                        <td className="py-3 px-2">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 bg-gray-200 rounded-full h-2 overflow-hidden">
                              <div 
                                className="bg-green-600 h-2 rounded-full transition-all"
                                style={{ width: `${dev.completion_rate}%` }}
                              ></div>
                            </div>
                            <span className="text-sm font-medium text-gray-700 min-w-[45px]">
                              {dev.completion_rate}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </Card>
        )}

        {/* Developer Status Section */}
        <Card>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">
                Developer Status ({developers.length} developers)
              </h2>
              <div className="flex items-center gap-4 text-sm">
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-green-500"></span>
                  Working
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                  Active
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-gray-400"></span>
                  Idle
                </span>
              </div>
            </div>

            {loadingDevelopers ? (
              <div className="text-center py-4 text-gray-500">Loading developers...</div>
            ) : developers.length === 0 ? (
              <div className="text-center py-4 text-gray-500">No developers found</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left text-sm font-semibold text-gray-600 py-3 px-2">Status</th>
                      <th className="text-left text-sm font-semibold text-gray-600 py-3 px-2">Developer</th>
                      <th className="text-left text-sm font-semibold text-gray-600 py-3 px-2">Current Branch</th>
                      <th className="text-left text-sm font-semibold text-gray-600 py-3 px-2">Last Commit</th>
                      <th className="text-left text-sm font-semibold text-gray-600 py-3 px-2">Items Worked On</th>
                      <th className="text-left text-sm font-semibold text-gray-600 py-3 px-2">Last Activity</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {developers.map((dev) => (
                      <tr key={dev.workspace_name} className="hover:bg-gray-50">
                        <td className="py-3 px-2">
                          <div className="flex items-center gap-2">
                            <span className={`w-3 h-3 rounded-full ${getStatusColor(dev.status)}`}></span>
                            <span className="text-sm text-gray-600">{getStatusText(dev.status)}</span>
                          </div>
                        </td>
                        <td className="py-3 px-2">
                          <div className="font-medium text-gray-900">{dev.developer_name}</div>
                        </td>
                        <td className="py-3 px-2">
                          <code className="text-sm bg-gray-100 px-2 py-1 rounded" title={dev.current_branch}>
                            {formatBranch(dev.current_branch)}
                          </code>
                        </td>
                        <td className="py-3 px-2">
                          <div className="text-sm text-gray-600 truncate max-w-xs" title={dev.last_commit_message}>
                            {dev.last_commit_message || 'No commits'}
                          </div>
                        </td>
                        <td className="py-3 px-2">
                          {dev.modified_items && dev.modified_items.length > 0 ? (
                            <div className="flex flex-wrap gap-1" title={dev.modified_items.join(', ')}>
                              {dev.modified_items.slice(0, 3).map((item, idx) => (
                                <span key={idx} className="text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded">
                                  {item}
                                </span>
                              ))}
                              {dev.modified_items.length > 3 && (
                                <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                                  +{dev.modified_items.length - 3} more
                                </span>
                              )}
                            </div>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="py-3 px-2 text-sm text-gray-500">
                          {formatTimeAgo(dev.last_commit_time)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </Card>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Activity */}
          <Card className="lg:col-span-1">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">
                  Recent Activity
                </h2>
              </div>

              {loadingActivities ? (
                <div className="text-center py-4 text-gray-500">Loading activities...</div>
              ) : activities.length === 0 ? (
                <div className="text-center py-4 text-gray-500">No recent activity</div>
              ) : (
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {activities.map((item) => (
                    <div
                      key={item.id}
                      className="border-b border-gray-100 last:border-0 pb-4 last:pb-0"
                    >
                      <div className="flex items-start justify-between">
                        <div className="min-w-0 flex-1">
                          <div className="text-sm font-medium text-gray-900">
                            {item.developer}
                          </div>
                          <div className="text-sm text-gray-600 truncate mt-1" title={item.action}>
                            {item.action}
                          </div>
                          {item.item_id && (
                            <div className="text-xs text-primary mt-1">
                              {item.item_id}
                            </div>
                          )}
                        </div>
                        <div className="ml-2 flex-shrink-0">
                          <StatusBadge status={item.status.toUpperCase()} />
                        </div>
                      </div>
                      <div className="text-xs text-gray-500 mt-2">
                        {formatTimeAgo(item.time)}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <button
                onClick={() => navigate('/history')}
                className="w-full text-base text-primary hover:text-primary-hover text-center py-2"
              >
                View All Activity
              </button>
            </div>
          </Card>

          {/* Available Modules */}
          <Card className="lg:col-span-2">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">
                  Available Modules (from CHECKLIST)
                </h2>
              </div>

              {/* Module List */}
              {loadingModules ? (
                <div className="text-center py-8 text-gray-600">Loading modules...</div>
              ) : modules.length === 0 ? (
                <div className="text-center py-8 text-gray-600">No modules found</div>
              ) : (
                <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
                  <table className="min-w-full">
                    <thead className="sticky top-0 bg-white">
                      <tr className="border-b border-gray-200">
                        <th className="text-left text-sm font-semibold text-gray-600 uppercase tracking-wider py-3">
                          Module ID
                        </th>
                        <th className="text-left text-sm font-semibold text-gray-600 uppercase tracking-wider py-3">
                          Module Name
                        </th>
                        <th className="text-left text-sm font-semibold text-gray-600 uppercase tracking-wider py-3">
                          Items
                        </th>
                        <th className="text-right text-sm font-semibold text-gray-600 uppercase tracking-wider py-3">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {modules.map((module) => (
                        <tr key={module.module_id} className="hover:bg-gray-50">
                          <td className="py-3 text-sm font-medium text-gray-900">
                            {module.module_id}
                          </td>
                          <td className="py-3 text-sm text-gray-600">
                            {module.module_name}
                          </td>
                          <td className="py-3 text-sm text-gray-600">
                            {module.item_count} items
                          </td>
                          <td className="py-3 text-right">
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => navigate(`/generate/new?module=${module.module_id}`)}
                            >
                              Create Checker
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
