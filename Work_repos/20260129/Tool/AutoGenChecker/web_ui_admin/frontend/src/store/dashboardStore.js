import { create } from 'zustand'

const API_BASE = 'http://localhost:8000'

/**
 * Dashboard data cache store
 * Caches developers, activities, stats to avoid repeated API calls
 */
export const useDashboardStore = create((set, get) => ({
  // Cached data
  developers: [],
  activities: [],
  stats: {
    total_developers: 0,
    active_developers: 0,
    completed_today: 0,
    total_commits_today: 0
  },
  
  // Loading states
  loadingDevelopers: false,
  loadingActivities: false,
  loadingStats: false,
  
  // Cache metadata
  lastFetched: null,
  isLoaded: false,
  
  // Cache TTL: 2 minutes for dashboard data
  CACHE_TTL: 2 * 60 * 1000,

  // Check if cache is valid
  isCacheValid: () => {
    const { isLoaded, lastFetched, CACHE_TTL } = get()
    if (!isLoaded || !lastFetched) return false
    return Date.now() - lastFetched < CACHE_TTL
  },

  // Fetch all dashboard data
  fetchAll: async (force = false) => {
    const { isCacheValid, loadingDevelopers, loadingActivities, loadingStats } = get()
    
    // Return if cache is valid and not forced
    if (!force && isCacheValid()) {
      console.log('📦 Using cached dashboard data')
      return
    }
    
    // Prevent duplicate requests
    if (loadingDevelopers || loadingActivities || loadingStats) {
      return
    }

    set({ 
      loadingDevelopers: true, 
      loadingActivities: true, 
      loadingStats: true 
    })

    try {
      // Fetch all in parallel
      const [developersRes, activitiesRes, statsRes] = await Promise.all([
        fetch(`${API_BASE}/api/dashboard/developers`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/api/dashboard/activity?limit=10`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/api/dashboard/stats`).then(r => r.json()).catch(() => ({}))
      ])

      set({
        developers: developersRes,
        activities: activitiesRes,
        stats: statsRes,
        loadingDevelopers: false,
        loadingActivities: false,
        loadingStats: false,
        lastFetched: Date.now(),
        isLoaded: true
      })

      console.log('✅ Dashboard data loaded')
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      set({
        loadingDevelopers: false,
        loadingActivities: false,
        loadingStats: false
      })
    }
  },

  // Force refresh
  refresh: async () => {
    console.log('🔄 Refreshing dashboard data...')
    
    // First, trigger git fetch for all workspaces
    try {
      const refreshRes = await fetch(`${API_BASE}/api/dashboard/refresh`, {
        method: 'POST'
      })
      const refreshData = await refreshRes.json()
      console.log('✅ Git fetch completed:', refreshData.message)
    } catch (error) {
      console.warn('⚠️ Git fetch failed:', error)
      // Continue anyway to refresh data
    }
    
    // Then reload all data
    set({ lastFetched: null })
    return get().fetchAll(true)
  },

  // Clear cache
  clearCache: () => set({
    developers: [],
    activities: [],
    stats: {
      total_developers: 0,
      active_developers: 0,
      completed_today: 0,
      total_commits_today: 0
    },
    lastFetched: null,
    isLoaded: false
  })
}))
