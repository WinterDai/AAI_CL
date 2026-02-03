import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { generationApi } from '@/api/endpoints'
import { useGenerationStore } from '@/store/generationStore'

export function useGeneration(itemId) {
  const queryClient = useQueryClient()
  const setProject = useGenerationStore((s) => s.setProject)
  const setStatus = useGenerationStore((s) => s.setStatus)
  
  // Start generation
  const startMutation = useMutation({
    mutationFn: generationApi.start,
    onSuccess: (data) => {
      setProject(data.item_id, data.module)
      setStatus('running')
      queryClient.invalidateQueries(['generation', itemId])
    },
  })
  
  // Get status
  const statusQuery = useQuery({
    queryKey: ['generation', 'status', itemId],
    queryFn: () => generationApi.getStatus(itemId),
    enabled: !!itemId,
    refetchInterval: 2000, // Poll every 2 seconds
  })
  
  // Get progress
  const progressQuery = useQuery({
    queryKey: ['generation', 'progress', itemId],
    queryFn: () => generationApi.getProgress(itemId),
    enabled: !!itemId,
  })
  
  // Continue to next step
  const continueMutation = useMutation({
    mutationFn: () => generationApi.continue(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries(['generation', itemId])
    },
  })
  
  // Save progress
  const saveMutation = useMutation({
    mutationFn: (data) => generationApi.save(itemId, data),
  })
  
  return {
    start: startMutation.mutate,
    isStarting: startMutation.isPending,
    status: statusQuery.data,
    progress: progressQuery.data,
    continue: continueMutation.mutate,
    save: saveMutation.mutate,
  }
}
