import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Card from '@/components/common/Card'
import Button from '@/components/common/Button'
import StatusBadge from '@/components/common/StatusBadge'
import HistoryDetail from '@/components/history/HistoryDetail'
import { getDashboardItems } from '@/api/endpoints'
import apiClient from '@/api/client'

export default function History() {
  const navigate = useNavigate()
  const [selectedItem, setSelectedItem] = useState(null)
  const [historyData, setHistoryData] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    status: 'all',
    module: 'all',
    owner: 'all',
    source: 'all'  // 'all', 'PD', 'MD'
  })

  // Fetch all items from Re-assign Excel
  const fetchHistory = async (forceRefresh = false) => {
    try {
      setLoading(true)
      console.log('Fetching items from Excel...')
      
      // Force refresh if requested
      if (forceRefresh) {
        await apiClient.post('/api/dashboard/items/refresh')
      }
      
      const data = await getDashboardItems()
      console.log('Received items:', data.length)
      
      // Transform to history format
      const transformedData = data.map((item, index) => ({
        id: index + 1,
        itemId: item.item_id,
        owner: item.owner || 'Unassigned',
        moduleName: item.module_name || 'Unknown',
        description: item.description || '',
        status: item.status?.toUpperCase() || 'UNKNOWN',
        source: item.source === 'Re-assign-MD' ? 'MD' : 'PD'
      }))
      console.log('Transformed data:', transformedData.length, 'items')
      setHistoryData(transformedData)
    } catch (error) {
      console.error('Failed to fetch items:', error)
      setHistoryData([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [])

  const handleViewDetail = (item) => {
    setSelectedItem(item)
  }

  const handleRefresh = () => {
    fetchHistory(true)
  }

  // Get unique owners and modules for filter dropdowns
  const uniqueOwners = ['all', ...new Set(historyData.map(item => item.owner).filter(Boolean))]
  const uniqueModules = ['all', ...new Set(historyData.map(item => item.moduleName).filter(Boolean))]

  const filteredData = historyData.filter(item => {
    if (filters.status !== 'all' && item.status !== filters.status) return false
    if (filters.module !== 'all' && item.moduleName !== filters.module) return false
    if (filters.owner !== 'all' && item.owner !== filters.owner) return false
    if (filters.source !== 'all' && item.source !== filters.source) return false
    return true
  })

  return (
    <div className="min-h-full bg-gray-50 flex">
      <div className={`flex-1 transition-all ${selectedItem ? 'mr-96' : ''}`}>
        <div className="w-full px-6 py-8 space-y-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900">History</h1>
              <p className="mt-1 text-base text-gray-600">
                View and manage past checker generations
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="secondary" onClick={handleRefresh}>
                Refresh
              </Button>
              <Button onClick={() => navigate('/generate/new')}>
                New Generation
              </Button>
            </div>
          </div>

          <Card>
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center space-x-4 flex-wrap gap-2">
                {/* PD/MD Toggle Buttons */}
                <div className="flex rounded-lg overflow-hidden border border-gray-300">
                  <button
                    onClick={() => setFilters({ ...filters, source: 'all' })}
                    className={`px-4 py-2 text-sm font-medium transition-colors ${
                      filters.source === 'all' 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-white text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    All
                  </button>
                  <button
                    onClick={() => setFilters({ ...filters, source: 'PD' })}
                    className={`px-4 py-2 text-sm font-medium border-l border-gray-300 transition-colors ${
                      filters.source === 'PD' 
                        ? 'bg-green-600 text-white' 
                        : 'bg-white text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    PD
                  </button>
                  <button
                    onClick={() => setFilters({ ...filters, source: 'MD' })}
                    className={`px-4 py-2 text-sm font-medium border-l border-gray-300 transition-colors ${
                      filters.source === 'MD' 
                        ? 'bg-purple-600 text-white' 
                        : 'bg-white text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    MD
                  </button>
                </div>

                <select
                  value={filters.status}
                  onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                  className="px-3 py-2 text-sm border border-gray-300 rounded-lg"
                >
                  <option value="all">All Status</option>
                  <option value="COMPLETED">Completed</option>
                  <option value="IN_PROGRESS">In Progress</option>
                  <option value="NOT_STARTED">Not Started</option>
                </select>

                <select
                  value={filters.module}
                  onChange={(e) => setFilters({ ...filters, module: e.target.value })}
                  className="px-3 py-2 text-sm border border-gray-300 rounded-lg"
                >
                  {uniqueModules.map(mod => (
                    <option key={mod} value={mod}>
                      {mod === 'all' ? 'All Modules' : mod}
                    </option>
                  ))}
                </select>

                <select
                  value={filters.owner}
                  onChange={(e) => setFilters({ ...filters, owner: e.target.value })}
                  className="px-3 py-2 text-sm border border-gray-300 rounded-lg"
                >
                  {uniqueOwners.map(owner => (
                    <option key={owner} value={owner}>
                      {owner === 'all' ? 'All Owners' : owner}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center space-x-2">
                <div className="text-sm text-gray-600">
                  Showing {filteredData.length} of {historyData.length} items
                </div>
              </div>
            </div>
          </Card>

          <Card>
            {loading ? (
              <div className="text-center py-8 text-gray-600">Loading history...</div>
            ) : filteredData.length === 0 ? (
              <div className="text-center py-8 text-gray-600">No activity found</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full table-auto">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left text-xs font-semibold text-gray-600 uppercase tracking-wider py-3 px-2 whitespace-nowrap">
                        Item ID
                      </th>
                      <th className="text-left text-xs font-semibold text-gray-600 uppercase tracking-wider py-3 px-2">
                        Description
                      </th>
                      <th className="text-left text-xs font-semibold text-gray-600 uppercase tracking-wider py-3 px-2 whitespace-nowrap">
                        Module
                      </th>
                      <th className="text-left text-xs font-semibold text-gray-600 uppercase tracking-wider py-3 px-2 whitespace-nowrap">
                        Owner
                      </th>
                      <th className="text-left text-xs font-semibold text-gray-600 uppercase tracking-wider py-3 px-2 whitespace-nowrap">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {filteredData.map((item) => (
                      <tr 
                        key={item.id} 
                        className="hover:bg-gray-50"
                      >
                        <td className="py-3 px-2 text-sm font-medium text-gray-900 whitespace-nowrap">
                          {item.itemId}
                        </td>
                        <td className="py-3 px-2 text-sm text-gray-600 max-w-xs">
                          <div className="truncate" title={item.description}>
                            {item.description}
                          </div>
                        </td>
                        <td className="py-3 px-2 text-sm text-gray-600 whitespace-nowrap">
                          {item.moduleName}
                        </td>
                        <td className="py-3 px-2 text-sm text-gray-600 whitespace-nowrap">
                          {item.owner}
                        </td>
                        <td className="py-3 px-2 whitespace-nowrap">
                          <StatusBadge status={item.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>
      </div>

      {selectedItem && (
        <HistoryDetail
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
        />
      )}
    </div>
  )
}
