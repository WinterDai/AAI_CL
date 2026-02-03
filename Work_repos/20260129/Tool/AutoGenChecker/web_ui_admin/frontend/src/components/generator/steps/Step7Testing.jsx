import React, { useState, useEffect } from 'react';
import Button from '../../common/Button';
import Card from '../../common/Card';
import { useGenerationStore } from '../../../store/generationStore';
import apiClient from '../../../api/client';

export default function Step7Testing({ itemId }) {
  const { 
    module,
    generatedCode,
    itemConfig,
    generatedReadme,
    setCurrentStep,
    project,
    getStep1State,
    fileAnalysis,
    // Step7 persistent state
    step7IsRunning,
    setStep7IsRunning,
    step7TestLogs,
    setStep7TestLogs,
    addStep7Log
  } = useGenerationStore();
  
  // Get step1State using the getter (returns correct values based on lock status)
  const step1State = getStep1State();
  
  const [testResults, setTestResults] = useState({});
  // Use store state for running status (persists across navigation)
  const isRunning = step7IsRunning;
  const setIsRunning = setStep7IsRunning;
  // Ensure testLog is always an array (handle corrupted persist state)
  const testLog = Array.isArray(step7TestLogs) ? step7TestLogs : [];
  const setTestLog = setStep7TestLogs;
  
  const [selectedType, setSelectedType] = useState(null);
  const [expandedTests, setExpandedTests] = useState({});
  
  // Integration test state
  const [integrationResult, setIntegrationResult] = useState(null);
  const [isRunningIntegration, setIsRunningIntegration] = useState(false);
  
  // File content viewing state
  const [viewingFile, setViewingFile] = useState(null);  // { name, path, content, loading }
  const [fileViewOpen, setFileViewOpen] = useState(false);

  // Get effective config (support resume)
  // PRIORITY: project (locked) > step1State > props
  const effectiveModule = project?.locked ? project.module : (step1State?.selectedModule || module);
  const effectiveItemId = project?.locked ? project.itemId : (step1State?.selectedItem || itemId);
  const effectiveConfig = project?.locked ? project.yamlConfig : (itemConfig || step1State?.yamlData);

  // 6 test types matching CLI exactly (names match CLI format)
  const testTypes = [
    { id: 'type1_na', name: 'Type 1 (requirements.value=N/A, waivers.value=N/A)', desc: 'Boolean check, no waivers' },
    { id: 'type1_0', name: 'Type 1 (requirements.value=N/A, waivers.value=0)', desc: 'Boolean check with waiver=0' },
    { id: 'type2_na', name: 'Type 2 (requirements.value>0, waivers.value=N/A)', desc: 'Value check, no waivers' },
    { id: 'type2_0', name: 'Type 2 (requirements.value>0, waivers.value=0)', desc: 'Value check with waiver=0' },
    { id: 'type3', name: 'Type 3 (requirements.value>0, waivers.value>0)', desc: 'Value check with waivers' },
    { id: 'type4', name: 'Type 4 (requirements.value=N/A, waivers.value>0)', desc: 'Boolean check with waivers' }
  ];

  const handleRunTest = async (testType) => {
    if (!generatedCode || !effectiveConfig) {
      alert('Please complete Steps 1-6 first');
      return;
    }

    setIsRunning(true);
    setSelectedType(testType);
    setTestLog(prev => [...prev, `🧪 Running ${testType}...`]);

    try {
      const response = await apiClient.post('/api/step7/run-test', {
        module: effectiveModule,
        item_id: effectiveItemId,
        code: generatedCode,
        config: effectiveConfig,
        readme: generatedReadme || '',
        test_type: testType
      });

      if (response.data.status === 'success') {
        setTestResults(prev => ({
          ...prev,
          [testType]: response.data
        }));
        
        const resultIcon = response.data.check_result === 'PASS' ? '✅' : 
                          response.data.check_result === 'FAIL' ? '❌' : '⚠️';
        setTestLog(prev => [...prev, `    ${resultIcon} ${response.data.check_result} (${response.data.execution_time?.toFixed(2)}s)`]);
      } else {
        throw new Error(response.data.error || 'Test failed');
      }
    } catch (error) {
      console.error('Test failed:', error);
      setTestResults(prev => ({
        ...prev,
        [testType]: {
          status: 'error',
          test_passed: false,
          check_result: 'ERROR',
          error: error.message
        }
      }));
      setTestLog(prev => [...prev, `    ⚠️ ERROR: ${error.message}`]);
    } finally {
      setIsRunning(false);
      setSelectedType(null);
    }
  };

  const handleRunAllTests = async () => {
    if (!generatedCode || !effectiveConfig) {
      alert('Please complete Steps 1-6 first');
      return;
    }

    setIsRunning(true);
    setTestResults({});
    setTestLog(['🚀 Running all 6 test types...', '']);

    try {
      const response = await apiClient.post('/api/step7/run-all-tests', {
        module: effectiveModule,
        item_id: effectiveItemId,
        code: generatedCode,
        config: effectiveConfig,
        readme: generatedReadme || ''
      });

      if (response.data.status === 'success') {
        setTestResults(response.data.results || {});
        setTestLog(response.data.test_log || []);
      } else {
        throw new Error(response.data.error || 'Tests failed');
      }
    } catch (error) {
      console.error('All tests failed:', error);
      setTestLog(prev => [...prev, `❌ Error: ${error.message}`]);
    } finally {
      setIsRunning(false);
    }
  };

  // Integration test handler
  const handleIntegrationTest = async () => {
    if (!generatedCode) {
      alert('Please complete code generation first');
      return;
    }

    setIsRunningIntegration(true);
    setIntegrationResult(null);

    try {
      const response = await apiClient.post('/api/step7/integration-test', {
        module: effectiveModule,
        item_id: effectiveItemId,
        code: generatedCode
      });

      setIntegrationResult(response.data);
    } catch (error) {
      console.error('Integration test failed:', error);
      setIntegrationResult({
        status: 'error',
        error: error.message
      });
    } finally {
      setIsRunningIntegration(false);
    }
  };

  // Handle viewing file content
  const handleViewFile = async (fileName, filePath) => {
    setViewingFile({ name: fileName, path: filePath, content: null, loading: true });
    setFileViewOpen(true);
    
    try {
      const response = await apiClient.get('/api/step7/read-file', {
        params: { path: filePath }
      });
      
      if (response.data.status === 'success') {
        setViewingFile(prev => ({ ...prev, content: response.data.content, loading: false }));
      } else {
        setViewingFile(prev => ({ ...prev, content: `Error: ${response.data.error}`, loading: false }));
      }
    } catch (error) {
      setViewingFile(prev => ({ ...prev, content: `Error: ${error.message}`, loading: false }));
    }
  };

  const toggleExpanded = (testType) => {
    setExpandedTests(prev => ({
      ...prev,
      [testType]: !prev[testType]
    }));
  };

  const handleProceed = () => {
    const passedCount = Object.values(testResults).filter(r => r.check_result === 'PASS').length;
    const totalCount = Object.keys(testResults).length;
    
    if (totalCount > 0 && passedCount < totalCount) {
      const confirm = window.confirm(`${totalCount - passedCount} test(s) did not pass. Proceed anyway?`);
      if (!confirm) return;
    }
    setCurrentStep(8);
  };

  const handleBack = () => {
    setCurrentStep(6);
  };

  if (!generatedCode) {
    return (
      <Card>
        <div className="text-center py-8">
          <p className="text-gray-500 mb-4">Please complete Steps 1-6 first</p>
          <Button onClick={() => setCurrentStep(6)}>
            Go to Step 6
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="p-4 space-y-3">
      <Card>
        <div className="mb-3">
          <h2 className="text-base font-semibold mb-1">Step 7: Interactive Testing</h2>
          <p className="text-xs text-gray-600">
            Test checker with all 6 Type configurations (matching CLI workflow)
          </p>
          <div className="mt-2 text-xs text-gray-500">
            <p><strong>Test Types:</strong></p>
            <ul className="list-disc list-inside ml-2">
              <li>Type 1 (N/A, N/A/0): Boolean check without/with waiver=0</li>
              <li>Type 2 (&gt;0, N/A/0): Value check without/with waiver=0</li>
              <li>Type 3 (&gt;0, &gt;0): Value check with active waivers</li>
              <li>Type 4 (N/A, &gt;0): Boolean check with active waivers</li>
            </ul>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 mb-4 flex-wrap">
          <Button
            onClick={handleRunAllTests}
            disabled={isRunning || isRunningIntegration}
            size="xs"
            className="bg-blue-600 hover:bg-blue-700"
          >
            {isRunning ? '⏳ Running...' : '🚀 Run All 6 Tests'}
          </Button>
          <Button
            onClick={handleIntegrationTest}
            disabled={isRunning || isRunningIntegration}
            size="xs"
            className="bg-purple-600 hover:bg-purple-700"
          >
            {isRunningIntegration ? '⏳ Running...' : '🔗 Integration Test'}
          </Button>
          <Button
            onClick={handleProceed}
            disabled={isRunning || isRunningIntegration}
            size="xs"
            className="bg-green-600 hover:bg-green-700"
          >
            ✓ Proceed to Step 8
          </Button>
          <Button
            onClick={handleBack}
            disabled={isRunning || isRunningIntegration}
            size="xs"
            variant="secondary"
          >
            ← Back to Step 6
          </Button>
        </div>

        {/* Integration Test Results */}
        {integrationResult && (
          <div className="mb-4 border rounded-lg overflow-hidden">
            <div className={`p-2 font-semibold text-xs ${
              integrationResult.status === 'success' ? 'bg-green-100 text-green-800' :
              integrationResult.status === 'error' ? 'bg-red-100 text-red-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              🔗 Integration Test Results
              {integrationResult.checker_result && (
                <span className="ml-2">
                  - Checker: {integrationResult.checker_result === 'PASS' ? '✅ PASS' : 
                             integrationResult.checker_result === 'FAIL' ? '❌ FAIL' : '⚠️ UNKNOWN'}
                </span>
              )}
            </div>
            
            <div className="p-3 space-y-2">
              {/* Steps */}
              {integrationResult.steps && integrationResult.steps.length > 0 && (
                <div>
                  <h4 className="font-medium text-xs mb-1">Steps:</h4>
                  <div className="space-y-0.5">
                    {integrationResult.steps.map((step, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-xs">
                        <span>
                          {step.status === 'success' ? '✅' : 
                           step.status === 'error' ? '❌' : 
                           step.status === 'warning' ? '⚠️' : '⏳'}
                        </span>
                        <span className="font-medium">[{idx + 1}/4]</span>
                        <span>{step.name}</span>
                        {step.message && <span className="text-gray-600">- {step.message}</span>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Generated Files */}
              {integrationResult.generated_files && Object.keys(integrationResult.generated_files).length > 0 && (
                <div>
                  <h4 className="font-medium text-xs mb-1">Generated Files:</h4>
                  <div className="grid grid-cols-3 gap-1">
                    {Object.entries(integrationResult.generated_files).map(([name, info]) => (
                      <div key={name} className={`p-2 rounded text-xs ${
                        info.exists ? 'bg-green-50 text-green-800' : 'bg-gray-50 text-gray-500'
                      }`}>
                        <div className="font-medium">{name}</div>
                        {info.exists ? (
                          <>
                            <div>{info.size ? `${info.size} bytes` : 'exists'}</div>
                            <button
                              onClick={() => handleViewFile(name, info.path)}
                              className="text-blue-600 hover:underline mt-1"
                            >
                              📄 View content
                            </button>
                          </>
                        ) : (
                          <div>not found</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Output (collapsible) */}
              {(integrationResult.stdout || integrationResult.stderr) && (
                <details className="mt-2">
                  <summary className="cursor-pointer text-sm text-blue-600 hover:underline">
                    Show output details
                  </summary>
                  <div className="mt-2 bg-gray-50 border border-gray-200 p-3 rounded text-xs font-mono max-h-48 overflow-auto">
                    {integrationResult.stdout && (
                      <div>
                        <div className="text-gray-500 font-bold">STDOUT:</div>
                        <pre className="whitespace-pre-wrap text-gray-700">{integrationResult.stdout}</pre>
                      </div>
                    )}
                    {integrationResult.stderr && (
                      <div className="mt-2">
                        <div className="text-gray-500 font-bold">STDERR:</div>
                        <pre className="whitespace-pre-wrap text-red-600">{integrationResult.stderr}</pre>
                      </div>
                    )}
                  </div>
                </details>
              )}
              
              {integrationResult.error && (
                <div className="text-red-600 text-sm">
                  ❌ Error: {integrationResult.error}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Test Types Grid - 2 columns x 3 rows */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {testTypes.map((type) => {
            const result = testResults[type.id];
            const isActive = selectedType === type.id;
            const isExpanded = expandedTests[type.id];

            return (
              <div
                key={type.id}
                className={`border rounded-lg p-3 ${
                  result?.check_result === 'PASS'
                    ? 'border-green-300 bg-green-50'
                    : result?.check_result === 'FAIL'
                    ? 'border-red-300 bg-red-50'
                    : result?.check_result === 'ERROR'
                    ? 'border-yellow-300 bg-yellow-50'
                    : 'border-gray-300 bg-white'
                }`}
              >
                <div className="flex items-start justify-between mb-1">
                  <div>
                    <h3 className="font-semibold text-xs">{type.name}</h3>
                    <p className="text-[10px] text-gray-600">{type.desc}</p>
                  </div>
                  {result && (
                    <div className="text-sm">
                      {result.check_result === 'PASS' ? '✅' : 
                       result.check_result === 'FAIL' ? '❌' : '⚠️'}
                    </div>
                  )}
                </div>

                <Button
                  onClick={() => handleRunTest(type.id)}
                  disabled={isRunning}
                  size="xs"
                  variant={result?.check_result === 'PASS' ? 'secondary' : 'primary'}
                  className="w-full mb-1"
                >
                  {isActive ? '⏳ Running...' : result ? '↻ Re-run' : '▶ Run'}
                </Button>

                {result && (
                  <div className="mt-1">
                    <div className="text-[10px]">
                      {result.check_result === 'PASS' && (
                        <span className="text-green-700">✓ PASS ({result.execution_time?.toFixed(2)}s)</span>
                      )}
                      {result.check_result === 'FAIL' && (
                        <span className="text-red-700">✗ FAIL ({result.execution_time?.toFixed(2)}s)</span>
                      )}
                      {result.check_result === 'ERROR' && (
                        <span className="text-yellow-700">⚠ ERROR: {result.error}</span>
                      )}
                    </div>
                    
                    {/* Expandable output */}
                    {(result.log_output || result.report_output) && (
                      <button
                        onClick={() => toggleExpanded(type.id)}
                        className="text-[10px] text-blue-600 hover:underline mt-0.5"
                      >
                        {isExpanded ? '▼ Hide output' : '▶ Show output'}
                      </button>
                    )}
                    
                    {isExpanded && (
                      <div className="mt-1 p-1.5 bg-gray-100 rounded text-[10px] font-mono max-h-36 overflow-auto">
                        {result.log_output && (
                          <div>
                            <div className="font-bold text-gray-700">Log:</div>
                            <pre className="whitespace-pre-wrap">{result.log_output}</pre>
                          </div>
                        )}
                        {result.report_output && (
                          <div className="mt-2">
                            <div className="font-bold text-gray-700">Report:</div>
                            <pre className="whitespace-pre-wrap">{result.report_output}</pre>
                          </div>
                        )}
                        {result.stderr && (
                          <div className="mt-2 text-red-600">
                            <div className="font-bold">Stderr:</div>
                            <pre className="whitespace-pre-wrap">{result.stderr}</pre>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Test Log */}
        {testLog.length > 0 && (
          <div className="mt-4">
            <h3 className="font-semibold text-xs mb-1">Test Log</h3>
            <div className="bg-gray-50 border border-gray-200 text-gray-700 p-3 rounded-lg font-mono text-xs max-h-48 overflow-auto">
              {testLog.map((line, idx) => (
                <div key={idx}>{line}</div>
              ))}
            </div>
          </div>
        )}

        {/* Summary */}
        {Object.keys(testResults).length > 0 && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <h3 className="font-semibold text-xs mb-1">Test Summary</h3>
            <div className="flex gap-4 text-xs">
              <div>
                <span className="text-gray-600">Total: </span>
                <span className="font-semibold">{Object.keys(testResults).length}/6</span>
              </div>
              <div>
                <span className="text-gray-600">Passed: </span>
                <span className="font-semibold text-green-600">
                  {Object.values(testResults).filter(r => r.check_result === 'PASS').length}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Failed: </span>
                <span className="font-semibold text-red-600">
                  {Object.values(testResults).filter(r => r.check_result === 'FAIL').length}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Errors: </span>
                <span className="font-semibold text-yellow-600">
                  {Object.values(testResults).filter(r => r.check_result === 'ERROR' || r.check_result === 'UNKNOWN').length}
                </span>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* File Content Modal */}
      {fileViewOpen && viewingFile && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] m-4 flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="font-semibold text-sm">
                📄 {viewingFile.name} - {viewingFile.path}
              </h3>
              <button
                onClick={() => { setFileViewOpen(false); setViewingFile(null); }}
                className="text-gray-500 hover:text-gray-700 text-base font-bold"
              >
                ×
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4">
              {viewingFile.loading ? (
                <div className="flex items-center justify-center h-32">
                  <span className="text-gray-500">Loading...</span>
                </div>
              ) : (
                <pre className="bg-gray-50 border border-gray-200 p-4 rounded text-sm font-mono whitespace-pre-wrap">
                  {viewingFile.content}
                </pre>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
