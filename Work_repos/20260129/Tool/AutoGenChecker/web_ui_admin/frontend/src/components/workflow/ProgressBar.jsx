export default function ProgressBar({ currentStep, totalSteps = 9, status }) {
  const progress = Math.round((currentStep / totalSteps) * 100)

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-900 font-medium">
          Step {currentStep} of {totalSteps}
        </span>
        <span className="text-gray-600">
          {progress}%
        </span>
      </div>
      
      <div className="w-full bg-gray-200 rounded-full h-1">
        <div
          className="bg-primary h-1 rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
      
      {status && (
        <div className="text-sm text-gray-600">
          {status}
        </div>
      )}
    </div>
  )
}
