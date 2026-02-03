import apiClient from './client'

// Generation API
export const generationApi = {
  start: (data) => apiClient.post('/api/generation/start', data),
  getStatus: (itemId) => apiClient.get(`/api/generation/status/${itemId}`),
  continue: (itemId) => apiClient.post(`/api/generation/${itemId}/continue`),
  save: (itemId, data) => apiClient.post(`/api/generation/${itemId}/save`, data),
  getProgress: (itemId) => apiClient.get(`/api/generation/${itemId}/progress`),
}

// History API
export const historyApi = {
  list: (params) => apiClient.get('/api/history/list', { params }),
  getDetail: (historyId) => apiClient.get(`/api/history/${historyId}`),
  getLogs: (historyId) => apiClient.get(`/api/history/${historyId}/logs`),
  getCode: (historyId) => apiClient.get(`/api/history/${historyId}/code`),
  getReadme: (historyId) => apiClient.get(`/api/history/${historyId}/readme`),
  getYaml: (historyId) => apiClient.get(`/api/history/${historyId}/yaml`),
  getTests: (historyId) => apiClient.get(`/api/history/${historyId}/tests`),
}

// Templates API
export const templatesApi = {
  list: (params) => apiClient.get('/api/templates/list', { params }),
  getDetail: (templateId) => apiClient.get(`/api/templates/${templateId}`),
  create: (data) => apiClient.post('/api/templates/create', data),
  delete: (templateId) => apiClient.delete(`/api/templates/${templateId}`),
}

// Settings API
export const settingsApi = {
  get: () => apiClient.get('/api/settings/'),
  update: (data) => apiClient.put('/api/settings/', data),
  getLLMModels: (provider) => apiClient.get('/api/settings/llm-models', { params: { provider } }),
}

// Dashboard API
export const dashboardApi = {
  getDevelopers: async () => {
    const response = await apiClient.get('/api/dashboard/developers')
    return response.data
  },
  getActivity: async (limit = 100) => {
    const response = await apiClient.get('/api/dashboard/activity', { params: { limit } })
    return response.data
  },
  getStats: async () => {
    const response = await apiClient.get('/api/dashboard/stats')
    return response.data
  },
  getItems: async () => {
    const response = await apiClient.get('/api/dashboard/items')
    return response.data
  },
  getExcelSummary: async () => {
    const response = await apiClient.get('/api/dashboard/excel-summary')
    return response.data
  },
}

// Export individual functions for convenience
export const getDashboardDevelopers = () => dashboardApi.getDevelopers()
export const getDashboardActivity = (limit) => dashboardApi.getActivity(limit)
export const getDashboardStats = () => dashboardApi.getStats()
export const getDashboardItems = () => dashboardApi.getItems()
export const getDashboardExcelSummary = () => dashboardApi.getExcelSummary()

export default {
  generation: generationApi,
  history: historyApi,
  templates: templatesApi,
  settings: settingsApi,
  dashboard: dashboardApi,
}
