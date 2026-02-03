import React, { useState, useEffect } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import Button from '../../common/Button';
import Card from '../../common/Card';
import { useGenerationStore } from '../../../store/generationStore';
import { useSettingsStore } from '../../../store/settingsStore';
import apiClient from '../../../api/client';

export default function Step5Code({ itemId }) {
  const { 
    generatedReadme,
    setGeneratedReadme,
    fileAnalysis,
    itemConfig,
    yamlConfig,
    generatedCode,
    setGeneratedCode,
    setCurrentStep,
    setStepState,
    // Step5 persistent state
    step5IsGenerating,
    setStep5IsGenerating,
    step5GenerationLogs,
    setStep5GenerationLogs,
    addStep5Log,
    // Use project state directly (locked after Step1 save)
    project,
    getStep1State
  } = useGenerationStore();
  
  // Get step1State using the getter (returns correct values based on lock status)
  const step1State = getStep1State();
  
  // Get settings for LLM config and retry attempts
  const settings = useSettingsStore((s) => s.settings);
  
  // Use store state for generation status (persists across navigation)
  const isGenerating = step5IsGenerating;
  const setIsGenerating = setStep5IsGenerating;
  // Ensure generationLog is always an array (handle corrupted persist state)
  const generationLog = Array.isArray(step5GenerationLogs) ? step5GenerationLogs : [];
  const setGenerationLog = setStep5GenerationLogs;
  
  const [isLoading, setIsLoading] = useState(true);
  const [isReloading, setIsReloading] = useState(false);
  const [viewMode, setViewMode] = useState('rendered'); // 'rendered' or 'raw'
  const [qualityScore, setQualityScore] = useState(0);
  const [warnings, setWarnings] = useState([]);
  const [readmeSource, setReadmeSource] = useState(''); // 'store' or 'file'

  // Get effective module and item_id
  // PRIORITY: project (locked) > step1State > props (URL param)
  // When project is locked (after Step1 Save), use project values
  const effectiveModule = project?.locked ? project.module : (step1State?.selectedModule || itemId);
  const effectiveItemId = project?.locked ? project.itemId : (step1State?.selectedItem || itemId);

  // Check for README and Code availability on mount (support resume from file)
  useEffect(() => {
    const checkAvailability = async () => {
      console.log('[Step5] checkAvailability called');
      console.log('[Step5]   project:', project);
      console.log('[Step5]   effectiveModule:', effectiveModule);
      console.log('[Step5]   effectiveItemId:', effectiveItemId);
      console.log('[Step5]   generatedReadme exists:', !!generatedReadme);
      console.log('[Step5]   generatedCode exists:', !!generatedCode);
      
      setIsLoading(true);
      
      // Check README availability
      if (!generatedReadme && effectiveModule && effectiveItemId) {
        try {
          console.log('[Step5] Loading README...');
          const response = await apiClient.post('/api/step3/load-readme', {
            module: effectiveModule,
            item_id: effectiveItemId
          });
          
          if (response.data.exists && response.data.readme) {
            console.log(`📂 Loaded README from file: ${response.data.path}`);
            console.log(`   Last modified: ${response.data.modified_time}`);
            setGeneratedReadme(response.data.readme);
            setReadmeSource('file');
          } else {
            console.log('[Step5] README not found:', response.data);
          }
        } catch (error) {
          console.log('No README file found, need to complete Step 3', error);
        }
      } else if (generatedReadme) {
        setReadmeSource('store');
      }
      
      // Check Code availability (load from file if not in store)
      if (!generatedCode && effectiveModule && effectiveItemId) {
        try {
          console.log('[Step5] Loading Code...');
          const response = await apiClient.post('/api/step5/load-code', {
            module: effectiveModule,
            item_id: effectiveItemId
          });
          
          console.log('[Step5] Load code response:', response.data);
          
          if (response.data.status === 'success' && response.data.exists) {
            console.log(`📂 Loaded Code from file: ${response.data.path}`);
            console.log(`   Last modified: ${response.data.modified_time}`);
            console.log(`   Lines: ${response.data.lines}`);
            setGeneratedCode(response.data.code);
            setQualityScore(response.data.quality_score || 0);
            setGenerationLog([
              `📂 Resumed from file: ${response.data.path}`,
              `   Modified: ${response.data.modified_time}`,
              `   Lines: ${response.data.lines}`,
            ]);
          } else {
            console.log('[Step5] Code not found or not exists');
          }
        } catch (error) {
          console.log('No Code file found, need to generate', error);
        }
      }
      
      setIsLoading(false);
    };
    
    checkAvailability();
  }, [effectiveModule, effectiveItemId, generatedReadme, generatedCode, setGeneratedReadme, setGeneratedCode]);

  const handleGenerateCode = async (regenerate = false) => {
    // Get effective config
    const effectiveConfig = itemConfig || yamlConfig;
    const effectiveAnalysis = fileAnalysis || [];
    
    if (!generatedReadme) {
      alert('README not found. Please complete Step 3 first.');
      return;
    }

    setIsGenerating(true);
    setGenerationLog([]);
    setWarnings([]);

    try {
      // Show initial status - will be replaced by backend's phases_log
      setGenerationLog([
        '─'.repeat(80),
        '[Step 5/9] 💻 Multi-Phase Code Generation',
        '─'.repeat(80),
        '',
        '📋 Preparing request...',
        `    Module: ${effectiveModule}`,
        `    Item: ${effectiveItemId}`,
        `    README: ${generatedReadme.length} chars`,
        `    Files: ${effectiveAnalysis.length} analyzed`,
        '',
        '🤖 Calling CLI CodeGenerationMixin...',
        '    ⏳ This uses the exact same logic as CLI Step 5',
        '    ⏳ Multi-phase generation may take 1-2 minutes...',
      ]);

      const response = await apiClient.post('/api/step5/generate-code', {
        module: effectiveModule,
        item_id: effectiveItemId,
        readme: generatedReadme,
        file_analysis: effectiveAnalysis,
        config: effectiveConfig,
        regenerate: regenerate,
        llm_provider: settings?.llmProvider || 'jedai',
        llm_model: settings?.llmModel || 'claude-sonnet-4',
        max_retry_attempts: settings?.maxRetryAttempts || 3
      });

      if (response.data.status === 'success') {
        setGeneratedCode(response.data.code);
        setQualityScore(response.data.quality_score || 0);
        setWarnings(response.data.warnings || []);
        
        // Mark Step 5 as completed so Step 6 knows it's ready
        setStepState(5, 'completed');
        
        // Use backend's phases_log if available
        if (response.data.phases_log && response.data.phases_log.length > 0) {
          setGenerationLog(response.data.phases_log);
        } else {
          // Fallback to simple completion message
          setGenerationLog(prev => [
            ...prev,
            '',
            '✅ Code generation complete!',
            `    Lines: ${response.data.lines}`,
            `    Quality: ${response.data.quality_score}/100`,
            response.data.saved_path ? `    💾 Saved to: ${response.data.saved_path}` : '',
          ].filter(Boolean));
        }
      } else {
        throw new Error(response.data.error || 'Code generation failed');
      }
    } catch (error) {
      console.error('Code generation failed:', error);
      setGenerationLog(prev => [...prev, '', `❌ Error: ${error.message}`]);
      alert(`Code generation failed: ${error.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  // Reload code from file (sync with VS Code changes)
  const handleReloadFromFile = async () => {
    if (!effectiveModule || !effectiveItemId) {
      alert('Module or Item ID not available');
      return;
    }

    setIsReloading(true);
    try {
      const response = await apiClient.post('/api/step5/load-code', {
        module: effectiveModule,
        item_id: effectiveItemId
      });

      if (response.data.status === 'success' && response.data.exists) {
        setGeneratedCode(response.data.code);
        setQualityScore(response.data.quality_score || 0);
        setGenerationLog(prev => [
          ...prev,
          '',
          `🔄 Reloaded from file: ${response.data.path}`,
          `    Modified: ${response.data.modified_time}`,
          `    Lines: ${response.data.lines}`,
        ]);
        alert(`✅ Code reloaded from file!\nModified: ${response.data.modified_time}`);
      } else {
        alert('No code file found on disk. Generate code first.');
      }
    } catch (error) {
      console.error('Reload failed:', error);
      alert(`Reload failed: ${error.message}`);
    } finally {
      setIsReloading(false);
    }
  };

  const handleProceed = () => {
    if (!generatedCode) {
      alert('Please generate code first');
      return;
    }
    setCurrentStep(6);
  };

  const handleBack = () => {
    setCurrentStep(4);
  };

  // Show loading state
  if (isLoading) {
    return (
      <Card>
        <div className="text-center py-8">
          <p className="text-gray-500">⏳ Checking README availability...</p>
        </div>
      </Card>
    );
  }

  // Show error if no README available
  if (!generatedReadme) {
    return (
      <Card>
        <div className="text-center py-8">
          <p className="text-gray-500 mb-4">README not found. Please complete Steps 1-4 first.</p>
          <p className="text-sm text-gray-400 mb-4">
            Module: {effectiveModule || 'Not selected'}<br/>
            Item: {effectiveItemId || 'Not selected'}
          </p>
          <Button onClick={() => setCurrentStep(3)}>
            Go to Step 3 (README Generation)
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="p-4 space-y-3">
      <Card>
        <div className="mb-3">
          <h2 className="text-base font-semibold mb-1">Step 5: Code Generation</h2>
          <p className="text-xs text-gray-600">
            Generate complete checker code using AI based on README specification
          </p>
          {readmeSource === 'file' && (
            <p className="text-xs text-blue-600 mt-1">
              📂 README loaded from file (resume mode)
            </p>
          )}
          <div className="mt-2 text-xs text-gray-500">
            <p><strong>Code Generation includes:</strong></p>
            <ul className="list-disc list-inside ml-2">
              <li>Header + Imports + Class definition</li>
              <li>_parse_input_files() method</li>
              <li>All 4 type execution methods (_execute_type1~4)</li>
              <li>Main block and complete implementation</li>
            </ul>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 mb-3">
          {!generatedCode ? (
            <Button
              onClick={() => handleGenerateCode(false)}
              disabled={isGenerating}
              size="xs"
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isGenerating ? '⏳ Generating...' : '🚀 Generate Code'}
            </Button>
          ) : (
            <>
              <Button
                onClick={handleProceed}
                disabled={isGenerating}
                size="xs"
                className="bg-green-600 hover:bg-green-700"
              >
                ✓ Proceed to Step 6
              </Button>
              <Button
                onClick={() => handleGenerateCode(true)}
                disabled={isGenerating}
                size="xs"
                className="bg-orange-600 hover:bg-orange-700"
              >
                ↻ Regenerate
              </Button>
              <Button
                onClick={handleReloadFromFile}
                disabled={isGenerating || isReloading}
                size="xs"
                className="bg-purple-600 hover:bg-purple-700"
                title="Reload code from file (sync VS Code changes)"
              >
                {isReloading ? '⏳ Reloading...' : '📂 Reload from File'}
              </Button>
            </>
          )}
          <Button
            onClick={handleBack}
            disabled={isGenerating}
            size="xs"
            variant="secondary"
          >
            ← Back to Step 4
          </Button>
        </div>

        {/* Generation Logs */}
        {generationLog.length > 0 && (
          <div className="mb-3">
            <h3 className="text-xs font-semibold text-gray-900 mb-1">Generation Log</h3>
            <div className="bg-white border border-gray-200 rounded-lg p-3 max-h-[150px] overflow-auto">
              <div className="space-y-0.5 font-mono text-xs">
                {generationLog.map((log, idx) => (
                  <div key={idx} className={
                    log.includes('❌') || log.includes('Error') ? 'text-red-600' :
                    log.includes('✅') || log.includes('Success') ? 'text-green-600' :
                    log.includes('⚠️') || log.includes('Warning') ? 'text-yellow-600' :
                    'text-gray-700'
                  }>
                    {log}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Quality Metrics */}
        {generatedCode && (
          <div className="mb-3 p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-xs">Code Quality Score</h3>
                <p className="text-sm font-bold text-blue-600">{qualityScore}/100</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-600">{generatedCode.split('\n').length} lines</p>
                {qualityScore >= 90 && <span className="text-green-600 font-semibold">Excellent</span>}
                {qualityScore >= 70 && qualityScore < 90 && <span className="text-blue-600 font-semibold">Good</span>}
                {qualityScore >= 50 && qualityScore < 70 && <span className="text-yellow-600 font-semibold">Acceptable</span>}
                {qualityScore < 50 && <span className="text-red-600 font-semibold">Needs Review</span>}
              </div>
            </div>
          </div>
        )}

        {/* Warnings */}
        {warnings.length > 0 && (
          <div className="mb-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <h3 className="font-semibold text-yellow-800 mb-1 text-xs">⚠️ Warnings:</h3>
            <ul className="list-disc list-inside text-xs text-yellow-700">
              {warnings.map((warning, idx) => (
                <li key={idx}>{warning}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Code Display */}
        {generatedCode && (
          <>
            {/* View Mode Toggle */}
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-semibold text-gray-900">Generated Code</h3>
              <div className="flex items-center space-x-1.5 bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('rendered')}
                  className={`px-2 py-1 text-xs rounded transition-colors ${
                    viewMode === 'rendered'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  🎨 Syntax
                </button>
                <button
                  onClick={() => setViewMode('raw')}
                  className={`px-2 py-1 text-xs rounded transition-colors ${
                    viewMode === 'raw'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  📝 Raw
                </button>
              </div>
            </div>

            {/* Code Content */}
            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
              {viewMode === 'rendered' ? (
                <SyntaxHighlighter
                  language="python"
                  style={{
                    'pre[class*="language-"]': {
                      background: '#f8fafc',
                      margin: 0,
                      padding: '0.75rem',
                      fontSize: '0.75rem',
                      lineHeight: '1.4',
                      overflow: 'auto',
                      maxHeight: '480px',
                    },
                    'code[class*="language-"]': {
                      color: '#334155',
                      fontFamily: 'Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace',
                    },
                    'comment': { color: '#64748b', fontStyle: 'italic' },
                    'punctuation': { color: '#64748b' },
                    'property': { color: '#0369a1' },
                    'string': { color: '#059669' },
                    'keyword': { color: '#7c3aed' },
                    'function': { color: '#0284c7' },
                    'number': { color: '#d97706' },
                    'operator': { color: '#475569' },
                    'class-name': { color: '#0891b2' },
                    'builtin': { color: '#0284c7' },
                    'decorator': { color: '#7c3aed' },
                  }}
                  customStyle={{
                    margin: 0,
                    borderRadius: '0.5rem'
                  }}
                  showLineNumbers
                  wrapLines
                >
                  {generatedCode}
                </SyntaxHighlighter>
              ) : (
                <div className="p-4 overflow-auto max-h-[480px]">
                  <pre className="text-xs whitespace-pre-wrap font-mono text-gray-900">
                    {generatedCode}
                  </pre>
                </div>
              )}
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
