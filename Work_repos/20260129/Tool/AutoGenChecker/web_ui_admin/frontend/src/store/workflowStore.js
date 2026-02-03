/**
 * Workflow Store - 管理工作流状态 (分发/开发/回收)
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const API_BASE = 'http://localhost:8000/api/workflow'

export const useWorkflowStore = create(
  persist(
    (set, get) => ({
      // ============================================
      // State
      // ============================================
      
      // 当前开发者
      currentDeveloper: null,
      developers: [],
      
      // 任务数据
      tasks: [],
      taskStats: null,
      loadingTasks: false,
      
      // 分发状态
      dispatchStatus: null,
      isDispatching: false,
      
      // 回收状态
      collectionPreview: null,
      collectionResults: null,
      isCollecting: false,
      
      // ============================================
      // Actions - Developer
      // ============================================
      
      setCurrentDeveloper: (developer) => {
        set({ currentDeveloper: developer })
        if (developer) {
          get().fetchMyTasks()
        }
      },
      
      fetchDevelopers: async () => {
        try {
          const res = await fetch(`${API_BASE}/dispatch/developers`)
          const data = await res.json()
          if (data.status === 'success') {
            set({ developers: data.developers })
          }
          return data
        } catch (error) {
          console.error('Failed to fetch developers:', error)
          return { status: 'error', error: error.message }
        }
      },
      
      // ============================================
      // Actions - Tasks (Development)
      // ============================================
      
      fetchMyTasks: async () => {
        const { currentDeveloper } = get()
        if (!currentDeveloper) return
        
        set({ loadingTasks: true })
        try {
          // Get tasks from Excel summary
          const res = await fetch('http://localhost:8000/api/dashboard/excel-summary')
          const data = await res.json()
          
          if (!data.developers) {
            throw new Error('No developers data')
          }
          
          // Get all items for current developer
          const itemsRes = await fetch('http://localhost:8000/api/dashboard/items')
          const itemsData = await itemsRes.json()
          
          // Filter items for current developer
          const myItems = itemsData.filter(item => item.owner === currentDeveloper)
          
          // Transform to task format
          const tasks = myItems.map(item => ({
            item_id: item.item_id,
            module: item.module_name,
            description: item.description,
            status: item.status,
            source: item.source
          }))
          
          // Calculate statistics
          const total = tasks.length
          const completed = tasks.filter(t => t.status === 'completed').length
          const in_progress = tasks.filter(t => t.status === 'in_progress').length
          const not_started = tasks.filter(t => t.status === 'not_started').length
          
          const taskStats = {
            total,
            completed,
            in_progress,
            not_started,
            progress_percent: total > 0 ? Math.round(completed / total * 100) : 0
          }
          
          set({ 
            tasks,
            taskStats
          })
          
          return { status: 'success', tasks, statistics: taskStats }
        } catch (error) {
          console.error('Failed to fetch tasks:', error)
          set({ tasks: [], taskStats: null })
          return { status: 'error', error: error.message }
        } finally {
          set({ loadingTasks: false })
        }
      },
      
      getTasksByModule: () => {
        const { tasks } = get()
        return tasks.reduce((acc, task) => {
          if (!acc[task.module]) {
            acc[task.module] = []
          }
          acc[task.module].push(task)
          return acc
        }, {})
      },
      
      // ============================================
      // Actions - Dispatch
      // ============================================
      
      createWorkspace: async (request) => {
        set({ isDispatching: true, dispatchStatus: null })
        try {
          const res = await fetch(`${API_BASE}/dispatch/create-workspace`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request)
          })
          const data = await res.json()
          set({ dispatchStatus: data })
          return data
        } catch (error) {
          console.error('Failed to create workspace:', error)
          const errorData = { status: 'error', error: error.message }
          set({ dispatchStatus: errorData })
          return errorData
        } finally {
          set({ isDispatching: false })
        }
      },
      
      getDeveloperAssignments: async (developerName) => {
        try {
          const res = await fetch(`${API_BASE}/dispatch/assignments/${developerName}`)
          const data = await res.json()
          return data
        } catch (error) {
          console.error('Failed to fetch assignments:', error)
          return { status: 'error', error: error.message }
        }
      },
      
      clearDispatchStatus: () => set({ dispatchStatus: null }),
      
      // ============================================
      // Actions - Collection
      // ============================================
      
      fetchCollectionPreview: async (developerName = null) => {
        const developer = developerName || get().currentDeveloper
        if (!developer) return
        
        try {
          const res = await fetch(`${API_BASE}/collect/preview/${developer}`)
          const data = await res.json()
          if (data.status === 'success') {
            set({ collectionPreview: data })
          }
          return data
        } catch (error) {
          console.error('Failed to fetch collection preview:', error)
          return { status: 'error', error: error.message }
        }
      },
      
      collectItems: async (items, developerName = null) => {
        const developer = developerName || get().currentDeveloper
        if (!developer) return { status: 'error', error: 'No developer selected' }
        
        set({ isCollecting: true, collectionResults: null })
        try {
          const res = await fetch(`${API_BASE}/collect/batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              developer_name: developer,
              items
            })
          })
          const data = await res.json()
          set({ collectionResults: data })
          return data
        } catch (error) {
          console.error('Failed to collect items:', error)
          const errorData = { status: 'error', error: error.message }
          set({ collectionResults: errorData })
          return errorData
        } finally {
          set({ isCollecting: false })
        }
      },
      
      collectSingleItem: async (module, itemId, developerName = null) => {
        const developer = developerName || get().currentDeveloper
        if (!developer) return { status: 'error', error: 'No developer selected' }
        
        try {
          const res = await fetch(`${API_BASE}/collect/item`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              developer_name: developer,
              module,
              item_id: itemId
            })
          })
          return await res.json()
        } catch (error) {
          console.error('Failed to collect item:', error)
          return { status: 'error', error: error.message }
        }
      },
      
      clearCollectionResults: () => set({ collectionResults: null }),
      
      // ============================================
      // Actions - Reset
      // ============================================
      
      reset: () => set({
        tasks: [],
        taskStats: null,
        dispatchStatus: null,
        collectionPreview: null,
        collectionResults: null
      })
    }),
    {
      name: 'workflow-storage',
      partialize: (state) => ({ 
        currentDeveloper: state.currentDeveloper 
      })
    }
  )
)
