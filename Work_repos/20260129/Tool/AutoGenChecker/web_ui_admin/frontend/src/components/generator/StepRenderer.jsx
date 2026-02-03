import Step1Configuration from './steps/Step1Configuration'
import Step2FileAnalysis from './steps/Step2FileAnalysis'
import Step3README from './steps/Step3README'
import Step4Review from './steps/Step4Review'
import Step5Code from './steps/Step5Code'
import Step6SelfCheck from './steps/Step6SelfCheck'
import Step7Testing from './steps/Step7Testing'
import Step8FinalReview from './steps/Step8FinalReview'
import Step9Package from './steps/Step9Package'

export default function StepRenderer({ currentStep, itemId }) {
  console.log('🎯 StepRenderer rendering:', { currentStep, itemId })
  
  switch (currentStep) {
    case 1:
      return <Step1Configuration itemId={itemId} />
    case 2:
      return <Step2FileAnalysis itemId={itemId} />
    case 3:
      return <Step3README itemId={itemId} />
    case 4:
      return <Step4Review itemId={itemId} />
    case 5:
      return <Step5Code itemId={itemId} />
    case 6:
      return <Step6SelfCheck itemId={itemId} />
    case 7:
      return <Step7Testing itemId={itemId} />
    case 8:
      return <Step8FinalReview itemId={itemId} />
    case 9:
      return <Step9Package itemId={itemId} />
    default:
      return <div className="p-8">Invalid step</div>
  }
}
