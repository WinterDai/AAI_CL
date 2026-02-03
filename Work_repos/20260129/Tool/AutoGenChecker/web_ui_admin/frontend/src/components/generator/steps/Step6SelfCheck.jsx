import React, { useState, useEffect } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import Button from '../../common/Button';
import Card from '../../common/Card';
import { useGenerationStore } from '../../../store/generationStore';
import apiClient from '../../../api/client';

export default function Step6SelfCheck({ itemId }) {
  const { 
    module,
    generatedCode,
    itemConfig,
    fileAnalysis,
    generatedReadme,
    setGeneratedCode,
    setCurrentStep,
    stepStates,
    project,
    getStep1State,
    // Step6 persistent state
    step6IsChecking,
    setStep6IsChecking,
    step6CheckLogs,
    setStep6CheckLogs,
    addStep6Log
  } = useGenerationStore();
  
  // Get step1State using the getter (returns correct values based on lock status)
  const step1State = getStep1State();
  
  // Use store state for check status (persists across navigation)
  const isChecking = step6IsChecking;
  const setIsChecking = setStep6IsChecking;
  // Ensure checkLog is always an array (handle corrupted persist state)
  const checkLog = Array.isArray(step6CheckLogs) ? step6CheckLogs : [];
  const setCheckLog = setStep6CheckLogs;
  
  const [isReloading, setIsReloading] = useState(false);
  const [checkResults, setCheckResults] = useState(null);
  const [viewMode, setViewMode] = useState('rendered');
  const [editMode, setEditMode] = useState(false);
  const [editedCode, setEditedCode] = useState(generatedCode);

  useEffect(() => {
    setEditedCode(generatedCode);
  }, [generatedCode]);

  // Get effective config (support resume from Step 1 selection)
  // PRIORITY: project (locked) > step1State > props
  const effectiveModule = project?.locked ? project.module : (step1State?.selectedModule || module);
  const effectiveItemId = project?.locked ? project.itemId : (step1State?.selectedItem || itemId);
  const effectiveConfig = project?.locked ? project.yamlConfig : (itemConfig || step1State?.yamlData);

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
        setEditedCode(response.data.code);
        setCheckResults(null); // Clear previous check results
        setCheckLog(prev => [
          ...prev,
          `🔄 Reloaded from file: ${response.data.path}`,
          `    Modified: ${response.data.modified_time}`,
        ]);
        alert(`✅ Code reloaded from file!\nModified: ${response.data.modified_time}`);
      } else {
        alert('No code file found on disk.');
      }
    } catch (error) {
      console.error('Reload failed:', error);
      alert(`Reload failed: ${error.message}`);
    } finally {
      setIsReloading(false);
    }
  };

  const handleAutoCheck = async () => {
    // Check if Step 5 is completed or code exists
    if (!generatedCode) {
      alert('No generated code found. Please complete Step 5 first.');
      return;
    }
    if (!effectiveConfig) {
      alert('No configuration found. Please complete Step 1 first.');
      return;
    }

    setIsChecking(true);
    setCheckLog([]);
    setCheckResults(null);

    try {
      // Use streaming API for real-time log updates
      const response = await fetch('http://localhost:8000/api/step6/check-and-fix-stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          module: effectiveModule,
          item_id: effectiveItemId,
          code: generatedCode,
          config: effectiveConfig,
          file_analysis: fileAnalysis || [],
          readme: generatedReadme || '',
          max_fix_attempts: 3
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'log') {
                // Append log message in real-time
                setCheckLog(prev => [...prev, data.message]);
              } else if (data.type === 'complete') {
                // Handle final result
                if (data.status === 'success') {
                  setCheckResults(data);
                  
                  if (data.fixed_code && data.fixed_code !== generatedCode) {
                    setGeneratedCode(data.fixed_code);
                    setEditedCode(data.fixed_code);
                  }
                } else {
                  throw new Error(data.error || 'Check failed');
                }
              }
            } catch (parseError) {
              // Ignore JSON parse errors for incomplete messages
              console.debug('SSE parse error:', parseError);
            }
          }
        }
      }
    } catch (error) {
      console.error('Self-check failed:', error);
      setCheckLog(prev => [...prev, `❌ Error: ${error.message}`]);
      alert(`Self-check failed: ${error.message}`);
    } finally {
      setIsChecking(false);
    }
  };

  const handleManualCheck = async () => {
    setIsChecking(true);
    setCheckLog(['🔍 Validating manual edits...']);
    try {
      const response = await apiClient.post('/api/step6/manual-fix', {
        module: effectiveModule,
        item_id: effectiveItemId,
        code: editedCode,
        config: effectiveConfig,
        file_analysis: fileAnalysis || [],
        readme: generatedReadme || '',
        max_fix_attempts: 0
      });

      if (response.data.status === 'success') {
        setCheckResults(response.data);
        setGeneratedCode(editedCode);
        setEditMode(false);
        
        // Use detailed check log from backend
        if (response.data.check_log && response.data.check_log.length > 0) {
          setCheckLog(response.data.check_log);
        }
      }
    } catch (error) {
      console.error('Manual check failed:', error);
      setCheckLog(prev => [...prev, `❌ Error: ${error.message}`]);
      alert(`Validation failed: ${error.message}`);
    } finally {
      setIsChecking(false);
    }
  };

  const handleProceed = () => {
    if (!checkResults || checkResults.has_issues) {
      alert('Please fix all critical issues before proceeding');
      return;
    }
    setCurrentStep(7);
  };

  const handleBack = () => {
    setCurrentStep(5);
  };

  if (!generatedCode) {
    return (
      <Card>
        <div className="text-center py-8">
          <p className="text-gray-500 mb-4">Please complete Steps 1-5 first</p>
          <Button onClick={() => setCurrentStep(5)}>
            Go to Step 5
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="p-4 space-y-3">
      <Card>
        <div className="mb-3">
          <h2 className="text-base font-semibold mb-1">Step 6: Self-Check & Fix</h2>
          <p className="text-xs text-gray-600">
            Validate generated code and automatically fix issues
          </p>
          <div className="mt-2 text-xs text-gray-500">
            <p><strong>Validation Checks:</strong></p>
            <ul className="list-disc list-inside ml-2">
              <li>Syntax validation</li>
              <li>Template compliance</li>
              <li>Required methods presence</li>
              <li>Import validation</li>
              <li>Waiver tag rules</li>
              <li>Runtime validation</li>
            </ul>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 mb-3">
          {!editMode ? (
            <>
              <Button
                onClick={handleAutoCheck}
                disabled={isChecking || isReloading}
                size="xs"
                className="bg-blue-600 hover:bg-blue-700"
              >
                {isChecking ? '⏳ Checking...' : '🔍 Auto Check & Fix'}
              </Button>
              <Button
                onClick={handleReloadFromFile}
                disabled={isChecking || isReloading}
                size="xs"
                className="bg-purple-600 hover:bg-purple-700"
                title="Reload code from file (sync with VS Code changes)"
              >
                {isReloading ? '⏳ Reloading...' : '📂 Reload from File'}
              </Button>
              <Button
                onClick={() => setEditMode(true)}
                disabled={isChecking || isReloading}
                size="xs"
                className="bg-yellow-600 hover:bg-yellow-700"
              >
                ✎ Manual Edit
              </Button>
              {checkResults && !checkResults.has_issues && (
                <Button
                  onClick={handleProceed}
                  disabled={isChecking || isReloading}
                  size="xs"
                  className="bg-green-600 hover:bg-green-700"
                >
                  ✓ Proceed to Step 7
                </Button>
              )}
              <Button
                onClick={handleBack}
                disabled={isChecking || isReloading}
                size="xs"
                variant="secondary"
              >
                ← Back to Step 5
              </Button>
            </>
          ) : (
            <>
              <Button
                onClick={handleManualCheck}
                disabled={isChecking}
                size="xs"
                className="bg-green-600 hover:bg-green-700"
              >
                💾 Save & Validate
              </Button>
              <Button
                onClick={() => {
                  setEditMode(false);
                  setEditedCode(generatedCode);
                }}
                disabled={isChecking}
                size="xs"
                variant="secondary"
              >
                ✕ Cancel
              </Button>
            </>
          )}
        </div>

        {/* Check Log */}
        {checkLog.length > 0 && (
          <div className="mb-3">
            <h3 className="text-xs font-semibold text-gray-900 mb-1">Check Log</h3>
            <div className="bg-white border border-gray-200 rounded-lg p-3 max-h-[150px] overflow-auto">
              <div className="space-y-0.5 font-mono text-xs">
                {checkLog.map((log, idx) => (
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

        {/* Check Results */}
        {checkResults && (
          <div className={`mb-3 p-3 rounded-lg ${
            checkResults.has_issues 
              ? 'bg-red-50 border border-red-200' 
              : checkResults.has_warnings
              ? 'bg-yellow-50 border border-yellow-200'
              : 'bg-green-50 border border-green-200'
          }`}>
            <div className="flex items-center justify-between mb-1">
              <h3 className={`font-semibold text-xs ${
                checkResults.has_issues ? 'text-red-800' : 
                checkResults.has_warnings ? 'text-yellow-800' : 
                'text-green-800'
              }`}>
                {checkResults.has_issues ? '❌ Issues Found' : 
                 checkResults.has_warnings ? '⚠️ Warnings Found' : 
                 '✅ All Checks Passed'}
              </h3>
              <div className="text-xs">
                {checkResults.fix_attempts > 0 && (
                  <span className="text-gray-600">
                    Fixed in {checkResults.fix_attempts} attempt(s)
                  </span>
                )}
              </div>
            </div>
            
            {checkResults.critical_count > 0 && (
              <div className="mb-1">
                <p className="text-xs font-semibold text-red-700">
                  Critical Issues: {checkResults.critical_count}
                </p>
              </div>
            )}
            
            {checkResults.warning_count > 0 && (
              <div className="mb-1">
                <p className="text-xs font-semibold text-yellow-700">
                  Warnings: {checkResults.warning_count}
                </p>
              </div>
            )}

            {checkResults.issues && checkResults.issues.length > 0 && (
              <div className="mt-2">
                <p className="text-xs font-semibold mb-1">Issues:</p>
                <ul className="space-y-1 text-xs">
                  {checkResults.issues.slice(0, 5).map((issue, idx) => (
                    <li key={idx} className="pl-3 border-l-2 border-gray-300">
                      <span className={`font-semibold ${
                        issue.severity === 'critical' ? 'text-red-600' : 'text-yellow-600'
                      }`}>
                        [{issue.type}]
                      </span>{' '}
                      <span className="text-gray-700">{issue.message}</span>
                    </li>
                  ))}
                  {checkResults.issues.length > 5 && (
                    <li className="text-gray-500 text-xs">
                      ... and {checkResults.issues.length - 5} more
                    </li>
                  )}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Code Display/Edit */}
        {!editMode && (
          <>
            <div className="flex items-center justify-between mb-2">
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
                  showLineNumbers
                  wrapLines
                >
                  {generatedCode}
                </SyntaxHighlighter>
              ) : (
                <pre className="bg-gray-50 border border-gray-200 text-gray-900 p-3 overflow-auto max-h-[480px] text-xs font-mono rounded-lg">
                  <code>{generatedCode}</code>
                </pre>
              )}
            </div>
          </>
        )}

        {editMode && (
          <div>
            <textarea
              value={editedCode}
              onChange={(e) => setEditedCode(e.target.value)}
              className="w-full h-[480px] font-mono text-xs p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              style={{ 
                resize: 'vertical',
                backgroundColor: '#1e1e1e',
                color: '#d4d4d4'
              }}
            />
            <p className="text-xs text-gray-500 mt-1">
              {editedCode.length} characters • {editedCode.split('\n').length} lines
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}
