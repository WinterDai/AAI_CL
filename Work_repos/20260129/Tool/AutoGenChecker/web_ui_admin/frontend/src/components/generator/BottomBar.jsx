import { useGenerationStore } from '@/store/generationStore'
import Button from '@/components/common/Button'
import ProgressBar from '@/components/workflow/ProgressBar'

const STEP_NAMES = [
  '', // 0 index placeholder
  'Configuration',
  'File Analysis',
  'README Generation',
  'README Review',
  'Code Implementation',
  'Self Check',
  'Testing',
  'Final Review',
  'Package'
]

export default function BottomBar() {
  const currentStep = useGenerationStore((s) => s.currentStep)
  const progress = useGenerationStore((s) => s.progress)
  const status = useGenerationStore((s) => s.status)
  const prevStep = useGenerationStore((s) => s.prevStep)
  const nextStep = useGenerationStore((s) => s.nextStep)

  const stepName = STEP_NAMES[currentStep] || 'Unknown'
  const statusMessage = status === 'running' 
    ? 'AI generating code (8s elapsed)' 
    : status === 'completed'
    ? 'Generation completed'
    : 'Ready'

  const handleBack = () => {
    console.log('Back button clicked')
    prevStep()
  }

  const handleContinue = () => {
    console.log('Continue button clicked')
    nextStep()
  }

  return (
    <div className="h-12 border-t border-gray-200 bg-white px-6 py-2">
      <div className="flex items-center justify-between">
        <div className="flex-1 max-w-2xl">
          <ProgressBar 
            currentStep={currentStep} 
            totalSteps={9}
            status={statusMessage}
          />
        </div>

        <div className="flex items-center space-x-2 ml-6">
          <Button
            variant="secondary"
            onClick={handleBack}
            disabled={currentStep === 1}
            className="text-xs px-3 py-1.5"
          >
            Back
          </Button>
          <Button
            onClick={handleContinue}
            disabled={currentStep === 9}
            className="text-xs px-3 py-1.5"
          >
            Continue
          </Button>
        </div>
      </div>
    </div>
  )
}
