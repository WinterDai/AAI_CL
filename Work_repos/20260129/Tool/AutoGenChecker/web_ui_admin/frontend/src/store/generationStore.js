import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

export const useGenerationStore = create(
  persist(
    (set, get) => ({
      // ============ 核心项目配置（Step1 Save 后锁定）============
      // 这是整个会话的"锚点"，所有步骤都使用这个配置
      project: {
        module: '',
        itemId: '',
        yamlConfig: null,
        locked: false,  // true = Step1 已 Save，所有步骤使用此配置
      },
      
      // ============ 当前步骤 ============
      currentStep: 1,
      progress: 0,
      status: 'idle', // idle | running | paused | completed | failed
      
      // Resume status from backend
      resumeStatus: null,
      
      // Step completion status
      stepStates: {
        1: 'idle',
        2: 'idle',
        3: 'idle',
        4: 'idle',
        5: 'idle',
        6: 'idle',
        7: 'idle',
        8: 'idle',
        9: 'idle'
      },
      
      // ============ 各步骤产出 ============
      fileAnalysis: [],      // Step2 产出
      generatedReadme: '',   // Step3 产出
      generatedCode: '',     // Step5 产出
      testResults: [],       // Step7 产出
      generatedYaml: '',
      
      // ============ 各步骤运行状态 ============
      step2IsAnalyzing: false,
      step3IsGenerating: false,
      step3GenerationLogs: [],
      step5IsGenerating: false,
      step5GenerationLogs: [],
      step6IsChecking: false,
      step6CheckLogs: [],
      step7IsRunning: false,
      step7TestLogs: [],
      step8IsProcessing: false,
      step9IsPackaging: false,
      
      // ============ 辅助状态 ============
      config: {},
      hints: '',
      hintsHistory: [],
      itemConfig: null,
      
      // Step1 临时编辑状态（保存前的草稿）
      step1Draft: {
        selectedModule: '',
        selectedItem: '',
        yamlData: null,
        editableYaml: '',
        modules: [],
        items: []
      },
      
      // ============ 核心 Actions ============
      
      // 保存项目配置（Step1 Save 按钮）
      // 这会"锁定"项目，后续所有步骤都使用此配置
      saveProject: (module, itemId, yamlConfig) => {
        console.log('🔒 Project locked:', { module, itemId })
        set({
          project: {
            module,
            itemId,
            yamlConfig,
            locked: true
          },
          stepStates: {
            ...get().stepStates,
            1: 'completed'
          }
        })
      },
      
      // 解锁项目（允许在 Step1 重新选择）
      unlockProject: () => {
        console.log('🔓 Project unlocked')
        set((state) => ({
          project: {
            ...state.project,
            locked: false
          }
        }))
      },
      
      // 切换项目（清空所有步骤数据，重新开始）
      switchProject: () => {
        console.log('🔄 Switching project - clearing all data')
        get().reset()
      },
      
      // 设置当前步骤
      setCurrentStep: (step) => {
        const { project } = get()
        
        // Step 1 总是可以访问
        if (step === 1) {
          set({ currentStep: 1, progress: Math.round((1 / 9) * 100) })
          return true
        }
        
        // 其他步骤需要项目已锁定
        if (!project.locked) {
          console.warn('⚠️ Cannot go to step', step, '- project not saved')
          return false
        }
        
        set({ 
          currentStep: step,
          progress: Math.round((step / 9) * 100)
        })
        return true
      },
      
      setStatus: (status) => set({ status }),
      
      setGeneratedCode: (code) => set({ generatedCode: code }),
      
      setGeneratedReadme: (readme) => set({ generatedReadme: readme }),
      
      setGeneratedYaml: (yaml) => set({ generatedYaml: yaml }),
      
      setFileAnalysis: (analysis) => set({ fileAnalysis: analysis }),
      
      setTestResults: (results) => set({ testResults: results }),
      
      setConfig: (config) => set({ config }),
      
      setItemConfig: (itemConfig) => set({ itemConfig }),
      
      setHints: (hints) => set({ hints }),
      
      setHintsHistory: (hintsHistory) => set({ hintsHistory }),
      
      // Step2 state actions
      setStep2IsAnalyzing: (isAnalyzing) => set({ step2IsAnalyzing: isAnalyzing }),
      
      // Step3 state actions
      setStep3IsGenerating: (isGenerating) => set({ step3IsGenerating: isGenerating }),
      
      setStep3GenerationLogs: (logs) => set({ step3GenerationLogs: logs }),
      
      addStep3Log: (message, level = 'info') => {
        const timestamp = new Date().toLocaleTimeString()
        set((state) => ({
          step3GenerationLogs: [...state.step3GenerationLogs, { timestamp, message, level }]
        }))
      },
      
      // Step5 state actions
      setStep5IsGenerating: (isGenerating) => set({ step5IsGenerating: isGenerating }),
      
      setStep5GenerationLogs: (logs) => set({ step5GenerationLogs: logs }),
      
      addStep5Log: (message) => {
        set((state) => ({
          step5GenerationLogs: [...state.step5GenerationLogs, message]
        }))
      },
      
      // Step6 state actions
      setStep6IsChecking: (isChecking) => set({ step6IsChecking: isChecking }),
      
      setStep6CheckLogs: (logs) => set({ step6CheckLogs: logs }),
      
      addStep6Log: (message) => {
        set((state) => ({
          step6CheckLogs: [...state.step6CheckLogs, message]
        }))
      },
      
      // Step7 state actions
      setStep7IsRunning: (isRunning) => set({ step7IsRunning: isRunning }),
      
      setStep7TestLogs: (logs) => set({ step7TestLogs: logs }),
      
      addStep7Log: (message) => {
        set((state) => ({
          step7TestLogs: [...state.step7TestLogs, message]
        }))
      },
      
      // Step8 state actions
      setStep8IsProcessing: (isProcessing) => set({ step8IsProcessing: isProcessing }),
      
      // Step9 state actions
      setStep9IsPackaging: (isPackaging) => set({ step9IsPackaging: isPackaging }),
      
      // 设置步骤完成状态
      setStepState: (step, state) => set((prev) => ({
        stepStates: { ...prev.stepStates, [step]: state }
      })),
      
      // Resume 状态
      setResumeStatus: (resumeStatus) => set({ resumeStatus }),
      
      // Step1 草稿状态
      setStep1Draft: (draft) => set((state) => ({
        step1Draft: { ...state.step1Draft, ...draft }
      })),
      
      // ============ 兼容旧代码的方法 ============
      // 这些方法保持向后兼容，内部使用新的 project 结构
      
      // 获取 step1State（兼容旧代码）
      getStep1State: () => {
        const state = get()
        return {
          selectedModule: state.project.locked ? state.project.module : state.step1Draft.selectedModule,
          selectedItem: state.project.locked ? state.project.itemId : state.step1Draft.selectedItem,
          yamlData: state.project.locked ? state.project.yamlConfig : state.step1Draft.yamlData,
          editableYaml: state.step1Draft.editableYaml,
          modules: state.step1Draft.modules,
          items: state.step1Draft.items
        }
      },
      
      setStep1State: (step1State) => set((state) => ({
        step1Draft: { ...state.step1Draft, ...step1State }
      })),
      
      // yamlConfig 兼容方法
      getYamlConfig: () => get().project.yamlConfig,
      
      setYamlConfig: (yamlConfig) => set((state) => ({
        project: { ...state.project, yamlConfig }
      })),
      
      // module 和 itemId 兼容方法
      getModule: () => get().project.module,
      getItemId: () => get().project.itemId,
      isProjectLocked: () => get().project.locked,

      nextStep: () => {
        const { currentStep, project } = get()
        if (!project.locked && currentStep === 1) {
          console.warn('⚠️ Please save configuration before proceeding')
          return false
        }
        if (currentStep < 9) {
          set({ 
            currentStep: currentStep + 1,
            progress: Math.round(((currentStep + 1) / 9) * 100)
          })
          return true
        }
        return false
      },
      
      prevStep: () => {
        const { currentStep } = get()
        if (currentStep > 1) {
          set({ 
            currentStep: currentStep - 1,
            progress: Math.round(((currentStep - 1) / 9) * 100)
          })
          return true
        }
        return false
      },
      
      reset: () => set({
        project: {
          module: '',
          itemId: '',
          yamlConfig: null,
          locked: false
        },
        currentStep: 1,
        progress: 0,
        status: 'idle',
        resumeStatus: null,
        stepStates: {
          1: 'idle', 2: 'idle', 3: 'idle', 4: 'idle', 5: 'idle',
          6: 'idle', 7: 'idle', 8: 'idle', 9: 'idle'
        },
        generatedCode: '',
        generatedReadme: '',
        generatedYaml: '',
        fileAnalysis: [],
        testResults: [],
        config: {},
        hints: '',
        hintsHistory: [],
        itemConfig: null,
        step2IsAnalyzing: false,
        step3IsGenerating: false,
        step3GenerationLogs: [],
        step5IsGenerating: false,
        step5GenerationLogs: [],
        step6IsChecking: false,
        step6CheckLogs: [],
        step7IsRunning: false,
        step7TestLogs: [],
        step8IsProcessing: false,
        step9IsPackaging: false,
        step1Draft: {
          selectedModule: '',
          selectedItem: '',
          yamlData: null,
          editableYaml: '',
          modules: [],
          items: []
        },
      }),
    }),
    {
      name: 'autogen-generation-storage',
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({
        // 持久化核心项目配置
        project: state.project,
        currentStep: state.currentStep,
        stepStates: state.stepStates,
        step1Draft: state.step1Draft,
        
        // 持久化各步骤产出
        generatedReadme: state.generatedReadme,
        generatedCode: state.generatedCode,
        generatedYaml: state.generatedYaml,
        fileAnalysis: state.fileAnalysis,
        testResults: state.testResults,
        
        // 持久化各步骤运行状态（用于页面导航）
        step2IsAnalyzing: state.step2IsAnalyzing,
        step3IsGenerating: state.step3IsGenerating,
        step3GenerationLogs: state.step3GenerationLogs,
        step5IsGenerating: state.step5IsGenerating,
        step5GenerationLogs: state.step5GenerationLogs,
        step6IsChecking: state.step6IsChecking,
        step6CheckLogs: state.step6CheckLogs,
        step7IsRunning: state.step7IsRunning,
        step7TestLogs: state.step7TestLogs,
        step8IsProcessing: state.step8IsProcessing,
        step9IsPackaging: state.step9IsPackaging,
        
        // 其他需要持久化的状态
        itemConfig: state.itemConfig,
        hints: state.hints,
        hintsHistory: state.hintsHistory,
      }),
    }
  )
)
