/**
 * DeveloperSelector - 开发者选择下拉组件
 * 
 * 用于在 Header 中选择当前开发者
 * 选择后自动加载该开发者的任务列表
 */
import { useEffect, useState } from 'react'
import { useWorkflowStore } from '@/store/workflowStore'
import { getDashboardExcelSummary } from '@/api/endpoints'

export default function DeveloperSelector() {
  const { 
    currentDeveloper, 
    setCurrentDeveloper, 
  } = useWorkflowStore()

  const [excelDevelopers, setExcelDevelopers] = useState([])
  const [loading, setLoading] = useState(false)

  // 从 Excel 加载开发者列表
  useEffect(() => {
    const fetchExcelDevelopers = async () => {
      setLoading(true)
      try {
        const data = await getDashboardExcelSummary()
        if (data.developers) {
          // 提取开发者名字并排序
          const devNames = data.developers.map(d => d.name).sort()
          setExcelDevelopers(devNames)
        }
      } catch (error) {
        console.error('Failed to fetch developers from Excel:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchExcelDevelopers()
  }, [])

  const handleChange = (e) => {
    const developer = e.target.value || null
    setCurrentDeveloper(developer)
  }

  const handleAdminClick = () => {
    setCurrentDeveloper(null)
  }

  return (
    <div className="flex items-center gap-0">
      {/* Developer Dropdown */}
      <div className="relative inline-block">
        <select
          value={currentDeveloper || ''}
          onChange={handleChange}
          disabled={loading}
          className="text-xs border border-gray-300 rounded-l-md px-2 py-1 pr-6 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent min-w-[110px] cursor-pointer hover:border-gray-400 transition-colors appearance-none"
        >
          <option value="">{loading ? 'Loading...' : 'Developer'}</option>
          {excelDevelopers.map(dev => (
            <option key={dev} value={dev}>
              {dev}
            </option>
          ))}
        </select>
        <svg 
          className="w-3 h-3 text-gray-500 absolute right-1.5 top-1/2 -translate-y-1/2 pointer-events-none" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M19 9l-7 7-7-7" 
          />
        </svg>
      </div>
      
      {/* Admin Button */}
      <button
        onClick={handleAdminClick}
        className={`text-xs border border-l-0 rounded-r-md px-2 py-1 transition-colors ${
          !currentDeveloper 
            ? 'bg-primary text-white border-primary' 
            : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
        }`}
      >
        Admin
      </button>
    </div>
  )
}
