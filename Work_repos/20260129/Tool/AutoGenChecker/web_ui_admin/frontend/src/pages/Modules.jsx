import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Card from '@/components/common/Card'
import Button from '@/components/common/Button'
import StatusBadge from '@/components/common/StatusBadge'
import { useModulesStore } from '@/store/modulesStore'

export default function Modules() {
  const navigate = useNavigate()
  
  // Use cached modules from global store
  const { modules, isLoading: loading, fetchModules } = useModulesStore()
  
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [expandedModule, setExpandedModule] = useState(null)
  const [viewMode, setViewMode] = useState('grid') // 'grid' or 'list'

  // Fetch modules from cache on mount
  useEffect(() => {
    fetchModules()
  }, [fetchModules])

  // Categorize modules
  const getCategory = (moduleId) => {
    if (moduleId.includes('STA') || moduleId.includes('DCD')) return 'Timing'
    if (moduleId.includes('POWER') || moduleId.includes('EMIR')) return 'Power'
    if (moduleId.includes('PHYSICAL') || moduleId.includes('DRC') || moduleId.includes('LVS')) return 'Physical'
    if (moduleId.includes('SYNTHESIS') || moduleId.includes('LEC')) return 'Synthesis'
    if (moduleId.includes('LIBRARY') || moduleId.includes('TECHFILE')) return 'Setup'
    if (moduleId.includes('FINAL') || moduleId.includes('IPTAG')) return 'Final'
    if (moduleId.includes('INNOVUS') || moduleId.includes('IMPLEMENTATION')) return 'Implementation'
    if (moduleId.includes('CONSTRAINT') || moduleId.includes('CLP')) return 'Constraints'
    return 'Other'
  }

  const getCategoryColor = (category) => {
    const colors = {
      'Timing': 'bg-blue-100 text-blue-700',
      'Power': 'bg-red-100 text-red-700',
      'Physical': 'bg-green-100 text-green-700',
      'Synthesis': 'bg-purple-100 text-purple-700',
      'Setup': 'bg-gray-100 text-gray-700',
      'Final': 'bg-orange-100 text-orange-700',
      'Implementation': 'bg-indigo-100 text-indigo-700',
      'Constraints': 'bg-yellow-100 text-yellow-700',
      'Other': 'bg-gray-100 text-gray-600'
    }
    return colors[category] || colors['Other']
  }

  // Get unique categories
  const categories = ['All', ...new Set(modules.map(m => getCategory(m.module_id)))]

  // Filter modules
  const filteredModules = modules.filter(module => {
    const matchesSearch = module.module_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          module.module_name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = selectedCategory === 'All' || getCategory(module.module_id) === selectedCategory
    return matchesSearch && matchesCategory
  })

  // Stats
  const totalItems = modules.reduce((sum, m) => sum + m.item_count, 0)
  const categoryStats = categories.filter(c => c !== 'All').map(cat => ({
    name: cat,
    count: modules.filter(m => getCategory(m.module_id) === cat).length,
    items: modules.filter(m => getCategory(m.module_id) === cat).reduce((sum, m) => sum + m.item_count, 0)
  }))

  const handleStartGeneration = (moduleId, itemId = null) => {
    if (itemId) {
      navigate(`/generate/${itemId}`)
    } else {
      navigate('/generate/new', { state: { preselectedModule: moduleId } })
    }
  }

  if (loading) {
    return (
      <div className="min-h-full bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading modules...</p>
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
            <h1 className="text-2xl font-semibold text-gray-900">Module Browser</h1>
            <p className="mt-1 text-sm text-gray-600">
              Browse all {modules.length} checker modules with {totalItems} total items
            </p>
          </div>
          <div className="flex items-center gap-3">
            {/* View Mode Toggle */}
            <div className="flex items-center bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded ${viewMode === 'grid' ? 'bg-white shadow-sm' : 'text-gray-500'}`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded ${viewMode === 'list' ? 'bg-white shadow-sm' : 'text-gray-500'}`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            </div>
            <Button onClick={() => navigate('/generate/new')}>
              New Generation
            </Button>
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
          <Card>
            <div className="text-center py-1">
              <div className="text-2xl font-bold text-blue-600">{modules.length}</div>
              <div className="text-xs text-gray-500">Modules</div>
            </div>
          </Card>
          <Card>
            <div className="text-center py-1">
              <div className="text-2xl font-bold text-green-600">{totalItems}</div>
              <div className="text-xs text-gray-500">Total Items</div>
            </div>
          </Card>
          {categoryStats.slice(0, 6).map(stat => (
            <Card key={stat.name}>
              <div className="text-center py-1">
                <div className="text-lg font-bold text-gray-900">{stat.count}</div>
                <div className="text-xs text-gray-500 truncate">{stat.name}</div>
              </div>
            </Card>
          ))}
        </div>

        {/* Search and Filter */}
        <Card>
          <div className="flex flex-col md:flex-row md:items-center gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                placeholder="Search modules by name or ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Category Filter */}
            <div className="flex items-center gap-2 overflow-x-auto pb-1">
              {categories.map(cat => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-full whitespace-nowrap transition-colors ${
                    selectedCategory === cat
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {cat === 'All' ? 'All Categories' : cat}
                </button>
              ))}
            </div>
          </div>
        </Card>

        {/* Module Display */}
        {viewMode === 'grid' ? (
          // Grid View
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredModules.map(module => {
              const category = getCategory(module.module_id)
              const isExpanded = expandedModule === module.module_id
              
              return (
                <Card 
                  key={module.module_id} 
                  className={`hover:shadow-lg transition-all cursor-pointer ${isExpanded ? 'ring-2 ring-blue-500' : ''}`}
                  onClick={() => setExpandedModule(isExpanded ? null : module.module_id)}
                >
                  <div className="space-y-3">
                    {/* Header */}
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getCategoryColor(category)}`}>
                          {category}
                        </span>
                      </div>
                      <span className="text-sm font-semibold text-blue-600">{module.item_count} items</span>
                    </div>

                    {/* Module ID */}
                    <div>
                      <div className="text-sm font-semibold text-gray-900 truncate" title={module.module_id}>
                        {module.module_id}
                      </div>
                      <div className="text-xs text-gray-500 mt-0.5">{module.module_name}</div>
                    </div>

                    {/* Expanded Content */}
                    {isExpanded && (
                      <div className="pt-3 border-t border-gray-100 space-y-3">
                        {/* Items Preview */}
                        <div>
                          <div className="text-xs font-medium text-gray-500 mb-2">Items:</div>
                          <div className="max-h-32 overflow-y-auto space-y-1">
                            {module.items.slice(0, 10).map(item => (
                              <div 
                                key={item}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleStartGeneration(module.module_id, item)
                                }}
                                className="text-xs text-gray-600 hover:text-blue-600 hover:bg-blue-50 px-2 py-1 rounded cursor-pointer"
                              >
                                {item}
                              </div>
                            ))}
                            {module.items.length > 10 && (
                              <div className="text-xs text-gray-400 px-2">
                                +{module.items.length - 10} more...
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Action Button */}
                        <Button 
                          size="sm" 
                          className="w-full"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleStartGeneration(module.module_id)
                          }}
                        >
                          Start Generation
                        </Button>
                      </div>
                    )}
                  </div>
                </Card>
              )
            })}
          </div>
        ) : (
          // List View
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">Module</th>
                    <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">Category</th>
                    <th className="text-center py-3 px-4 text-xs font-medium text-gray-500 uppercase">Items</th>
                    <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">Sample Items</th>
                    <th className="text-right py-3 px-4 text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredModules.map(module => {
                    const category = getCategory(module.module_id)
                    return (
                      <tr key={module.module_id} className="hover:bg-gray-50">
                        <td className="py-3 px-4">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{module.module_id}</div>
                            <div className="text-xs text-gray-500">{module.module_name}</div>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getCategoryColor(category)}`}>
                            {category}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span className="text-sm font-semibold text-blue-600">{module.item_count}</span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex flex-wrap gap-1 max-w-md">
                            {module.items.slice(0, 3).map(item => (
                              <span 
                                key={item} 
                                className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded cursor-pointer hover:bg-blue-100 hover:text-blue-700"
                                onClick={() => handleStartGeneration(module.module_id, item)}
                              >
                                {item}
                              </span>
                            ))}
                            {module.items.length > 3 && (
                              <span className="text-xs text-gray-400">+{module.items.length - 3}</span>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Button 
                            size="sm" 
                            variant="secondary"
                            onClick={() => handleStartGeneration(module.module_id)}
                          >
                            Generate
                          </Button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* Empty State */}
        {filteredModules.length === 0 && (
          <div className="text-center py-12">
            <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-gray-500">No modules found matching your criteria</p>
            <button 
              onClick={() => { setSearchTerm(''); setSelectedCategory('All'); }}
              className="mt-2 text-blue-600 hover:text-blue-700 text-sm"
            >
              Clear filters
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
