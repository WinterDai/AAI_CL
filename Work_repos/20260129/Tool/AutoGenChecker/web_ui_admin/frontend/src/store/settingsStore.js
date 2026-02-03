import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// Default settings for JEDAI LLM integration
const DEFAULT_SETTINGS = {
  // LLM Configuration
  llmProvider: 'jedai',
  llmModel: 'claude-sonnet-4',
  
  // Generation Settings  
  maxRetryAttempts: 3,
  autoSave: true,
  
  // UI Settings
  darkMode: false,
}

export const useSettingsStore = create(
  persist(
    (set, get) => ({
      // Settings object
      settings: { ...DEFAULT_SETTINGS },
      
      // Loading state
      isLoading: false,
      lastSyncTime: null,
      
      // Actions
      updateSettings: (newSettings) => {
        set({ 
          settings: { ...get().settings, ...newSettings },
          lastSyncTime: new Date().toISOString()
        })
      },
      
      // Update single setting
      setSetting: (key, value) => {
        set({ 
          settings: { ...get().settings, [key]: value },
          lastSyncTime: new Date().toISOString()
        })
      },
      
      // Get single setting
      getSetting: (key) => get().settings[key],
      
      // Get LLM config for API calls
      getLLMConfig: () => {
        const { llmProvider, llmModel } = get().settings
        return { llmProvider, llmModel }
      },
      
      // Get generation config
      getGenerationConfig: () => {
        const { maxRetryAttempts, autoSave } = get().settings
        return { maxRetryAttempts, autoSave }
      },
      
      // Sync with backend
      setLoading: (isLoading) => set({ isLoading }),
      
      reset: () => set({
        settings: { ...DEFAULT_SETTINGS },
        lastSyncTime: new Date().toISOString()
      }),
    }),
    {
      name: 'autogenchecker-settings',
      version: 3, // Bump version for simplified settings
    }
  )
)
