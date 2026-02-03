import React, { useState } from 'react';
import Button from '../../common/Button';
import Card from '../../common/Card';
import { useGenerationStore } from '../../../store/generationStore';
import apiClient from '../../../api/client';

export default function Step9Package({ itemId }) {
  const { 
    module,
    generatedCode,
    generatedReadme,
    itemConfig,
    fileAnalysis,
    setCurrentStep,
    project,
    getStep1State,
    // Step9 persistent state
    step9IsPackaging,
    setStep9IsPackaging
  } = useGenerationStore();
  
  // Get step1State using the getter (returns correct values based on lock status)
  const step1State = getStep1State();
  
  // Use store state for packaging status (persists across navigation)
  const isPackaging = step9IsPackaging;
  const setIsPackaging = setStep9IsPackaging;
  const [packageResult, setPackageResult] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  
  // State for file viewer modal
  const [viewingFile, setViewingFile] = useState(null);
  const [fileContent, setFileContent] = useState('');
  const [isLoadingFile, setIsLoadingFile] = useState(false);

  // View file content
  const handleViewFile = async (filePath) => {
    setIsLoadingFile(true);
    try {
      const response = await apiClient.post('/api/step9/view-file', {
        file_path: filePath
      });
      if (response.data.status === 'success') {
        setFileContent(response.data.content);
        setViewingFile(response.data.file_name || filePath);
      } else {
        alert(`Error: ${response.data.error}`);
      }
    } catch (error) {
      alert(`Failed to load file: ${error.message}`);
    } finally {
      setIsLoadingFile(false);
    }
  };

  // Get effective values from step1State (support resume)
  // PRIORITY: project (locked) > step1State > props
  const effectiveModule = project?.locked ? project.module : (step1State?.selectedModule || module);
  const effectiveItemId = project?.locked ? project.itemId : (step1State?.selectedItem || itemId);
  const effectiveConfig = project?.locked ? project.yamlConfig : (itemConfig || step1State?.yamlData);

  const handlePackage = async () => {
    if (!generatedCode) {
      alert('Please complete code generation first');
      return;
    }

    setIsPackaging(true);

    try {
      // Debug: First try debug endpoint
      const debugResponse = await apiClient.post('/api/step9/package-debug', {
        module: effectiveModule || '',
        item_id: effectiveItemId || '',
        code: generatedCode || '',
        readme: generatedReadme || '',
        config: effectiveConfig || {},
        file_analysis: fileAnalysis || null
      });
      
      console.log('Debug response:', debugResponse.data);
      
      // Then try real endpoint
      const response = await apiClient.post('/api/step9/package', {
        module: effectiveModule || '',
        item_id: effectiveItemId || '',
        code: generatedCode || '',
        readme: generatedReadme || '',
        config: effectiveConfig || {},
        file_analysis: fileAnalysis || null
      });

      if (response.data.status === 'success') {
        setPackageResult(response.data);
      } else {
        throw new Error(response.data.error || 'Package failed');
      }
    } catch (error) {
      console.error('Package failed:', error);
      alert(`Package failed: ${error.message}`);
    } finally {
      setIsPackaging(false);
    }
  };

  const handleBack = () => {
    setCurrentStep(8);
  };

  const handleNewChecker = () => {
    const confirm = window.confirm('Start a new checker? This will reset all progress.');
    if (confirm) {
      setCurrentStep(1);
      window.location.href = '/';
    }
  };

  const handleGitUpload = async () => {
    if (!packageResult) {
      alert('Please package the checker first');
      return;
    }

    const branchName = prompt(
      `Enter branch name (or leave empty for auto-generated):`,
      `checker-${effectiveModule}-${effectiveItemId}`
    );

    if (branchName === null) return; // User cancelled

    setIsUploading(true);
    setUploadResult(null);

    try {
      // Get input_files from config
      const inputFiles = effectiveConfig?.input_files || [];
      
      const response = await apiClient.post('/api/step9/git-upload', {
        module: effectiveModule,
        item_id: effectiveItemId,
        branch_name: branchName || undefined,
        commit_message: `Add checker for ${effectiveModule}/${effectiveItemId}`,
        input_files: inputFiles  // Include input files from config
      });

      if (response.data.status === 'success') {
        setUploadResult(response.data);
        alert(`✅ Successfully uploaded to branch: ${response.data.branch}`);
      } else {
        throw new Error(response.data.error || 'Upload failed');
      }
    } catch (error) {
      console.error('Git upload failed:', error);
      alert(`❌ Git upload failed: ${error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  if (!generatedCode) {
    return (
      <Card>
        <div className="text-center py-8">
          <p className="text-gray-500 mb-4">Please complete Steps 1-8 first</p>
          <Button onClick={() => setCurrentStep(8)}>
            Go to Step 8
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="p-4 space-y-3">
      <Card>
        <div className="mb-4">
          <h2 className="text-base font-semibold mb-1">Step 9: Package & Report</h2>
          <p className="text-xs text-gray-600">
            Package checker artifacts and generate final report
          </p>
        </div>

        {!packageResult ? (
          <>
            {/* Pre-package Summary */}
            <div className="mb-4 p-3 bg-gray-50 rounded-lg">
              <h3 className="font-semibold text-xs mb-2">Ready to Package:</h3>
              <div className="space-y-1 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Item ID:</span>
                  <span className="font-mono font-semibold">{effectiveItemId}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Module:</span>
                  <span className="font-mono">{effectiveModule}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Code Lines:</span>
                  <span className="font-semibold">{generatedCode.split('\n').length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">README Lines:</span>
                  <span className="font-semibold">{generatedReadme.split('\n').length}</span>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
              <Button
                onClick={handlePackage}
                disabled={isPackaging}
                size="xs"
                className="bg-green-600 hover:bg-green-700"
              >
                {isPackaging ? '⏳ Packaging...' : '📦 Package Checker'}
              </Button>
              <Button
                onClick={handleBack}
                disabled={isPackaging}
                size="xs"
                variant="secondary"
              >
                ← Back to Step 8
              </Button>
            </div>
          </>
        ) : (
          <>
            {/* Success Message */}
            <div className="mb-4 p-4 bg-green-50 border-2 border-green-300 rounded-lg text-center">
              <div className="text-4xl mb-3">🎉</div>
              <h3 className="text-sm font-bold text-green-800 mb-1">
                Checker Generated Successfully!
              </h3>
              <p className="text-xs text-green-700">
                All artifacts have been packaged and saved.
              </p>
            </div>

            {/* Artifacts */}
            <div className="mb-4">
              <h3 className="font-semibold text-xs mb-2">Generated Artifacts:</h3>
              <div className="space-y-1">
                {packageResult.artifacts && Object.entries(packageResult.artifacts)
                  .filter(([key, path]) => path && (typeof path === 'string' || (Array.isArray(path) && path.length > 0)))
                  .map(([key, path]) => (
                  <div key={key} className="p-2 bg-gray-50 rounded-lg flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <span className="font-semibold text-xs capitalize">{key}:</span>
                      {Array.isArray(path) ? (
                        <ul className="ml-2 mt-1">
                          {path.map((p, idx) => (
                            <li key={idx} className="font-mono text-[10px] text-gray-600 truncate">{p}</li>
                          ))}
                        </ul>
                      ) : (
                        <span className="ml-2 font-mono text-[10px] text-gray-600 truncate block">{path}</span>
                      )}
                    </div>
                    <button
                      onClick={() => {
                        // For arrays, view the first file; for strings, view directly
                        const filePath = Array.isArray(path) ? path[0] : path;
                        handleViewFile(filePath);
                      }}
                      disabled={isLoadingFile}
                      className="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-100 whitespace-nowrap ml-2 disabled:opacity-50"
                    >
                      {isLoadingFile ? '⏳' : '📄'} View
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* File Content Viewer Modal */}
            {viewingFile && (
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-xs">📄 {viewingFile}</h3>
                  <button
                    onClick={() => { setViewingFile(null); setFileContent(''); }}
                    className="px-2 py-0.5 text-xs text-gray-500 hover:text-gray-700"
                  >
                    ✕ Close
                  </button>
                </div>
                <div className="bg-gray-50 border border-gray-200 text-gray-800 p-3 rounded-lg overflow-auto max-h-64">
                  <pre className="text-[10px] font-mono whitespace-pre-wrap">
                    {fileContent}
                  </pre>
                </div>
              </div>
            )}

            {/* Report */}
            {packageResult.report && (
              <div className="mb-4">
                <h3 className="font-semibold text-xs mb-2">Generation Report:</h3>
                <div className="bg-gray-50 border border-gray-200 text-gray-800 p-4 rounded-lg overflow-auto max-h-72">
                  <pre className="text-[10px] font-mono whitespace-pre">
                    {packageResult.report}
                  </pre>
                </div>
              </div>
            )}

            {/* Git Upload Section */}
            <div className="mb-4">
              <h3 className="font-semibold text-xs mb-2">Upload to Git:</h3>
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-xs text-gray-700 mb-2">
                  Upload checker scripts and input files to a git branch for version control.
                </p>
                <Button
                  onClick={handleGitUpload}
                  disabled={isUploading}
                  size="xs"
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  {isUploading ? '⏳ Uploading to Git...' : '🔀 Upload to Git Branch'}
                </Button>
              </div>
              
              {uploadResult && (
                <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <h4 className="font-semibold text-green-800 text-xs mb-1">✅ Upload Successful!</h4>
                  <div className="space-y-0.5 text-xs">
                    <div>
                      <span className="font-semibold">Branch:</span>
                      <span className="ml-2 font-mono text-green-700">{uploadResult.branch}</span>
                    </div>
                    {uploadResult.commit && (
                      <div>
                        <span className="font-semibold">Commit:</span>
                        <span className="ml-2 font-mono text-green-700">{uploadResult.commit}</span>
                      </div>
                    )}
                    {uploadResult.files_uploaded && uploadResult.files_uploaded.length > 0 && (
                      <div>
                        <span className="font-semibold">Files ({uploadResult.files_uploaded.length}):</span>
                        <ul className="ml-4 mt-1 list-disc list-inside">
                          {uploadResult.files_uploaded.slice(0, 5).map((file, idx) => (
                            <li key={idx} className="text-xs font-mono text-gray-600">{file}</li>
                          ))}
                          {uploadResult.files_uploaded.length > 5 && (
                            <li className="text-xs text-gray-500">...and {uploadResult.files_uploaded.length - 5} more</li>
                          )}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Final Actions */}
            <div className="flex gap-2">
              <Button
                onClick={handleNewChecker}
                size="xs"
                className="bg-blue-600 hover:bg-blue-700"
              >
                🆕 Generate New Checker
              </Button>
              <Button
                onClick={() => window.location.href = '/'}
                size="xs"
                variant="secondary"
              >
                🏠 Back to Dashboard
              </Button>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
