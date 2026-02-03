import { useParams, useNavigate, useLocation, useSearchParams } from 'react-router-dom'
import { useEffect } from 'react'
import { useGenerationStore } from '@/store/generationStore'
import LeftSidebar from '@/components/generator/LeftSidebar'
import BottomBar from '@/components/generator/BottomBar'
import StepRenderer from '@/components/generator/StepRenderer'

export default function Generator() {
  const { itemId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()

  const moduleParam = searchParams.get('module')
  const itemParam = searchParams.get('item')
  
  const currentStep = useGenerationStore((s) => s.currentStep)
  const setCurrentStep = useGenerationStore((s) => s.setCurrentStep)
  const setStep1Draft = useGenerationStore((s) => s.setStep1Draft)
  
  // Initialize on mount
  useEffect(() => {
    const finalItemId = itemParam || itemId || ''
    const finalModule = moduleParam || ''
    const stepMatch = location.pathname.match(/\/generate\/step(\d+)/)
    const targetStep = stepMatch ? parseInt(stepMatch[1], 10) : 1

    console.log('🔧 Generator mounted:', {
      itemId,
      itemParam,
      moduleParam,
      finalItemId,
      finalModule,
      pathname: location.pathname,
      targetStep
    })

    // 设置当前步骤
    setCurrentStep(targetStep)
    
    // 如果 URL 有 module/item 参数，设置到草稿状态
    if (finalModule || finalItemId) {
      setStep1Draft({
        selectedModule: finalModule,
        selectedItem: finalItemId
      })
    }
  }, [itemId, moduleParam, itemParam, location.pathname, setCurrentStep, setStep1Draft])

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="h-10 border-b border-gray-200 bg-white px-6 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => navigate('/')}
            className="text-xs text-gray-600 hover:text-gray-900 flex items-center"
          >
            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Dashboard
          </button>
          <div className="text-xs text-gray-900 font-medium">
            {itemId || 'New Generation'}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button className="text-xs text-gray-600 hover:text-gray-900">
            Save
          </button>
          <button className="text-xs text-gray-600 hover:text-gray-900">
            Export
          </button>
          <button className="text-gray-600 hover:text-gray-900">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <LeftSidebar itemId={itemId} />
        
        {/* Main Area */}
        <div className="flex-1 overflow-auto custom-scrollbar">
          <StepRenderer currentStep={currentStep} itemId={itemId} />
        </div>
      </div>

      {/* Bottom Bar */}
      <BottomBar />
    </div>
  )
}
