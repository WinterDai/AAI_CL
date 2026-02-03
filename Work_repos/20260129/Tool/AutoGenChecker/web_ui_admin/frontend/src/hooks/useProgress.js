import { useEffect } from 'use'
import { useGenerationStore } from '@/store/generationStore'

export function useProgress(itemId) {
  const setCurrentStep = useGenerationStore((s) => s.setCurrentStep)
  const setStatus = useGenerationStore((s) => s.setStatus)
  
  useEffect(() => {
    if (!itemId) return

    // Establish SSE connection
    const eventSource = new EventSource(
      `/api/generation/stream/progress?item_id=${itemId}`
    )

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.step) {
        setCurrentStep(data.step)
      }
      
      if (data.status === 'completed') {
        setStatus('completed')
        eventSource.close()
      }
    }

    eventSource.onerror = () => {
      console.error('SSE connection error')
      eventSource.close()
    }

    return () => {
      eventSource.close()
    }
  }, [itemId, setCurrentStep, setStatus])
}
