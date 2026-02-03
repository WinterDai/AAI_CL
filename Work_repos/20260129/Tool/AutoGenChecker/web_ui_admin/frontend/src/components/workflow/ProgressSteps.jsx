import clsx from 'clsx'
import { useGenerationStore } from '@/store/generationStore'

export default function ProgressSteps({ currentStep, steps, onStepClick }) {
  // Check if project is locked (Step 1 saved)
  const project = useGenerationStore((s) => s.project)
  const configSaved = project.locked
  
  const defaultSteps = [
    { id: 1, name: 'Configuration' },
    { id: 2, name: 'File Analysis' },
    { id: 3, name: 'README' },
    { id: 4, name: 'Review' },
    { id: 5, name: 'Implementation' },
    { id: 6, name: 'Self Check' },
    { id: 7, name: 'Testing' },
    { id: 8, name: 'Final Review' },
    { id: 9, name: 'Package' }
  ]

  const stepsToRender = steps || defaultSteps

  const getStepStatus = (stepId) => {
    if (stepId < currentStep) return 'completed'
    if (stepId === currentStep) return 'active'
    return 'pending'
  }
  
  const handleStepClick = (stepId) => {
    // Step 1 is always accessible
    if (stepId === 1) {
      onStepClick?.(stepId)
      return
    }
    
    // For other steps, check if configuration is saved
    if (!configSaved) {
      alert('⚠️ Please save your configuration in Step 1 first before proceeding to other steps.')
      return
    }
    
    onStepClick?.(stepId)
  }

  return (
    <div className="space-y-1.5">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
        Workflow Progress
      </h3>
      
      {stepsToRender.map((step) => {
        const status = getStepStatus(step.id)
        const isDisabled = step.id > 1 && !configSaved
        
        return (
          <button
            key={step.id}
            onClick={() => handleStepClick(step.id)}
            disabled={isDisabled}
            className={clsx(
              'w-full flex items-center space-x-2 py-1.5 transition-colors text-left',
              status === 'active' && 'bg-gray-50 -mx-2 px-2 rounded',
              isDisabled && 'opacity-50 cursor-not-allowed',
              !isDisabled && onStepClick && 'hover:bg-gray-100 cursor-pointer',
              !onStepClick && 'cursor-default'
            )}
          >
            {/* Status Indicator */}
            <div className="flex-shrink-0">
              {status === 'completed' ? (
                <div className="w-1.5 h-1.5 rounded-full bg-success" />
              ) : status === 'active' ? (
                <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse-dot" />
              ) : isDisabled ? (
                <div className="w-1.5 h-1.5 rounded-full bg-gray-200" />
              ) : (
                <div className="w-1.5 h-1.5 rounded-full bg-gray-300" />
              )}
            </div>
            
            {/* Step Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-1.5">
                <span className="text-xs text-gray-500">
                  Step {step.id}
                </span>
                <span className={clsx(
                  'text-xs truncate',
                  status === 'active' 
                    ? 'text-gray-900 font-medium' 
                    : 'text-gray-600',
                  isDisabled && 'text-gray-400'
                )}>
                  {step.name}
                </span>
                {isDisabled && (
                  <svg className="w-2.5 h-2.5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                  </svg>
                )}
              </div>
            </div>
          </button>
        )
      })}
    </div>
  )
}
