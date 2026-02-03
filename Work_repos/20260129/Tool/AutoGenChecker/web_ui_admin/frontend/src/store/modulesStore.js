import { create } from 'zustand'

/**
 * Global modules cache store
 * Prevents redundant API calls across pages (Dashboard, Modules, Generator)
 */
export const useModulesStore = create((set, get) => ({
  // Cached modules data
  modules: [],
  isLoaded: false,
  isLoading: false,
  lastFetched: null,
  error: null,

  // Cache TTL: 5 minutes (modules rarely change during a session)
  CACHE_TTL: 5 * 60 * 1000,

  // Check if cache is valid
  isCacheValid: () => {
    const { isLoaded, lastFetched, CACHE_TTL } = get()
    if (!isLoaded || !lastFetched) return false
    return Date.now() - lastFetched < CACHE_TTL
  },

  // Fetch modules (with caching)
  fetchModules: async (force = false) => {
    const { isLoading, isCacheValid, modules } = get()

    // Return cached data if valid and not forced
    if (!force && isCacheValid()) {
      return modules
    }

    // Prevent duplicate requests
    if (isLoading) {
      // Wait for ongoing request
      return new Promise((resolve) => {
        const checkLoading = setInterval(() => {
          const state = get()
          if (!state.isLoading) {
            clearInterval(checkLoading)
            resolve(state.modules)
          }
        }, 50)
      })
    }

    set({ isLoading: true, error: null })

    try {
      const response = await fetch('http://localhost:8000/api/step1/modules')
      if (!response.ok) throw new Error('Failed to fetch modules')
      
      const data = await response.json()
      
      set({
        modules: data,
        isLoaded: true,
        isLoading: false,
        lastFetched: Date.now(),
        error: null
      })

      console.log(`✅ Modules loaded: ${data.length} modules`)
      return data
    } catch (error) {
      console.error('Failed to load modules:', error)
      set({
        isLoading: false,
        error: error.message
      })
      return []
    }
  },

  // Force refresh
  refresh: () => get().fetchModules(true),

  // Get module by ID
  getModule: (moduleId) => {
    const { modules } = get()
    return modules.find(m => m.module_id === moduleId)
  },

  // Get items for a module
  getModuleItems: (moduleId) => {
    const module = get().getModule(moduleId)
    return module?.items || []
  },

  // Clear cache
  clearCache: () => set({
    modules: [],
    isLoaded: false,
    lastFetched: null,
    error: null
  })
}))
