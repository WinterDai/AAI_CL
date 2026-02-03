import { useState, useRef } from 'react'
import { useGenerationStore } from '@/store/generationStore'
import ProgressSteps from '@/components/workflow/ProgressSteps'

export default function LeftSidebar({ itemId }) {
  const currentStep = useGenerationStore((s) => s.currentStep)
  const setCurrentStep = useGenerationStore((s) => s.setCurrentStep)
  const project = useGenerationStore((s) => s.project)
  const step1Draft = useGenerationStore((s) => s.step1Draft)
  
  // 可调整宽度的状态
  const [sidebarWidth, setSidebarWidth] = useState(320) // 默认 320px (w-80)
  const [isResizing, setIsResizing] = useState(false)
  const sidebarRef = useRef(null)

  // Get real data from project (if locked) or step1Draft
  const selectedModule = project.locked ? project.module : step1Draft.selectedModule
  const selectedItem = project.locked ? project.itemId : step1Draft.selectedItem
  const yamlData = project.locked ? project.yamlConfig : step1Draft.yamlData
  
  // Extract configuration from YAML data
  const configData = {
    module: selectedModule,
    itemId: selectedItem,
    description: yamlData?.description || 'Not loaded',
    inputFiles: yamlData?.input_files || []
  }

  // Get hints history from store (synced from Step3)
  const hintsHistory = useGenerationStore((s) => s.hintsHistory) || []

  // 处理鼠标拖拽调整宽度
  const handleMouseDown = (e) => {
    setIsResizing(true)
    e.preventDefault()
  }

  const handleMouseMove = (e) => {
    if (!isResizing) return
    
    const newWidth = e.clientX
    // 限制最小 200px，最大 600px
    if (newWidth >= 200 && newWidth <= 600) {
      setSidebarWidth(newWidth)
    }
  }

  const handleMouseUp = () => {
    setIsResizing(false)
  }

  // 添加全局鼠标事件监听
  if (typeof window !== 'undefined') {
    window.onmousemove = handleMouseMove
    window.onmouseup = handleMouseUp
  }

  return (
    <div 
      ref={sidebarRef}
      className="relative border-r border-gray-200 bg-gray-50 overflow-auto custom-scrollbar"
      style={{ width: `${sidebarWidth}px`, minWidth: '200px', maxWidth: '600px' }}
    >
      <div className="p-4 space-y-4">
        {/* Workflow Progress */}
        <ProgressSteps currentStep={currentStep} onStepClick={setCurrentStep} />

        {/* Divider */}
        <div className="border-t border-gray-200" />

        {/* Configuration */}
        <div className="space-y-2">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Configuration
          </h3>
          
          <div className="space-y-2">
            <div>
              <div className="text-xs text-gray-500 mb-0.5">Module</div>
              <div className="text-xs text-gray-900">{configData.module || '(Select in Step 1)'}</div>
            </div>
            
            <div>
              <div className="text-xs text-gray-500 mb-0.5">Item ID</div>
              <div className="text-xs text-gray-900">{configData.itemId || '(Select in Step 1)'}</div>
            </div>
            
            <div>
              <div className="text-xs text-gray-500 mb-0.5">Description</div>
              <div className="text-xs text-gray-900">{configData.description}</div>
            </div>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-gray-200" />

        {/* Input Files */}
        <div className="space-y-2">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Input Files ({configData.inputFiles.length})
          </h3>
          
          <div className="space-y-1.5">
            {configData.inputFiles.length > 0 ? (
              configData.inputFiles.map((file, index) => {
                // Extract filename from path
                const fileName = typeof file === 'string' ? file.split('/').pop() : file
                return (
                  <div
                    key={index}
                    className="w-full px-2 py-1.5 text-xs text-gray-900 bg-white rounded border border-gray-200"
                    title={file}
                  >
                    <span className="truncate block">{fileName}</span>
                  </div>
                )
              })
            ) : (
              <div className="text-xs text-gray-400 italic">No input files loaded</div>
            )}
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-gray-200" />

        {/* Hints History */}
        <div className="space-y-2">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Hints History ({hintsHistory.length})
          </h3>
          
          <div className="space-y-1.5 max-h-40 overflow-auto">
            {hintsHistory.length > 0 ? (
              [...hintsHistory].reverse().map((hint, index) => (
                <div
                  key={index}
                  className="w-full px-2 py-1.5 text-xs bg-white rounded border border-gray-200 hover:border-gray-300 transition-colors"
                >
                  <div className="text-xs text-gray-500 mb-0.5">{hint.timestamp}</div>
                  <div className="text-xs text-gray-700 line-clamp-2">
                    {hint.hints?.substring(0, 80)}{hint.hints?.length > 80 ? '...' : ''}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-xs text-gray-400 italic">No hints saved yet</div>
            )}
          </div>
        </div>
      </div>
      
      {/* 可拖拽的分隔条 */}
      <div
        className={`absolute top-0 right-0 w-1 h-full cursor-col-resize hover:bg-blue-500 transition-colors ${
          isResizing ? 'bg-blue-500' : 'bg-transparent'
        }`}
        onMouseDown={handleMouseDown}
        title="拖拽调整宽度"
      />
    </div>
  )
}
